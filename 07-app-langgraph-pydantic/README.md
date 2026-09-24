# 07 — Capstone: agente de triagem em LangGraph + Pydantic

> **Verificado em 24/09/2026** contra `docs/models/typesafe.md` e `docs/models/decision.md` do
> repositório real do [`pydantic-ai`](https://github.com/pydantic/pydantic-ai). A integração
> `pydantic_ai.models.typesafe.TypeSafeModel` existe de fato — não é extrapolação dos PDFs de
> pesquisa.

Este tópico junta tudo que os anteriores construíram numa aplicação pequena: um agente
[LangGraph](https://github.com/langchain-ai/langgraph) (o mesmo orquestrador usado em
[`estudo-chatbot`](https://github.com/gutoportelaa/estudo-chatbot)) que usa o Kev/Jev como nó de
decisão, roteando o grafo com base na resposta tipada — em vez de pedir pra um LLM "decidir e
escrever" tudo de uma vez.

A ideia central, e por que ela é elegante: **o mesmo `BaseModel` do Pydantic que define o schema
da decisão também define o tipo de retorno do nó do LangGraph.** Você não escreve a pergunta em
texto (prompt engineering) nem duplica a definição em dois lugares — o `pydantic-ai` lê os
campos do `BaseModel` e monta as perguntas `Choice`/`Score`/`Noul` sozinho.

## Fundamentos, na ordem em que aparecem no código

### 1. O `BaseModel` *é* a pergunta (não um schema de saída de LLM)

```python
class TriagemTicket(BaseModel):
    """Triagem de um ticket de suporte."""

    urgente: bool = Field(description="Precisa de resposta na próxima hora?")
    departamento: Literal["billing", "shipping", "returns", "other"] = Field(
        description="Qual time deve tratar isso?"
    )
```

**Fundamento System One:** cada campo vira uma pergunta tipada, todas resolvidas na mesma
chamada. `bool` → `Noul`; `Literal[...]` → `Choice`. Isso é diferente de "JSON mode" num LLM: o
Jev/Kev não gera esse JSON token a token, ele lê a resposta direto do pointer head (ver
[`01-arquitetura-system-one/`](../01-arquitetura-system-one/)).

**Fundamento Pydantic AI:** a *docstring* da classe vira o contexto geral da decisão; a
*description* de cada campo vira o texto da pergunta daquele campo especificamente. Não há
prompt separado — o schema inteiro é a especificação da tarefa.

### 2. Apontar o modelo para o Kev local, não para o Jev pago

```python
from typesafe_sdk import TypeSafeClient
from pydantic_ai.models.typesafe import TypeSafeModel
from pydantic_ai.providers.typesafe import TypeSafeProvider

kev_client = TypeSafeClient(api_key="local", base_url="http://127.0.0.1:8009")
modelo_decisao = TypeSafeModel("kev-latest", provider=TypeSafeProvider(typesafe_client=kev_client))
```

**Fundamento:** o `provider` é o único ponto de configuração que muda entre "estou testando de
graça no Kev local" (tópico 02) e "estou rodando contra o Jev pago" (tópico 04). O resto do
código — o `BaseModel`, o `Agent`, o grafo — não muda nada.

### 3. Um nó do LangGraph que decide (não gera texto)

```python
def no_triagem(estado: EstadoAgente) -> EstadoAgente:
    agent = Agent(modelo_decisao, output_type=TriagemTicket)
    resultado = agent.run_sync(estado["ticket"])
    return {**estado, "decisao": resultado.output}
```

**Fundamento LangGraph:** um nó é só uma função `Estado -> Estado parcial`. Aqui ele não chama
um LLM que "conversa" — ele chama um `Agent` do `pydantic-ai` cujo `output_type` é o
`BaseModel` da seção 1. `resultado.output` já vem como uma instância de `TriagemTicket`, tipada,
sem parsing manual de JSON.

### 4. Roteamento condicional pela decisão tipada

```python
def decidir_proximo(estado: EstadoAgente) -> Literal["automatiza", "escalar_llm"]:
    return "escalar_llm" if estado["decisao"].urgente else "automatiza"

grafo.add_conditional_edges("triagem", decidir_proximo)
```

**Fundamento LangGraph:** `add_conditional_edges` lê o estado depois de um nó rodar e escolhe o
próximo nó por nome — é isso que faz o grafo ramificar. **Fundamento System One aplicado:** a
condição não é "o texto parece urgente?" reavaliada por um LLM — é o campo `urgente: bool`
(primitiva `Noul`) que o Kev/Jev já calibrou. O LLM ("System Two") só entra no caminho
`escalar_llm`, para os casos que o próprio modelo de decisão marcou como precisando de
julgamento mais rico — o padrão híbrido que os relatórios de pesquisa recomendam.

## Rodando

```bash
uv sync --group langgraph --group kev-local

# aba 1: sobe o Kev local (ver 02-primitivas-com-kev/README.md)
uv run --group kev-local python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009

# aba 2: roda o agente
cp .env.example .env   # se for usar o nó de fallback LLM: GOOGLE_API_KEY
uv run --group langgraph python 07-app-langgraph-pydantic/app.py
```

Ver [`app.py`](app.py) para o grafo completo, incluindo o nó `escalar_llm` (reaproveitando o
padrão Gemini do [`estudo-chatbot`](https://github.com/gutoportelaa/estudo-chatbot)) para os
casos que a triagem marcar como urgentes.
