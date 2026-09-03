from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin

from ..models import Course, CourseBlock, CourseCategory

User = get_user_model()


def expected_course(course: Course) -> dict:
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


def expected_category(category: CourseCategory) -> dict:
    return {
        "id": category.id,
        "slug": category.slug,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active,
    }


def expected_block(block: CourseBlock) -> dict:
    return {
        "id": block.id,
        "course": block.course_id,
        "name": block.name,
        "summary": block.summary,
        "is_active": block.is_active,
        "order": block.order,
    }


@override_settings(ROOT_URLCONF="courses.urls")
class CourseApiTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "course-list"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="course-author", yauid=1)
        cls.course = Course.objects.create(
            author=cls.user,
            slug="python-basics",
            name="Python basics",
            summary="A short course",
            estimated_time=60,
        )
        cls.second_course = Course.objects.create(
            author=cls.user,
            slug="django-basics",
            name="Django basics",
            estimated_time=45,
        )

    def get_detail_url(self, course: Course | None = None) -> str:
        return reverse("course-detail", args=[(course or self.course).id])

    def test_url_name_contract(self):
        self.assertURLNameEqual("/courses/")

    def test_list_checks_json_order_and_query_count(self):
        self.list_request(
            self.get_url(),
            [expected_course(self.course), expected_course(self.second_course)],
            pagination=False,
            num_queries=1,
        )

    def test_detail_checks_status_and_json_contract(self):
        self.detail_request(
            self.get_detail_url(),
            expected=expected_course(self.course),
            num_queries=1,
        )

    def test_create_returns_retrieve_serializer(self):
        self.client.force_authenticate(self.user)
        data = {
            "slug": "django-rest-framework",
            "name": "Django REST Framework",
            "summary": "Build APIs",
            "estimated_time": 90,
        }

        response = self.create_request(self.get_url(), data=data)

        course = Course.objects.get(slug=data["slug"])
        self.assertDictEqual(response.data, expected_course(course))

    def test_create_reports_serializer_errors(self):
        self.client.force_authenticate(self.user)
        self.create_request(
            self.get_url(),
            data={"slug": self.course.slug, "name": "Duplicate"},
            status_code=status.HTTP_400_BAD_REQUEST,
            check_errors=True,
            expected={"slug": ["unique"]},
        )

    def test_update_returns_retrieve_serializer(self):
        self.client.force_authenticate(self.user)
        response = self.update_request(
            self.get_detail_url(),
            data={
                "slug": self.course.slug,
                "name": "Advanced Python",
                "summary": "Updated by PUT",
                "estimated_time": 120,
            },
        )

        self.course.refresh_from_db()
        self.assertDictEqual(response.data, expected_course(self.course))

    def test_partial_update_returns_retrieve_serializer(self):
        self.client.force_authenticate(self.user)
        response = self.partial_update_request(
            self.get_detail_url(),
            data={"summary": "Updated by PATCH"},
        )

        self.course.refresh_from_db()
        self.assertDictEqual(response.data, expected_course(self.course))

    def test_delete_checks_status_and_removes_object(self):
        self.delete_request(self.get_detail_url())

        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_missing_object_checks_not_found_status(self):
        self.detail_request(
            reverse("course-detail", args=[999999]),
            status_code=status.HTTP_404_NOT_FOUND,
        )


@override_settings(ROOT_URLCONF="courses.urls")
class CourseCategoryApiTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "course-category-list"

    @classmethod
    def setUpTestData(cls):
        cls.category = CourseCategory.objects.create(slug="backend", name="Backend")
        cls.second_category = CourseCategory.objects.create(
            slug="frontend", name="Frontend", is_active=False
        )

    def get_detail_url(self, category: CourseCategory | None = None) -> str:
        return reverse("course-category-detail", args=[(category or self.category).id])

    def test_list_can_ignore_result_order(self):
        self.list_request(
            self.get_url(),
            [expected_category(self.second_category), expected_category(self.category)],
            pagination=False,
            check_order=False,
            num_queries=1,
        )

    def test_detail_checks_complete_response(self):
        self.detail_request(
            self.get_detail_url(),
            expected=expected_category(self.category),
            num_queries=1,
        )

    def test_create(self):
        response = self.create_request(
            self.get_url(),
            data={
                "slug": "databases",
                "name": "Databases",
                "description": "SQL courses",
            },
        )

        category = CourseCategory.objects.get(slug="databases")
        self.assertDictEqual(response.data, expected_category(category))

    def test_create_checks_required_field_error(self):
        self.create_request(
            self.get_url(),
            data={"slug": "empty-name"},
            status_code=status.HTTP_400_BAD_REQUEST,
            check_errors=True,
            expected={"name": ["required"]},
        )

    def test_update(self):
        response = self.update_request(
            self.get_detail_url(),
            data={
                "slug": "backend",
                "name": "Backend development",
                "description": "Server-side",
            },
        )

        self.category.refresh_from_db()
        self.assertDictEqual(response.data, expected_category(self.category))

    def test_partial_update(self):
        response = self.partial_update_request(
            self.get_detail_url(), data={"is_active": False}
        )

        self.category.refresh_from_db()
        self.assertDictEqual(response.data, expected_category(self.category))

    def test_delete(self):
        self.delete_request(self.get_detail_url())

        self.assertFalse(CourseCategory.objects.filter(id=self.category.id).exists())


@override_settings(ROOT_URLCONF="courses.urls")
class CourseBlockApiTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "course-block-list"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="block-author", yauid=2)
        cls.course = Course.objects.create(
            author=cls.user, slug="api-design", name="API design"
        )
        cls.block = CourseBlock.objects.create(
            course=cls.course, name="Introduction", summary="Start here"
        )

    def get_detail_url(self) -> str:
        return reverse("course-block-detail", args=[self.block.id])

    def test_list(self):
        self.list_request(
            self.get_url(),
            [expected_block(self.block)],
            pagination=False,
            num_queries=1,
        )

    def test_create(self):
        response = self.create_request(
            self.get_url(),
            data={
                "course": self.course.id,
                "name": "HTTP",
                "summary": "Protocol basics",
            },
        )

        block = CourseBlock.objects.get(id=response.data["id"])
        self.assertDictEqual(response.data, expected_block(block))

    def test_partial_update(self):
        response = self.partial_update_request(
            self.get_detail_url(), data={"summary": "Updated summary"}
        )

        self.block.refresh_from_db()
        self.assertDictEqual(response.data, expected_block(self.block))

    def test_delete(self):
        self.delete_request(self.get_detail_url())

        self.assertFalse(CourseBlock.objects.filter(id=self.block.id).exists())
