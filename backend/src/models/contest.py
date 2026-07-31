from typing import *
from sqlmodel import *
from sqlalchemy import BigInteger

from .links import ContestTask, ContestRegistration

if TYPE_CHECKING:
    from .user import User
    from .problem import Problem
    from .submission import Submission


class ContestPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    name: Optional[str] = Field(index=True)
    registration_start: Optional[int] = Field(default=None, index=True, sa_type=BigInteger)
    registration_end: Optional[int] = Field(default=None, index=True, sa_type=BigInteger)
    start_time: int = Field(index=True, sa_type=BigInteger)
    end_time: int = Field(index=True, sa_type=BigInteger)


class ContestView(ContestPublic):
    description: Optional[str] = Field(sa_type=TEXT)


class Contest(ContestView, table=True):
    password: Optional[str] = Field()
    problems: list["Problem"] = Relationship(link_model=ContestTask)
    registrations: list[ContestRegistration] = Relationship(back_populates="contest")
    submissions: list["Submission"] = Relationship(back_populates="contest")

    def __str__(self): return self.name
    def __repr__(self): return f"Contest({self.name} {self.start_time} -> {self.end_time})"
