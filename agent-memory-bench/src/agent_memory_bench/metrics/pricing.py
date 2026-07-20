"""Anthropic API pricing, USD per million tokens (2026-06).

Source: Anthropic models/pricing (cached 2026-05-26). Update via PR when prices
change — see CONTRIBUTING.md. Cost is computed, never hard-coded, so a price
change only edits this table.
"""
from __future__ import annotations

# model id -> (input $/MTok, output $/MTok)
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-fable-5": (10.00, 50.00),
}

# The default model used for cost_usd_per_query. Sonnet 4.6 is the typical
# production agent model — high-volume, mid-priced — so it's the fair default
# for "what does carrying this memory cost me per query".
DEFAULT_MODEL = "claude-sonnet-4-6"


def cost_usd(input_tokens: int, output_tokens: int, model: str = DEFAULT_MODEL) -> float:
    """Cost of one query in USD: input context + output answer at ``model`` price."""
    if model not in PRICING:
        raise KeyError(f"unknown model {model!r}; known: {sorted(PRICING)}")
    in_price, out_price = PRICING[model]
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000
