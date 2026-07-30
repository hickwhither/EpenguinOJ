from typing import *
from sqlmodel import *
from src.utils import utcnow

if TYPE_CHECKING:
    from .user import User
    from .contest import Contest


class ContestTask(SQLModel, table=True):
    contest_id: int = Field(foreign_key="contest.id", primary_key=True, ondelete="CASCADE")
    problem_id: int = Field(foreign_key="problem.id", primary_key=True, ondelete="CASCADE")

    display_order: int = Field(default=0)
    max_score: float = Field(default=100.0)


class ContestRegistrationBase(SQLModel):
    registered_at: int = Field(default_factory=utcnow)
    total_score: float = Field(default=0.0)
    penalty: float = Field(default=0.0)
    old_rating: Optional[int] = Field()
    new_rating: Optional[int] = Field()


class ContestRegistration(ContestRegistrationBase, table=True):
    contest_id: int = Field(foreign_key="contest.id", primary_key=True, ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", primary_key=True, ondelete="CASCADE")
    user: "User" = Relationship(back_populates="registrations")
    contest: "Contest" = Relationship(back_populates="registrations")

    def __str__(self): return f"{self.user.username}"
