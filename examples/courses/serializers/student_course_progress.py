from typing import Optional

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from ..models import CourseStudent, StudentModuleProgress

User = get_user_model()


class UserInlineLabSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    class Meta:
        model = User
        fields = ("username", "full_name")


class GradeStudentLabSerializer(serializers.ModelSerializer):
    user = UserInlineLabSerializer()
    finished_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CourseStudent
        fields = (
            "id",
            "status",
            "substatus",
            "is_finished",
            "finished_date",
            "is_required",
            "required_since",
            "created",
            "user",
            "group_id",
        )
        read_only_fields = fields


class CourseStudentProgressModulesField(serializers.DictField):
    def to_representation(self, course_student: CourseStudent):
        return {
            str(progress.module_id): progress.score
            for progress in course_student.module_progresses.all()
        }


class CourseStudentProgressAttendanceModulesField(serializers.DictField):
    def to_representation(self, course_student: CourseStudent):
        return {
            str(progress.module_id): bool(progress.is_set_attendance)
            for progress in course_student.module_progresses.all()
        }


class CourseStudentProgressScoreField(serializers.IntegerField):
    def to_representation(self, course_student: CourseStudent) -> int:
        progress = next(iter(course_student.course_progresses.all()), None)
        if not progress:
            return 0
        return progress.score


class CourseStudentProgressLanguageField(serializers.CharField):
    def to_representation(self, course_student: CourseStudent) -> str:
        if course_student.language:
            return course_student.language.language

        return None


class StudentCourseProgressListSerializer(serializers.ModelSerializer):
    student = GradeStudentLabSerializer(source="*")
    modules = CourseStudentProgressModulesField(
        source="*", child=serializers.IntegerField()
    )
    is_set_attendance = CourseStudentProgressAttendanceModulesField(
        source="*", child=serializers.BooleanField()
    )
    score = CourseStudentProgressScoreField(source="*")
    language = CourseStudentProgressLanguageField(source="*")

    class Meta:
        model = CourseStudent
        fields = ("student", "modules", "is_set_attendance", "score", "language")
        read_only_fields = fields


class StudentCourseProgressChangeListSerializer(StudentCourseProgressListSerializer):
    changed = serializers.SerializerMethodField()

    class Meta(StudentCourseProgressListSerializer.Meta):
        fields = StudentCourseProgressListSerializer.Meta.fields + ("changed",)

    def get_changed(self, obj: CourseStudent) -> dict:
        return self.context["attendances"][obj.id]


@extend_schema_serializer(component_name="StudentCourseModuleProgress")
class StudentModuleProgressExternalSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="module_id")  # noqa: A003
    score_updated_at = serializers.DateTimeField(
        source="modified", label=_("score update date")
    )
    module_passed_at = serializers.DateTimeField(
        source="passing_date", label=_("module completion date")
    )

    class Meta:
        model = StudentModuleProgress
        fields = ("id", "score", "score_updated_at", "module_passed_at")
        read_only_fields = fields


class CourseStudentProgressScoreExternalField(serializers.IntegerField):
    def to_representation(self, course_student: CourseStudent) -> Optional[int]:
        # At most one student progress record is stored per course, but it may be
        # retrieved through `.prefetch_related`.
        progress = next(iter(course_student.course_progresses.all()), None)
        if not progress:
            return None
        return progress.score


@extend_schema_serializer(component_name="StudentCourseProgress")
class StudentCourseProgressListExternalSerializer(serializers.ModelSerializer):
    started_at = serializers.DateTimeField(
        source="created", label=_("course enrollment date")
    )
    is_finished = serializers.BooleanField(
        source="is_passed", label=_("passing score achieved")
    )
    finished_at = serializers.DateTimeField(
        source="passing_date", label=_("course completion date")
    )
    yandex_login = serializers.CharField(source="user.username")
    modules = StudentModuleProgressExternalSerializer(
        source="module_progresses", many=True
    )
    score = CourseStudentProgressScoreExternalField(source="*", label=_("scores"))
    language = CourseStudentProgressLanguageField(source="*", label=_("study language"))

    class Meta:
        model = CourseStudent
        fields = (
            "id",
            "started_at",
            "yandex_login",
            "status",
            "is_finished",
            "finished_at",
            "is_required",
            "required_since",
            "score",
            "modules",
            "language",
        )
        read_only_fields = fields
