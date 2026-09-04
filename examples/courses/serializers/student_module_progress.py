from rest_framework import serializers

from ..models import StudentModuleProgress


class StudentModuleProgressListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentModuleProgress
        fields = (
            "module_id",
            "score",
        )
        read_only_fields = fields
