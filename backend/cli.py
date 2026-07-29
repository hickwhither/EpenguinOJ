import asyncio

import typer
from sqlmodel import select

from src.database import async_session_maker, init_db
from src.models import User

app = typer.Typer(help="HWOJ CLI tools.")


@app.command()
def set_superuser(username: str):
    """Set a user as superuser (Admin)."""
    asyncio.run(_set_superuser(username))


async def _set_superuser(username: str):
    await init_db()
    async with async_session_maker() as session:
        user = (
            await session.exec(select(User).where(User.username == username))
        ).first()
        if user is None:
            typer.echo(f"User '{username}' was not found.", err=True)
            raise typer.Exit(code=1)
        user.superuser = True
        session.add(user)
        await session.commit()
        typer.echo(f"User '{username}' is now a superuser.")


if __name__ == "__main__":
    app()
