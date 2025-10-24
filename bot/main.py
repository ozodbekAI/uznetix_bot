import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.engine import db
from bot.handlers import start, interview, admin
from bot.middlewares.database import DatabaseMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def on_startup(bot: Bot):
    """Actions on bot startup"""
    logger.info("Initializing database...")
    db.init_engine()
    await db.create_tables()
    logger.info("Database initialized")
    
    logger.info(f"Bot {settings.BOT_NAME} started!")


async def on_shutdown(bot: Bot):
    """Actions on bot shutdown"""
    logger.info("Shutting down...")
    await db.dispose()
    logger.info("Bot stopped")


async def main():
    """Main bot function"""
    
    # Initialize bot
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher with memory storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # Register handlers
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(interview.router)
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")