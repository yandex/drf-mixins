from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
from rest_framework import status
from rest_framework.response import Response

from yandex_drf_mixins.drf import (
    ValidateDjango4xxResponseMixin,
    assert_django_4xx_response,
    validate_django_4xx_response_decorator,
)


class Django4xxResponseSchemaTests(SimpleTestCase):
    def test_accepts_django_error_trees(self):
        valid_responses = [
            {"detail": "Not found."},
            ["Invalid request."],
            {"field": ["This field is required.", "Invalid value."]},
            {"field": [{"nested_field": ["This field is required."]}]},
            {"detail": gettext_lazy("Try again.")},
        ]

        for data in valid_responses:
            with self.subTest(data=data):
                response = Response(data, status=status.HTTP_400_BAD_REQUEST)
                self.assertIs(assert_django_4xx_response(response), response)

    def test_rejects_non_error_response_bodies(self):
        invalid_responses = [
            None,
            "Invalid request.",
            {"field": None},
            {"field": [1]},
            [True],
        ]

        for data in invalid_responses:
            with self.subTest(data=data):
                response = Response(data, status=status.HTTP_400_BAD_REQUEST)
                with self.assertRaisesRegex(AssertionError, r"Error path: \$") as context:
                    assert_django_4xx_response(response)

                self.assertIsInstance(context.exception.__cause__, JSONSchemaValidationError)
                self.assertIn("HTTP status: 400", str(context.exception))
                self.assertIn(f"Response body: {data!r}", str(context.exception))

    def test_ignores_non_4xx_response(self):
        response = Response(None, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.assertIs(assert_django_4xx_response(response), response)

    def test_ignores_response_without_data(self):
        response = Mock(status_code=status.HTTP_404_NOT_FOUND, spec=["status_code"])

        self.assertIs(assert_django_4xx_response(response), response)


class ValidateDjango4xxResponseMixinTests(SimpleTestCase):
    def test_strict_validation_raises_by_default(self):
        response = Response(None, status=status.HTTP_400_BAD_REQUEST)

        with self.assertRaises(AssertionError):
            ValidateDjango4xxResponseMixin().validate_django_4xx_response(response)

    @patch("yandex_drf_mixins.base.error_response.logger")
    def test_soft_validation_logs_and_returns_response(self, logger):
        class SoftValidationMixin(ValidateDjango4xxResponseMixin):
            raise_django_4xx_response_validation_error = False

        response = Response(None, status=status.HTTP_400_BAD_REQUEST)

        result = SoftValidationMixin().validate_django_4xx_response(response)

        self.assertIs(result, response)
        logger.error.assert_called_once()
        self.assertEqual(logger.error.call_args.args[0], "%s")
        self.assertEqual(logger.error.call_args.kwargs, {"exc_info": True})

    def test_decorator_validates_returned_response(self):
        response = Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        class Client(ValidateDjango4xxResponseMixin):
            @validate_django_4xx_response_decorator
            def request(self):
                return response

        self.assertIs(Client().request(), response)
