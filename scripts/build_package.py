"""Build a manual-install UniLED Next package."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

INTEGRATION_ROOT = Path("custom_components") / "uniled"
DEFAULT_OUTPUT = Path("dist") / "uniled-next.zip"

EXCLUDED_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".venv",
        "dist",
    }
)
PACKAGE_SUFFIXES = frozenset({".json", ".py", ".yaml"})
FORBIDDEN_PACKAGE_SUFFIXES = frozenset(
    {
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".png",
        ".pyc",
        ".pyo",
        ".svg",
        ".webp",
    }
)
HA_PLATFORM_MODULES = (
    "sensor",
    "light",
    "number",
    "select",
    "switch",
    "scene",
    "button",
)
RUNTIME_DATA_FILES = (
    INTEGRATION_ROOT / "core" / "catalog" / "models.json",
)
REQUIRED_PACKAGE_FILES = (
    INTEGRATION_ROOT / "__init__.py",
    INTEGRATION_ROOT / "config_flow.py",
    INTEGRATION_ROOT / "manifest.json",
    INTEGRATION_ROOT / "services.yaml",
    INTEGRATION_ROOT / "translations" / "en.json",
    *(INTEGRATION_ROOT / f"{platform}.py" for platform in HA_PLATFORM_MODULES),
    *RUNTIME_DATA_FILES,
)


def iter_package_files(project_root: Path) -> tuple[Path, ...]:
    """Return project-relative files included in the install package."""
    integration_root = project_root / INTEGRATION_ROOT
    files: list[Path] = []
    for path in integration_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(project_root)
        if any(part in EXCLUDED_DIR_NAMES for part in relative.parts):
            continue
        if path.suffix not in PACKAGE_SUFFIXES:
            continue
        files.append(relative)
    return tuple(sorted(files))


def validate_package_files(files: tuple[Path, ...]) -> None:
    """Validate package file-list invariants."""
    missing = tuple(path for path in REQUIRED_PACKAGE_FILES if path not in files)
    if missing:
        raise ValueError(
            "package file list is missing required files: "
            + ", ".join(path.as_posix() for path in missing)
        )

    forbidden = tuple(
        path
        for path in files
        if path.suffix in FORBIDDEN_PACKAGE_SUFFIXES
        or any(part in EXCLUDED_DIR_NAMES for part in path.parts)
    )
    if forbidden:
        raise ValueError(
            "package file list contains forbidden files: "
            + ", ".join(path.as_posix() for path in forbidden)
        )


def build_package(project_root: Path, output: Path) -> tuple[Path, tuple[Path, ...]]:
    """Build the install zip and return the written path plus file list."""
    files = iter_package_files(project_root)
    validate_package_files(files)

    output = output if output.is_absolute() else project_root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for relative in files:
            zipf.write(project_root / relative, relative.as_posix())
    return output, files


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a manual Home Assistant custom-component package.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output zip path, default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the package file list without writing a zip.",
    )
    return parser


def main() -> int:
    """Run the command-line entry point."""
    args = _parser().parse_args()
    project_root = Path(__file__).resolve().parents[1]
    files = iter_package_files(project_root)
    validate_package_files(files)

    if args.list:
        for path in files:
            print(path.as_posix())
        return 0

    output, files = build_package(project_root, args.output)
    print(f"Wrote {output} with {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
