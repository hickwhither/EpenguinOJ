import asyncio
import json
import time

from fastadmin import (
    SqlAlchemyModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
)
from sqlmodel import select
from src.database import async_session_maker
from src.models import Submission
from src.services.submission import rejudge_submissions
from ..config import redis_client
from .. import TimestampAdminMixin


@register(Submission, sqlalchemy_sessionmaker=async_session_maker)
class SubmissionAdmin(TimestampAdminMixin, SqlAlchemyModelAdmin):
    menu_section = "Judging"
    list_display = ("id", "date_created", "status", "language", )
    list_display_links = ("id",)
    list_filter = ("status", "language", "judger_name", "user_id", "contest_registration_id", "problem_id")
    search_fields = ("source", "error")
    readonly_fields = ("id", "date_created")
    timestamp_fields = ("date_created", "judged_date")
    formfield_overrides = {
        "source": (WidgetType.TextArea, {}),
        "error": (WidgetType.TextArea, {}),
    }

    actions = ("rejudge", "rejudge_all_submission")

    @action(description="Rejudge submissions")
    async def rejudge(self, ids: list[int] | None = None):
        if not ids:
            return ActionResponseSchema(
                type=ActionResponseType.MESSAGE, data="No submissions selected"
            )
        async with async_session_maker() as session:
            stmt = select(Submission).where(Submission.id.in_(ids))
            submissions = (await session.scalars(stmt)).all()
            if not submissions:
                return ActionResponseSchema(
                    type=ActionResponseType.MESSAGE, data="No submissions found"
                )
            count = await rejudge_submissions(session, redis_client, submissions)
        return ActionResponseSchema(
            type=ActionResponseType.MESSAGE,
            data=f"Queued {count} submission(s) for rejudge",
        )
