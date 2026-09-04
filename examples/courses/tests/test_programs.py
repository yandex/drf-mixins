from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin

from ..models import Course, CourseProgram

User = get_user_model()


@override_settings(ROOT_URLCONF="courses.urls")
class CourseProgramUpsertTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "course-program-detail"

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="program-author", yauid=13)
        cls.course = Course.objects.create(
            author=user, slug="program-course", name="Program course"
        )

    def get_detail_url(self):
        return self.get_url(self.course.id)

    def test_url(self):
        self.assertURLNameEqual("/programs/{}/", args=[self.course.id])

    def test_put_creates_missing_program(self):
        program = {
            "group_blocks": False,
            "modules": [{"title": "Introduction", "minutes": 30}],
        }
        self.update_request(
            self.get_detail_url(),
            data={"course": self.course.id, "program": program},
            expected={"course": self.course.id, "program": program},
            status_code=status.HTTP_201_CREATED,
        )
        self.assertTrue(CourseProgram.objects.filter(course=self.course).exists())

    def test_put_updates_existing_program(self):
        CourseProgram.objects.create(course=self.course)
        program = {"group_blocks": True, "blocks": [{"title": "Part 1", "modules": []}]}
        self.update_request(
            self.get_detail_url(),
            data={"course": self.course.id, "program": program},
            expected={"course": self.course.id, "program": program},
        )

    def test_invalid_program_reports_error(self):
        self.update_request(
            self.get_detail_url(),
            data={"course": self.course.id, "program": {}},
            status_code=status.HTTP_400_BAD_REQUEST,
            check_errors=True,
            expected={"program": ["invalid", "invalid", "invalid", "invalid"]},
        )

    def test_unknown_course_reports_error(self):
        self.update_request(
            self.get_url(999999),
            data={"course": 999999, "program": {"group_blocks": False, "modules": []}},
            status_code=status.HTTP_400_BAD_REQUEST,
            check_errors=True,
            expected={"course": ["does_not_exist"]},
        )
