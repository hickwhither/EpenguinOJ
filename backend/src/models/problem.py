from typing import *
from sqlmodel import *

from .links import ContestTask

if TYPE_CHECKING:
    from .user import User
    from .submission import Submission
    from .contest import Contest


class ProblemPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    name: Optional[str] = Field(index=True)


class ProblemView(ProblemPublic):
    statement: Optional[str] = Field(sa_type=TEXT)
    time_limit: float = Field(default=1)
    memory_limit: int = Field(default=32768)
    input: Optional[str] = Field()
    output: Optional[str] = Field()


class Problem(ProblemView, table=True):
    is_public: bool = Field(default=False, index=True)
    answer: str = Field(sa_type=TEXT)
    checker: Optional[str] = Field(sa_type=TEXT)
    submissions: list["Submission"] = Relationship(back_populates="problem", cascade_delete=True)
    subtasks: list["Subtask"] = Relationship(back_populates="problem", cascade_delete=True)

    def __str__(self): return self.name
    def __repr__(self): return f"Problem({self.name})"


class SubtaskPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    name: Optional[str] = Field(index=True)
    description: Optional[str] = Field(sa_type=TEXT)
    points: int = Field(default=1)


class SubtaskView(SubtaskPublic): # For Judgers can see what in here
    generator: str = Field(sa_type=TEXT)
    validator: str = Field(sa_type=TEXT)
    seeds: list[Any] = Field(default_factory=list, sa_column=Column(JSON))


class Subtask(SubtaskView, table=True):
    problem_id: int = Field(foreign_key="problem.id", ondelete="CASCADE")
    problem: Problem = Relationship(back_populates="subtasks")
    hacks: list["Hack"] = Relationship(back_populates="subtask", cascade_delete=True)
    userhacks: list["UserHack"] = Relationship(back_populates="subtask", cascade_delete=True)

    def __str__(self): return self.name


class Hack(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: Optional[str] = Field(index=True)
    description: Optional[str] = Field(sa_type=TEXT)
    language: str = Field(index=True)
    source: str = Field(sa_type=TEXT)

    subtask_id: int = Field(foreign_key="subtask.id", ondelete="CASCADE")
    subtask: Subtask = Relationship(back_populates="hacks")


class UserHack(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    language: str = Field(index=True)
    source: str = Field(sa_type=TEXT)
    status: Optional[str] = Field(default=None)

    subtask_id: int = Field(foreign_key="subtask.id", ondelete="CASCADE")
    submission_id: int = Field(foreign_key="submission.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")

    subtask: Subtask = Relationship(back_populates="userhacks")
    submission: "Submission" = Relationship(back_populates="userhacks")
    user: "User" = Relationship(back_populates="userhacks")

