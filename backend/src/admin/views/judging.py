import json
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
) 

from src.database import async_session_maker
from src.models import Submission, UserHack
from ..config import redis_client


@register(Submission, sqlalchemy_sessionmaker=async_session_maker)
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

    actions = ("rejudge", "rejudge_all_submission")
    
    @action(description="Rejudge all submissions")
    async def rejudge(self, request, id: int):
        async with async_session_maker() as session:
            sub = await session.get(Submission, id)
            payload = {
                "submission_id": sub.id,
                "problem_id": sub.problem_id,
                "language": sub.language,
                "source": sub.source,
            }
            await redis_client.rpush("submission", json.dumps(payload))


@register(UserHack, sqlalchemy_sessionmaker=async_session_maker)
class UserHackAdmin(SqlAlchemyModelAdmin):
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

