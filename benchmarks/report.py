import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
from tabulate import tabulate

from .runner import BenchmarkResult

SWEEP_RESULTS_PATH: Path = Path("benchmark_results/sweep_results.json")

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_csv(
    results: list[BenchmarkResult],
    path: str = "benchmark_results/benchmark_results.csv",
) -> None:
    df = pd.DataFrame([asdict(r) for r in results])
    df.to_csv(path, index=False)
    print(f"\n✓ Raw results saved to {path}")


def save_json(
    metrics: dict, path: str = "benchmark_results/benchmark_summary.json"
) -> None:
    summary_path = Path(path)
    summary_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"✓ Summary saved to {path}")


def save_sweep_results(
    ranked: list[dict[str, Any]],
    sweep_config: dict[str, Any],
) -> None:
    payload: dict[str, Any] = {
        "sweep_config": sweep_config,
        "results": [
            {
                "rank": rank,
                **{k: v for k, v in entry.items() if k != "full_metrics"},
                "full_metrics": entry["full_metrics"],
            }
            for rank, entry in enumerate(ranked, 1)
        ],
    }

    SWEEP_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SWEEP_RESULTS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"✓ Full results saved to {SWEEP_RESULTS_PATH}")


# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------


def print_report(metrics: dict, results: list[BenchmarkResult] | None = None) -> None:
    print("\n" + "=" * 70)
    print("PROMPTSHIELD BENCHMARK RESULTS")
    print("=" * 70)

    print("\n📊 Overall")
    print(f"   Total prompts tested : {metrics['total_prompts']}")
    print(f"   Recall (attacks)     : {metrics['recall_attacks'] * 100:.1f}%")
    print(f"   False positive rate  : {metrics['false_positive_rate'] * 100:.1f}%")
    print(f"   Flag rate            : {metrics['flag_rate'] * 100:.1f}%")

    print("\n📍 Layer Distribution")
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

    print("\n⏱  Latency by Layer (ms)")
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

    print("\n🎯 Attacks blocked by layer")
    for layer, count in metrics["attacks_blocked_by_layer"].items():
        print(f"   {layer:12s} : {count}")

    if metrics["ambiguous_distribution"]:
        print("\n🔍 Ambiguous prompts verdict distribution")
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


def print_ranked_table(ranked: list[dict[str, Any]]) -> None:
    rows = []
    for rank, entry in enumerate(ranked, 1):
        ld = entry["layer_distribution"]

        def _pct(layer: str) -> str:
            return f"{ld.get(layer, {}).get('pct', 0.0):.0f}%"

        lp = entry["latency_p95_ms"]

        def _p95(layer: str) -> str:
            val = lp.get(layer)
            return f"{val:.0f}" if val is not None else "—"

        model_short = entry["model"]
        if len(model_short) > 20:
            model_short = "…" + model_short[-19:]

        llm_short = entry["llm_model"]
        if len(llm_short) > 15:
            llm_short = "…" + llm_short[-14:]

        rows.append(
            [
                rank,
                model_short,
                llm_short,
                entry["threshold"],
                f"{entry['recall'] * 100:.1f}%",
                f"{entry['fpr'] * 100:.1f}%",
                f"{entry['flag_rate'] * 100:.1f}%",
                _pct("regex"),
                _pct("embedding"),
                _pct("llm"),
                _p95("regex"),
                _p95("embedding"),
                _p95("llm"),
                f"{entry['composite']:+.4f}",
            ]
        )

    headers = [
        "#",
        "Model",
        "LLM",
        "Thresh",
        "Recall",
        "FPR",
        "FlagRate",
        "Reg%",
        "Emb%",
        "LLM%",
        "p95 Reg",
        "p95 Emb",
        "p95 LLM",
        "Composite ↓",
    ]

    print("\n" + "=" * 72)
    print("SWEEP RESULTS  —  ranked by  recall − (2 × fpr)")
    print("=" * 72)
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline", floatfmt=".4f"))
    print()

    best = ranked[0]
    print(
        f"🏆  Best configuration:\n"
        f"   Model     : {best['model']}\n"
        f"   LLM       : {best['llm_model']}\n"
        f"   Threshold : {best['threshold']}\n"
        f"   Composite : {best['composite']:+.4f}  "
        f"(recall={best['recall'] * 100:.1f}%, fpr={best['fpr'] * 100:.1f}%)"
    )
    print()
