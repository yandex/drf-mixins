from typing import Any, Type

from asgiref.sync import sync_to_async
from django.core.exceptions import ImproperlyConfigured
from rest_framework.serializers import BaseSerializer


class ParamsBaseMixin:
    params_serializer_class: Type[BaseSerializer] | None = None
    params_raise_exception = True
    params_serializer_many = False

    @property
    def params(self) -> Any:
        raise NotImplementedError

    def _get_params_serializer(self) -> BaseSerializer:
        if not hasattr(self, "_params_serializer"):
            serializer_class = self.params_serializer_class
            if serializer_class is None:
                raise ImproperlyConfigured("`params_serializer_class` has to be initialized.")
            self._params_serializer = serializer_class(  # pylint: disable=not-callable
                data=self.params,
                many=self.params_serializer_many,
            )
        return self._params_serializer


class ValidatedParamsMixin(ParamsBaseMixin):
    @property
    def validated_params(self) -> Any:
        if not hasattr(self, "_validated_params"):
            serializer = self._get_params_serializer()
            serializer.is_valid(raise_exception=self.params_raise_exception)
            self._validated_params = serializer.validated_data
        return self._validated_params


class AValidatedParamsMixin(ParamsBaseMixin):
    async def avalidated_params(self) -> Any:
        if not hasattr(self, "_validated_params"):
            serializer = self._get_params_serializer()
            await sync_to_async(serializer.is_valid)(raise_exception=self.params_raise_exception)
            self._validated_params = serializer.validated_data
        return self._validated_params


class GetParamsMixin(ParamsBaseMixin):
    @property
    def params(self) -> Any:
        if self.params_serializer_many:
            keys = self.request.query_params.keys()
            return [
                dict(zip(keys, values)) for values in zip(*(self.request.query_params.getlist(key) for key in keys))
            ]
        return self.request.query_params


class PostParamsMixin(ParamsBaseMixin):
    @property
    def params(self) -> Any:
        return self.request.data
