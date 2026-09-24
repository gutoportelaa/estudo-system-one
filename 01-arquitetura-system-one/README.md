# 01 — Arquitetura System One

> **Verificado em 24/09/2026** contra fontes primárias reais: PyPI (`typesafe-sdk`), Hugging Face
> (`jaredpalmer/kev-0.5b`) e GitHub (`jaredpalmer/kev`). Os detalhes de arquitetura abaixo batem
> com o que o model card do Kev descreve explicitamente como réplica inferida da arquitetura do
> Jev — a TypeSafe nunca publicou os pesos nem um paper da arquitetura do Jev em si.

## O problema que o Jev resolve

Um LLM tradicional, mesmo em "JSON mode"/structured output, ainda:
1. gera token a token (latência escala com o tamanho da resposta);
2. cobra por tokens de saída (tipicamente mais caro que entrada);
3. pode falhar em produzir um schema válido sob pressão (schema hallucination);
4. tende a ser *overconfident* — diz "tenho certeza" sem que isso corresponda à taxa de acerto real.

Se tudo que você precisa é **uma decisão tipada** (é spam? qual departamento? qual a urgência
de 0 a 1?), pagar o custo de uma geração de texto inteira — e ainda arriscar um schema quebrado
— é desperdício. O Jev/Kev ataca exatamente esse caso de uso.

## Mecanismo: single forward pass + block-causal attention

Um LLM comum gasta a maior parte do tempo no **decode**: gerar um token, recomputar,
gerar o próximo, repetir. O Jev elimina essa fase inteira.

```
LLM tradicional (System Two)
  state+pergunta → [prefill] → [decode: token, token, token, ... token] → parsear JSON
                                 ↑ cada token depende do anterior (sequencial)

Jev/Kev (System One)
  state + N perguntas → [1 forward pass] → N distribuições de probabilidade, direto
                          ↑ tudo em paralelo, sem geração
```

O que é compartilhado com um Transformer comum:
- tokenização (BPE/byte-level);
- embeddings vetoriais de entrada;
- camadas de self-attention (bidirecionais, como um encoder).

O que muda:
- **sem decoder autorregressivo**: não existe geração sequencial;
- **sem Language Modeling Head**: o vetor da última camada não vira um softmax sobre todo o
  vocabulário. Em vez disso, um **pointer head** pequeno projeta o estado oculto de cada opção
  candidata (ex. `returns`, `shipping`, `billing`) e o estado oculto do token de decisão para o
  mesmo espaço vetorial, faz um produto escalar entre eles, e aplica softmax só sobre as opções
  legais daquela pergunta — não sobre 50k+ tokens de vocabulário.

O truque que faz múltiplas perguntas caberem numa única chamada sem vazar contexto entre elas é
a **máscara de atenção em blocos** (block-causal attention):

```
        state  Q_A   Q_B   Q_C
state [  ✓  ] [ - ] [ - ] [ - ]     state é o prefixo compartilhado;
Q_A   [  ✓  ] [ ✓ ] [ x ] [ x ]     cada pergunta só "enxerga" o state + a si mesma;
Q_B   [  ✓  ] [ x ] [ ✓ ] [ x ]     Q_A nunca vê os tokens de Q_B, e vice-versa
Q_C   [  ✓  ] [ x ] [ x ] [ ✓ ]     (x = atenção mascarada / -inf antes do softmax)
```

Isso resolve dois problemas ao mesmo tempo: (a) a resposta de uma pergunta não "vaza" para
outra dentro da mesma chamada; (b) o `state` só precisa ser processado (prefill) **uma vez**,
mesmo com dezenas de perguntas ramificando dele em paralelo — daí a latência ficar praticamente
constante independente de quantas perguntas você manda.

## As três primitivas: Choice, Score, Noul

Já detalhadas no [glossário](../docs/glossario.md#choice--score--noul). O ponto de engenharia
importante: o schema (quais opções existem, quantos níveis o Score tem) é definido **em tempo de
execução**, na própria chamada — não é algo que exige fine-tuning. O modelo generaliza
zero-shot a partir da descrição textual de cada opção que você manda.

## Janela de contexto e "Context Rot"

O Jev documentado tem 64k tokens totais por request (32k para `state` + a pergunta mais longa).
O Kev, sendo bem menor, tem janelas bem mais modestas na prática (o `kev-0.5b`, por exemplo, foi
treinado com ≤384 tokens de state — ver model card). Em ambos os casos, o mecanismo de
degradação é o mesmo: sem chain-of-thought para "filtrar" o que importa antes de decidir,
conteúdo irrelevante no `state` funciona como distrator e achata as distribuições de
probabilidade (Score e Choice ficam mais indecisos, Noul tende a colapsar para 0.5).

**Implicação de engenharia, testada na prática em [`02-primitivas-com-kev/`](../02-primitivas-com-kev/):**
filtre e recupere dados em código *antes* de montar o `state` — mande só os campos que a
pergunta específica precisa, não o payload inteiro do sistema.

## O que fica para o tópico seguinte

O *como* o modelo chega a ser calibrado (a probabilidade 0.8 realmente significar ~80% de
acerto) é assunto do RLCD — ver [`03-calibracao-rlcd/`](../03-calibracao-rlcd/).
