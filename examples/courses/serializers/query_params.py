from rest_framework import serializers


class CourseIdsParamsSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        allow_empty=False,
    )

    class Meta:
        fields = ("ids",)
        required_fields = fields
