# Build and Publishing Guide

This document outlines the steps to build and publish new versions of the package.

## Publishing Workflow

### 1. Pre-publish Checks

Run all checks in sequence (each step only proceeds if previous step succeeds):

```bash
# Update dependencies and run tests
poetry update && \
poetry run pytest && \
poetry check
```

### 2. Version Update

Choose ONE of these version bump commands based on your changes:

```bash
poetry version patch  # for bug fixes (0.0.x)
poetry version minor  # for new features (0.x.0)
poetry version major  # for breaking changes (x.0.0)
```

Then verify version sync:

```bash
poetry run pytest tests/test_version.py
```

### 3. Build and Publish

Execute the build and publish sequence:

```bash
# Clean, build, and publish
rm -rf dist/ && \
poetry build && \
poetry publish
```

### 4. Post-publish Verification

Create git tag and verify installation:

```bash
# Tag and push
git tag v$(poetry version -s) && \
git push origin v$(poetry version -s) && \
pip install --no-cache-dir kge-kubectl-get-events
```

## Configuration

### PyPI Authentication

```bash
# Configure PyPI token (only needed once)
poetry config pypi-token.pypi your-token
```

### Test PyPI (Optional)

```bash
# Configure Test PyPI (only needed once)
poetry config repositories.testpypi "https://test.pypi.org/legacy/" && \
poetry config pypi-token.testpypi your-test-token

# Publish to Test PyPI
poetry publish -r testpypi
```

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

Key improvements made:

1. Combined related commands using `&&` for sequential execution
2. Organized into clear, numbered sections
3. Separated mandatory steps from optional ones
4. Removed redundant explanations
5. Made the workflow more linear and easier to follow
6. Added command chaining to ensure each step only proceeds if the previous step succeeds

Would you like me to explain any part of this process in more detail or make any additional improvements?