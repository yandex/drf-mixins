import subprocess
import sys

import pytest


def test_drf_namespace_exports_the_supported_contract():
    from yandex_drf_mixins import drf

    expected = {
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
    }

    assert expected <= set(drf.__all__)


def test_adrf_namespace_exports_the_supported_contract():
    pytest.importorskip("adrf")
    from yandex_drf_mixins import adrf

    expected = {
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
    }

    assert expected <= set(adrf.__all__)


def test_testing_namespace_exports_only_public_test_mixins():
    from yandex_drf_mixins import testing

    assert set(testing.__all__) == {"GenericRequestMixin", "UrlNameMixin"}


def test_adrf_pagination_can_be_loaded_while_drf_viewsets_are_initializing():
    pytest.importorskip("adrf")

    code = """
from django.conf import settings
settings.configure(
    REST_FRAMEWORK={
        'DEFAULT_PAGINATION_CLASS': (
            'tests.pagination_import_fixture.ALimitOffsetPagination'
        ),
    },
)
import rest_framework.viewsets
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
