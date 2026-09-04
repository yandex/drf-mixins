# mypy: disable-error-code="no-untyped-def"

from typing import Protocol, cast

from adrf.mixins import get_data
from asgiref.sync import sync_to_async
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models import ProtectedError, QuerySet
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from yandex_drf_mixins.base.exceptions import ProtectedValidationError
from yandex_drf_mixins.base.params import AValidatedParamsMixin, GetParamsMixin, PostParamsMixin
from yandex_drf_mixins.base.protected import get_protected_object_name
from yandex_drf_mixins.base.serializers import ActionSerializerBaseMixin


class _AsyncSerializer(Protocol):
    instance: models.Model | None

    async def asave(self) -> models.Model: ...


class _PrefetchedModel(Protocol):
    _prefetched_objects_cache: dict[object, object]


class ActionSerializerMixin(ActionSerializerBaseMixin):
    pass


class ACreateWithRetrieveModelMixin:
    async def acreate_with_retrieve(
        self, request: Request, response_status: int = status.HTTP_201_CREATED, *args, **kwargs
    ) -> Response:
        serializer = self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        await self.aperform_create(serializer)
        if serializer.instance is None:
            raise ImproperlyConfigured(
                "`aperform_create()` must call `serializer.asave()` or set `serializer.instance`."
            )
        response_serializer = self.get_retrieve_serializer(serializer.instance)
        data = await get_data(response_serializer)
        headers = self.get_success_headers(data)
        return Response(data, status=response_status, headers=headers)

    async def acreate(
        self, request: Request, response_status: int = status.HTTP_201_CREATED, *args, **kwargs
    ) -> Response:
        try:
            return await self.acreate_with_retrieve(request, response_status, *args, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc

    async def aperform_create(self, serializer: _AsyncSerializer) -> None:
        await serializer.asave()


class AUpdateWithRetrieveModelMixin:
    async def aupdate_with_retrieve(
        self, request: Request, instance: models.Model | None = None, *args, **kwargs
    ) -> Response:
        partial = kwargs.pop("partial", False)
        instance = instance or await self.aget_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        await self.aperform_update(serializer)
        if getattr(instance, "_prefetched_objects_cache", None):
            cast(_PrefetchedModel, instance)._prefetched_objects_cache = {}
        response_serializer = self.get_retrieve_serializer(serializer.instance)
        data = await get_data(response_serializer)
        return Response(data)

    async def apartial_update_with_retrieve(self, request: Request, *args, **kwargs) -> Response:
        kwargs["partial"] = True
        return await self.aupdate_with_retrieve(request, *args, **kwargs)

    async def aupdate(self, request: Request, *args, **kwargs) -> Response:
        try:
            return await self.aupdate_with_retrieve(request, *args, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc

    async def apartial_update(self, request: Request, *args, **kwargs) -> Response:
        try:
            return await self.apartial_update_with_retrieve(request, *args, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc

    async def aperform_update(self, serializer: _AsyncSerializer) -> None:
        await serializer.asave()


class AUpdateOrCreateWithRetrieveModelMixin:
    async def aupdate_or_create(self, request: Request, *args, **kwargs) -> Response:
        try:
            instance = await self.aget_object()
            self.action = "update"
            return await self.aupdate_with_retrieve(request, instance, *args, **kwargs)
        except Http404:
            self.action = "create"
            return await self.acreate_with_retrieve(request, *args, **kwargs)


class ADeleteProtectedModelMixin:
    protected_error_message = _("cannot be deleted because related %(object_name)s exist")
    protected_object_default_name = _("related data")
    protected_objects_limit: int | None = 1

    async def adestroy(self, request: Request, *args, **kwargs) -> Response:
        instance = await self.aget_object()
        await self.aperform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    async def aperform_destroy(self, instance: models.Model) -> None:
        try:
            await instance.adelete()
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc
        except ProtectedError as exc:
            object_name = get_protected_object_name(
                exc.protected_objects,
                limit=self.protected_objects_limit,
                default=self.protected_object_default_name,
            )
            message = self.protected_error_message % {"object_name": object_name}
            raise ProtectedValidationError(message) from exc


class ASerializeGetParamsViewMixin(GetParamsMixin, AValidatedParamsMixin):
    pass


class ASerializePostParamsViewMixin(PostParamsMixin, AValidatedParamsMixin):
    pass


class _AGetViewQuerysetMixin:
    async def aget_view_queryset(self) -> QuerySet[models.Model]:
        raise NotImplementedError


class AListModelMixin(_AGetViewQuerysetMixin):
    async def alist(self, *args, **kwargs) -> Response:
        queryset = await self.aget_view_queryset()
        queryset = self.filter_queryset(queryset)
        page = await self.apaginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = await get_data(serializer)
            return await self.get_apaginated_response(data)
        serializer = self.get_serializer(queryset, many=True)
        data = await get_data(serializer)
        return Response(data, status=status.HTTP_200_OK)


class AListWithAdditionalDataMixin(_AGetViewQuerysetMixin):
    async def alist_with_additional_data(
        self,
        request: Request,
        additional_data: dict[str, object],
        objects_field_name: str = "objects",
        *args,
        **kwargs,
    ) -> Response:
        queryset = await self.aget_view_queryset()
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer({**additional_data, objects_field_name: queryset})
        data = await get_data(serializer)
        return Response(data, status=status.HTTP_200_OK)
