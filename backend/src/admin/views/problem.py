from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
)
from sqlmodel import select

from src.database import async_session_maker
from src.models import Submission, Problem
from ..config import redis_client
from .judging import SubmissionAdmin, rejudge_submissions


# INLINES
class SubmissionInLine(SubmissionAdmin, SqlAlchemyInlineModelAdmin):
    model = Submission
    fk_name = "problem_id"

# ---

@register(Problem, sqlalchemy_sessionmaker=async_session_maker)
class ProblemAdmin(SqlAlchemyModelAdmin):
    menu_section = "Problem"
    list_display = ("id", "name", "is_public", "time_limit", "memory_limit")
    list_display_links = ("id", "name")
    list_filter = ("is_public",)
    search_fields = ("name", "statement")
    formfield_overrides = {
        "statement": (WidgetType.TextArea, {}),
        "package": (WidgetType.JsonTextArea, {}),
    }
    inlines = (SubmissionInLine,)

    actions = ("sync_to_redis", "rejudge_all_submission")

    @action(description="Rejudge all submissions of selected problems")
    async def rejudge_all_submission(self, ids: list[int]):
        if not ids:
            return ActionResponseSchema(
                type=ActionResponseType.MESSAGE, data="No problems selected"
            )
        async with async_session_maker() as session:
            statement = select(Submission).where(Submission.problem_id.in_(ids))
            submissions = (await session.scalars(statement)).all()
            if not submissions:
                return ActionResponseSchema(
                    type=ActionResponseType.MESSAGE, data="No submissions found"
                )
            count = await rejudge_submissions(session, redis_client, submissions)
        return ActionResponseSchema(
            type=ActionResponseType.MESSAGE,
            data=f"Queued {count} submission(s) across {len(ids)} problem(s)",
        )
