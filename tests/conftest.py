"""Shared fixtures.

pytest imports this file automatically for every test in the directory, which is
why the fixtures below need no import anywhere: a test just names one as an
argument and pytest supplies it. That is the convention, not a trick.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import commit_all, git, head
from portolano import cli


@pytest.fixture
def upstream(tmp_path: Path) -> Path:
    """A source repository with code in two unrelated places."""
    repo = tmp_path / "upstream"
    (repo / "src" / "services" / "notification").mkdir(parents=True)
    (repo / "src" / "services" / "notification" / "dispatch.py").write_text("x = 1\n")
    (repo / "src" / "other").mkdir(parents=True)
    (repo / "src" / "other" / "thing.py").write_text("y = 1\n")
    git("init", "-q", "-b", "main", cwd=repo)
    git("config", "user.email", "t@example.com", cwd=repo)
    git("config", "user.name", "Test", cwd=repo)
    commit_all(repo, "initial")
    return repo


@pytest.fixture
def workspace(tmp_path: Path, upstream: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An initialised workspace with `upstream` added as the `backend` submodule."""
    # git refuses the file:// transport for submodules by default; real users
    # clone over https/ssh, so this is a test-environment concession only.
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "protocol.file.allow")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "always")

    root = tmp_path / "my-wiki"
    cli.main(["init", str(root), "--name", "demo"])
    git("config", "user.email", "t@example.com", cwd=root)
    git("config", "user.name", "Test", cwd=root)
    monkeypatch.chdir(root)
    cli.main(["add", str(upstream), "--name", "backend"])
    return root


@pytest.fixture
def page(workspace: Path):
    """Write a page with a freshness contract, and hand back its path."""

    def _write(verified: str, covers: str, *, wiki: str = "backend", name: str = "dispatch.md") -> Path:
        target = workspace / "wiki" / wiki / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "---\n"
            f"title: {name}\n"
            f"slug: {wiki}/{name.removesuffix('.md')}\n"
            "type: reference\n"
            "status: active\n"
            "summary: test page.\n"
            "related: []\n"
            "updated: 2026-01-01\n"
            f"verified-at: {verified}\n"
            f"covers: [{covers}]\n"
            "---\n\n# Page\n"
        )
        return target

    return _write


@pytest.fixture
def pull(workspace: Path, upstream: Path):
    """Advance a submodule checkout, the way `git submodule update --remote` would."""

    def _pull(name: str = "backend") -> None:
        sub = workspace / "repos" / name
        git("fetch", "-q", "origin", cwd=sub)
        git("checkout", "-q", head(upstream), cwd=sub)

    return _pull
