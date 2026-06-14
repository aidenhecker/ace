from agent_memory_bench.tokens import count_tokens
from agent_memory_bench.metrics import cost_usd, PRICING, DEFAULT_MODEL


def test_count_tokens_basic():
    assert count_tokens("") == 0
    assert count_tokens("hello world") >= 2
    # more text → more tokens (monotone)
    assert count_tokens("a b c d e f g") > count_tokens("a b")


def test_pricing_table_shape():
    for model, (i, o) in PRICING.items():
        assert i > 0 and o > 0 and o >= i  # output never cheaper than input
    assert DEFAULT_MODEL in PRICING


def test_cost_is_linear_and_priced():
    # Sonnet 4.6 = $3/$15 per MTok
    c = cost_usd(1_000_000, 0, "claude-sonnet-4-6")
    assert abs(c - 3.0) < 1e-9
    c2 = cost_usd(0, 1_000_000, "claude-sonnet-4-6")
    assert abs(c2 - 15.0) < 1e-9


def test_unknown_model_raises():
    import pytest

    with pytest.raises(KeyError):
        cost_usd(100, 100, "gpt-4")
