from rest_framework.viewsets import ModelViewSet

from .mixins import (
    ActionSerializerMixin,
    CreateWithRetrieveModelMixin,
    DeleteProtectedModelMixin,
    ListWithAdditionalDataMixin,
    UpdateOrCreateWithRetrieveModelMixin,
    UpdateWithRetrieveModelMixin,
)


class BaseModelViewSet(
    ActionSerializerMixin,
    CreateWithRetrieveModelMixin,
    UpdateWithRetrieveModelMixin,
    UpdateOrCreateWithRetrieveModelMixin,
    DeleteProtectedModelMixin,
    ListWithAdditionalDataMixin,
    ModelViewSet,
):
    pass
