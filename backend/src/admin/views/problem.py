import json
from pathlib import Path
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
) 
from sqlmodel import select

from src.database import async_session_maker
from src.models import Submission, Subtask, Problem, Hack
from ..config import redis_client
from src.redis_sync import sync_problem_to_redis
from .judging import SubmissionAdmin


@register(Subtask, sqlalchemy_sessionmaker=async_session_maker)
class SubtaskAdmin(SqlAlchemyModelAdmin):
    menu_section = "Problem"
    list_display = ("id", "problem_id", "name", "description", "points")
    list_filter = {"problem_id", }
    search_fields = ("name", "description", )
    formfield_overrides = {
        "description": (WidgetType.TextArea,{}),
        "generator": (WidgetType.TextArea, {}),
        "validator": (WidgetType.TextArea, {}),
        "seeds": (WidgetType.JsonTextArea, {}),
    }



@register(Hack, sqlalchemy_sessionmaker=async_session_maker)
class HackAdmin(SqlAlchemyModelAdmin):
    menu_section = "Problem"
    list_display = ("id", "description", "subtask" "language",)
    list_filter = ("subtask", "language")
    search_fields = ("description", "subtask")
    formfield_overrides = {
        "source": (WidgetType.TextArea, {}),
    }


# INLINES
class SubtaskInline(SubtaskAdmin, SqlAlchemyInlineModelAdmin):
    model = Subtask
    fk_name = "problem_id"


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
        "answer": (WidgetType.TextArea, {}),
        "checker": (WidgetType.TextArea, {}),
    }
    inlines = (SubtaskInline, SubmissionInLine,)

    actions = ("sync_to_redis", "rejudge_all_submission")

    @action(description="Rejudge all submissions")
    async def rejudge_all_submission(self, request, id: int):
        async with async_session_maker() as session:
            statement = select(Submission).where(Submission.problem_id == id)
            submissions = (await session.scalars(statement)).all()
            for sub in submissions:
                payload = {
                    "submission_id": sub.id,
                    "problem_id": sub.problem_id,
                    "language": sub.language,
                    "source": sub.source,
                }
                await sync_problem_to_redis(redis_client, id)
                await redis_client.rpush("submission", json.dumps(payload))
        return ActionResponseSchema(type=ActionResponseType.MESSAGE, data=f"Queued {len(submissions)} submission(s) from {id}")


