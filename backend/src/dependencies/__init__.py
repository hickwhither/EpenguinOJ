from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    total_pages: int

from pwdlib import PasswordHash
pwd = PasswordHash.recommended()
def hash_password(password: str | bytes): return pwd.hash(password)
def verify_password(password: str | bytes, hash: str | bytes): return pwd.verify(password, hash)