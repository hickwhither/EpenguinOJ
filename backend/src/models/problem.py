from typing import *
from sqlmodel import *
from sqlalchemy import JSON

if TYPE_CHECKING:
    from .contest import Contest
    from .submission import Submission


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
    display_order: int = Field(default=0)
    package: dict = Field(default_factory=dict, sa_column=Column(JSON))
    submissions: list["Submission"] = Relationship(back_populates="problem", cascade_delete=True)
    contest_id: Optional[int] = Field(foreign_key="contest.id", ondelete="SET NULL")
    contest: Optional["Contest"] = Relationship(back_populates="problems")

    def __str__(self): return self.name
    def __repr__(self): return f"Problem({self.name})"
