from rest_framework.routers import DefaultRouter

from .views import (
    CourseBlockLabViewSet,
    CourseCategoryLabViewSet,
    CourseLabViewSet,
    CourseModuleLabViewSet,
    CourseProgramLabViewSet,
    PaginatedCourseLabViewSet,
    StudyModeLabViewSet,
)

app_name = "courses-example"

router = DefaultRouter()
router.register("courses", CourseLabViewSet, basename="course")
router.register("categories", CourseCategoryLabViewSet, basename="course-category")
router.register("blocks", CourseBlockLabViewSet, basename="course-block")
router.register("modules", CourseModuleLabViewSet, basename="course-module")
router.register("study-modes", StudyModeLabViewSet, basename="study-mode")
router.register(
    "paginated-courses", PaginatedCourseLabViewSet, basename="paginated-course"
)
router.register("programs", CourseProgramLabViewSet, basename="course-program")

urlpatterns = router.urls
