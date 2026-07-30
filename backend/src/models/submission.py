from typing import *
from sqlmodel import *
from enum import Enum
from datetime import datetime
from sqlalchemy import Index


if TYPE_CHECKING:
    from .user import User
    from .problem import Problem, UserHack
    from .contest import Contest


class SUBMISSION_STATUS(str, Enum):
    QUEUED = "QW"
    COMPILING = "C"
    PROCESSING = "P"
    DONE = "D"


class SUBMISSION_VERDICT(str, Enum):
    ACCEPTED = "OK"
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


class SubmissionPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    status: str = Field(default=SUBMISSION_STATUS.QUEUED, index=True)
    score: Optional[float] = Field(default=0.0)
    max_score: Optional[float] = Field(default=0.0)
    time_used: Optional[float] = Field()
    memory_used: Optional[float] = Field()
    date_created: datetime = Field(default_factory=datetime.now, index=True)


class SubmissionView(SubmissionPublic):
    error: Optional[str] = Field()
    results: Optional[list[dict[str, Any]]] = Field(sa_column=Column(JSON))
    language: str = Field(index=True)
    source: str = Field(sa_type=TEXT)


class Submission(SubmissionView, table=True):
    __table_args__ = (
        # Filter sort: contest -> user -> problem 
        Index("idx_user_problem", "user_id", "problem_id"),
        Index("idx_contest_user", "contest_id", "user_id"),
    )

    judger_name: Optional[str] = Field(index=True)
    judged_date: Optional[datetime] = Field()
    
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    problem_id: int = Field(foreign_key="problem.id", ondelete="CASCADE", index=True)
    contest_id: Optional[int] = Field(foreign_key="contest.id", ondelete="SET NULL")

    user: "User" = Relationship(back_populates="submissions")
    contest: Optional["Contest"] = Relationship(back_populates="submissions")
    problem: "Problem" = Relationship(back_populates="submissions")
    userhacks: "UserHack" = Relationship(back_populates="submission", cascade_delete=True)

    def __str__(self): return f"{self.id}(by {self.user_id})"
    def __repr__(self): return f"Submission({self.id} by {self.user_id})"
