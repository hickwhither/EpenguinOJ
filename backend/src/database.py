import os
import json
from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, create_engine, Session, select

from .models import *

def get_database_url():
    return os.getenv('DATABASE_URL') or "sqlite:///database.db"


def get_engine_kwargs(database_url: str):
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(get_database_url(), **get_engine_kwargs(get_database_url()))


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)


SessionDep = Annotated[Session, Depends(get_session)]