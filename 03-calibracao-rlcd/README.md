# 03 — Calibração e RLCD

## RLCD vs. RLHF vs. RLVR

| Método | Otimiza para | Resultado típico |
| --- | --- | --- |
| **RLHF** (LLMs de chat) | Preferência humana — qual resposta os avaliadores preferem | Respostas assertivas e "agradáveis" tendem a ganhar, mesmo sem suporte real — leva a *overconfidence* e sycophancy |
| **DPO** | Mesma preferência humana, otimizada direto sobre pares (sem reward model explícito) | Mesmo viés do RLHF, herdado dos pares de preferência |
| **RLVR** (reasoning models) | Verificabilidade programática — a resposta está certa ou errada | Bom para domínios com verificação barata (matemática, código); não diz nada sobre calibração |
| **RLCD** (Jev/Kev) | Calibração epistêmica — a probabilidade declarada deve bater com a taxa de acerto real | Se o modelo diz 0.8 de confiança, ele deve acertar ~80% das vezes num conjunto grande de casos parecidos |

A diferença central: RLHF pergunta "qual resposta um humano prefere?" — um proxy estilístico.
RLCD pergunta "essa probabilidade é honesta?" — um proxy estatístico, medido contra
**Strictly Proper Scoring Rules** (o Brier Score é uma delas): a única forma de recompensa em
que o ótimo matemático coincide exatamente com dizer a verdade sobre sua própria incerteza.
Um modelo treinado com uma "proper scoring rule" não ganha nada exagerando confiança — ao
contrário de um modelo otimizado para "parecer convincente".

## Brier Score e ECE — as duas métricas de calibração

**Brier Score** = erro quadrático médio entre a probabilidade prevista e o resultado real
(1 = classe correta, 0 = demais). Penaliza tanto errar a classe quanto errar a confiança —
dizer 0.99 e errar dói muito mais que dizer 0.55 e errar.

**ECE (Expected Calibration Error)** agrupa previsões em faixas de confiança (bins) e mede o
desvio médio entre a confiança declarada e a acurácia observada em cada faixa. Um modelo
perfeitamente calibrado tem ECE = 0: entre todas as vezes que ele disse "estou 70% confiante",
ele acertou exatamente 70% delas.

## Pipeline de dados sintéticos (por que é necessário)

RLCD precisa de um "gabarito" (ground truth) livre de ambiguidade em escala massiva — algo que
avaliadores humanos não garantem sozinhos (humanos discordam entre si, o que introduz ruído na
própria calibração-alvo). A abordagem documentada é gerar categorias/regras fechadas
algoritmicamente e usar LLMs para fabricar cenários simulando cada categoria, garantindo que o
rótulo seja inquestionável por construção — o oposto do RLHF, onde o "rótulo" é uma preferência
subjetiva.

## Prática: medindo ECE de verdade no Kev

[`medir_calibracao.py`](medir_calibracao.py) implementa o cálculo do zero contra um Kev local
(mesmo setup do tópico 02): ~24 afirmações com rótulo verdadeiro/falso conhecido, pergunta
`Noul` "esta afirmação é verdadeira?", agrupamento em bins de confiança, e o ECE calculado na
mão — para entender exatamente o que o número mede, não só aceitar o valor publicado.

```bash
# aba 1 (se ainda não estiver rodando)
uv run --group kev-local python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009

# aba 2
uv run python 03-calibracao-rlcd/medir_calibracao.py
```

**O que observar:** nosso conjunto é pequeno e propositalmente simples (fatos gerais, não o
domínio de treino do Kev), então não é uma réplica do número oficial — é para ver o *mecanismo*.
Compare o ECE medido aqui com os valores reais publicados no
[model card do Kev-0.8B](https://huggingface.co/jaredpalmer/kev-0.8b): ~0.033 "as served" e
~0.049–0.054 fora de distribuição, sobre milhares de exemplos. Um ECE muito pior no nosso teste
não significa que o modelo é ruim — pode significar que nossa amostra é pequena demais, ou que
"fatos gerais de cultura" estão fora do que o modelo foi treinado/calibrado para julgar
(lembrar: Kev-0.8B foi treinado majoritariamente em Banking77, BoolQ, AG News, MNLI, SST-5 e
Yelp — domínios bem diferentes de trivia geral).
