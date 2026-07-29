import json
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
)
from sqlmodel import select

from src.database import async_session_maker
from src.models import Contest


@register(Contest, sqlalchemy_sessionmaker=async_session_maker)
class ContestAdmin(SqlAlchemyModelAdmin):
    menu_section = "Contest"
    list_display = ("id", "name", "start_time", "end_time")
    list_display_links = ("id", "name")
    search_fields = ("name", "description")
    formfield_overrides = {
        "description": (WidgetType.TextArea),
        "password": (WidgetType.PasswordInput, {"required": False}),
    }

