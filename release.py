#! /usr/bin/env python3
import re
import subprocess
import argparse
import sys

def check_version_match(version):
    try:
        # Check pyproject.toml
        with open("pyproject.toml", "r") as f:
            pyproject_content = f.read()
        if "version = " not in pyproject_content:
            print("Error: 'version = ' not found in pyproject.toml")
            return
        # Check __init__.py
        with open("src/kge/__init__.py", "r") as f:
            init_content = f.read()
        if "__version__ = " not in init_content:
            print("Error: '__version__ = ' not found in __init__.py")
            return
        # Extract versions from files
        pyproject_version = re.search(r'version = "(.+)"', pyproject_content).group(1)
        init_version = re.search(r'__version__ = "(.+)"', init_content).group(1)
        if version != pyproject_version or version != init_version:
            print(f"Error: Version mismatch between pyproject.toml and __init__.py")
            print(f"pyproject.toml: {pyproject_version}")
            print(f"__init__.py: {init_version}")
            return
        print(f"Versions match: pyproject.toml = {pyproject_version}, __init__.py = {init_version}")
    except Exception as e:
        print(f"Error: {e}")
        return

def create_release(version, commit):
    try:
        # Check if version is already released
        release_command = ["gh", "release", "list", "--json", "name", "--jq", ".[].name"]
        release_list = subprocess.check_output(release_command, text=True).splitlines()
        if f"v{version}" in release_list:
            print(f"Error: Version {version} is already released")
            return
        # Create release
        release_command = ["gh", "release", "create", f"v{version}", "--title", f"v{version}", "--notes", f"Release v{version}"]
        if commit:
            subprocess.run(release_command, check=True)
        print(f"Release v{version} created successfully")
    except Exception as e:
        print(f"Error: {e}")
        return

def update_version(bump_type):
    try:
        # Read current version
        with open("pyproject.toml", "r") as f:
            pyproject_content = f.read()
        current_version = re.search(r'version = "(.+)"', pyproject_content).group(1)
        print(f"{bump_type} current version: {current_version}")
        # Increment version
        major, minor, patch = map(int, current_version.split('.'))
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
        # Update pyproject.toml
        pyproject_content = re.sub(r'version = "(.+)"', f'version = "{new_version}"', pyproject_content)
        with open("pyproject.toml", "w") as f:
            f.write(pyproject_content)
        # Update __init__.py
        with open("src/kge/__init__.py", "r") as f:
            init_content = f.read()
        init_content = re.sub(r'__version__ = "(.+)"', f'__version__ = "{new_version}"', init_content)
        with open("src/kge/__init__.py", "w") as f:
            f.write(init_content)
        print(f"Version updated to {new_version}")
        return new_version
    except Exception as e:
        print(f"Error: {e}")
        return

def run_tests():
    try:
        subprocess.run(["pytest"], check=True)
        print("Tests passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_lint():
    try:
        subprocess.run(["flake8", "."], check=True)
        print("Lint passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_format():
    try:
        subprocess.run(["black", "."], check=True)
        print("Format passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_build():
    try:
        subprocess.run(["python", "setup.py", "build"], check=True)
        print("Build passed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Create a new release or update the version")
        parser.add_argument("--patch", action="store_true", help="Bump the patch version")
        parser.add_argument("--minor", action="store_true", help="Bump the minor version")
        parser.add_argument("--major", action="store_true", help="Bump the major version")
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
            return
        if not run_tests():
            return
        if not run_lint():
            return
        if not run_format():
            return
        if not run_build():
            return
        # Update version
        new_version = update_version(bump_type=bump_type)
        # Check version match
        check_version_match(new_version)
        # Create release
        create_release(new_version, args.commit)
    except Exception as e:
        print(f"Error: {e}")
        return

    

if __name__ == "__main__":
    main()
