"""
Start command and main menu handlers with Django API
"""

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.reply import get_main_menu_keyboard, get_admin_menu_keyboard, remove_keyboard
from bot.utils.permissions import is_admin
from bot.api_client import DjangoAPIClient

router = Router(name="start")

# Foydalanuvchi ma'lumotlarini saqlash uchun (hozircha dictda)
user_registrations = {}

# Ro'yxatdan o'tish holatlari
class RegistrationStates(StatesGroup):
    waiting_for_fullname = State()
    waiting_for_age = State()
    waiting_for_phone = State()
    waiting_for_second_phone = State()

def get_phone_keyboard():
    """Telefon raqamini yuborish uchun tugma"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Handle /start command with Django API
    """
    # Ro'yxatdan o'tish jarayoni tekshiriladi
    user_id = str(message.from_user.id)
    
    if user_id not in user_registrations:
        # Ro'yxatdan o'tmagan foydalanuvchi
        await state.set_state(RegistrationStates.waiting_for_fullname)
        await message.answer(
            "Assalomu alaykum! Karmana tumani muammolarini qabul qilish botiga xush kelibsiz.\n\n"
            "Avval ro'yxatdan o'tishingiz kerak.\n"
            "📝 Iltimos, to'liq ism va familiyangizni kiriting:",
            reply_markup=remove_keyboard,
            parse_mode="HTML"
        )
        return
    
    # Agar ro'yxatdan o'tgan bo'lsa, oddiy start
    await show_main_menu(message)


async def show_main_menu(message: Message):
    """Asosiy menyuni ko'rsatish"""
    user_id = str(message.from_user.id)
    user_data = user_registrations.get(user_id, {})
    
    # Check if user is admin
    admin = await is_admin(message.from_user)
    
    # Welcome message
    welcome_text = (
        "Assalomu alaykum!\n"
        "Karmana tumani muammolarini qabul qilish botiga xush kelibsiz.\n\n"
        "📝 <b>Muammo yuborish</b> - Mahallangizdagi muammoni yozib qoldiring\n"
        "📋 <b>Mening murojaatlarim</b> - Oldin yuborgan murojaatlaringizni ko'ring\n"
    )
    
    if admin:
        welcome_text += (
            "\n👨‍💻 <b>Administrator rejimi:</b>\n"
            "👨‍💻 <b>Barcha murojaatlar</b> - Barcha foydalanuvchilarning murojaatlari\n"
            "📊 <b>Statistika</b> - Umumiy statistika\n"
        )
    
    # Foydalanuvchi ma'lumotlari
    if user_data:
        welcome_text += f"\n\n👤 <b>Foydalanuvchi:</b> {user_data.get('full_name', '')}"
    
    # Send welcome message with appropriate keyboard
    if admin:
        await message.answer(
            welcome_text,
            reply_markup=get_admin_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )


# Ro'yxatdan o'tish bosqichlari
@router.message(RegistrationStates.waiting_for_fullname)
async def process_fullname(message: Message, state: FSMContext):
    """To'liq ismni qabul qilish"""
    if len(message.text.strip()) < 5:
        await message.answer("❌ Iltimos, to'liq ism va familiyangizni kiriting (kamida 5 ta belgi):")
        return
    
    user_id = str(message.from_user.id)
    user_registrations[user_id] = {"full_name": message.text.strip()}
    
    await state.set_state(RegistrationStates.waiting_for_age)
    await message.answer(
        f"✅ Ismingiz qabul qilindi: {message.text.strip()}\n\n"
        "📅 Iltimos, yoshingizni kiriting (faqat raqamda):"
    )


@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    """Yoshni qabul qilish"""
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, yoshingizni faqat raqamlarda kiriting:")
        return
    
    age = int(message.text)
    if age < 10 or age > 120:
        await message.answer("❌ Iltimos, haqiqiy yoshingizni kiriting (10-120 oralig'ida):")
        return
    
    user_id = str(message.from_user.id)
    user_registrations[user_id]["age"] = age
    
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer(
        f"✅ Yosh qabul qilindi: {age}\n\n"
        "📱 Iltimos, telefon raqamingizni yuboring:",
        reply_markup=get_phone_keyboard()
    )


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Telefon raqamini kontakt orqali qabul qilish"""
    phone = message.contact.phone_number
    
    user_id = str(message.from_user.id)
    user_registrations[user_id]["phone"] = phone
    
    await state.set_state(RegistrationStates.waiting_for_second_phone)
    await message.answer(
        f"✅ Asosiy telefon raqam qabul qilindi: {phone}\n\n"
        "📱 Qo'shimcha telefon raqamingiz bormi?\n"
        "Agar bo'lsa, raqamni yuboring yoki /skip buyrug'i bilan o'tkazib yuboring:",
        reply_markup=remove_keyboard
    )


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Telefon raqamini text orqali qabul qilish"""
    phone = message.text.strip()
    
    # Oddiy telefon raqam validatsiyasi
    if not (phone.startswith('+') or phone.isdigit()):
        await message.answer("❌ Iltimos, to'g'ri telefon raqamini kiriting:\nMasalan: +998901234567 yoki 901234567")
        return
    
    user_id = str(message.from_user.id)
    user_registrations[user_id]["phone"] = phone
    
    await state.set_state(RegistrationStates.waiting_for_second_phone)
    await message.answer(
        f"✅ Asosiy telefon raqam qabul qilindi: {phone}\n\n"
        "📱 Qo'shimcha telefon raqamingiz bormi?\n"
        "Agar bo'lsa, raqamni yuboring yoki /skip buyrug'i bilan o'tkazib yuboring:"
    )


@router.message(RegistrationStates.waiting_for_second_phone, Command("skip"))
async def skip_second_phone(message: Message, state: FSMContext):
    """Qo'shimcha telefon raqamini o'tkazib yuborish"""
    user_id = str(message.from_user.id)
    user_data = user_registrations[user_id]
    
    # Ro'yxatdan o'tish yakunlandi
    await state.clear()
    
    registration_info = (
        "🎉 Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
        f"👤 <b>Ism:</b> {user_data.get('full_name', '')}\n"
        f"📅 <b>Yosh:</b> {user_data.get('age', '')}\n"
        f"📱 <b>Telefon:</b> {user_data.get('phone', '')}\n"
    )
    
    if "second_phone" in user_data:
        registration_info += f"📱 <b>Qo'shimcha telefon:</b> {user_data.get('second_phone', '')}\n"
    
    registration_info += "\nEndi botdan to'liq foydalanishingiz mumkin!"
    
    await message.answer(registration_info, parse_mode="HTML")
    await show_main_menu(message)


@router.message(RegistrationStates.waiting_for_second_phone)
async def process_second_phone(message: Message, state: FSMContext):
    """Qo'shimcha telefon raqamini qabul qilish"""
    phone = message.text.strip()
    
    # Oddiy telefon raqam validatsiyasi
    if not (phone.startswith('+') or phone.isdigit()):
        await message.answer("❌ Iltimos, to'g'ri telefon raqamini kiriting:\nMasalan: +998901234567 yoki 901234567")
        return
    
    user_id = str(message.from_user.id)
    user_registrations[user_id]["second_phone"] = phone
    
    # Ro'yxatdan o'tish yakunlandi
    await state.clear()
    
    user_data = user_registrations[user_id]
    registration_info = (
        "🎉 Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
        f"👤 <b>Ism:</b> {user_data.get('full_name', '')}\n"
        f"📅 <b>Yosh:</b> {user_data.get('age', '')}\n"
        f"📱 <b>Asosiy telefon:</b> {user_data.get('phone', '')}\n"
        f"📱 <b>Qo'shimcha telefon:</b> {user_data.get('second_phone', '')}\n"
        "\nEndi botdan to'liq foydalanishingiz mumkin!"
    )
    
    await message.answer(registration_info, parse_mode="HTML")
    await show_main_menu(message)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handle /help command
    """
    help_text = (
        "🤖 <b>Bot yordami:</b>\n\n"
        "📝 <b>Muammo yuborish</b> - Yangi muammo yuborish uchun\n"
        "📋 <b>Mening murojaatlarim</b> - Sizning murojaatlaringiz ro'yxati\n\n"
        "📸 <b>Rasm yuklash:</b>\n"
        "- Bir nechta rasmlarni yuklashingiz mumkin\n"
        "- Har bir rasm alohida xabar sifatida yuborilishi kerak\n"
        "- Rasmlarni yuborishni tugatgach, '✅ Yuborish' tugmasini bosing\n\n"
        "🔄 <b>Murojaat holati:</b>\n"
        "🆕 Yangi - Tekshirish kutilmoqda\n"
        "🔄 Jarayonda - Ish olib borilmoqda\n"
        "✅ Hal qilindi - Muammo hal qilindi\n"
        "⏳ Kehtirildi - Vaqtinchalik kehtirildi\n\n"
        "❓ Qo'shimcha savollar uchun: @admin"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "🏠 Bosh menyu")
async def back_to_main_menu(message: Message):
    """
    Handle back to main menu button
    """
    await show_main_menu(message)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Handle /cancel command
    """
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "Amal bekor qilindi.",
            reply_markup=remove_keyboard
        )
    
    # Ro'yxatdan o'tmagan foydalanuvchini tekshirish
    user_id = str(message.from_user.id)
    if user_id not in user_registrations:
        await cmd_start(message, state)
    else:
        await show_main_menu(message)


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """
    Foydalanuvchi profili haqida ma'lumot
    """
    user_id = str(message.from_user.id)
    user_data = user_registrations.get(user_id)
    
    if not user_data:
        await message.answer("❌ Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
        return
    
    profile_text = (
        "👤 <b>Sizning profilingiz:</b>\n\n"
        f"🆔 <b>ID:</b> {message.from_user.id}\n"
        f"👤 <b>To'liq ism:</b> {user_data.get('full_name', 'Noma\'lum')}\n"
        f"📅 <b>Yosh:</b> {user_data.get('age', 'Noma\'lum')}\n"
        f"📱 <b>Telefon:</b> {user_data.get('phone', 'Noma\'lum')}\n"
    )
    
    if "second_phone" in user_data:
        profile_text += f"📱 <b>Qo'shimcha telefon:</b> {user_data.get('second_phone')}\n"
    
    await message.answer(profile_text, parse_mode="HTML")