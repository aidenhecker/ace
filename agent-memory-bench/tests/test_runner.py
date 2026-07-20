"""End-to-end runner tests against the committed frozen snapshots (offline)."""
import pytest

from agent_memory_bench.corpora import list_corpora, load_corpus
from agent_memory_bench.runner import run, run_corpus, RECALL_KS


@pytest.mark.parametrize("name", list(list_corpora()))
def test_snapshot_present_and_nonempty(name):
    corpus = load_corpus(name)
    assert len(corpus) > 0
    assert all(d.get("id") and d.get("text") for d in corpus.documents)


@pytest.mark.parametrize("name", list(list_corpora()))
def test_run_corpus_shape(name):
    r = run_corpus(name, n_questions=10)
    assert r["n_docs"] > 0
    assert r["n_questions"] > 0
    for sname in ("raw", "claude_mem", "ace"):
        s = r["strategies"][sname]
        assert s["context_tokens"] > 0
        assert s["cost_usd_per_query"] > 0
        for k in RECALL_KS:
            assert 0.0 <= s[f"recall_at_{k}"] <= 1.0
            if k > 1:
                # recall is monotone non-decreasing in k
                assert s[f"recall_at_{k}"] >= s[f"recall_at_1"] - 1e-9


@pytest.mark.parametrize("name", list(list_corpora()))
def test_ace_compresses(name):
    r = run_corpus(name, n_questions=10)
    assert r["compression_ratio_raw_over_ace"] > 1.0
    # ACE context is the smallest of the three on every corpus
    ace = r["strategies"]["ace"]["context_tokens"]
    raw = r["strategies"]["raw"]["context_tokens"]
    cmem = r["strategies"]["claude_mem"]["context_tokens"]
    assert ace <= cmem <= raw


def test_full_report_meta():
    rep = run(n_questions=5)
    assert rep["meta"]["tokenizer"].startswith("tiktoken/")
    assert set(rep["corpora"]) == set(list_corpora())
