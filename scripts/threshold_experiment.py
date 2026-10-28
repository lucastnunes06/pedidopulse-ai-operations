"""Compare validation-selected thresholds under hypothetical error costs.

This is a sensitivity exercise on synthetic labels, not an operational cost study.
The test partition is evaluated only after a threshold is picked on validation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score

from app.data import FEATURES, make_orders
from app.model import ROOT, load_model


CANDIDATES = np.round(np.arange(0.12, 0.66, 0.02), 2)
COST_SCENARIOS = (1, 3, 5, 10)


def confusion(y_true: np.ndarray, positive: np.ndarray) -> dict[str, int]:
    return {
        "tp": int(((y_true == 1) & positive).sum()),
        "fp": int(((y_true == 0) & positive).sum()),
        "tn": int(((y_true == 0) & ~positive).sum()),
        "fn": int(((y_true == 1) & ~positive).sum()),
    }


def select_threshold(y: np.ndarray, scores: np.ndarray, fn_cost: int) -> tuple[float, int]:
    """Select the first minimum-cost threshold using validation labels only."""
    costs = []
    for threshold in CANDIDATES:
        cm = confusion(y, scores >= threshold)
        costs.append(fn_cost * cm["fn"] + cm["fp"])
    best = int(np.argmin(costs))
    return float(CANDIDATES[best]), int(costs[best])


def run() -> dict:
    dataset = make_orders(n=4000, seed=42).sort_values("created_at").reset_index(drop=True)
    valid, test = dataset.iloc[2400:3200], dataset.iloc[3200:]
    model = load_model()["model"]
    validation_scores = model.predict_proba(valid[FEATURES])[:, 1]
    test_scores = model.predict_proba(test[FEATURES])[:, 1]
    y_valid = valid["late"].to_numpy()
    y_test = test["late"].to_numpy()

    results = []
    for fn_cost in COST_SCENARIOS:
        threshold, validation_cost = select_threshold(y_valid, validation_scores, fn_cost)
        predicted = test_scores >= threshold
        cm = confusion(y_test, predicted)
        results.append({
            "false_negative_weight": fn_cost,
            "false_positive_weight": 1,
            "threshold_from_validation": threshold,
            "validation_cost_units": validation_cost,
            "test_precision": round(float(precision_score(y_test, predicted, zero_division=0)), 4),
            "test_recall": round(float(recall_score(y_test, predicted, zero_division=0)), 4),
            "test_f1": round(float(f1_score(y_test, predicted, zero_division=0)), 4),
            "test_confusion": cm,
            "test_review_queue": cm["tp"] + cm["fp"],
        })

    payload = {
        "scope": "Sensitivity experiment; 100% synthetic data and hypothetical costs",
        "split": "chronological: train 2400, validation 800, test 800",
        "choice": "threshold selected on validation only; test held out",
        "candidate_thresholds": CANDIDATES.tolist(),
        "scenarios": results,
        "note": "The model was already trained with seed 42. No retraining or production impact claim.",
    }
    destination = ROOT / "artifacts" / "threshold_study.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    study = run()
    for s in study["scenarios"]:
        print(f"FN×{s['false_negative_weight']}: t={s['threshold_from_validation']:.2f} "
              f"recall={s['test_recall']:.3f} precision={s['test_precision']:.3f} "
              f"review={s['test_review_queue']} FP={s['test_confusion']['fp']}")
