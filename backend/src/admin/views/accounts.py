from fastadmin import SqlAlchemyModelAdmin, WidgetType, register
from sqlalchemy import select

from src.database import async_session_maker
from src.dependencies import hash_password, verify_password
from src.models import User

@register(User, sqlalchemy_sessionmaker=async_session_maker)
class UserAdmin(SqlAlchemyModelAdmin):
    menu_section = "Accounts"
    list_display = ("id", "username", "email", "active", "superuser", "date_joined")
    list_display_links = ("id", "username")
    list_filter = ("active", "superuser", "rank")
    search_fields = ("username", "email", "discord_id", "nickname")
    readonly_fields = ("id", "date_joined", "last_login")
    formfield_overrides = {
        "password": (WidgetType.PasswordInput, {"passwordModalForm": True}),
        "bio": (WidgetType.TextArea),
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