---
name: yandex-drf-mixins-api-tests
description: "Generate and run complete API tests for an existing DRF ModelViewSet using UrlNameMixin and GenericRequestMixin from yandex-drf-mixins. Use this skill whenever a user asks to cover a viewset, endpoint, CRUD API, filters, pagination, action-specific serializers, upsert, or protected deletion with tests based on the canonical courses examples."
compatibility: "Django REST Framework, ADRF, and yandex-drf-mixins; requires the project's configured test environment."
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
argument-hint: "path/to/views.py:ModelViewSet --output path/to/tests"
user-invocable: true
---

# Generate ModelViewSet API tests

Create executable API tests for the public contract of an existing
`ModelViewSet`. Use the `yandex-drf-mixins` testing helpers so that each concise
scenario checks the URL, HTTP status, JSON response, error codes, and, when
reliable, SQL query count.

User request: `$ARGUMENTS`

## Input and output

Accept two required arguments:

1. A viewset reference in one of these formats:
   - `path/to/views.py:CourseViewSet`, which is preferred and unambiguous;
   - `package.views.CourseViewSet`, a Python dotted path.
2. `--output path/to/tests`, the directory for generated test modules.

Example:

```text
/yandex-drf-mixins-api-tests courses/views.py:CourseViewSet --output courses/tests/api
```

If the class or `--output` is missing, ask one short question and do not write
files. Resolve relative paths from the current project root and accept absolute
paths. Create the destination directory when necessary.

Write one or more `test_*.py` files only inside the requested directory. Do not
modify viewsets, serializers, models, routers, settings, or other production
code. If the endpoint itself is broken, report the problem instead of adapting
production code to make the generated tests pass.

## Canonical sources

Before designing tests, read completely:

- `references/test-patterns.md` next to this file;
- `examples/courses/tests/` from the `yandex-drf-mixins` repository when it is
  available next to the skill;
- the implementation of `GenericRequestMixin` in the installed or local package
  when its signature may differ from the reference.

The courses tests define style and useful scenarios, but they are not templates
for blind copying. Transfer only behavior that the target viewset actually has.

## 1. Analyze the endpoint

Read all related project code first:

- the class, its parents, and overridden methods;
- `queryset`, model, `lookup_field`, and `http_method_names`;
- `serializer_class`, `serializer_classes`, and per-action serializers;
- router/URL patterns, namespaces, and basename;
- permissions, authentication, and existing test authentication helpers;
- pagination, filter backends, `filterset_fields`, search, and ordering;
- `@action` methods, parameter serializers, and additional list response data;
- factories, fixtures, and neighboring API tests;
- model constraints and serializer validators with stable error codes.

Do not import the application for introspection before Django is configured.
Static inspection is usually sufficient. Use runtime introspection only through
the project's configured shell or test command.

Resolve the actual basename from the router. Do not infer it only from the class
name: explicit `basename=` and namespaces take precedence.

## 2. Build the scenario matrix

Cover every detected public behavior, not internal calls. A full CRUD viewset
normally requires:

- named list and detail URLs;
- list with the full JSON contract and expected order;
- detail with the full JSON contract;
- create plus resulting database state;
- at least one create or update validation error with `check_errors=True`;
- PUT and PATCH plus resulting database state;
- DELETE plus object absence;
- a missing-object 404 when it is a meaningful contract branch.

Add scenarios only when supported by the viewset:

- action-specific serializers: check the actual response serializer;
- filters/search/ordering: test each parameter and safe empty values separately;
- pagination: default page, limit, offset, empty page, and `all=true` for
  `LimitOffsetAllPagination`;
- update-or-create: both branches with their different status codes;
- protected deletion: the stable error code;
- parameter serializers: valid parameters and invalid parameter error codes;
- additional list data: the complete external response object;
- custom actions: a positive and at least one relevant negative scenario;
- permissions: allowed and denied requests using the project's authentication
  conventions.

Do not add a CRUD action disabled by `http_method_names`, a missing mixin, or an
explicit implementation. Never invent filters, permissions, errors, or fixtures.

## 3. Write the tests

Use the native Django or DRF test case already adopted by the project. The
default synchronous form is:

```python
class CourseApiTestCase(UrlNameMixin, GenericRequestMixin, APITestCase):
    URL_NAME = "course-list"
```

Follow these rules:

- put `UrlNameMixin` and `GenericRequestMixin` before the test case class;
- create shared data with `setUpTestData()` or existing factories;
- place full expected JSON builders in domain functions named
  `expected_<entity>()` outside the test case;
- use the matching `GenericRequestMixin` helper for list, detail, create, update,
  patch, and delete, and `make_request()` for custom methods;
- check errors with `check_errors=True` and stable `ErrorDetail.code` values, not
  localized message text;
- after mutating requests, assert meaningful database state separately;
- pass `pagination=False` explicitly for unpaginated lists;
- use `only_ids=True` for focused filter assertions, but keep at least one base
  list/detail test that checks the full JSON response;
- use `check_order=False` only when the endpoint does not guarantee ordering;
- do not mock the ORM, serializer, or viewset in an API test;
- do not copy sensitive production data into fixtures.

Start with `num_queries=None`. Add an explicit query count only after a successful
local run when the value is stable and the project intentionally treats it as a
budget. Keep it `None` for asynchronous endpoints because the library ignores an
explicit count inside an event loop and emits `RuntimeWarning`.

For asynchronous endpoints, preserve the same public contract assertions and use
the project's established async test case/client. Do not make a test asynchronous
only because the viewset inherits `ABaseModelViewSet`; first inspect how ADRF
endpoints are tested in that project.

## 4. Run the TDD cycle

1. Write tests to the destination directory.
2. Run only the new test module with the project's standard command.
3. Correct test data, expected JSON, URLs, and contract assumptions.
4. Do not modify production code without a separate user request.
5. After the focused run passes, run the full destination test directory.
6. Run the formatter, import sorter, linter, and type checker used by the project,
   limited to new files when supported.

If the test command cannot be determined from README, `pyproject.toml`, `Pipfile`,
`Makefile`, `tox.ini`, CI, or neighboring commands, ask the user instead of
inventing a new environment.

## 5. Quality checklist

Before finishing, verify that:

- every HTTP call uses `GenericRequestMixin` unless the helper genuinely does
  not support the required transport;
- errors use `check_errors=True`;
- at least one complete JSON contract is checked, rather than IDs only;
- tests do not depend on translated error text or accidental ordering;
- fixtures are minimal and endpoint-specific;
- all new files are inside `--output`;
- focused tests and project checks pass.

In the final response, list created files, covered scenarios, and exact commands
with results. Separately identify any viewset behavior that could not be covered
and explain why.
