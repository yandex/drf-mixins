import os

from django.apps import AppConfig

SECRET_KEY = "example-only"


class UsersConfig(AppConfig):
    name = "lms.users"
    label = "users"


class PreferencesConfig(AppConfig):
    name = "lms.preferences"
    label = "preferences"


class TagsConfig(AppConfig):
    name = "lms.tags"
    label = "tags"


class CourseTeamsConfig(AppConfig):
    name = "lms.courseteams"
    label = "courseteams"


class ModuleTypesConfig(AppConfig):
    name = "lms.moduletypes"
    label = "moduletypes"


class BookmarksConfig(AppConfig):
    name = "lms.bookmarks"
    label = "bookmarks"


USE_TZ = True
TIME_ZONE = "UTC"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
ROOT_URLCONF = "courses.urls"
AUTH_USER_MODEL = "users.User"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "lms"),
        "USER": os.environ.get("POSTGRES_USER", "lms"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": int(os.environ.get("POSTGRES_PORT", "5432")),
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "guardian",
    "simple_history",
    "django_celery_beat",
    "example_settings.UsersConfig",
    "example_settings.PreferencesConfig",
    "example_settings.TagsConfig",
    "example_settings.CourseTeamsConfig",
    "example_settings.ModuleTypesConfig",
    "example_settings.BookmarksConfig",
    "courses",
]

MIDDLEWARE = []
MIGRATION_MODULES = {
    "users": None,
    "preferences": None,
    "tags": None,
    "courseteams": None,
    "moduletypes": None,
    "bookmarks": None,
}
REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": []}
COURSE_MODULE_DEFAULT_WEIGHT = 0
COURSE_RESERVED_SLUGS = set()
FRONTEND_ROOT = "https://example.test"
FRONTEND_LAB_ROOT = "https://example.test/lab"
ADMIN_ROOT = "https://example.test/admin"
