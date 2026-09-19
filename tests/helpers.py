"""Plain helpers for the tests.

Kept out of conftest.py on purpose: conftest is for fixtures that pytest injects,
this is for functions a test calls itself. Mixing the two makes it unclear which
names arrive by magic and which by import.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = ["commit_all", "git", "head"]


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def commit_all(repo: Path, message: str) -> None:
    git("add", "-A", cwd=repo)
    git("commit", "-qm", message, cwd=repo)


def head(repo: Path) -> str:
    return git("rev-parse", "HEAD", cwd=repo).stdout.strip()
