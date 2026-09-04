from rest_framework import serializers

from courses.models import Course
from lms.calendars.models import CalendarEvent, CalendarLayer
from lms.classrooms.models import Timeslot


class CourseCalendarTimeslotInlineSerializer(serializers.ModelSerializer):
    calendar_event_id = serializers.PrimaryKeyRelatedField(
        source="calendar_event",
        queryset=CalendarEvent.objects.all(),
    )

    class Meta:
        model = Timeslot
        fields = (
            "id",
            "calendar_event_id",
            "begin_date",
            "end_date",
        )
        read_only_fields = fields


class CourseCalendarSerializer(serializers.ModelSerializer):
    calendar_layer_id = serializers.PrimaryKeyRelatedField(
        source="calendar_layer",
        queryset=CalendarLayer.objects.all(),
    )
    timeslots = CourseCalendarTimeslotInlineSerializer(
        many=True, read_only=True, source="classroom_timeslots"
    )

    class Meta:
        model = Course
        fields = (
            "id",
            "calendar_layer_id",
            "timeslots",
        )
        read_only_fields = fields
