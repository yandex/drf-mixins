from django.db.models import ProtectedError
from django.test import SimpleTestCase
from django.utils.translation import override
from rest_framework.exceptions import ValidationError

from yandex_drf_mixins.drf import DeleteProtectedModelMixin, LimitOffsetAllPagination


class TranslationContractTests(SimpleTestCase):
    def test_english_messages_are_used_by_default(self):
        with override("en"):
            self.assertEqual(
                str(DeleteProtectedModelMixin.protected_error_message),
                "cannot be deleted because related %(object_name)s exist",
            )
            self.assertEqual(
                str(DeleteProtectedModelMixin.protected_object_default_name),
                "related data",
            )
            self.assertEqual(
                self._all_query_description(),
                "Retrieve all results at once",
            )

    def test_russian_messages_are_loaded_from_package_catalog(self):
        with override("ru"):
            self.assertEqual(
                self._protected_error_message(),
                "нельзя удалить, потому что есть связанные данные",
            )
            self.assertEqual(
                self._all_query_description(),
                "Получить все результаты сразу",
            )

    @staticmethod
    def _protected_error_message() -> str:
        class Parent:
            def perform_destroy(self, instance):
                raise ProtectedError("protected", set())

        class View(DeleteProtectedModelMixin, Parent):
            pass

        try:
            View().perform_destroy(object())
        except ValidationError as exc:
            return str(exc.detail)
        raise AssertionError("ValidationError was not raised")

    @staticmethod
    def _all_query_description() -> str:
        parameters = LimitOffsetAllPagination().get_schema_operation_parameters(view=None)
        return parameters[-1]["description"]
