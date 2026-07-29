from .config import setup_admin_env
setup_admin_env()

from .views import accounts, judging, problem
from fastadmin import fastapi_app as admin_app

__all__ = ["admin_app"]