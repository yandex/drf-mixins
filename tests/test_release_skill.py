import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
SKILL_PATH = PROJECT_ROOT / ".agents/yandex-drf-mixins-release/skill.md"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/release.yml"
CI_WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"


def test_release_skill_delegates_publication_to_ci() -> None:
    content = SKILL_PATH.read_text()

    assert "allowed-tools: Bash, Read, Glob, Grep, Edit, Write" in content
    assert "never run `python -m twine upload`" in content.lower()
    assert ".github/workflows/release.yml" in content
    assert "a tag push starts validation, not publication" in content.lower()
    assert "only the separate manual" in content.lower()
    assert "`workflow_dispatch` run may publish" in content


def test_release_skill_covers_the_operator_workflow() -> None:
    content = SKILL_PATH.read_text()

    required_fragments = (
        "python -m pytest",
        "python -m build",
        "python -m twine check",
        'git push origin "v<VERSION>"',
        'gh workflow run release.yml --repo yandex/drf-mixins --ref "v<VERSION>"',
        "pypi.org/simple/",
        "pyproject.toml",
        "__version__",
        "python3.15",
    )
    for fragment in required_fragments:
        assert fragment in content


def test_release_skill_requires_author_checkpoints_by_default() -> None:
    content = SKILL_PATH.read_text()
    normalized = " ".join(content.split())

    assert "checkpoints by default" in content.lower()
    assert "without checkpoints in the initial invocation" in normalized
    assert "Stop and wait for the reply" in content
    assert "initial request to release" in content
    assert "stage-completion report" in content
    assert "absolute local file links" in content
    assert "direct CI run/check links" in content
    assert "Pushing the tag was not approval to publish" in content
    assert "the tag-triggered run test and build the source **without publishing**" in content

    stages = (
        "| Preflight (read-only; no approval needed) |",
        "| Candidate preparation |",
        "| Pull request |",
        "| Merge |",
        "| Tag and CI |",
        "| Manual publication |",
    )
    positions = [content.index(stage) for stage in stages]
    assert positions == sorted(positions)


def test_release_skill_starts_with_a_plan_and_tracks_deviations() -> None:
    content = SKILL_PATH.read_text()
    plan = content.split("## Plan before execution", 1)[1].split("## Execution mode", 1)[0]

    assert content.index("## Plan before execution") < content.index("## Execution mode and author checkpoints")
    assert "first response, before running the preflight commands" in plan
    assert "target version" in plan
    assert "checkpoint mode" in plan
    assert "checks and reviewable" in plan
    assert "mark what is complete" in plan
    assert "publish a revised plan before deviating" in plan
    assert "also applies when the author explicitly" in plan


def test_release_workflow_publishes_pypi_before_github_release() -> None:
    content = WORKFLOW_PATH.read_text()
    publish_job = content.split("\n  publish:\n", 1)[1].split("\n  github-release:\n", 1)[0]

    required_fragments = (
        'tags:\n      - "v*.*.*"',
        "workflow_dispatch:",
        "verify-ref:",
        "needs: verify-ref",
        "pypa/gh-action-pypi-publish@release/v1",
        "needs: publish",
        'gh release create "$GITHUB_REF_NAME"',
        "--verify-tag",
    )
    for fragment in required_fragments:
        assert fragment in content

    assert "if: github.event_name == 'workflow_dispatch' && github.ref_type == 'tag'" in publish_job
    assert "needs.compatibility.result == 'success'" in publish_job
    assert "needs.build.result == 'success'" in publish_job
    assert "id-token: write" in publish_job
    assert "environment:" not in publish_job
    assert content.count("id-token: write") == 1
    assert "python -m twine upload" not in content
    assert content.index("pypa/gh-action-pypi-publish@release/v1") < content.index("gh release create")


def test_github_release_job_checks_out_repository_before_gh_cli() -> None:
    content = WORKFLOW_PATH.read_text()
    release_job = content.split("\n  github-release:\n", 1)[1]

    checkout = re.search(r"- uses: actions/checkout@v\d+", release_job)
    download = re.search(r"- uses: actions/download-artifact@v\d+", release_job)

    assert checkout is not None
    assert download is not None
    assert checkout.start() < download.start() < release_job.index('gh release create "$GITHUB_REF_NAME"')


def test_ci_checks_release_artifact_transfer_with_matching_action_versions() -> None:
    release_content = WORKFLOW_PATH.read_text()
    ci_content = CI_WORKFLOW_PATH.read_text()

    for action in ("upload-artifact", "download-artifact"):
        pattern = rf"- uses: actions/{action}@(v\d+)"
        release_versions = set(re.findall(pattern, release_content))
        ci_versions = set(re.findall(pattern, ci_content))

        assert len(release_versions) == 1
        assert ci_versions == release_versions

    assert "sha256sum dist/*.whl dist/*.tar.gz > dist/SHA256SUMS" in ci_content
    assert "sha256sum -c dist/SHA256SUMS" in ci_content


def test_release_skill_preserves_separate_tag_and_publication_approvals() -> None:
    content = SKILL_PATH.read_text()

    assert "ask for a fresh approval to push the exact tag" in content
    assert "The tag approval" in content
    assert "does not authorize publication" in content
    assert "ask for a **new, separate**" in content
    assert "approval to dispatch publication" in content
    assert "optional environment field **empty**" in content
    assert "If tag protection is also unavailable, stop" in content


def test_release_workflow_checks_ref_before_any_publishable_work() -> None:
    content = WORKFLOW_PATH.read_text()
    verify_job = content.split("\n  verify-ref:\n", 1)[1].split("\n  compatibility:\n", 1)[0]
    build_job = content.split("\n  build:\n", 1)[1].split("\n  publish:\n", 1)[0]

    assert '"$GITHUB_REF_TYPE" != tag' in verify_job
    assert '"$GITHUB_REF_NAME" != v*.*.*' in verify_job
    assert 'git rev-list -n 1 "refs/tags/${GITHUB_REF_NAME}"' in build_job
    assert 'main_commit="$(git rev-parse FETCH_HEAD)"' in build_job
    assert build_job.index('main_commit="$(git rev-parse FETCH_HEAD)"') < build_job.index(
        'git fetch --force origin "refs/tags/${GITHUB_REF_NAME}:refs/tags/${GITHUB_REF_NAME}"'
    )
    assert 'git merge-base --is-ancestor "$GITHUB_SHA" "$main_commit"' in build_job


def test_release_workflow_covers_supported_runtime_boundaries() -> None:
    content = WORKFLOW_PATH.read_text()

    required_fragments = (
        "Python 3.10 / Django 4.0 / DRF 3.14 (core)",
        "Python 3.10 / Django 4.1 / DRF 3.14 / ADRF 0.1.7",
        "Python 3.15 / Django 6.1 / DRF 3.18 / ADRF latest",
        'python-version: "3.14"',
        'django: "~=6.1.0"',
        'drf: "~=3.18.0"',
        "adrf~=0.1.0",
        "needs:\n      - compatibility\n      - build",
    )
    for fragment in required_fragments:
        assert fragment in content
