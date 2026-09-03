# Canonical LMS example

The `courses` directory contains a sanitized, single-language version of
the LMS `courses` application. It keeps the core course, block, module and
progress models, while infrastructure integrations and unrelated reference
models are omitted. The historical LMS migrations are replaced with one
`0001_initial.py` describing the final example schema.

## Running the copied tests

Prepare an LMS checkout using its `setup-local-lms` skill. Then run the tests
from the root of this repository:

```bash
LMS_ROOT=/absolute/path/to/lms
PYTHONPATH="$(pwd)/src:$(pwd)/examples:$(pwd)/examples/lms:$LMS_ROOT" \
DJANGO_SETTINGS_MODULE=example_settings \
"$LMS_ROOT/venv/bin/python" -m pytest -n=10 -vvv \
    --nomigrations \
    examples/courses/tests
```

`example_settings.py` enables only the LMS applications referenced by the
remaining models. Their historical migrations are disabled for the isolated
test run; the example's own `0001_initial.py` is checked separately with
`makemigrations --check --dry-run`.
