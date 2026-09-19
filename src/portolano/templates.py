"""File templates written by `portolano init` and `portolano add`.

Kept as plain strings on purpose: the format is the product, so it has to be
readable here without a template engine in the way.

**Where each rule lives.** A rule that holds for the whole workspace is written
once, in `AGENTS.md`. The three files of a wiki triplet carry only what is true
of *that* wiki. Repeating the changelog convention in every `CHANGELOG.md` is the
same mistake this project exists to prevent: one fact, many copies, and they
drift the first time one of them is edited.

**A note on the backslashes.** Generated markdown must have one paragraph per
line: hard-wrapped prose is awkward to read and worse to edit in any editor that
soft-wraps, and a one-word change reflows the whole paragraph in the diff. But a
200-character string literal is unreadable here. A `\\` at the end of a line
inside a triple-quoted string swallows the newline, so the source stays in a
column and the output comes out on a single line.
"""

# The file users put their own rules in. `portolano` writes it once and never touches
# it again, so an upgrade can rewrite AGENTS.md without destroying anyone's work.
LOCAL_RULES = "AGENTS.local.md"

# The empty-state line for the repository map. Lives here because `portolano add`
# regenerates that block: two copies of the same sentence would drift apart, and
# this file is the one that owns the wording.
NO_REPOS = "*(no repositories yet — add one with `portolano add <git-url>`)*"


AGENTS_MD = """# {name} — repository map and wiki router

**This file is a router, not a manual.** It says which code you are in and which wiki \
governs it, and it holds the rules that apply everywhere. Everything project-specific — \
domain knowledge, gotchas, how a subsystem works — lives in the wiki, never here.

**The wiki describes concepts, not code.** The code is right there and you can read it, so a \
page that narrates what a function does is a page that will be wrong next month and was never \
worth the tokens. Write what reading the code cannot tell you: why it is this way, what was \
tried and abandoned, where one responsibility ends and the next begins, which trap is waiting. \
Point at the code with `file:line` and let the reader open it.

## Repository map

<!-- portolano:repos -->
{no_repos}
<!-- /portolano:repos -->

## Working rules

1. **Read the relevant `index.md` first.** It is the catalog — use it to find the page \
instead of scanning source. Subagents must read it themselves; they do not inherit your reads.
2. **If no page covers what you looked for, say so explicitly in your reply.** Treat \
unlisted areas as undocumented, not as absent.
3. **Update the wiki in the same session**, the way you would update a test — including \
for facts you learned incidentally and were not asked about. Never leave a durable \
finding only in the chat.
4. **The index mirrors the wiki.** Every page is listed under `## Pages` in that wiki's \
`index.md`, **inside the `<!-- portolano:index -->` markers**, on one line reusing its \
`summary:` verbatim. A new page is not finished until it is listed: by rule 2, an unlisted page \
does not exist.
5. **Removing a page is not finished either, until the index agrees.** Delete the entry with the \
file, move it with the file, rewrite it when the `summary:` changes — then drop the slug from \
every `related:` that named it, and from **Read first** if it was there. An entry pointing at a \
page that is gone costs more than the page ever did.
6. **Point at code, never copy it.** A `file:line` reference survives the file changing \
under it; a pasted snippet goes wrong silently, and nothing will ever tell you.

## Page contract

Every page except `index.md`, `README.md` and `CHANGELOG.md` opens with YAML frontmatter:

```yaml
title:       human title
slug:        path within the wiki, minus .md
type:        overview | reference | analysis | plan | proposal | audit | estimate | tdd
status:      active | draft | superseded | archived
summary:     one line, reused verbatim in index.md
updated:     date of the last content change
related:     [slugs of neighbouring pages]
covers:      [globs of the source paths this page describes]   # code pages
verified-at: the commit this page was last checked against     # code pages
evidence:    read | inferred | run                             # recommended
```

Body: **no fixed structure.** A page a human wants to edit is worth more than a page that \
matches a template. *What it does · Where it lives (`file:line`) · Gotchas · Open questions* is a \
good default when nothing better suggests itself — drop a heading with nothing under it, add one \
the subject needs.

What is not negotiable is the weight, not the shape. **Tables and lists instead of paragraphs. \
The result instead of the investigation. Never pasted code — cite `file:line`.** Those three are \
the guardrail that keeps an agent's prose from taking the page over; everything above them is \
the author's call.

**One page answers one question.** Split a page that answers two, or whose `covers` spans \
unrelated parts of the tree. Merge one that cannot be acted on without opening another. \
There is no line limit — the unit is the subject, not the length.

`covers` plus `verified-at` are what make staleness computable: run `portolano stale` to see \
which pages the code has moved out from under. **Suspect is not wrong** — re-read, fix, \
then advance `verified-at`.

## Linking

`related:` is the link graph, kept **inside the page** so it is edited with the content \
and cannot drift away from it. Keep it roughly reciprocal: if A lists B, B usually lists A.

In prose use **relative markdown links** — `./sibling.md`, `../other-domain/page.md`. \
**Never `[[wikilinks]]`**: they need tooling to resolve, and none is required here.

## Diagrams

Optional, but they earn their place wherever something crosses a boundary — an external \
integration, a flow across services. Use **Mermaid inside the page**: it renders without a \
build step and, being text, it diffs in git. Draw the interaction, not the class hierarchy, \
and put the trap in the diagram. A diagram is part of the page, so the same `verified-at` \
covers it.

## Changelog

One line per change in the wiki's `CHANGELOG.md`: `DATE slug what changed (why)`, under \
~200 characters. If a finding needs more room it belongs in a page, and the changelog \
links to it.

## Where a rule lives

Two different kinds of rule, and they do not go in the same place.

| Kind | Where it belongs |
|---|---|
| **How the wiki works** — the page contract, the protocol above | this file. It is about the wiki, not about the code |
| **What is true of the code** — stack, versions, conventions, constraints | the wiki, never this file |

Knowledge about the code is layered, and **the narrower layer wins**: where a general page \
and the page that owns a specific area disagree, the owning page is right for that area. \
State the exception where it applies, and name what it overrides.

**Conventions live in pages, not in preambles.** A code style, a testing rule, a constraint \
that holds for one area — it goes in a page with full frontmatter, so it carries `covers` and \
`verified-at` like everything else. A convention buried in a README cannot be checked for \
staleness, and conventions go stale like any other claim about the code.

**How many pages is your call.** One `conventions.md` for the whole wiki is a perfectly good \
answer; so is one page per area, when the areas really do differ. **One page answers one \
question** above is the only arbiter.

Each wiki's `index.md` has two sections: **Read first**, the pages that must be read before \
writing code in that area, and **Pages**, the catalog of everything else. Keep **Read \
first** short — it is read every session, so a long one makes every session more expensive \
— and add a convention page to it the moment you write one.

<!-- portolano:master -->
<!-- /portolano:master -->
## Reading order

1. **This file** — you already have it; it is the whole format, nothing to fetch.
2. **[`{local_rules}`]({local_rules}), if the project has one** — rules written by hand and never \
touched by `portolano`, so they survive upgrades. **Where it disagrees with this file, it wins.**
3. **The `index.md` of the wiki that governs what you are about to touch**, including \
everything it lists under **Read first** — before writing any code or any page.
"""

CLAUDE_MD = "@AGENTS.md\n"

CONFIG_YAML = """# Portolano configuration. `portolano` reads and rewrites this file.
name: {name}
wiki_dir: wiki
repos_dir: repos

# Populated by `portolano add`: maps a wiki to the repository it describes.
repos: {{}}
"""

INDEX_MD = """# {title} — wiki index

## Read first

*(none yet)*

## Pages

<!-- portolano:index -->
*(no pages yet)*
<!-- /portolano:index -->
"""

WIKI_README_MD = """# {title} — knowledge wiki

*(What this wiki covers, in a line or two. Replace this.)*

**Start at [`index.md`](index.md)** — the catalog of pages, and what to read first.
"""

CHANGELOG_MD = """# {title} — wiki changelog

- {date} — wiki created
"""

MASTER_README_BODY = """# {title} — master wiki

*Domain knowledge that spans repositories: terms, flows, invariants, boundaries.*

**Start at [`index.md`](index.md).**
"""


# Injected into AGENTS.md only once a master wiki exists. Kept out of the base
# template so a single-repository workspace never mentions a directory it has not
# got.
MASTER_SECTION = """## The master wiki

`{wiki_dir}/_master/` holds what belongs to no single repository: what a domain term \
means, how a flow crosses several services, why the boundaries fall where they do. It \
**links down and never duplicates** — technical detail belongs to the wiki of the \
repository that owns it, and that wiki overrides the master where they disagree.

"""


# ---------------------------------------------------------------------------
# The bootstrap brief
# ---------------------------------------------------------------------------
# Printed by `portolano bootstrap`, never written to disk. It is a prompt, not a
# file the workspace keeps: `portolano` makes no model calls, so the agent - any
# agent - is the one that does the work. What the command contributes is the
# measuring, which is cheap, exact, and the part an agent is worst at guessing.

ALTITUDE_LOW = """**Low pass — the repository is small enough to read.**

Open the entry point of each area and say what it does. Read **at most 30 files**. If the \
repository turns out to be smaller still, you may write up to **three** more pages after the \
overview, one per area that genuinely stands alone."""

ALTITUDE_CRUISING = """**Cruising altitude — too large to read, small enough to map.**

Name each top-level area and where its responsibility ends. Open **entry points only** — the \
manifest, the routes, the main module — and **at most 15 files**. No implementation. \
**One page, then stop.**"""

ALTITUDE_HIGH = """**Ten thousand metres — this repository will not fit in any context window.**

Name the top-level areas and nothing below them. Open **at most 5 files**: the manifest, the \
top-level README, the entry point. Read no implementation at all. **One page, then stop.**"""


BOOTSTRAP_MD = """# Bootstrap the `{wiki}` wiki

The wiki at `{wiki_path}` is empty. Your job is to write its **first page**: a map of the \
territory, not a description of it.

**Read `AGENTS.md` at the workspace root before you start.** It holds the page format and the \
rules that apply to every page; none of it is repeated here.

## What has already been measured for you

| Measured | Value |
|---|---|
| Repository | `{repo_path}` |
| Files tracked by git | **{files}** |
| Top-level directories | {dirs} |
| Paths not counted | {skipped} |
| Commit to record as `verified-at` | `{commit}` |

{altitude}

## Four rules

1. **Describe what you see, never what you expect.** A framework you recognise does not tell \
you what this project did with it. If you did not open the file, name it and say it is \
undocumented — that is a useful sentence. A guess dressed as a fact is worse than a blank page, \
because the next reader cannot tell them apart.
2. **Spend little.** You are drawing the coastline, not sounding the harbour. Stay inside the \
file budget above; when you reach it, stop and write what you have.
3. **Structure, then hand over.** Your output is a map the maintainer uses to decide what to \
document next. Finding the areas is the work. Explaining them is theirs.
4. **Declare every gap.** End the page with what you did not look at and what you could not \
work out. An honest list of holes is the most valuable thing a first page contains.

## The page to write

`{wiki_path}/overview.md`, with this frontmatter:

```yaml
---
title: {title} — overview
slug: overview
type: overview
status: active
summary: <one line, and it is reused verbatim in index.md>
related: []
updated: {date}
evidence: read
verified-at: {commit}
covers: [<see below>]
---
```

**`covers` is not `**`.** A page that claims the whole tree is suspect after every commit, which \
is the same as being suspect never. List the few files that change when the *shape* changes — \
the build manifest, the dependency file, the top-level config. If this repository has none, \
leave `covers` and `verified-at` out entirely: a page with no freshness contract is honest, a \
contract that cries wolf is not.

The body answers three questions and stops:

| Question | What the answer contains |
|---|---|
| **What is this?** | what the repository is for, in two or three sentences. Not what the framework does — what *this* project does with it |
| **How is it laid out?** | one row per top-level area: its name, what lives there, and where its responsibility ends. This is the part that has to be right |
| **What is not documented yet?** | the areas you flew over, the questions you could not answer, anything that looked surprising and went unexplained |

## When the page is written

1. Add it to `## Pages` in `{wiki_path}/index.md`, inside the markers, reusing `summary:` verbatim.
2. Append one line to `{wiki_path}/CHANGELOG.md`.
3. Tell the maintainer **which area you would document next, and why** — you have just read more \
of this repository than anyone will for a while.

## What not to do

| Do not | Why |
|---|---|
| Do not write stub pages | forty stubs pointing at each other are worse than one honest page |
| Do not paste code | cite `file:line` |
| Do not narrate the search | the result, not the voyage |
| Do not invent a `verified-at` | it is in the table above |
"""


# `briefs/` holds spent instructions, not knowledge: the wiki is the product and
# its CHANGELOG is the record. A .gitignore inside the directory keeps the
# decision self-contained - `init` does not have to write one at the root, and a
# brief worth keeping can still be committed with `git add -f`.
BRIEFS_GITIGNORE = """# Briefs are scratch: regenerate them with `portolano bootstrap`.
# Keeping one is fine - `git add -f briefs/<name>.md`.
*
!.gitignore
"""


BOOTSTRAP_MASTER_MD = """# Bootstrap the master wiki

`{wiki_path}/` holds what belongs to **no single repository**: what a domain term means, how a \
flow crosses several services, which invariants hold system-wide, why the boundaries fall where \
they do.

**Read `AGENTS.md` at the workspace root before you start.** It holds the page format and the \
rules that apply to every page; none of it is repeated here.

## What you read, and what you do not

| Wiki | Its overview |
|---|---|
{overviews}

**Read those pages and nothing else. No source code at all.** The master wiki is written from \
the repository wikis, not from the repositories. If one of them has no overview yet, say so and \
stop — a master page built on a wiki that does not exist is a guess.

## Four rules

1. **It links down and never duplicates.** Technical detail belongs to the wiki of the \
repository that owns it. A master page with `file:line` references in it has taken somebody \
else's job.
2. **Only what spans.** If a fact is true of one repository alone, it is already in that \
repository's wiki and does not belong here.
3. **Describe what you see, never what you expect.** The repository overviews are your only \
evidence. Where two of them use the same word for different things, that disagreement **is** \
the finding — write it down rather than smoothing it over.
4. **Declare every gap.** End with the terms you could not pin down and the flows you could \
only half trace.

## The page to write

`{wiki_path}/overview.md`, with this frontmatter:

```yaml
---
title: {name} — domain overview
slug: overview
type: overview
status: active
summary: <one line, and it is reused verbatim in index.md>
related: []
updated: {date}
evidence: read
---
```

**No `covers`, no `verified-at`.** A business domain does not move with commits, so a freshness \
contract here would only cry wolf. Leave both out.

The body answers three questions and stops:

| Question | What the answer contains |
|---|---|
| **What is this system?** | what the whole thing does, for whom. Two or three sentences |
| **What do the words mean?** | the domain terms, defined once. This is the part that pays for the page |
| **Where do the boundaries fall?** | which repository owns what, and why the split is where it is |

## When the page is written

1. Add it to `## Pages` in `{wiki_path}/index.md`, inside the markers, reusing `summary:` verbatim.
2. Append one line to `{wiki_path}/CHANGELOG.md`.
3. Tell the maintainer which domain term deserves its own page next, and why.
"""
