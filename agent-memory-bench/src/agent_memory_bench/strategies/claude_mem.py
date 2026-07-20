"""claude-mem — distilled observation rows (modeled baseline).

claude-mem (npm, v13.x) is a Claude Code session-memory tool: it summarizes
transcripts into *observation rows* (a title + subtitle per chunk) stored in
SQLite, dumps the most recent rows at session boot, and retrieves via full-text
search. ACE's own README pegs this at ~17K tokens of rows vs ACE's ~300.

WHY THIS IS A MODELED BASELINE, NOT THE LIVE PACKAGE: claude-mem only produces
observations by hooking live Claude Code sessions through an LLM — there is no
`compress(corpus)` entry point, and running it is neither deterministic nor
offline. So we model its *documented storage behavior* faithfully: one distilled
observation row per document (a title-length extract), carried in full as the
boot context, retrieved by keyword. This reproduces claude-mem's token profile
and retrieval shape without claiming to invoke the real package. See BENCHMARK.md
§"On the claude-mem baseline" for the full disclosure.
"""
from __future__ import annotations

from .base import Strategy, counts_of, tf_rank
from ..text import first_line, words

# A claude-mem observation row is roughly a title + short subtitle. We model it
# as the document's first line plus a brief extractive subtitle (~the first ~40
# words total), matching the row sizes the tool stores and dumps at boot.
_ROW_WORD_BUDGET = 40


def _observation_row(text: str) -> str:
    title = first_line(text, max_chars=120)
    remaining = text[len(title):]
    subtitle_words = words(remaining)[: max(0, _ROW_WORD_BUDGET - len(words(title)))]
    subtitle = " ".join(subtitle_words)
    return f"{title}: {subtitle}".strip().rstrip(":").strip()


class ClaudeMemStrategy(Strategy):
    name = "claude_mem"

    def build(self) -> None:
        self._rows = {d["id"]: _observation_row(d["text"]) for d in self.corpus.documents}
        self._index = {doc_id: counts_of(row) for doc_id, row in self._rows.items()}
        # Boot context = all observation rows (the "~17K tokens of rows").
        self._context = "\n".join(f"- {row}" for row in self._rows.values())

    def context_text(self) -> str:
        return self._context

    def retrieve(self, query: str, k: int) -> list[str]:
        return tf_rank(query, self._index, k)
