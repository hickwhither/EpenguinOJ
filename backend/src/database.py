import os
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import *

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


SessionDep = Annotated[AsyncSession, Depends(get_session)]