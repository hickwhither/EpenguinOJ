from .config import setup_admin_env
setup_admin_env()

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastadmin import fastapi_app as admin_app
from fastadmin.models.base import ModelAdmin

_admin_tz = ZoneInfo(os.environ.get("ADMIN_TIMEZONE", "Asia/Ho_Chi_Minh"))


class TimestampAdminMixin:
    timestamp_fields: tuple[str, ...] = ()

    async def serialize_obj_attributes(self, obj, attributes, list_view=False):
        data = await super().serialize_obj_attributes(obj, attributes, list_view)
        for field in self.timestamp_fields:
            if field in data and isinstance(data[field], (int, float)):
                dt = datetime.fromtimestamp(data[field], tz=_admin_tz)
                data[field] = dt.strftime("%Y-%m-%d %H:%M:%S")
        return data

    def deserialize_value(self, field, value):
        if field.column_name in self.timestamp_fields:
            return value
        return super().deserialize_value(field, value)

    async def save_model(self, id, payload, request=None):
        for field in self.timestamp_fields:
            if field in payload and isinstance(payload[field], str) and payload[field]:
                dt = datetime.fromisoformat(payload[field])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=_admin_tz)
                payload[field] = int(dt.timestamp())
        return await super().save_model(id, payload, request)


from .views import accounts, judging, problem

__all__ = ["admin_app", "TimestampAdminMixin"]
