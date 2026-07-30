import json
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
)
from sqlmodel import select

from src.database import async_session_maker
from src.models import Contest
from .. import TimestampAdminMixin


@register(Contest, sqlalchemy_sessionmaker=async_session_maker)
class ContestAdmin(TimestampAdminMixin, SqlAlchemyModelAdmin):
    menu_section = "Contest"
    list_display = ("id", "name", "start_time", "end_time")
    list_display_links = ("id", "name")
    search_fields = ("name", "description")
    timestamp_fields = ("start_time", "end_time", "registration_start", "registration_end")
    formfield_overrides = {
        "description": (WidgetType.TextArea,{}),
        "password": (WidgetType.PasswordInput, {"required": False}),
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time": (WidgetType.DateTimePicker, {}),
        "registration_start": (WidgetType.DateTimePicker, {}),
        "registration_end": (WidgetType.DateTimePicker, {}),
    }
