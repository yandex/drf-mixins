from typing import TYPE_CHECKING, Any

from .mixins import (
    ACreateWithRetrieveModelMixin,
    ActionSerializerMixin,
    ADeleteProtectedModelMixin,
    AListModelMixin,
    AListWithAdditionalDataMixin,
    ASerializeGetParamsViewMixin,
    ASerializePostParamsViewMixin,
    AUpdateOrCreateWithRetrieveModelMixin,
    AUpdateWithRetrieveModelMixin,
)
from .pagination import ALimitOffsetAllPagination, ALimitOffsetPagination

if TYPE_CHECKING:
    from .viewsets import ABaseModelViewSet

__all__ = [
    "ABaseModelViewSet",
    "ACreateWithRetrieveModelMixin",
    "ADeleteProtectedModelMixin",
    "AListModelMixin",
    "AListWithAdditionalDataMixin",
    "ALimitOffsetAllPagination",
    "ALimitOffsetPagination",
    "ASerializeGetParamsViewMixin",
    "ASerializePostParamsViewMixin",
    "AUpdateOrCreateWithRetrieveModelMixin",
    "AUpdateWithRetrieveModelMixin",
    "ActionSerializerMixin",
]


def __getattr__(name: str) -> Any:
    if name == "ABaseModelViewSet":
        from .viewsets import ABaseModelViewSet  # pylint: disable=import-outside-toplevel

        return ABaseModelViewSet
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
