---
name: yandex-drf-mixins-release
description: "Prepare and trigger an automated yandex-drf-mixins release. Use this skill for release, publish, tag, and version-bump requests. It updates and verifies the version, builds and tests artifacts, creates a version-bump PR, and triggers the protected tag-to-PyPI-to-GitHub-Release workflow after explicit authorization."
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
argument-hint: "[new version, for example 0.2.0]"
---

# Release yandex-drf-mixins

Prepare a new `yandex-drf-mixins` version and publish it through the protected
GitHub Actions workflow in `.github/workflows/release.yml`.

## Release contract

The release flow is:

1. prepare and merge a version-bump pull request;
2. create and push the matching `v<version>` tag on the merged commit;
3. let GitHub Actions test and build the tagged source;
4. publish the distributions to PyPI with OIDC Trusted Publishing;
5. create a GitHub Release only after the PyPI job succeeds.

Never run `python -m twine upload` locally and never read or create `.pypirc` or
long-lived PyPI credentials. Publication belongs exclusively to the protected
CI job. Pushing the release tag irreversibly starts publication, so do it only
when the operator explicitly requests a release or explicitly approves the tag.

## One-time setup prerequisite

Before the first automated release, the operator must configure:

- a PyPI Trusted Publisher for owner `yandex`, repository `drf-mixins`,
  workflow `release.yml`, and environment `pypi`;
- a protected GitHub environment named `pypi`, preferably with a required
  reviewer and deployment restricted to release tags;
- protection for the `v*` tag namespace so only release maintainers can create
  tags.

If these settings have not been confirmed, prepare the pull request and local
artifacts, but stop before pushing the tag and show the exact missing setup.

## Input

Read the target PEP 440 version from the request. If it is missing and cannot be
unambiguously inferred from an existing version-bump pull request, ask one
question and stop.

Read:

- `pyproject.toml` for the current version, dependencies, and quality commands;
- `src/yandex_drf_mixins/__init__.py` for `__version__`;
- `README.md` for the current verification and release workflow;
- `.github/workflows/release.yml` for the actual publication contract.

At the start, report the current and target versions. Keep the tag push in a
separate command so its publication effect remains explicit and auditable.

## 1. Confirm that the version is available

```bash
python -m pip index versions \
  --index-url https://pypi.org/simple/ \
  yandex-drf-mixins
git ls-remote --tags origin "refs/tags/v<VERSION>"
gh release view "v<VERSION>" --repo yandex/drf-mixins
```

The target version, tag, and GitHub Release must all be absent. Stop if any of
them already exists. Never retry a partially failed publication blindly.

## 2. Update the version

Update both declarations with the regular editing tool:

- `pyproject.toml`: `version = "<VERSION>"`;
- `src/yandex_drf_mixins/__init__.py`: `__version__ = "<VERSION>"`.

```bash
rg '^(version =|__version__ =)' \
  pyproject.toml src/yandex_drf_mixins/__init__.py
git diff -- pyproject.toml src/yandex_drf_mixins/__init__.py
```

Both files must contain exactly the target version.

## 3. Run the quality gate

```bash
python -m pytest
python -m black --check src tests
python -m isort --check-only src tests
python -m flake8 src tests
python -m mypy --explicit-package-bases src/yandex_drf_mixins
PYTHONPATH=.:src python -m pylint src/yandex_drf_mixins
python -m bandit -q -r src
```

Stop on any failure.

## 4. Build and inspect isolated artifacts

```bash
RELEASE_DIR="$(mktemp -d /tmp/yandex-drf-mixins-release.XXXXXX)"
python -m build --outdir "$RELEASE_DIR"
python -m twine check \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>-py3-none-any.whl" \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>.tar.gz"
python -m zipfile -l \
  "$RELEASE_DIR/yandex_drf_mixins-<VERSION>-py3-none-any.whl"
```

The wheel must contain `yandex_drf_mixins/py.typed`, the `drf`, `adrf`, and
`testing` namespaces, and the internal `base` package. It must not contain the
old `drf_mixins` package.

## 5. Test the wheel on the supported range boundaries

When `python3.10` and `python3.13` are available, install the wheel into clean
virtual environments and run the test suite exactly as documented in README.
If either interpreter is unavailable, report the untested boundary and do not
call the release fully verified.

## 6. Create and merge the version-bump pull request

The release pull request must contain only the version declarations and any
explicitly requested release notes. Commit, push, and create the pull request
only when the request authorizes repository publication. Wait for required CI
and merge without bypassing branch protection.

After merge, fetch `origin/main`, identify the exact merged commit, and verify
that both version declarations on that commit still match `<VERSION>`.

## 7. Final checkpoint before publication

Report:

- the merged commit SHA;
- the target tag `v<VERSION>`;
- test, quality, build, and wheel-verification results;
- confirmation that PyPI, git tags, and GitHub Releases do not already contain
  the target version;
- confirmation that the PyPI Trusted Publisher and protected `pypi`
  environment are configured.

Do not push the tag unless publication has been explicitly authorized.

## 8. Trigger the automated release

Create the tag on the verified merged commit and push it as a separate action:

```bash
git tag -s "v<VERSION>" "<MERGED_SHA>" -m "Release <VERSION>"
git push origin "v<VERSION>"
```

If signed-tag support is unavailable, stop and ask the operator whether to use
an annotated tag; do not silently downgrade the release tag.

The tag starts `.github/workflows/release.yml`. Do not upload artifacts through
another path while the workflow is running.

## 9. Monitor and verify the release

Wait for the complete release workflow. On failure, report the failed job and
its direct URL. Do not recreate the tag, reuse the version, or publish manually.

After success, independently verify:

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

gh release view "v<VERSION>" \
  --repo yandex/drf-mixins \
  --json tagName,url,isDraft,isPrerelease,assets
```

The installed package must print the exact target version, and the GitHub
Release must be published with both the wheel and source distribution attached.

## Failure handling

- A PyPI conflict means the version is already reserved; never overwrite it.
- A Trusted Publishing failure means the PyPI publisher identity, workflow
  filename, or GitHub environment does not match the configured trust policy.
- If PyPI succeeds but GitHub Release creation fails, rerun only the failed
  GitHub Actions job or create the release from the existing tag and the exact
  workflow artifacts. Never republish the PyPI version.
