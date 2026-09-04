from adrf.shortcuts import aget_object_or_404
from adrf.viewsets import ModelViewSet
from django.db import models
from django.db.models import QuerySet
from rest_framework.request import Request

from yandex_drf_mixins.base.permissions import acheck_object_permissions
from yandex_drf_mixins.base.querysets import aget_view_queryset

from .mixins import (
    ACreateWithRetrieveModelMixin,
    ActionSerializerMixin,
    ADeleteProtectedModelMixin,
    AListModelMixin,
    AListWithAdditionalDataMixin,
    AUpdateOrCreateWithRetrieveModelMixin,
    AUpdateWithRetrieveModelMixin,
)


class ABaseModelViewSet(
    ActionSerializerMixin,
    AListModelMixin,
    ACreateWithRetrieveModelMixin,
    AUpdateWithRetrieveModelMixin,
    AUpdateOrCreateWithRetrieveModelMixin,
    ADeleteProtectedModelMixin,
    AListWithAdditionalDataMixin,
    ModelViewSet,
):
    async def aget_view_queryset(self) -> QuerySet[models.Model]:
        return await aget_view_queryset(self)

    async def aget_object(self) -> models.Model:
        queryset = await aget_view_queryset(self)
        queryset = self.filter_queryset(queryset)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg not in self.kwargs:
            raise AssertionError(
                f"Expected view {self.__class__.__name__} to be called with a URL "
                f'keyword argument named "{lookup_url_kwarg}".'
            )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = await aget_object_or_404(queryset, **filter_kwargs)
        await self.acheck_object_permissions(self.request, obj)
        return obj

    async def acheck_object_permissions(self, request: Request, obj: models.Model) -> None:
        await acheck_object_permissions(self, request, obj, self.get_permissions())

    async def apaginate_queryset(self, queryset: QuerySet[models.Model]) -> list[models.Model] | None:
        if self.paginator is None:
            return None
        if hasattr(self.paginator, "apaginate_queryset"):
            return await self.paginator.apaginate_queryset(queryset, self.request, view=self)
        return self.paginator.paginate_queryset(queryset, self.request, view=self)
