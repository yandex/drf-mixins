from typing import TYPE_CHECKING, Any

from asgiref.sync import iscoroutinefunction
from django.db import models
from django.db.models import QuerySet

if TYPE_CHECKING:
    from rest_framework.generics import GenericAPIView
else:
    GenericAPIView = Any


async def aget_view_queryset(view: GenericAPIView) -> QuerySet[models.Model]:
    if iscoroutinefunction(view.get_queryset):
        return await view.get_queryset()
    return view.get_queryset()
