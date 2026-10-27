# PedidoPulse — AI Operations Copilot

> **Da previsão à decisão, com evidências.** Simulador de risco de atraso e triagem operacional usando Machine Learning + busca de políticas (RAG lexical) + integração opcional com LLM.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688) ![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-FF9900) ![Status](https://img.shields.io/badge/status-demo%20local-6d78a7)

**⚠️ Projeto independente de portfólio.** Não afiliado ao iFood. Todos os pedidos, políticas e resultados são fictícios; não existem clientes reais, ações externas, economia financeira ou dados de produção.

## O problema

Uma operação de entregas recebe múltiplos sinais e precisa priorizar o que merece atenção. Como combinar um **modelo de risco de atraso** com **recomendações sustentadas por políticas**, preservando rastreabilidade e evitando decisões automáticas indevidas?

## O que foi construído

- **Pipeline de ML**: geração de dados sintéticos com seed, extração de features, split temporal **60/20/20**, regressão logística, otimização do limiar em validação e comparação com baseline no teste.
- **RAG auditável**: indexação das normas fictícias com TF-IDF, top-k e evidências recuperadas por ID.
- **Copiloto operacional**: Python/FastAPI, regras de escalonamento e possibilidade de gerar explicações com **Groq API** (somente se o usuário habilitar uma chave).
- **Guardrails**: bloqueio ilustrativo de prompt injection, máscara de e-mails/telefones, sem reembolso ou cancelamento automático.
- **Painel web interativo**: pedidos ordenados por risco, filtro, triagem e visualização das referências.
- **Testes e CI**: `pytest`, testes de API, avaliação de retrieval, workflow GitHub Actions.

## Demo local

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate | Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/train.py
uvicorn app.main:app --reload
```

Abra **http://127.0.0.1:8000** para o dashboard e **http://127.0.0.1:8000/docs** para Swagger.

O repositório também inclui um modelo treinado e pedidos de exemplo; `train.py` recria os artefatos. Não é necessário ter API key.

## Execução e validação

```bash
pytest -q
python scripts/evaluate_rag.py
```

Para testar a integração REAL com LLM (opcional): configure `GROQ_API_KEY` via variável de ambiente e envie `mode="groq"` em `POST /api/triage/PED-00001`. **Nunca publique sua chave**, e evite transmitir informação pessoal.

```bash
curl -X POST http://127.0.0.1:8000/api/triage/PED-00001   -H 'Content-Type: application/json'   -d '{"note":"Fila alta no restaurante", "mode":"offline"}'
```

### Métricas verificáveis

Os resultados reais **desta simulação** são gravados automaticamente em `artifacts/metrics.json`; `artifacts/rag_eval.json` registra a suíte lexical de recuperação e segurança. O painel lê esses números, não valores inseridos manualmente.

**Atenção:** resultados em dados sintéticos não permitem inferir ganhos financeiros, qualidade real ou capacidade de operar no iFood.

## Arquitetura

Veja [docs/ARQUITETURA.md](docs/ARQUITETURA.md), incluindo diagrama, trade-offs e limitações.

```text
app/          API, modelo, busca lexical, guardrails e serviço de triagem
app/static/   dashboard web sem dependência de CDN
scripts/      treino reproduzível e avaliação RAG
artifacts/    modelo e métricas geradas
data/         amostra de pedidos fictícios
tests/        testes automatizados
.github/      testes de CI
```

## Próximos experimentos

1. Calibrar probabilidades e testar drift, usando dados autorizados.
2. Comparar retrieval lexical com embeddings e rerankers.
3. Adicionar avaliação sistemática de alucinações para a LLM opcional.
4. Publicar um vídeo curto com cenário, decisão e limitações.

---

Feito como estudo autoral de **Engenharia de IA aplicada a produtos de logística**.
