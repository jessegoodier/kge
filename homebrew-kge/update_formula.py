#!/usr/bin/env python3
"""
Update the Homebrew formula for kge-kubectl-get-events to the latest version.
"""

import os
import sys
import json
import requests
import re
from pathlib import Path


def update_formula():
    """Update the formula to the latest version."""
    package_name = "kge-kubectl-get-events"
    formula_name = "kge_kubectl_get_events"
    formula_file = Path("Formula/kge_kubectl_get_events.rb")
    
    if not formula_file.exists():
        print(f"Error: Formula file Formula/{formula_name}.rb not found")
        sys.exit(1)
    
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
        
        # Write the updated formula
        formula_file.write_text(formula_content)
        
        print(f"Updated {package_name} formula to version {latest_version}")
        print(f"URL: {sdist_url}")
        print(f"SHA256: {sha256}")
        
    except requests.RequestException as e:
        print(f"Error fetching package info from PyPI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    update_formula()
