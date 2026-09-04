from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin

from ..models import Course

User = get_user_model()


def expected_course(course):
    return {
        "id": course.id,
        "slug": course.slug,
        "name": course.name,
        "shortname": course.shortname,
        "summary": course.summary,
        "description": course.description,
        "target_audience_description": course.target_audience_description,
        "estimated_time": course.estimated_time,
        "author_id": course.author_id,
    }


@override_settings(ROOT_URLCONF="courses.urls")
class CoursePaginationTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "paginated-course-list"

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="pagination-author", yauid=12)
        cls.courses = [
            Course.objects.create(
                author=user, slug=f"course-{index}", name=f"Course {index}"
            )
            for index in range(3)
        ]

    def test_default_page(self):
        self.list_request(
            self.get_url(),
            [expected_course(course) for course in self.courses[:2]],
            count=3,
        )

    def test_limit(self):
        self.list_request(
            f"{self.get_url()}?limit=1", [expected_course(self.courses[0])], count=3
        )

    def test_offset(self):
        self.list_request(
            f"{self.get_url()}?limit=2&offset=1",
            [expected_course(course) for course in self.courses[1:]],
            count=3,
        )

    def test_all_returns_every_object(self):
        self.list_request(
            f"{self.get_url()}?all=true",
            [expected_course(course) for course in self.courses],
            count=3,
        )

    def test_all_respects_offset(self):
        self.list_request(
            f"{self.get_url()}?all=true&offset=1",
            [expected_course(course) for course in self.courses[1:]],
            count=3,
        )

    def test_empty_page(self):
        self.list_request(f"{self.get_url()}?offset=10", [], count=3)
