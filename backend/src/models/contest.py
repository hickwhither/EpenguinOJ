from typing import *
from sqlmodel import *
from sqlalchemy import BigInteger, UniqueConstraint
from src.services.timing import utcnow


if TYPE_CHECKING:
    from .user import User
    from .problem import Problem
    from .submission import Submission


# Nodels
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
    problems: list["Problem"] = Relationship(back_populates="contest")
    registrations: list["ContestRegistration"] = Relationship(back_populates="contest")

    def __str__(self): return self.name
    def __repr__(self): return f"Contest({self.name} {self.start_time} -> {self.end_time})"


# Links
class ContestRegistrationPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    registered_at: int = Field(default_factory=utcnow, sa_type=BigInteger)
    old_rating: Optional[int] = Field()
    new_rating: Optional[int] = Field()
    total_score: float = Field(default=0.0)
    problem_scores: dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    penalty: int = Field(default=0, sa_type=BigInteger)


class ContestRegistrationOut(ContestRegistrationPublic):
    contest: Optional[ContestPublic] = None


class ContestRegistration(ContestRegistrationPublic, table=True):
    __tablename__ = "contest_registration"
    __table_args__ = (UniqueConstraint("contest_id", "user_id"),)
    contest_id: int = Field(foreign_key="contest.id", index=True, ondelete="CASCADE")
    contest: "Contest" = Relationship(back_populates="registrations")
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: "User" = Relationship(back_populates="registrations")
    submissions: list["Submission"] = Relationship(back_populates="contest_registration", cascade_delete=True)

    def __str__(self): return f"{self.user.username}"
