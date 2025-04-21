#!/usr/bin/env python3
"""
Update the Homebrew formula for kge-kubectl-get-events to the latest version.
"""

import sys
import requests
import re
import subprocess
import venv
from pathlib import Path


def get_package_metadata(package_name):
    """Get package metadata including download URL and SHA256."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()
        package_info = response.json()
        
        latest_version = package_info["info"]["version"]
        
        # Find the sdist URL and SHA256
        sdist_url = None
        sha256 = None
        for url_info in package_info["urls"]:
            if url_info["packagetype"] == "sdist":
                sdist_url = url_info["url"]
                sha256 = url_info["digests"]["sha256"]
                break
        
        if not sdist_url or not sha256:
            print(f"Error: Could not find sdist URL or SHA256 for {package_name}")
            sys.exit(1)
            
        return latest_version, sdist_url, sha256
    except requests.RequestException as e:
        print(f"Error fetching package info from PyPI: {e}")
        sys.exit(1)


def get_all_dependencies(package_name, venv_path):
    """Get all dependencies (including transitive) for a package using pip show."""
    try:
        # Use the virtual environment's pip to install and show package info
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
        
        # First install the package in the virtual environment
        subprocess.run(
            [str(pip_path), "install", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get the dependency tree
        result = subprocess.run(
            [str(pip_path), "show", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output to find the Requires line
        requires_line = None
        for line in result.stdout.split('\n'):
            if line.startswith('Requires:'):
                requires_line = line
                break
        
        if not requires_line:
            return []
            
        # Extract package names from the Requires line
        direct_dependencies = requires_line.replace('Requires:', '').strip().split(', ')
        direct_dependencies = [dep for dep in direct_dependencies if dep]  # Remove empty strings
        
        # Get transitive dependencies for each direct dependency
        all_dependencies = set(direct_dependencies)
        for dep in direct_dependencies:
            result = subprocess.run(
                [str(pip_path), "show", dep],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output to find the Requires line
            for line in result.stdout.split('\n'):
                if line.startswith('Requires:'):
                    transitive_deps = line.replace('Requires:', '').strip().split(', ')
                    all_dependencies.update(dep for dep in transitive_deps if dep)  # Only add non-empty deps
                    break
        
        # Remove the main package and empty strings from dependencies
        all_dependencies.discard(package_name.replace("-", "_"))
        all_dependencies.discard("")
        
        return sorted(all_dependencies)
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting dependencies for {package_name}: {e}")
        return []


def get_resource_block(package_name):
    """Generate a resource block for a package."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()
        package_info = response.json()
        
        # Find the sdist URL and SHA256
        sdist_url = None
        sha256 = None
        for url_info in package_info["urls"]:
            if url_info["packagetype"] == "sdist":
                sdist_url = url_info["url"]
                sha256 = url_info["digests"]["sha256"]
                break
        
        if not sdist_url or not sha256:
            return None
            
        return f'''  resource "{package_name}" do
    url "{sdist_url}"
    sha256 "{sha256}"
  end

'''
    except requests.RequestException:
        return None


def update_formula():
    """Update the formula to the latest version."""
    package_name = "kge-kubectl-get-events"
    formula_name = "kge"
    formula_file = Path("homebrew-kge/Formula") / f"{formula_name}.rb"
    
    if not formula_file.exists():
        print(f"Error: Formula file {formula_file} not found")
        sys.exit(1)
    
    # Get main package metadata
    latest_version, sdist_url, sha256 = get_package_metadata(package_name)
    
    # Read the current formula
    formula_content = formula_file.read_text()
    
    # Update the URL and SHA256
    formula_content = re.sub(
        r'url "([^"]+)"',
        f'url "{sdist_url}"',
        formula_content
    )
    formula_content = re.sub(
        r'sha256 "([^"]+)"',
        f'sha256 "{sha256}"',
        formula_content
    )
    
    # Remove existing resource blocks and extra newlines
    formula_content = re.sub(
        r'  resource "[^"]+" do\n    url "[^"]+"\n    sha256 "[^"]+"\n  end\n',
        '',
        formula_content
    )
    formula_content = re.sub(
        r'\n{3,}',
        '\n\n',
        formula_content
    )
    
    # Create a virtual environment for getting dependencies
    venv_path = Path("venv")
    if venv_path.exists():
        import shutil
        shutil.rmtree(venv_path)
    venv.create(venv_path, with_pip=True)
    
    # Get all dependencies (including transitive)
    dependencies = get_all_dependencies(package_name, venv_path)
    
    # Add resource blocks for all dependencies
    resource_blocks = []
    for dep in dependencies:
        resource_block = get_resource_block(dep)
        if resource_block:
            resource_blocks.append(resource_block)
    
    # Insert resource blocks before the install method
    formula_content = re.sub(
        r'  def install',
        f"{''.join(resource_blocks)}  def install",
        formula_content
    )
    
    # Write the updated formula
    formula_file.write_text(formula_content)
    
    print(f"Updated {package_name} formula to version {latest_version}")
    print(f"URL: {sdist_url}")
    print(f"SHA256: {sha256}")
    print("\nAdded resources for dependencies:")
    for dep in dependencies:
        print(f"  - {dep}")


if __name__ == "__main__":
    update_formula()
