"""agent-memory-bench CLI.

    agent-memory-bench run                 # all corpora, pretty table + JSON
    agent-memory-bench run --corpus hn_top --json
    agent-memory-bench fetch hn_top        # refresh a frozen snapshot from live source
    agent-memory-bench fetch all
    agent-memory-bench list                # list corpora
"""
from __future__ import annotations

import argparse
import json
import sys

from .corpora import list_corpora
from .metrics import DEFAULT_MODEL, PRICING
from .runner import RECALL_KS, run


def _fmt_usd(x: float) -> str:
    return f"${x:.6f}"


def _print_table(report: dict) -> None:
    meta = report["meta"]
    print(f"\nagent-memory-bench · tokenizer={meta['tokenizer']} · pricing={meta['pricing_model']}\n")
    for cname, c in report["corpora"].items():
        print(f"━━ {cname}  ({c['n_docs']} docs, {c['n_questions']} questions)")
        header = f"  {'strategy':<12} {'ctx_tokens':>11} {'r@1':>6} {'r@5':>6} {'r@10':>6} {'$/query':>12}"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for sname, s in c["strategies"].items():
            print(
                f"  {sname:<12} {s['context_tokens']:>11,} "
                f"{s['recall_at_1']:>6.2f} {s['recall_at_5']:>6.2f} {s['recall_at_10']:>6.2f} "
                f"{_fmt_usd(s['cost_usd_per_query']):>12}"
            )
        print(f"  → compression (raw ÷ ace context): {c['compression_ratio_raw_over_ace']:.1f}×\n")


def cmd_run(args) -> int:
    corpora = [args.corpus] if args.corpus else None
    try:
        report = run(corpora=corpora, model=args.model, n_questions=args.questions)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        print("hint: run `agent-memory-bench fetch all` first.", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_table(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


def cmd_fetch(args) -> int:
    from .corpora.fetchers import FETCHERS, fetch_and_freeze

    names = list(FETCHERS) if args.name == "all" else [args.name]
    for name in names:
        if name not in FETCHERS:
            print(f"unknown corpus {name!r}; known: {list(FETCHERS)} or 'all'", file=sys.stderr)
            return 2
        print(f"fetching {name} …", file=sys.stderr)
        corpus = fetch_and_freeze(name)
        print(f"  froze {len(corpus)} docs → data/{name}.json", file=sys.stderr)
    return 0


def cmd_list(_args) -> int:
    print("corpora:")
    for name, desc in list_corpora().items():
        print(f"  {name:<16} {desc}")
    print("\nmodels (input/output $ per MTok):")
    for m, (i, o) in PRICING.items():
        print(f"  {m:<20} {i:>6.2f} / {o:>6.2f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent-memory-bench", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")

    r = sub.add_parser("run", help="run the benchmark")
    r.add_argument("--corpus", choices=list(list_corpora()), help="single corpus (default: all)")
    r.add_argument("--model", default=DEFAULT_MODEL, choices=list(PRICING), help="pricing model")
    r.add_argument("--questions", type=int, default=50, help="Q&A test-set size")
    r.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    r.add_argument("--out", help="also write the JSON report to this path")
    r.set_defaults(func=cmd_run)

    f = sub.add_parser("fetch", help="refresh a frozen corpus snapshot from its live source")
    f.add_argument("name", help="corpus name or 'all'")
    f.set_defaults(func=cmd_fetch)

    l = sub.add_parser("list", help="list corpora and pricing")
    l.set_defaults(func=cmd_list)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        # bare invocation → run all corpora (the uvx one-liner)
        args = parser.parse_args(["run"])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
