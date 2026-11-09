import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.utils.functional import Promise
from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

from yandex_drf_mixins.schema import DJANGO_4XX_ERROR_JSON_SCHEMA

logger = logging.getLogger(__name__)

_django_4xx_error_validator = Draft7Validator(DJANGO_4XX_ERROR_JSON_SCHEMA)


def _normalize_lazy_strings(value: Any) -> Any:
    if isinstance(value, Promise):
        return str(value)
    if isinstance(value, list):
        return [_normalize_lazy_strings(item) for item in value]
    if isinstance(value, dict):
        return {_normalize_lazy_strings(key): _normalize_lazy_strings(item) for key, item in value.items()}
    return value


def _format_json_path(path: Any) -> str:
    result = "$"
    for item in path:
        result += f"[{item}]" if isinstance(item, int) else f".{item}"
    return result


def assert_django_4xx_response(response: Any) -> Any:
    """Assert that a Django/DRF 4xx response contains a conventional error tree."""
    if 400 <= response.status_code < 500 and hasattr(response, "data"):
        data = _normalize_lazy_strings(response.data)
        try:
            _django_4xx_error_validator.validate(data)
        except ValidationError as error:
            raise AssertionError(
                "Django/DRF 4xx response does not match the error JSON Schema.\n"
                f"HTTP status: {response.status_code}\n"
                f"Error path: {_format_json_path(error.absolute_path)}\n"
                f"Reason: {error.message}\n"
                f"Response body: {data!r}"
            ) from error

    return response


def validate_django_4xx_response_decorator(request_method: Callable[..., Any]) -> Callable[..., Any]:
    """Validate a response returned by a synchronous request method."""

    @wraps(request_method)
    def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Any:
        response = request_method(instance, *args, **kwargs)
        return instance.validate_django_4xx_response(response)

    return wrapper


class ValidateDjango4xxResponseBaseMixin:
    """Shared response validation for synchronous and asynchronous views."""

    raise_django_4xx_response_validation_error = True

    def validate_django_4xx_response(self, response: Any) -> Any:
        try:
            return assert_django_4xx_response(response)
        except AssertionError as error:
            if self.raise_django_4xx_response_validation_error:
                raise

            logger.error("%s", error, exc_info=True)
            return response

    @validate_django_4xx_response_decorator
    def finalize_response(self, request: Any, response: Any, *args: Any, **kwargs: Any) -> Any:
        return super().finalize_response(request, response, *args, **kwargs)
