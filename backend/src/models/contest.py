from typing import *
from sqlmodel import *
from sqlalchemy import Column, DateTime
from datetime import datetime

from .links import ContestTask, ContestRegistration

if TYPE_CHECKING:
    from .user import User
    from .problem import Problem
    from .submission import Submission


class ContestPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    name: Optional[str] = Field(index=True)
    registration_start: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), index=True))
    registration_end: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), index=True))
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True), index=True))
    end_time: datetime = Field(sa_column=Column(DateTime(timezone=True), index=True))


class ContestView(ContestPublic):
    description: Optional[str] = Field(sa_type=TEXT)


class Contest(ContestView, table=True):
    password: Optional[str] = Field()
    problems: list["Problem"] = Relationship(link_model=ContestTask)
    registrations: list[ContestRegistration] = Relationship(back_populates="contest")
    submissions: list["Submission"] = Relationship(back_populates="contest")

    def __str__(self): return self.name
    def __repr__(self): return f"Contest({self.name} {self.start_time} -> {self.end_time})"

