# mypy: disable-error-code="no-untyped-def"

from typing import Mapping, Type

from rest_framework.serializers import BaseSerializer


class ActionSerializerBaseMixin:
    serializer_class: Type[BaseSerializer]
    serializer_classes: Mapping[str, Type[BaseSerializer]] | None = None
    action: str

    def get_serializer_class(self) -> Type[BaseSerializer]:
        serializer_classes = self.serializer_classes or {}
        return serializer_classes.get(self.action, self.serializer_class)

    def get_retrieve_serializer(self, *args, **kwargs) -> BaseSerializer:
        serializer_classes = self.serializer_classes or {}
        serializer_class = serializer_classes.get("retrieve", self.serializer_class)
        kwargs["context"] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)
