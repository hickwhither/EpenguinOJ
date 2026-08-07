from fastadmin import (
    SqlAlchemyModelAdmin, SqlAlchemyInlineModelAdmin, WidgetType,
    ActionResponseSchema, ActionResponseType,
    register, action,
)
from sqlmodel import select

from src.database import async_session_maker
from src.models import Contest, ContestRegistration, Problem
from src.services.ranking import recompute_registration
from .. import TimestampAdminMixin
from .problem import ProblemAdmin


class ProblemInLine(ProblemAdmin, SqlAlchemyInlineModelAdmin):
    model = Problem
    fk_name = "contest_id"


@register(Contest, sqlalchemy_sessionmaker=async_session_maker)
class ContestAdmin(TimestampAdminMixin, SqlAlchemyModelAdmin):
    menu_section = "Contest"
    list_display = ("id", "name", "start_time", "end_time")
    list_display_links = ("id", "name")
    search_fields = ("name", "description")
    timestamp_fields = ("start_time", "end_time", "registration_start", "registration_end")
    inlines = (ProblemInLine,)
    actions = ("recompute_registrations",)
    formfield_overrides = {
        "description": (WidgetType.TextArea,{}),
        "password": (WidgetType.PasswordInput, {"required": False}),
        "start_time": (WidgetType.DateTimePicker, {"required": True}),
        "end_time": (WidgetType.DateTimePicker, {"required": True}),
        "registration_start": (WidgetType.DateTimePicker, {}),
        "registration_end": (WidgetType.DateTimePicker, {}),
    }

    @action(description="Recompute ranking for selected contests")
    async def recompute_registrations(self, ids: list[int] | None = None):
        if not ids:
            return ActionResponseSchema(
                type=ActionResponseType.MESSAGE, data="No contests selected"
            )
        async with async_session_maker() as session:
            stmt = select(ContestRegistration).where(
                ContestRegistration.contest_id.in_(ids)
            )
            regs = (await session.scalars(stmt)).all()
            for reg in regs:
                await recompute_registration(session, reg.contest_id, reg.user_id)
            await session.commit()
        return ActionResponseSchema(
            type=ActionResponseType.MESSAGE,
            data=f"Recomputed ranking for {len(regs)} registration(s)",
        )
