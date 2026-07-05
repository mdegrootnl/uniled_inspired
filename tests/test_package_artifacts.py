"""Manual install package tests."""

from __future__ import annotations

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from scripts.build_package import (
    FORBIDDEN_PACKAGE_SUFFIXES,
    HA_PLATFORM_MODULES,
    INTEGRATION_ROOT,
    REQUIRED_PACKAGE_FILES,
    RUNTIME_DATA_FILES,
    build_package,
    iter_package_files,
    validate_package_files,
)


def _forwarded_platforms() -> tuple[str, ...]:
    """Return the platform modules forwarded by integration setup."""
    source = (Path.cwd() / INTEGRATION_ROOT / "__init__.py").read_text(
        encoding="utf-8"
    )
    module = ast.parse(source)
    for statement in module.body:
        if not isinstance(statement, ast.AnnAssign):
            continue
        target = statement.target
        if isinstance(target, ast.Name) and target.id == "PLATFORMS":
            return tuple(ast.literal_eval(statement.value))
    raise AssertionError("PLATFORMS assignment not found in integration __init__.py")


def test_package_file_list_contains_required_home_assistant_artifacts() -> None:
    """The package file list contains the HA custom-component entry points."""
    files = iter_package_files(Path.cwd())

    validate_package_files(files)

    for required in REQUIRED_PACKAGE_FILES:
        assert required in files


def test_package_file_list_contains_forwarded_platform_modules() -> None:
    """The package includes every platform module forwarded during HA setup."""
    files = iter_package_files(Path.cwd())

    assert HA_PLATFORM_MODULES == _forwarded_platforms()
    for platform in HA_PLATFORM_MODULES:
        assert INTEGRATION_ROOT / f"{platform}.py" in files


def test_package_file_list_contains_runtime_catalog_data() -> None:
    """The package includes generated data needed before HA can create entities."""
    files = iter_package_files(Path.cwd())

    for data_file in RUNTIME_DATA_FILES:
        assert data_file in files


def test_package_file_list_excludes_caches_and_image_assets() -> None:
    """The package file list excludes transient files and bundled images."""
    files = iter_package_files(Path.cwd())

    assert files
    assert all("__pycache__" not in path.parts for path in files)
    assert all(path.suffix != ".pyc" for path in files)
    assert all(path.suffix not in FORBIDDEN_PACKAGE_SUFFIXES for path in files)


def test_build_package_writes_expected_zip_entries() -> None:
    """The manual install zip mirrors the validated file list."""
    files = iter_package_files(Path.cwd())

    with TemporaryDirectory(prefix="uniled-package-") as tmp:
        output, packaged_files = build_package(Path.cwd(), Path(tmp) / "uniled.zip")

        assert packaged_files == files
        with ZipFile(output) as zipf:
            assert tuple(sorted(zipf.namelist())) == tuple(
                path.as_posix() for path in files
            )
