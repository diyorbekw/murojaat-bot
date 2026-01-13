"""
Main application entry point
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config

# Import routers
from bot.handlers.start import router as start_router
from bot.handlers.complaint_create import router as complaint_create_router
from bot.handlers.complaint_view import router as complaint_view_router
from bot.handlers.admin import router as admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main application function
    """
    # Check if token is set
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Bot token not configured! Please set BOT_TOKEN in .env file")
        print("\n" + "="*50)
        print("ERROR: Bot token not configured!")
        print("Please do the following:")
        print("1. Open .env file")
        print("2. Replace YOUR_BOT_TOKEN_HERE with your actual bot token")
        print("3. Make sure token looks like: 1234567890:ABCdefGHIjklMNOpqrSTUvxyZ")
        print("="*50)
        return
    
    # Initialize bot with default properties
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher with memory storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(start_router)
    dp.include_router(complaint_create_router)
    dp.include_router(complaint_view_router)
    dp.include_router(admin_router)
    
    # Start bot
    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
        print(f"\nError details: {e}")