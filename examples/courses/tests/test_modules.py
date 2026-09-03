from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin

from lms.moduletypes.models import ModuleType

from ..models import Course, CourseBlock, CourseModule

User = get_user_model()


def expected_module(module):
    return {
        "id": module.id,
        "course": module.course_id,
        "block": module.block_id,
        "module_type": module.module_type_id,
        "name": module.name,
        "description": module.description,
        "estimated_time": module.estimated_time,
        "is_active": module.is_active,
        "weight": module.weight,
        "order": module.order,
    }


@override_settings(ROOT_URLCONF="courses.urls")
class CourseModuleApiTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "course-module-list"

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="module-author", yauid=14)
        cls.course = Course.objects.create(
            author=user, slug="modules-course", name="Modules course"
        )
        cls.other_course = Course.objects.create(
            author=user, slug="other-course", name="Other course"
        )
        cls.block = CourseBlock.objects.create(course=cls.course, name="Block")
        cls.module_type, _ = ModuleType.objects.get_or_create(
            app_label="courses", model="coursemodule"
        )
        cls.module = CourseModule.objects.create(
            course=cls.course,
            block=cls.block,
            module_type=cls.module_type,
            name="Introduction",
            estimated_time=30,
        )

    def get_detail_url(self):
        return reverse("course-module-detail", args=[self.module.id])

    def test_list(self):
        self.list_request(
            self.get_url(),
            [expected_module(self.module)],
            pagination=False,
            num_queries=1,
        )

    def test_detail(self):
        self.detail_request(
            self.get_detail_url(), expected=expected_module(self.module), num_queries=1
        )

    def test_create(self):
        response = self.create_request(
            self.get_url(),
            data={
                "course": self.course.id,
                "block": self.block.id,
                "module_type": self.module_type.id,
                "name": "Practice",
                "estimated_time": 45,
            },
        )
        self.assertTrue(
            CourseModule.objects.filter(
                id=response.data["id"], name="Practice"
            ).exists()
        )

    def test_create_rejects_block_from_another_course(self):
        other_block = CourseBlock.objects.create(
            course=self.other_course, name="Other block"
        )
        self.create_request(
            self.get_url(),
            data={
                "course": self.course.id,
                "block": other_block.id,
                "module_type": self.module_type.id,
                "name": "Invalid",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
            check_errors=True,
            expected={"__all__": ["invalid"]},
        )

    def test_partial_update(self):
        self.partial_update_request(
            self.get_detail_url(), data={"description": "Updated"}
        )
        self.assertEqual(
            CourseModule.objects.get(id=self.module.id).description, "Updated"
        )

    def test_delete(self):
        self.delete_request(self.get_detail_url())
        self.assertFalse(CourseModule.objects.filter(id=self.module.id).exists())


@override_settings(ROOT_URLCONF="courses.urls")
class ProtectedCourseBlockDeleteTestCase(
    UrlNameMixin, GenericRequestMixin, APITestCase
):
    URL_NAME = "course-block-detail"

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="protected-author", yauid=15)
        course = Course.objects.create(
            author=user, slug="protected-course", name="Protected course"
        )
        cls.block = CourseBlock.objects.create(course=course, name="Protected block")
        module_type, _ = ModuleType.objects.get_or_create(
            app_label="courses", model="coursemodule"
        )
        CourseModule.objects.create(
            course=course, block=cls.block, module_type=module_type, name="Module"
        )

    def test_delete_reports_protected_error(self):
        self.delete_request(
            self.get_url(self.block.id),
            status_code=status.HTTP_400_BAD_REQUEST,
            check_errors=True,
            expected={"detail": "protected"},
        )
