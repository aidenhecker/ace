"""ACE — Access · Compact · Execute. Subjective salience pointers + co-occurrence.

Faithful offline model of github.com/hmatrades/ace. ACE stores *salience
pointers* — concepts with a hit count and decay — not content. The model's
weights supply meaning at recall time; the flag store supplies attention. The
session-boot context is a tiny bounded block of the top-salient concepts
(~hundreds of tokens) regardless of corpus size; the full flag store (every
concept + provenance + co-occurrence graph) is queryable on demand.

This benchmark reports:
  * context cost  = the bounded $ACE boot block (what every session pays).
  * recall        = a query against the FULL flag store (concept -> source docs),
                    mirroring `flag recall` / `flag graph` hitting the store.

Offline-extractor note: real ACE extracts concepts with an LLM (Haiku/Ollama).
For a reproducible, key-free benchmark we extract concepts deterministically
(top content words per document → snake_case concepts, frequency = hits). This
preserves ACE's COMPRESSION mechanism exactly (pointers vs text); the LLM
extractor would change recall quality, not the token ratios. See BENCHMARK.md.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .base import Strategy
from ..text import content_words

# How many concepts each document contributes to the store.
_CONCEPTS_PER_DOC = 8
# Size of the bounded session-boot block (top concepts by salience).
_BOOT_BLOCK_CONCEPTS = 60

# ACE stance thresholds on effective salience (from ace/src/store.js).
def _stance(eff: float) -> str:
    if eff >= 8:
        return "strong"
    if eff >= 3:
        return "familiar"
    if eff >= 1:
        return "light"
    return "faded"


class AceStrategy(Strategy):
    name = "ace"

    def build(self) -> None:
        # hits[concept] = total occurrences across corpus (no time decay in a
        # single snapshot, so effective salience == hits here).
        self._hits: Counter = Counter()
        # provenance[concept] = set of doc ids whose top concepts include it.
        self._provenance: dict[str, set] = defaultdict(set)

        for d in self.corpus.documents:
            counts = Counter(content_words(d["text"]))
            top = [c for c, _ in counts.most_common(_CONCEPTS_PER_DOC)]
            for c in top:
                self._hits[c] += counts[c]
                self._provenance[c].add(d["id"])

        self._boot = self._render_boot_block()

    # ── context cost ────────────────────────────────────────────────────────
    def _render_boot_block(self) -> str:
        top = self._hits.most_common(_BOOT_BLOCK_CONCEPTS)
        lines = ["$ACE — salient concepts (boot block)", "concept                  hits  stance"]
        for concept, hits in top:
            lines.append(f"{concept[:24]:<24} {hits:>4}  {_stance(float(hits))}")
        return "\n".join(lines)

    def context_text(self) -> str:
        return self._boot

    # ── recall: query the full store ─────────────────────────────────────────
    def retrieve(self, query: str, k: int) -> list[str]:
        q_terms = set(content_words(query))
        doc_scores: Counter = Counter()
        for concept, hits in self._hits.items():
            if _matches(concept, q_terms):
                for doc_id in self._provenance[concept]:
                    doc_scores[doc_id] += hits
        ranked = sorted(doc_scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [doc_id for doc_id, _ in ranked[:k]]


def _matches(concept: str, q_terms: set) -> bool:
    """A concept matches the query if it shares a term (exact, or substring
    either direction — handling plural/morphology), mirroring ace/bench/recall.js.
    """
    if concept in q_terms:
        return True
    for t in q_terms:
        if concept in t or t in concept:
            return True
    return False
