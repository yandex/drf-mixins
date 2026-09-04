from urllib.parse import urljoin

from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Course


# IndexAPI Serializers
# ===============
class IndexLanguageSerializer(serializers.Serializer):
    ru = serializers.CharField(required=False)
    en = serializers.CharField(required=False)
    language = serializers.ChoiceField(
        choices=[("ru", "ru"), ("en", "en"), ("both", "both")], default="both"
    )


class CourseIndexSerializer(serializers.ModelSerializer):
    updated = serializers.DateTimeField(source="modified")
    name = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    api_url = serializers.SerializerMethodField()

    @extend_schema_field(IndexLanguageSerializer)
    def get_name(self, obj: Course) -> dict:
        return {
            "ru": obj.name,
            "language": "ru",
        }

    @extend_schema_field(IndexLanguageSerializer)
    def get_content(self, obj: Course):
        return {
            "ru": obj.description,
            "language": "ru",
        }

    @extend_schema_field(OpenApiTypes.URI)
    def get_url(self, obj: Course):
        return obj.frontend_url

    @extend_schema_field(OpenApiTypes.URI)
    def get_api_url(self, obj: Course):
        request = self.context["request"]

        current_uri = f"{request.scheme}://{request.get_host()}"
        path = reverse("index_api:course-index-detail", args=(obj.pk,))

        return urljoin(current_uri, path)

    class Meta:
        model = Course
        fields = (
            "id",
            "created",
            "updated",
            "name",
            "content",
            "url",
            "api_url",
        )
        read_only_fields = fields
