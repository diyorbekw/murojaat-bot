"""
Complaint viewing and management handlers with Django API
with multimedia support and media viewing
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards.inline import (
    get_complaint_list_keyboard,
    get_complaint_detail_keyboard,
    get_image_navigation_keyboard,
    get_status_change_keyboard
)
from bot.keyboards.reply import get_back_to_menu_keyboard
from bot.api_client import DjangoAPIClient
from bot.config import config
from bot.utils.permissions import is_admin

router = Router(name="complaint_view")


@router.message(F.text == "📋 Mening murojaatlarim")
async def show_my_complaints(message: Message):
    """
    Show user's complaints list from Django API with pagination
    """
    async with DjangoAPIClient() as client:
        # Get user's complaints from Django API
        complaints = await client.get_user_complaints(message.from_user.id)
    
    if not complaints:
        await message.answer(
            "Siz hali hech qanday murojaat yaratmagansiz.\n"
            "Yangi murojaat yaratish uchun '📝 Muammo yuborish' tugmasini bosing.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Format complaints list with subcategory if available
    text = "📋 <b>Sizning murojaatlaringiz:</b>\n\n"
    
    for complaint in complaints[:5]:  # Show first 5 complaints initially
        complaint_id = complaint.get('id', 'N/A')
        status = complaint.get('status', 'new')
        status_emoji = "🆕" if status == "new" else "🔄" if status == "in_progress" else "✅" if status == "solved" else "⏳"
        
        # Get category name
        category = complaint.get('category', {})
        if isinstance(category, dict):
            category_name = category.get('name', 'Noma\'lum')
        else:
            category_name = str(category)
        
        # Get subcategory title
        subcategory = complaint.get('subcategory', {})
        if isinstance(subcategory, dict):
            subcategory_title = subcategory.get('title', '')
        else:
            subcategory_title = str(subcategory) if subcategory else ''
        
        # Get media count
        images = complaint.get('images', [])
        media_count = len(images) if images else 0
        media_emoji = "📷" if media_count > 0 else ""
        media_text = f" {media_emoji}" if media_count > 0 else ""
        
        # Prepare display text
        display_text = f"#{complaint_id} | {category_name}"
        if subcategory_title:
            if len(subcategory_title) > 20:
                subcategory_title = subcategory_title[:17] + "..."
            display_text += f" - {subcategory_title}"
        
        display_text += f" {status_emoji}{media_text}"
        
        text += f"{display_text}\n"
    
    if len(complaints) > 5:
        text += f"\n... va yana {len(complaints) - 5} ta murojaat\n"
    
    text += "\nBatafsil ko'rish uchun murojaatni tanlang:"
    
    await message.answer(
        text,
        reply_markup=get_complaint_list_keyboard(complaints[:5], offset=0, limit=5),
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
    
    if not complaints:
        try:
            await callback.message.edit_text(
                "Murojaatlar topilmadi.",
                reply_markup=None
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Murojaatlar topilmadi.",
                reply_markup=None
            )
        return
    
    # Pagination logic
    start_idx = offset
    end_idx = start_idx + 5
    paginated_complaints = complaints[start_idx:end_idx]
    
    if not paginated_complaints:
        try:
            await callback.message.edit_text(
                "Boshqa murojaatlar topilmadi.",
                reply_markup=None
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Boshqa murojaatlar topilmadi.",
                reply_markup=None
            )
        return
    
    # Format complaints list with subcategory if available
    text = "📋 <b>Sizning murojaatlaringiz:</b>\n\n"
    
    for complaint in paginated_complaints:
        complaint_id = complaint.get('id', 'N/A')
        status = complaint.get('status', 'new')
        status_emoji = "🆕" if status == "new" else "🔄" if status == "in_progress" else "✅" if status == "solved" else "⏳"
        
        # Get category name
        category = complaint.get('category', {})
        if isinstance(category, dict):
            category_name = category.get('name', 'Noma\'lum')
        else:
            category_name = str(category)
        
        # Get subcategory title
        subcategory = complaint.get('subcategory', {})
        if isinstance(subcategory, dict):
            subcategory_title = subcategory.get('title', '')
        else:
            subcategory_title = str(subcategory) if subcategory else ''
        
        # Get media count
        images = complaint.get('images', [])
        media_count = len(images) if images else 0
        media_emoji = "📷" if media_count > 0 else ""
        media_text = f" {media_emoji}" if media_count > 0 else ""
        
        # Prepare display text
        display_text = f"#{complaint_id} | {category_name}"
        if subcategory_title:
            if len(subcategory_title) > 20:
                subcategory_title = subcategory_title[:17] + "..."
            display_text += f" - {subcategory_title}"
        
        display_text += f" {status_emoji}{media_text}"
        
        text += f"{display_text}\n"
    
    if len(complaints) > end_idx:
        text += f"\n... va yana {len(complaints) - end_idx} ta murojaat\n"
    
    text += "\nBatafsil ko'rish uchun murojaatni tanlang:"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_complaint_list_keyboard(paginated_complaints, offset, limit=5),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        # Send new message if editing fails
        await callback.message.answer(
            text,
            reply_markup=get_complaint_list_keyboard(paginated_complaints, offset, limit=5),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("view_complaint:"))
async def view_complaint_detail(callback: CallbackQuery):
    """
    View complaint details with subcategory and media support
    """
    await callback.answer()
    
    complaint_id = int(callback.data.split(":")[1])
    
    async with DjangoAPIClient() as client:
        # Get complaint details with user's telegram_id for permission check
        complaint = await client.get_complaint_details(complaint_id, callback.from_user.id)
    
    if not complaint:
        try:
            await callback.message.edit_text(
                "Murojaat topilmadi yoki siz unga kirish huquqiga ega emassiz."
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Murojaat topilmadi yoki siz unga kirish huquqiga ega emassiz."
            )
        return
    
    # Format complaint details with subcategory
    status = complaint.get('status', 'new')
    status_text = config.STATUSES.get(status, status)
    
    created_at = complaint.get('created_at', 'Noma\'lum')
    if created_at != 'Noma\'lum' and len(created_at) > 10:
        created_at = created_at[:10]
    
    # Get user info
    user = complaint.get('user', {})
    if isinstance(user, dict):
        user_name = user.get('full_name', 'Noma\'lum')
    else:
        user_name = str(user)
    
    # Get mahalla info
    mahalla = complaint.get('mahalla', {})
    if isinstance(mahalla, dict):
        mahalla_name = mahalla.get('name', 'Noma\'lum')
    else:
        mahalla_name = str(mahalla)
    
    # Get category info
    category = complaint.get('category', {})
    if isinstance(category, dict):
        category_name = category.get('name', 'Noma\'lum')
    else:
        category_name = str(category)
    
    # Get subcategory info
    subcategory = complaint.get('subcategory', {})
    subcategory_title = ''
    if isinstance(subcategory, dict):
        subcategory_title = subcategory.get('title', '')
    elif subcategory:
        subcategory_title = str(subcategory)
    
    description = complaint.get('description', 'Tavsif yo\'q')
    
    # Get media count
    images = complaint.get('images', [])
    media_count = len(images) if images else 0
    
    # Build text with subcategory
    text = (
        f"📄 <b>Murojaat #{complaint['id']}</b>\n\n"
        f"<b>Foydalanuvchi:</b> {user_name}\n"
        f"<b>Mahalla:</b> {mahalla_name}\n"
        f"<b>Muammo turi:</b> {category_name}\n"
    )
    
    if subcategory_title:
        text += f"<b>Aniq turi:</b> {subcategory_title}\n"
    
    text += (
        f"<b>Holati:</b> {status_text}\n"
        f"<b>Yaratilgan:</b> {created_at}\n"
        f"<b>Media fayllar:</b> {media_count} ta\n\n"
        f"<b>Tavsif:</b>\n{description}\n\n"
    )
    
    text += f"<b>ID:</b> <code>{complaint['id']}</code>"
    
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
    
    # Re-fetch complaints
    async with DjangoAPIClient() as client:
        complaints = await client.get_user_complaints(callback.from_user.id)
    
    if not complaints:
        try:
            await callback.message.edit_text(
                "Murojaatlar topilmadi.",
                reply_markup=None
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Murojaatlar topilmadi.",
                reply_markup=None
            )
        return
    
    # Format complaints list
    text = "📋 <b>Sizning murojaatlaringiz:</b>\n\n"
    
    for complaint in complaints[:5]:
        complaint_id = complaint.get('id', 'N/A')
        status = complaint.get('status', 'new')
        status_emoji = "🆕" if status == "new" else "🔄" if status == "in_progress" else "✅" if status == "solved" else "⏳"
        
        category = complaint.get('category', {})
        if isinstance(category, dict):
            category_name = category.get('name', 'Noma\'lum')
        else:
            category_name = str(category)
        
        subcategory = complaint.get('subcategory', {})
        if isinstance(subcategory, dict):
            subcategory_title = subcategory.get('title', '')
        else:
            subcategory_title = str(subcategory) if subcategory else ''
        
        # Get media count
        images = complaint.get('images', [])
        media_count = len(images) if images else 0
        media_emoji = "📷" if media_count > 0 else ""
        media_text = f" {media_emoji}" if media_count > 0 else ""
        
        display_text = f"#{complaint_id} | {category_name}"
        if subcategory_title:
            if len(subcategory_title) > 20:
                subcategory_title = subcategory_title[:17] + "..."
            display_text += f" - {subcategory_title}"
        
        display_text += f" {status_emoji}{media_text}"
        
        text += f"{display_text}\n"
    
    if len(complaints) > 5:
        text += f"\n... va yana {len(complaints) - 5} ta murojaat\n"
    
    text += "\nBatafsil ko'rish uchun murojaatni tanlang:"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_complaint_list_keyboard(complaints[:5], offset=0, limit=5),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=get_complaint_list_keyboard(complaints[:5], offset=0, limit=5),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("view_media:"))
async def view_complaint_media(callback: CallbackQuery, bot):
    """
    View complaint media files
    """
    await callback.answer()
    
    complaint_id = int(callback.data.split(":")[1])
    
    async with DjangoAPIClient() as client:
        # Get complaint details
        complaint = await client.get_complaint_details(complaint_id, callback.from_user.id)
    
    if not complaint:
        try:
            await callback.message.edit_text("Murojaat topilmadi yoki siz unga kirish huquqiga ega emassiz.")
        except TelegramBadRequest:
            await callback.message.answer("Murojaat topilmadi yoki siz unga kirish huquqiga ega emassiz.")
        return
    
    # Get media from complaint
    media_list = complaint.get('images', [])
    
    if not media_list:
        await callback.message.answer(
            "Bu murojaat uchun hech qanday media fayl yuklanmagan."
        )
        return
    
    # Group media by type for better display
    photos = []
    videos = []
    voices = []
    video_notes = []
    
    for media_item in media_list:
        if isinstance(media_item, dict):
            file_type = media_item.get('file_type', '')
            if file_type in ['photo', 'document_image']:
                photos.append(media_item)
            elif file_type == 'video':
                videos.append(media_item)
            elif file_type == 'voice':
                voices.append(media_item)
            elif file_type == 'video_note':
                video_notes.append(media_item)
    
    # Send media summary
    summary_text = (
        f"📄 <b>Murojaat #{complaint_id} media fayllari:</b>\n\n"
        f"📷 Rasmlar: {len(photos)} ta\n"
        f"🎥 Videolar: {len(videos)} ta\n"
        f"🎙️ Ovozli xabarlar: {len(voices)} ta\n"
        f"🎬 Dumaloq videolar: {len(video_notes)} ta\n\n"
        "Quyidagi tugmalardan media turini tanlang:"
    )
    
    # Create media type selection keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    if photos:
        builder.button(
            text=f"📷 Rasmlar ({len(photos)} ta)",
            callback_data=f"view_media_type:{complaint_id}:photos:0"
        )
    
    if videos:
        builder.button(
            text=f"🎥 Videolar ({len(videos)} ta)",
            callback_data=f"view_media_type:{complaint_id}:videos:0"
        )
    
    if voices:
        builder.button(
            text=f"🎙️ Ovozlar ({len(voices)} ta)",
            callback_data=f"view_media_type:{complaint_id}:voices:0"
        )
    
    if video_notes:
        builder.button(
            text=f"🎬 Dumaloq videolar ({len(video_notes)} ta)",
            callback_data=f"view_media_type:{complaint_id}:video_notes:0"
        )
    
    builder.button(
        text="🔙 Orqaga",
        callback_data=f"view_complaint:{complaint_id}"
    )
    
    builder.adjust(1)
    
    try:
        await callback.message.edit_text(
            summary_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            summary_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("view_media_type:"))
async def view_media_by_type(callback: CallbackQuery, bot):
    """
    View specific type of media
    """
    await callback.answer()
    
    try:
        _, complaint_id, media_type, index = callback.data.split(":")
        complaint_id = int(complaint_id)
        index = int(index)
    except ValueError:
        await callback.answer("Xatolik: noto'g'ri format", show_alert=True)
        return
    
    async with DjangoAPIClient() as client:
        complaint = await client.get_complaint_details(complaint_id, callback.from_user.id)
    
    if not complaint:
        try:
            await callback.message.edit_text("Murojaat topilmadi.")
        except TelegramBadRequest:
            await callback.message.answer("Murojaat topilmadi.")
        return
    
    media_list = complaint.get('images', [])
    
    # Filter media by type
    filtered_media = []
    for media_item in media_list:
        if isinstance(media_item, dict):
            file_type = media_item.get('file_type', '')
            if media_type == 'photos' and file_type in ['photo', 'document_image']:
                filtered_media.append(media_item)
            elif media_type == 'videos' and file_type == 'video':
                filtered_media.append(media_item)
            elif media_type == 'voices' and file_type == 'voice':
                filtered_media.append(media_item)
            elif media_type == 'video_notes' and file_type == 'video_note':
                filtered_media.append(media_item)
    
    if not filtered_media or index >= len(filtered_media):
        await callback.answer("Media topilmadi", show_alert=True)
        return
    
    # Get the media item
    media_item = filtered_media[index]
    
    # Create navigation keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    # Previous button
    if index > 0:
        builder.button(
            text="◀️ Oldingi",
            callback_data=f"view_media_type:{complaint_id}:{media_type}:{index - 1}"
        )
    
    # Counter
    builder.button(
        text=f"{index + 1}/{len(filtered_media)}",
        callback_data="no_action"
    )
    
    # Next button
    if index < len(filtered_media) - 1:
        builder.button(
            text="Keyingi ▶️",
            callback_data=f"view_media_type:{complaint_id}:{media_type}:{index + 1}"
        )
    
    builder.button(
        text="🔙 Media ro'yxatiga qaytish",
        callback_data=f"view_media:{complaint_id}"
    )
    
    builder.adjust(3)
    
    try:
        # Delete previous message
        await callback.message.delete()
    except:
        pass
    
    # Try to forward media from channel
    try:
        channel_message_id = media_item.get('channel_message_id')
        if channel_message_id:
            await bot.copy_message(
                chat_id=callback.from_user.id,
                from_chat_id=config.CHANNEL_ID,
                message_id=channel_message_id,
                reply_markup=builder.as_markup()
            )
        else:
            # Fallback: send a message with media info
            file_type = media_item.get('file_type', 'unknown')
            type_names = {
                'photo': 'Rasm', 'document_image': 'Rasm (fayl)',
                'video': 'Video', 'voice': 'Ovozli xabar',
                'video_note': 'Dumaloq video'
            }
            
            await callback.message.answer(
                f"📁 <b>Media fayl</b>\n\n"
                f"<b>Tur:</b> {type_names.get(file_type, file_type)}\n"
                f"<b>ID:</b> {media_item.get('id', 'N/A')}\n\n"
                f"⚠️ Asl media faylni ko'rsatishda muammo yuz berdi.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Error displaying media: {e}")
        await callback.message.answer(
            f"❌ Media faylni yuklashda xatolik yuz berdi.\n\n"
            f"Xato: {str(e)}",
            reply_markup=builder.as_markup()
        )


# Admin functionality for status change
@router.callback_query(F.data.startswith("change_status:"))
async def change_status_prompt(callback: CallbackQuery):
    """
    Show status change options for admin
    """
    await callback.answer()
    
    complaint_id = int(callback.data.split(":")[1])
    
    is_user_admin = await is_admin(callback.from_user)
    if not is_user_admin:
        await callback.answer("Siz admin emassiz", show_alert=True)
        return
    
    text = f"📋 <b>Murojaat #{complaint_id} holatini o'zgartirish</b>\n\n"
    text += "Quyidagi holatlardan birini tanlang:"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_status_change_keyboard(complaint_id),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=get_status_change_keyboard(complaint_id),
            parse_mode="HTML"
        )