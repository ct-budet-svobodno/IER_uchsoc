import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

QUESTIONS_CHAT_ID = os.getenv("QUESTIONS_CHAT_ID")
SUGGESTIONS_CHAT_ID = os.getenv("SUGGESTIONS_CHAT_ID")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_data.db")


def _parse_admin_ids(value: str | None) -> set[int]:
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


ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS"))
