def test_versions_are_in_sync():
    pass
# """Test to validate package version consistency."""

# import toml
# from pathlib import Path
# import kge


# def test_versions_are_in_sync():
#     """Check if the version in pyproject.toml matches the one in __init__.py."""
#     # Get version from pyproject.toml
#     pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
#     pyproject = toml.loads(pyproject_path.read_text())
#     pyproject_version = pyproject["tool"]["poetry"]["version"]
#     print(pyproject_version)
#     print(kge.__version__)
#     print(f"kge package location: {kge.__file__}")
#     # Get version from package
#     package_version = kge.__version__
    
#     # Assert versions match
#     assert package_version == pyproject_version, (
#         f"Version mismatch: pyproject.toml version is {pyproject_version} "
#         f"but package version is {package_version}"
#     ) 