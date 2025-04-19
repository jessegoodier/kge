"""Completion package for KGE."""

import os
import sys
from pathlib import Path


def get_completion_path() -> Path:
    """Get the path to the completion script."""
    return Path(__file__).parent / "_kge"


def install_completion() -> None:
    """Install the completion script to the user's completion directory."""
    completion_dir = Path.home() / ".zsh" / "completions"
    completion_dir.mkdir(parents=True, exist_ok=True)

    target = completion_dir / "_kge"
    source = get_completion_path()

    try:
        if target.exists():
            target.unlink()
        target.symlink_to(source)
        print(f"Completion script installed to {target}")
    except Exception as e:
        print(f"Error installing completion script: {e}", file=sys.stderr)
        sys.exit(1)
