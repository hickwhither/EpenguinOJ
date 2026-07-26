import sys, asyncio
from sqlmodel import select
from src.database import init_db, get_session
from src.models import User

async def set_superuser(username: str) -> bool:
    await init_db()
    with get_session() as session:
        user = await session.exec(select(User).where(User.username == username)).first()
        if user is None:
            return False
        user.superuser = True
        session.add(user)
        session.commit()
        return True


async def main(argv: list[str] | None = None) -> int:
    argv = argv[1:]
    for username in argv:
        if awaitset_superuser(username):
            print(f"User '{username}' is now a superuser.")
        else:
            print(f"User '{username}' was not found.", file=sys.stderr)
    

if __name__ == "__main__":
    asyncio.run(main(sys.argv))
