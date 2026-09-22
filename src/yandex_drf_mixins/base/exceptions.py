from rest_framework.exceptions import ErrorDetail, ValidationError


class ProtectedValidationError(ValidationError):
    """Validation error whose detail is a scalar instead of a one-item list."""

    def __init__(self, detail: str, code: str = "protected") -> None:
        super().__init__(detail, code)
        # DRF's ValidationError does not call Exception.__init__, so keyword
        # construction would otherwise leave args empty and break copy/pickle.
        self.args = (detail, code)
        self.detail = ErrorDetail(detail, code=code)
