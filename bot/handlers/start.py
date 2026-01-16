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
    # Django API dan foydalanuvchi holatini tekshirish
    async with DjangoAPIClient() as client:
        user_data = await client.check_user_registration(message.from_user.id)
    
    if not user_data.get('exists') or not user_data.get('registration_completed'):
        # Ro'yxatdan o'tmagan yoki to'liq ro'yxatdan o'tmagan foydalanuvchi
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
    """To'liq ismni qabul qilish va Django API ga yuborish"""
    if len(message.text.strip()) < 5:
        await message.answer("❌ Iltimos, to'liq ism va familiyangizni kiriting (kamida 5 ta belgi):")
        return
    
    full_name = message.text.strip()
    
    try:
        # Django API ga foydalanuvchi yaratish
        async with DjangoAPIClient() as client:
            user = await client.get_or_create_user(
                telegram_id=message.from_user.id,
                full_name=full_name,
                username=message.from_user.username
            )
        
        if user:
            await state.update_data(full_name=full_name)
            await state.set_state(RegistrationStates.waiting_for_age)
            await message.answer(
                f"✅ Ismingiz qabul qilindi: {full_name}\n\n"
                "📅 Iltimos, yoshingizni kiriting (faqat raqamda):"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
    except Exception as e:
        print(f"Error in process_fullname: {e}")
        await message.answer("❌ Server xatosi yuz berdi. Iltimos, keyinroq urinib ko'ring.")


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
    
    await state.update_data(age=age)
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
    
    await state.update_data(phone=phone)
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
    
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.waiting_for_second_phone)
    await message.answer(
        f"✅ Asosiy telefon raqam qabul qilindi: {phone}\n\n"
        "📱 Qo'shimcha telefon raqamingiz bormi?\n"
        "Agar bo'lsa, raqamni yuboring yoki /skip buyrug'i bilan o'tkazib yuboring:"
    )


@router.message(RegistrationStates.waiting_for_second_phone, Command("skip"))
async def skip_second_phone(message: Message, state: FSMContext):
    """Qo'shimcha telefon raqamini o'tkazib yuborish va Django API ga saqlash"""
    try:
        user_data = await state.get_data()
        
        # Django API ga profilni yangilash
        async with DjangoAPIClient() as client:
            updated_user = await client.update_user_profile(
                telegram_id=message.from_user.id,
                full_name=user_data.get('full_name'),
                phone_number=user_data.get('phone'),
                age=user_data.get('age'),
                second_phone=None
            )
        
        if updated_user:
            # Ro'yxatdan o'tish yakunlandi
            await state.clear()
            
            profile_text = f"""
🎉 Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz!

👤 <b>Ism:</b> {updated_user.full_name}
📅 <b>Yosh:</b> {updated_user.age}
📱 <b>Telefon:</b> {updated_user.phone_number}

Endi botdan to'liq foydalanishingiz mumkin!
"""
            
            await message.answer(profile_text, parse_mode="HTML")
            await show_main_menu(message)
        else:
            await message.answer("❌ Xatolik yuz berdi. Iltimos, /start ni bosib qaytadan urinib ko'ring.")
    except Exception as e:
        print(f"Error in skip_second_phone: {e}")
        await message.answer("❌ Server xatosi yuz berdi. Iltimos, keyinroq urinib ko'ring.")


@router.message(RegistrationStates.waiting_for_second_phone)
async def process_second_phone(message: Message, state: FSMContext):
    """Qo'shimcha telefon raqamini qabul qilish va Django API ga saqlash"""
    try:
        phone = message.text.strip()
        
        # Oddiy telefon raqam validatsiyasi
        if not (phone.startswith('+') or phone.isdigit()):
            await message.answer("❌ Iltimos, to'g'ri telefon raqamini kiriting:\nMasalan: +998901234567 yoki 901234567")
            return
        
        user_data = await state.get_data()
        
        # Django API ga profilni yangilash
        async with DjangoAPIClient() as client:
            updated_user = await client.update_user_profile(
                telegram_id=message.from_user.id,
                full_name=user_data.get('full_name'),
                phone_number=user_data.get('phone'),
                age=user_data.get('age'),
                second_phone=phone
            )
        
        if updated_user:
            # Ro'yxatdan o'tish yakunlandi
            await state.clear()
            
            profile_text = f"""
🎉 Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz!

👤 <b>Ism:</b> {updated_user.full_name}
📅 <b>Yosh:</b> {updated_user.age}
📱 <b>Asosiy telefon:</b> {updated_user.phone_number}
📱 <b>Qo'shimcha telefon:</b> {updated_user.second_phone}

Endi botdan to'liq foydalanishingiz mumkin!
"""
            
            await message.answer(profile_text, parse_mode="HTML")
            await show_main_menu(message)
        else:
            await message.answer("❌ Xatolik yuz berdi. Iltimos, /start ni bosib qaytadan urinib ko'ring.")
    except Exception as e:
        print(f"Error in process_second_phone: {e}")
        await message.answer("❌ Server xatosi yuz berdi. Iltimos, keyinroq urinib ko'ring.")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """
    Foydalanuvchi profili haqida ma'lumot
    """
    # Django API dan foydalanuvchi ma'lumotlarini olish
    async with DjangoAPIClient() as client:
        user_data = await client.get_user_profile(message.from_user.id)
    
    if not user_data:
        await message.answer("❌ Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
        return
    
    profile_text = f"""
👤 <b>Sizning profilingiz:</b>

🆔 <b>ID:</b> {message.from_user.id}
👤 <b>To'liq ism:</b> {user_data.full_name or "Noma'lum"}
📅 <b>Yosh:</b> {user_data.age or "Noma'lum"}
📱 <b>Telefon:</b> {user_data.phone_number or "Noma'lum"}
"""
    
    if user_data.second_phone:
        profile_text += f"📱 <b>Qo'shimcha telefon:</b> {user_data.second_phone}\n"
    
    profile_text += f"\n✅ <b>Ro'yxatdan o'tish:</b> {'Tugallangan' if user_data.registration_completed else 'Tugallanmagan'}"
    
    await message.answer(profile_text, parse_mode="HTML")


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
    
    await show_main_menu(message)