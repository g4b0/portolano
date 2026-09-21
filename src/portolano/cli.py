"""The command line: turn arguments into a call, and a result into text.

Nothing here decides whether a page is stale - that lives in `core`. If a change
to the freshness rule forces an edit in this file, the separation has sprung a
leak.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from . import __version__, core, templates

NAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")

# Generated instructions live here, and the directory keeps them out of git.
BRIEFS_DIR = "briefs"


def fail(message: str) -> None:
    """Stop with a message the user can act on, and no traceback."""
    sys.exit(f"error: {message}")


def require_root() -> Path:
    root = core.find_root()
    if root is None:
        fail(f"no {core.CONFIG_NAME} here or in any parent. Run `portolano init` first.")
    return root


# --------------------------------------------------------------------------
# writing files
# --------------------------------------------------------------------------

def write_triplet(wiki: Path, title: str, master: bool = False) -> None:
    """The three fixed files every wiki has: catalog, landing page, trace.

    None of them restates a rule that holds for the whole workspace - those are
    written once in AGENTS.md. These three say only what is true of this wiki.
    """
    wiki.mkdir(parents=True, exist_ok=True)

    (wiki / "index.md").write_text(templates.INDEX_MD.format(title=title), encoding="utf-8")

    readme = templates.MASTER_README_BODY if master else templates.WIKI_README_MD
    (wiki / "README.md").write_text(readme.format(title=title), encoding="utf-8")

    (wiki / "CHANGELOG.md").write_text(
        templates.CHANGELOG_MD.format(title=title, date=core.today()), encoding="utf-8"
    )


def render_repo_map(config: dict, master: bool = False) -> str:
    if not config["repos"]:
        return templates.NO_REPOS

    rows = ["| Working in | Wiki | Source |", "|---|---|---|"]
    if master:
        path = f"{config['wiki_dir']}/{core.MASTER_WIKI}/index.md"
        rows.append(f"| *(cross-cutting)* | [`{path}`]({path}) | - |")
    for ref in core.iter_repos(config):
        wiki = f"{config['wiki_dir']}/{ref.name}/index.md"
        rows.append(f"| `{ref.path}` | [`{wiki}`]({wiki}) | {ref.url} |")
    return "\n".join(rows)


def sync_router(root: Path, config: dict) -> None:
    """Rewrite the generated blocks of AGENTS.md, then regenerate CLAUDE.md."""
    agents = root / "AGENTS.md"
    text = agents.read_text(encoding="utf-8")
    master = core.has_master(root, config)

    blocks = {
        "repos": render_repo_map(config, master),
        "master": templates.MASTER_SECTION.format(wiki_dir=config["wiki_dir"]) if master else "",
    }

    for marker, body in blocks.items():
        replacement = f"<!-- portolano:{marker} -->\n{body}\n<!-- /portolano:{marker} -->"
        text, replaced = re.subn(
            rf"<!-- portolano:{marker} -->.*?<!-- /portolano:{marker} -->",
            lambda _, r=replacement: r,
            text,
            flags=re.DOTALL,
        )
        if not replaced:
            print(
                f"warning: the <!-- portolano:{marker} --> markers are missing from AGENTS.md, "
                f"so that block was not updated.",
                file=sys.stderr,
            )

    agents.write_text(text, encoding="utf-8")
    (root / "CLAUDE.md").write_text(templates.CLAUDE_MD, encoding="utf-8")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

WRITTEN_BY_INIT = ("AGENTS.md", "CLAUDE.md", core.CONFIG_NAME)


def check_target(root: Path, force: bool) -> None:
    """Refuse to scatter a workspace over a directory that is already in use.

    `--force` exists for a directory that is the right one but untidy - a
    README written in advance, a leftover virtualenv. It is not a way to run
    a workspace inside the project it documents: the code has to be a
    registered submodule for `stale` to have anything to measure against.

    The check is here because the same command run in the wrong directory is
    how somebody's work gets buried.
    """
    if (root / core.CONFIG_NAME).exists():
        fail(f"{root / core.CONFIG_NAME} already exists - this is already a workspace")

    # Never clobber a file we would write, not even with --force: there is no
    # sensible way to merge two routers, and the old one would be unrecoverable.
    for name in WRITTEN_BY_INIT:
        if (root / name).exists():
            fail(
                f"{root / name} already exists.\n"
                f"       Move or delete it first - `init` will not overwrite it."
            )

    if not root.is_dir() or force:
        return

    entries = sorted(item.name for item in root.iterdir() if not item.name.startswith("."))
    if not entries:
        return

    shown = ", ".join(entries[:4]) + (", ..." if len(entries) > 4 else "")
    fail(
        f"{root} is not empty ({len(entries)} entries: {shown}).\n"
        f"       Give a new directory - `portolano init my-wiki` - or pass --force to\n"
        f"       initialise inside an existing project."
    )


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    check_target(root, args.force)

    name = args.name or root.name
    root.mkdir(parents=True, exist_ok=True)

    (root / "AGENTS.md").write_text(
        templates.AGENTS_MD.format(
            name=name,
            no_repos=templates.NO_REPOS,
            wiki_dir="wiki",
            local_rules=templates.LOCAL_RULES,
        ),
        encoding="utf-8",
    )
    (root / core.CONFIG_NAME).write_text(
        templates.CONFIG_YAML.format(name=name), encoding="utf-8"
    )

    config = core.load_config(root)
    (root / config["wiki_dir"]).mkdir(exist_ok=True)
    (root / config["repos_dir"]).mkdir(exist_ok=True)
    (root / config["repos_dir"] / ".gitkeep").touch()
    sync_router(root, config)

    if not (root / ".git").exists():
        core.git("init", "-q", cwd=root)

    print(f"initialised Portolano wiki in {root}")
    print("  AGENTS.md          the router (source of truth)")
    print("  CLAUDE.md          generated adapter")
    print(f"  {core.CONFIG_NAME}     configuration")
    print(f"  {config['repos_dir']}/         the code, added as submodules")
    print(f"  {config['wiki_dir']}/          wikis live here, one per repository")
    print("\nnext: portolano add <git-url>")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    root = require_root()
    config = core.load_config(root)

    name = args.name or re.sub(r"\.git$", "", args.url.rstrip("/").rsplit("/", 1)[-1])
    if not NAME_RE.fullmatch(name):
        fail(f"'{name}' is not a usable wiki name (lowercase, digits, . _ -)")
    if name in config["repos"]:
        fail(f"'{name}' is already registered")

    relative = f"{config['repos_dir']}/{name}"
    result = core.git("submodule", "add", args.url, relative, cwd=root)
    if result.returncode != 0:
        fail(f"git submodule add failed:\n{result.stderr.strip()}")

    # `skip` is written empty so it is discoverable: nobody reads a field
    # that only appears in the documentation.
    entry = {"url": args.url, "path": relative, "skip": []}
    if args.branch:
        entry["branch"] = args.branch
    config["repos"][name] = entry

    core.save_config(root, config)
    write_triplet(root / config["wiki_dir"] / name, name)

    created_master = maybe_create_master(root, config, args)
    sync_router(root, config)

    print(f"added '{name}'")
    print(f"  {relative}/  submodule")
    print(f"  {config['wiki_dir']}/{name}/  wiki")
    if created_master:
        print(f"  {config['wiki_dir']}/{core.MASTER_WIKI}/  master wiki")
    print("  AGENTS.md repository map updated")
    return 0


def create_master(root: Path, config: dict) -> None:
    write_triplet(root / config["wiki_dir"] / core.MASTER_WIKI, config["name"], master=True)


def maybe_create_master(root: Path, config: dict, args: argparse.Namespace) -> bool:
    """Offer a master wiki once there is more than one repository to cut across.

    It is optional and meaningless with a single repository, so it is not created
    up front. `--master` / `--no-master` skip the question; with no terminal to
    ask on, the answer is no.
    """
    if core.has_master(root, config) or args.no_master:
        return False
    if len(config["repos"]) < 2 and not args.master:
        return False

    if not args.master:
        print(
            f"\nThis workspace now has {len(config['repos'])} repositories. A master wiki "
            f"holds what cuts across them:\nwhat a domain term means, how a flow spans "
            f"services, why the boundaries fall where they do.\nYou can always add "
            f"one later with `portolano master`."
        )
        try:
            answer = input("create one? [y/N] ")
        except EOFError:
            # No terminal and nothing piped in - a CI run, say. Do not guess yes.
            print("(no input available - skipped; use --master to create it)")
            return False
        if answer.strip().lower() != "y":
            return False

    create_master(root, config)
    return True


def cmd_master(args: argparse.Namespace) -> int:
    """Create the master wiki on demand, and re-sync the router either way.

    Running it when the master already exists is not an error: it rewrites the
    generated blocks of AGENTS.md, which also repairs a workspace where the
    directory was added or deleted by hand.
    """
    root = require_root()
    config = core.load_config(root)
    existed = core.has_master(root, config)

    if not existed:
        create_master(root, config)
    sync_router(root, config)

    where = f"{config['wiki_dir']}/{core.MASTER_WIKI}/"
    if existed:
        print(f"master wiki already at {where} — router re-synced")
    else:
        print(f"created {where}")
        print("  it holds what belongs to no single repository: domain terms,")
        print("  flows that span services, why the boundaries fall where they do")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    root = require_root()
    config = core.load_config(root)

    ref = core.get_repo(config, args.name)
    if ref is None:
        fail(f"'{args.name}' is not registered")

    wiki = root / config["wiki_dir"] / args.name
    pages = list(wiki.rglob("*.md")) if wiki.is_dir() else []

    if not args.yes:
        print(f"about to remove '{args.name}':")
        print(f"  submodule {ref.path}")
        print(f"  wiki      {config['wiki_dir']}/{args.name}/  ({len(pages)} file)")
        if input("this deletes written pages. continue? [y/N] ").strip().lower() != "y":
            print("aborted")
            return 1

    core.git("submodule", "deinit", "-f", ref.path, cwd=root)
    core.git("rm", "-f", ref.path, cwd=root)
    for doomed in (root / ".git" / "modules" / ref.path, root / ref.path, wiki):
        shutil.rmtree(doomed, ignore_errors=True)

    # A brief names a wiki. Leaving one behind for a wiki that is gone is the
    # exact defect this project exists to catch.
    brief = root / BRIEFS_DIR / f"{args.name}.md"
    brief.unlink(missing_ok=True)

    del config["repos"][args.name]
    core.save_config(root, config)
    sync_router(root, config)

    print(f"removed '{args.name}'")
    print(f"  {ref.path}/  submodule")
    print(f"  {config['wiki_dir']}/{args.name}/  wiki ({len(pages)} file)")
    print("  AGENTS.md repository map updated")
    return 0


def readme_written(root: Path, config: dict, name: str) -> bool:
    """A README is written once the placeholder `add` left in it is gone."""
    readme = root / config["wiki_dir"] / name / "README.md"
    return readme.exists() and templates.README_PLACEHOLDER not in readme.read_text(encoding="utf-8")


def wiki_pages(root: Path, config: dict, name: str) -> list[str]:
    """The pages a wiki already has, the three fixed files aside."""
    wiki = root / config["wiki_dir"] / name
    return sorted(p.name for p in wiki.glob("*.md") if p.name not in core.FIXED_FILES)


def write_brief(root: Path, name: str, text: str) -> Path:
    """Put a brief on disk, under a directory that ignores its own contents."""
    briefs = root / BRIEFS_DIR
    briefs.mkdir(exist_ok=True)
    gitignore = briefs / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(templates.BRIEFS_GITIGNORE, encoding="utf-8")

    path = briefs / f"{name}.md"
    path.write_text(text, encoding="utf-8")
    return path


def repo_brief(root: Path, config: dict, ref: core.RepoRef) -> str | None:
    """The brief for one repository's wiki, or None when git cannot answer."""
    repo = root / ref.path
    if not core.is_checked_out(repo):
        return None

    measured = core.survey(repo, ref.skip)
    commit = core.head_commit(repo)
    if measured is None or commit is None:
        return None
    files, dirs = measured

    bands = {core.LOW: templates.ALTITUDE_LOW,
             core.CRUISING: templates.ALTITUDE_CRUISING,
             core.HIGH: templates.ALTITUDE_HIGH}

    return templates.BOOTSTRAP_MD.format(
        wiki=ref.name,
        wiki_path=f"{config['wiki_dir']}/{ref.name}",
        repo_path=ref.path,
        title=ref.name,
        files=files,
        dirs=", ".join(f"`{d}`" for d in dirs) or "*(none - everything is at the top level)*",
        skipped=", ".join(f"`{g}`" for g in ref.skip) or "*(nothing - you are seeing all of it)*",
        commit=commit,
        date=core.today(),
        altitude=bands[core.altitude(files)],
    )


def master_brief(root: Path, config: dict) -> str:
    """The master wiki is written from the repo wikis, so it lists them."""
    rows = []
    for ref in core.iter_repos(config):
        readme = f"{config['wiki_dir']}/{ref.name}/README.md"
        written = readme_written(root, config, ref.name)
        rows.append(f"| `{ref.name}` | `{readme}`" + ("" if written else " — **not written yet**") + " |")

    return templates.BOOTSTRAP_MASTER_MD.format(
        wiki_path=f"{config['wiki_dir']}/{core.MASTER_WIKI}",
        name=config["name"],
        date=core.today(),
        readmes="\n".join(rows) or "| *(no repositories yet)* | |",
    )


def cmd_bootstrap(args: argparse.Namespace) -> None:
    """Write the brief that turns an empty wiki into its first page.

    No model is called here - `portolano` never calls one, and never writes
    inside `wiki/`. What this adds to a prompt the user could have typed is the
    measuring: the file count, the areas, the exact commit. Those are the three
    things an agent guesses badly and git answers exactly.
    """
    root = require_root()
    config = core.load_config(root)

    wikis = [ref.name for ref in core.iter_repos(config)]
    if core.has_master(root, config):
        wikis.append(core.MASTER_WIKI)
    if not wikis:
        fail("no wikis yet - add a repository with `portolano add <git-url>`")

    if args.wiki:
        if args.wiki not in wikis:
            fail(f"no wiki named {args.wiki!r}. Known: " + ", ".join(wikis))
        wikis = [args.wiki]

    written, skipped = [], []
    for name in wikis:
        pages = wiki_pages(root, config, name)
        if pages and not args.force:
            skipped.append(f"{name} (has {len(pages)} page(s): {', '.join(pages[:3])})")
            continue
        if readme_written(root, config, name) and not args.force:
            skipped.append(f"{name} (README.md already written)")
            continue

        if name == core.MASTER_WIKI:
            text = master_brief(root, config)
        else:
            ref = core.get_repo(config, name)
            text = repo_brief(root, config, ref)
            if text is None:
                skipped.append(f"{name} (not checked out - run `git submodule update --init`)")
                continue

        written.append(write_brief(root, name, text).relative_to(root))

    for path in written:
        print(f"wrote {path}")
    for note in skipped:
        print(f"skipped {note}")

    if written:
        print("\nRead each brief, correct what only you know, then hand it to your agent.")
    elif skipped:
        print("\nNothing to write. Pass --force to rewrite a brief for a wiki already written.")


def cmd_stale(args: argparse.Namespace) -> int:
    root = require_root()
    config = core.load_config(root)

    statuses = [core.page_status(page, root, config) for page in core.iter_pages(root, config, args.wiki)]
    if not statuses:
        print("no pages yet")
        return 0

    for ref in core.iter_repos(config):
        if args.wiki and ref.name != args.wiki:
            continue
        behind, branch = core.check_drift(root, ref)
        if behind is None:
            print(
                f"warning: cannot tell whether {ref.path} is up to date - no remote "
                f"branch resolved.\n         freshness below reflects the local "
                f"checkout only.\n"
            )
        elif behind:
            print(
                f"warning: {ref.path} is {behind} commit(s) behind {branch} - "
                f"freshness below reflects the local checkout.\n"
                f"         run `git -C {ref.path} pull` before trusting it.\n"
            )

    rank = {core.SUSPECT: 0, core.ERROR: 1, core.NO_CONTRACT: 2, core.FRESH: 3}
    width = max(len(str(s.page.relative_to(root))) for s in statuses)

    for status in sorted(statuses, key=lambda s: (rank[s.state], str(s.page))):
        if args.suspect_only and status.state != core.SUSPECT:
            continue
        label = status.state.upper() if status.state == core.SUSPECT else status.state
        page = str(status.page.relative_to(root))
        print(f"{page:<{width}}  {label:<11}  {status.detail}")

    counts = {state: 0 for state in rank}
    for status in statuses:
        counts[status.state] += 1

    print(
        f"\n{counts[core.SUSPECT]} suspect, {counts[core.FRESH]} fresh, "
        f"{counts[core.NO_CONTRACT]} without contract, {counts[core.ERROR]} error"
    )
    if counts[core.SUSPECT]:
        print("\nsuspect is not wrong: re-read those commits, fix the page,")
        print("then advance verified-at to the commit you checked against.")

    return 1 if counts[core.SUSPECT] and args.exit_code else 0


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portolano", description="Portolano - project knowledge that knows when it went stale."
    )
    parser.add_argument("--version", action="version", version=f"portolano {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="scaffold a Portolano knowledge repository")
    init.add_argument("directory", nargs="?", default=".")
    init.add_argument("--name", help="project name (default: directory name)")
    init.add_argument(
        "--force", action="store_true", help="allow a directory that is not empty"
    )
    init.set_defaults(func=cmd_init)

    add = sub.add_parser("add", help="add a repository as a submodule, with its wiki")
    add.add_argument("url")
    add.add_argument("--name", help="wiki name (default: from the URL)")
    add.add_argument("--branch", help="remote branch to measure freshness against")
    master = add.add_mutually_exclusive_group()
    master.add_argument("--master", action="store_true", help="create the master wiki now")
    master.add_argument("--no-master", action="store_true", help="never ask about it")
    add.set_defaults(func=cmd_add)

    remove = sub.add_parser("remove", help="remove a repository, its submodule and its wiki")
    remove.add_argument("name")
    remove.add_argument("-y", "--yes", action="store_true", help="skip the confirmation")
    remove.set_defaults(func=cmd_remove)

    master_cmd = sub.add_parser("master", help="create the master wiki, or re-sync the router")
    master_cmd.set_defaults(func=cmd_master)

    boot = sub.add_parser("bootstrap", help="write the brief for a wiki's first page")
    boot.add_argument("wiki", nargs="?", help="which wiki (default: the only one)")
    boot.add_argument("--force", action="store_true", help="write it even if the wiki has pages")
    boot.set_defaults(func=cmd_bootstrap)

    stale = sub.add_parser("stale", help="list pages whose covers moved since verified-at")
    stale.add_argument("wiki", nargs="?", help="restrict to one wiki")
    stale.add_argument("--suspect-only", action="store_true", help="hide the fresh pages")
    stale.add_argument("--exit-code", action="store_true", help="exit 1 if anything is suspect")
    stale.set_defaults(func=cmd_stale)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
