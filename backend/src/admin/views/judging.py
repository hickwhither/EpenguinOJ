import json
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
)
from sqlmodel import select
from src.database import async_session_maker
from src.models import Submission, UserHack, SUBMISSION_STATUS
from ..config import redis_client
from src.redis_sync import sync_problem_to_redis
from .. import TimestampAdminMixin


async def rejudge_submissions(session, redis, submissions) -> int:
    """Reset submissions to QUEUED and enqueue them for the judge.

    Returns the number of submissions queued.
    """
    submissions = list(submissions)
    if not submissions:
        return 0

    for problem_id in {sub.problem_id for sub in submissions}:
        await sync_problem_to_redis(redis, problem_id)

    payloads = [
        json.dumps({
            "submission_id": sub.id,
            "problem_id": sub.problem_id,
            "language": sub.language,
            "source": sub.source,
        })
        for sub in submissions
    ]
    await redis.rpush("submission", *payloads)

    for sub in submissions:
        sub.status = SUBMISSION_STATUS.QUEUED
        sub.score = 0.0
        sub.max_score = 0.0
        sub.time_used = None
        sub.memory_used = None
        sub.results = None
        sub.error = None
        sub.judger_name = None
        sub.judged_date = None
        session.add(sub)
    await session.commit()

    return len(submissions)


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
