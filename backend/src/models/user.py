from typing import *
from sqlmodel import *
from sqlalchemy import JSON, BigInteger
from src.utils import utcnow
import random

from .links import ContestRegistration

if TYPE_CHECKING:
    from .problem import UserHack
    from .submission import Submission
    from .contest import Contest

DEFAULT_AVATARS = [
    "dolly.webp",
    "ei_snailchan.webp",
    "ei_snailien.webp",
    "nanahira.webp",
    "seal.webp",
    "sheep.webp",
    "Telu.webp",
    "xchara.webp",
]


class UserPublic(SQLModel):
    username: str = Field(unique=True, index=True)
    nickname: Optional[str] = Field()
    avatar_url: Optional[str] = Field(default_factory=lambda: "/default-avatars/"+random.choice(DEFAULT_AVATARS))
    rating: Optional[int] = Field(index=True) # Contest rating
    elo: Optional[int] = Field(index=True) # Solo cf
    rank: Optional[str] = Field(index=True)
    badges: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class UserView(UserPublic):
    bio: Optional[str] = Field()


class User(UserView, table=True):
    id: Optional[int] = Field(primary_key=True)
    password: str = Field()
    email: str = Field(unique=True, index=True)
    discord_id: Optional[str] = Field(index=True)
    cf_handle: Optional[str] = Field(index=True)

    # Permissions
    active: bool = Field(default=True, index=True)
    superuser: bool = Field(default=False, index=True)
    permissions: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Timestamps
    last_login: Optional[int] = Field(default=None, index=True, sa_type=BigInteger)
    date_joined: int = Field(default_factory=utcnow, index=True, sa_type=BigInteger)

    # Relationships
    registrations: list[ContestRegistration] = Relationship(back_populates="user", cascade_delete=True)
    submissions: list["Submission"] = Relationship(back_populates="user", cascade_delete=True)
    userhacks: list["UserHack"] = Relationship(back_populates="user", cascade_delete=True)

    def __str__(self): return self.username
    def __repr__(self):return f"User({self.username}-{self.discord_id or self.email})"
