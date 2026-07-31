import os
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import *

def get_database_url() -> str:
    return os.getenv('DATABASE_URL') or "sqlite+aiosqlite:///database.db"


database_url = get_database_url()
print(database_url)
engine = create_async_engine(database_url)

async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await ensure_ranking_columns()


RANKING_ALTERS = {
    "problem_scores": "ALTER TABLE contestregistration ADD COLUMN problem_scores JSON NULL",
    "last_improve_time": "ALTER TABLE contestregistration ADD COLUMN last_improve_time BIGINT NULL",
}


async def ensure_ranking_columns():
    """Additive migration for the ranking columns on `contestregistration`.

    `create_all` never alters existing tables, so add the missing ranking
    columns explicitly. Safe to run on every startup.
    """
    async with engine.begin() as conn:
        def _run(sync_conn):
            insp = sa_inspect(sync_conn)
            try:
                existing = {c["name"] for c in insp.get_columns("contestregistration")}
            except Exception:
                return
            for name, ddl in RANKING_ALTERS.items():
                if name not in existing:
                    sync_conn.exec_driver_sql(ddl)

        await conn.run_sync(_run)


SessionDep = Annotated[AsyncSession, Depends(get_session)]