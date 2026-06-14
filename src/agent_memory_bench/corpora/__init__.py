"""Corpora: public text collections, fetched + frozen to local snapshots.

Each corpus is a list of {"id", "text"} documents. The benchmark runs against
*frozen snapshots* committed under ``data/`` so checked-in results are exactly
reproducible (live sources like HN change daily). Refresh a snapshot with
``agent-memory-bench fetch <corpus>``.
"""
from __future__ import annotations

from .base import CORPORA, Corpus, Document, load_corpus, list_corpora

__all__ = ["CORPORA", "Corpus", "Document", "load_corpus", "list_corpora"]
