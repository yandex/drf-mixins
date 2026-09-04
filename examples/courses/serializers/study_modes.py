from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from ..models import StudyMode


class StudyModeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyMode
        fields = (
            "id",
            "slug",
            "name",
        )
        read_only_fields = fields


@extend_schema_serializer(component_name="StudyMode")
class StudyModeListExternalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyMode
        fields = (
            "id",
            "slug",
            "name",
        )
        read_only_fields = fields
