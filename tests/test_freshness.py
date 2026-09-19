"""The freshness contract: does a page know when it stopped being true?"""

from __future__ import annotations

from helpers import commit_all, head
from portolano import core


def status_of(root, target):
    return core.page_status(target, root, core.load_config(root))


def test_fresh_when_nothing_moved(workspace, upstream, page):
    target = page(head(upstream), "src/services/notification/**")
    assert status_of(workspace, target).state == core.FRESH


def test_suspect_when_covered_code_moves(workspace, upstream, page, pull):
    before = head(upstream)
    (upstream / "src" / "services" / "notification" / "dispatch.py").write_text("x = 2\n")
    commit_all(upstream, "change dispatch")
    pull()

    result = status_of(workspace, page(before, "src/services/notification/**"))
    assert result.state == core.SUSPECT
    assert result.commits == 1


def test_unrelated_change_leaves_the_page_fresh(workspace, upstream, page, pull):
    """This is what `covers` buys: only the declared paths count."""
    before = head(upstream)
    (upstream / "src" / "other" / "thing.py").write_text("y = 2\n")
    commit_all(upstream, "unrelated")
    pull()

    result = status_of(workspace, page(before, "src/services/notification/**"))
    assert result.state == core.FRESH


def test_page_without_a_contract_is_reported_as_such(workspace):
    target = workspace / "wiki" / "backend" / "plain.md"
    target.write_text("# no frontmatter\n")
    assert status_of(workspace, target).state == core.NO_CONTRACT


def test_unknown_commit_is_an_error_not_a_crash(workspace, page):
    result = status_of(workspace, page("deadbee", "src/**"))
    assert result.state == core.ERROR
    assert "deadbee" in result.detail


def test_master_page_with_a_contract_is_an_error(workspace, page):
    """A master page describes a domain; it has no single repository to check."""
    result = status_of(workspace, page("abc1234", "src/**", wiki="_master", name="domain.md"))
    assert result.state == core.ERROR
    assert "master" in result.detail
