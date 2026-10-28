# Decisões, experimentos e limitações

Este documento registra mudanças verificáveis no projeto. Ele não é um diário de desenvolvimento retroativo: os experimentos listados aqui podem ser reproduzidos com o código atual.

## 1. O que a classificação resolve (e o que não resolve)

A demonstração usa uma regressão logística para estimar a chance de atraso em pedidos **fictícios**. Escolhi uma arquitetura simples de entender: variáveis numéricas padronizadas, categoria de clima com one-hot encoding e um classificador linear. Isso permite acompanhar o pré-processamento, os scores e o ponto de corte sem adicionar um modelo mais complexo só por adicionar.

O rótulo de atraso é criado por uma função do próprio gerador sintético (`app/data.py`). O modelo pode aprender essa relação e ter bons resultados sem que isso diga nada sobre pedidos reais.

## 2. O limiar é uma escolha, não uma propriedade do modelo

O modelo calcula probabilidades; a regra que decide quais pedidos revisar depende de um limiar. O `train.py` escolhe esse limiar **na validação**, atribuindo custo fictício de 5 unidades a um falso negativo e 1 a um falso positivo. O conjunto de teste não participa da escolha.

Criei `scripts/threshold_experiment.py` para examinar o efeito de pesos alternativos (FN = 1, 3, 5, 10, mantendo FP = 1). O script reaproveita o modelo treinado, seleciona um limiar na validação e avalia esse limiar no conjunto de teste.

| Peso do falso negativo | Limiar | Recall no teste | Precisão no teste | Pedidos enviados para revisão (em 800) | Falsos positivos |
|---:|---:|---:|---:|---:|---:|
| 1 | 0,46 | 40,3% | 63,7% | 157 | 57 |
| 3 | 0,28 | 71,0% | 54,1% | 325 | 149 |
| 5 | 0,16 | 87,9% | 40,0% | 545 | 327 |
| 10 | 0,12 | 93,5% | 36,8% | 630 | 398 |

**O que isso mostra:** no cenário FN=5, encontrar mais atrasos exige revisar muitos pedidos que não atrasariam. A configuração FN=1 alivia a fila, mas deixa mais atrasos passarem. Não existe limiar “ideal” sem dados reais, capacidade da equipe de revisão e uma decisão responsável sobre custos.

Reproduza:

```bash
python scripts/train.py
python -m scripts.threshold_experiment
pytest -q
```

Dados do estudo: [`artifacts/threshold_study.json`](../artifacts/threshold_study.json). A análise não alterou o limiar padrão de 0,16, usado para comparar com o resultado anterior.

## 3. Por que regras antes de LLM

O sistema recupera trechos de seis políticas fictícias por TF-IDF e devolve seus IDs. **A geração com Groq é opcional e produz apenas texto explicativo**. As ações de triagem são definidas por regras de aplicação; o sistema não pode fazer cancelamentos, reembolsos nem contatos reais.

Essa divisão é uma simplificação deliberada: permite testar a triagem sem depender de rede ou de respostas não determinísticas. Também significa que o projeto **não é um agente autônomo**. O filtro de prompt injection contém apenas padrões simples e não substitui uma análise de segurança.

## 4. Uma melhoria concreta de manutenção no front-end

A primeira versão do painel tinha HTML, CSS e JavaScript reunidos em `app/static/index.html`. Isso dificultava localizar estilos, revisar eventos e testar mudanças na interface. Separei os arquivos em:

- `index.html`: estrutura e elementos;
- `styles.css`: apresentação e responsividade;
- `app.js`: carregamento, filtro e solicitação de triagem.

Como o navegador precisa solicitar esses arquivos separadamente, a API passou a servir `/static/` por meio de `StaticFiles` do FastAPI. Também incluí navegação pela tecla Enter/Espaço nas linhas de pedidos, estados de carregamento e proteção contra respostas assíncronas chegando fora de ordem. O texto vindo da API entra no DOM usando `textContent`, não HTML arbitrário.

## 5. Verificações realizadas

- Testes de geração reproduzível, endpoints, limites de entrada e segurança ilustrativa.
- Testes do cálculo de confusão e da escolha do limiar de revisão.
- Validação da rota e dos assets estáticos no FastAPI.
- Teste visual local com navegador Chromium, usando dados de demonstração.

Os testes não substituem uma avaliação de UX, segurança ou qualidade de ML em produção. Novos experimentos úteis: validação com dados reais autorizados, calibração de probabilidade, análise de drift, teste adversarial e avaliação humana da utilidade das recomendações.

## 6. Transparência sobre o processo

A implementação inicial e parte da documentação tiveram auxílio de ferramentas de IA. As mudanças e experimentos deste repositório são apresentados com scripts executáveis e resultados verificáveis, sem alegar um histórico de desenvolvimento ou validação que não ocorreu.
