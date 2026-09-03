from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin

from ..models import Course

User = get_user_model()


def expected_ids(courses):
    return [{"id": course.id} for course in courses]


@override_settings(ROOT_URLCONF="courses.urls")
class CourseFilterTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "course-list"

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="filter-author", yauid=11)
        cls.active_course = Course.objects.create(
            author=user,
            slug="active-course",
            name="Active Python",
            course_type=Course.TypeChoices.COURSE,
            format=Course.FormatChoices.SELF_STUDY,
            is_active=True,
            estimated_time=60,
        )
        cls.archived_track = Course.objects.create(
            author=user,
            slug="archived-track",
            name="Archived track",
            course_type=Course.TypeChoices.TRACK,
            format=Course.FormatChoices.WITH_TEACHER,
            is_archive=True,
        )

    def test_filter_by_type(self):
        self.list_request(
            f"{self.get_url()}?course_type={Course.TypeChoices.TRACK}",
            expected_ids([self.archived_track]),
            pagination=False,
            only_ids=True,
        )

    def test_filter_by_format(self):
        self.list_request(
            f"{self.get_url()}?course_format={Course.FormatChoices.SELF_STUDY}",
            expected_ids([self.active_course]),
            pagination=False,
            only_ids=True,
        )

    def test_filter_by_active(self):
        self.list_request(
            f"{self.get_url()}?is_active=true",
            expected_ids([self.active_course]),
            pagination=False,
            only_ids=True,
        )

    def test_filter_by_archive(self):
        self.list_request(
            f"{self.get_url()}?is_archive=true",
            expected_ids([self.archived_track]),
            pagination=False,
            only_ids=True,
        )

    def test_filter_by_ids(self):
        self.list_request(
            f"{self.get_url()}?ids={self.archived_track.id},{self.active_course.id}",
            expected_ids([self.active_course, self.archived_track]),
            pagination=False,
            only_ids=True,
        )

    def test_filter_by_one_id(self):
        self.list_request(
            f"{self.get_url()}?ids={self.active_course.id}",
            expected_ids([self.active_course]),
            pagination=False,
            only_ids=True,
        )

    def test_empty_ids_does_not_filter(self):
        self.list_request(
            f"{self.get_url()}?ids=",
            expected_ids([self.active_course, self.archived_track]),
            pagination=False,
            only_ids=True,
        )

    def test_search_by_name(self):
        self.list_request(
            f"{self.get_url()}?search=python",
            expected_ids([self.active_course]),
            pagination=False,
            only_ids=True,
        )
