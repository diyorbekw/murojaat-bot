"""
Django API client for bot
"""

import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class UserData:
    """User data structure"""
    telegram_id: int
    full_name: str
    username: Optional[str] = None
    phone_number: Optional[str] = None
    second_phone: Optional[str] = None
    age: Optional[int] = None
    role: str = 'user'
    registration_completed: bool = False
    # Qo'shimcha maydonlar
    id: Optional[int] = None
    language: str = 'uz'
    is_active: bool = True
    is_blocked: bool = False
    complaints_count: int = 0
    last_complaint_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_active: Optional[str] = None


class DjangoAPIClient:
    """Async client for Django API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"API request error: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {}
    
    # User-related methods
    async def get_or_create_user(self, telegram_id: int, full_name: str, 
                                username: Optional[str] = None) -> Optional[UserData]:
        """Get or create user in Django"""
        endpoint = "telegram/register/"
        data = {
            "telegram_id": telegram_id,
            "full_name": full_name,
            "username": username
        }
        
        result = await self._request("POST", endpoint, json=data)
        if result:
            # Faqat UserData da mavjud bo'lgan maydonlarni olib, qolganlarini ignore qilish
            user_data_dict = {}
            user_data_fields = UserData.__dataclass_fields__.keys()
            
            for field in user_data_fields:
                if field in result:
                    user_data_dict[field] = result[field]
            
            return UserData(**user_data_dict)
        return None
    
    async def check_user_registration(self, telegram_id: int) -> Dict[str, Any]:
        """Check if user is registered"""
        endpoint = f"check_user_registration/{telegram_id}/"
        return await self._request("GET", endpoint)
    
    async def update_user_profile(self, telegram_id: int, **kwargs) -> Optional[UserData]:
        """Update user profile"""
        endpoint = "telegram/update_profile/"
        data = {"telegram_id": telegram_id, **kwargs}
        
        result = await self._request("POST", endpoint, json=data)
        if result:
            # Faqat UserData da mavjud bo'lgan maydonlarni olib, qolganlarini ignore qilish
            user_data_dict = {}
            user_data_fields = UserData.__dataclass_fields__.keys()
            
            for field in user_data_fields:
                if field in result:
                    user_data_dict[field] = result[field]
            
            return UserData(**user_data_dict)
        return None
    
    async def get_user_profile(self, telegram_id: int) -> Optional[UserData]:
        """Get user profile by telegram_id"""
        # Avval check_user_registration qilamiz
        check_result = await self.check_user_registration(telegram_id)
        
        if check_result.get('exists'):
            # Agar user mavjud bo'lsa, to'liq ma'lumotlarini olish
            try:
                # Foydalanuvchini telegram_id bo'yicha qidirish
                endpoint = f"users/by_telegram_id/?telegram_id={telegram_id}"
                result = await self._request("GET", endpoint)
                
                if result:
                    # UserData ga konvertatsiya qilish
                    user_data_dict = {}
                    user_data_fields = UserData.__dataclass_fields__.keys()
                    
                    for field in user_data_fields:
                        if field in result:
                            user_data_dict[field] = result[field]
                    
                    return UserData(**user_data_dict)
            except Exception as e:
                print(f"Error getting user profile: {e}")
        
        return None
    
    # Category and SubCategory methods
    async def get_categories(self) -> list:
        """Get list of categories"""
        endpoint = "telegram/categories/"
        result = await self._request("GET", endpoint)
        return result or []
    
    async def get_subcategories(self, category_id: Optional[int] = None) -> list:
        """Get list of subcategories"""
        if category_id:
            endpoint = f"telegram/subcategories/?category_id={category_id}"
        else:
            endpoint = "telegram/subcategories/"
        result = await self._request("GET", endpoint)
        return result or []
    
    async def get_category_with_subcategories(self, category_id: int) -> Dict[str, Any]:
        """Get category with its subcategories"""
        # Category ma'lumotlari
        categories = await self.get_categories()
        category = next((c for c in categories if c.get('id') == category_id), None)
        
        if category:
            # Subcategory ma'lumotlari
            subcategories = await self.get_subcategories(category_id)
            category['subcategories'] = subcategories
        
        return category or {}
    
    # Mahalla methods
    async def get_mahallas(self) -> list:
        """Get list of mahallas"""
        endpoint = "telegram/mahallas/"
        result = await self._request("GET", endpoint)
        return result or []
    
    # Complaint-related methods
    async def create_complaint(self, complaint_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new complaint with subcategory support"""
        endpoint = "complaints/telegram_create/"
        result = await self._request("POST", endpoint, json=complaint_data)
        return result
    
    async def get_user_complaints(self, telegram_id: int) -> list:
        """Get user's complaints"""
        endpoint = f"complaints/?telegram_id={telegram_id}"
        result = await self._request("GET", endpoint)
        return result.get("results", []) if "results" in result else result
    
    async def get_complaint_details(self, complaint_id: int, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get complaint details"""
        endpoint = f"complaints/{complaint_id}/?telegram_id={telegram_id}"
        return await self._request("GET", endpoint)
    
    # Statistics
    async def get_user_stats(self, telegram_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        endpoint = f"complaints/stats/?telegram_id={telegram_id}"
        return await self._request("GET", endpoint)
    
    async def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        endpoint = "stats/"
        return await self._request("GET", endpoint)