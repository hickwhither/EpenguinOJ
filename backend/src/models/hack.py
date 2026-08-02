from typing import *
from sqlmodel import *

if TYPE_CHECKING:
    from .user import User
    from .submission import Submission


class HackPublic(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    status: Optional[str] = Field(default=None)


class Hack(HackPublic, table=True):
    language: str = Field(index=True)
    source: str = Field(sa_type=TEXT)

    submission_id: int = Field(foreign_key="submission.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")

    submission: "Submission" = Relationship(back_populates="hacks")
    user: "User" = Relationship(back_populates="hacks")