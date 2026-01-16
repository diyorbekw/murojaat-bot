"""
Inline keyboard markup builders
"""

from typing import Dict, List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import config


def get_subcategory_inline_keyboard(subcategories: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for subcategory selection
    """
    builder = InlineKeyboardBuilder()
    
    # Add subcategory buttons (limit to 6 per row)
    for subcat in subcategories:
        title = subcat.get('title', '')
        if len(title) > 30:
            title = title[:27] + "..."
        
        builder.add(
            InlineKeyboardButton(
                text=title,
                callback_data=f"subcat:{subcat.get('title')}"
            )
        )
    
    builder.adjust(1)  # One button per row for readability
    
    builder.adjust(1)
    return builder.as_markup()


def get_complaint_list_keyboard(complaints: List[Dict], offset: int = 0, limit: int = 5) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for complaints list with pagination
    """
    builder = InlineKeyboardBuilder()
    
    # Add complaint buttons
    for complaint in complaints:
        complaint_id = complaint["id"]
        category = complaint.get('category', {})
        if isinstance(category, dict):
            category_name = category.get('name', 'Noma\'lum')
        else:
            category_name = str(category)
        
        status = complaint.get('status', 'new')
        status_emoji = "🆕" if status == "new" else "🔄" if status == "in_progress" else "✅" if status == "solved" else "⏳"
        
        button_text = f"#{complaint_id} | {category_name} {status_emoji}"
        if len(button_text) > 50:
            button_text = button_text[:47] + "..."
        
        builder.add(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_complaint:{complaint_id}"
            )
        )
    
    builder.adjust(1)  # One button per row
    
    # Add pagination if needed
    if offset > 0 or len(complaints) == limit:
        pagination_builder = InlineKeyboardBuilder()
        
        if offset > 0:
            pagination_builder.add(
                InlineKeyboardButton(
                    text="◀️ Oldingi",
                    callback_data=f"list_complaints:{offset - limit}"
                )
            )
        
        if len(complaints) == limit:
            pagination_builder.add(
                InlineKeyboardButton(
                    text="Keyingi ▶️",
                    callback_data=f"list_complaints:{offset + limit}"
                )
            )
        
        if pagination_builder.buttons:
            builder.attach(pagination_builder)
    
    return builder.as_markup()


def get_complaint_detail_keyboard(complaint_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for complaint details
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="📁 Media fayllar",
            callback_data=f"view_media:{complaint_id}"
        )
    )
    
    if is_admin:
        builder.add(
            InlineKeyboardButton(
                text="✏️ Statusni o'zgartirish",
                callback_data=f"change_status:{complaint_id}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="📋 Ro'yxatga qaytish",
            callback_data="back_to_list"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_status_change_keyboard(complaint_id: int) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for status change
    """
    builder = InlineKeyboardBuilder()
    
    for status_key, status_text in config.STATUSES.items():
        builder.add(
            InlineKeyboardButton(
                text=status_text,
                callback_data=f"set_status:{complaint_id}:{status_key}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"view_complaint:{complaint_id}"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_image_navigation_keyboard(complaint_id: int, image_index: int, total_images: int) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for image navigation
    """
    builder = InlineKeyboardBuilder()
    
    # Previous button
    if image_index > 0:
        builder.add(
            InlineKeyboardButton(
                text="◀️ Oldingi",
                callback_data=f"navigate_image:{complaint_id}:{image_index - 1}"
            )
        )
    
    # Counter
    builder.add(
        InlineKeyboardButton(
            text=f"{image_index + 1}/{total_images}",
            callback_data="no_action"
        )
    )
    
    # Next button
    if image_index < total_images - 1:
        builder.add(
            InlineKeyboardButton(
                text="Keyingi ▶️",
                callback_data=f"navigate_image:{complaint_id}:{image_index + 1}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"view_complaint:{complaint_id}"
        )
    )
    
    builder.adjust(3)
    return builder.as_markup()