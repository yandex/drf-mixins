from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
SKILL_PATH = PROJECT_ROOT / ".agents/yandex-drf-mixins-release/skill.md"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/release.yml"


def test_release_skill_delegates_publication_to_ci() -> None:
    content = SKILL_PATH.read_text()

    assert "allowed-tools: Bash, Read, Glob, Grep, Edit, Write" in content
    assert "never run `python -m twine upload`" in content.lower()
    assert ".github/workflows/release.yml" in content
    assert "pushing the release tag irreversibly starts publication" in content.lower()


def test_release_skill_covers_the_operator_workflow() -> None:
    content = SKILL_PATH.read_text()

    required_fragments = (
        "python -m pytest",
        "python -m build",
        "python -m twine check",
        'git push origin "v<VERSION>"',
        "pypi.org/simple/",
        "pyproject.toml",
        "__version__",
        "python3.15",
    )
    for fragment in required_fragments:
        assert fragment in content


def test_release_workflow_publishes_pypi_before_github_release() -> None:
    content = WORKFLOW_PATH.read_text()

    required_fragments = (
        'tags:\n      - "v*.*.*"',
        "environment:\n      name: pypi",
        "id-token: write",
        "pypa/gh-action-pypi-publish@release/v1",
        "needs: publish",
        'gh release create "$GITHUB_REF_NAME"',
        "--verify-tag",
    )
    for fragment in required_fragments:
        assert fragment in content

    assert "python -m twine upload" not in content
    assert content.index("pypa/gh-action-pypi-publish@release/v1") < content.index("gh release create")


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
