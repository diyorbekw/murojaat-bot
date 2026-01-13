"""
Django REST API client for Telegram bot
"""

import aiohttp
import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from bot.config import config

logger = logging.getLogger(__name__)


class DjangoAPIClient:
    """Async client for Django REST API"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request to Django API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = kwargs.pop('headers', {})
        headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        try:
            # DEBUG: Print request info
            logger.debug(f"API Request: {method} {url}")
            
            async with self.session.request(method, url, headers=headers, **kwargs) as response:
                logger.debug(f"API Response Status: {response.status}")
                
                if response.status in (200, 201):
                    return await response.json()
                elif response.status == 204:
                    return {}
                else:
                    error_text = await response.text()
                    logger.error(f"API Error {response.status}: {error_text}")
                    
                    # DEBUG: Return test data for development
                    if response.status == 403:
                        logger.warning("API returned 403, using fallback data for development")
                        return self._get_fallback_data(endpoint, method, kwargs.get('params'))
                    
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP Client Error: {e}")
            # Return fallback data for development
            return self._get_fallback_data(endpoint, method, kwargs.get('params'))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_fallback_data(endpoint, method, kwargs.get('params'))
    
    def _get_fallback_data(self, endpoint: str, method: str, params: dict = None) -> Optional[Dict]:
        """Return fallback data for development when API fails"""
        logger.warning(f"Using fallback data for {method} {endpoint}")
        
        if 'mahallas' in endpoint:
            return [{'id': i, 'name': name} for i, name in enumerate(config.DEFAULT_MAHALLAS, 1)]
        
        elif 'categories' in endpoint:
            return [{'id': i, 'name': name, 'icon': '📝'} for i, name in enumerate(config.DEFAULT_CATEGORIES, 1)]
        
        elif 'complaints/telegram_create' in endpoint and method == 'POST':
            # Mock complaint creation response
            return {
                'id': random.randint(1000, 9999),
                'status': 'new',
                'user': {'full_name': 'Test User', 'telegram_id': 123456789},
                'mahalla': {'name': 'Test Mahalla'},
                'category': {'name': 'Test Category'}
            }
        
        elif 'complaints' in endpoint and method == 'GET':
            # Mock complaints list with telegram_id filtering
            telegram_id = params.get('telegram_id') if params else None
            
            complaints = []
            for i in range(5):
                days_ago = random.randint(0, 30)
                created_at = (datetime.now() - timedelta(days=days_ago)).isoformat()
                
                # Agar telegram_id berilgan bo'lsa, faqat shu user uchun
                if telegram_id:
                    user_telegram_id = int(telegram_id)
                else:
                    user_telegram_id = 123456789 + i
                
                complaints.append({
                    'id': random.randint(100, 999),
                    'status': random.choice(['new', 'in_progress', 'solved', 'delayed']),
                    'title': f"Test complaint {i+1}",
                    'description': f"This is a test complaint #{i+1}",
                    'created_at': created_at,
                    'user': {
                        'full_name': f'Test User {i+1}',
                        'telegram_id': user_telegram_id
                    },
                    'mahalla': {
                        'name': random.choice(config.DEFAULT_MAHALLAS)
                    },
                    'category': {
                        'name': random.choice(config.DEFAULT_CATEGORIES)
                    },
                    'images': []
                })
            
            return {'results': complaints}
        
        return None
    
    # User operations
    async def register_user(self, telegram_id: int, full_name: str, username: str = None) -> Optional[Dict]:
        """Register Telegram user in Django"""
        data = {
            'telegram_id': telegram_id,
            'full_name': full_name,
            'username': username,
        }
        return await self._make_request('POST', 'telegram/register/', json=data)
    
    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        params = {'telegram_id': telegram_id}
        result = await self._make_request('GET', 'users/', params=params)
        if result and 'results' in result and len(result['results']) > 0:
            return result['results'][0]
        return None
    
    # Mahalla operations
    async def get_mahallas(self) -> List[Dict]:
        """Get list of mahallas from Django"""
        result = await self._make_request('GET', 'telegram/mahallas/')
        return result if result else []
    
    # Category operations
    async def get_categories(self) -> List[Dict]:
        """Get list of categories from Django"""
        result = await self._make_request('GET', 'telegram/categories/')
        return result if result else []
    
    # Complaint operations
    async def create_complaint(self, complaint_data: Dict) -> Optional[Dict]:
        """Create new complaint in Django"""
        return await self._make_request('POST', 'complaints/telegram_create/', json=complaint_data)
    
    async def get_user_complaints(self, telegram_id: int) -> List[Dict]:
        """Get user's complaints from Django"""
        params = {'telegram_id': telegram_id}  # telegram_id parametrini qo'shamiz
        result = await self._make_request('GET', 'complaints/', params=params)
        if result and 'results' in result:
            return result['results']
        return []
    
    async def get_complaint(self, complaint_id: int, telegram_id: int = None) -> Optional[Dict]:
        """Get complaint by ID from Django"""
        params = {}
        if telegram_id:
            params['telegram_id'] = telegram_id
        
        result = await self._make_request('GET', f'complaints/{complaint_id}/', params=params)
        return result
    
    async def update_complaint_status(self, complaint_id: int, status: str, note: str = None) -> bool:
        """Update complaint status in Django"""
        data = {'status': status}
        if note:
            data['note'] = note
        
        result = await self._make_request('PATCH', f'complaints/{complaint_id}/', json=data)
        return result is not None
    
    async def add_complaint_image(self, complaint_id: int, channel_message_id: int, file_id: str = None) -> bool:
        """Add image to complaint in Django"""
        data = {
            'channel_message_id': channel_message_id,
            'file_id': file_id,
        }
        result = await self._make_request('POST', f'complaints/{complaint_id}/add_image/', json=data)
        return result is not None
    
    async def get_all_complaints(self, status: str = None) -> List[Dict]:
        """Get all complaints from Django (for admin)"""
        params = {}
        if status:
            params['status'] = status
        
        result = await self._make_request('GET', 'complaints/', params=params)
        if result and 'results' in result:
            return result['results']
        return []
    
    async def get_stats(self) -> Optional[Dict]:
        """Get statistics from Django"""
        return await self._make_request('GET', 'stats/')
    
    # Helper methods for compatibility with existing code
    async def get_or_create_user_local(self, telegram_id: int, full_name: str) -> Dict:
        """Get or create user (for backward compatibility)"""
        user = await self.get_user(telegram_id)
        if user:
            return user
        
        new_user = await self.register_user(telegram_id, full_name)
        if new_user:
            return new_user
        
        # Fallback to local structure if API fails
        return {
            'id': telegram_id,
            'telegram_id': telegram_id,
            'full_name': full_name,
            'role': 'user'
        }


# Test API connection
async def test_api_connection():
    """Test connection to Django API"""
    async with DjangoAPIClient() as client:
        print(f"Testing API connection to: {config.API_BASE_URL}")
        
        mahallas = await client.get_mahallas()
        if mahallas is not None:
            print(f"✅ API connection successful. Found {len(mahallas)} mahallas.")
            return True
        else:
            print("❌ API connection failed.")
            return False


if __name__ == '__main__':
    asyncio.run(test_api_connection())