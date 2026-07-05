"""Run the local no-argument test functions without pytest.

This is a lightweight fallback for development shells where pytest and Home
Assistant test helpers are not installed. It intentionally supports only the
current direct unit-test shape; pytest remains the target runner once available.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import inspect
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from types import ModuleType


def run_direct_tests(tests_dir: Path) -> int:
    """Run every no-argument ``test_*`` function under ``tests_dir``."""
    passed = 0
    failures: list[tuple[Path, str, BaseException]] = []

    for path in sorted(tests_dir.glob("test_*.py")):
        module = _load_module(path)
        for name, test in _iter_test_functions(module):
            try:
                _run_test(test)
            except BaseException as exc:  # noqa: BLE001 - print all failures.
                failures.append((path, name, exc))
            else:
                passed += 1

    if failures:
        print(f"{passed} direct tests passed before failures")
        for path, name, exc in failures:
            print(f"FAILED {path}::{name}: {exc!r}")
            traceback.print_exception(exc)
        return 1

    print(f"{passed} direct tests passed")
    return 0


def _load_module(path: Path) -> ModuleType:
    module_name = f"_uniled_direct_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _iter_test_functions(module: ModuleType) -> tuple[tuple[str, Callable], ...]:
    return tuple(
        (name, obj)
        for name, obj in sorted(vars(module).items())
        if name.startswith("test_") and callable(obj)
    )


def _run_test(test: Callable) -> None:
    signature = inspect.signature(test)
    if signature.parameters:
        raise RuntimeError(f"{test.__module__}.{test.__name__} expects parameters")
    result = test()
    if inspect.isawaitable(result):
        asyncio.run(result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run UniLED direct tests without requiring pytest.",
    )
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=Path("tests"),
        help="Test directory to scan, default: tests",
    )
    return parser


def main() -> int:
    """Run the direct test fallback."""
    args = _parser().parse_args()
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))
    tests_dir = args.tests_dir
    if not tests_dir.exists():
        print(f"{tests_dir} does not exist", file=sys.stderr)
        return 2
    return run_direct_tests(tests_dir)


if __name__ == "__main__":
    raise SystemExit(main())
