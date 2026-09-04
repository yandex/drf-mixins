import asyncio
import warnings
from types import SimpleNamespace

from django.test import TestCase
from rest_framework.response import Response

from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin


class UrlNameContractTests(UrlNameMixin, TestCase):
    URL_NAME = "ping"

    def test_get_url_reverses_configured_name(self):
        self.assertEqual(self.get_url(), "/ping/")


class GenericRequestContractTests(GenericRequestMixin, TestCase):
    def test_num_queries_is_not_checked_by_default(self):
        response = self.make_request("/ping/", expected={"ok": True})

        self.assertEqual(response.status_code, 200)

    def test_explicit_num_queries_is_checked_in_sync_context(self):
        response = self.make_request(
            "/ping/",
            expected={"ok": True},
            num_queries=0,
        )

        self.assertEqual(response.status_code, 200)

    def test_count_zero_is_checked(self):
        class Client:
            def get(self, *args, **kwargs):
                return Response({"count": 0, "next": None, "previous": None, "results": []})

        self.client = Client()

        response = self.list_request("/", expected=[], count=0)

        self.assertEqual(response.data["count"], 0)

    def test_count_is_not_checked_by_default(self):
        class Client:
            def get(self, *args, **kwargs):
                return Response({"count": 5, "next": None, "previous": None, "results": []})

        self.client = Client()

        response = self.list_request("/", expected=[])

        self.assertEqual(response.data["count"], 5)


class AsyncNumQueriesContractTests(GenericRequestMixin, TestCase):
    async def test_explicit_num_queries_is_ignored_with_runtime_warning(self):
        class Client:
            def get(self, *args, **kwargs):
                return SimpleNamespace(
                    status_code=200,
                    data={"ok": True},
                    content=b"",
                )

        self.client = Client()

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            response = self.make_request("/", expected={"ok": True}, num_queries=1)
            await asyncio.sleep(0)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item.category is RuntimeWarning for item in captured), captured)
