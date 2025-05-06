from setuptools import setup, find_packages
import os
import tomli


def get_version():
    """Get the version from the package without importing it."""
    with open(os.path.join("src", "kge", "__init__.py"), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"')


def get_pyproject_metadata():
    """Read metadata from pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)
    return pyproject["project"]


metadata = get_pyproject_metadata()

setup(
    name=metadata["name"],
    version=get_version(),
    description=metadata["description"],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author=metadata["authors"][0]["name"],
    author_email=metadata["authors"][0]["email"],
    url=metadata["urls"]["Homepage"],
    project_urls=metadata["urls"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "kge": ["completion/_kge"],
    },
    python_requires=metadata["requires-python"],
    install_requires=metadata["dependencies"],
    extras_require={
        "test": [
            "coverage>=7.2.0",
            "pytest>=8.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kge = kge.cli.main:main",
        ],
    },
    keywords=metadata["keywords"],
    license=metadata["license"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
