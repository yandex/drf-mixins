from typing import TYPE_CHECKING, Any

from .mixins import (
    ActionSerializerMixin,
    CreateWithRetrieveModelMixin,
    DeleteProtectedModelMixin,
    ListWithAdditionalDataMixin,
    SerializeGetParamsViewMixin,
    SerializePostParamsViewMixin,
    UpdateOrCreateWithRetrieveModelMixin,
    UpdateWithRetrieveModelMixin,
)
from .pagination import LimitOffsetAllPagination

if TYPE_CHECKING:
    from .viewsets import BaseModelViewSet

__all__ = [
    "ActionSerializerMixin",
    "BaseModelViewSet",
    "CreateWithRetrieveModelMixin",
    "DeleteProtectedModelMixin",
    "LimitOffsetAllPagination",
    "ListWithAdditionalDataMixin",
    "SerializeGetParamsViewMixin",
    "SerializePostParamsViewMixin",
    "UpdateOrCreateWithRetrieveModelMixin",
    "UpdateWithRetrieveModelMixin",
]


def __getattr__(name: str) -> Any:
    if name == "BaseModelViewSet":
        from .viewsets import BaseModelViewSet  # pylint: disable=import-outside-toplevel

        return BaseModelViewSet
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
