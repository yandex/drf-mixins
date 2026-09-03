SECRET_KEY = "tests"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "tests.testapp",
    "yandex_drf_mixins",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
ROOT_URLCONF = "tests.urls"
USE_TZ = True

MIGRATION_MODULES = {"testapp": None}
