"""Q&A test-set generation — deterministic, derived from the corpus itself.

For each sampled document we form a question from its title (first line) and mark
that document as the gold answer. This mirrors ace/bench/recall.js: questions are
built from the source material both systems see, so neither is favored by
vocabulary. recall@k then asks: does the strategy surface the gold document in
its top-k retrieval?

Deterministic: sampling uses a fixed-seed RNG, so the same corpus snapshot always
yields the same questions.
"""
from __future__ import annotations

import random

from .corpora import Corpus
from .text import content_words, first_line, words

Question = dict  # {"query": str, "gold_id": str, "keywords": list[str]}

_MIN_PROBE_WORDS = 3
_PROBE_WORDS = 30


def _probe(text: str) -> str:
    """A realistic query: the document's title plus its opening words.

    Short H1 titles ('Prompt caching') alone don't carry enough signal, so we
    extend with the document's lead until there are a few content words — the
    natural 'I'm looking for the thing about X' query a user would type.
    """
    title = first_line(text, max_chars=160)
    lead = " ".join(words(text)[:_PROBE_WORDS])
    probe = f"{title} {lead}".strip()
    return probe


def generate_questions(corpus: Corpus, n: int = 50, seed: int = 1729) -> list[Question]:
    candidates = []
    for d in corpus.documents:
        probe = _probe(d["text"])
        kws = content_words(probe)
        if len(kws) >= _MIN_PROBE_WORDS:
            candidates.append((d["id"], probe, kws))
    rng = random.Random(seed)
    rng.shuffle(candidates)
    chosen = candidates[: min(n, len(candidates))]
    chosen.sort(key=lambda c: c[0])  # stable output order
    return [
        {"query": title, "gold_id": doc_id, "keywords": kws[:5]}
        for doc_id, title, kws in chosen
    ]
