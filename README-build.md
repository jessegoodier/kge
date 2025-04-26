# Build and Publishing Guide

This document outlines the steps to build and publish new versions of the package.

## Publishing Workflow

### 1. Pre-publish Checks

Run all checks in sequence (each step only proceeds if previous step succeeds):

```bash
# Update dependencies and run tests
pip install -e . && \
python -m pytest && \
python setup.py check
```

### 2. Version Update

Update the version in `src/kge/__init__.py` by modifying the `__version__` string:
- For bug fixes: increment the patch version (0.0.x)
- For new features: increment the minor version (0.x.0)
- For breaking changes: increment the major version (x.0.0)

Then verify version sync:

```bash
python -m pytest tests/test_version.py
```

### 3. Build and Publish

Execute the build and publish sequence:

```bash
# Clean, build, and publish
rm -rf dist/ build/ && \
python setup.py sdist bdist_wheel && \
twine upload dist/*
```

### 4. Post-publish Verification

Create git tag and verify installation:

```bash
# Tag and push
git tag v$(python -c "from kge import __version__; print(__version__)") && \
git push origin v$(python -c "from kge import __version__; print(__version__)") && \
pip install --no-cache-dir kge
```

## Configuration



## Advanced Testing (Optional)

To test the built package in a clean environment:

```bash
# Create and activate test environment
python -m venv test_venv && \
source test_venv/bin/activate && \
pip install dist/*.whl && \
python -c "import kge; print(kge.__version__)" && \
deactivate && \
rm -rf test_venv
```
