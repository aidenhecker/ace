"""Memory strategies under test.

Each strategy turns a corpus into (a) a *context block* — the standing memory it
carries into the model's context at query time — and (b) a *retrieval index* —
how it ranks documents for a query. The benchmark measures the size of (a) and
the recall of (b).
"""
from __future__ import annotations

from .base import Strategy
from .raw import RawStrategy
from .claude_mem import ClaudeMemStrategy
from .ace import AceStrategy

STRATEGIES: dict[str, type[Strategy]] = {
    "raw": RawStrategy,
    "claude_mem": ClaudeMemStrategy,
    "ace": AceStrategy,
}

__all__ = ["Strategy", "RawStrategy", "ClaudeMemStrategy", "AceStrategy", "STRATEGIES"]
