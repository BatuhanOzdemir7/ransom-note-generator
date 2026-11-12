"""Remove generated output from previous font builds."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
GENERATED_DIRECTORIES = ("build", "generated_letters", "font_workspace")


def _remove_read_only_path(operation, path: str, error_info) -> None:
    """Make a read-only path writable and retry the failed removal."""
    os.chmod(path, stat.S_IWRITE)
    operation(path)


def _remove_path(path: Path) -> None:
    """Remove a file, directory, or symbolic link at the given path."""
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, onerror=_remove_read_only_path)


def _remove_path_or_skip_locked_empty(path: Path) -> None:
    """Remove a path, allowing an OS-locked folder only when it is empty."""
    try:
        _remove_path(path)
    except PermissionError:
        if path.is_dir() and not any(path.iterdir()):
            print(f"Could not remove locked empty folder: {path}")
            return
        raise


def cleanup_workspace(project_root: Path = PROJECT_ROOT) -> None:
    """Delete known build outputs and every Python cache under the project."""
    root = Path(project_root).resolve()

    for directory_name in GENERATED_DIRECTORIES:
        _remove_path_or_skip_locked_empty(root / directory_name)

    cache_directories = sorted(
        root.rglob("__pycache__"),
        key=lambda cache_path: len(cache_path.parts),
        reverse=True,
    )
    for cache_directory in cache_directories:
        _remove_path_or_skip_locked_empty(cache_directory)


if __name__ == "__main__":
    cleanup_workspace()
    print("Removed generated build folders and Python caches.")
