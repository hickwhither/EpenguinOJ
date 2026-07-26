import os
from redis.asyncio import Redis

# Redis Client
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

def setup_admin_env():
    """Thiết lập các biến môi trường cho FastAdmin"""
    os.environ.setdefault("ADMIN_USER_MODEL", "User")
    os.environ.setdefault("ADMIN_USER_MODEL_USERNAME_FIELD", "username")
    os.environ.setdefault("ADMIN_SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    os.environ.setdefault("ADMIN_SITE_NAME", f"{os.getenv('APP_NAME', 'HWOJ')} Admin")

    os.environ.setdefault("ADMIN_SITE_SIGN_IN_LOGO", "/logo.png")
    os.environ.setdefault("ADMIN_SITE_HEADER_LOGO", "/logo.png")
    os.environ.setdefault("ADMIN_SITE_FAVICON", "/logo.png")