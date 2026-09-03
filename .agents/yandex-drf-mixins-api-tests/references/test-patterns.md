# Canonical test patterns

Use this reference after analyzing the target viewset. These snippets are
adapted from `examples/courses/tests`; replace domain names and fixtures with the
actual entities from the target project.

## Base test case and expected-response helper

```python
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from yandex_drf_mixins.testing import GenericRequestMixin, UrlNameMixin


def expected_entity(entity):
    return {
        "id": entity.id,
        "slug": entity.slug,
        "name": entity.name,
    }


class EntityApiTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "entity-list"

    def get_detail_url(self):
        return reverse("entity-detail", args=[self.entity.id])
```

The expected-response helper describes the endpoint's complete stable JSON.
Include only response fields, and calculate dynamic values from the object or
response whenever possible.

## URL, list, and detail

```python
def test_url(self):
    self.assertURLNameEqual("/entities/")

def test_list(self):
    self.list_request(
        self.get_url(),
        [expected_entity(self.entity)],
        pagination=False,
        num_queries=None,
    )

def test_detail(self):
    self.detail_request(
        self.get_detail_url(),
        expected=expected_entity(self.entity),
        num_queries=None,
    )
```

Use the full route name for namespaced routers, for example
`api:entity-list`. `assertURLNameEqual()` supports `args`, `kwargs`, and
`base_url`.

## Create, update, patch, and delete

```python
def test_create(self):
    response = self.create_request(
        self.get_url(),
        data={"slug": "new", "name": "New entity"},
    )
    entity = Entity.objects.get(id=response.data["id"])
    self.assertDictEqual(response.data, expected_entity(entity))

def test_update(self):
    response = self.update_request(
        self.get_detail_url(),
        data={"slug": self.entity.slug, "name": "Updated"},
    )
    self.entity.refresh_from_db()
    self.assertDictEqual(response.data, expected_entity(self.entity))

def test_partial_update(self):
    self.partial_update_request(
        self.get_detail_url(),
        data={"name": "Patched"},
        expected=lambda _: expected_entity(Entity.objects.get(id=self.entity.id)),
    )

def test_delete(self):
    self.delete_request(self.get_detail_url())
    self.assertFalse(Entity.objects.filter(id=self.entity.id).exists())
```

When write and retrieve serializers differ, the expected response must describe
the retrieve serializer. That is the contract provided by
`CreateWithRetrieveModelMixin` and `UpdateWithRetrieveModelMixin`.

## Error codes

```python
def test_duplicate_slug_error(self):
    self.create_request(
        self.get_url(),
        data={"slug": self.entity.slug, "name": "Duplicate"},
        status_code=status.HTTP_400_BAD_REQUEST,
        check_errors=True,
        expected={"slug": ["unique"]},
    )
```

`expected` mirrors the nested response structure but stores `ErrorDetail.code`
values at the leaves. Do not assert localized text such as
`"This field is required."`.

## Filters and search

```python
def expected_ids(entities):
    return [{"id": entity.id} for entity in entities]

def test_filter_by_active(self):
    self.list_request(
        f"{self.get_url()}?is_active=true",
        expected_ids([self.active_entity]),
        pagination=False,
        only_ids=True,
    )

def test_search(self):
    self.list_request(
        f"{self.get_url()}?search=python",
        expected_ids([self.python_entity]),
        pagination=False,
        only_ids=True,
    )
```

Create a separate test for every declared parameter. For a custom ID list,
cover single, multiple, and empty values when empty input has its own branch.

## `LimitOffsetAllPagination`

```python
def test_default_page(self):
    self.list_request(self.get_url(), expected[:2], count=3)

def test_limit_and_offset(self):
    self.list_request(f"{self.get_url()}?limit=1&offset=1", expected[1:2], count=3)

def test_all(self):
    self.list_request(f"{self.get_url()}?all=true", expected, count=3)

def test_empty_page(self):
    self.list_request(f"{self.get_url()}?offset=100", [], count=3)
```

Add `all=true` only for `LimitOffsetAllPagination` or its asynchronous equivalent.

## Update-or-create

```python
def test_put_creates_missing_object(self):
    self.update_request(
        self.get_detail_url(),
        data=self.payload,
        expected=self.expected,
        status_code=status.HTTP_201_CREATED,
    )

def test_put_updates_existing_object(self):
    RelatedObject.objects.create(parent=self.parent)
    self.update_request(
        self.get_detail_url(),
        data=self.payload,
        expected=self.expected,
    )
```

Both branches are required for `UpdateOrCreateWithRetrieveModelMixin`: create
returns 201 and update returns 200.

## Protected deletion

```python
def test_delete_reports_protected_error(self):
    self.delete_request(
        self.get_detail_url(),
        status_code=status.HTTP_400_BAD_REQUEST,
        check_errors=True,
        expected={"detail": "protected"},
    )
```

Create the smallest related object that actually causes `ProtectedError` or
`DjangoValidationError`.

## Custom actions and parameter serializers

```python
def test_custom_action(self):
    self.make_request(
        self.get_action_url(),
        method="post",
        data={"value": 1},
        expected={"result": 2},
    )

def test_custom_action_invalid_params(self):
    self.make_request(
        self.get_action_url(),
        method="post",
        data={},
        status_code=status.HTTP_400_BAD_REQUEST,
        check_errors=True,
        expected={"value": ["required"]},
    )
```

For GET parameters, append a query string to the URL. Assert the action's public
response rather than the internal `validated_params` or `avalidated_params`
property.

## Lists with additional data

`ListWithAdditionalDataMixin` returns an object, not a one-element list. Assert
the complete external structure with `make_request()`:

```python
def test_list_with_additional_data(self):
    self.make_request(
        self.get_url(),
        expected={
            "results": [expected_entity(self.entity)],
            "meta": self.expected_meta,
        },
    )
```

## SQL query checks

First make the test pass with `num_queries=None`. Add a number only after
measuring it in the project's standard environment and confirming that it is an
intentional contract. Do not assert a query count in asynchronous tests: inside
an event loop the library deliberately ignores `num_queries` and emits a warning.
