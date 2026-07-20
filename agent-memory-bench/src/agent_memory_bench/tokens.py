"""Token counting.

We use tiktoken's ``cl100k_base`` encoding as a deterministic, offline,
reproducible proxy for token counts. This is an APPROXIMATION of Anthropic's
tokenizer — Anthropic does not publish an exact local tokenizer, and the exact
``/v1/messages/count_tokens`` endpoint requires an API key and network access,
which would make the benchmark non-reproducible and non-offline.

What this means for the numbers:
  * Absolute token counts are approximate (typically within ~10-20% of a model's
    true count on prose; more on code/non-English).
  * RATIOS between strategies — the headline of this benchmark — are robust,
    because all strategies are measured with the same tokenizer. If ACE's block
    is 195x smaller than the raw corpus under cl100k_base, it is ~195x smaller
    under any consistent tokenizer.

To verify against a real Anthropic count, run `count_tokens` on the emitted
context blocks (see BENCHMARK.md).
"""
from __future__ import annotations

import functools

ENCODING_NAME = "cl100k_base"


@functools.lru_cache(maxsize=1)
def _enc():
    import tiktoken

    return tiktoken.get_encoding(ENCODING_NAME)


def count_tokens(text: str) -> int:
    """Number of tokens in ``text`` under cl100k_base."""
    if not text:
        return 0
    return len(_enc().encode(text, disallowed_special=()))
