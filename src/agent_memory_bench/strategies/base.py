"""Strategy interface + a shared TF retrieval scorer."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter

from ..corpora import Corpus
from ..text import content_words


class Strategy(ABC):
    """A memory strategy: compress a corpus, carry a context block, retrieve docs."""

    name: str = "base"

    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        self.build()

    @abstractmethod
    def build(self) -> None:
        """Construct the internal representation from ``self.corpus``."""

    @abstractmethod
    def context_text(self) -> str:
        """The standing memory block carried into context at query time."""

    @abstractmethod
    def retrieve(self, query: str, k: int) -> list[str]:
        """Return up to ``k`` document ids ranked most-relevant-first."""


def tf_rank(query: str, indexed: dict[str, Counter], k: int) -> list[str]:
    """Rank items by summed query-term frequency (a transparent TF scorer).

    ``indexed`` maps item_id -> Counter of that item's content-word frequencies.
    Score(item) = sum over query terms of freq(term, item). Ties broken by id for
    determinism. Items with score 0 are dropped.
    """
    q_terms = set(content_words(query))
    scored: list[tuple[float, str]] = []
    for item_id, counts in indexed.items():
        score = sum(counts.get(t, 0) for t in q_terms)
        if score > 0:
            scored.append((score, item_id))
    # highest score first; deterministic tiebreak on id
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [item_id for _, item_id in scored[:k]]


def counts_of(text: str) -> Counter:
    return Counter(content_words(text))
