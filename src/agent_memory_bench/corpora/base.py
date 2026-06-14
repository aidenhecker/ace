"""Corpus registry + snapshot I/O.

A snapshot is a JSON file: {"name", "source", "fetched_at", "documents":[{id,text}]}.
Frozen snapshots live in the packaged ``data/`` dir so the benchmark is fully
offline and reproducible. ``fetch`` (see fetchers.py) refreshes them from live
sources.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from importlib import resources
from typing import Callable

Document = dict  # {"id": str, "text": str}


@dataclass
class Corpus:
    name: str
    documents: list[Document]
    source: str = ""
    fetched_at: str = ""

    def __len__(self) -> int:
        return len(self.documents)


# corpus name -> (live source description, fetcher callable)
# fetchers are imported lazily to keep `load_corpus` (offline) dependency-free.
_REGISTRY: dict[str, str] = {
    "anthropic_docs": "Anthropic docs (platform.claude.com/docs/en/*.md) — canonical agent-context corpus",
    "kernel_log": "Linux kernel commit subjects (api.github.com torvalds/linux) — dense technical text",
    "hn_top": "Hacker News top stories (hacker-news.firebaseio.com) — conversational corpus",
}

CORPORA = tuple(_REGISTRY)


def list_corpora() -> dict[str, str]:
    return dict(_REGISTRY)


def _data_dir() -> str:
    # Packaged snapshots ship under agent_memory_bench/data/.
    with resources.as_file(resources.files("agent_memory_bench") / "data") as p:
        return str(p)


def snapshot_path(name: str) -> str:
    return os.path.join(_data_dir(), f"{name}.json")


def save_corpus(corpus: Corpus) -> str:
    path = snapshot_path(corpus.name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "name": corpus.name,
        "source": corpus.source,
        "fetched_at": corpus.fetched_at,
        "documents": corpus.documents,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=0)
    return path


def load_corpus(name: str) -> Corpus:
    if name not in _REGISTRY:
        raise KeyError(f"unknown corpus {name!r}; known: {list(_REGISTRY)}")
    path = snapshot_path(name)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no frozen snapshot for {name!r} at {path}. "
            f"Run `agent-memory-bench fetch {name}` to download it."
        )
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return Corpus(
        name=payload["name"],
        documents=payload["documents"],
        source=payload.get("source", ""),
        fetched_at=payload.get("fetched_at", ""),
    )
