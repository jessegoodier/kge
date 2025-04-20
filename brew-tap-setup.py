#!/usr/bin/env python3
"""
brew_tap_setup.py - Generate a Homebrew tap repository for a Python package

This script creates the necessary files and structure for a Homebrew tap
repository that installs a Python package from PyPI.
"""

import os
import sys
import json
import subprocess
import argparse
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


class HomebrewTapGenerator:
    def __init__(self, package_name: str, tap_name: str, github_username: str):
        self.package_name = package_name
        self.tap_name = tap_name
        self.github_username = github_username
        self.repo_name = f"homebrew-{tap_name}"
        self.package_info = self._fetch_package_info()
        
    def _fetch_package_info(self) -> Dict[str, Any]:
        """Fetch package information from PyPI."""
        try:
            response = requests.get(f"https://pypi.org/pypi/{self.package_name}/json")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching package info from PyPI: {e}")
            sys.exit(1)
    
    def _get_latest_version(self) -> str:
        """Get the latest version of the package."""
        return self.package_info["info"]["version"]
    
    def _get_package_description(self) -> str:
        """Get the package description."""
        return self.package_info["info"]["summary"]
    
    def _get_package_url(self) -> str:
        """Get the package homepage URL."""
        return self.package_info["info"]["home_page"] or self.package_info["info"]["project_url"] or f"https://pypi.org/project/{self.package_name}/"
    
    def _get_sdist_url_and_sha256(self) -> Tuple[str, str]:
        """Get the URL and SHA256 hash of the source distribution."""
        for url_info in self.package_info["urls"]:
            if url_info["packagetype"] == "sdist":
                return url_info["url"], url_info["digests"]["sha256"]
        
        # If no sdist is found, raise an error
        raise ValueError(f"No source distribution (sdist) found for {self.package_name}")
    
    def _create_directory_structure(self):
        """Create the directory structure for the Homebrew tap."""
        # Create the main directory
        os.makedirs(self.repo_name, exist_ok=True)
        
        # Create the Formula directory
        formula_dir = os.path.join(self.repo_name, "Formula")
        os.makedirs(formula_dir, exist_ok=True)
        
        return formula_dir
    
    def _generate_formula(self) -> str:
        """Generate the Ruby formula for the package."""
        version = self._get_latest_version()
        description = self._get_package_description()
        homepage = self._get_package_url()
        url, sha256 = self._get_sdist_url_and_sha256()
        
        # Convert package name to formula-friendly name
        formula_name = self.package_name.replace("-", "_")
        
        # Create the formula content
        formula = f'''class {formula_name.capitalize()} < Formula
  include Language::Python::Virtualenv

  desc "{description}"
  homepage "{homepage}"
  url "{url}"
  sha256 "{sha256}"
  license "{self.package_info['info'].get('license', 'Unknown')}"

  depends_on "python@3"

  # Add dependencies
'''

        # Add resource blocks for package dependencies
        if 'requires_dist' in self.package_info['info'] and self.package_info['info']['requires_dist']:
            for dep in self.package_info['info']['requires_dist']:
                # Extract the package name from the dependency string
                dep_name = re.match(r"([^<>=;]+)", dep).group(1).strip()
                
                # Skip if the dependency has extra markers or is a requirement for a specific version of Python
                if "extra ==" in dep or "python_version" in dep:
                    continue
                    
                formula += f'''  resource "{dep_name}" do
    url "https://pypi.org/simple/#{dep_name}/"
  end

'''

        # Add installation commands
        formula += f'''  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"{self.package_name}", "--version"
  end
end
'''
        
        return formula
    
    def _generate_readme(self) -> str:
        """Generate the README for the tap repository."""
        return f'''# {self.tap_name}

A Homebrew tap for {self.package_name}.

## Installation

```bash
# Add the tap
brew tap {self.github_username}/{self.tap_name}

# Install the package
brew install {self.package_name}
```

## Updating

To update the formula when a new version of {self.package_name} is released:

1. Run the update script:
   ```
   ./update_formula.py
   ```

2. Commit and push the changes:
   ```
   git add Formula/{self.package_name.replace("-", "_")}.rb
   git commit -m "Update {self.package_name} to version X.Y.Z"
   git push
   ```

## License

This Homebrew tap is provided under the same license as {self.package_name}.
'''
    
    def _generate_update_script(self) -> str:
        """Generate a script to update the formula when a new version is released."""
        formula_name = self.package_name.replace("-", "_")
        return f'''#!/usr/bin/env python3
"""
Update the Homebrew formula for {self.package_name} to the latest version.
"""

import os
import sys
import json
import requests
import re
from pathlib import Path


def update_formula():
    """Update the formula to the latest version."""
    package_name = "{self.package_name}"
    formula_name = "{formula_name}"
    formula_file = Path("Formula/{formula_name}.rb")
    
    if not formula_file.exists():
        print(f"Error: Formula file Formula/{{formula_name}}.rb not found")
        sys.exit(1)
    
    try:
        response = requests.get(f"https://pypi.org/pypi/{{package_name}}/json")
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
            print(f"Error: Could not find sdist URL or SHA256 for {{package_name}}")
            sys.exit(1)
        
        # Read the current formula
        formula_content = formula_file.read_text()
        
        # Update the URL and SHA256
        formula_content = re.sub(
            r'url "([^"]+)"',
            f'url "{{sdist_url}}"',
            formula_content
        )
        formula_content = re.sub(
            r'sha256 "([^"]+)"',
            f'sha256 "{{sha256}}"',
            formula_content
        )
        
        # Write the updated formula
        formula_file.write_text(formula_content)
        
        print(f"Updated {{package_name}} formula to version {{latest_version}}")
        print(f"URL: {{sdist_url}}")
        print(f"SHA256: {{sha256}}")
        
    except requests.RequestException as e:
        print(f"Error fetching package info from PyPI: {{e}}")
        sys.exit(1)


if __name__ == "__main__":
    update_formula()
'''
    
    def _generate_gitignore(self) -> str:
        """Generate a .gitignore file."""
        return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*

# VS Code
.vscode/

# PyCharm
.idea/

# Environment
.env
.venv
venv/
ENV/
'''
    
    def generate_tap(self):
        """Generate the complete Homebrew tap repository."""
        # Create the directory structure
        formula_dir = self._create_directory_structure()
        
        # Generate and write the formula
        formula_path = os.path.join(formula_dir, f"{self.package_name.replace('-', '_')}.rb")
        with open(formula_path, "w") as f:
            f.write(self._generate_formula())
        
        # Generate and write the README
        readme_path = os.path.join(self.repo_name, "README.md")
        with open(readme_path, "w") as f:
            f.write(self._generate_readme())
        
        # Generate and write the update script
        update_script_path = os.path.join(self.repo_name, "update_formula.py")
        with open(update_script_path, "w") as f:
            f.write(self._generate_update_script())
        
        # Make the update script executable
        os.chmod(update_script_path, 0o755)
        
        # Generate and write the .gitignore
        gitignore_path = os.path.join(self.repo_name, ".gitignore")
        with open(gitignore_path, "w") as f:
            f.write(self._generate_gitignore())
        
        print(f"Generated Homebrew tap repository in {self.repo_name}/")
        print(f"Next steps:")
        print(f"1. Review the generated files")
        print(f"2. Initialize a Git repository:")
        print(f"   cd {self.repo_name}/")
        print(f"   git init")
        print(f"   git add .")
        print(f"   git commit -m 'Initial commit'")
        print(f"3. Create a repository on GitHub named {self.repo_name}")
        print(f"4. Push to GitHub:")
        print(f"   git remote add origin https://github.com/{self.github_username}/{self.repo_name}.git")
        print(f"   git push -u origin main")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate a Homebrew tap repository for a Python package"
    )
    parser.add_argument(
        "package_name",
        help="Name of the Python package on PyPI"
    )
    parser.add_argument(
        "tap_name",
        help="Name of the Homebrew tap (without the homebrew- prefix)"
    )
    parser.add_argument(
        "github_username",
        help="Your GitHub username"
    )
    
    args = parser.parse_args()
    
    generator = HomebrewTapGenerator(
        args.package_name,
        args.tap_name,
        args.github_username
    )
    generator.generate_tap()


if __name__ == "__main__":
    main()
