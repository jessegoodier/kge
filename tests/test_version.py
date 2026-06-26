import tomllib
from pathlib import Path

import kge


def test_package_version_matches_pyproject() -> None:
    with (Path(__file__).resolve().parents[1] / "pyproject.toml").open("rb") as f:
        pyproject_version = tomllib.load(f)["project"]["version"]

    assert kge.__version__ == pyproject_version
