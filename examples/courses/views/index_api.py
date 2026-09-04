from django.utils.translation import gettext
from drf_spectacular.utils import extend_schema

from lms.core.views.pagination import LimitOffsetAllPagination
from lms.core.views.viewsets import APIModelViewSet

from ..models import Course
from ..serializers.course_index import CourseIndexSerializer


class CourseIndexViewSet(APIModelViewSet):
    """Endpoints used by the internal search indexer."""

    serializer_class = CourseIndexSerializer
    queryset = Course.objects.filter(
        is_archive=False,
        is_active=True,
        course_type=Course.TypeChoices.COURSE,
    )
    pagination_class = LimitOffsetAllPagination

    @extend_schema(summary=gettext("List courses for internal search indexing"))
    def list(self, request, *args, **kwargs):  # noqa: A003
        return super().list(request, *args, **kwargs)

    @extend_schema(summary=gettext("Course details for internal search indexing"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
