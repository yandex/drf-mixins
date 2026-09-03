from rest_framework import serializers

from lms.preferences.serializers import (
    ColorThemeDetailLabSerializer,
    ColorThemeDetailSerializer,
)

from ..models import CourseCategory


class CourseCategoryListSerializer(serializers.ModelSerializer):
    depth = serializers.IntegerField(source="node_depth")
    color_theme = ColorThemeDetailLabSerializer()

    class Meta:
        model = CourseCategory
        fields = (
            "id",
            "parent_id",
            "slug",
            "name",
            "depth",
            "color_theme",
        )
        read_only_fields = fields


class CourseCategoryDetailSerializer(serializers.ModelSerializer):
    depth = serializers.IntegerField(source="node_depth")
    color_theme = ColorThemeDetailSerializer()

    class Meta:
        model = CourseCategory
        fields = (
            "id",
            "parent_id",
            "slug",
            "name",
            "depth",
            "color_theme",
        )
        read_only_fields = fields


# LabAPI serializers
# ==================
class CourseCategoryListLabSerializer(serializers.ModelSerializer):
    depth = serializers.IntegerField(source="node_depth")
    color_theme = ColorThemeDetailLabSerializer()

    class Meta:
        model = CourseCategory
        fields = (
            "id",
            "parent_id",
            "slug",
            "name",
            "depth",
            "color_theme",
            "created",
            "modified",
        )
        read_only_fields = fields


class CourseCategoryDetailLabSerializer(serializers.ModelSerializer):
    depth = serializers.IntegerField(source="node_depth")
    color_theme = ColorThemeDetailLabSerializer()

    class Meta:
        model = CourseCategory
        fields = (
            "id",
            "parent_id",
            "slug",
            "name",
            "depth",
            "color_theme",
            "created",
            "modified",
        )
        read_only_fields = fields
