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

**The wiki orients; it does not paraphrase.** Its reader is a programmer or an agent, and both \
can read the code. A page that walks through what a function does duplicates something already \
readable, and goes wrong the moment the function changes. Write what the code cannot tell you: \
the concepts, the algorithm when there is one, the architecture and where one responsibility ends \
and the next begins, why it is this way, what was tried and abandoned, which trap is waiting. \
Then point at the code with `file:line` and let the reader open it.

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
matches a template. *The idea · Where it lives (`file:line`) · Gotchas · Open questions* is a \
good default when nothing better suggests itself — drop a heading with nothing under it, add one \
the subject needs.

**Write for a human first: short prose, carried by structure.** A paragraph says one thing in a \
few sentences. Where the content has a shape, give it that shape — a list for items in parallel, \
a table for a comparison, a Mermaid diagram for a flow. Which one is your judgement: a table \
nobody can read at a glance should have been two sentences, and a paragraph naming six things \
should have been a list.

What is not negotiable is the weight, not the shape. **The result instead of the investigation. \
Never pasted code — cite `file:line`.** Those two keep an agent's prose from taking the page over; \
everything else is the author's call.

**One page answers one question.** Split a page that answers two, or whose `covers` spans \
unrelated parts of the tree. Merge one that cannot be acted on without opening another. \
There is no line limit — the unit is the subject, not the length.

`covers` plus `verified-at` are what make staleness computable: run `portolano stale` to see \
which pages the code has moved out from under. **Suspect is not wrong** — re-read, fix, \
then advance `verified-at`.

**A wiki's `README.md` is its hat, and the one file meant never to change.** It says what the \
repository is — in the master wiki, what the system is — and how it divides: one line per \
top-level directory, or per repository. Nothing in it may be something a commit can make false: \
no frontmatter, no `file:line`, no file below the top level, no diagram. `index.md` links to it \
from under its title.

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

# `bootstrap` treats a README that still carries this as unwritten, so the
# placeholder and the check share one string.
README_PLACEHOLDER = "Replace this."

WIKI_README_MD = """# {title} — knowledge wiki

*(What the repository is, and one line per top-level directory. Replace this.)*

**Start at [`index.md`](index.md)** — the catalog of pages, and what to read first.
"""

CHANGELOG_MD = """# {title} — wiki changelog

- {date} — wiki created
"""

MASTER_README_BODY = """# {title} — master wiki

*Domain knowledge that spans repositories: terms, flows, invariants, boundaries.*

*(What the system does and for whom, and which repository owns what. Replace this.)*

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
# Written to `briefs/<wiki>.md` by `portolano bootstrap`. It is a prompt, not
# knowledge the workspace keeps: `portolano` makes no model calls, so the agent -
# any agent - is the one that does the work. What the command contributes is the
# measuring, which is cheap, exact, and the part an agent is worst at guessing.
#
# What it asks for is the wiki's README: a fixed file, so no frontmatter and no
# freshness contract - and therefore nothing in it a commit could make false.

ALTITUDE_LOW = """**Low pass — the repository is small enough to read.**

Read what you need to be sure what each area is for, entry points first — **at most 30 files**. \
Reading all of it is allowed; describing all of it is not. What you learn below the level of an \
area may go on up to **three** pages, one per area that genuinely stands alone, each with its \
own `covers` and `verified-at`. The README stays as short as if you had read nothing."""

ALTITUDE_CRUISING = """**Cruising altitude — too large to read, small enough to map.**

Name each top-level area and what it is for. Open **entry points only** — the manifest, the \
top-level README, the main module — and **at most 15 files**. No implementation. \
**The README, then stop.**"""

ALTITUDE_HIGH = """**Ten thousand metres — this repository will not fit in any context window.**

Name the top-level areas and nothing below them. Open **at most 5 files**: the manifest, the \
top-level README, the entry point. Read no implementation at all. **The README, then stop.**"""


BOOTSTRAP_MD = """# Bootstrap the `{wiki}` wiki

The wiki at `{wiki_path}` is empty. Your job is to fill in its **`README.md`**: what this \
repository is and how it divides, in words that stay true for as long as the project does. It is \
the wiki's landing page, and the one file in it meant never to change.

**Read `AGENTS.md` at the workspace root before you start.** It holds the page format and the \
rules for every page. The README is not a page, and this brief says where it departs from them.

## What has already been measured for you

| Measured | Value |
|---|---|
| Repository | `{repo_path}` |
| Files tracked by git | **{files}** |
| Top-level directories | {dirs} |
| Paths not counted | {skipped} |
| Commit to record as `verified-at` on any code page | `{commit}` |

{altitude}

## Four rules

1. **Write what outlives the code.** The README should never need editing unless the project \
changes course. Test every sentence: would it still be true after a year of ordinary commits? A \
file name, a function, a line number, a count, a version — each one fails, and belongs on a code \
page if anywhere.
2. **Describe what you see, never what you expect.** A framework you recognise does not tell \
you what this project did with it. A guess dressed as a fact is worse than a blank page, \
because the next reader cannot tell them apart.
3. **Spend little.** You are drawing the coastline, not sounding the harbour. Stay inside the \
file budget above, and remember that reading more does not mean writing more.
4. **Hand the gaps over; do not file them.** What you did not open, what looked wrong, what you \
could not work out: it is the most valuable thing you found and the most perishable, so it goes \
in your report to the maintainer, not in a file meant never to change.

## The file to fill

`{wiki_path}/README.md` already exists. Replace its placeholder line and keep the rest — the \
title, and the pointer to `index.md` at the bottom.

**No frontmatter.** The README is one of the wiki's three fixed files: it is not a page, it is not \
listed under `## Pages`, and it carries no `covers` or `verified-at`. That is the point — nothing in \
it should be something a commit can make false.

It answers two questions and stops:

| Question | What the answer contains |
|---|---|
| **What is this?** | what the repository is for and who it serves, in two or three sentences. What *this* project does, not what its framework does |
| **How is it laid out?** | one row per top-level directory in the table above: what it is for, in one line. Directories, not files — nothing below the top level |

That is the whole file. A dozen lines is a good README; a hundred is a code page in disguise.

## What stays out of the README

| Leave out | Why |
|---|---|
| `file:line`, and any file below the top level | `AGENTS.md` asks for them on code pages, where `verified-at` keeps them honest. The README has none, so nothing would ever tell you they moved |
| Diagrams | same reason: a diagram is covered by a `verified-at` the README does not have |
| Traps, gotchas, surprises | a code page, if the altitude allows one. Otherwise your report |
| A list of what is not documented | the index is the list of what is. The gaps go in your report |
| Stub pages | forty stubs pointing at each other are worse than one honest page |
| The story of the search | the result, not the voyage |

## When you are done

1. Link the README from `{wiki_path}/index.md`: one line under the title, above `## Read first` — \
`[README.md](README.md) — ` and what this repository is, in one line. It is the wiki's hat, there \
for any reader who wants it.
2. Append one line to `{wiki_path}/CHANGELOG.md`.
3. If you wrote code pages, add each to `## Pages` in `{wiki_path}/index.md`, inside the markers, \
reusing its `summary:` verbatim.
4. Report to the maintainer, in this order: what you did not open; what looked wrong or \
contradictory, with `file:line` — here it belongs; and **which area you would document next, \
and why**. You have just read more of this repository than anyone will for a while.
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

| Wiki | Its README |
|---|---|
{readmes}

**Read those files, then the pages each wiki's `index.md` lists — and nothing else. No source \
code at all.** The master wiki is written from the repository wikis, not from the repositories. \
If a README is not written yet, say so and stop — a master page built on a wiki that does not \
exist is a guess.

## Four rules

1. **It links down and never duplicates.** Technical detail belongs to the wiki of the \
repository that owns it. A master page with `file:line` references in it has taken somebody \
else's job.
2. **Only what spans.** If a fact is true of one repository alone, it is already in that \
repository's wiki and does not belong here.
3. **Describe what you see, never what you expect.** The repository wikis are your only \
evidence. Where two of them use the same word for different things, that disagreement **is** \
the finding — write it down rather than smoothing it over.
4. **Declare every gap.** End with the terms you could not pin down and the flows you could \
only half trace.

## What to write

**`{wiki_path}/README.md`** already exists. Replace its placeholder line and keep the rest. It is a \
fixed file — no frontmatter, no `file:line` — and it answers two questions:

| Question | What the answer contains |
|---|---|
| **What is this system?** | what the whole thing does, for whom. Two or three sentences |
| **Where do the boundaries fall?** | one row per repository: what it owns, and why the split is where it is |

**`{wiki_path}/glossary.md`**, a page, for the domain terms defined once — the part that pays for \
the master wiki. Use this frontmatter:

```yaml
---
title: {name} — glossary
slug: glossary
type: reference
status: active
summary: <one line, and it is reused verbatim in index.md>
related: []
updated: {date}
evidence: read
---
```

**No `covers`, no `verified-at`**, on either file. A business domain does not move with commits, \
so a freshness contract here would only cry wolf.

## When you are done

1. Link the README from `{wiki_path}/index.md`: one line under the title, above `## Read first` — \
`[README.md](README.md) — ` and what the system is, in one line.
2. Add the glossary to `## Pages` in the same `index.md`, inside the markers, reusing `summary:` \
verbatim.
3. Append one line to `{wiki_path}/CHANGELOG.md`.
4. Tell the maintainer which domain term deserves its own page next, and why.
"""
