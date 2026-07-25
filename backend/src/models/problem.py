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
    answer: str = Field()
    tests: Optional[dict[str, dict[str, Any]]] = Field(default_factory=dict, sa_column=Column(JSON))
    submissions: list["Submission"] = Relationship(back_populates="problem", cascade_delete=True)
    hacks: list["Hack"] = Relationship(back_populates="problem", cascade_delete=True)

    def __str__(self): return self.name
    def __repr__(self): return f"Problem({self.name})"


class Hack(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    batch: Optional[str] = Field(index=True)
    language: str = Field(index=True)
    source: str = Field(sa_type=TEXT)
    verified: bool = Field(default=False)

    user_id: Optional[int] = Field(foreign_key="user.id", ondelete="SET NULL")
    problem_id: int = Field(foreign_key="problem.id", ondelete="CASCADE")

    user: Optional["User"] = Relationship(back_populates="hacks")
    problem: Problem = Relationship(back_populates="hacks")
