"""Completion package for KGE."""

import sys
from pathlib import Path


def get_completion_path() -> Path:
    """Get the path to the completion script."""
    return Path(__file__).parent / "_kge"


# TODO: Add support for other shells
# TODO: fix zsh completion
def install_completion() -> None:
    """Install the completion script to the user's completion directory."""
    completion_dir = Path.home() / ".zsh" / "completions"
    completion_dir.mkdir(parents=True, exist_ok=True)

    target = completion_dir / "_kge"
    source = get_completion_path()

    try:
        if target.exists():
            if target.is_symlink():
                print(f"Removing existing symlink at {target}")
                target.unlink()
            elif target.is_file():
                print(f"Regular file exists at {target}")
                response = input("Do you want to replace it? (y/N): ").strip().lower()
                if response != "y":
                    print("Installation cancelled.")
                    sys.exit(0)
                print(f"Removing existing file at {target}")
                target.unlink()
            else:
                print(f"Unexpected file type at {target}")
                response = input("Do you want to replace it? (y/N): ").strip().lower()
                if response != "y":
                    print("Installation cancelled.")
                    sys.exit(0)
                print(f"Removing existing file at {target}")
                target.unlink()

        # Ensure the target is completely removed before creating symlink
        if target.exists():
            target.unlink()

        print(f"Creating symlink from {source} to {target}")
        target.symlink_to(source)
        print(f"Completion script installed to {target}")
    except Exception as e:
        print(f"Error installing completion script: {e}", file=sys.stderr)
        print(f"Source path: {source}", file=sys.stderr)
        print(f"Target path: {target}", file=sys.stderr)
        print(f"Source exists: {source.exists()}", file=sys.stderr)
        print(f"Target exists: {target.exists()}", file=sys.stderr)
        if target.exists():
            print(f"Target is symlink: {target.is_symlink()}", file=sys.stderr)
            print(f"Target is file: {target.is_file()}", file=sys.stderr)
        sys.exit(1)
