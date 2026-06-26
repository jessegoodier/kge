"""KGE - Kubernetes Get Events package."""

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

_DISTRIBUTION_NAME = "kge-kubectl-get-events"


def _read_pyproject_version() -> str:
    with (Path(__file__).resolve().parents[2] / "pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)
    return str(pyproject["project"]["version"])


try:
    __version__ = version(_DISTRIBUTION_NAME)
except PackageNotFoundError:
    __version__ = _read_pyproject_version()
