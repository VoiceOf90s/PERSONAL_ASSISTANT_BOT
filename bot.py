import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from handlers import basic, info, personal, settings
from utils.db import init_db
from utils.scheduler import check_reminders

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Валидация конфигурации
if not Config.validate():
    logging.error("❌ Ошибка конфигурации. Проверьте переменные окружения.")
    sys.exit(1)

bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


async def on_startup():
    init_db()
    scheduler.add_job(check_reminders, "interval", seconds=30, args=(bot,))
    scheduler.start()
    logging.info("✅ Bot started!")


async def on_shutdown():
    """Корректное завершение работы бота"""
    logging.info("🛑 Shutting down bot...")
    scheduler.shutdown(wait=True)
    await bot.session.close()
    logging.info("✅ Bot stopped gracefully")


async def main():
    dp.include_routers(
        basic.router,
        info.router,
        personal.router,
        settings.router,
    )
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("⚠️ Interrupted by user")
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}")
        sys.exit(1)