# Prior art

What is new here, and what is not.

**The short version:** coupling documentation to the code it describes, and flagging it when that code moves, is not a new idea — it has been a commercial product for years. Doing it with **nothing to host and nothing to sign up for**, at page granularity, in a format an agent reads natively, is.

---

## The problem has a name and a measurement

**[*Context Rot in AI-Assisted Software Development*](https://arxiv.org/abs/2606.09090)** — Christoph Treude (Singapore Management University), Sebastian Baltes (Heidelberg University), June 2026.

They define **context rot** as *"the gradual divergence between what a configuration file says about a codebase, its tools, its architecture, or its conventions, and what actually holds"*, and make three moves: name the phenomenon, show it is detectable with tools that already exist, and lay out a research roadmap.

| Their finding | Number |
|---|---|
| Repositories sampled (95% confidence, 5% margin) | 356 |
| With at least one stale code reference | **23.0%** |
| Of flagged elements, genuine on manual inspection | 64% |

That last row is the one to keep in view: **a third of what such a checker flags is noise.** It is the empirical case for treating a stale signal as *suspect* rather than as an error — which is what Portolano does.

Their roadmap lists four open questions. The mitigation half of the fourth — *"alerting developers when a configuration file is not updated alongside related code changes"* — is what `covers` and `verified-at` do.

⚠️ Preprint, not peer-reviewed. The term *context rot* is also borrowed: it first described degradation inside a model's input window, and this paper extends it to versioned repository artifacts.

---

## The method it inherits

**[Karpathy's *llm-wiki* gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** — April 2026. Let the model keep a wiki — ingest, query, lint — so what it learns accumulates instead of evaporating at the end of a session.

The gist is about sources you *read*: documents that sit still. Portolano applies the same method where the source **moves on its own**, which is the whole reason a freshness contract is needed at all. Chronologically the gist comes first; it is the method ancestor, not an answer to the paper above.

**[llm-wiki-manager](https://github.com/sametbrr/llm-wiki-manager)** — May 2026. The gist built out as a working skill, and the closest sibling this project has. Three layers: `raw/` for sources a human curates, `wiki/` for pages the model owns, a schema file describing the conventions. It has an index as the front door, a changelog, and a linter for orphans and broken links.

The resemblance runs deep, and so does the one difference that matters. It documents **documents** — papers, articles, transcripts — and a document does not change after you file it. There is no commit to measure against because nothing moves on its own, so a freshness contract would have nothing to attach to.

That is the whole line between the two, and it is worth stating plainly: **the substrate is what forces the mechanism.** Point the same method at source code and `covers` plus `verified-at` stop being an embellishment and become the part that keeps the wiki worth reading. Neither project is a version of the other.

---

## The evidence that shapes the format

| Study | What it found |
|---|---|
| [*Agent READMEs*](https://doi.org/10.1145/3840295) — ACM TOSEM, 2026 | 2,303 context files from 1,925 repositories. They are "not static documentation but complex, difficult-to-read artifacts that evolve like configuration code". The only peer-reviewed study in this group |
| [arXiv:2608.11095](https://arxiv.org/abs/2608.11095) | 247,694 instruction lifetimes: context files more than triple over their life, and the older an instruction is the less likely it is ever removed — because once its rationale is lost, deleting it safely is intractable. Recording the *why* is what makes pruning possible |
| [arXiv:2602.11988](https://arxiv.org/abs/2602.11988) | context files did not improve task success and cost over 20% more — but *instructions* were followed well and *repository overviews* were the unhelpful part. The case for a thin router |
| [arXiv:2604.11243](https://arxiv.org/abs/2604.11243) | a persistent knowledge layer answered the same four queries in 47K tokens against 305K for a RAG baseline |

The literature is **not settled**: other work finds context files reduce agent runtime and token use. Portolano's bet is that the distinction is *preloaded* versus *retrieved from an index on demand* — nobody has yet measured them against each other.

---

## Complementary tools

The two largest projects in the adjacent space do **not** do what Portolano does, and that is what makes them interesting: each covers a phase Portolano deliberately leaves alone. Neither integration is built yet — they are the two that make obvious sense.

| Tool | What it covers | How the two could meet |
|---|---|---|
| [**OpenSpec**](https://github.com/Fission-AI/OpenSpec), [**spec-kit**](https://github.com/github/spec-kit) | *what you are about to build*: every change starts as a proposal, and the spec is archived once it ships | complementary in **time**. A spec describes the future, a page describes the present. The archive moment is the natural trigger: **when a change is archived, the pages whose `covers` it touched become suspect** — a spec that just shipped is the best possible evidence that a page is out of date, and it arrives with the rationale already written |
| [**Cline's Memory Bank**](https://docs.cline.bot/best-practices/memory-bank) | *standing context*: a fixed set of files loaded at the start of every session | complementary in **layer**. A memory bank is a rendering of knowledge, not a place to keep it. The wiki is the source; a memory bank is one more generated adapter, exactly like `CLAUDE.md` — same reason, same pipeline |

The pattern behind both: Portolano's scope is **durable knowledge about what exists**. Everything upstream of that (deciding what to build) and downstream of it (rendering it into whatever a given tool loads) belongs to somebody else, and should.

---

## Neighbours

| Project | What it does | Where Portolano differs |
|---|---|---|
| [**Swimm**](https://swimm.io) | code-coupled documentation with pull-request staleness checks, shipping for years, and a great deal more besides | a commercial product: a service, an account, a price, coupling at the snippet level, written for human readers. Portolano is the open-source answer to the same instinct — nothing to sign up for, nothing to host, `git log` as the entire engine |
| [**Lore**](https://arxiv.org/abs/2603.15566) | encodes decisions into git commit trailers: constraints, rejected alternatives, no files and no database | it attaches knowledge to the **change**, we attach it to the **subject**. Immutable history against a maintained description of the present. Lore also cannot reach backwards: existing commits carry no trailers, so the codebases where the problem is worst get nothing. A Portolano page can be written today about code from five years ago |
| Doc-freshness CI checks, context-file auditors, spec-drift indexers | a dozen small projects, most of them months old | no established open-source project has taken this slot. The problem is real and nobody has won it yet |

---

## What Portolano actually claims

Not that the mechanism is new. The combination:

| Claim | What it rests on |
|---|---|
| **Zero infrastructure** | git is the database; the check is one command |
| **Page granularity, declared scope** | the page states what it covers, rather than a tool inferring it |
| **Suspect, never auto-repaired** | given that a third of flags are noise, auto-repair is how you get pages nobody has read |
| **Aimed at what is not in the code** | the *why*, the rejected options, the traps, the boundaries. The half that no checker can derive from source |
| **Retroactive** | nothing had to be done right at the time |
