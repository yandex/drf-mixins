from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
CI_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"


def test_package_metadata_declares_the_supported_version_ranges() -> None:
    content = PYPROJECT_PATH.read_text()

    required_fragments = (
        'requires-python = ">=3.10,<3.16"',
        '"Django>=4.0,<6.2"',
        '"djangorestframework>=3.14,<3.19"',
        '"Programming Language :: Python :: 3.14"',
        '"Programming Language :: Python :: 3.15"',
    )
    for fragment in required_fragments:
        assert fragment in content


def test_ci_covers_the_new_runtime_boundaries() -> None:
    content = CI_PATH.read_text()

    required_fragments = (
        'python-version: "3.15"',
        'django: "~=6.1.0"',
        'drf: "~=3.18.0"',
        "adrf~=0.1.0",
        "Python 3.10 / Django 4.0 / DRF 3.14 (core)",
        "          - name: Python 3.10\n",
        "          - name: Python 3.11\n",
        "          - name: Python 3.12\n",
        "          - name: Python 3.13\n",
    )
    for fragment in required_fragments:
        assert fragment in content
