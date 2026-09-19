"""Everything Portolano knows how to do, minus the command line.

Two halves, in order: talking to git, and deciding whether a page is still true.
Both are plain functions taking a path - there is no state to keep, so there is
no object to keep it in.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_NAME = "portolano.yaml"
MASTER_WIKI = "_master"
FIXED_FILES = {"index.md", "README.md", "CHANGELOG.md"}

# Survey bands: how many tracked files put a repository in each one.
SMALL_REPO, MEDIUM_REPO = 150, 1500
LOW, CRUISING, HIGH = "low", "cruising", "high"

# What `stale` can conclude about a page.
FRESH = "fresh"
SUSPECT = "suspect"
NO_CONTRACT = "no-contract"
ERROR = "error"

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


@dataclass
class PageStatus:
    """The verdict on one page."""

    page: Path
    state: str
    detail: str = ""
    commits: int = 0


@dataclass
class RepoRef:
    """A repository the wiki describes, as read out of portolano.yaml."""

    name: str
    url: str
    path: str
    branch: str | None = None
    # Globs that are tracked but are not this project's work: vendored
    # dependencies, generated stubs, committed build output. Counting them
    # sends `bootstrap` to the wrong altitude.
    skip: list[str] = field(default_factory=list)


def today() -> str:
    # The local date, deliberately: a changelog line is dated in the timezone of
    # whoever wrote it. UTC would date an evening entry in Auckland yesterday.
    return dt.date.today().isoformat()


# --------------------------------------------------------------------------
# git
# --------------------------------------------------------------------------

def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a git command and hand back the result, failures included.

    `check=False` on purpose: for most of what we ask, a non-zero exit is the
    answer (the commit does not exist) rather than an accident.
    """
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def head_commit(repo: Path) -> str | None:
    """The short commit a checkout sits on, or None when we cannot tell."""
    result = git("rev-parse", "--short", "HEAD", cwd=repo)
    return result.stdout.strip() or None if result.returncode == 0 else None


def survey(repo: Path, skip: list[str] | None = None) -> tuple[int, list[str]] | None:
    """Count what a repository holds, without opening a single file.

    git does the counting, so this costs nothing - which matters, because the
    whole job of this measurement is to tell an agent how much it can afford
    to read.

    `skip` drops paths from the count with the same `:(glob)` pathspec that
    `covers` uses, so one glob syntax covers the whole tool.
    """
    args = ["ls-files"]
    if skip:
        args.append("--")
        args += [f":(glob,exclude){pattern}" for pattern in skip]
    result = git(*args, cwd=repo)
    if result.returncode != 0:
        return None
    paths = result.stdout.splitlines()
    return len(paths), sorted({p.split("/")[0] for p in paths if "/" in p})


def altitude(files: int) -> str:
    """How high to fly over a repository of this size.

    The thresholds are round numbers, not findings - nobody has measured where
    a codebase stops being readable in one sitting. What they buy is that the
    answer comes from counting instead of from the agent's mood, and that two
    runs over the same repository agree.
    """
    if files <= SMALL_REPO:
        return LOW
    if files <= MEDIUM_REPO:
        return CRUISING
    return HIGH


def is_checked_out(repo: Path) -> bool:
    """A submodule that was never initialised has no .git entry."""
    return (repo / ".git").exists()


def has_commit(repo: Path, rev: str) -> bool:
    return git("cat-file", "-e", f"{rev}^{{commit}}", cwd=repo).returncode == 0


def commits_touching(repo: Path, since: str, globs: list[str]) -> list[str] | None:
    """One-line log entries after `since` that touched any of `globs`.

    The `:(glob)` prefix is what stops `*` from crossing a `/`. Without it git
    matches with plain fnmatch, so `src/*.php` would also match
    `src/deep/nested/thing.php` and a page would be called suspect by commits
    in directories it never claimed. Returns None if git itself failed.
    """
    pathspecs = [f":(glob){g}" for g in globs]
    result = git("log", "--oneline", f"{since}..HEAD", "--", *pathspecs, cwd=repo)
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line.strip()]


def remote_branch(repo: Path, preferred: str | None = None) -> str | None:
    """The remote branch this checkout should be compared against.

    Order: what the user configured, what the remote says its HEAD is, then the
    two conventional names. **Returns None when none of them resolve**, and the
    caller must treat that as *unknown* - never as *up to date*.
    """
    candidates = []
    if preferred:
        candidates.append(f"origin/{preferred}")

    symref = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD", cwd=repo)
    if symref.returncode == 0 and symref.stdout.strip():
        candidates.append(symref.stdout.strip())

    candidates += ["origin/main", "origin/master"]

    for ref in candidates:
        if has_commit(repo, ref):
            return ref
    return None


def count_behind(repo: Path, ref: str) -> int | None:
    """How many commits HEAD is behind `ref`, or None if git could not say."""
    result = git("rev-list", "--count", f"HEAD..{ref}", cwd=repo)
    if result.returncode != 0 or not result.stdout.strip().isdigit():
        return None
    return int(result.stdout.strip())


# --------------------------------------------------------------------------
# the workspace
# --------------------------------------------------------------------------

def find_root(start: Path | None = None) -> Path | None:
    """Walk up from `start` until a portolano.yaml turns up."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / CONFIG_NAME).is_file():
            return candidate
    return None


def load_config(root: Path) -> dict:
    """The config stays a plain dict: it is exactly the shape of the YAML file."""
    config = yaml.safe_load((root / CONFIG_NAME).read_text(encoding="utf-8")) or {}
    config.setdefault("wiki_dir", "wiki")
    config.setdefault("repos_dir", "repos")
    config.setdefault("repos", {})
    return config


def save_config(root: Path, config: dict) -> None:
    (root / CONFIG_NAME).write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def iter_repos(config: dict) -> Iterator[RepoRef]:
    """The one place a config entry becomes an object.

    Past this point the code says `ref.path` instead of `meta["path"]`, which is
    where a typo would otherwise go unnoticed until it blew up.
    """
    for name, meta in sorted(config["repos"].items()):
        yield RepoRef(name=name, **meta)


def get_repo(config: dict, name: str) -> RepoRef | None:
    meta = config["repos"].get(name)
    return RepoRef(name=name, **meta) if meta else None


def read_frontmatter(page: Path) -> dict | None:
    """The YAML block at the top of a page, or None if there is no valid one."""
    try:
        text = page.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    match = FRONTMATTER_RE.match(text)
    if not match:
        return None

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None

    return data if isinstance(data, dict) else None


def iter_pages(root: Path, config: dict, only: str | None = None) -> Iterator[Path]:
    """Every content page, skipping the three fixed files of each triplet."""
    base = root / config["wiki_dir"]
    if only:
        base = base / only
    if not base.is_dir():
        return

    for page in sorted(base.rglob("*.md")):
        if page.name not in FIXED_FILES:
            yield page


def page_status(page: Path, root: Path, config: dict) -> PageStatus:
    """Whether a page is still true, as far as git can tell."""
    meta = read_frontmatter(page) or {}
    covers = meta.get("covers")
    verified = meta.get("verified-at")

    if not covers or not verified:
        return PageStatus(page, NO_CONTRACT, "no covers/verified-at")
    if isinstance(covers, str):
        covers = [covers]

    parts = page.relative_to(root / config["wiki_dir"]).parts
    if len(parts) < 2:
        return PageStatus(page, ERROR, f"page sits directly in {config['wiki_dir']}/")

    wiki_name = parts[0]
    if wiki_name == MASTER_WIKI:
        return PageStatus(page, ERROR, "master pages describe a domain, not one repository")

    ref = get_repo(config, wiki_name)
    if ref is None:
        return PageStatus(page, ERROR, f"no repository registered for '{wiki_name}'")

    repo = root / ref.path
    if not is_checked_out(repo):
        return PageStatus(page, ERROR, f"{ref.path} is not checked out")
    if not has_commit(repo, verified):
        return PageStatus(page, ERROR, f"commit {verified} not found in {ref.name}")

    commits = commits_touching(repo, verified, covers)
    if commits is None:
        return PageStatus(page, ERROR, "git log failed")
    if not commits:
        return PageStatus(page, FRESH, f"nothing under covers since {verified}")
    return PageStatus(page, SUSPECT, f"{len(commits)} commit(s) since {verified}", len(commits))


def has_master(root: Path, config: dict) -> bool:
    """Whether this workspace keeps a master wiki.

    It is optional, and pointless with a single repository: cross-cutting
    knowledge needs at least two things to cut across.
    """
    return (root / config["wiki_dir"] / MASTER_WIKI).is_dir()


def check_drift(root: Path, ref: RepoRef) -> tuple[int | None, str | None]:
    """How far a checkout is behind its remote: (count, branch).

    A count of None means *unknown*, and the caller must not report it as zero.
    A pinned submodule nobody updated is the quiet way for every page above it
    to look fresh against months-old code.
    """
    repo = root / ref.path
    if not is_checked_out(repo):
        return None, None

    branch = remote_branch(repo, ref.branch)
    if branch is None:
        return None, None

    return count_behind(repo, branch), branch
