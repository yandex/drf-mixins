# yandex-drf-mixins

Typed reusable components for Django REST Framework and ADRF.

The library provides several independent groups of mixins:

- DRF and ADRF `ModelViewSet` base classes, action-specific serializer selection,
  and create/update/upsert responses rendered with a retrieve serializer;
- query-parameter and request-body serialization and validation;
- synchronous and asynchronous limit/offset pagination with `?all=true` support;
- URL and API request test mixins that check status codes, JSON contracts, error
  codes, and SQL query counts.

Components can be used independently or as a coherent set through
`BaseModelViewSet` and `ABaseModelViewSet`.

## Installation

```bash
pip install yandex-drf-mixins
```

ADRF is an optional dependency:

```bash
pip install 'yandex-drf-mixins[adrf]'
```

Supported versions:

- Python 3.10–3.13;
- Django 4.0–5.1;
- Django REST Framework 3.14–3.15;
- ADRF 0.1.7+ within the 0.1.x series.

The package includes a `py.typed` marker, so its public API types are available to
mypy and other PEP 561-compatible type checkers.

### Internationalization

The package provides English source messages and Russian translations for its
user-facing API errors and schema descriptions. Add the package to Django's
application registry so Django can discover the bundled translation catalog:

```python
INSTALLED_APPS = [
    # ...
    "yandex_drf_mixins",
]
```

The active translation follows Django's standard `LANGUAGE_CODE`, locale
middleware, and `translation.override()` behavior. English remains the fallback
when no supported translation is active.

## Quick start

Add two mixins to a regular `APITestCase`:

```python
from rest_framework.test import APITestCase

from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin


class CourseListTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "api:course-list"
```

The route is then resolved by name, while the request and routine assertions fit
into a single method call.

## LMS test examples

User setup, authentication, and factory data are omitted because they are
application-specific and identical with or without this library.

### LMS: test a paginated list

This example is adapted from LMS tag tests. The domain-specific
`build_expected()` helper is omitted because it is unchanged by the library.

```python
class TagListTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "api:tag-list"

    def test_list(self):
        expected = self.build_expected(self.tags)

        self.list_request(
            url=self.get_url(),
            expected=expected,
            num_queries=4,
        )
```

`list_request()` checks:

- HTTP 200;
- the standard DRF pagination structure: `count`, `next`, `previous`, `results`;
- the value of `count`;
- object IDs and their order;
- the complete JSON representation of every object;
- exactly four SQL queries.

<details>
<summary>Without the library: the same list test written manually</summary>

```python
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TagListTestCase(APITestCase):
    def test_list(self):
        expected = self.build_expected(self.tags)
        url = reverse("api:tag-list")

        with self.assertNumQueries(4):
            response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.keys(),
            {"count", "next", "previous", "results"},
        )
        self.assertEqual(response.data["count"], len(expected))
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [item["id"] for item in expected],
        )
        self.assertListEqual(response.data["results"], expected)
```

</details>

### LMS: test creation and a serializer error code

`expected` may be a function of the response, which is useful for generated IDs
or timestamps. DRF errors can be checked by their stable `ErrorDetail.code`
values instead of localized messages. Implementations of `build_expected()` and
`build_expected_errors()` are omitted.

```python
class TagCreateTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "labapi:tag-create"

    def test_create(self):
        tag = TagFactory.build()

        self.create_request(
            url=self.get_url(),
            data={"name": tag.name},
            expected=lambda response: self.build_expected(tag, response),
            num_queries=5,
        )

    def test_duplicate_name(self):
        self.create_request(
            url=self.get_url(),
            data={"name": "existing-tag"},
            status_code=400,
            check_errors=True,
            expected=self.build_expected_errors(),
            num_queries=2,
        )
```

<details>
<summary>Without the library: creation and error checks written manually</summary>

```python
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TagCreateTestCase(APITestCase):
    def test_create(self):
        tag = TagFactory.build()
        url = reverse("labapi:tag-create")

        with self.assertNumQueries(5):
            response = self.client.post(
                url,
                data={"name": tag.name},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(
            response.data,
            self.build_expected(tag, response),
        )

    def test_duplicate_name(self):
        url = reverse("labapi:tag-create")

        with self.assertNumQueries(2):
            response = self.client.post(
                url,
                data={"name": "existing-tag"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_errors = self.build_expected_errors()
        self.assertEqual(response.data.keys(), expected_errors.keys())
        self.assertEqual(
            response.data["name"][0].code,
            expected_errors["name"][0],
        )
```

</details>

`update_request()`, `partial_update_request()`, and `delete_request()` work the
same way. Tests contain only endpoint-specific data, while requests and repeated
assertions remain in the library.

## API structure

Public components are separated by execution model:

```python
from yandex_drf_mixins.drf import BaseModelViewSet
from yandex_drf_mixins.adrf import ABaseModelViewSet
from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin
```

- `yandex_drf_mixins.drf` contains synchronous DRF components;
- `yandex_drf_mixins.adrf` contains ADRF components, with asynchronous classes
  prefixed by `A`;
- `yandex_drf_mixins.testing` contains API test mixins;
- `yandex_drf_mixins.base` is internal and must not be imported by applications.

## Testing API

### `UrlNameMixin`

Set `URL_NAME` and use:

- `get_url(*args, **kwargs)` to call Django `reverse()`;
- `assertURLNameEqual(url, base_url=None, args=None, kwargs=None)` to check that a
  named route matches the expected URL.

```python
class CourseDetailTestCase(UrlNameMixin, APITestCase):
    URL_NAME = "api:course-detail"

    def test_url(self):
        self.assertURLNameEqual(
            "courses/{}/",
            args=(self.course.id,),
            base_url="api/v1/",
        )
```

### `GenericRequestMixin`

Common request helper arguments:

- `expected`: expected JSON or a `response -> expected` callable;
- `status_code`: expected status, defaulting to 200, 201 for create, and 204 for
  delete;
- `num_queries`: expected SQL query count; `None` disables the check;
- `check_errors=True`: recursively compare DRF error codes;
- `data`: JSON request body.

Available methods:

| Method | Default HTTP | Purpose |
|---|---:|---|
| `list_request()` | GET | Check a list and optional DRF pagination |
| `detail_request()` | GET | Check one object |
| `create_request()` | POST | Check creation, expecting 201 by default |
| `update_request()` | PUT | Check a full update |
| `partial_update_request()` | PATCH | Check a partial update |
| `delete_request()` | DELETE | Check deletion, expecting 204 by default |
| `make_request()` | configurable | Perform any supported request scenario |
| `assert_errors()` | — | Recursively compare `ErrorDetail` structures and codes |

Additional `list_request()` arguments:

- `pagination=True`: expect `count/next/previous/results`;
- `count`: expected total size, including a correct `count=0` check;
- `check_ids=True`: compare object IDs;
- `only_ids=True`: limit comparison to IDs;
- `check_order=False`: compare without considering order.

In synchronous tests, an explicit `num_queries` uses Django's native
`assertNumQueries()`. The check is unreliable inside an event loop, so it is
ignored there with a `RuntimeWarning`. Pass `num_queries=None` when SQL budgets
are intentionally not checked.

## Action-specific serializers

### `ActionSerializerMixin`

Select a serializer by `self.action`:

```python
from yandex_drf_mixins.drf import ActionSerializerMixin


class CourseViewSet(ActionSerializerMixin, ModelViewSet):
    serializer_class = CourseSerializer
    serializer_classes = {
        "list": CourseListSerializer,
        "retrieve": CourseDetailSerializer,
        "create": CourseWriteSerializer,
    }
```

`get_serializer_class()` returns the action-specific class or falls back to
`serializer_class`. `get_retrieve_serializer()` always selects the `retrieve`
serializer and adds the regular viewset serializer context. The same
`ActionSerializerMixin` is exported from both `drf` and `adrf`.

## Write serializer input, retrieve serializer output

### Synchronous mixins

- `CreateWithRetrieveModelMixin` validates the input serializer, calls
  `perform_create()`, and renders the retrieve serializer;
- `UpdateWithRetrieveModelMixin` supports PUT/PATCH, calls `perform_update()`,
  clears the prefetch cache, and renders the retrieve serializer;
- `UpdateOrCreateWithRetrieveModelMixin` updates an existing object or switches
  the action to `create` after `Http404` and creates a new one;
- Django `ValidationError` is converted to DRF `ValidationError` with exception
  chaining preserved.

```python
from yandex_drf_mixins.drf import BaseModelViewSet


class CourseViewSet(BaseModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    serializer_classes = {
        "create": CourseWriteSerializer,
        "update": CourseWriteSerializer,
        "partial_update": CourseWriteSerializer,
        "retrieve": CourseDetailSerializer,
    }
```

### Asynchronous counterparts

- `ACreateWithRetrieveModelMixin`: `acreate()`, `acreate_with_retrieve()`, and
  `aperform_create()`;
- `AUpdateWithRetrieveModelMixin`: `aupdate()`, `apartial_update()`,
  `aupdate_with_retrieve()`, `apartial_update_with_retrieve()`, and
  `aperform_update()`;
- `AUpdateOrCreateWithRetrieveModelMixin`: `aupdate_or_create()`.

The default `aperform_create()` and `aperform_update()` implementations call
`await serializer.asave()`. After `aperform_create()`, the serializer must have
an `instance`, otherwise the library raises `ImproperlyConfigured`. Asynchronous
serializer data is read through the native `adrf.mixins.get_data()` helper.

## Protected deletion

### `DeleteProtectedModelMixin`

The synchronous mixin converts Django `ValidationError` and `ProtectedError`
into DRF errors. Protected-relation text is configured through class attributes:

```python
class CourseViewSet(BaseModelViewSet):
    protected_error_message = "Course cannot be deleted: %(object_name)s exists"
    protected_object_default_name = "related data"
    protected_objects_limit = 1
```

`protected_objects_limit` limits the number of protecting object names in the
message. It defaults to `1`; `None` includes all names.
`protected_object_default_name` is used when `ProtectedError` has no objects.
These settings are shared by synchronous and asynchronous mixins.

`ProtectedError` is returned as one `ErrorDetail`, not a one-element list.

### `ADeleteProtectedModelMixin`

The asynchronous version provides `adestroy()` and `aperform_destroy()`. Its
default implementation calls `await instance.adelete()` and handles
`ValidationError` and `ProtectedError` in the same way.

## Query-parameter and request-body validation

### DRF

```python
from rest_framework.views import APIView
from yandex_drf_mixins.drf import SerializeGetParamsViewMixin


class CourseSearchView(SerializeGetParamsViewMixin, APIView):
    params_serializer_class = CourseSearchParamsSerializer

    def get(self, request):
        params = self.validated_params
        return Response(search_courses(**params))
```

- `SerializeGetParamsViewMixin` serializes `request.query_params`;
- `SerializePostParamsViewMixin` serializes `request.data`;
- `params_serializer_class` selects the serializer;
- `params_raise_exception` controls `is_valid(raise_exception=...)`;
- `params_serializer_many=True` collects query parameters into a list of objects;
- `validated_params` is evaluated lazily and cached.

### ADRF

`ASerializeGetParamsViewMixin` and `ASerializePostParamsViewMixin` use the same
configuration contract but expose the result asynchronously:

```python
class AsyncCourseSearchView(ASerializeGetParamsViewMixin, APIView):
    params_serializer_class = CourseSearchParamsSerializer

    async def get(self, request):
        params = await self.avalidated_params()
        return Response(await search_courses(**params))
```

## Lists with additional data

`ListWithAdditionalDataMixin` serializes an object containing a queryset and
additional fields:

```python
def list(self, request, *args, **kwargs):
    return self.list_with_additional_data(
        request,
        additional_data={"facets": build_facets()},
        objects_field_name="courses",
    )
```

The asynchronous `AListWithAdditionalDataMixin` provides
`await alist_with_additional_data(...)`. Both variants apply
`filter_queryset()` and keep the queryset lazy until serialization.

## Pagination

### `LimitOffsetAllPagination`

Extends DRF `LimitOffsetPagination` with `?all=true`:

```python
from yandex_drf_mixins.drf import LimitOffsetAllPagination


class CourseViewSet(BaseModelViewSet):
    pagination_class = LimitOffsetAllPagination
```

- without `all`, standard limit/offset pagination is used;
- `?all=true` returns all items as one lazy queryset slice;
- an invalid boolean value is treated as `False`;
- `all` is added to OpenAPI operation parameters;
- the legacy CoreAPI schema is not supported.

### Asynchronous pagination

- `ALimitOffsetPagination` is the asynchronous equivalent of standard
  limit/offset pagination;
- `ALimitOffsetAllPagination` additionally supports `?all=true`;
- `aget_count()` uses `QuerySet.acount()` and falls back to `len()` for ordinary
  sequences;
- `apaginate_queryset()` returns a lazy slice without converting it to `list`.

## Base viewsets

### `BaseModelViewSet`

Combines:

- `ActionSerializerMixin`;
- create/update with retrieve serialization;
- update-or-create;
- protected deletion;
- lists with additional data;
- the standard DRF `ModelViewSet`.

### `ABaseModelViewSet`

The asynchronous base class includes:

- `AListModelMixin` with `alist()`;
- asynchronous create/update/update-or-create/delete mixins;
- `AListWithAdditionalDataMixin`;
- `aget_object()` through `adrf.shortcuts.aget_object_or_404`;
- `acheck_object_permissions()` with mixed sync/async permission support;
- `apaginate_queryset()` adapters for asynchronous and regular paginators.

`get_queryset()` may be synchronous or declared with `async def`; the library
detects the variant with `iscoroutinefunction`. `filter_queryset()` intentionally
remains synchronous.

ADRF example:

```python
from yandex_drf_mixins.adrf import ABaseModelViewSet, ALimitOffsetAllPagination


class StaffOccupationViewSet(ABaseModelViewSet):
    queryset = StaffOccupation.objects.select_related("direction")
    serializer_class = StaffOccupationSerializer
    pagination_class = ALimitOffsetAllPagination

    async def list(self, request, *args, **kwargs):
        return await self.alist(request, *args, **kwargs)
```

Every coroutine method owned by the library has an `a` prefix. Synchronous
methods are not duplicated in ADRF classes.

## Canonical courses example

The sanitized LMS `courses` application is available under `examples/courses`.
It demonstrates realistic viewsets, serializers, filters, pagination, CRUD,
upsert, protected deletion, and compact tests built with `GenericRequestMixin`.
See `examples/README.md` for setup and test commands.

## Running library tests

Run commands from the repository root. For the complete suite, including the
ADRF contract, create an isolated environment and install development dependencies:

```bash
python3.13 -m venv venv
source venv/bin/activate
python3 -m pip install -e '.[dev]'
python3 -m pytest
```

`DJANGO_SETTINGS_MODULE=tests.settings` and the test directory are configured in
`pyproject.toml`, so they do not need to be passed on the command line.

Run contract groups independently:

```bash
# Synchronous DRF components
python3 -m pytest tests/test_drf.py

# Asynchronous ADRF components
python3 -m pytest tests/test_adrf.py

# Public imports, testing mixins, and release skill
python3 -m pytest \
  tests/test_public_api.py \
  tests/test_testing.py \
  tests/test_release_skill.py
```

Repeat the full suite on Python 3.10 to check the minimum supported version. If
ADRF is not installed, ADRF-specific tests are skipped while DRF and testing
contracts must still pass.

## Development

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest
python3 -m black --check src tests
python3 -m isort --check-only src tests
python3 -m flake8 src tests
python3 -m mypy --explicit-package-bases src/yandex_drf_mixins
PYTHONPATH=.:src python3 -m pylint src/yandex_drf_mixins
python3 -m bandit -q -r src
python3 -m build
```

Build and test the wheel locally in LMS before publishing. Publication is a
separate explicitly confirmed step.

Use `.agents/yandex-drf-mixins-release/skill.md` to prepare a release. The skill
performs reversible preparation and verification automatically, but never runs
the irreversible `twine upload` command.
