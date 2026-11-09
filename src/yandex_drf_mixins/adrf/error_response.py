from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from yandex_drf_mixins.base.error_response import ValidateDjango4xxResponseBaseMixin, assert_django_4xx_response

__all__ = [
    "AValidateDjango4xxResponseMixin",
    "assert_django_4xx_response",
    "avalidate_django_4xx_response_decorator",
]


def avalidate_django_4xx_response_decorator(
    request_method: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    """Validate a response returned by an asynchronous ADRF request method."""

    @wraps(request_method)
    async def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Any:
        response = await request_method(instance, *args, **kwargs)
        return instance.validate_django_4xx_response(response)

    return wrapper


class AValidateDjango4xxResponseMixin(ValidateDjango4xxResponseBaseMixin):
    """Validate ADRF 4xx responses strictly or log invalid bodies in soft mode."""
