"""Treino com separação cronológica, tuning no conjunto de validação e teste intocado."""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, brier_score_loss, confusion_matrix
from .data import FEATURES, make_orders

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
NUM = [x for x in FEATURES if x != "weather"]

def _preprocessor():
    return ColumnTransformer([
        ("num", StandardScaler(), NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["weather"]),
    ])

def train(seed: int = 42, n: int = 4000) -> dict:
    ART.mkdir(exist_ok=True)
    df = make_orders(n=n, seed=seed).sort_values("created_at").reset_index(drop=True)
    train_end, valid_end = int(.60 * n), int(.80 * n)
    tr, val, test = df.iloc[:train_end], df.iloc[train_end:valid_end], df.iloc[valid_end:]
    model = Pipeline([("features", _preprocessor()), ("classifier", LogisticRegression(max_iter=500, random_state=seed))])
    model.fit(tr[FEATURES], tr["late"])
    scores_val = model.predict_proba(val[FEATURES])[:, 1]
    # FN custa cinco unidades simuladas; FP uma. Apenas escolha de projeto, não custo real.
    candidates = np.arange(.12, .66, .02)
    losses = [5 * ((val["late"].values == 1) & (scores_val < t)).sum() +
              ((val["late"].values == 0) & (scores_val >= t)).sum() for t in candidates]
    threshold = float(candidates[int(np.argmin(losses))])
    scores = model.predict_proba(test[FEATURES])[:, 1]
    pred = (scores >= threshold).astype(int)
    # baseline operacional arbitrário: acima de 7 km ou tempestade.
    baseline = ((test["distance_km"].to_numpy() > 7) | (test["weather"].to_numpy() == "tempestade")).astype(int)
    def report(y, p, prob=None):
        result = {"precision": round(float(precision_score(y, p, zero_division=0)), 4),
                  "recall": round(float(recall_score(y, p, zero_division=0)), 4),
                  "f1": round(float(f1_score(y, p, zero_division=0)), 4),
                  "confusion_matrix": confusion_matrix(y, p).tolist()}
        if prob is not None:
            result["roc_auc"] = round(float(roc_auc_score(y, prob)), 4)
            result["brier_score"] = round(float(brier_score_loss(y, prob)), 4)
        return result
    metrics = {
        "dataset": "100% sintético, gerado com seed fixa; não representa operações reais",
        "seed": seed, "train_rows": len(tr), "validation_rows": len(val), "test_rows": len(test),
        "holdout": "últimos 20% das observações, sem ajuste de hiperparâmetros no teste",
        "threshold": round(threshold, 3), "cost_assumption": "FN=5, FP=1 (pesos fictícios)",
        "model": report(test["late"].values, pred, scores),
        "baseline": report(test["late"].values, baseline),
        "positives_test": int(test["late"].sum()),
        "note": "Métricas em dados simulados. Não equivalem a desempenho em produção."
    }
    joblib.dump({"model": model, "threshold": threshold}, ART / "risk_model.joblib")
    (ART / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    # Exemplos independentes para demo, sem rótulo/PII real.
    demo = make_orders(36, seed=seed + 100)
    (ROOT / "data").mkdir(exist_ok=True)
    demo.to_csv(ROOT / "data" / "demo_orders.csv", index=False)
    return metrics

def load_model():
    p = ART / "risk_model.joblib"
    if not p.exists():
        raise FileNotFoundError("Modelo ausente. Execute: python scripts/train.py")
    return joblib.load(p)
