import json
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
)
from sqlmodel import select
from src.database import async_session_maker
from src.models import Submission, UserHack
from ..config import redis_client
from src.redis_sync import sync_problem_to_redis
from .. import TimestampAdminMixin


@register(Submission, sqlalchemy_sessionmaker=async_session_maker)
class SubmissionAdmin(TimestampAdminMixin, SqlAlchemyModelAdmin):
    menu_section = "Judging"
    list_display = ("id", "date_created", "status", "score", "language", )
    list_display_links = ("id",)
    list_filter = ("status", "language", "judger_name", "user_id", "contest_id", "problem_id")
    search_fields = ("source", "error")
    readonly_fields = ("id", "date_created")
    timestamp_fields = ("date_created", "judged_date")
    formfield_overrides = {
        "source": (WidgetType.TextArea, {}),
        "error": (WidgetType.TextArea, {}),
    }

    actions = ("rejudge", "rejudge_all_submission")

    @action(description="Rejudge submissions")
    async def rejudge(self, ids: list[int]|None = None):
        async with async_session_maker() as session:
            stmt = select(Submission).where(Submission.id.in_(ids))
            result = await session.exec(stmt)
            submissions = result.all()
            if not submissions:
                return

            problem_ids = {sub.problem_id for sub in submissions}
            for problem_id in problem_ids:
                await sync_problem_to_redis(redis_client, problem_id)

            payloads = [
                json.dumps({
                    "submission_id": sub.id,
                    "problem_id": sub.problem_id,
                    "language": sub.language,
                    "source": sub.source,
                })
                for sub in submissions
            ]

            if payloads:
                await redis_client.rpush("submission", *payloads)


@register(UserHack, sqlalchemy_sessionmaker=async_session_maker)
class UserHackAdmin(TimestampAdminMixin, SqlAlchemyModelAdmin):
    menu_section = "Judging"
    list_display = ("id", "date_created", "status", "percentage", "language", "subtask", )
    list_display_links = ("id",)
    list_filter = ("status", "language", "judger_name", "user_id", "submission_id", "subtask_id")
    search_fields = ("source", "error")
    readonly_fields = ("id", "date_created")
    timestamp_fields = ("date_created",)
    formfield_overrides = {
        "source": (WidgetType.TextArea, {}),
        "error": (WidgetType.TextArea, {}),
    }
