"""
Start command and main menu handlers with Django API
"""

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command

from bot.keyboards.reply import get_main_menu_keyboard, get_admin_menu_keyboard, remove_keyboard
from bot.utils.permissions import is_admin
from bot.api_client import DjangoAPIClient

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handle /start command with Django API
    """
    async with DjangoAPIClient() as client:
        # Register or get user from Django
        user = await client.get_or_create_user_local(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name
        )
    
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
    await cmd_start(message)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    """
    Handle /cancel command
    """
    await message.answer(
        "Amal bekor qilindi.",
        reply_markup=remove_keyboard
    )
    await cmd_start(message)