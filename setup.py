from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kge-kubectl-get-events",
    version="0.2.5",
    author="Jesse Goodier",
    author_email="31039225+jessegoodier@users.noreply.github.com",
    description="A kubernetes utility for viewing pod events in a user-friendly way",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jessegoodier/kge",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "kubernetes>=12.0.0",
    ],
    extras_require={
        "test": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kge=kge.cli.main:main",
        ],
    },
    test_suite="tests",
) 