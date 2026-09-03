from rest_framework import serializers

from .. import models


class CourseWriteSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Course
        fields = (
            "slug",
            "name",
            "shortname",
            "summary",
            "description",
            "target_audience_description",
            "estimated_time",
            "author",
        )


class CourseRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Course
        fields = (
            "id",
            "slug",
            "name",
            "shortname",
            "summary",
            "description",
            "target_audience_description",
            "estimated_time",
            "author_id",
        )
        read_only_fields = fields


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseCategory
        fields = ("id", "slug", "name", "description", "is_active")


class CourseBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseBlock
        fields = ("id", "course", "name", "summary", "is_active", "order")


class CourseModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseModule
        fields = (
            "id",
            "course",
            "block",
            "module_type",
            "name",
            "description",
            "estimated_time",
            "is_active",
            "weight",
            "order",
        )


class StudyModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StudyMode
        fields = ("id", "slug", "name", "description", "is_active", "order")


class CourseProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseProgram
        fields = ("course", "program")
