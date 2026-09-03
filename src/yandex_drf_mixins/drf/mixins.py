# mypy: disable-error-code="no-untyped-def"

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from yandex_drf_mixins.base.exceptions import ProtectedValidationError
from yandex_drf_mixins.base.params import GetParamsMixin, PostParamsMixin, ValidatedParamsMixin
from yandex_drf_mixins.base.protected import get_protected_object_name
from yandex_drf_mixins.base.serializers import ActionSerializerBaseMixin


class ActionSerializerMixin(ActionSerializerBaseMixin):
    pass


class CreateWithRetrieveModelMixin:
    def create_with_retrieve(
        self, request: Any, response_status: int = status.HTTP_201_CREATED, *args, **kwargs
    ) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_serializer = self.get_retrieve_serializer(serializer.instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=response_status, headers=headers)

    def create(self, request: Any, response_status: int = status.HTTP_201_CREATED, *args, **kwargs) -> Response:
        try:
            return self.create_with_retrieve(request, response_status, *args, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc


class UpdateWithRetrieveModelMixin:
    def update_with_retrieve(self, request: Any, instance: Any = None, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", False)
        instance = instance or self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        response_serializer = self.get_retrieve_serializer(serializer.instance)
        return Response(response_serializer.data)

    def partial_update_with_retrieve(self, request: Any, *args, **kwargs) -> Response:
        kwargs["partial"] = True
        return self.update_with_retrieve(request, *args, **kwargs)

    def update(self, request: Any, *args, **kwargs) -> Response:
        try:
            return self.update_with_retrieve(request, *args, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc

    def partial_update(self, request: Any, *args, **kwargs) -> Response:
        try:
            return self.partial_update_with_retrieve(request, *args, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc


class UpdateOrCreateWithRetrieveModelMixin:
    def update_or_create(self, request: Any, *args, **kwargs) -> Response:
        try:
            instance = self.get_object()
            self.action = "update"
            return self.update_with_retrieve(request, instance, *args, **kwargs)
        except Http404:
            self.action = "create"
            return self.create_with_retrieve(request, *args, **kwargs)


class DeleteProtectedModelMixin:
    protected_error_message = _("cannot be deleted because related %(object_name)s exist")
    protected_object_default_name = _("related data")
    protected_objects_limit: int | None = 1

    def perform_destroy(self, instance: models.Model) -> Any:
        try:
            return super().perform_destroy(instance)
        except DjangoValidationError as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc)) from exc
        except models.deletion.ProtectedError as exc:
            object_name = get_protected_object_name(
                exc.protected_objects,
                limit=self.protected_objects_limit,
                default=self.protected_object_default_name,
            )
            message = self.protected_error_message % {"object_name": object_name}
            raise ProtectedValidationError(message) from exc


class SerializeGetParamsViewMixin(GetParamsMixin, ValidatedParamsMixin):
    pass


class SerializePostParamsViewMixin(PostParamsMixin, ValidatedParamsMixin):
    pass


class ListWithAdditionalDataMixin:
    def list_with_additional_data(
        self,
        request: Any,
        additional_data: dict[str, Any],
        objects_field_name: str = "objects",
        *args,
        **kwargs,
    ) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer({**additional_data, objects_field_name: queryset})
        return Response(serializer.data, status=status.HTTP_200_OK)
