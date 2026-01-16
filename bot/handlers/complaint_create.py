"""
Complaint creation handlers with FSM and Django API
with multimedia support (photo, voice, video, video_note)
and urgent notification option with location
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType, Location
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.states import ComplaintStates
from bot.keyboards.reply import (
    get_mahalla_keyboard,
    get_category_keyboard,
    get_subcategory_keyboard,
    get_media_keyboard,
    get_urgent_keyboard,
    get_location_keyboard,
    get_cancel_keyboard,
    remove_keyboard,
    get_back_to_menu_keyboard
)
from bot.keyboards.inline import get_subcategory_inline_keyboard
from bot.api_client import DjangoAPIClient
from bot.config import config

router = Router(name="complaint_create")


@router.message(F.text == "📝 Muammo yuborish")
async def start_complaint_creation(message: Message, state: FSMContext):
    """
    Start complaint creation process
    """
    # Check if user is already in some state
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(
            "Sizda davom etayotgan murojaat mavjud. "
            "Avval uni yakunlang yoki '❌ Bekor qilish' tugmasini bosing."
        )
        return
    
    async with DjangoAPIClient() as client:
        # Get mahallas from API
        mahallas_data = await client.get_mahallas()
        
        if not mahallas_data:
            # Use default mahallas if API fails
            mahalla_names = config.DEFAULT_MAHALLAS
        else:
            mahalla_names = [m['name'] for m in mahallas_data]
    
    # Store mahallas in state for later validation
    await state.update_data(available_mahallas=mahalla_names)
    
    await message.answer(
        "Yaxshi, yangi murojaat yaratamiz.\n\n"
        "1-qadam: <b>Mahallani tanlang:</b>",
        reply_markup=get_mahalla_keyboard(mahalla_names),
        parse_mode="HTML"
    )
    await state.set_state(ComplaintStates.waiting_for_mahalla)


@router.message(ComplaintStates.waiting_for_mahalla)
async def process_mahalla(message: Message, state: FSMContext):
    """
    Process selected mahalla
    """
    # Get available mahallas from state
    data = await state.get_data()
    available_mahallas = data.get('available_mahallas', config.DEFAULT_MAHALLAS)
    
    # Validate mahalla
    if message.text not in available_mahallas:
        await message.answer(
            "Iltimos, ro'yxatdan mahallani tanlang.",
            reply_markup=get_mahalla_keyboard(available_mahallas)
        )
        return
    
    await state.update_data(mahalla=message.text)
    
    async with DjangoAPIClient() as client:
        # Get categories from API
        categories_data = await client.get_categories()
        
        if not categories_data:
            # Use default categories if API fails
            category_names = config.DEFAULT_CATEGORIES
            category_dicts = [{'id': i+1, 'name': name} for i, name in enumerate(category_names)]
        else:
            category_names = [c['name'] for c in categories_data]
            category_dicts = categories_data
    
    # Store categories in state for later use
    await state.update_data(
        available_categories=category_names,
        categories_data=category_dicts
    )
    
    await message.answer(
        "2-qadam: <b>Muammo turini tanlang:</b>",
        reply_markup=get_category_keyboard(category_names),
        parse_mode="HTML"
    )
    await state.set_state(ComplaintStates.waiting_for_category)


@router.message(ComplaintStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    """
    Process selected category
    """
    # Get available categories from state
    data = await state.get_data()
    available_categories = data.get('available_categories', config.DEFAULT_CATEGORIES)
    categories_data = data.get('categories_data', [])
    
    # Validate category
    if message.text not in available_categories:
        await message.answer(
            "Iltimos, ro'yxatdan muammo turini tanlang.",
            reply_markup=get_category_keyboard(available_categories)
        )
        return
    
    # Find selected category data
    selected_category = None
    for cat in categories_data:
        if cat['name'] == message.text:
            selected_category = cat
            break
    
    if not selected_category:
        await message.answer(
            "Xatolik: tanlangan kategoriya topilmadi.",
            reply_markup=get_category_keyboard(available_categories)
        )
        return
    
    # Store category data in state
    await state.update_data(
        category=message.text,
        category_id=selected_category.get('id'),
        category_data=selected_category
    )
    
    async with DjangoAPIClient() as client:
        # Get subcategories for this category
        subcategories_data = await client.get_subcategories(selected_category.get('id'))
    
    if subcategories_data:
        # Store subcategories in state
        await state.update_data(subcategories_data=subcategories_data)
        
        # Show subcategories as inline buttons
        msg = await message.answer(text="Yuklanmoqda...", reply_markup=remove_keyboard)
        await msg.delete()
        
        await message.answer(
            "3-qadam: <b>Muammoning aniq turini tanlang:</b>\n\n"
            "Quyidagi tugmalardan birini tanlang yoki o'zingiz yozing:",
            reply_markup=get_subcategory_inline_keyboard(subcategories_data),
            parse_mode="HTML"
        )
        await state.set_state(ComplaintStates.waiting_for_subcategory)
    else:
        # No subcategories, skip to description
        await message.answer(
            "3-qadam: <b>Muammoni batafsil yozing:</b>\n\n"
            "Iltimos, muammoning joyi, vaqti va batafsil tavsifini yozing.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(ComplaintStates.waiting_for_description)


@router.callback_query(ComplaintStates.waiting_for_subcategory, F.data.startswith("subcat:"))
async def process_subcategory_selection(callback: CallbackQuery, state: FSMContext):
    """
    Process selected subcategory from inline keyboard
    """
    await callback.answer()
    
    subcategory_title = callback.data.split(":", 1)[1]
    
    # Get subcategories data from state
    data = await state.get_data()
    subcategories_data = data.get('subcategories_data', [])
    
    # Find the selected subcategory
    selected_subcategory = None
    for subcat in subcategories_data:
        if subcat['title'] == subcategory_title:
            selected_subcategory = subcat
            break
    
    if selected_subcategory:
        await state.update_data(
            subcategory=subcategory_title,
            subcategory_id=selected_subcategory.get('id')
        )
        
        await callback.message.edit_text(
            f"✅ Aniq tur tanlandi: <b>{subcategory_title}</b>\n\n"
            "4-qadam: <b>Muammoni batafsil yozing:</b>\n\n"
            "Iltimos, muammoning joyi, vaqti va batafsil tavsifini yozing.",
            parse_mode="HTML"
        )
        
        await callback.message.answer(
            "Yozishni boshlang yoki '❌ Bekor qilish' tugmasini bosing:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(ComplaintStates.waiting_for_description)
    else:
        await callback.answer("Xatolik: tanlangan subkategoriya topilmadi.", show_alert=True)


@router.message(ComplaintStates.waiting_for_subcategory)
async def process_custom_subcategory(message: Message, state: FSMContext):
    """
    Process custom subcategory entered by user
    """
    if message.text == "❌ Bekor qilish":
        await message.answer(
            "Murojaat yaratish bekor qilindi.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await state.clear()
        return
    
    # Store custom subcategory
    await state.update_data(
        subcategory=message.text,
        subcategory_id=None  # Custom subcategory, no ID
    )
    
    await message.answer(
        f"✅ Aniq tur tanlandi: <b>{message.text}</b>\n\n"
        "4-qadam: <b>Muammoni batafsil yozing:</b>\n\n"
        "Iltimos, muammoning joyi, vaqti va batafsil tavsifini yozing.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ComplaintStates.waiting_for_description)


@router.message(ComplaintStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """
    Process complaint description or handle cancel
    """
    if message.text == "❌ Bekor qilish":
        await message.answer(
            "Murojaat yaratish bekor qilindi.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await state.clear()
        return

    if len(message.text) < 10:
        await message.answer(
            "Iltimos, muammoni batafsilroq yozing (kamida 10 ta belgi).",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(description=message.text)
    
    await message.answer(
        "5-qadam: <b>Agar mavjud bo'lsa, media fayllar yuboring.</b>\n\n"
        "Qabul qilinadigan fayl turlari:\n"
        "📷 Rasm (photo)\n"
        "🎥 Video (video)\n"
        "🎙️ Ovozli xabar (voice)\n"
        "🎬 Dumaloq video (video_note)\n\n"
        "Bir nechta media yuborishingiz mumkin.\n"
        "Har bir media alohida xabar sifatida yuborilishi kerak.\n"
        "Medialarni yuborishni tugatgach, '✅ Yuborish' tugmasini bosing.\n\n"
        "Agar media yo'q bo'lsa, shunchaki '✅ Yuborish' tugmasini bosing.",
        reply_markup=get_media_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ComplaintStates.waiting_for_media)


@router.message(
    ComplaintStates.waiting_for_media,
    F.content_type.in_({
        ContentType.PHOTO, 
        ContentType.VIDEO, 
        ContentType.VOICE, 
        ContentType.VIDEO_NOTE,
        ContentType.DOCUMENT
    })
)
async def process_media(message: Message, state: FSMContext):
    """
    Process uploaded media (photo, video, voice, video_note)
    """
    # Get current media list or initialize
    data = await state.get_data()
    media = data.get("media", [])
    
    # Determine media type and store appropriate data
    media_item = {
        "message_id": message.message_id,
        "content_type": message.content_type,
        "date": message.date.isoformat() if message.date else None
    }
    
    if message.photo:
        # For photos, get the largest size
        file_id = message.photo[-1].file_id
        media_item.update({
            "file_id": file_id,
            "file_type": "photo",
            "caption": message.caption,
            "width": message.photo[-1].width,
            "height": message.photo[-1].height
        })
        media_type_emoji = "📷"
        media_type_text = "rasm"
        
    elif message.video:
        file_id = message.video.file_id
        media_item.update({
            "file_id": file_id,
            "file_type": "video",
            "caption": message.caption,
            "duration": message.video.duration,
            "width": message.video.width,
            "height": message.video.height,
            "mime_type": message.video.mime_type
        })
        media_type_emoji = "🎥"
        media_type_text = "video"
        
    elif message.voice:
        file_id = message.voice.file_id
        media_item.update({
            "file_id": file_id,
            "file_type": "voice",
            "duration": message.voice.duration,
            "mime_type": message.voice.mime_type
        })
        media_type_emoji = "🎙️"
        media_type_text = "ovozli xabar"
        
    elif message.video_note:
        file_id = message.video_note.file_id
        media_item.update({
            "file_id": file_id,
            "file_type": "video_note",
            "duration": message.video_note.duration,
            "length": message.video_note.length
        })
        media_type_emoji = "🎬"
        media_type_text = "dumaloq video"
        
    elif message.document:
        # Check if it's an image document
        if message.document.mime_type and message.document.mime_type.startswith("image/"):
            file_id = message.document.file_id
            media_item.update({
                "file_id": file_id,
                "file_type": "document_image",
                "caption": message.caption,
                "file_name": message.document.file_name,
                "mime_type": message.document.mime_type
            })
            media_type_emoji = "📷"
            media_type_text = "rasm (fayl)"
        else:
            await message.answer(
                "Iltimos, faqat rasm, video, ovoz yoki dumaloq video yuboring.",
                reply_markup=get_media_keyboard()
            )
            return
    else:
        return
    
    # Store the message object reference for forwarding
    media_item["message"] = message
    
    media.append(media_item)
    await state.update_data(media=media)
    
    # Count media by type
    media_counts = {}
    for item in media:
        media_type = item.get("file_type", "unknown")
        if media_type in media_counts:
            media_counts[media_type] += 1
        else:
            media_counts[media_type] = 1
    
    # Prepare summary text
    summary_parts = []
    type_emojis = {
        "photo": "📷", "document_image": "📷", 
        "video": "🎥", "voice": "🎙️", "video_note": "🎬"
    }
    
    for media_type, count in media_counts.items():
        emoji = type_emojis.get(media_type, "📁")
        if media_type == "photo":
            summary_parts.append(f"{emoji} {count} rasm")
        elif media_type == "document_image":
            summary_parts.append(f"{emoji} {count} rasm(fayl)")
        elif media_type == "video":
            summary_parts.append(f"{emoji} {count} video")
        elif media_type == "voice":
            summary_parts.append(f"{emoji} {count} ovoz")
        elif media_type == "video_note":
            summary_parts.append(f"{emoji} {count} dumaloq video")
    
    summary_text = ", ".join(summary_parts) if summary_parts else "hech qanday media"
    
    # Send confirmation
    await message.answer(
        f"✅ {media_type_emoji} {media_type_text} qabul qilindi.\n\n"
        f"📊 Jami media: {len(media)} ta\n"
        f"{summary_text}\n\n"
        "Yana media yuborishingiz yoki '✅ Yuborish' tugmasini bosishingiz mumkin.",
        reply_markup=get_media_keyboard()
    )


@router.message(ComplaintStates.waiting_for_media, F.text == "✅ Yuborish")
async def submit_complaint(message: Message, state: FSMContext, bot):
    """
    Ask about urgent notification before final submission
    """
    data = await state.get_data()
    
    # Check if user has added any media
    media_items = data.get("media", [])
    media_summary = ""
    if media_items:
        media_counts = {}
        for item in media_items:
            media_type = item.get("file_type", "unknown")
            if media_type in media_counts:
                media_counts[media_type] += 1
            else:
                media_counts[media_type] = 1
        
        media_summary_parts = []
        if media_counts.get("photo", 0) > 0:
            media_summary_parts.append(f"📷 {media_counts['photo']} rasm")
        if media_counts.get("document_image", 0) > 0:
            media_summary_parts.append(f"📷 {media_counts['document_image']} rasm(fayl)")
        if media_counts.get("video", 0) > 0:
            media_summary_parts.append(f"🎥 {media_counts['video']} video")
        if media_counts.get("voice", 0) > 0:
            media_summary_parts.append(f"🎙️ {media_counts['voice']} ovoz")
        if media_counts.get("video_note", 0) > 0:
            media_summary_parts.append(f"🎬 {media_counts['video_note']} dumaloq video")
        
        media_summary = ", ".join(media_summary_parts)
        total_media = sum(media_counts.values())
        media_info = f"\n📊 <b>Media fayllar:</b> {media_summary}\n<b>Jami media:</b> {total_media} ta"
    else:
        media_info = "\n📊 <b>Media fayllar:</b> yo'q"
    
    # Show summary and ask about urgent notification
    summary_text = (
        f"📝 <b>Murojaatning qisqacha mazmuni:</b>\n\n"
        f"<b>Mahalla:</b> {data['mahalla']}\n"
        f"<b>Muammo turi:</b> {data['category']}\n"
    )
    
    if data.get('subcategory'):
        summary_text += f"<b>Aniq turi:</b> {data['subcategory']}\n"
    
    summary_text += f"<b>Tavsif:</b> {data['description'][:100]}..."
    summary_text += media_info
    
    summary_text += (
        f"\n\n❓ <b>Tezkor xabar yuborilsinmi?</b>\n\n"
        "<i>Eslatma:</i> Tezkor xabar uchun lokatsiya yuborishingiz talab qilinadi."
    )
    
    await message.answer(
        summary_text,
        reply_markup=get_urgent_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ComplaintStates.waiting_for_urgent_confirm)


@router.message(ComplaintStates.waiting_for_urgent_confirm)
async def process_urgent_confirmation(message: Message, state: FSMContext, bot):
    """
    Process urgent confirmation - ask for location if urgent
    """
    user_response = message.text.strip().lower()
    
    # Simple check for yes/no responses
    if user_response in ['✅ ha', 'ha', 'ha✅', 'yes', 'yeah', 'h', '✅', 'ha tezkor']:
        is_urgent = True
    elif user_response in ['❌ yo\'q', '❌ yoq', 'yo\'q', 'yoq', 'no', 'n', '❌', 'yoq oddiy']:
        is_urgent = False
    else:
        # If not recognized, show the keyboard again
        await message.answer(
            "Iltimos, '✅ Ha' yoki '❌ Yo'q' tugmalaridan birini tanlang.",
            reply_markup=get_urgent_keyboard()
        )
        return
    
    # Store urgent status in state
    await state.update_data(is_urgent=is_urgent)
    
    if is_urgent:
        # Ask for location if urgent
        await message.answer(
            "📍 <b>Tezkor xabar uchun lokatsiya kerak.</b>\n\n"
            "Iltimos, joylashuvingizni yuboring yoki '⏭️ O'tkazib yuborish' tugmasini bosing:",
            reply_markup=get_location_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(ComplaintStates.waiting_for_location)
    else:
        # For non-urgent, proceed directly to save complaint
        await save_complaint_final(message, state, bot, is_urgent=False, location=None)


@router.message(ComplaintStates.waiting_for_location, F.location)
async def process_location_received(message: Message, state: FSMContext, bot):
    """
    Process received location for urgent complaint
    """
    location = {
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
        "live_period": getattr(message.location, 'live_period', None),
        "heading": getattr(message.location, 'heading', None),
        "horizontal_accuracy": getattr(message.location, 'horizontal_accuracy', None)
    }
    
    await state.update_data(location=location)
    await save_complaint_final(message, state, bot, is_urgent=True, location=location)


@router.message(ComplaintStates.waiting_for_location, F.text == "⏭️ O'tkazib yuborish")
async def skip_location(message: Message, state: FSMContext, bot):
    """
    Skip location for urgent complaint
    """
    await message.answer(
        "⚠️ <b>Lokatsiya o'tkazib yuborildi.</b>\n\n"
        "Tezkor xabar lokatsiyasiz yuboriladi.",
        parse_mode="HTML"
    )
    await save_complaint_final(message, state, bot, is_urgent=True, location=None)


@router.message(ComplaintStates.waiting_for_location)
async def invalid_input_in_location_state(message: Message):
    """
    Handle invalid input in location state
    """
    await message.answer(
        "Iltimos, lokatsiya yuboring yoki '⏭️ O'tkazib yuborish' tugmasini bosing.",
        reply_markup=get_location_keyboard()
    )


async def save_complaint_final(message: Message, state: FSMContext, bot, is_urgent: bool, location: Optional[Dict]):
    """
    Save complaint to Django API and send notifications
    """
    data = await state.get_data()
    
    # Prepare complaint data for Django API
    complaint_data = {
        'telegram_id': message.from_user.id,
        'full_name': message.from_user.full_name,
        'username': message.from_user.username,
        'mahalla_name': data['mahalla'],
        'category_name': data['category'],
        'title': f"{data['category']} muammosi - {data['mahalla']}",
        'description': data['description']
    }
    
    # Add subcategory if available
    if data.get('subcategory'):
        complaint_data['subcategory_title'] = data['subcategory']
    
    async with DjangoAPIClient() as client:
        # Send complaint to Django API
        api_response = await client.create_complaint(complaint_data)
        
        if not api_response:
            await message.answer(
                "❌ Murojaatni saqlashda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
            return
        
        complaint_id = api_response.get('id')
        
        # Process media if any
        media_items = data.get("media", [])
        media_counts = {
            "photo": 0,
            "video": 0,
            "voice": 0,
            "video_note": 0,
            "document_image": 0
        }
        
        if media_items:
            await message.answer(
                "📤 Media fayllarni saqlash jarayoni...",
                reply_markup=remove_keyboard
            )
            
            for media_item in media_items:
                try:
                    # Forward media to channel
                    msg = await bot.copy_message(
                        chat_id=config.CHANNEL_ID,
                        from_chat_id=message.chat.id,
                        message_id=media_item["message"].message_id,
                        disable_notification=True
                    )
                    
                    # Count media type
                    media_type = media_item.get("file_type")
                    if media_type in media_counts:
                        media_counts[media_type] += 1
                    
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    print(f"Error saving media: {e}")
                    continue
        
        # Prepare media summary for confirmation
        media_summary_parts = []
        if media_counts["photo"] > 0:
            media_summary_parts.append(f"📷 {media_counts['photo']} rasm")
        if media_counts["document_image"] > 0:
            media_summary_parts.append(f"📷 {media_counts['document_image']} rasm(fayl)")
        if media_counts["video"] > 0:
            media_summary_parts.append(f"🎥 {media_counts['video']} video")
        if media_counts["voice"] > 0:
            media_summary_parts.append(f"🎙️ {media_counts['voice']} ovoz")
        if media_counts["video_note"] > 0:
            media_summary_parts.append(f"🎬 {media_counts['video_note']} dumaloq video")
        
        media_summary = ", ".join(media_summary_parts) if media_summary_parts else "yo'q"
        total_media = sum(media_counts.values())
    
    # Prepare confirmation message for USER (bot ichida)
    status_text = config.STATUSES["new"]
    urgent_text = "⏰ TEZKOR XABAR" if is_urgent else "📨 ODDIY XABAR"
    location_text = "📍 Lokatsiya: Mavjud" if location else "📍 Lokatsiya: Yo'q"
    
    confirmation_text = (
        f"✅ <b>Murojaatingiz qabul qilindi!</b>\n\n"
        f"<b>Murojaat raqami:</b> #{complaint_id}\n"
        f"<b>Turi:</b> {urgent_text}\n"
        f"<b>Mahalla:</b> {data['mahalla']}\n"
        f"<b>Muammo turi:</b> {data['category']}\n"
    )
    
    if data.get('subcategory'):
        confirmation_text += f"<b>Aniq turi:</b> {data['subcategory']}\n"
    
    if is_urgent:
        confirmation_text += f"<b>{location_text}</b>\n"
    
    confirmation_text += (
        f"<b>Holati:</b> {status_text}\n"
        f"<b>Media fayllar:</b> {media_summary}\n"
        f"<b>Jami media:</b> {total_media} ta\n\n"
        f"<b>Tavsif:</b>\n{data['description']}\n\n"
        "Murojaatingiz holatini '📋 Mening murojaatlarim' bo'limidan kuzatishingiz mumkin."
    )
    
    # Send confirmation to user
    await message.answer(
        confirmation_text,
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )
    
    # Prepare notification for GROUP
    urgent_emoji = "⏰" if is_urgent else "📨"
    urgent_label = "TEZKOR XABAR" if is_urgent else "ODDIY XABAR"
    location_status = "📍 Lokatsiya mavjud" if location else "📍 Lokatsiya yo'q"
    
    group_notification = (
        f"{urgent_emoji} <b>YANGI MUROJAAT ({urgent_label})</b>\n\n"
        f"<b>ID:</b> #{complaint_id}\n"
        f"<b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"<b>Telegram:</b> @{message.from_user.username}\n"
        f"<b>Mahalla:</b> {data['mahalla']}\n"
        f"<b>Muammo turi:</b> {data['category']}\n"
    )
    
    if data.get('subcategory'):
        group_notification += f"<b>Aniq turi:</b> {data['subcategory']}\n"
    
    if is_urgent:
        group_notification += f"<b>{location_status}</b>\n"
    
    group_notification += (
        f"<b>Media fayllar:</b> {media_summary}\n"
        f"<b>Jami media:</b> {total_media} ta\n\n"
        f"<b>Tavsif:</b>\n{data['description']}\n\n"
    )
    
    # Prepare hashtags
    mahalla_tag = data['mahalla'].replace(' ', '_').replace("'", '_').replace('-', '_').lower()
    category_tag = data['category'].replace(' ', '_').replace('-', '_').replace("'", '_').lower()
    subcategory_tag = data.get('subcategory', '').replace(' ', '_').replace("'", '_').replace('-', '_').lower() if data.get('subcategory') else ''
    
    tags = f"#murojaat #{mahalla_tag} #{category_tag}"
    if subcategory_tag:
        tags += f" #{subcategory_tag}"
    if is_urgent:
        tags += " #tezkor"
        if location:
            tags += " #lokatsiya"
    
    group_notification += tags
    
    # Send to group
    try:
        group_message = await bot.send_message(
            chat_id=config.GROUP_ID,
            text=group_notification,
            parse_mode="HTML"
        )
        
        # If location exists and is urgent, send location to group
        if is_urgent and location:
            try:
                await bot.send_location(
                    chat_id=config.GROUP_ID,
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                    reply_to_message_id=group_message.message_id
                )
            except Exception as e:
                print(f"Error sending location to group: {e}")
                
    except Exception as e:
        print(f"Error sending to group: {e}")
        await message.answer(
            f"⚠️ Guruhga xabar yuborishda xatolik yuz berdi. Murojaatingiz saqlangan bo'lsa ham, "
            f"guruhga xabar yuborilmadi.\n\nXato: {str(e)}",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    # Clear state
    await state.clear()


@router.message(ComplaintStates.waiting_for_urgent_confirm, F.text == "❌ Bekor qilish")
async def cancel_complaint_urgent(message: Message, state: FSMContext):
    """
    Cancel complaint creation from urgent confirmation state
    """
    await message.answer(
        "Murojaat yaratish bekor qilindi.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()


@router.message(ComplaintStates.waiting_for_location, F.text == "❌ Bekor qilish")
async def cancel_complaint_location(message: Message, state: FSMContext):
    """
    Cancel complaint creation from location state
    """
    await message.answer(
        "Murojaat yaratish bekor qilindi.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()


@router.message(ComplaintStates.waiting_for_media, F.text == "❌ Bekor qilish")
async def cancel_complaint(message: Message, state: FSMContext):
    """
    Cancel complaint creation
    """
    await message.answer(
        "Murojaat yaratish bekor qilindi.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()


@router.message(ComplaintStates.waiting_for_media)
async def invalid_input_in_media_state(message: Message):
    """
    Handle invalid input in media state
    """
    await message.answer(
        "Iltimos, media fayl yuboring (rasm, video, ovoz, dumaloq video) "
        "yoki '✅ Yuborish' tugmasini bosing.",
        reply_markup=get_media_keyboard()
    )