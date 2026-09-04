from django_filters import rest_framework as filters
from django_filters.constants import EMPTY_VALUES


class CourseCategoryWithCoursesFilter(filters.BooleanFilter):
    def filter(self, qs, value):  # noqa: A003
        if value in EMPTY_VALUES:
            return qs

        if value is True:
            qs = qs.with_courses()
        if value is False:
            qs = qs.without_courses()

        return qs
