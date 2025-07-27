#! /usr/bin/env python3
import argparse
import re
import subprocess

import requests


def find_github_version():
    # Get latest release version from GitHub
    release_command = [
        "gh",
        "release",
        "list",
        "--json",
        "name",
        "--jq",
        ".[0].name",
    ]
    try:
        latest_release = subprocess.check_output(release_command, text=True).strip()
        if latest_release:
            latest_version = latest_release.lstrip("v")  # Remove 'v' prefix
            return latest_version
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def find_pypi_version(github_version):
    try:
        # Get latest version from PyPI
        # https://pypi.org/pypi/kge-kubectl-get-events/json
        pypi_url = "https://pypi.org/pypi/kge-kubectl-get-events/json"
        pypi_response = requests.get(pypi_url)
        pypi_json = pypi_response.json()
        if pypi_json:
            pypi_version = pypi_json["info"]["version"]
            if pypi_version == github_version:
                return True
            else:
                return False
    except Exception as e:
        print(f"Error in find_pypi_version: {e}")
        return False


def check_version_match(version):
    try:
        # Check pyproject.toml
        with open("pyproject.toml", "r") as f:
            pyproject_content = f.read()
        if "version = " not in pyproject_content:
            print("Error: 'version = ' not found in pyproject.toml")
            exit(1)
        else:
            print("pyproject.toml version: ", pyproject_content)
            pyproject_version = re.search(r'version = "(.+)"', pyproject_content).group(
                1
            )
        # Check __init__.py
        with open("src/kge/__init__.py", "r") as f:
            init_content = f.read()
        if "__version__ = " not in init_content:
            print("Error: '__version__ = ' not found in __init__.py")
            exit(1)
        else:
            print("__init__.py version: ", init_content)
            init_version = re.search(r'__version__ = "(.+)"', init_content).group(1)
        if version != pyproject_version or version != init_version:
            print("Error: Version mismatch between pyproject.toml and __init__.py")
            print(f"pyproject.toml: {pyproject_version}")
            print(f"__init__.py: {init_version}")
            exit(1)
        print(
            f"Versions match: pyproject.toml = {pyproject_version}, __init__.py = {init_version}"
        )
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def create_release(version, commit):
    try:
        # Check if version is already released
        check_for_duplicate_release = [
            "gh",
            "release",
            "list",
            "--json",
            "name",
            "--jq",
            ".[].name",
        ]
        release_list = subprocess.check_output(
            check_for_duplicate_release, text=True
        ).splitlines()
        if f"v{version}" in release_list:
            print(f"Error: Version {version} is already released")
            exit(1)

        if commit:
            # commit the changes
            git_add = subprocess.run(
                ["git", "add", "pyproject.toml", "src/kge/__init__.py"], check=True
            )
            if git_add.returncode != 0:
                print("Error: Failed to add changes to git")
                exit(1)
            git_commit = subprocess.run(
                ["git", "commit", "-m", f"Bump version to {version}"], check=True
            )
            if git_commit.returncode != 0:
                print("Error: Failed to commit changes to git")
                exit(1)
            git_push = subprocess.run(["git", "push"], check=True)
            if git_push.returncode != 0:
                print("Error: Failed to push changes to git")
                exit(1)
            # Check version match
            check_version_match(version)
            # Create release
            release_command = [
                "gh",
                "release",
                "create",
                f"v{version}",
                "--title",
                f"v{version}",
                "--notes",
                f"Release v{version}",
            ]
            subprocess.run(release_command, check=True)
            print(f"Release v{version} created successfully")
        else:
            print(
                f"Release v{version} would have been created successfully, add --commit to create it"
            )
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def get_new_version(current_version, bump_type, commit=False):
    try:
        print(f"Bumping {bump_type} version from {current_version}")
        # Increment version
        major, minor, patch = map(int, current_version.split("."))
        if bump_type == "patch":
            patch += 1
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        new_version = f"{major}.{minor}.{patch}"
        print(f"New version: {new_version}")
        # Update pyproject.toml
        with open("pyproject.toml", "r") as f:
            pyproject_content = f.read()
        pyproject_content = re.sub(
            r'version = "(.+)"', f'version = "{new_version}"', pyproject_content
        )
        if commit:
            with open("pyproject.toml", "w") as f:
                f.write(pyproject_content)
            # Update __init__.py
        with open("src/kge/__init__.py", "r") as f:
            init_content = f.read()
        init_content = re.sub(
            r'__version__ = "(.+)"', f'__version__ = "{new_version}"', init_content
        )
        if commit:
            with open("src/kge/__init__.py", "w") as f:
                f.write(init_content)
        return new_version
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def check_git_status():
    try:
        # Check if we're on main branch
        current_branch = subprocess.run(
            ["git", "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        if current_branch != "main":
            print(f"Error: Not on main branch (currently on {current_branch})")
            print(
                "Please ensure your changes are merged to main before creating a release"
            )
            return False

        git_status = subprocess.run(
            ["git", "status"], check=True, capture_output=True, text=True
        )
        if "Changes to be committed" in git_status.stdout:
            print("Error: There are changes to be committed")
            return False
        if "Changes not staged for commit" in git_status.stdout:
            print("Error: There are changes not staged for commit")
            return False

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def install_dev_package():
    try:
        subprocess.run(["uv", "pip", "install", "-e", "."], check=True)
        print("Development package installed")
        return True
    except Exception as e:
        print(f"Error installing development package: {e}")
        return False


def run_tests():
    try:
        if not install_dev_package():
            return False
        subprocess.run(["uv", "run", "pytest"], check=True)
        print("Tests passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_lint():
    try:
        # First try to fix automatically fixable issues
        subprocess.run(["uvx", "ruff", "check", "--fix", "src"], check=True)
        # Then run a final check
        subprocess.run(["uvx", "ruff", "check", "src"], check=True)
        print("Lint passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_format():
    try:
        subprocess.run(["uvx", "black", "src"], check=True)
        subprocess.run(["uvx", "isort", "src"], check=True)
        print("Format passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_type_check():
    try:
        if not install_dev_package():
            return False
        subprocess.run(["uvx", "mypy", "src"], check=True)
        print("Type check passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_build():
    try:
        subprocess.run(["uv", "run", "python", "-m", "build"], check=True)
        print("Build passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="Create a new release or update the version"
        )
        parser.add_argument(
            "--patch", action="store_true", help="Bump the patch version"
        )
        parser.add_argument(
            "--minor", action="store_true", help="Bump the minor version"
        )
        parser.add_argument(
            "--major", action="store_true", help="Bump the major version"
        )
        parser.add_argument("--commit", action="store_true", help="Commit the changes")
        args = parser.parse_args()

        # Determine bump type from flags
        if args.major:
            bump_type = "major"
        elif args.minor:
            bump_type = "minor"
        elif args.patch:
            bump_type = "patch"
        else:
            print("Error: Please specify one of --patch, --minor, or --major")
            exit(1)
        # run black to fix formatting
        subprocess.run(["black", "src"], check=True)
        if not run_tests():
            exit(1)
        if not run_lint():
            exit(1)
        if not run_format():
            exit(1)
        if not run_type_check():
            exit(1)
        if not run_build():
            exit(1)
        if not check_git_status():
            exit(1)
        # Get latest version from GitHub
        current_version = find_github_version()
        if current_version:
            print(f"Latest version on GitHub: {current_version}")
        else:
            print("No releases found on GitHub")
            exit(1)
        if not find_pypi_version(current_version):
            print(
                f"Error: GitHub version {current_version} does not match PyPI version\nThis must be fixed manually before releasing"
            )
            exit(1)
        # Update version
        new_version = get_new_version(
            current_version, bump_type=bump_type, commit=args.commit
        )
        # Create release
        create_release(new_version, args.commit)
    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()
