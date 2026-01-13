"""
Complaint viewing and management handlers with Django API
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards.inline import (
    get_complaint_list_keyboard,
    get_complaint_detail_keyboard,
    get_image_navigation_keyboard
)
from bot.keyboards.reply import get_back_to_menu_keyboard
from bot.api_client import DjangoAPIClient
from bot.config import config
from bot.utils.permissions import is_admin

router = Router(name="complaint_view")


@router.message(F.text == "📋 Mening murojaatlarim")
async def show_my_complaints(message: Message):
    """
    Show user's complaints list from Django API
    """
    async with DjangoAPIClient() as client:
        # Get user's complaints from Django API with telegram_id parameter
        complaints = await client.get_user_complaints(message.from_user.id)
    
    if not complaints:
        await message.answer(
            "Siz hali hech qanday murojaat yaratmagansiz.\n"
            "Yangi murojaat yaratish uchun '📝 Muammo yuborish' tugmasini bosing.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Format complaints list
    text = "📋 <b>Sizning murojaatlaringiz:</b>\n\n"
    
    for complaint in complaints:
        status = complaint.get('status', 'new')
        status_emoji = "🆕" if status == "new" else "🔄" if status == "in_progress" else "✅" if status == "solved" else "⏳"
        category = complaint.get('category', {}).get('name', 'Noma\'lum') if isinstance(complaint.get('category'), dict) else complaint.get('category', 'Noma\'lum')
        mahalla = complaint.get('mahalla', {}).get('name', 'Noma\'lum') if isinstance(complaint.get('mahalla'), dict) else complaint.get('mahalla', 'Noma\'lum')
        text += f"#{complaint['id']} | {category} | {mahalla} {status_emoji}\n"
    
    text += "\nBatafsil ko'rish uchun murojaatni tanlang:"
    
    await message.answer(
        text,
        reply_markup=get_complaint_list_keyboard(complaints),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("list_complaints:"))
async def handle_complaint_list_pagination(callback: CallbackQuery):
    """
    Handle complaint list pagination
    """
    await callback.answer()
    
    offset = int(callback.data.split(":")[1])
    
    async with DjangoAPIClient() as client:
        complaints = await client.get_user_complaints(callback.from_user.id)
    
    # Simple pagination (API dan to'g'ri pagination bo'lsa yaxshi)
    if not complaints:
        await callback.message.edit_text(
            "Boshqa murojaatlar topilmadi.",
            reply_markup=None
        )
        return
    
    # Simple pagination logic
    start_idx = offset
    end_idx = start_idx + 5
    paginated_complaints = complaints[start_idx:end_idx]
    
    if not paginated_complaints:
        await callback.message.edit_text(
            "Boshqa murojaatlar topilmadi.",
            reply_markup=None
        )
        return
    
    text = "📋 <b>Sizning murojaatlaringiz:</b>\n\n"
    
    for complaint in paginated_complaints:
        status = complaint.get('status', 'new')
        status_emoji = "🆕" if status == "new" else "🔄" if status == "in_progress" else "✅" if status == "solved" else "⏳"
        category = complaint.get('category', {}).get('name', 'Noma\'lum') if isinstance(complaint.get('category'), dict) else complaint.get('category', 'Noma\'lum')
        mahalla = complaint.get('mahalla', {}).get('name', 'Noma\'lum') if isinstance(complaint.get('mahalla'), dict) else complaint.get('mahalla', 'Noma\'lum')
        text += f"#{complaint['id']} | {category} | {mahalla} {status_emoji}\n"
    
    text += "\nBatafsil ko'rish uchun murojaatni tanlang:"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_complaint_list_keyboard(paginated_complaints, offset),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        # Message wasn't modified, ignore
        pass


@router.callback_query(F.data.startswith("view_complaint:"))
async def view_complaint_detail(callback: CallbackQuery):
    """
    View complaint details
    """
    await callback.answer()
    
    complaint_id = int(callback.data.split(":")[1])
    
    async with DjangoAPIClient() as client:
        # Get complaint with user's telegram_id for permission check
        complaint = await client.get_complaint(complaint_id, callback.from_user.id)
    
    if not complaint:
        await callback.message.edit_text(
            "Murojaat topilmadi yoki siz unga kirish huquqiga ega emassiz."
        )
        return
    
    # Format complaint details
    status = complaint.get('status', 'new')
    status_text = config.STATUSES.get(status, status)
    created_at = complaint.get('created_at', 'Noma\'lum')[:10] if complaint.get('created_at') else 'Noma\'lum'
    user_name = complaint.get('user', {}).get('full_name', 'Noma\'lum')
    mahalla_name = complaint.get('mahalla', {}).get('name', 'Noma\'lum') if isinstance(complaint.get('mahalla'), dict) else complaint.get('mahalla', 'Noma\'lum')
    category_name = complaint.get('category', {}).get('name', 'Noma\'lum') if isinstance(complaint.get('category'), dict) else complaint.get('category', 'Noma\'lum')
    description = complaint.get('description', 'Tavsif yo\'q')
    
    text = (
        f"📄 <b>Murojaat #{complaint['id']}</b>\n\n"
        f"<b>Foydalanuvchi:</b> {user_name}\n"
        f"<b>Mahalla:</b> {mahalla_name}\n"
        f"<b>Muammo turi:</b> {category_name}\n"
        f"<b>Holati:</b> {status_text}\n"
        f"<b>Yaratilgan:</b> {created_at}\n\n"
        f"<b>Tavsif:</b>\n{description}\n\n"
        f"<b>ID:</b> <code>{complaint['id']}</code>"
    )
    
    # Check if user is admin for admin buttons
    is_user_admin = await is_admin(callback.from_user)
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_complaint_detail_keyboard(complaint_id, is_user_admin),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        # Send new message if editing fails
        await callback.message.answer(
            text,
            reply_markup=get_complaint_detail_keyboard(complaint_id, is_user_admin),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "back_to_list")
async def back_to_complaint_list(callback: CallbackQuery):
    """
    Go back to complaint list
    """
    await callback.answer()
    await show_my_complaints(callback.message)


@router.callback_query(F.data.startswith("view_images:"))
async def view_complaint_images(callback: CallbackQuery, bot):
    """
    View complaint images
    """
    await callback.answer()
    
    complaint_id = int(callback.data.split(":")[1])
    
    async with DjangoAPIClient() as client:
        # Get complaint with user's telegram_id for permission check
        complaint = await client.get_complaint(complaint_id, callback.from_user.id)
    
    if not complaint:
        await callback.message.edit_text("Murojaat topilmadi yoki siz unga kirish huquqiga ega emassiz.")
        return
    
    # Get images from complaint
    images = complaint.get('images', [])
    
    if not images:
        await callback.message.answer(
            "Bu murojaat uchun hech qanday rasm yuklanmagan."
        )
        return
    
    # Send first image
    try:
        if images[0].get('channel_message_id'):
            await bot.copy_message(
                chat_id=callback.from_user.id,
                from_chat_id=config.CHANNEL_ID,
                message_id=images[0]['channel_message_id'],
                reply_markup=get_image_navigation_keyboard(complaint_id, 0, len(images))
            )
    except Exception as e:
        await callback.message.answer(
            f"Rasmlarni yuklashda xatolik: {str(e)}"
        )