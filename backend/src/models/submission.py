from typing import *
from sqlmodel import *
from sqlalchemy import Column, JSON, Index, TEXT, BigInteger
from src.services.timing import utcnow
from enum import Enum


if TYPE_CHECKING:
    from .user import User
    from .problem import Problem
    from .hack import Hack

    from .contest import ContestRegistration


class SUBMISSION_VERDICT(str, Enum):
    ACCEPTED = "AC"
    PARTIALLY_ACCEPTED = "PAC"
    WRONG_ANSWER = "WA"
    TIME_LIMIT_EXCEEDED = "TLE"
    MEMORY_LIMIT_EXCEEDED = "MLE"
    OUTPUT_LIMIT_EXCEEDED = "OLE"
    INVALID_RETURN = "IR"
    RUNTIME_ERROR = "RTE"
    COMPILE_ERROR = "CE"
    INTERNAL_ERROR = "IE"
    SHORT_CIRCUITED = "SC"
    ABORTED = "AB"


class SUBMISSION_STATUS(str, Enum):
    ACCEPTED = "AC"
    PARTIALLY_ACCEPTED = "PAC"
    WRONG_ANSWER = "WA"
    TIME_LIMIT_EXCEEDED = "TLE"
    MEMORY_LIMIT_EXCEEDED = "MLE"
    OUTPUT_LIMIT_EXCEEDED = "OLE"
    INVALID_RETURN = "IR"
    RUNTIME_ERROR = "RTE"
    COMPILE_ERROR = "CE"
    INTERNAL_ERROR = "IE"
    SHORT_CIRCUITED = "SC"
    ABORTED = "AB"
    QUEUED = "QW"
    COMPILING = "C"
    PROCESSING = "P"


class SubmissionPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    status: str = Field(default=SUBMISSION_STATUS.QUEUED, index=True)
    time: Optional[float] = Field()
    memory: Optional[float] = Field()
    date_created: int = Field(default_factory=utcnow, index=True, sa_type=BigInteger)


class SubmissionView(SubmissionPublic):
    error: Optional[str] = Field()
    results: Optional[list[dict[str, Any]]] = Field(sa_column=Column(JSON))
    language: str = Field(index=True)
    source: str = Field(sa_type=TEXT)


class Submission(SubmissionView, table=True):
    judger_name: Optional[str] = Field(index=True)
    judged_date: Optional[int] = Field(default=None, sa_type=BigInteger)

    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    user: "User" = Relationship(back_populates="submissions")
    problem_id: int = Field(foreign_key="problem.id", ondelete="CASCADE", index=True)
    problem: "Problem" = Relationship(back_populates="submissions")
    contest_registration_id: Optional[int] = Field(foreign_key="contest_registration.id", ondelete="SET NULL")
    contest_registration: Optional["ContestRegistration"] = Relationship(back_populates="submissions")
    hacks: list["Hack"] = Relationship(back_populates="submission", cascade_delete=True)

    def __str__(self): return f"{self.id}(by {self.user_id})"
    def __repr__(self): return f"Submission({self.id} by {self.user_id})"
