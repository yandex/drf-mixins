from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from courses.models import Course, CourseCategory, CourseStudent, StudyMode
from lms.enrollments.models import EnrolledUser
from lms.enrollments.serializers.enrolled_user import (
    CourseStudentProgressScoreField,
    EnrolledUserTrackerIssueInlineSerializer,
)


class CourseStudentTabLanguageField(serializers.CharField):
    """Return the student's study-language ISO code or None."""

    def to_representation(self, course_student: CourseStudent) -> str | None:
        if course_student.language_id and course_student.language:
            return course_student.language.language
        return None


class CourseCategoryInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = (
            "id",
            "slug",
            "name",
        )
        read_only_fields = fields


class StudyModeInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyMode
        fields = (
            "id",
            "slug",
            "name",
        )
        read_only_fields = fields


class CourseTabInlineSerializer(serializers.ModelSerializer):
    study_mode = StudyModeInlineSerializer(allow_null=True)
    categories = CourseCategoryInlineSerializer(many=True)
    type = serializers.ChoiceField(
        choices=Course.TypeChoices.choices, source="course_type"
    )  # noqa: A003
    bookmark = serializers.BooleanField()

    class Meta:
        model = Course
        fields = (
            "id",
            "is_active",
            "payment_method",
            "paid_percent",
            "price",
            "study_mode",
            "categories",
            "type",
            "name",
            "slug",
            "structure",
            "bookmark",
        )
        read_only_fields = fields


class EnrollTabLanguageField(serializers.CharField):
    """Return the application language ISO code or None."""

    def to_representation(self, enrolled_user: EnrolledUser) -> str | None:
        if enrolled_user.language_id and enrolled_user.language:
            return enrolled_user.language.language
        return None


class EnrollTabInlineSerializer(serializers.ModelSerializer):
    application_status = serializers.ChoiceField(
        choices=EnrolledUser.ApplicationStatusChoices.choices,
    )
    issues = EnrolledUserTrackerIssueInlineSerializer(many=True)
    language = EnrollTabLanguageField(source="*", allow_null=True)

    class Meta:
        model = EnrolledUser
        fields = (
            "id",
            "application_status",
            "issues",
            "language",
        )
        read_only_fields = fields


class CourseStudentTabInlineSerializer(serializers.ModelSerializer):
    score = CourseStudentProgressScoreField(source="*", allow_null=True)
    language = CourseStudentTabLanguageField(source="*", allow_null=True)

    class Meta:
        model = CourseStudent
        fields = (
            "id",
            "status",
            "substatus",
            "is_passed",
            "is_required",
            "is_visible",
            "score",
            "language",
        )
        read_only_fields = fields


class MyBaseTabSerializer(serializers.Serializer):
    """
    Base serializer that defines the contract for all tab endpoints.
    Each endpoint works with different entities, so subclasses must extract fields
    from the corresponding input entity types.
    """

    course = serializers.SerializerMethodField()
    enroll = serializers.SerializerMethodField(allow_null=True)
    student = serializers.SerializerMethodField(allow_null=True)

    @extend_schema_field(CourseTabInlineSerializer())
    def get_course(
        self, obj: Course | EnrolledUser | CourseStudent
    ) -> CourseTabInlineSerializer:
        course = self._get_course(obj)
        return CourseTabInlineSerializer(course).data

    @extend_schema_field(EnrollTabInlineSerializer())
    def get_enroll(
        self, obj: Course | EnrolledUser | CourseStudent
    ) -> EnrollTabInlineSerializer | None:
        enroll = self._get_enroll(obj)
        if enroll:
            return EnrollTabInlineSerializer(enroll).data

    @extend_schema_field(CourseStudentTabInlineSerializer())
    def get_student(
        self, obj: Course | EnrolledUser | CourseStudent
    ) -> CourseStudentTabInlineSerializer | None:
        student = self._get_student(obj)
        if student:
            return CourseStudentTabInlineSerializer(student).data

    def _get_course(self, obj: Course | EnrolledUser | CourseStudent) -> Course:
        raise NotImplementedError()

    def _get_enroll(
        self, obj: Course | EnrolledUser | CourseStudent
    ) -> EnrolledUser | None:
        raise NotImplementedError()

    def _get_student(
        self, obj: Course | EnrolledUser | CourseStudent
    ) -> CourseStudent | None:
        raise NotImplementedError()

    class Meta:
        fields = (
            "course",
            "enroll",
            "student",
        )
        read_only_fields = fields


class MyCoursesTabSerializer(MyBaseTabSerializer):
    """
    Serializer that accepts a course and extracts its application and student.
    """

    def _get_course(self, obj: Course) -> Course:
        return obj

    def _get_enroll(self, obj: Course) -> EnrolledUser | None:
        return obj.enrolled_users.first()

    def _get_student(self, obj: Course) -> CourseStudent | None:
        return obj.students.first()


class MyStudentsTabSerializer(MyBaseTabSerializer):
    """
    Serializer that accepts a student and extracts its application and student.
    """

    def _get_course(self, obj: CourseStudent) -> Course:
        course = obj.course
        course.bookmark = obj.bookmark
        return course

    def _get_enroll(self, obj: CourseStudent) -> EnrolledUser | None:
        return obj.enrolled_users.first()

    def _get_student(self, obj: CourseStudent) -> CourseStudent | None:
        return obj


class MyEnrollsTabSerializer(MyBaseTabSerializer):
    """
    Serializer that accepts an application and extracts its course and student.
    """

    def _get_course(self, obj: EnrolledUser) -> Course:
        course = obj.course
        course.bookmark = obj.bookmark
        return course

    def _get_enroll(self, obj: EnrolledUser) -> EnrolledUser | None:
        return obj

    def _get_student(self, obj: EnrolledUser) -> CourseStudent | None:
        return obj.course_student
