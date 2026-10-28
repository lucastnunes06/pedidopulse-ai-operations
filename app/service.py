from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import json
import pandas as pd
from .data import FEATURES
from .knowledge import Retriever
from .llm import injection_detected, redact_pii, optional_groq_generate
from .model import ROOT, load_model

@lru_cache(maxsize=1)
def state():
    payload = load_model()
    df = pd.read_csv(ROOT / "data" / "demo_orders.csv")
    probabilities = payload["model"].predict_proba(df[FEATURES])[:, 1]
    orders = df.drop(columns=["late"]).to_dict(orient="records")
    for order, prob in zip(orders, probabilities):
        order["risk"] = round(float(prob), 4)
        order["risk_label"] = "Alto" if prob >= payload["threshold"] else "Baixo"
    return {"model": payload, "orders": orders, "retriever": Retriever()}

def list_orders():
    return sorted(state()["orders"], key=lambda d: d["risk"], reverse=True)

def triage(order_id: str, note: str = "", mode: str = "offline") -> dict:
    order = next((x for x in state()["orders"] if x["order_id"] == order_id), None)
    if not order:
        raise KeyError("Pedido de simulação não encontrado")
    if injection_detected(note):
        return {"order_id": order_id, "status": "blocked", "message": "Entrada contém tentativa de instrução indevida; encaminhar para revisão humana.", "citations": [], "provider": "guardrail", "actions": ["REVISAR_MANUALMENTE"]}
    risk = order["risk"]
    context = f"atraso entrega trânsito {order['weather']} fila restaurante {order['kitchen_queue']} segurança revisão humana {redact_pii(note)}"
    evidence = state()["retriever"].search(context)
    if not evidence:
        return {"order_id": order_id, "status": "no_evidence", "message": "Sem evidência recuperada. Solicitar revisão humana.", "citations": [], "provider": "retrieval", "actions": ["REVISAR_MANUALMENTE"]}
    high = order["risk_label"] == "Alto"
    actions = ["CONFERIR_ESTIMATIVA", "REVISAR_MANUALMENTE"] if high else ["MONITORAR_PEDIDO"]
    if high and order["kitchen_queue"] >= 6:
        actions.insert(1, "VERIFICAR_FILA_COM_RESTAURANTE")
    if mode == "groq":
        message = optional_groq_generate(context, evidence, risk)
        # Qualquer texto da LLM permanece recomendação; ações são só do motor determinístico.
        provider = "groq"
    else:
        message = (f"Risco estimado de atraso: {risk:.0%} ({order['risk_label'].lower()}). "
                   + ("Recomendo conferir o andamento e escalar para análise humana antes de qualquer decisão. " if high
                      else "Recomendo continuar acompanhando o pedido. ")
                   + f"Políticas consultadas: {', '.join('['+p['id']+']' for p in evidence)}. "
                   + "Este sistema não executa reembolsos nem contatos reais.")
        provider = "regras_offline_sem_llm"
    return {"order_id": order_id, "status": "ok", "message": message,
            "citations": evidence, "provider": provider, "actions": actions,
            "risk": risk, "human_review_required": high}

def metrics():
    return json.loads((ROOT / "artifacts" / "metrics.json").read_text(encoding="utf-8"))
