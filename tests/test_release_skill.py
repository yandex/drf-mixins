from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
SKILL_PATH = PROJECT_ROOT / ".agents/yandex-drf-mixins-release/skill.md"


def test_release_skill_automates_everything_except_upload() -> None:
    content = SKILL_PATH.read_text()

    assert "allowed-tools: Bash, Read, Glob, Grep, Edit, Write" in content
    assert "perform steps 1–7 automatically" in content.lower()
    assert "do not run `python -m twine upload`" in content.lower()
    assert "perform step 9 automatically" in content.lower()


def test_release_skill_covers_the_operator_workflow() -> None:
    content = SKILL_PATH.read_text()

    required_fragments = (
        "python -m pytest",
        "python -m build",
        "python -m twine check",
        "python -m twine upload --repository pypi",
        "pypi.org/simple/",
        "pyproject.toml",
        "__version__",
    )
    for fragment in required_fragments:
        assert fragment in content
