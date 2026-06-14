"""The benchmark runner — ties corpora, strategies, Q&A, and metrics together."""
from __future__ import annotations

from .corpora import load_corpus, list_corpora
from .metrics import DEFAULT_MODEL, cost_usd
from .qa import generate_questions
from .strategies import STRATEGIES
from .tokens import ENCODING_NAME, count_tokens

# Assumed answer length per query, in tokens. The cost differentiator across
# strategies is the *standing memory context* they carry (context_tokens); the
# generated answer is assumed equal across strategies. Documented in BENCHMARK.md.
ASSUMED_ANSWER_TOKENS = 200

RECALL_KS = (1, 5, 10)


def _recall_at_ks(strategy, questions, ks):
    hits = {k: 0 for k in ks}
    kmax = max(ks)
    for q in questions:
        ranked = strategy.retrieve(q["query"], kmax)
        gold = q["gold_id"]
        # rank position of the gold doc (1-based), or None
        pos = ranked.index(gold) + 1 if gold in ranked else None
        for k in ks:
            if pos is not None and pos <= k:
                hits[k] += 1
    n = len(questions) or 1
    return {k: round(hits[k] / n, 4) for k in ks}


def run_corpus(name: str, model: str = DEFAULT_MODEL, n_questions: int = 50) -> dict:
    corpus = load_corpus(name)
    questions = generate_questions(corpus, n=n_questions)

    result = {
        "n_docs": len(corpus),
        "n_questions": len(questions),
        "source": corpus.source,
        "fetched_at": corpus.fetched_at,
        "strategies": {},
    }
    for sname, scls in STRATEGIES.items():
        strat = scls(corpus)
        ctx_tokens = count_tokens(strat.context_text())
        recall = _recall_at_ks(strat, questions, RECALL_KS)
        entry = {
            "context_tokens": ctx_tokens,
            "tokens_out": ASSUMED_ANSWER_TOKENS,
            "cost_usd_per_query": round(
                cost_usd(ctx_tokens, ASSUMED_ANSWER_TOKENS, model), 8
            ),
        }
        for k in RECALL_KS:
            entry[f"recall_at_{k}"] = recall[k]
        result["strategies"][sname] = entry

    raw_ctx = result["strategies"]["raw"]["context_tokens"]
    ace_ctx = result["strategies"]["ace"]["context_tokens"] or 1
    result["compression_ratio_raw_over_ace"] = round(raw_ctx / ace_ctx, 1)
    return result


def run(corpora=None, model: str = DEFAULT_MODEL, n_questions: int = 50) -> dict:
    corpora = list(corpora) if corpora else list(list_corpora())
    return {
        "meta": {
            "tokenizer": f"tiktoken/{ENCODING_NAME}",
            "tokenizer_note": "approximation of Anthropic tokenization; ratios are tokenizer-robust",
            "pricing_model": model,
            "assumed_answer_tokens": ASSUMED_ANSWER_TOKENS,
            "recall_ks": list(RECALL_KS),
            "n_questions": n_questions,
        },
        "corpora": {name: run_corpus(name, model, n_questions) for name in corpora},
    }
