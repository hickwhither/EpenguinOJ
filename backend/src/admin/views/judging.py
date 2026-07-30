import json
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
) 

from src.database import async_session_maker
from src.models import Submission, UserHack
from ..config import redis_client
from src.redis_sync import sync_problem_to_redis


@register(Submission, sqlalchemy_sessionmaker=async_session_maker)
class SubmissionAdmin(SqlAlchemyModelAdmin):
    menu_section = "Judging"
    list_display = ("id", "date_created", "status", "score", "language", )
    list_display_links = ("id",)
    list_filter = ("status", "language", "judger_name", "user_id", "contest_id", "problem_id")
    search_fields = ("source", "error")
    readonly_fields = ("id", "date_created")
    formfield_overrides = {
        "source": (WidgetType.TextArea, {}),
        "error": (WidgetType.TextArea, {}),
    }

    actions = ("rejudge", "rejudge_all_submission")
    
    @action(description="Rejudge all submissions")
    async def rejudge(self, id: int):
        async with async_session_maker() as session:
            sub = await session.get(Submission, id)
            payload = {
                "submission_id": sub.id,
                "problem_id": sub.problem_id,
                "language": sub.language,
                "source": sub.source,
            }
            await sync_problem_to_redis(redis_client, sub.problem_id)
            await redis_client.rpush("submission", json.dumps(payload))


@register(UserHack, sqlalchemy_sessionmaker=async_session_maker)
class UserHackAdmin(SqlAlchemyModelAdmin):
    menu_section = "Judging"
    list_display = ("id", "date_created", "status", "percentage", "language", "subtask", )
    list_display_links = ("id",)
    list_filter = ("status", "language", "judger_name", "user_id", "submission_id", "subtask_id")
    search_fields = ("source", "error")
    readonly_fields = ("id", "date_created")
    formfield_overrides = {
        "source": (WidgetType.TextArea, {}),
        "error": (WidgetType.TextArea, {}),
    }

