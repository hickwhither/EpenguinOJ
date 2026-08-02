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
from starlette.middleware.sessions import SessionMiddleware

from .database import init_db
from .services.submission import background_sync_submission


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.state.redis = aioredis.from_url(redis_url, decode_responses=True)
    print("Redis connected!")
    consumer = asyncio.create_task(background_sync_submission(app.state.redis))
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
    from .webhook import router as webhook_router

    app.include_router(api_router)
    app.include_router(webhook_router)

    return app
