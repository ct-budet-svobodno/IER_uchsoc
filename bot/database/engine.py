import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bot.config import DATABASE_URL

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

session_factory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    from bot.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.begin() as conn:
        def add_missing_columns(sync_conn):
            inspector = inspect(sync_conn)
            tables_info = {
                "questions": [
                    ("is_answered", "BOOLEAN DEFAULT 0"),
                    ("answer_text", "TEXT"),
                    ("answered_at", "DATETIME"),
                ],
            }
            for table, columns in tables_info.items():
                existing = {col["name"] for col in inspector.get_columns(table)}
                for col_name, col_type in columns:
                    if col_name not in existing:
                        sync_conn.execute(
                            text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        )
                        logger.info("Added column %s to table %s", col_name, table)

        await conn.run_sync(add_missing_columns)
