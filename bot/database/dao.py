from datetime import datetime

from sqlalchemy import select

from bot.database.engine import session_factory
from bot.database.models import Question, Suggestion, User


async def upsert_user(
    user_id: int,
    language: str | None = None,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    async with session_factory() as session:
        user = await session.get(User, user_id)
        now = datetime.utcnow()
        if user:
            if language:
                user.language = language
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.last_seen = now
        else:
            user = User(
                user_id=user_id,
                language=language or "ru",
                username=username,
                first_name=first_name,
                last_name=last_name,
                first_seen=now,
                last_seen=now,
            )
            session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_user_language(user_id: int) -> str | None:
    async with session_factory() as session:
        user = await session.get(User, user_id)
        if user:
            return user.language
        return None


async def get_all_user_ids() -> list[int]:
    async with session_factory() as session:
        rows = await session.execute(select(User.user_id))
        return [row[0] for row in rows]


async def create_question(user_id: int, text: str, username: str | None = None) -> Question:
    async with session_factory() as session:
        item = Question(
            user_id=user_id,
            username=username,
            text=text,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


async def get_question_by_id(question_id: int) -> Question | None:
    async with session_factory() as session:
        return await session.get(Question, question_id)


async def answer_question(question_id: int, answer_text: str) -> Question | None:
    async with session_factory() as session:
        item = await session.get(Question, question_id)
        if not item or item.is_answered:
            return None
        item.is_answered = True
        item.answer_text = answer_text
        item.answered_at = datetime.utcnow()
        await session.commit()
        await session.refresh(item)
        return item


async def create_suggestion(user_id: int, text: str, username: str | None = None) -> Suggestion:
    async with session_factory() as session:
        item = Suggestion(
            user_id=user_id,
            username=username,
            text=text,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
