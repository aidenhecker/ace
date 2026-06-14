# BENCHMARK.md — methodology

This document defines exactly what is measured and why, **before** you read a
single number off the README. If a number isn't defined here, don't quote it.

## The question

> *Does ACE's salience-pointer memory really replace ~17K tokens of agent context
> with ~300 — and what does that cost in recall?*

We answer it for three public corpora by measuring, per strategy:

| metric | definition |
|---|---|
| `context_tokens` | tokens of the **standing memory block** a strategy carries into the model's context at query time (the headline cost) |
| `recall_at_k` (k=1,5,10) | fraction of Q&A probes whose **gold document** appears in the strategy's top-k retrieval |
| `tokens_out` | assumed answer length per query — a **fixed constant** (200), equal across strategies (see below) |
| `cost_usd_per_query` | `(context_tokens × input_price + tokens_out × output_price) / 1e6` at 2026-06 Anthropic pricing |
| `compression_ratio` | `raw.context_tokens ÷ ace.context_tokens` per corpus |

`tokens_out` is held constant because the differentiator between strategies is
the **standing memory they carry**, not the answer they generate. We do not call
a live model (that would need a key and break reproducibility); cost differences
therefore come purely from `context_tokens`. If you want true end-to-end cost,
multiply through your own model + answer-length assumptions — the harness exposes
`--model`.

## The three strategies

All three implement one interface (`strategies/base.py`): build a representation
from the corpus, expose a `context_text()` (the standing block), and `retrieve()`
the top-k documents for a query.

- **`raw`** — no compression. The memory *is* the corpus: every document carried
  verbatim, retrieval by term-frequency over full text. The recall ceiling and
  the cost floor's opposite — what "just stuff the transcript in" costs.
- **`claude_mem`** — distilled **observation rows** (one title+lead extract per
  document), all rows carried at boot, keyword retrieval over rows. Models
  claude-mem's documented storage shape. *See the disclosure below.*
- **`ace`** — **salience pointers**: concepts with hit-counts, a bounded
  session-boot block of the top-salient concepts, and a full flag store
  (concept → source docs) queried for recall. Faithful model of
  [github.com/hmatrades/ace](https://github.com/hmatrades/ace).

### Retrieval scoring

A transparent term-frequency scorer (`strategies/base.py::tf_rank`): score(item)
= Σ over query content-words of freq(word, item); ties broken by id for
determinism; zero-score items dropped. `raw` scores over full docs, `claude_mem`
over rows, `ace` matches query terms against concepts (substring either
direction, mirroring `ace/bench/recall.js`) and maps matched concepts back to
their source documents via provenance.

### ACE: bounded boot block vs. full store

This is the crux. Real ACE carries a small `$ACE` block at session boot (top
concepts, ~hundreds of tokens) while keeping the full flag store + co-occurrence
graph available to query on demand (`flag recall`, `flag graph`). We model both:

- `context_tokens` measures the **bounded boot block** — what every session pays.
  It is ~constant in corpus size (446 / 454 / 453 tokens on our three corpora).
- `recall` queries the **full store** (every concept + provenance) — what the
  agent can reach when it decides to.

So ACE's cost is flat while its reach is broad — at the price of pointer-level
(not content-level) precision.

## The Q&A test set

Deterministic and corpus-derived (`qa.py`): for each sampled document, the probe
is its title (first line) plus its opening words; the gold answer is that
document. Probes are built from the source material both systems see, so neither
is favored by vocabulary (the approach in `ace/bench/recall.js`). Sampling uses a
fixed-seed RNG → the same snapshot always yields the same questions → identical
numbers on every run.

## Corpora — real, fetched, frozen

| corpus | source | what it stresses |
|---|---|---|
| `anthropic_docs` | `platform.claude.com/docs/en/*.md` (22 pages) | long documents — the canonical agent-context case |
| `kernel_log` | `api.github.com/torvalds/linux` commit subjects (100) | dense technical text full of identifiers |
| `hn_top` | `hacker-news.firebaseio.com` top stories (~100) | short conversational text |

Live sources change (HN rotates daily), so each corpus is **frozen to a JSON
snapshot** under `agent_memory_bench/data/`. The benchmark and CI run against the
frozen snapshots → checked-in results are exactly reproducible.
`agent-memory-bench fetch <corpus>` refreshes a snapshot from the live source.

## Token counting

`tiktoken/cl100k_base` — a deterministic, offline, key-free proxy for Anthropic
tokenization (Anthropic ships no local tokenizer; `count_tokens` needs the
network and a key). Absolute counts are approximate (~10-20% on prose, more on
code); **ratios between strategies are tokenizer-robust** because all strategies
are measured with the same encoder. To check against a real Anthropic count, run
`count_tokens` on an emitted `context_text()` block.

## Honest caveats (read before you cite)

1. **On the claude-mem baseline.** claude-mem (npm v13.x) is a Claude Code
   session-memory tool: it produces observation rows only by hooking live
   sessions through an LLM, and stores them in SQLite. There is no
   `compress(corpus)` entry point, and running it is neither deterministic nor
   offline. We therefore **model its documented storage behavior** — one distilled
   row per document, all rows at boot, keyword retrieval — rather than invoke the
   live package. The numbers reflect claude-mem's *token profile and retrieval
   shape*, not a live run. Treat "claude-mem" here as "a faithful claude-mem-style
   observation-row baseline."
2. **ACE extraction is offline, not LLM.** Real ACE extracts concepts with Haiku/
   Ollama. We use a deterministic top-content-word extractor so the benchmark
   needs no key. This **preserves the compression mechanism exactly** (pointers vs
   text → the token ratios are real) but **changes recall quality** — an LLM
   extractor would pick better concepts and likely lift ACE's recall, especially
   on `kernel_log`. ACE's recall here is a *floor*, not a ceiling.
3. **`tokens_out` is assumed, not generated.** Cost is context-dominated by
   construction; we don't run inference.
4. **Recall is single-gold retrieval.** Each probe has exactly one correct
   document; this rewards discriminative representations and is harsh on lossy
   compression — by design, so the trade-off is visible.
5. **Corpora are small** (20–100 docs). They're sized for a 60-second laptop run,
   not statistical heft. The bounded-vs-linear context story extrapolates; the
   recall percentages are indicative, not population estimates. Bring a bigger
   corpus via `fetch` / a new fetcher to stress it harder.
