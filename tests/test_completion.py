"""Tests for completion functionality."""

import os
import shutil
from pathlib import Path
import pytest
from kge.completion import install_completion, get_completion_path


@pytest.fixture
def completion_dir(tmp_path):
    """Create a temporary completion directory."""
    completion_dir = tmp_path / ".zsh" / "completions"
    completion_dir.mkdir(parents=True)
    return completion_dir


def test_get_completion_path():
    """Test that completion path is correctly determined."""
    path = get_completion_path()
    assert path.exists()
    assert path.name == "_kge"


def test_install_completion(completion_dir, monkeypatch):
    """Test installation of completion script."""
    # Mock home directory to use our temporary directory
    monkeypatch.setattr(Path, "home", lambda: completion_dir.parent.parent)

    # Install completion
    install_completion()

    # Check that symlink was created
    target = completion_dir / "_kge"
    assert target.exists()
    assert target.is_symlink()
    assert target.resolve() == get_completion_path()


def test_install_completion_existing_file(completion_dir, monkeypatch):
    """Test installation when a regular file already exists."""
    # Mock home directory
    monkeypatch.setattr(Path, "home", lambda: completion_dir.parent.parent)

    # Create existing file
    target = completion_dir / "_kge"
    target.touch()

    # Mock user input to replace file
    monkeypatch.setattr("builtins.input", lambda _: "y")

    # Install completion
    install_completion()

    # Check that symlink was created
    assert target.exists()
    assert target.is_symlink()
    assert target.resolve() == get_completion_path()


def test_install_completion_existing_symlink(completion_dir, monkeypatch):
    """Test installation when a symlink already exists."""
    # Mock home directory
    monkeypatch.setattr(Path, "home", lambda: completion_dir.parent.parent)

    # Create existing symlink
    target = completion_dir / "_kge"
    target.symlink_to(Path("/dev/null"))

    # Install completion
    install_completion()

    # Check that symlink was updated
    assert target.exists()
    assert target.is_symlink()
    assert target.resolve() == get_completion_path()