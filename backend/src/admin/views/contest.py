import json
from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
) 
from sqlmodel import select

from src.database import async_session_maker
from src.models import Submission, Contest, Problem, Subtask, Hack
from ..config import redis_client
from src.redis_sync import sync_hack_to_redis, sync_subtask_to_redis, sync_problem_to_redis


class RedisSyncMixin:
    redis_prefix: str | None = None
    sync_func = None

    async def save_model(self, id: int | None, payload: dict):
        obj = await super().save_model(id, payload)
        obj_id = getattr(obj, "id", None) or id or payload.get("id")
        if obj_id and self.sync_func:
            await self.sync_func(redis_client, obj_id)
        return obj

    async def delete_model(self, id: int) -> None:
        await super().delete_model(id)
        if self.redis_prefix:
            await redis_client.delete(f"{self.redis_prefix}:{id}")


# INLINES
class SubtaskInline(SqlAlchemyInlineModelAdmin):
    model = Subtask
    list_display = ("id", "problem_id", "name", "description", "points")
    fk_name = "problem_id"
    formfield_overrides = {
        "description": (WidgetType.TextArea, {"rows": 2}),
        "generator": (WidgetType.TextArea, {"rows": 4}),
        "validator": (WidgetType.TextArea, {"rows": 4}),
        "seeds": (WidgetType.TextArea, {"rows": 2}),
    }


# REGISTERS
@register(Problem, sqlalchemy_sessionmaker=async_session_maker)
class ProblemAdmin(SqlAlchemyModelAdmin):
    redis_prefix = "problem"
    sync_func = staticmethod(sync_problem_to_redis)

    menu_section = "Contest"
    list_display = ("id", "name", "is_public", "time_limit", "memory_limit")
    list_display_links = ("id", "name")
    list_filter = ("is_public",)
    search_fields = ("name", "statement")
    inlines = (SubtaskInline,)
    formfield_overrides = {
        "statement": (WidgetType.TextArea, {"rows": 12}),
        "answer": (WidgetType.TextArea, {"rows": 12}),
        "checker": (WidgetType.TextArea, {"rows": 12}),
    }
    actions = ("sync_to_redis", "rejudge_all_submission")

    @action(description="Sync to redis")
    async def sync_to_redis(self, request, id: int):
        await sync_problem_to_redis(redis_client, id)
        return ActionResponseSchema(type=ActionResponseType.MESSAGE, data=f"Synced {id}")
    # 
    @action(description="Rejudge all submissions")
    async def rejudge_all_submission(self, request, id: int):
        await sync_problem_to_redis(redis_client, id)
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
                await redis_client.rpush("submission", json.dumps(payload))
        return ActionResponseSchema(type=ActionResponseType.MESSAGE, data=f"Queued {len(submissions)} submission(s) from {id}")


@register(Subtask, sqlalchemy_sessionmaker=async_session_maker)
class SubtaskAdmin(RedisSyncMixin, SqlAlchemyModelAdmin):
    redis_prefix = "subtask"
    sync_func = staticmethod(sync_subtask_to_redis)

    menu_section = "Contest"
    list_display = ("id", "problem_id", "points")
    list_filter = {"problem_id", }
    search_fields = ("description", )
    formfield_overrides = {
        "description": (WidgetType.TextArea, {"rows": 4}),
        "generator": (WidgetType.TextArea, {"rows": 8}),
        "validator": (WidgetType.TextArea, {"rows": 8}),
        "seeds": (WidgetType.TextArea, {"rows": 1}),
    }

@register(Hack, sqlalchemy_sessionmaker=async_session_maker)
class HackAdmin(SqlAlchemyModelAdmin):
    redis_prefix = "hack"
    sync_func = staticmethod(sync_hack_to_redis)
    
    menu_section = "Contest"
    list_display = ("id", "name",  "language",)
    list_filter = ("language", "subtask_id")
    search_fields = ("name", "description", )


@register(Contest, sqlalchemy_sessionmaker=async_session_maker)
class ContestAdmin(SqlAlchemyModelAdmin):
    menu_section = "Contest"
    list_display = ("id", "name", "start_time", "end_time")
    list_display_links = ("id", "name")
    search_fields = ("name", "description")
    formfield_overrides = {
        "description": (WidgetType.TextArea, {"rows": 4}),
        "password": (WidgetType.PasswordInput, {"required": False}),
    }

