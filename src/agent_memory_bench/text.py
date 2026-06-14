"""Shared lightweight text utilities — word tokenization, stopwords, content words.

Pure stdlib, deterministic. Used by the offline ACE extractor, the retrieval
scorers, and Q&A generation so every component sees words the same way.
"""
from __future__ import annotations

import re

STOPWORDS = frozenset(
    """
    the a an and or but if then else for to of in on at by with from into out up
    down over under again further is are was were be been being have has had do does
    did doing this that these those i you he she it we they them his her its our your
    their what which who whom whose when where why how all any both each few more most
    other some such no nor not only own same so than too very can will just dont should
    now about as also use using used via per get got make made new one two three
    """.split()
)

_WORD = re.compile(r"[a-z0-9][a-z0-9_]+")


def words(text: str) -> list[str]:
    """Lowercase word tokens (length >= 2, alphanumeric/underscore)."""
    return _WORD.findall((text or "").lower())


def content_words(text: str, min_len: int = 3) -> list[str]:
    """Words minus stopwords and short tokens — the meaning-bearing tokens."""
    return [w for w in words(text) if len(w) >= min_len and w not in STOPWORDS]


def first_line(text: str, max_chars: int = 200) -> str:
    """The first non-empty line, trimmed — a document's natural 'title'."""
    for line in (text or "").splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:max_chars]
    return (text or "").strip()[:max_chars]
