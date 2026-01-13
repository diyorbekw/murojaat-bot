"""
Admin handlers for complaint management
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import (
    get_complaint_list_keyboard,
    get_complaint_detail_keyboard,
    get_status_change_keyboard
)
from bot.keyboards.reply import get_back_to_menu_keyboard
from bot.database.db import db
from bot.config import config
from bot.utils.permissions import is_admin

router = Router(name="admin")


@router.message(F.text == "👨‍💻 Barcha murojaatlar")
async def show_all_complaints(message: Message):
    """
    Show all complaints (admin only)
    """
    # Check if user is admin
    if not await is_admin(message.from_user):
        await message.answer(
            "Bu buyruq faqat administratorlar uchun.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Get all complaints
    complaints = db.get_all_complaints(limit=5)
    
    if not complaints:
        await message.answer(
            "Hozircha hech qanday murojaat yo'q.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Format complaints list
    text = "👨‍💻 <b>Barcha murojaatlar:</b>\n\n"
    
    for complaint in complaints:
        status_emoji = "🆕" if complaint["status"] == "new" else "🔄" if complaint["status"] == "in_progress" else "✅" if complaint["status"] == "solved" else "⏳"
        text += f"#{complaint['id']} | {complaint['full_name']} | {complaint['category']} {status_emoji}\n"
    
    text += "\nBatafsil ko'rish uchun murojaatni tanlang:"
    
    await message.answer(
        text,
        reply_markup=get_complaint_list_keyboard(complaints),
        parse_mode="HTML"
    )


@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    """
    Show complaint statistics (admin only)
    """
    # Check if user is admin
    if not await is_admin(message.from_user):
        await message.answer(
            "Bu buyruq faqat administratorlar uchun.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Get statistics
    stats = db.get_complaint_count()
    total = sum(stats.values())
    
    # Format statistics
    text = "📊 <b>Umumiy statistika:</b>\n\n"
    text += f"<b>Jami murojaatlar:</b> {total} ta\n\n"
    
    for status_key, status_text in config.STATUSES.items():
        count = stats.get(status_key, 0)
        percentage = (count / total * 100) if total > 0 else 0
        text += f"{status_text}: {count} ta ({percentage:.1f}%)\n"
    
    # Get today's complaints (simplified)
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM complaints WHERE DATE(created_at) = DATE('now')"
        )
        today_count = cursor.fetchone()[0]
    
    text += f"\n<b>Bugungi murojaatlar:</b> {today_count} ta"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(F.data.startswith("change_status:"))
async def change_complaint_status(callback: CallbackQuery):
    """
    Start changing complaint status (admin only)
    """
    await callback.answer()
    
    # Check if user is admin
    if not await is_admin(callback.from_user):
        await callback.message.edit_text(
            "Bu amal faqat administratorlar uchun."
        )
        return
    
    complaint_id = int(callback.data.split(":")[1])
    complaint = db.get_complaint(complaint_id)
    
    if not complaint:
        await callback.message.edit_text("Murojaat topilmadi.")
        return
    
    text = (
        f"✏️ <b>Murojaat holatini o'zgartirish</b>\n\n"
        f"<b>Murojaat:</b> #{complaint_id}\n"
        f"<b>Joriy holat:</b> {config.STATUSES.get(complaint['status'], complaint['status'])}\n\n"
        f"Yangi holatni tanlang:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_status_change_keyboard(complaint_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("set_status:"))
async def set_complaint_status(callback: CallbackQuery):
    """
    Set new complaint status (admin only)
    """
    await callback.answer()
    
    # Check if user is admin
    if not await is_admin(callback.from_user):
        await callback.message.edit_text(
            "Bu amal faqat administratorlar uchun."
        )
        return
    
    _, complaint_id, new_status = callback.data.split(":")
    complaint_id = int(complaint_id)
    
    # Update status in database
    success = db.update_complaint_status(complaint_id, new_status)
    
    if not success:
        await callback.message.edit_text(
            "Murojaat holatini o'zgartirishda xatolik yuz berdi."
        )
        return
    
    # Get updated complaint
    complaint = db.get_complaint(complaint_id)
    
    if not complaint:
        await callback.message.edit_text("Murojaat topilmadi.")
        return
    
    # Format confirmation message
    status_text = config.STATUSES.get(new_status, new_status)
    
    text = (
        f"✅ <b>Murojaat holati o'zgartirildi!</b>\n\n"
        f"<b>Murojaat:</b> #{complaint_id}\n"
        f"<b>Yangi holat:</b> {status_text}\n\n"
        f"<b>Foydalanuvchi:</b> {complaint['full_name']}\n"
        f"<b>Mahalla:</b> {complaint['mahalla']}\n"
        f"<b>Muammo turi:</b> {complaint['category']}"
    )
    
    # Update message
    await callback.message.edit_text(
        text,
        reply_markup=get_complaint_detail_keyboard(complaint_id, is_admin=True),
        parse_mode="HTML"
    )
    
    # Notify user about status change
    try:
        from bot.main import bot
        
        user_notification = (
            f"📢 <b>Murojaatingiz holati o'zgartirildi!</b>\n\n"
            f"<b>Murojaat raqami:</b> #{complaint_id}\n"
            f"<b>Yangi holat:</b> {status_text}\n\n"
            f"<b>Muammo turi:</b> {complaint['category']}\n"
            f"<b>Mahalla:</b> {complaint['mahalla']}\n\n"
            f"Batafsil ma'lumot: /start"
        )
        
        await bot.send_message(
            chat_id=complaint['telegram_id'],
            text=user_notification,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Error notifying user: {e}")


# Admin pagination for all complaints
@router.callback_query(F.data.startswith("list_complaints:"))
async def handle_admin_complaint_list_pagination(callback: CallbackQuery):
    """
    Handle admin complaint list pagination
    """
    await callback.answer()
    
    # Check if user is admin
    if not await is_admin(callback.from_user):
        await callback.message.edit_text(
            "Bu amal faqat administratorlar uchun."
        )
        return
    
    offset = int(callback.data.split(":")[1])
    complaints = db.get_all_complaints(limit=5, offset=offset)
    
    if not complaints:
        await callback.message.edit_text(
            "Boshqa murojaatlar topilmadi.",
            reply_markup=None
        )
        return
    
    text = "👨‍💻 <b>Barcha murojaatlar:</b>\n\n"
    
    for complaint in complaints:
        status_emoji = "🆕" if complaint["status"] == "new" else "🔄" if complaint["status"] == "in_progress" else "✅" if complaint["status"] == "solved" else "⏳"
        text += f"#{complaint['id']} | {complaint['full_name']} | {complaint['category']} {status_emoji}\n"
    
    text += "\nBatafsil ko'rish uchun murojaatni tanlang:"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_complaint_list_keyboard(complaints, offset),
            parse_mode="HTML"
        )
    except:
        # If editing fails, send new message
        await callback.message.answer(
            text,
            reply_markup=get_complaint_list_keyboard(complaints, offset),
            parse_mode="HTML"
        )