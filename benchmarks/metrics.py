from dataclasses import asdict

import numpy as np
import pandas as pd

from .runner import BenchmarkResult


def compute_metrics(results: list[BenchmarkResult]) -> dict:
    df = pd.DataFrame([asdict(r) for r in results])

    # --- Per-layer latency ---
    layers = ["regex", "embedding", "llm", "none"]
    latency_by_layer = {}
    for layer in layers:
        subset = df[df["pipeline_layer"] == layer]["latency_ms"]
        if len(subset) > 0:
            latency_by_layer[layer] = {
                "count": len(subset),
                "p50_ms": float(np.percentile(subset, 50)),
                "p95_ms": float(np.percentile(subset, 95)),
                "p99_ms": float(np.percentile(subset, 99)),
                "mean_ms": float(subset.mean()),
            }

    # --- Layer distribution (% of requests stopped at each layer) ---
    total = len(df)
    layer_dist = {
        layer: {
            "count": int((df["pipeline_layer"] == layer).sum()),
            "pct": round(100 * (df["pipeline_layer"] == layer).sum() / total, 1),
        }
        for layer in layers
    }

    # --- Recall on attacks ---
    attacks = df[df["expected"] == "attack"]
    recall = (
        float((attacks["verdict"] == "blocked").sum() / len(attacks))
        if len(attacks) > 0
        else 0.0
    )
    attacks_blocked_by_layer = (
        attacks.groupby("pipeline_layer")["verdict"].count().to_dict()
    )

    # --- False positive rate on safe prompts ---
    safe = df[df["expected"] == "safe"]
    fp_rate = (
        float((safe["verdict"] != "pass").sum() / len(safe)) if len(safe) > 0 else 0.0
    )
    false_positives = safe[safe["verdict"] != "pass"]["prompt"].tolist()

    # --- Ambiguous prompt distribution ---
    ambiguous = df[df["expected"] == "ambiguous"]
    ambiguous_dist = (
        ambiguous["verdict"].value_counts().to_dict() if len(ambiguous) > 0 else {}
    )

    # --- Flag rate ---
    flag_rate = float((df["verdict"] == "flag").sum() / total)

    return {
        "total_prompts": total,
        "recall_attacks": round(recall, 4),
        "false_positive_rate": round(fp_rate, 4),
        "flag_rate": round(flag_rate, 4),
        "layer_distribution": layer_dist,
        "latency_by_layer": latency_by_layer,
        "attacks_blocked_by_layer": attacks_blocked_by_layer,
        "false_positive_prompts": false_positives,
        "ambiguous_distribution": ambiguous_dist,
    }
