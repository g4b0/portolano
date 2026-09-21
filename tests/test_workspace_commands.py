"""init / add / remove / stale: the workspace is built and torn down cleanly."""

from __future__ import annotations

import subprocess

import pytest

from helpers import commit_all, git, head
from portolano import cli, core


def test_init_creates_the_router_but_no_master(workspace):
    """A master wiki is meaningless with one repository, so init does not make one."""
    assert (workspace / "AGENTS.md").is_file()
    assert (workspace / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    for name in ("index.md", "README.md", "CHANGELOG.md"):
        assert (workspace / "wiki" / "backend" / name).is_file()
    assert not (workspace / "wiki" / "_master").exists()
    assert "The master wiki" not in (workspace / "AGENTS.md").read_text()


def test_add_registers_repo_wiki_and_router(workspace):
    config = core.load_config(workspace)
    assert config["repos"]["backend"]["path"] == "repos/backend"
    assert (workspace / "repos" / "backend" / "src").is_dir()
    assert (workspace / "wiki" / "backend" / "index.md").is_file()
    assert "repos/backend" in (workspace / "AGENTS.md").read_text()


def test_add_refuses_a_duplicate_name(workspace, upstream, capsys):
    try:
        cli.main(["add", str(upstream), "--name", "backend"])
    except SystemExit as exc:
        assert "already registered" in str(exc.code)
    else:
        raise AssertionError("expected the duplicate to be refused")


def test_remove_undoes_everything(workspace):
    cli.main(["remove", "backend", "--yes"])
    assert "backend" not in core.load_config(workspace)["repos"]
    assert not (workspace / "repos" / "backend").exists()
    assert not (workspace / "wiki" / "backend").exists()
    assert "repos/backend" not in (workspace / "AGENTS.md").read_text()


def test_stale_warns_when_the_checkout_is_behind(workspace, upstream, page, capsys):
    """A pinned submodule can make a page look fresh against months-old code."""
    before = head(upstream)
    (upstream / "src" / "services" / "notification" / "dispatch.py").write_text("x = 3\n")
    commit_all(upstream, "moved on")
    subprocess.run(["git", "fetch", "-q", "origin"], cwd=workspace / "repos" / "backend", check=True)

    page(before, "src/services/notification/**")
    cli.main(["stale"])
    assert "behind origin/main" in capsys.readouterr().out


def test_drift_reports_unknown_rather_than_zero(tmp_path):
    """Not knowing must never be reported as being up to date."""
    repo = tmp_path / "loose"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    assert core.remote_branch(repo) is None


def test_second_repo_can_create_the_master_wiki(workspace, tmp_path):
    """The offer arrives with the second repository, not before."""
    other = tmp_path / "other"
    (other / "src").mkdir(parents=True)
    (other / "src" / "b.py").write_text("b = 1\n")
    git("init", "-q", "-b", "main", cwd=other)
    git("config", "user.email", "t@example.com", cwd=other)
    git("config", "user.name", "Test", cwd=other)
    commit_all(other, "initial")

    cli.main(["add", str(other), "--name", "frontend", "--master"])

    for name in ("index.md", "README.md", "CHANGELOG.md"):
        assert (workspace / "wiki" / "_master" / name).is_file()
    agents = (workspace / "AGENTS.md").read_text()
    assert "The master wiki" in agents
    assert "*(cross-cutting)*" in agents


def test_no_master_flag_keeps_the_workspace_flat(workspace, tmp_path):
    other = tmp_path / "other2"
    (other / "src").mkdir(parents=True)
    (other / "src" / "c.py").write_text("c = 1\n")
    git("init", "-q", "-b", "main", cwd=other)
    git("config", "user.email", "t@example.com", cwd=other)
    git("config", "user.name", "Test", cwd=other)
    commit_all(other, "initial")

    cli.main(["add", str(other), "--name", "worker", "--no-master"])

    assert not (workspace / "wiki" / "_master").exists()
    assert "*(cross-cutting)*" not in (workspace / "AGENTS.md").read_text()


def test_master_command_creates_it_on_demand(workspace):
    """A single-repository workspace can still opt in, at any time."""
    assert not (workspace / "wiki" / "_master").exists()

    cli.main(["master"])

    for name in ("index.md", "README.md", "CHANGELOG.md"):
        assert (workspace / "wiki" / "_master" / name).is_file()
    assert "The master wiki" in (workspace / "AGENTS.md").read_text()


def test_master_command_is_idempotent_and_repairs_the_router(workspace):
    cli.main(["master"])
    agents = workspace / "AGENTS.md"

    # someone edits the generated block by hand
    agents.write_text(agents.read_text().replace("## The master wiki", "## Gone"))
    cli.main(["master"])

    assert "## The master wiki" in agents.read_text()
    assert "## Gone" not in agents.read_text()


def test_local_rules_are_optional_but_announced(workspace):
    """portolano does not create the file; AGENTS.md tells the agent to read it if present."""
    assert not (workspace / "AGENTS.local.md").exists()
    agents = (workspace / "AGENTS.md").read_text()
    assert "AGENTS.local.md" in agents
    assert "if the project has one" in agents
    assert "it wins" in agents


def test_agents_md_carries_the_whole_format_offline(workspace):
    """No external link: a local agent with no network must still have the rules."""
    agents = (workspace / "AGENTS.md").read_text()
    assert "http" not in agents
    for rule in ("verified-at", "related:", "[[wikilinks]]", "Mermaid", "One page answers one question"):
        assert rule in agents


def test_ptl_never_touches_local_rules(workspace, tmp_path):
    local = workspace / "AGENTS.local.md"
    local.write_text("# mine\n\nNever commit on Fridays.\n")

    other = tmp_path / "third"
    (other / "src").mkdir(parents=True)
    (other / "src" / "d.py").write_text("d = 1\n")
    git("init", "-q", "-b", "main", cwd=other)
    git("config", "user.email", "t@example.com", cwd=other)
    git("config", "user.name", "Test", cwd=other)
    commit_all(other, "initial")

    cli.main(["add", str(other), "--name", "third", "--no-master"])
    cli.main(["master"])

    assert local.read_text() == "# mine\n\nNever commit on Fridays.\n"


def test_index_has_a_read_first_section_outside_the_markers(workspace):
    """Conventions are pages; the index is where the mandatory ones are named."""
    index = (workspace / "wiki" / "backend" / "index.md").read_text()
    assert "## Read first" in index
    before_markers = index.split("<!-- portolano:index -->")[0]
    assert "## Read first" in before_markers


def test_wiki_readme_does_not_hold_rules(workspace):
    readme = (workspace / "wiki" / "backend" / "README.md").read_text()
    assert "Local conventions" not in readme
    assert "index.md" in readme


def test_init_refuses_a_directory_that_is_not_empty(tmp_path, capsys):
    """The accident this prevents: `portolano init` in a directory full of work."""
    busy = tmp_path / "Develop"
    (busy / "my-project").mkdir(parents=True)
    (busy / "notes.txt").write_text("important\n")

    with pytest.raises(SystemExit) as exc:
        cli.main(["init", str(busy)])

    assert "is not empty" in str(exc.value)
    assert not (busy / "AGENTS.md").exists()
    assert not (busy / "portolano.yaml").exists()
    assert not (busy / ".git").exists()
    assert (busy / "notes.txt").read_text() == "important\n"


def test_init_force_allows_an_existing_project(tmp_path):
    """The single-repository shape: a wiki beside the code it describes."""
    project = tmp_path / "myapp"
    (project / "src").mkdir(parents=True)

    cli.main(["init", str(project), "--force"])

    assert (project / "AGENTS.md").is_file()
    assert (project / "src").is_dir()


def test_init_never_overwrites_an_existing_agents_md(tmp_path):
    project = tmp_path / "hasagents"
    project.mkdir()
    (project / "AGENTS.md").write_text("# mine\n")

    with pytest.raises(SystemExit) as exc:
        cli.main(["init", str(project), "--force"])

    assert "will not overwrite" in str(exc.value)
    assert (project / "AGENTS.md").read_text() == "# mine\n"


def test_bootstrap_writes_a_brief_carrying_the_measurement_and_the_commit(workspace):
    """The brief's whole contribution is what git can answer and an agent cannot."""
    cli.main(["bootstrap"])

    brief = (workspace / "briefs" / "backend.md").read_text()
    assert "`repos/backend`" in brief
    assert core.head_commit(workspace / "repos" / "backend") in brief
    assert "`src`" in brief


def test_bootstrap_skips_a_wiki_whose_readme_is_written(workspace, capsys):
    """The README is what a bootstrap fills in, so a written one means the job is done."""
    readme = workspace / "wiki" / "backend" / "README.md"
    readme.write_text("# backend\n\nThe billing service.\n")
    cli.main(["bootstrap"])

    assert not (workspace / "briefs" / "backend.md").exists()
    assert "README.md already written" in capsys.readouterr().out


def test_briefs_ignore_themselves(workspace):
    """Briefs are spent instructions, so the directory keeps them out of git."""
    cli.main(["bootstrap"])
    assert "*" in (workspace / "briefs" / ".gitignore").read_text()


def test_bootstrap_flies_higher_over_a_bigger_repository(workspace, monkeypatch):
    """Size decides the altitude, so two runs on one repository agree."""
    monkeypatch.setattr(core, "survey", lambda repo, skip=None: (9000, ["src"]))
    cli.main(["bootstrap"])
    assert "Ten thousand metres" in (workspace / "briefs" / "backend.md").read_text()

    monkeypatch.setattr(core, "survey", lambda repo, skip=None: (12, ["src"]))
    cli.main(["bootstrap", "--force"])
    assert "Low pass" in (workspace / "briefs" / "backend.md").read_text()


def test_bootstrap_skips_a_wiki_that_already_has_pages(workspace, page, capsys):
    """Writing the first page is the job; it is not a way to regenerate one."""
    page("abc1234", "src/**")
    cli.main(["bootstrap"])

    assert not (workspace / "briefs" / "backend.md").exists()
    assert "skipped" in capsys.readouterr().out

    cli.main(["bootstrap", "--force"])
    assert (workspace / "briefs" / "backend.md").exists()


def test_bootstrap_covers_every_wiki_in_one_run(workspace, upstream):
    """A workspace of several repositories is bootstrapped by one command."""
    cli.main(["add", str(upstream), "--name", "frontend", "--no-master"])
    cli.main(["bootstrap"])

    assert (workspace / "briefs" / "backend.md").exists()
    assert (workspace / "briefs" / "frontend.md").exists()


def test_the_master_brief_is_written_from_the_repo_wikis_not_from_the_code(workspace):
    """The master wiki spans repositories, so its evidence is their wikis."""
    cli.main(["master"])
    cli.main(["bootstrap", core.MASTER_WIKI])

    brief = (workspace / "briefs" / f"{core.MASTER_WIKI}.md").read_text()
    assert "wiki/backend/README.md" in brief
    assert "`wiki/_master/README.md`" in brief  # its own hat, filled like any other
    assert "not written yet" in brief          # it says so rather than assuming
    assert "No source code at all" in brief


def test_altitude_bands_are_continuous():
    """No file count falls between two bands."""
    assert core.altitude(core.SMALL_REPO) == core.LOW
    assert core.altitude(core.SMALL_REPO + 1) == core.CRUISING
    assert core.altitude(core.MEDIUM_REPO) == core.CRUISING
    assert core.altitude(core.MEDIUM_REPO + 1) == core.HIGH


def test_skip_keeps_vendored_code_out_of_the_measurement(workspace, upstream):
    """A tracked dependency is not this project's work, and counting it lies."""
    vendor = upstream / "vendor" / "lib"
    vendor.mkdir(parents=True)
    for i in range(30):
        (vendor / f"dep{i}.py").write_text("x = 1\n")
    commit_all(upstream, "vendor it")
    git("fetch", "-q", "origin", cwd=workspace / "repos" / "backend")
    git("checkout", "-q", head(upstream), cwd=workspace / "repos" / "backend")

    config = core.load_config(workspace)
    counted, _ = core.survey(workspace / "repos" / "backend")

    config["repos"]["backend"]["skip"] = ["vendor/**"]
    core.save_config(workspace, config)
    kept, dirs = core.survey(workspace / "repos" / "backend", ["vendor/**"])

    assert counted - kept == 30
    assert "vendor" not in dirs

    cli.main(["bootstrap"])
    brief = (workspace / "briefs" / "backend.md").read_text()
    # what was hidden is stated, so nothing is skipped behind the agent's back
    assert "`vendor/**`" in brief


def test_remove_takes_the_brief_with_it(workspace):
    """A brief names a wiki; one left behind points at something gone."""
    cli.main(["bootstrap"])
    assert (workspace / "briefs" / "backend.md").exists()

    cli.main(["remove", "backend", "-y"])
    assert not (workspace / "briefs" / "backend.md").exists()
