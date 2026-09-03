from django.core.exceptions import ImproperlyConfigured
from django.db.models import ProtectedError, QuerySet
from django.test import TestCase
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from tests.testapp.models import Item, ProtectedChild
from yandex_drf_mixins.drf import (
    ActionSerializerMixin,
    BaseModelViewSet,
    DeleteProtectedModelMixin,
    LimitOffsetAllPagination,
    ListWithAdditionalDataMixin,
    SerializeGetParamsViewMixin,
    SerializePostParamsViewMixin,
)


class ItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ("id", "name")


class ItemRetrieveSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="name")

    class Meta:
        model = Item
        fields = ("id", "label")


class ItemViewSet(BaseModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemWriteSerializer
    serializer_classes = {"retrieve": ItemRetrieveSerializer}


class ActionSerializerContractTests(TestCase):
    def test_action_specific_serializer_wins_over_default(self):
        class View(ActionSerializerMixin):
            action = "retrieve"
            serializer_class = ItemWriteSerializer
            serializer_classes = {"retrieve": ItemRetrieveSerializer}

        self.assertIs(View().get_serializer_class(), ItemRetrieveSerializer)

    def test_default_serializer_is_used_for_unknown_action(self):
        class View(ActionSerializerMixin):
            action = "list"
            serializer_class = ItemWriteSerializer
            serializer_classes = None

        self.assertIs(View().get_serializer_class(), ItemWriteSerializer)


class RetrieveMutationContractTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_create_returns_retrieve_representation(self):
        request = self.factory.post("/items/", {"name": "created"}, format="json")
        response = ItemViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {"id": Item.objects.get().pk, "label": "created"})

    def test_update_returns_retrieve_representation(self):
        item = Item.objects.create(name="before")
        request = self.factory.put(f"/items/{item.pk}/", {"name": "after"}, format="json")
        response = ItemViewSet.as_view({"put": "update"})(request, pk=item.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"id": item.pk, "label": "after"})


class DeleteProtectedContractTests(TestCase):
    def test_protected_error_is_a_scalar_error_detail_and_uses_customizable_template(self):
        item = Item.objects.create(name="parent")
        ProtectedChild.objects.create(item=item)

        class View(DeleteProtectedModelMixin):
            protected_error_message = "cannot delete: %(object_name)s"

            def perform_destroy(self, instance):
                return super().perform_destroy(instance)

        class DeleteView(View, BaseModelViewSet):
            queryset = Item.objects.all()
            serializer_class = ItemWriteSerializer

        with self.assertRaises(ValidationError) as raised:
            DeleteView().perform_destroy(item)

        self.assertIsInstance(raised.exception.detail, ErrorDetail)
        self.assertEqual(raised.exception.detail.code, "protected")
        self.assertIn("cannot delete:", str(raised.exception.detail))

    def test_protected_objects_limit_and_default_name_are_configurable(self):
        protected = [
            type("Protected", (), {"_meta": type("Meta", (), {"verbose_name": name})()})()
            for name in ("first", "second")
        ]

        class Parent:
            def perform_destroy(self, instance):
                raise ProtectedError("protected", protected)

        class View(DeleteProtectedModelMixin, Parent):
            protected_objects_limit = None
            protected_object_default_name = "related records"

        view = View()

        with self.assertRaises(ValidationError) as raised:
            view.perform_destroy(Item())

        self.assertIn("first, second", str(raised.exception.detail))


class ParamsSerializer(serializers.Serializer):
    value = serializers.IntegerField()


class ParamsContractTests(TestCase):
    def test_get_params_are_validated_and_cached(self):
        request = Request(APIRequestFactory().get("/?value=42"))

        class View(SerializeGetParamsViewMixin):
            params_serializer_class = ParamsSerializer

        view = View()
        view.request = request

        self.assertEqual(view.validated_params, {"value": 42})
        self.assertIs(view.validated_params, view.validated_params)

    def test_post_params_are_validated(self):
        request = Request(
            APIRequestFactory().post("/", {"value": 7}, format="json"),
            parsers=[JSONParser()],
        )

        class View(SerializePostParamsViewMixin):
            params_serializer_class = ParamsSerializer

        view = View()
        view.request = request

        self.assertEqual(view.validated_params, {"value": 7})

    def test_missing_serializer_class_is_reported(self):
        view = SerializeGetParamsViewMixin()
        view.request = Request(APIRequestFactory().get("/"))

        with self.assertRaises(ImproperlyConfigured):
            _ = view.validated_params


class PaginationContractTests(TestCase):
    def test_all_returns_a_lazy_queryset_slice(self):
        Item.objects.bulk_create([Item(name="one"), Item(name="two")])
        request = Request(APIRequestFactory().get("/?all=true"))

        result = LimitOffsetAllPagination().paginate_queryset(Item.objects.order_by("id"), request)

        self.assertIsInstance(result, QuerySet)
        self.assertEqual(list(result.values_list("name", flat=True)), ["one", "two"])


class ListWithAdditionalDataContractTests(TestCase):
    def test_list_response_combines_additional_data_and_serialized_objects(self):
        Item.objects.create(name="one")

        class ResultSerializer(serializers.Serializer):
            total = serializers.IntegerField()
            objects = ItemRetrieveSerializer(many=True)

        class View(ListWithAdditionalDataMixin):
            serializer_class = ResultSerializer

            def get_queryset(self):
                return Item.objects.order_by("id")

            def filter_queryset(self, queryset):
                return queryset

            def get_serializer(self, *args, **kwargs):
                return self.serializer_class(*args, **kwargs)

        response = View().list_with_additional_data(
            request=None,
            additional_data={"total": 1},
        )

        self.assertEqual(response.data, {"total": 1, "objects": [{"id": 1, "label": "one"}]})
