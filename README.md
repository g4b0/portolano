# Portolano

**Project knowledge your coding agent writes, reads and keeps honest — and that knows when it has gone out of date.**

> A *portolano* was the book of sailing directions: what you see from the deck, where the shoals are, which bearing to hold. Portolan charts were the first maps drawn from real compass bearings instead of theory — made by sailors who had already sailed that coast, for the ones who would sail it next.
>
> **Your codebase is the coast. Portolano is the book the last crew left you.**

---

## The problem, in one paragraph

An agent can read your code. It cannot read *why* the code is that way, what was tried and abandoned, which deploy step bites, or where one module's responsibility ends. So every session pays to re-derive what it can, and guesses the rest. The usual fix — a `CLAUDE.md` or `AGENTS.md` describing the project — rots: Treude and Baltes call this **context rot**, *"the gradual divergence between what a configuration file says about a codebase, its tools, its architecture, or its conventions, and what actually holds"*, and found stale references in **23% of 356 sampled repositories** ([arXiv:2606.09090](https://arxiv.org/abs/2606.09090)).

Portolano's answer is one idea: **every page records the commit it was checked against and the paths it describes.** Staleness stops being a virtue you're supposed to remember and becomes a query you can run.

---

## What it's for

Three payoffs, and the third is the one that pays for the other two.

| Who gains | What they get |
|---|---|
| **For the agent** | it reads an index and one page instead of grepping its way across the repository. The knowledge is already distilled, so it does not re-derive it every session |
| **For you** | one place to look. Point your editor at the wiki root and the code sits underneath it as submodules — wiki and source open in the same window, in the same search |
| **For the project** | documentation that is *organised* rather than *accumulated*: a catalog, one page per subject, and a rule for when each page stops being true |

**The token argument is the concrete one.** Re-deriving how a subsystem works costs thousands of tokens and produces nothing durable; reading a page costs a few hundred and the page stays. Measured on the same four queries against the same domain, a persistent knowledge layer used **47K tokens where a retrieval baseline used 305K** ([arXiv:2604.11243](https://arxiv.org/abs/2604.11243)).

The saving compounds, which is why the freshness contract matters: a wiki nobody trusts gets re-derived anyway, and then you have paid twice.

---

## The whole idea, in one example

A page in the wiki:

```markdown
---
title: Notification dispatch
slug: notifications/dispatch
type: reference
status: active
summary: How queued notifications are fanned out to email, SMS and push.
related: [queue/workers]
updated: 2026-01-14
verified-at: 4312f47                       # the commit this was checked against
covers: [src/services/notification/**]     # what this page describes
---

# Notification dispatch

## What it does
Fans a queued notification out to every channel the user has enabled.

## Where it lives
| Concern | Location |
|---|---|
| entry point | `src/services/notification/Dispatcher.php:42` |

## Gotchas
- Retries are **not** idempotent below the channel layer — a requeue can send twice.
```

A month later, ask the page whether it is still true:

```bash
git log --oneline 4312f47..HEAD -- ':(glob)src/services/notification/**'
```

| Output | Meaning | What you do |
|---|---|---|
| empty | nothing it describes moved | nothing. Costs nothing |
| some commits | the page is **suspect**, not wrong | read them, fix the page, advance `verified-at` |

That is the entire mechanism. No service, no database, no index to host: **git is the database**, and the check is one command. Everything else in Portolano is convention around this one move.

---

## Starting from nothing

You do not write the first page by hand. `portolano bootstrap` measures every repository in the workspace — how many files git tracks, which top-level areas exist, which commit it sits on — and writes one brief per wiki into `briefs/`, each telling your agent **how high to fly**: read the entry points of a small repository, name the areas of a large one, read no implementation at all in a huge one.

It asks for one page: what the repository is, how it is laid out, and what it did not look at. That last list is the queue for everything after.

**Portolano makes no model calls, here or anywhere.** The brief is text you hand to whichever agent you use. What the command contributes is the measuring — the part an agent guesses badly and git answers exactly.

---

## Why it is built this way

| Principle | What it means in practice |
|---|---|
| **Concepts, not code** | the code is readable; a page that narrates it is rot waiting to happen. Pages hold what the code cannot say — the why, the boundary, the trap |
| **KISS, literally** | anything that would need a daemon, a server or an account is out by design |
| **Router, not manual** | the always-loaded file says *which wiki governs what*, and nothing else. Knowledge is fetched from an index on demand, not preloaded into every prompt |
| **Suspect, not repaired** | the mechanism finds candidates; the judgement stays yours. A page that was auto-corrected is a page nobody re-read |
| **Vendor-neutral** | `AGENTS.md` is the source; `CLAUDE.md` and friends are generated |
| **Not just for new code** | a page can be written today about code written five years ago. Nothing needs to have been done right at the time |

---

## Where to go next

| Page | What is in it |
|---|---|
| 🚀 [**Quickstart**](docs/quickstart.md) | a working wiki in about ten minutes |
| 📖 [**Format reference**](docs/format.md) | frontmatter, vocabularies, linking, length rules — the wiki about the wiki |
| 🔭 [**Prior art**](docs/prior-art.md) | where this sits in the literature and among existing tools |

---

## Background

Three references worth knowing, and they are not the same thing:

| Reference | What it contributes |
|---|---|
| [Karpathy's *llm-wiki* gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (Apr 2026) | the **method**: let the model keep a wiki, so what it learns accumulates instead of evaporating. Portolano points that method at a target that moves |
| [Treude & Baltes, *Context Rot*](https://arxiv.org/abs/2606.09090) (Jun 2026) | the **problem**, defined and measured for the code setting, plus a research roadmap. Portolano is one answer to the preventive mitigation they list as an open question |
| [*Agent READMEs*, ACM TOSEM](https://doi.org/10.1145/3840295) (2026) | the **evidence**: across 2,303 context files, these are not static documentation but artifacts that grow like configuration code through frequent small additions. Which is why the router stays thin |

---

**Status:** v0 — the format is settled enough to use and still expected to move. See [prior art](docs/prior-art.md) for what is and isn't new here.

**License:** [Apache-2.0](LICENSE).
