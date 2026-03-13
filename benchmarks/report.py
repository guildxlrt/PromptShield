import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from tabulate import tabulate

from .runner import BenchmarkResult

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_csv(
    results: list[BenchmarkResult], path: str = "benchmark_results.csv"
) -> None:
    df = pd.DataFrame([asdict(r) for r in results])
    df.to_csv(path, index=False)
    print(f"\n✓ Raw results saved to {path}")


def save_json(metrics: dict, path: str = "benchmark_summary.json") -> None:
    summary_path = Path(path)
    summary_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"✓ Summary saved to {path}")


# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------


def print_report(metrics: dict, results: list[BenchmarkResult] | None = None) -> None:
    print("\n" + "=" * 70)
    print("PROMPTSHIELD BENCHMARK RESULTS")
    print("=" * 70)

    print(f"\n📊 Overall")
    print(f"   Total prompts tested : {metrics['total_prompts']}")
    print(f"   Recall (attacks)     : {metrics['recall_attacks'] * 100:.1f}%")
    print(f"   False positive rate  : {metrics['false_positive_rate'] * 100:.1f}%")
    print(f"   Flag rate            : {metrics['flag_rate'] * 100:.1f}%")

    print(f"\n📍 Layer Distribution")
    layer_rows = [
        [layer, d["count"], f"{d['pct']}%"]
        for layer, d in metrics["layer_distribution"].items()
        if d["count"] > 0
    ]
    print(
        tabulate(
            layer_rows,
            headers=["Layer", "Count", "% of requests"],
            tablefmt="rounded_outline",
        )
    )

    print(f"\n⏱  Latency by Layer (ms)")
    latency_rows = [
        [
            layer,
            f"{d['p50_ms']:.1f}",
            f"{d['p95_ms']:.1f}",
            f"{d['p99_ms']:.1f}",
            f"{d['mean_ms']:.1f}",
        ]
        for layer, d in metrics["latency_by_layer"].items()
    ]
    print(
        tabulate(
            latency_rows,
            headers=["Layer", "p50", "p95", "p99", "mean"],
            tablefmt="rounded_outline",
        )
    )

    print(f"\n🎯 Attacks blocked by layer")
    for layer, count in metrics["attacks_blocked_by_layer"].items():
        print(f"   {layer:12s} : {count}")

    if metrics["ambiguous_distribution"]:
        print(f"\n🔍 Ambiguous prompts verdict distribution")
        for verdict, count in metrics["ambiguous_distribution"].items():
            print(f"   {verdict:10s} : {count}")

    # Print detailed false positive information if results are provided
    if results:
        false_positives = [
            r for r in results if r.expected == "safe" and r.verdict != "pass"
        ]

        if false_positives:
            print(
                f"\n⚠️  False positive details ({len(false_positives)} safe prompts incorrectly blocked):"
            )
            for r in false_positives:
                print(f"\n   Prompt  : {r.prompt}")
                print(f"   Verdict : {r.verdict} via {r.pipeline_layer}")
                print(f"   Reason  : {r.reason}")
    elif metrics["false_positive_prompts"]:
        # Fallback to old behavior if results not provided
        print(
            f"\n⚠️  False positives ({len(metrics['false_positive_prompts'])} safe prompts incorrectly blocked):"
        )
        for p in metrics["false_positive_prompts"]:
            print(f"   - {p[:80]}")

    print("\n" + "=" * 70)
