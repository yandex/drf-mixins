from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from yandex_drf_mixins.drf import BaseModelViewSet, LimitOffsetAllPagination

from ..models import (
    Course,
    CourseBlock,
    CourseCategory,
    CourseModule,
    CourseProgram,
    StudyMode,
)
from ..serializers import (
    CourseBlockSerializer,
    CourseCategorySerializer,
    CourseModuleSerializer,
    CourseProgramSerializer,
    CourseRetrieveSerializer,
    CourseWriteSerializer,
    StudyModeSerializer,
)


class ExampleLimitOffsetAllPagination(LimitOffsetAllPagination):
    default_limit = 2


class CourseLabViewSet(BaseModelViewSet):
    queryset = Course.objects.select_related("author").order_by("id")
    serializer_class = CourseRetrieveSerializer
    serializer_classes = {
        "create": CourseWriteSerializer,
        "update": CourseWriteSerializer,
        "partial_update": CourseWriteSerializer,
        "retrieve": CourseRetrieveSerializer,
    }
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ("course_type", "is_active", "is_archive")
    search_fields = ("name",)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        ids = self.request.query_params.get("ids")
        if ids:
            queryset = queryset.filter(id__in=ids.split(","))
        course_format = self.request.query_params.get("course_format")
        if course_format:
            queryset = queryset.filter(format=course_format)
        return queryset


class PaginatedCourseLabViewSet(CourseLabViewSet):
    pagination_class = ExampleLimitOffsetAllPagination


class CourseCategoryLabViewSet(BaseModelViewSet):
    queryset = CourseCategory.objects.order_by("id")
    serializer_class = CourseCategorySerializer


class CourseBlockLabViewSet(BaseModelViewSet):
    queryset = CourseBlock.objects.select_related("course").order_by("id")
    serializer_class = CourseBlockSerializer


class CourseModuleLabViewSet(BaseModelViewSet):
    queryset = CourseModule.objects.select_related(
        "course", "block", "module_type"
    ).order_by("id")
    serializer_class = CourseModuleSerializer


class StudyModeLabViewSet(BaseModelViewSet):
    queryset = StudyMode.objects.order_by("order", "id")
    serializer_class = StudyModeSerializer


class CourseProgramLabViewSet(BaseModelViewSet):
    queryset = CourseProgram.objects.select_related("course")
    serializer_class = CourseProgramSerializer

    def update(self, request, *args, **kwargs):
        return self.update_or_create(request, *args, **kwargs)
