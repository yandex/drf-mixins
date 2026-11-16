---
name: yandex-drf-mixins-release
description: "Prepare and trigger an automated yandex-drf-mixins release with author-approved checkpoints by default. Use for release, publish, tag, and version-bump requests; an initial explicit no-checkpoints request can opt out of stage-by-stage approval, but publication still requires authorization."
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

## Execution mode and author checkpoints

Use **checkpoints by default**. Only an explicit request to run *without
checkpoints in the initial invocation* selects the uninterrupted mode. Do not
infer an opt-out from urgency, a release request, prior approvals, or silence;
do not switch modes partway through a run. State the chosen mode at the start.
The author is the person who requested this release, not the git commit author.

In checkpoint mode, read-only inspection may start immediately. Before each
next stage below, show the completed stage's result and ask the author for
explicit approval of that **named next stage**. Stop and wait for the reply;
the initial request to release, an approval for an earlier stage, and a GitHub
environment approval are not approval for a later checkpoint. If the author
changes the candidate, re-run affected checks and ask again against the new
evidence. A refusal or missing reply leaves the release paused, not failed.

| Stage | Work after approval | Evidence to report before asking for the next stage |
| --- | --- | --- |
| Preflight (read-only; no approval needed) | Inspect current versions, remote main, PyPI, tags, releases, existing PRs and one-time setup. | Current/target version and links to the exact repository revision, PyPI project and any existing PR or tag. Ask to prepare the candidate. |
| Candidate preparation | Update version declarations if needed; run quality checks, build/inspect artifacts and test the wheel on supported boundaries. Do not commit or push. | Results and limitations, candidate diff, absolute local links to the wheel, sdist and retained check logs, plus their hashes. Ask to publish the version-bump PR. |
| Pull request | Commit and push only the authorized release-candidate changes; open or reuse the version-bump PR and wait for required CI. Do not merge. | PR and Files changed links, exact head commit, direct CI run/check links and results. Ask to merge. |
| Merge | Merge without bypassing protection, fetch main and verify the merged version declarations. Do not push a tag. | Merged PR and exact merge-commit links, branch protection/CI outcome, plus the verified version. Ask to push the signed release tag. |
| Tag and automated publication | Recheck version availability and setup, create/push the matching signed tag on the verified merge commit, then monitor the workflow through PyPI and GitHub Release. | Immediately report the tag and workflow run links; after completion report the direct jobs, PyPI version, GitHub Release/assets and independent installation result. |

Every stage-completion report must say what was done, what remains unverified,
and provide direct links for the author to inspect **that stage's artifacts**.
Use exact GitHub/PyPI URLs for remote artifacts and absolute local file links
for pre-publication artifacts; retain local artifacts and logs across pauses.
Never substitute a generic repository page for an available PR, commit, check,
workflow, tag or release link. If an artifact has no durable URL yet, say so and
provide its local path and hash; if an expected artifact is missing, do not claim
the stage complete. On resumption, recheck mutable remote state before acting.
If a stage is already complete before invocation, verify and report its existing
artifacts rather than repeating the mutation, then ask at the next checkpoint.

Without checkpoints, run the same verification and report the same artifacts,
but do not pause for stage-by-stage approvals. This mode does not waive the
separate authorization for repository publication, merge, or release-tag push,
nor any one-time setup, branch protection or failure stop. A request to
"release <VERSION> without checkpoints" authorizes the release sequence; a
request only to prepare or inspect does not authorize publication.

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
In checkpoint mode, apply the stages above to the numbered procedures below:
sections 1 and the read-only parts of Input are preflight; sections 2–5 prepare
the candidate; section 6 contains separate PR and merge stages; sections 7–9
cover the tag and automated-publication stage. Section 7's report is the tag
approval checkpoint, not permission to proceed by itself.

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

Before running checks, create an evidence directory outside the repository
(for example with `mktemp -d /tmp/yandex-drf-mixins-release.XXXXXX`). Save the
candidate diff and each check's output and exit status there without exposing
secrets. Reuse its absolute path for the distributions below, report that path
at the checkpoint, and do not delete it while author review is pending. After
resuming, use the reported path rather than relying on a shell variable from a
previous session.

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
# Use the evidence directory created before the quality gate.
RELEASE_DIR="<ABSOLUTE_EVIDENCE_DIRECTORY>"
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

When `python3.10` and `python3.15` are available, install the wheel into clean
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
In checkpoint mode, stop between PR/CI completion and merge. Do not treat a
green CI run or the approval to open the PR as permission to merge.

## 7. Final checkpoint before publication

Report:

- the merged commit SHA;
- the target tag `v<VERSION>`;
- test, quality, build, and wheel-verification results;
- confirmation that PyPI, git tags, and GitHub Releases do not already contain
  the target version;
- confirmation that the PyPI Trusted Publisher and protected `pypi`
  environment are configured.

In checkpoint mode, ask for a fresh approval to push the exact tag on the exact
merged commit, even if the initial request was to release. Do not push the tag
unless publication has been explicitly authorized. The tag approval starts the
entire automated workflow; the skill cannot pause it between build, PyPI and
GitHub Release. Explain this consequence at the checkpoint.

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
python3.15 -m venv "$VERIFY_DIR/venv"
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
