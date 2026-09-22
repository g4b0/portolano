# Quickstart

A working wiki in about ten minutes.

> **Status.** `portolano` v0.2 works — `init`, `add`, `bootstrap`, `master`, `remove` and `stale` are implemented and tested. It is **not on PyPI yet**, so install it from the repository (below). `lint` and `reindex` are not written yet — the format does not depend on them.

---

## What you are about to build

A knowledge repository that is **separate from the code it describes**. The code arrives as git submodules; each one gets its own wiki; a master wiki holds what spans them.

```
my-wiki/
├── AGENTS.md            # the router — source of truth, vendor-neutral
├── CLAUDE.md            # generated adapter, never edited by hand
├── portolano.yaml       # which repos, which wikis
├── repos/               # git submodules: the code being described
│   ├── backend/
│   └── frontend/
└── wiki/
    ├── _master/         # domain knowledge that spans repos
    ├── backend/         # technical detail for one repo
    └── frontend/
```

Why the wiki lives apart from the code: **it is yours**. You can document a repository you do not own, cannot commit to, or only have read access to. Nothing has to be accepted upstream for the wiki to be useful.

---

## 1. Install

```bash
uv tool install git+https://github.com/g4b0/portolano     # or: pipx install git+...
```

The command is `portolano`. Python 3.10+, one dependency, no service, no account.

If you would rather type less, alias it — the short forms worth having are taken by other tools, so Portolano does not claim one:

```bash
alias ptl=portolano
```

## 2. Create the knowledge repository

```bash
portolano init my-wiki && cd my-wiki
```

You get `AGENTS.md` (the router), `portolano.yaml`, the generated `CLAUDE.md`, and the two empty directories. No wiki yet — a wiki is created by `portolano add`, one per repository, as the triplet `index.md` (the catalog), `README.md` (the landing page), `CHANGELOG.md` (the trace).

`init` refuses a directory that already has files in it, so a mistyped path cannot scatter a workspace over an existing project. `--force` overrides that when you know the directory is the right one and merely untidy — a `README.md` you had already written, a leftover virtualenv. Even then it will not overwrite an `AGENTS.md`, `CLAUDE.md` or `portolano.yaml` that already exists.

## 3. Add the code you want to describe

```bash
portolano add https://github.com/acme/backend.git
portolano add https://github.com/acme/frontend.git --name web
```

Each call does four things at once: clones the repo as a submodule under `repos/`, scaffolds `wiki/<name>/` with its own triplet, registers it in `portolano.yaml`, and regenerates the router's repository map so agents know which wiki governs which path.

To undo all of it:

```bash
portolano remove web            # deinits the submodule, unregisters, and asks before deleting the wiki
```

## 4. Draw the map before the detail

An empty wiki is the hardest place to start, so `portolano` does the measuring first:

```bash
portolano bootstrap                 # every wiki that is still empty
portolano bootstrap backend         # or just one
```

```
wrote briefs/backend.md
wrote briefs/frontend.md
wrote briefs/_master.md
```

One brief per wiki, in `briefs/`. Each counts the files git tracks in that repository, lists the top-level areas, and reads the commit the submodule sits on. The master wiki gets a different brief: it is written **from the repository wikis, never from the code**, so it lists their READMEs and says which ones are not written yet.

`briefs/` keeps itself out of git — a brief is a spent instruction, and the durable record is the wiki's `CHANGELOG.md`. Keep one anyway with `git add -f` if you want it.

Then read it, and change it. You know things about this repository that no measurement can see — which directory is dead, which one is the part that actually matters, what is vendored and should be skipped. A brief you have corrected costs a minute and saves an agent from carefully documenting the wrong half of the tree.

**This is the pattern, not a convenience.** `portolano` writes instructions, you approve them, the agent acts. Nothing is generated behind your back, and nothing in the workspace changes until you decide it should.

The brief sets the **altitude** from the measurement, so the agent does not decide for itself how much to read:

| Files tracked | What the agent is told |
|---|---|
| ≤ 150 | read what it needs to be sure of each area, at most 30 files, and up to three code pages besides the README |
| ≤ 1500 | name each area and what it is for, entry points only, at most 15 files |
| more | name the top-level areas, read no implementation at all, at most 5 files |

Whatever the size, the brief asks for the wiki's **`README.md`**, and asks for it **short and meant never to change**: what the repository is, and one line per top-level directory. The README is a fixed file, so it has no frontmatter — no `covers`, no `verified-at`, and nothing in it a commit could make false: no `file:line`, no diagram. What the agent did not look at, and what looked wrong, comes back to you in its report instead of going in the file. That report is your queue.

**`portolano` makes no model calls, here or anywhere.** The brief is text; your agent does the work. What the command contributes is the counting and the commit, which is what an agent guesses badly and git answers exactly.

### What should not be counted

A repository that commits its dependencies, its generated stubs or its build output measures bigger than it is, and a brief built on that number sends the agent to the wrong altitude. Say so in `portolano.yaml`:

```yaml
repos:
  backend:
    url: https://github.com/acme/backend.git
    path: repos/backend
    skip:
      - vendor/**
      - src/generated/**
```

Same `:(glob)` syntax as `covers`, and only the measurement is affected — nothing is hidden from the agent. **The brief states what was skipped**, so a page is never written by somebody who did not know half the tree was left out.

A wiki that already has pages is skipped rather than overwritten — `bootstrap` writes the first page, it does not regenerate them. `--force` says otherwise.

## 5. Write the first page

Point your agent at whatever you understand least — that is where a page is worth most. **Write about the concept, not the code**: the code is one `git grep` away, so a page earns its place with the *why*, the boundary and the trap, not with a retelling of what the functions do.

> Read `repos/backend/src/services/notification`, then write the matching page under
> `wiki/backend/` in the Portolano format. Set `verified-at` to the commit you read and
> `covers` to the paths it describes. Add it to `index.md` and append one line to `CHANGELOG.md`.

The page format is in the [format reference](format.md). The short version: full frontmatter, then whatever structure the subject asks for — *The idea · Where it lives (`file:line`) · Gotchas · Open questions* is a good default, not a schema. Pages are short prose carried by lists, tables and Mermaid diagrams where the content has that shape, and they explain the idea rather than paraphrase the code. Two rules are firm, and they are about weight rather than shape: no pasted code, and the result rather than the investigation.

## 6. Keep it true

```bash
portolano stale                 # every page whose covers moved since its verified-at
```

```
wiki/backend/notifications/dispatch.md   SUSPECT   7 commits since 4312f47
wiki/backend/queue/workers.md            fresh
```

*Suspect* is not *wrong*: the command builds the work list, you and your agent decide. Re-read, fix, advance `verified-at`. When nothing under `covers` moved there is nothing to do at all — and that case is the common one, which is the point.

Two flags worth knowing:

| Flag | What it does |
|---|---|
| `portolano stale --exit-code` | exits non-zero when anything is suspect, so it drops straight into CI |
| *(automatic)* | if a submodule checkout is behind its remote, `portolano stale` says so first. Freshness is measured against the code **you have**, and a pinned submodule can otherwise make a page look fresh against months-old source |

<details>
<summary><b>What `stale` actually runs</b></summary>

One command per page, and nothing else:

```bash
git -C repos/backend log --oneline 4312f47..HEAD -- ':(glob)src/services/notification/**'
```

Empty output means the page is fresh, non-empty means it is suspect. That is the whole mechanism — `portolano stale` loops it over every page that declares a contract and formats the result.

Worth knowing because it is what *no lock-in* means here: the wiki is plain markdown in a git repository, and the freshness check is a command you can type. If `portolano` vanished tomorrow, both would still work.

</details>

---

## The master wiki — optional

**It is not created for you.** Cross-cutting knowledge needs at least two things to cut across, so a single-repository workspace does not get one. It appears when you ask:

```bash
portolano master                 # any time, even with one repository
portolano add <url> --master     # while adding a repository
```

Adding a *second* repository also offers it once; `--no-master` declines without being asked, and `portolano master` is idempotent, so running it again just re-syncs the router.

`wiki/_master/` is for the knowledge that **belongs to no single repository**: what a domain term actually means, how a flow crosses three services, which invariants hold system-wide, why the boundaries fall where they do.

| Belongs in the master wiki | Belongs in a repo wiki |
|---|---|
| what "settlement" means in this business | how `SettlementJob` is implemented |
| the payment flow across four services | the retry policy of one client |
| why the split between backend and worker exists | the worker's queue configuration |

The rule that keeps it from becoming a second copy of everything: **the master wiki links down and never duplicates.** It carries the domain and delegates every technical detail to the repo wiki that owns it. A master page with `file:line` references in it is a master page that has taken someone else's job.

Master pages usually carry no `covers` or `verified-at` — they describe a business domain, not a directory, and business domains do not move with commits. When one does track code across repos, list the globs of every repo it spans.

---

## `AGENTS.local.md` — optional

`AGENTS.md` is **generated**, and a future `portolano upgrade` will rewrite it. Anything you add there would be lost. `AGENTS.local.md` is the seam: **`portolano` never writes it, never reads it, never touches it**, and `AGENTS.md` already tells every agent to read it if it exists and to let it win on conflict.

Create it by hand when you need it:

```markdown
# myproject — local rules

Rules for this project that `portolano` must never overwrite. `AGENTS.md` is generated and will be replaced on upgrade; this file is yours.

**Where this file disagrees with `AGENTS.md`, this file wins.** Say what you are overriding, so the next reader can tell a decision from an accident.

Commit it: these are the team's rules, not one person's preferences.

## Additions

*(none yet)*

## Overrides

*(none yet)*
```

Commit it — these are the team's rules, not one person's preferences.

⚠️ **Do not call it `AGENTS.override.md`.** That name already means something else: Codex reads the override file *instead of* `AGENTS.md`, so your router would be silently ignored.

---

## Two shapes

| Shape | What changes |
|---|---|
| **Many repos** | the layout above: one submodule and one wiki each, plus the master |
| **One repo** | the same layout with a single submodule, and no master — cross-cutting knowledge needs at least two things to cut across. Nothing else differs |

The method is the same either way. **Only the number of submodules changes.**

The workspace is always its own repository, and the code always arrives as a submodule — including when there is exactly one of it. That is what lets the wiki describe a repository you do not own, cannot commit to, or only have read access to.

Running `portolano init` *inside* the project you want to document is not a supported shape: the freshness contract measures a page against the repository registered for its wiki, and a workspace with no registered repository has nothing to measure against.

---

## Next

- [Format reference](format.md) — frontmatter, vocabularies, linking, length rules
- [Prior art](prior-art.md) — what is new here and what is not
