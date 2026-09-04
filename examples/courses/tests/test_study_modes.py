from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin

from ..models import StudyMode


def expected_study_mode(study_mode):
    return {
        "id": study_mode.id,
        "slug": study_mode.slug,
        "name": study_mode.name,
        "description": study_mode.description,
        "is_active": study_mode.is_active,
        "order": study_mode.order,
    }


@override_settings(ROOT_URLCONF="courses.urls")
class StudyModeApiTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "study-mode-list"

    @classmethod
    def setUpTestData(cls):
        cls.study_mode = StudyMode.objects.create(slug="online", name="Online")

    def get_detail_url(self):
        return reverse("study-mode-detail", args=[self.study_mode.id])

    def test_url(self):
        self.assertURLNameEqual("/study-modes/")

    def test_list(self):
        self.list_request(
            self.get_url(),
            [expected_study_mode(self.study_mode)],
            pagination=False,
            num_queries=1,
        )

    def test_detail(self):
        self.detail_request(
            self.get_detail_url(),
            expected=expected_study_mode(self.study_mode),
            num_queries=1,
        )

    def test_create(self):
        response = self.create_request(
            self.get_url(), data={"slug": "hybrid", "name": "Hybrid"}
        )
        self.assertTrue(
            StudyMode.objects.filter(id=response.data["id"], slug="hybrid").exists()
        )

    def test_partial_update(self):
        self.partial_update_request(
            self.get_detail_url(),
            data={"description": "Remote"},
            expected=lambda _: expected_study_mode(
                StudyMode.objects.get(id=self.study_mode.id)
            ),
        )

    def test_duplicate_slug_error(self):
        self.create_request(
            self.get_url(),
            data={"slug": "online", "name": "Duplicate"},
            status_code=status.HTTP_400_BAD_REQUEST,
            check_errors=True,
            expected={"slug": ["unique"]},
        )

    def test_delete(self):
        self.delete_request(self.get_detail_url())
        self.assertFalse(StudyMode.objects.filter(id=self.study_mode.id).exists())
