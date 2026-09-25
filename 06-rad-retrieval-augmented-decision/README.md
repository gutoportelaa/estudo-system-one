# 06 — RAD: Retrieval-Augmented Decision

## RAG vs. RAD

```
RAG tradicional (RAG-estudo)
  pergunta -> retrieve (busca vetorial) -> LLM gera resposta em texto a partir do contexto
              ↑ risco: o LLM pode "inventar" algo que não está nos trechos recuperados

RAD (este tópico)
  pedido   -> retrieve (busca vetorial) -> filtrar em código -> Kev/Jev DECIDE (não gera texto)
              ↑ mesma recuperação, mas a resposta final é uma primitiva tipada e calibrada,
                não uma frase que pode alucinar
```

O passo de `retrieve` é idêntico ao de um RAG comum (embeddings + similaridade). A diferença
está só no que acontece *depois* de recuperar o contexto: em vez de jogar tudo num prompt de
LLM e pedir uma resposta em texto, filtramos em código (mandamos só os trechos recuperados, não
a base inteira — reduzindo "context rot", ver
[`01-arquitetura-system-one/`](../01-arquitetura-system-one/)) e pedimos uma decisão tipada.

## O exemplo: elegibilidade de reembolso

[`rad_reembolso.py`](rad_reembolso.py) simula uma pequena base de política de devolução (6
trechos) e dois pedidos de cliente. Para cada pedido: busca por similaridade os 2 trechos de
política mais relevantes, monta um `state` só com o pedido + esses trechos, e pede ao Kev/Jev
duas primitivas: `elegivel` (`Noul`) e `motivo` (`Choice` entre as categorias possíveis).

## Rodando

```bash
uv sync --group kev-local --group llm-comparativo

cp 06-rad-retrieval-augmented-decision/.env.example 06-rad-retrieval-augmented-decision/.env
# preencher GOOGLE_API_KEY

uv run --group kev-local python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009  # aba 1
uv run python 06-rad-retrieval-augmented-decision/rad_reembolso.py                   # aba 2
```

## O que observar

- No segundo pedido de exemplo (roupa íntima, dentro do prazo mas de categoria não elegível), a
  busca deveria recuperar tanto o trecho do prazo de 30 dias quanto o da exclusão de itens
  íntimos — e a decisão certa depende de pesar os dois ao mesmo tempo, não só o primeiro que
  aparece. É um bom teste da primitiva `Choice`: ela força uma escolha única entre motivos que
  competem entre si.
- Compare o comportamento aqui com o que aconteceria num RAG tradicional pedindo a um LLM para
  "explicar se o reembolso é válido": o LLM pode escrever uma explicação plausível e ainda assim
  errar a citação da política, ou inventar uma exceção que não existe nos trechos recuperados.
  O RAD não tem esse risco especificamente porque não gera texto — mas também não devolve uma
  explicação em prosa para o cliente; isso ficaria a cargo de um passo `System Two` separado
  (ver o padrão híbrido em [`07-app-langgraph-pydantic/`](../07-app-langgraph-pydantic/)).
