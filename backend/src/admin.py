import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .database import get_database_url
from .models import Contest, Problem, Submission, User
from .dependencies import hash_password, verify_password

os.environ.setdefault("ADMIN_USER_MODEL", "User")
os.environ.setdefault("ADMIN_USER_MODEL_USERNAME_FIELD", "username")
os.environ.setdefault("ADMIN_SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
os.environ.setdefault("ADMIN_SITE_NAME", f"{os.getenv('APP_NAME', 'HWOJ')} Admin")

os.environ.setdefault("ADMIN_SITE_SIGN_IN_LOGO", "/logo.png")
os.environ.setdefault("ADMIN_SITE_HEADER_LOGO", "/logo.png")
os.environ.setdefault("ADMIN_SITE_FAVICON", "/logo.png")

from fastadmin import SqlAlchemyModelAdmin, WidgetType, fastapi_app as admin_app, register


def get_async_database_url() -> str:
    database_url = get_database_url()
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if database_url.startswith("mysql+pymysql://"):
        return database_url.replace("mysql+pymysql://", "mysql+asyncmy://", 1)
    if database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+asyncmy://", 1)
    return database_url


admin_engine = create_async_engine(get_async_database_url())
admin_sessionmaker = async_sessionmaker(admin_engine, expire_on_commit=False)


@register(User, sqlalchemy_sessionmaker=admin_sessionmaker)
class UserAdmin(SqlAlchemyModelAdmin):
    menu_section = "Accounts"
    list_display = ("id", "username", "email", "active", "superuser", "date_joined")
    list_display_links = ("id", "username")
    list_filter = ("active", "superuser", "rank")
    search_fields = ("username", "email", "discord_id", "nickname")
    readonly_fields = ("id", "date_joined", "last_login")
    formfield_overrides = {
        "password": (WidgetType.PasswordInput, {"passwordModalForm": True}),
        "bio": (WidgetType.TextArea, {"rows": 4}),
    }

    async def authenticate(self, username: str, password: str) -> int | None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            query = select(self.model_cls).filter_by(username=username, superuser=True, active=True)
            result = await session.scalars(query)
            user = result.first()
            if user and verify_password(password, user.password):
                return user.id
        return None

    async def change_password(self, id: int, password: str) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            user = await session.get(self.model_cls, id)
            if user:
                user.password = hash_password(password)
                await session.commit()


@register(Problem, sqlalchemy_sessionmaker=admin_sessionmaker)
class ProblemAdmin(SqlAlchemyModelAdmin):
    menu_section = "Content"
    list_display = ("id", "code", "name", "is_public", "type", "time_limit", "memory_limit")
    list_display_links = ("id", "code", "name")
    list_filter = ("is_public", "type")
    search_fields = ("code", "name", "statement")
    formfield_overrides = {
        "statement": (WidgetType.TextArea, {"rows": 12}),
    }


@register(Contest, sqlalchemy_sessionmaker=admin_sessionmaker)
class ContestAdmin(SqlAlchemyModelAdmin):
    menu_section = "Content"
    list_display = ("id", "name", "start_time", "end_time")
    list_display_links = ("id", "name")
    search_fields = ("name", "description")
    formfield_overrides = {
        "description": (WidgetType.TextArea, {"rows": 4}),
        "password": (WidgetType.PasswordInput, {"required": False}),
    }

    async def get_participants_list(self, obj: Contest) -> str:
        if not obj.registrations:
            return "Chưa có"
        # Lấy tối đa 5 người đầu tiên để tránh bị dài giao diện
        names = [reg.user.username for reg in obj.registrations[:5]]
        total = len(obj.registrations)
        res = ", ".join(names)
        if total > 5:
            res += f" và {total - 5} người khác..."
        return res

    get_participants_list.short_description = "Participants"


@register(Submission, sqlalchemy_sessionmaker=admin_sessionmaker)
class SubmissionAdmin(SqlAlchemyModelAdmin):
    menu_section = "Judging"
    list_display = ("id", "date_created", "status", "percentage", "language", "user_id", "problem_id", "contest_id")
    list_display_links = ("id",)
    list_filter = ("status", "language", "judger_name")
    search_fields = ("source", "error")
    readonly_fields = ("id", "date_created")
    formfield_overrides = {
        "source": (WidgetType.TextArea, {"rows": 12}),
        "error": (WidgetType.TextArea, {"rows": 4}),
    }

