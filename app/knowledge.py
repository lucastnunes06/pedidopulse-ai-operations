"""RAG leve: TF-IDF sobre políticas FICTÍCIAS; retorna evidências e scores."""
from __future__ import annotations
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass(frozen=True)
class Policy:
    id: str
    title: str
    body: str

POLICIES = [
    Policy("POL-01", "Atraso previsto", "Se o risco de atraso for alto, conferir tempo estimado, verificar causa e preparar comunicação objetiva. A ferramenta apenas recomenda; a equipe responsável decide."),
    Policy("POL-02", "Fila no restaurante", "Quando a fila de preparo estiver alta, consultar disponibilidade do restaurante e informar a estimativa com transparência. Não inventar prazos."),
    Policy("POL-03", "Chuva e trânsito", "Em condições climáticas adversas ou trânsito intenso, priorizar segurança de todos os envolvidos, verificar novas estimativas e evitar promessas de entrega não verificadas."),
    Policy("POL-04", "Reembolso e compensação", "Não aprovar reembolso, cancelamento ou compensação automaticamente. Encaminhar qualquer decisão financeira para uma pessoa autorizada após validação da situação."),
    Policy("POL-05", "Privacidade dos clientes", "Não expor telefone, endereço, e-mail ou outros dados pessoais em respostas de IA ou logs. Minimizar os dados enviados a provedores externos."),
    Policy("POL-06", "Acompanhamento operacional", "Pedidos com risco baixo devem continuar monitorados. Risco alto exige revisão humana e registro da justificativa; recomendações são auxiliares."),
]

class Retriever:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), strip_accents="unicode")
        self.matrix = self.vectorizer.fit_transform([f"{p.title}. {p.body}" for p in POLICIES])

    def search(self, query: str, k: int = 3) -> list[dict]:
        sim = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        indices = sim.argsort()[::-1][:k]
        return [{"id": POLICIES[i].id, "title": POLICIES[i].title,
                 "text": POLICIES[i].body, "score": round(float(sim[i]), 3)}
                for i in indices if sim[i] > 0]
