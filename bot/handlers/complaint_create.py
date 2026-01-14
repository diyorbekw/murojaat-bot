"""
Complaint creation handlers with FSM and Django API
"""

import asyncio
from typing import List
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.states import ComplaintStates
from bot.keyboards.reply import (
    get_mahalla_keyboard,
    get_category_keyboard,
    get_images_keyboard,
    get_cancel_keyboard,
    remove_keyboard,
    get_back_to_menu_keyboard
)
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
        else:
            category_names = [c['name'] for c in categories_data]
    
    # Store categories in state for later validation
    await state.update_data(available_categories=category_names)
    
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
    
    # Validate category
    if message.text not in available_categories:
        await message.answer(
            "Iltimos, ro'yxatdan muammo turini tanlang.",
            reply_markup=get_category_keyboard(available_categories)
        )
        return
    
    await state.update_data(category=message.text)
    
    await message.answer(
        "3-qadam: <b>Muammoni batafsil yozing:</b>\n\n"
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
        "4-qadam: <b>Agar mavjud bo'lsa, rasm yuboring.</b>\n\n"
        "Bir nechta rasm yuborishingiz mumkin.\n"
        "Har bir rasm alohida xabar sifatida yuborilishi kerak.\n"
        "Rasmlarni yuborishni tugatgach, '✅ Yuborish' tugmasini bosing.\n\n"
        "Agar rasm yo'q bo'lsa, shunchaki '✅ Yuborish' tugmasini bosing.",
        reply_markup=get_images_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ComplaintStates.waiting_for_images)


@router.message(
    ComplaintStates.waiting_for_images,
    F.content_type.in_({ContentType.PHOTO, ContentType.DOCUMENT})
)
async def process_image(message: Message, state: FSMContext):
    """
    Process uploaded image
    """
    # Get current images list or initialize
    data = await state.get_data()
    images = data.get("images", [])
    
    # Store image file_id
    if message.photo:
        # For photos, get the largest size
        file_id = message.photo[-1].file_id
        images.append({"file_id": file_id, "message": message})
    elif message.document:
        # Check if it's an image document
        if message.document.mime_type and message.document.mime_type.startswith("image/"):
            file_id = message.document.file_id
            images.append({"file_id": file_id, "message": message})
        else:
            await message.answer(
                "Iltimos, faqat rasm fayllarini yuboring.",
                reply_markup=get_images_keyboard()
            )
            return
    
    await state.update_data(images=images)
    
    # Send confirmation
    await message.answer(
        f"✅ Rasm qabul qilindi. Jami: {len(images)} ta\n\n"
        "Yana rasm yuborishingiz yoki '✅ Yuborish' tugmasini bosishingiz mumkin.",
        reply_markup=get_images_keyboard()
    )



@router.message(ComplaintStates.waiting_for_images, F.text == "✅ Yuborish")
async def submit_complaint(message: Message, state: FSMContext, bot):
    """
    Submit complaint and save to Django API
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
        'description': data['description'],
        'location': None,
        'priority': 'medium',
    }
    
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
        
        # Process images if any
        images = data.get("images", [])
        image_count = 0
        
        if images:
            await message.answer(
                "📤 Rasmlarni saqlash jarayoni...",
                reply_markup=remove_keyboard
            )
            
            for img_data in images:
                try:
                    # Forward image to channel
                    msg = await bot.copy_message(
                        chat_id=config.CHANNEL_ID,
                        from_chat_id=message.chat.id,
                        message_id=img_data["message"].message_id,
                        disable_notification=True
                    )
                    
                    # Save image to Django API
                    file_id = img_data.get("file_id")
                    await client.add_complaint_image(complaint_id, msg.message_id, file_id)
                    image_count += 1
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error saving image: {e}")
                    continue
    
    # Prepare confirmation message
    status_text = config.STATUSES["new"]
    
    confirmation_text = (
        f"✅ <b>Murojaatingiz qabul qilindi!</b>\n\n"
        f"<b>Murojaat raqami:</b> #{complaint_id}\n"
        f"<b>Mahalla:</b> {data['mahalla']}\n"
        f"<b>Muammo turi:</b> {data['category']}\n"
        f"<b>Holati:</b> {status_text}\n"
        f"<b>Rasmlar:</b> {image_count} ta\n\n"
        f"<b>Tavsif:</b>\n{data['description']}\n\n"
        "Murojaatingiz holatini '📋 Mening murojaatlarim' bo'limidan kuzatishingiz mumkin."
    )
    
    # Send confirmation to user
    await message.answer(
        confirmation_text,
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="HTML"
    )
    
    # Clear state
    await state.clear()
    
    # Notify admins about new complaint
    admin_notification = (
        f"🆕 <b>Yangi murojaat!</b>\n\n"
        f"<b>ID:</b> #{complaint_id}\n"
        f"<b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"<b>Mahalla:</b> {data['mahalla']}\n"
        f"<b>Muammo turi:</b> {data['category']}\n"
        f"<b>Rasmlar:</b> {image_count} ta\n\n"
        f"<b>Tavsif:</b>\n{data['description'][:200]}..."
    )
    
    from bot.utils.permissions import is_admin
    
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_notification,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {e}")


@router.message(ComplaintStates.waiting_for_images, F.text == "❌ Bekor qilish")
async def cancel_complaint(message: Message, state: FSMContext):
    """
    Cancel complaint creation
    """
    await message.answer(
        "Murojaat yaratish bekor qilindi.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()


@router.message(ComplaintStates.waiting_for_images)
async def invalid_input_in_images_state(message: Message):
    """
    Handle invalid input in images state
    """
    await message.answer(
        "Iltimos, rasm yuboring yoki '✅ Yuborish' tugmasini bosing.",
        reply_markup=get_images_keyboard()
    )