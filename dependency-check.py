import subprocess
import tempfile
import os
import json
from pathlib import Path

def get_dependencies(package_name):
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Downloading {package_name} and dependencies...")
        subprocess.run([
            "pip", "download", package_name, "--dest", temp_dir, "--no-binary", ":all:", "--no-deps"
        ], check=True)

        # Get the metadata for the package itself
        metadata = subprocess.run(
            ["pip", "show", package_name],
            stdout=subprocess.PIPE,
            check=True,
            text=True
        ).stdout

        deps = []
        for line in metadata.splitlines():
            if line.startswith("Requires:"):
                raw_deps = line.split(":", 1)[1].strip()
                if raw_deps:
                    deps = [dep.strip() for dep in raw_deps.split(",")]
                break

        print(f"Found dependencies for {package_name}: {deps}")
        return deps

def get_recursive_dependencies(package_name, visited=None):
    if visited is None:
        visited = set()
    if package_name in visited:
        return set()
    visited.add(package_name)
    deps = get_dependencies(package_name)
    all_deps = set(deps)
    for dep in deps:
        all_deps.update(get_recursive_dependencies(dep, visited))
    return all_deps

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python get_dependencies.py <package-name>")
        sys.exit(1)

    package = sys.argv[1]
    all_dependencies = get_recursive_dependencies(package)
    print("\nAll dependencies:")
    for dep in sorted(all_dependencies):
        print(f"- {dep}")
