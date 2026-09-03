---
name: yandex-drf-mixins-release
description: "Prepare and publish a new yandex-drf-mixins version to PyPI. Use this skill for release, publish, upload, and version-bump requests. It updates the version, runs the quality gate, builds and verifies artifacts automatically; the irreversible twine upload is always left to the operator."
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
argument-hint: "[new version, for example 0.2.0]"
---

# Release yandex-drf-mixins

Prepare a new `yandex-drf-mixins` version for the public PyPI. Automate
all reversible work and stop before publication.

## Responsibility boundary

- Perform steps 1–7 automatically: verify the environment and index, update the
  version, run the quality gate, then build and inspect the artifacts.
- Do not run `python -m twine upload` under any circumstances, including after
  the operator says to continue or grants permissions.
- Stop at step 8, show the operator the single publication command, and wait for
  them to run it manually and report the result.
- After the operator reports a successful upload, perform step 9 automatically.
- Never open or read `~/.pypirc`, access keys, secret keys, or other credentials.

Only upload requires manual control because it irreversibly reserves the version
number. All prior work is reproducible and must be completed by the agent.

## Input

Resolve the library root relative to this skill. Read the target PEP 440 version
from the arguments. If it is missing, ask one question and stop.

Read:

- `pyproject.toml` for the current version, dependencies, and quality commands;
- `src/yandex_drf_mixins/__init__.py` for `__version__`;
- `README.md` for the current local verification workflow.

Do not assume that the version is already updated. Use the absolute project root
and substitute the concrete target version for every `<VERSION>` placeholder.

At the start, report the current and target versions. During steps 1–7, provide
short progress updates and stop on any failure. Keep upload separate from all
other commands so it remains an explicit operator action.

## 1. Verify the environment and access

Run:

```bash
cd <ABSOLUTE_PROJECT_ROOT>
git status --short
python --version
python -m pip --version
python -m twine --version
test -s ~/.pypirc && echo '.pypirc exists' || echo '.pypirc is missing'
```

Verify or explain to the operator when needed:

- the package name is `yandex-drf-mixins`;
- API tokens are issued at `https://pypi.org/manage/account/token/`;
- the `pypi` section in `~/.pypirc` must point to
  `https://upload.pypi.org/legacy/`;
- protect the file with `chmod 400 ~/.pypirc`;
- never paste `.pypirc` contents into chat or print them in the terminal.

Install twine when it is unavailable:

```bash
python -m pip install 'twine>=5,<8'
```

## 2. Confirm that the version is absent from PyPI

```bash
python -m pip index versions \
  --index-url https://pypi.org/simple/ \
  yandex-drf-mixins
```

Stop if the target version already exists. Upload error `400 BAD REQUEST` usually
means that the version is already reserved.

## 3. Update the version

Update `pyproject.toml` and `src/yandex_drf_mixins/__init__.py` with the regular
editing tool. Do not modify them if both already contain the target version.

```bash
cd <ABSOLUTE_PROJECT_ROOT>
rg '^(version =|__version__ =)' pyproject.toml src/yandex_drf_mixins/__init__.py
git diff -- pyproject.toml src/yandex_drf_mixins/__init__.py
```

Both files must contain the same version.

## 4. Run the quality gate

```bash
python -m pytest
python -m black --check src tests
python -m isort --check-only src tests
python -m flake8 src tests
python -m mypy --explicit-package-bases src/yandex_drf_mixins
PYTHONPATH=.:src python -m pylint src/yandex_drf_mixins
python -m bandit -q -r src
```

Stop on any failure and do not proceed to the build.

## 5. Build and inspect isolated artifacts

Substitute the target version into the filenames:

```bash
RELEASE_DIR="$(mktemp -d /tmp/yandex-drf-mixins-release.XXXXXX)"
python -m build --outdir "$RELEASE_DIR"
python -m twine check \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>-py3-none-any.whl" \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>.tar.gz"
python -m zipfile -l "$RELEASE_DIR/yandex_drf_mixins-<VERSION>-py3-none-any.whl"
```

The wheel must contain `yandex_drf_mixins/py.typed`, the `drf`, `adrf`, and
`testing` namespaces, and the internal `base` package. It must not contain the
old `drf_mixins` package.

## 6. Test the wheel on minimum and maximum Python versions

When `python3.10` and `python3.13` are available, run:

```bash
python3.10 -m venv "$RELEASE_DIR/py310"
"$RELEASE_DIR/py310/bin/pip" install \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>-py3-none-any.whl" pytest pytest-django
PYTHONPATH=. DJANGO_SETTINGS_MODULE=tests.settings \
  "$RELEASE_DIR/py310/bin/python" -m pytest -q

python3.13 -m venv "$RELEASE_DIR/py313"
"$RELEASE_DIR/py313/bin/pip" install \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>-py3-none-any.whl[adrf]" \
  pytest pytest-django
PYTHONPATH=. DJANGO_SETTINGS_MODULE=tests.settings \
  "$RELEASE_DIR/py313/bin/python" -m pytest -q
```

If either interpreter is unavailable, explicitly report the untested part of the
range and do not call the release fully verified.

## 7. Show the final operator checkpoint

Before upload, report:

- absolute paths to both artifacts;
- test and linter results;
- confirmation that both version declarations match;
- wheel verification results on Python 3.10 and 3.13;
- `git status --short` and release-related changes;
- a warning that the next command irreversibly reserves the version number.

Do not continue to upload automatically. Preparation and verification must be
complete at this point, not left for the operator.

## 8. Publication command for the operator

Show this command as the final standalone shell block:

```bash
python -m twine upload --repository pypi \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>-py3-none-any.whl" \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>.tar.gz"
```

Do not run it. End the turn and wait for the operator's result.

## 9. Verify the published release automatically

After the operator reports success, run:

```bash
python -m pip index versions \
  --index-url https://pypi.org/simple/ \
  yandex-drf-mixins

VERIFY_DIR="$(mktemp -d /tmp/yandex-drf-mixins-verify.XXXXXX)"
python3.13 -m venv "$VERIFY_DIR/venv"
"$VERIFY_DIR/venv/bin/pip" install \
  --index-url https://pypi.org/simple/ \
  'yandex-drf-mixins[adrf]==<VERSION>'
"$VERIFY_DIR/venv/bin/python" -c \
  'import yandex_drf_mixins; print(yandex_drf_mixins.__version__)'
```

The final command must print the exact target version.

## Upload failures

- `400 BAD REQUEST`: the version already exists; choose a new version.
- `401 UNAUTHORIZED`: verify credentials in `.pypirc` without displaying them.
- `403 FORBIDDEN`: verify that the API token is allowed to publish this project
  and that the account is an owner or maintainer of the package.

After a failure, never retry blindly. First ask the operator to verify whether
the version appeared in the index.
