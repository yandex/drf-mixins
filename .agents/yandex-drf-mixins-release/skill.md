---
name: yandex-drf-mixins-release
description: "Prepare and publish a yandex-drf-mixins release through separate tag-CI and manually dispatched publication stages, with author-approved checkpoints by default. Use for release, publish, tag, and version-bump requests; an initial explicit no-checkpoints request can opt out of stage-by-stage approval, but publication still requires authorization."
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
argument-hint: "[new version, for example 0.2.0]"
---

# Release yandex-drf-mixins

Prepare a new `yandex-drf-mixins` version, validate its signed tag in CI, then
publish it through a separately dispatched GitHub Actions run in
`.github/workflows/release.yml`. GitHub Environments are unavailable on the
`yandex` organization's legacy Silver plan, so the author checkpoint between
tag CI and publication is mandatory in the default mode but is not a GitHub
environment approval.

## Release contract

The release flow is:

1. prepare and merge a version-bump pull request;
2. create and push the matching signed `v<version>` tag on the merged commit;
3. let the tag-triggered run test and build the source **without publishing**;
4. after a separate author approval, manually dispatch the workflow on that
   exact tag; it repeats the gates and builds before publishing to PyPI with
   OIDC Trusted Publishing;
5. create a GitHub Release only after the PyPI job succeeds.

Never run `python -m twine upload` locally and never read or create `.pypirc` or
long-lived PyPI credentials. Publication belongs exclusively to the CI publish
job. A tag push starts validation, not publication; only the separate manual
`workflow_dispatch` run may publish. Both the tag push and the dispatch require
their own authorization in checkpoint mode. Do not dispatch on a branch, an
unverified tag, or before the tag CI and artifact review have succeeded.

## Plan before execution

In the first response, before running the preflight commands, give the author
a concise ordered plan for this release. Name the target version (or mark it
unknown), the checkpoint mode, the stages below, the checks and reviewable
artifacts expected at each stage, and where author approval will be required.
The plan is not itself an approval. After reading the repository, update any
initially unknown version or already-completed stages in the plan.

Work through that plan in order. In each stage report, mark what is complete,
what remains, and which stage is next; link its evidence as specified below.
On resumption, identify the current stage before acting. If new facts require
a different version, scope, sequence, or validation, explain the reason and
publish a revised plan before deviating. Re-run affected checks and obtain a
fresh approval for any changed checkpoint; never rely on stale approval.
This planning and progress contract also applies when the author explicitly
selects the mode without checkpoints.

## Execution mode and author checkpoints

Use **checkpoints by default**. Only an explicit request to run *without
checkpoints in the initial invocation* selects the uninterrupted mode. Do not
infer an opt-out from urgency, a release request, prior approvals, or silence;
do not switch modes partway through a run. State the chosen mode at the start.
The author is the person who requested this release, not the git commit author.

In checkpoint mode, read-only inspection may start immediately. Before each
next stage below, show the completed stage's result and ask the author for
explicit approval of that **named next stage**. Stop and wait for the reply;
the initial request to release and an approval for an earlier stage are not
approval for a later checkpoint. If the author changes the candidate, re-run
affected checks and ask again against the new evidence. A refusal or missing
reply leaves the release paused, not failed.

| Stage | Work after approval | Evidence to report before asking for the next stage |
| --- | --- | --- |
| Preflight (read-only; no approval needed) | Inspect current versions, remote main, PyPI, tags, releases, existing PRs and one-time setup. | Current/target version and links to the exact repository revision, PyPI project and any existing PR or tag. Ask to prepare the candidate. |
| Candidate preparation | Update version declarations if needed; run quality checks, build/inspect artifacts and test the wheel on supported boundaries. Do not commit or push. | Results and limitations, candidate diff, absolute local links to the wheel, sdist and retained check logs, plus their hashes. Ask to publish the version-bump PR. |
| Pull request | Commit and push only the authorized release-candidate changes; open or reuse the version-bump PR and wait for required CI. Do not merge. | PR and Files changed links, exact head commit, direct CI run/check links and results. Ask to merge. |
| Merge | Merge without bypassing protection, fetch main and verify the merged version declarations. Do not push a tag. | Merged PR and exact merge-commit links, branch protection/CI outcome, plus the verified version. Ask to push the signed release tag for CI only. |
| Tag and CI | Recheck version availability and setup, create/push the matching signed tag on the verified merge commit, then wait for the tag-triggered compatibility and build jobs. Confirm PyPI and GitHub Release jobs were skipped. | Tag, exact commit, CI run and direct job links, results, build-artifact links and hashes. Ask for separate approval to dispatch publication on this exact tag. |
| Manual publication | Recheck the tag, commit, PyPI availability and publisher identity, then dispatch `release.yml` on the exact tag. Monitor the complete run. | Direct publication run/job links, PyPI version, GitHub Release/assets and independent installation result. |

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

- a PyPI Trusted Publisher for owner `yandex`, repository `drf-mixins`, and
  workflow `release.yml`, with its optional environment field **empty**;
- protection for the `v*` tag namespace so only release maintainers can create
  tags, with updates and deletions restricted;
- protection of `main` with required CI and an independent approving review
  for changes to the trusted release workflow. Review the effective branch
  protection before relying on it; an agent approval is not a substitute.

If these settings have not been confirmed, prepare the pull request and local
artifacts, but stop before pushing the tag and show the exact missing setup. On
the legacy Silver plan, do not treat `environment: pypi` in a workflow as a
protected environment. If tag protection is also unavailable, stop and ask for
a separately reviewed security design; do not silently drop this gate.
The existing PyPI publisher bound to environment `pypi` does not authorize the
environment-free job: add and confirm the new publisher before dispatch, then
remove the obsolete publisher after the transition is verified.

## Input

Read the target PEP 440 version from the request. If it is missing and cannot be
unambiguously inferred from an existing version-bump pull request, ask one
question and stop.

Read:

- `pyproject.toml` for the current version, dependencies, and quality commands;
- `src/yandex_drf_mixins/__init__.py` for `__version__`;
- `README.md` for the current verification and release workflow;
- `.github/workflows/release.yml` for the actual publication contract.

After reading the version declarations, report the current and target versions
and reconcile them with the initial plan. Keep the tag push in a separate
command so its tag-CI effect remains explicit and auditable.
In checkpoint mode, apply the stages above to the numbered procedures below:
sections 1 and the read-only parts of Input are preflight; sections 2–5 prepare
the candidate; section 6 contains separate PR and merge stages; section 7 is
the pre-tag checkpoint; section 8 is tag CI; sections 9–10 cover the separately
authorized manual-publication stage. A tag approval is not a publication
approval.

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

## 7. Final checkpoint before the tag

Report:

- the merged commit SHA;
- the target tag `v<VERSION>`;
- test, quality, build, and wheel-verification results;
- confirmation that PyPI, git tags, and GitHub Releases do not already contain
  the target version;
- confirmation that the PyPI Trusted Publisher matches owner `yandex`, repo
  `drf-mixins`, workflow `release.yml`, with **no environment**;
- effective `main` review/CI protection and `v*` tag-creation protection.

In checkpoint mode, ask for a fresh approval to push the exact tag on the exact
merged commit, even if the initial request was to release. The tag approval
starts **only** the tag CI; it does not authorize publication. Do not push a
tag while the old auto-publishing workflow is still active on its target commit.
Verify the merged workflow's `publish` job is guarded by
`github.event_name == 'workflow_dispatch'` before the push.

## 8. Push the tag and review the tag CI

Create the tag on the verified merged commit and push it as a separate action:

```bash
git tag -s "v<VERSION>" "<MERGED_SHA>" -m "Release <VERSION>"
git push origin "v<VERSION>"
```

If signed-tag support is unavailable, stop and ask the operator whether to use
an annotated tag; do not silently downgrade the release tag.

The tag starts `.github/workflows/release.yml` in validation-only mode. Wait
for the exact tag/commit's compatibility and build jobs to succeed, and verify
that its PyPI and GitHub Release jobs were **skipped**, not merely pending. Read
back the tag's dereferenced commit and collect the direct run/job URLs, retained
build-artifact links and distribution hashes. Do not dispatch publication on a
failed, cancelled, incomplete or different tag run.

If tag CI fails because the tagged source needs a code change, do not move or
recreate the published tag; prepare a reviewed fix and choose a new version/tag.
For an infrastructure-only failure, diagnose the direct job log and rerun the
same tag CI only when its outcome is known. Never use a failed tag CI as a
reason to upload locally.

In checkpoint mode, report the tag CI evidence and ask for a **new, separate**
approval to dispatch publication on the exact `v<VERSION>` tag. Stop here until
the author replies. Pushing the tag was not approval to publish.

## 9. Dispatch publication on the verified tag

Immediately before dispatch, recheck that the remote tag still dereferences to
the approved merge commit, its tag CI is green, PyPI and GitHub Release do not
already contain the version, and the environment-free PyPI Trusted Publisher
and repository protections are confirmed. A change in any of these facts
invalidates the prior approval: report it and ask again. Never dispatch on
`main` or a feature branch.

```bash
git ls-remote origin "refs/tags/v<VERSION>^{}"
gh workflow run release.yml --repo yandex/drf-mixins --ref "v<VERSION>"
```

The dispatch starts the complete gate-and-publication run. Match the resulting
run by event `workflow_dispatch`, exact tag ref, head commit and creation time;
capture its run ID and URL. If the dispatch response is lost, read back before
retrying so a second publication run is not started accidentally. The publish
job receives `id-token: write` only after compatibility and build succeed.
No long-lived token or local upload is allowed.

## 10. Monitor and verify the release

Wait for the complete **manual-dispatch** release run. On failure, report the
failed job and its direct URL. Check PyPI and GitHub Release for a partial
publication before any recovery; do not recreate the tag, reuse the version,
dispatch again blindly or publish manually.

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
- A Trusted Publishing failure can mean the owner, repo, workflow filename or
  optional environment claim does not match the environment-free PyPI record.
  Read the direct publish-job log and PyPI state; never add a long-lived token.
- A tag-triggered run must never reach PyPI. If it does, stop and report the
  workflow violation before any further tag or dispatch.
- If PyPI succeeds but GitHub Release creation fails, rerun only the failed
  GitHub Actions job or create the release from the existing tag and the exact
  workflow artifacts. Never republish the PyPI version.
