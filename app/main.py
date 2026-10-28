"""API pública somente para dados fictícios de demonstração."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from .service import list_orders, triage, metrics

app = FastAPI(title="PedidoPulse — AI Operations Copilot", version="1.0.0",
              description="Demonstração com dados sintéticos; sem relação com o iFood")

class TriageInput(BaseModel):
    note: str = Field(default="", max_length=500)
    mode: str = Field(default="offline", pattern="^(offline|groq)$")

@app.get("/", response_class=HTMLResponse)
def home():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/api/orders")
def orders():
    return {"synthetic": True, "orders": list_orders()}

@app.get("/api/metrics")
def quality_metrics():
    return metrics()

@app.post("/api/triage/{order_id}")
def triage_order(order_id: str, body: TriageInput):
    try:
        return triage(order_id, body.note, body.mode)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
