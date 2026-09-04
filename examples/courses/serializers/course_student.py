from django.contrib.auth import get_user_model
from rest_framework import serializers

from lms.users.serializers import UserDetailLabSerializer

from ..models import CourseStudent

User = get_user_model()


class CourseStudentListLabSerializer(serializers.ModelSerializer):
    user = UserDetailLabSerializer()

    class Meta:
        model = CourseStudent
        fields = (
            "id",
            "course_id",
            "group_id",
            "status",
            "is_passed",
            "user",
            "is_required",
            "required_since",
            "created",
            "modified",
        )
        read_only_fields = fields
