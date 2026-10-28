"""Geração reproduzível de pedidos SINTÉTICOS. Nenhum dado é do iFood."""
from __future__ import annotations
import numpy as np
import pandas as pd

FEATURES = ["hour", "distance_km", "weather", "courier_load", "kitchen_queue", "traffic_index", "elapsed_minutes", "promised_minutes"]
WEATHER = ["sol", "chuva", "tempestade"]

def make_orders(n: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hour = rng.integers(9, 24, n)
    distance = rng.uniform(0.7, 12.0, n)
    weather = rng.choice(WEATHER, size=n, p=[0.68, 0.27, 0.05])
    peak = ((hour >= 11) & (hour <= 13)) | ((hour >= 18) & (hour <= 21))
    courier_load = np.clip(rng.poisson(1.0 + 0.55 * peak), 0, 5)
    kitchen_queue = np.clip(rng.poisson(2.5 + 3.0 * peak), 0, 16)
    traffic = np.clip(rng.normal(1.05 + 0.27 * peak + 0.25 * (weather != "sol"), .19), .65, 2.3)
    elapsed = rng.integers(3, 31, n)
    promised = rng.integers(25, 66, n)
    # Relação sintética com ruído: não é regra empresarial nem dados de operação real.
    score = (-4.4 + 0.19 * distance + .46 * courier_load + .095 * kitchen_queue
             + .95 * (traffic - 1) + .045 * elapsed - .027 * (promised - 40)
             + .60 * (weather == "chuva") + 1.2 * (weather == "tempestade")
             + 0.35 * peak + rng.normal(0, .27, n))
    prob = 1 / (1 + np.exp(-score))
    late = rng.binomial(1, prob)
    base = pd.Timestamp("2026-09-01T09:00:00")
    return pd.DataFrame({
        "order_id": [f"PED-{i:05d}" for i in range(1, n + 1)],
        "created_at": [(base + pd.Timedelta(minutes=int(i * 8))).isoformat() for i in range(n)],
        "hour": hour, "distance_km": np.round(distance, 2), "weather": weather,
        "courier_load": courier_load, "kitchen_queue": kitchen_queue,
        "traffic_index": np.round(traffic, 2), "elapsed_minutes": elapsed,
        "promised_minutes": promised, "late": late,
    })
