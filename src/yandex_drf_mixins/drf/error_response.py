from yandex_drf_mixins.base.error_response import (
    ValidateDjango4xxResponseBaseMixin,
    assert_django_4xx_response,
    validate_django_4xx_response_decorator,
)

__all__ = [
    "ValidateDjango4xxResponseMixin",
    "assert_django_4xx_response",
    "validate_django_4xx_response_decorator",
]


class ValidateDjango4xxResponseMixin(ValidateDjango4xxResponseBaseMixin):
    """Validate DRF 4xx responses strictly or log invalid bodies in soft mode."""
