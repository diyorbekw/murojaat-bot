"""
Reply keyboard markup builders
"""

from typing import List, Optional
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.config import config


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create main menu keyboard for regular users
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(
        KeyboardButton(text="📝 Muammo yuborish"),
        KeyboardButton(text="📋 Mening murojaatlarim")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create main menu keyboard for admin users
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(
        KeyboardButton(text="📝 Muammo yuborish"),
        KeyboardButton(text="📋 Mening murojaatlarim"),
        KeyboardButton(text="👨‍💻 Barcha murojaatlar"),
        KeyboardButton(text="📊 Statistika")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_mahalla_keyboard(mahallas: List[str] = None) -> ReplyKeyboardMarkup:
    """
    Create keyboard for mahalla selection
    
    Args:
        mahallas: List of mahalla names (if None, use defaults)
    """
    builder = ReplyKeyboardBuilder()
    
    if mahallas is None:
        mahallas = config.DEFAULT_MAHALLAS
    
    for mahalla in mahallas:
        builder.add(KeyboardButton(text=mahalla))
    
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_category_keyboard(categories: List[str] = None) -> ReplyKeyboardMarkup:
    """
    Create keyboard for category selection
    
    Args:
        categories: List of category names (if None, use defaults)
    """
    builder = ReplyKeyboardBuilder()
    
    if categories is None:
        categories = config.DEFAULT_CATEGORIES
    
    for category in categories:
        builder.add(KeyboardButton(text=category))
    
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_subcategory_keyboard(subcategories: List[str] = None) -> ReplyKeyboardMarkup:
    """
    Create keyboard for subcategory selection
    
    Args:
        subcategories: List of subcategory names
    """
    builder = ReplyKeyboardBuilder()
    
    if not subcategories:
        return get_cancel_keyboard()
    
    for subcat in subcategories:
        builder.add(KeyboardButton(text=subcat))
    
    builder.add(KeyboardButton(text="✏️ Boshqa"))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    
    builder.adjust(1)  # One button per row
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_images_keyboard() -> ReplyKeyboardMarkup:
    """
    Create keyboard for image submission step
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(
        KeyboardButton(text="✅ Yuborish"),
        KeyboardButton(text="❌ Bekor qilish")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Create cancel-only keyboard
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    
    return builder.as_markup(resize_keyboard=True)


def get_back_to_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create back to menu keyboard
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="🏠 Bosh menyu"))
    
    return builder.as_markup(resize_keyboard=True)


# Remove keyboard utility
remove_keyboard = ReplyKeyboardRemove()

def get_media_keyboard() -> ReplyKeyboardMarkup:
    """
    Create keyboard for media submission step
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(
        KeyboardButton(text="✅ Yuborish"),
        KeyboardButton(text="❌ Bekor qilish")
    )
    
    return builder.as_markup(resize_keyboard=True)

def get_urgent_keyboard() -> ReplyKeyboardMarkup:
    """
    Create keyboard for urgent notification confirmation
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(
        KeyboardButton(text="✅ Ha"),
        KeyboardButton(text="❌ Yo'q")
    )
    
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_location_keyboard() -> ReplyKeyboardMarkup:
    """
    Create keyboard for location sharing
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(
        KeyboardButton(text="📍 Lokatsiyamni yuborish", request_location=True)
    )
    
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)