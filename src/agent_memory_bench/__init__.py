"""agent-memory-bench — reproduce ACE's agent-memory compression claim.

Run ACE vs claude-mem vs raw over public corpora and emit (tokens, recall@k,
cost-USD) so the "~300 tokens vs ~17K" claim becomes a number anyone replicates.
"""
__version__ = "0.1.0"

from .runner import run, run_corpus

__all__ = ["run", "run_corpus", "__version__"]
