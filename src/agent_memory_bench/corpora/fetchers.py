"""Live fetchers for the three corpora. Pure stdlib (urllib) — no extra deps.

Each fetcher returns a Corpus and `fetch_and_freeze` writes the snapshot. Live
sources change over time, so fetching refreshes the frozen JSON; the committed
snapshots are what the benchmark and CI run against.
"""
from __future__ import annotations

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from .base import Corpus, save_corpus

_UA = {"User-Agent": "agent-memory-bench/0.1 (+https://github.com/hmatrades/agent-memory-bench)"}
_TIMEOUT = 20


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        return r.read()


def _get_text(url: str) -> str:
    return _get(url).decode("utf-8", errors="replace")


def _get_json(url: str):
    return json.loads(_get(url).decode("utf-8", errors="replace"))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Anthropic docs ──────────────────────────────────────────────────────────
# A curated set of canonical doc pages served as Markdown. Each page is one doc.
_ANTHROPIC_DOC_PATHS = [
    "about-claude/models/overview",
    "build-with-claude/prompt-caching",
    "build-with-claude/extended-thinking",
    "build-with-claude/streaming",
    "build-with-claude/vision",
    "build-with-claude/pdf-support",
    "build-with-claude/batch-processing",
    "build-with-claude/files",
    "build-with-claude/token-counting",
    "build-with-claude/structured-outputs",
    "build-with-claude/citations",
    "build-with-claude/context-windows",
    "agents-and-tools/tool-use/overview",
    "agents-and-tools/tool-use/code-execution-tool",
    "agents-and-tools/tool-use/computer-use",
    "agents-and-tools/tool-use/bash-tool",
    "agents-and-tools/tool-use/text-editor-tool",
    "agents-and-tools/tool-use/memory-tool",
    "agents-and-tools/tool-use/tool-search-tool",
    "agents-and-tools/skills",
    "api/rate-limits",
    "api/errors",
]
_ANTHROPIC_BASE = "https://platform.claude.com/docs/en/"


def fetch_anthropic_docs(limit: int = 22) -> Corpus:
    docs = []
    for path in _ANTHROPIC_DOC_PATHS[:limit]:
        try:
            text = _get_text(_ANTHROPIC_BASE + path + ".md")
        except Exception:
            continue
        if text and not text.lstrip().startswith("<"):  # skip HTML error pages
            docs.append({"id": f"anthropic/{path}", "text": text.strip()})
    return Corpus("anthropic_docs", docs, source=_ANTHROPIC_BASE, fetched_at=_now())


# ── Linux kernel commit subjects ────────────────────────────────────────────
def fetch_kernel_log(limit: int = 100) -> Corpus:
    url = f"https://api.github.com/repos/torvalds/linux/commits?per_page={min(limit, 100)}"
    rows = _get_json(url)
    docs = []
    for r in rows:
        msg = (r.get("commit", {}) or {}).get("message", "") or ""
        sha = r.get("sha", "")[:12]
        if msg.strip():
            docs.append({"id": f"kernel/{sha}", "text": msg.strip()})
    return Corpus("kernel_log", docs, source="api.github.com/torvalds/linux", fetched_at=_now())


# ── Hacker News top stories ─────────────────────────────────────────────────
_HN = "https://hacker-news.firebaseio.com/v0"


def _hn_item(item_id: int) -> dict | None:
    try:
        it = _get_json(f"{_HN}/item/{item_id}.json")
    except Exception:
        return None
    if not it or it.get("type") != "story":
        return None
    title = it.get("title", "") or ""
    text = it.get("text", "") or ""
    body = f"{title}\n\n{text}".strip()
    return {"id": f"hn/{item_id}", "text": body} if title else None


def fetch_hn_top(limit: int = 100) -> Corpus:
    ids = _get_json(f"{_HN}/topstories.json")[:limit]
    docs = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        for d in pool.map(_hn_item, ids):
            if d:
                docs.append(d)
    docs.sort(key=lambda d: d["id"])  # stable order
    return Corpus("hn_top", docs, source=_HN, fetched_at=_now())


FETCHERS = {
    "anthropic_docs": fetch_anthropic_docs,
    "kernel_log": fetch_kernel_log,
    "hn_top": fetch_hn_top,
}


def fetch_and_freeze(name: str) -> Corpus:
    if name not in FETCHERS:
        raise KeyError(f"no fetcher for {name!r}")
    corpus = FETCHERS[name]()
    save_corpus(corpus)
    return corpus
