import warnings
import pytest


@pytest.fixture(autouse=True)
def ignore_warnings():
    """Fixture to ignore specific deprecation warnings."""
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, module="kubernetes.client.rest"
    )
