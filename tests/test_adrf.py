import asyncio

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db.models import ProtectedError
from django.test import SimpleTestCase
from django.utils.functional import Promise
from django.utils.translation import override
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

pytest.importorskip("adrf")

from yandex_drf_mixins.adrf import (  # noqa: E402
    ACreateWithRetrieveModelMixin,
    ADeleteProtectedModelMixin,
    ALimitOffsetAllPagination,
    AListModelMixin,
    ASerializeGetParamsViewMixin,
    AUpdateWithRetrieveModelMixin,
)
from yandex_drf_mixins.base.permissions import acheck_object_permissions  # noqa: E402


class AsyncSaveSerializer:
    def __init__(self):
        self.instance = None

    async def asave(self):
        self.instance = object()
        return self.instance


class AsyncHooksContractTests(SimpleTestCase):
    async def test_default_aperform_create_saves_serializer(self):
        serializer = AsyncSaveSerializer()

        await ACreateWithRetrieveModelMixin().aperform_create(serializer)

        self.assertIsNotNone(serializer.instance)

    async def test_create_contract_rejects_override_without_instance(self):
        class BrokenView(ACreateWithRetrieveModelMixin):
            async def aperform_create(self, serializer):
                return None

            def get_serializer(self, *args, **kwargs):
                class Serializer:
                    instance = None

                    def is_valid(self, *, raise_exception):
                        return True

                return Serializer()

        with self.assertRaises(ImproperlyConfigured):
            await BrokenView().acreate_with_retrieve(type("Request", (), {"data": {}})())

    async def test_default_aperform_update_saves_serializer(self):
        serializer = AsyncSaveSerializer()

        result = await AUpdateWithRetrieveModelMixin().aperform_update(serializer)

        self.assertIsNone(result)
        self.assertIsNotNone(serializer.instance)


class AsyncDeleteContractTests(SimpleTestCase):
    def test_default_protected_messages_are_lazy_translations(self):
        self.assertIsInstance(ADeleteProtectedModelMixin.protected_error_message, Promise)
        self.assertIsInstance(ADeleteProtectedModelMixin.protected_object_default_name, Promise)

    async def test_default_aperform_destroy_uses_native_adelete(self):
        class Instance:
            deleted = False

            async def adelete(self):
                self.deleted = True

        instance = Instance()

        await ADeleteProtectedModelMixin().aperform_destroy(instance)

        self.assertTrue(instance.deleted)

    async def test_protected_error_is_converted_to_scalar_validation_error(self):
        protected = type(
            "Protected",
            (),
            {"_meta": type("Meta", (), {"verbose_name": "child"})()},
        )()

        class Instance:
            async def adelete(self):
                raise ProtectedError("protected", {protected})

        with self.assertRaises(ValidationError) as raised:
            await ADeleteProtectedModelMixin().aperform_destroy(Instance())

        self.assertIsInstance(raised.exception.detail, ErrorDetail)
        self.assertEqual(raised.exception.detail.code, "protected")

    async def test_protected_objects_limit_is_configurable(self):
        def protected(name):
            return type(
                "Protected",
                (),
                {"_meta": type("Meta", (), {"verbose_name": name})()},
            )()

        class Instance:
            async def adelete(self):
                raise ProtectedError("protected", [protected("first"), protected("second")])

        class View(ADeleteProtectedModelMixin):
            protected_objects_limit = None

        with self.assertRaises(ValidationError) as raised:
            await View().aperform_destroy(Instance())

        self.assertIn("first, second", str(raised.exception.detail))

    async def test_empty_protected_objects_uses_customizable_default_name(self):
        class Instance:
            async def adelete(self):
                raise ProtectedError("protected", set())

        class View(ADeleteProtectedModelMixin):
            protected_object_default_name = "related records"

        with self.assertRaises(ValidationError) as raised:
            await View().aperform_destroy(Instance())

        self.assertIn("related records", str(raised.exception.detail))

    async def test_protected_error_uses_russian_package_translation(self):
        class Instance:
            async def adelete(self):
                raise ProtectedError("protected", set())

        with override("ru"):
            with self.assertRaises(ValidationError) as raised:
                await ADeleteProtectedModelMixin().aperform_destroy(Instance())

            self.assertEqual(
                str(raised.exception.detail),
                "нельзя удалить, потому что есть связанные данные",
            )


class ParamsSerializer(serializers.Serializer):
    value = serializers.IntegerField()


class AsyncParamsContractTests(SimpleTestCase):
    async def test_avalidated_params_returns_validated_data(self):
        class View(ASerializeGetParamsViewMixin):
            params_serializer_class = ParamsSerializer

        view = View()
        view.request = Request(APIRequestFactory().get("/?value=11"))

        self.assertEqual(await view.avalidated_params(), {"value": 11})


class AsyncQuerysetContractTests(SimpleTestCase):
    async def test_alist_supports_async_get_queryset_and_sync_filter(self):
        calls = []

        class Serializer:
            adata = asyncio.sleep(0, result=[{"id": 1}])

        class View(AListModelMixin):
            async def get_queryset(self):
                calls.append("get")
                return [1]

            async def aget_view_queryset(self):
                return await self.get_queryset()

            def filter_queryset(self, queryset):
                calls.append("filter")
                return queryset

            async def apaginate_queryset(self, queryset):
                return None

            def get_serializer(self, *args, **kwargs):
                return Serializer()

        response = await View().alist()

        self.assertEqual(response.data, [{"id": 1}])
        self.assertEqual(calls, ["get", "filter"])

    async def test_aget_view_queryset_is_a_required_mixin_method(self):
        with self.assertRaises(NotImplementedError):
            await AListModelMixin().aget_view_queryset()

        class View(AListModelMixin):
            async def aget_view_queryset(self):
                return [1]

        self.assertEqual(await View().aget_view_queryset(), [1])


class AsyncPermissionsContractTests(SimpleTestCase):
    async def test_preserves_permission_order_and_stops_after_first_denial(self):
        calls = []

        class AllowedSyncPermission:
            def has_object_permission(self, request, view, obj):
                calls.append("allowed-sync")
                return True

        class DeniedPermission:
            message = "denied"
            code = "denied"

            async def has_object_permission(self, request, view, obj):
                calls.append("denied-async")
                return False

        class UnreachedSyncPermission:
            def has_object_permission(self, request, view, obj):
                calls.append("unreached-sync")
                return True

        class View:
            def permission_denied(self, request, message, code):
                raise PermissionError(message, code)

        with self.assertRaises(PermissionError):
            await acheck_object_permissions(
                View(),
                object(),
                object(),
                [AllowedSyncPermission(), DeniedPermission(), UnreachedSyncPermission()],
            )

        self.assertEqual(calls, ["allowed-sync", "denied-async"])


class AsyncPaginationContractTests(SimpleTestCase):
    async def test_all_returns_a_lazy_slice_after_async_count(self):
        class AsyncQueryset:
            def __init__(self, values):
                self.values = values

            async def acount(self):
                return len(self.values)

            def __getitem__(self, item):
                return self.values[item]

        request = Request(APIRequestFactory().get("/?all=true"))

        result = await ALimitOffsetAllPagination().apaginate_queryset(AsyncQueryset([1, 2]), request)

        self.assertEqual(result, [1, 2])
