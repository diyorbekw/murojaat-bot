"""
Permission and role checking utilities
"""

from typing import Optional
from aiogram.types import User as TelegramUser

from bot.config import config
from bot.database.db import db


async def is_admin(telegram_user: TelegramUser) -> bool:
    """
    Check if user is admin by Telegram ID
    
    Args:
        telegram_user: Telegram user object
        
    Returns:
        bool: True if user is admin
    """
    # Check predefined admin IDs
    if telegram_user.id in config.ADMIN_IDS:
        return True
    
    # Check database role
    user = db.get_user_by_telegram_id(telegram_user.id)
    return user and user["role"] == "admin"


async def get_user_role(telegram_user: TelegramUser) -> str:
    """
    Get user role
    
    Args:
        telegram_user: Telegram user object
        
    Returns:
        str: User role (admin/user)
    """
    if telegram_user.id in config.ADMIN_IDS:
        return "admin"
    
    user = db.get_user_by_telegram_id(telegram_user.id)
    return user["role"] if user else "user"