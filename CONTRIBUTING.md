# Contributing

Three high-value contributions, easiest first.

## 1. Refresh pricing

Anthropic changed prices? Edit one table:

```python
# src/agent_memory_bench/metrics/pricing.py
PRICING = { "claude-sonnet-4-6": (3.00, 15.00), ... }  # (input $/MTok, output $/MTok)
```

Cost is always computed from this table — never hard-coded — so a price change is
a one-line PR.

## 2. Add a corpus

The most valuable PR: a new public corpus that stresses memory differently.

1. Add a fetcher to `src/agent_memory_bench/corpora/fetchers.py` returning a
   `Corpus` of `{"id", "text"}` documents; register it in `FETCHERS` and in
   `corpora/base.py::_REGISTRY`.
2. Freeze a snapshot: `agent-memory-bench fetch <name>` (writes
   `agent_memory_bench/data/<name>.json`) and **commit the snapshot** so results
   stay reproducible.
3. Add it to `results/` by re-running `agent-memory-bench run --out results/<date>.json`.

Corpora wanted: long support-ticket threads, RAG eval sets, multi-turn agent
transcripts, non-English text (to stress the tokenizer proxy).

## 3. Add a strategy

Subclass `Strategy` (`src/agent_memory_bench/strategies/base.py`):

```python
class MyStrategy(Strategy):
    name = "my_strategy"
    def build(self): ...            # construct from self.corpus
    def context_text(self) -> str: ...   # standing memory block (cost)
    def retrieve(self, query, k): ...    # top-k doc ids (recall)
```

Register it in `strategies/__init__.py::STRATEGIES`. Strategies wanted:
**vector-RAG** (embedding retrieval), **summary-recall** (LLM-distilled
paragraphs), and a **real-ACE adapter** that shells out to the `ace` npm package
for LLM-extracted concepts.

## Ground rules

- **Never fabricate numbers.** Every number in `results/` and the README must come
  from a real `agent-memory-bench run`. If a strategy loses, ship the loss.
- **Keep it deterministic and offline.** Tests and CI run against frozen snapshots
  with no network and no API key. Seeded RNG only.
- **Disclose modeled baselines.** If a strategy models a real tool rather than
  invoking it, say so in the module docstring (there's a test that checks).

## Dev loop

```bash
python -m venv .venv && ./.venv/bin/pip install -e ".[dev]"
./.venv/bin/python -m pytest -q          # 21 tests, offline
./.venv/bin/agent-memory-bench run       # the table
```
