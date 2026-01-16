"""
Bot configuration settings
"""

import os
from typing import Set
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for bot settings"""
    
    # Bot token from environment variable
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Django API configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000/api/")
    
    # Channel ID for storing images (must be public or bot must be admin)
    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "-1003690999820"))

    # Group ID for user complaints
    GROUP_ID: int = int(os.getenv("GROUP_ID", "-5202556656"))

    # Admin Telegram IDs (comma-separated in env)
    admin_ids_str = os.getenv("ADMIN_IDS", "7612526446")
    ADMIN_IDS: Set[int] = set(
        int(id.strip()) for id in admin_ids_str.split(",") if id.strip()
    )
    
    # Database file path (hozircha SQLite ishlatamiz, keyin API ga o'tamiz)
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "complaints.db")
    
    # Complaint statuses with emojis
    STATUSES: dict[str, str] = {
        "new": "🆕 Yangi",
        "in_progress": "🔄 Jarayonda",
        "solved": "✅ Hal qilindi",
        "delayed": "⏳ Kehtirildi"
    }
    
    # Default mahallas and categories (API dan olinadi, lekin fallback uchun)
    DEFAULT_MAHALLAS: list[str] = [
        "1-Mahalla", "2-Mahalla", "3-Mahalla", "4-Mahalla", "5-Mahalla",
        "6-Mahalla", "7-Mahalla", "8-Mahalla", "9-Mahalla", "10-Mahalla"
    ]
    
    DEFAULT_CATEGORIES: list[str] = [
        "Elektr", "Suv", "Yo'l", "Tibbiyot", "Toza",
        "Gaz", "Telekom", "Transport", "Boshqa"
    ]


config = Config()