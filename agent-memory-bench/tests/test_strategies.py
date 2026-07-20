import pytest

from agent_memory_bench.corpora import Corpus
from agent_memory_bench.strategies import RawStrategy, ClaudeMemStrategy, AceStrategy
from agent_memory_bench.tokens import count_tokens

DOCS = [
    {"id": "d1", "text": "Prompt caching reduces cost by reusing a stable prefix across requests."},
    {"id": "d2", "text": "Extended thinking lets the model reason step by step before answering."},
    {"id": "d3", "text": "Vision support accepts images as base64 or URL content blocks."},
    {"id": "d4", "text": "Streaming returns tokens incrementally over server-sent events."},
    {"id": "d5", "text": "Batch processing runs many requests asynchronously at half price."},
]
CORPUS = Corpus("toy", DOCS)


@pytest.mark.parametrize("cls", [RawStrategy, ClaudeMemStrategy, AceStrategy])
def test_builds_and_retrieves(cls):
    s = cls(CORPUS)
    assert s.context_text()  # non-empty memory block
    hits = s.retrieve("prompt caching prefix cost", 3)
    assert "d1" in hits  # the caching doc is retrievable by all strategies


def test_ace_smallest_at_realistic_scale():
    # ACE has a small fixed boot-block overhead, so on a tiny corpus it is not
    # the smallest — that's the bounded-vs-linear crossover. At realistic scale
    # (raw/claude_mem grow with the corpus, ACE stays flat) ACE is clearly the
    # smallest. This is the whole thesis, asserted directly.
    docs = [{"id": f"{d['id']}-{i}", "text": d["text"]} for i in range(50) for d in DOCS]
    big = Corpus("big", docs)
    raw = count_tokens(RawStrategy(big).context_text())
    cmem = count_tokens(ClaudeMemStrategy(big).context_text())
    ace = count_tokens(AceStrategy(big).context_text())
    # ACE is the smallest. (raw vs claude_mem ordering depends on doc length —
    # on real long-doc corpora raw >= claude_mem, verified in test_runner.py.)
    assert ace < cmem
    assert ace < raw
    assert ace > 0


def test_ace_context_is_bounded():
    # ACE's boot block does not grow with corpus size — duplicating the corpus
    # 20x must not materially grow the block (bounded-attention property).
    big = Corpus("big", DOCS * 20)
    small_ctx = count_tokens(AceStrategy(CORPUS).context_text())
    big_ctx = count_tokens(AceStrategy(big).context_text())
    assert big_ctx <= small_ctx * 2  # bounded, not linear in corpus size


def test_raw_context_grows_with_corpus():
    big = Corpus("big", DOCS * 20)
    small = count_tokens(RawStrategy(CORPUS).context_text())
    large = count_tokens(RawStrategy(big).context_text())
    assert large > small * 10  # raw grows ~linearly


def test_claude_mem_is_modeled_not_live():
    # Guard the honesty disclosure: the module must flag the modeled baseline.
    import agent_memory_bench.strategies.claude_mem as cm

    assert "modeled baseline" in cm.__doc__.lower()
