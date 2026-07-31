import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.database import async_session_maker
from src.services.ranking import backfill_all


async def main():
    async with async_session_maker() as session:
        count = await backfill_all(session)
        print(f"Backfilled {count} contest registration(s)")


if __name__ == "__main__":
    asyncio.run(main())
