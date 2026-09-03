from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from courses.models import Course

from .filters import CourseCategoryWithCoursesFilter
from .services import get_categories_with_available_courses_ids

User = get_user_model()


class CourseCategoryFilterSet(filters.FilterSet):
    with_courses = CourseCategoryWithCoursesFilter()
    with_available_courses = filters.BooleanFilter(
        method="filter_with_available_courses"
    )

    def filter_with_available_courses(self, queryset, name, value):
        if value is True:
            view_permission = Course.objects.get_default_permission("view")
            if not self.request.user.has_perm(view_permission):
                queryset = queryset.filter(
                    id__in=get_categories_with_available_courses_ids(self.request.user)
                )

        return queryset
