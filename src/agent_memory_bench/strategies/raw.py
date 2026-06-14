"""RAW — no compression. The honest upper bound on recall, worst on cost.

The whole corpus is the memory: every document carried into context verbatim,
retrieval over full document text. This is what "just stuff the transcript in
the context window" costs.
"""
from __future__ import annotations

from .base import Strategy, counts_of, tf_rank


class RawStrategy(Strategy):
    name = "raw"

    def build(self) -> None:
        self._index = {d["id"]: counts_of(d["text"]) for d in self.corpus.documents}
        self._context = "\n\n".join(d["text"] for d in self.corpus.documents)

    def context_text(self) -> str:
        return self._context

    def retrieve(self, query: str, k: int) -> list[str]:
        return tf_rank(query, self._index, k)
