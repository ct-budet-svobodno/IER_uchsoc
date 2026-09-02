import asyncio
import json
import random
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import FSInputFile

from bot.config import MEME_STORAGE_CHAT_ID
from bot.utils.content import DATA_DIR

MEMES_DIR = DATA_DIR / "photos" / "memes"
MEME_IDS_FILE = DATA_DIR / "meme_ids.json"

_meme_ids: list[str] = []


def reset_meme_cache() -> None:
    """Сбрасывает кэш file_id, чтобы следующие мемы подтянулись с сервера заново."""
    global _meme_ids
    _meme_ids = []


def _load_meme_ids() -> list[str]:
    global _meme_ids
    if _meme_ids:
        return _meme_ids
    if MEME_IDS_FILE.exists():
        try:
            _meme_ids = json.loads(MEME_IDS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _meme_ids = []
    return _meme_ids


async def ensure_meme_ids(bot: Bot) -> None:
    """Один раз загружает мемы в канал-хранилище и сохраняет их file_id.

    Дальше бот отправляет мемы по file_id: сервер не передаёт байты картинок,
    их раздаёт CDN Telegram.
    """
    if _load_meme_ids():
        return
    if not MEME_STORAGE_CHAT_ID:
        return
    meme_files = sorted(MEMES_DIR.glob("*.jpg"))
    if not meme_files:
        return
    ids: list[str] = []
    for meme_file in meme_files:
        while True:
            try:
                sent = await bot.send_photo(MEME_STORAGE_CHAT_ID, FSInputFile(meme_file))
                break
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
        ids.append(sent.photo[-1].file_id)
        await asyncio.sleep(1)
    _meme_ids = ids
    MEME_IDS_FILE.write_text(json.dumps(ids, ensure_ascii=False), encoding="utf-8")


async def get_random_meme(bot: Bot) -> str | Path:
    """Возвращает file_id мема (если канал настроен) или путь к локальному файлу."""
    ids = _load_meme_ids()
    if ids:
        return random.choice(ids)
    meme_files = [f for f in MEMES_DIR.glob("*.jpg")]
    if not meme_files:
        raise FileNotFoundError("no memes found")
    return random.choice(meme_files)