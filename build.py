#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

def get_current_version():
    """Get current version from pyproject.toml"""
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        raise ValueError("Could not find version in pyproject.toml")

def increment_version(version):
    """Increment version number"""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    
    # Increment patch version
    parts[2] = str(int(parts[2]) + 1)
    return '.'.join(parts)

def update_version_in_file(file_path, old_version, new_version):
    """Update version in a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace version in pyproject.toml format
    content = content.replace(f'version = "{old_version}"', f'version = "{new_version}"')
    content = content.replace(f"version = '{old_version}'", f"version = '{new_version}'")
    
    # Replace version in setup.py format
    content = content.replace(f"version='{old_version}'", f"version='{new_version}'")
    content = content.replace(f'version="{old_version}"', f'version="{new_version}"')
    
    # Replace version in other common formats
    content = content.replace(f"VERSION = '{old_version}'", f"VERSION = '{new_version}'")
    content = content.replace(f'VERSION = "{old_version}"', f'VERSION = "{new_version}"')
    content = content.replace(f"__version__ = '{old_version}'", f"__version__ = '{new_version}'")
    content = content.replace(f'__version__ = "{old_version}"', f'__version__ = "{new_version}"')
    
    # Replace version in Homebrew formula format
    content = content.replace(f'url "https://github.com/jessegoodier/kge-kubectl-get-events/archive/refs/tags/v{old_version}.tar.gz"', 
                            f'url "https://github.com/jessegoodier/kge-kubectl-get-events/archive/refs/tags/v{new_version}.tar.gz"')
    
    with open(file_path, 'w') as f:
        f.write(content)

def update_version_in_all_files(new_version):
    """Update version in all relevant files"""
    # List of files that might contain version information
    files_to_update = [
        'pyproject.toml',
        'setup.py',
        'kge/cli/main.py',
        'kge/cli/__init__.py',
        'README.md',
        'homebrew-formula/kge.rb'
    ]
    
    old_version = get_current_version()
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            try:
                update_version_in_file(file_path, old_version, new_version)
                print(f"Updated version in {file_path}")
            except Exception as e:
                print(f"Warning: Could not update version in {file_path}: {e}")

def run_tests():
    """Run all unit tests"""
    try:
        print("Running unit tests...")
        result = subprocess.run(['python', '-m', 'pytest', 'tests/'], check=True)
        if result.returncode == 0:
            print("All tests passed successfully!")
            return True
        return False
    except subprocess.CalledProcessError as e:
        print(f"Tests failed: {e}")
        return False

def build_package():
    """Build and upload the package"""
    try:
        # Clean previous builds
        subprocess.run(['rm', '-rf', 'dist', 'build', '*.egg-info'], check=True)
        
        # Build the package using pip
        subprocess.run(['pip', 'wheel', '--no-deps', '-w', 'dist', '.'], check=True)
        
        print("\nPackage built successfully!")
        print("To upload to PyPI, run: twine upload dist/*")
    except subprocess.CalledProcessError as e:
        print(f"Error building package: {e}")
        return False
    return True

def main():
    # Run tests first
    if not run_tests():
        print("Build aborted due to test failures")
        return

    # Get current version and increment it
    current_version = get_current_version()
    new_version = increment_version(current_version)
    
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Update version in all files
    update_version_in_all_files(new_version)
    
    # Build the package
    if build_package():
        print(f"\nSuccessfully built version {new_version}")
        print("Next steps:")
        print("1. Test the package locally")
        print("2. Commit the version changes")
        print("3. Create a git tag for the new version")
        print("4. Push the changes and tag")
        print("5. Upload to PyPI with: twine upload dist/*")
        print("6. Update the Homebrew formula SHA256 after uploading the release")

if __name__ == "__main__":
    main() 