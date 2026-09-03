# mypy: disable-error-code="no-untyped-def"

from typing import Any

from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.response import Response

from yandex_drf_mixins.base.testing import UnorderedList, num_queries_context


class UrlNameMixin:
    URL_NAME = ""

    def get_url(self, *args, **kwargs) -> str:
        return reverse(self.URL_NAME, args=args, kwargs=kwargs)

    def assertURLNameEqual(  # noqa: N802
        self, url: str, base_url: str | None = None, args: list[Any] | None = None, kwargs: dict[str, Any] | None = None
    ) -> None:
        if base_url:
            url = f"/{base_url}{url}"
        args = args or []
        kwargs = kwargs or {}
        self.assertURLEqual(self.get_url(*args, **kwargs), url.format(*args, **kwargs))


class GenericRequestMixin:
    def list_request(
        self,
        url: str,
        expected: Any,
        num_queries: int | None = None,
        pagination: bool = True,
        count: int | None = None,
        check_ids: bool = True,
        only_ids: bool = False,
        check_errors: bool = False,
        check_order: bool = True,
        status_code: int | None = None,
    ) -> Response:
        status_code = status.HTTP_200_OK if status_code is None else status_code
        with num_queries_context(self, num_queries):
            response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status_code)
        if check_errors:
            self.assert_errors(response.data, expected)
            return response
        if pagination:
            self.assertEqual(response.data.keys(), {"count", "next", "previous", "results"})
            if count is not None:
                self.assertEqual(response.data.get("count"), count)
            results = response.data.get("results")
        else:
            results = response.data
        if check_ids or only_ids:
            result_ids = [result["id"] for result in results]
            expected_ids = [item["id"] for item in expected]
            if not check_order:
                result_ids.sort()
                expected_ids.sort()
            self.assertListEqual(result_ids, expected_ids)
        if not only_ids:
            if not check_order:
                results = UnorderedList(results)
                expected = UnorderedList(expected)
            self.assertListEqual(results, expected)
        return response

    def detail_request(self, url: str, **kwargs) -> Response:
        return self.make_request(url=url, **kwargs)

    def make_request(
        self,
        url: str,
        *,
        method: str = "get",
        data: Any = "",
        expected: Any = None,
        num_queries: int | None = None,
        status_code: int | None = None,
        check_errors: bool = False,
    ) -> Response:
        status_code = status.HTTP_200_OK if status_code is None else status_code
        request_method = getattr(self.client, method)
        with num_queries_context(self, num_queries):
            response = request_method(url, data=data, format="json")
        self.assertEqual(response.status_code, status_code, response.content)
        if check_errors:
            try:
                self.assert_errors(response.data, expected)
            except Exception as exc:
                raise self.failureException(
                    f"Fail check request errors with exception: {exc!r}\n"
                    f"Got response data:\n{response.data}\nExpected:\n{expected}"
                ) from exc
            return response
        if expected is not None:
            results = response.data
            if callable(expected):
                expected = expected(response)
            if isinstance(expected, dict):
                self.assertDictEqual(results, expected)
            elif isinstance(expected, list):
                self.assertListEqual(results, expected)
            else:
                self.assertEqual(results, expected)
        return response

    def update_request(self, url: str, data: Any, **kwargs) -> Response:
        kwargs.setdefault("method", "put")
        return self.make_request(url, data=data, **kwargs)

    def partial_update_request(self, url: str, data: Any, **kwargs) -> Response:
        kwargs.setdefault("method", "patch")
        return self.make_request(url, data=data, **kwargs)

    def create_request(self, url: str, data: Any = "", **kwargs) -> Response:
        kwargs.setdefault("method", "post")
        kwargs.setdefault("status_code", status.HTTP_201_CREATED)
        return self.make_request(url, data=data, **kwargs)

    def delete_request(
        self,
        url: str,
        num_queries: int | None = None,
        status_code: int | None = None,
        method: str = "delete",
        expected: Any = None,
        check_errors: bool = False,
    ) -> Response:
        status_code = status.HTTP_204_NO_CONTENT if status_code is None else status_code
        request_method = getattr(self.client, method)
        with num_queries_context(self, num_queries):
            response = request_method(url)
        self.assertEqual(response.status_code, status_code, response.data)
        if check_errors:
            self.assert_errors(response.data, expected)
        return response

    def assert_errors(self, data: Any, expected_errors: Any) -> None:
        if isinstance(data, list):
            for index, error in enumerate(data):
                self.assert_errors(error, expected_errors[index])
        elif isinstance(data, dict):
            for field, errors in data.items():
                self.assert_errors(errors, expected_errors[field])
        elif isinstance(expected_errors, ErrorDetail):
            self.assertEqual(data, expected_errors)
        else:
            self.assertEqual(data.code, expected_errors)
