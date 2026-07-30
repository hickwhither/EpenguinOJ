from .config import setup_admin_env
setup_admin_env()

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastadmin import WidgetType, fastapi_app as admin_app, register_encoder
from fastadmin.models.base import ModelAdmin

_admin_tz = ZoneInfo(os.environ.get("ADMIN_TIMEZONE", "UTC"))

register_encoder(datetime, lambda dt: (
    dt.replace(tzinfo=timezone.utc).astimezone(_admin_tz).replace(tzinfo=None)
    if isinstance(dt, datetime) and dt.tzinfo is None
    else dt
))

_orig_deserialize = ModelAdmin.deserialize_value

def _patched_deserialize(self, field, value):
    result = _orig_deserialize(self, field, value)
    if isinstance(result, datetime) and field.form_widget_type == WidgetType.DateTimePicker:
        result = result.replace(tzinfo=_admin_tz).astimezone(timezone.utc).replace(tzinfo=None)
    return result

ModelAdmin.deserialize_value = _patched_deserialize

from .views import accounts, judging, problem

__all__ = ["admin_app"]