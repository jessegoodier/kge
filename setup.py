from setuptools import setup, find_packages
import os

def get_version():
    """Get the version from the package without importing it."""
    with open(os.path.join("src", "kge", "__init__.py"), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"')

setup(
    name="kge",
    version=get_version(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["kubernetes==28.1.0", "rich==13.7.0"],
    entry_points={
        "console_scripts": [
            "kge = kge.cli.main:main",
        ],
    },
)