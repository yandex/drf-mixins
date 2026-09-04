from datetime import datetime
from typing import Optional, Tuple

from django.db.models import Max, Min

from .models import CourseGroup


def get_group_dates_from_timeslots(
    group: Optional[CourseGroup],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Calculate study start and end dates from group time slots.
    Return the group's own dates when it has no time slots.
    """
    if group is None:
        return None, None

    timeslot_dates = group.timeslots.aggregate(
        min_begin=Min("begin_date"),
        max_end=Max("end_date"),
    )

    start = timeslot_dates["min_begin"] or group.begin_date
    end = timeslot_dates["max_end"] or group.end_date

    return start, end
