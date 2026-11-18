import copy
import pickle

from django.test import SimpleTestCase
from rest_framework.exceptions import ErrorDetail

from yandex_drf_mixins.base.exceptions import ProtectedValidationError, RestrictedValidationError


class ProtectedValidationErrorContractTests(SimpleTestCase):
    message = "cannot delete protected object"
    code = "custom_protected"

    def assert_error_is_preserved(self, error: ProtectedValidationError) -> None:
        self.assertEqual(error.args, (self.message, self.code))
        self.assertIsInstance(error.detail, ErrorDetail)
        self.assertEqual(str(error.detail), self.message)
        self.assertEqual(error.detail.code, self.code)

    def test_shallow_copy_preserves_constructor_arguments_and_detail(self):
        error = ProtectedValidationError(detail=self.message, code=self.code)

        cloned_error = copy.copy(error)

        self.assertIsNot(cloned_error, error)
        self.assert_error_is_preserved(cloned_error)

    def test_pickle_round_trip_preserves_constructor_arguments_and_detail(self):
        error = ProtectedValidationError(detail=self.message, code=self.code)

        restored_error = pickle.loads(pickle.dumps(error))

        self.assertIsNot(restored_error, error)
        self.assert_error_is_preserved(restored_error)


class RestrictedValidationErrorContractTests(SimpleTestCase):
    def test_restricted_error_is_distinct_and_preserves_scalar_detail(self):
        error = RestrictedValidationError("cannot delete restricted object")

        self.assertNotIsInstance(error, ProtectedValidationError)
        self.assertEqual(error.status_code, 400)
        self.assertIsInstance(error.detail, ErrorDetail)
        self.assertEqual(error.detail.code, "restricted")
        self.assertEqual(copy.copy(error).detail.code, "restricted")
        self.assertEqual(pickle.loads(pickle.dumps(error)).detail.code, "restricted")
