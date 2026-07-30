import asyncio
from dotenv import load_dotenv
load_dotenv()
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi_pagination import add_pagination
import redis.asyncio as aioredis
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from .database import async_session_maker, init_db
from .models import ContestRegistration, Problem, Submission
from .utils import utcnow


async def consume_results(redis):
    """Background task: pop finished results from Redis list and persist to DB."""
    while True:
        try:
            result = await redis.brpop("results", timeout=1)
            if not result:
                continue
            _, payload = result
            data = json.loads(payload)
            submission_id = data["submission_id"]
            async with async_session_maker() as session:
                sub = await session.get(Submission, submission_id)
                if sub:
                    sub.status = data.get("status", sub.status)
                    sub.score = data.get("score", sub.score)
                    sub.max_score = data.get("max_score", sub.max_score)
                    sub.time_used = data.get("time_used", sub.time_used)
                    sub.memory_used = data.get("memory_used", sub.memory_used)
                    sub.results = data.get("results", sub.results)
                    sub.error = data.get("error")
                    sub.judger_name = data.get("judger_name", sub.judger_name)
                    sub.judged_date = utcnow()
                    session.add(sub)

                    if sub.contest_id:
                        stmt = select(ContestRegistration).where(
                            ContestRegistration.contest_id == sub.contest_id,
                            ContestRegistration.user_id == sub.user_id,
                        )
                        reg = (await session.scalars(stmt)).first()
                        if reg and data.get("score", 0) > reg.total_score:
                            reg.total_score = data["score"]
                            session.add(reg)

                    await session.commit()
                await redis.delete(f"live:{submission_id}")
        except Exception as e:
            print(f"Consumer error: {e}")
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.state.redis = aioredis.from_url(redis_url, decode_responses=True)
    print("Redis connected!")
    consumer = asyncio.create_task(consume_results(app.state.redis))
    yield
    consumer.cancel()
    await app.state.redis.close()
    print("Redis closed!")


def create_app():
    app_name = os.getenv("APP_NAME", "OnlineJudge")
    app = FastAPI(
        title=app_name, description=f"{app_name} backend", lifespan=lifespan
    )

    add_pagination(app)

    allow_origins = os.getenv("ALLOWED_ORIGINS", "").split() + [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    print("ALLOWED ORIGINS:", allow_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "default-secret-key"),
        session_cookie="session",
        max_age=60 * 60 * 24 * 7,  # 7 days
        same_site="none",
        https_only=True,
    )

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse("./sigma.jpg")

    from .admin import admin_app

    app.mount("/admin", admin_app)

    from .user import router as api_router
    from .webhook import router as judger_router

    app.include_router(api_router)
    app.include_router(judger_router)

    return app