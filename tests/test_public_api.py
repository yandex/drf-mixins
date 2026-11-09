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
        "SerializeParamsBaseViewMixin",
        "SerializePostParamsViewMixin",
        "UpdateOrCreateWithRetrieveModelMixin",
        "UpdateWithRetrieveModelMixin",
        "ValidateDjango4xxResponseMixin",
        "assert_django_4xx_response",
        "validate_django_4xx_response_decorator",
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
        "ASerializeParamsBaseViewMixin",
        "ASerializePostParamsViewMixin",
        "AUpdateOrCreateWithRetrieveModelMixin",
        "AUpdateWithRetrieveModelMixin",
        "AValidateDjango4xxResponseMixin",
        "ActionSerializerMixin",
        "assert_django_4xx_response",
        "avalidate_django_4xx_response_decorator",
    }

    assert expected <= set(adrf.__all__)


def test_drf_and_adrf_share_the_response_assertion_implementation():
    pytest.importorskip("adrf")
    from yandex_drf_mixins import adrf, drf

    assert adrf.assert_django_4xx_response is drf.assert_django_4xx_response


def test_schema_namespace_exports_the_error_response_contract():
    from yandex_drf_mixins import drf, schema

    expected = {
        "DJANGO_4XX_ERROR_COMPONENT_NAME",
        "DJANGO_4XX_ERROR_JSON_SCHEMA",
        "DJANGO_4XX_ERROR_OPENAPI_EXAMPLES",
        "DJANGO_4XX_ERROR_OPENAPI_REF",
        "DJANGO_4XX_ERROR_OPENAPI_RESPONSE_REF",
        "DJANGO_4XX_ERROR_OPENAPI_SCHEMAS",
        "DJANGO_4XX_ERROR_RESPONSE_COMPONENT_NAME",
        "DJANGO_ERROR_ITEM_COMPONENT_NAME",
    }

    assert set(schema.__all__) == expected
    assert expected.isdisjoint(drf.__all__)


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
