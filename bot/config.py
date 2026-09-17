import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

QUESTIONS_CHAT_ID = os.getenv("QUESTIONS_CHAT_ID")
SUGGESTIONS_CHAT_ID = os.getenv("SUGGESTIONS_CHAT_ID")

MEME_STORAGE_CHAT_ID = os.getenv("MEME_STORAGE_CHAT_ID")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_data.db")


def _parse_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    result: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if part:
            try:
                result.add(int(part))
            except ValueError:
                pass
    return result


ADMIN_IDS: set[int] = _parse_ids(os.getenv("ADMIN_IDS"))
SUPER_ADMIN_IDS: set[int] = _parse_ids(os.getenv("SUPER_ADMIN_IDS"))


def set_questions_chat_id(chat_id: int) -> None:
    global QUESTIONS_CHAT_ID
    QUESTIONS_CHAT_ID = str(chat_id)


def set_suggestions_chat_id(chat_id: int) -> None:
    global SUGGESTIONS_CHAT_ID
    SUGGESTIONS_CHAT_ID = str(chat_id)


def is_admin(user_id: int | None) -> bool:
    return bool(user_id and (user_id in ADMIN_IDS or user_id in SUPER_ADMIN_IDS))


def is_super_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in SUPER_ADMIN_IDS)


def add_admin_id(user_id: int) -> None:
    ADMIN_IDS.add(user_id)


def remove_admin_id(user_id: int) -> None:
    ADMIN_IDS.discard(user_id)


def add_super_admin_id(user_id: int) -> None:
    SUPER_ADMIN_IDS.add(user_id)


def remove_super_admin_id(user_id: int) -> None:
    SUPER_ADMIN_IDS.discard(user_id)
