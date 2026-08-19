import asyncio
import atexit
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LOCK_FILE = Path(__file__).resolve().parent.parent / ".bot.lock"


def _acquire_single_instance() -> None:
    """Защита от двойного запуска: если бот уже работает, второй процесс выходит."""
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            old_pid = None
        if old_pid:
            try:
                os.kill(old_pid, 0)
                print(f"Бот уже запущен (PID {old_pid}). Завершаюсь.")
                sys.exit(1)
            except Exception:
                pass
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: LOCK_FILE.unlink(missing_ok=True))


_acquire_single_instance()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database.engine import init_db
from bot.handlers import admin, feedback, menu, start
from bot.middlewares.language import LanguageMiddleware
from bot.utils.memes import ensure_meme_ids

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("Set BOT_TOKEN in .env file")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(feedback.router)
    dp.include_router(menu.router)

    await init_db()
    logger.info("Database initialized")

    asyncio.create_task(ensure_meme_ids(bot))

    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
