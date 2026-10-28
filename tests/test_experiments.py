"""Tests added during the threshold trade-off and API maintenance review."""
from fastapi.testclient import TestClient
import numpy as np

from app.main import app
from app.service import triage
from scripts.threshold_experiment import confusion, run, select_threshold

client = TestClient(app)


def test_confusion_accounts_for_all_rows():
    result = confusion(np.array([1, 1, 0, 0]), np.array([True, False, True, False]))
    assert result == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}


def test_threshold_selection_uses_explicit_error_costs():
    labels = np.array([1, 0, 1, 0])
    probabilities = np.array([0.15, 0.22, 0.48, 0.58])
    low_fn_cost, _ = select_threshold(labels, probabilities, fn_cost=1)
    high_fn_cost, _ = select_threshold(labels, probabilities, fn_cost=10)
    assert high_fn_cost <= low_fn_cost


def test_sensitivity_study_is_reproducible_and_counts_reviews():
    study = run()
    assert len(study["scenarios"]) == 4
    for scenario in study["scenarios"]:
        cm = scenario["test_confusion"]
        assert sum(cm.values()) == 800
        assert scenario["test_review_queue"] == cm["tp"] + cm["fp"]


def test_rejects_notes_over_character_limit():
    response = client.post("/api/triage/PED-00001", json={"note": "x" * 501})
    assert response.status_code == 422


def test_recommendations_do_not_execute_external_actions():
    result = triage("PED-00001", "fila alta", "offline")
    assert result["provider"] == "regras_offline_sem_llm"
    assert all(a not in {"REEMBOLSAR", "CANCELAR", "CONTATAR_CLIENTE"} for a in result["actions"])


def test_frontend_assets_available_and_not_inlined():
    page = client.get("/")
    assert page.status_code == 200
    assert 'src="/static/app.js"' in page.text
    assert 'href="/static/styles.css"' in page.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
