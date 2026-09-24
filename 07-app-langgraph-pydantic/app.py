"""Agente de triagem: LangGraph orquestra, Kev/Jev decide, um LLM só entra se precisar.

Fundamentos comentados passo a passo em README.md. Resumo do fluxo:

    ticket -> [triagem: Kev/Jev, via Pydantic] -> urgente? -> [escalar_llm: Gemini]
                                                -> não      -> [automatiza]

Pré-requisito: um servidor Kev rodando (ver 02-primitivas-com-kev/README.md):
    uv run --group kev-local python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
"""

import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.typesafe import TypeSafeModel
from pydantic_ai.providers.typesafe import TypeSafeProvider
from typesafe_sdk import TypeSafeClient

load_dotenv()


# --- 1. O BaseModel é a pergunta (ver README.md, seção 1) ---------------------------------


class TriagemTicket(BaseModel):
    """Triagem de um ticket de suporte."""

    urgente: bool = Field(description="Precisa de resposta na próxima hora?")
    departamento: Literal["billing", "shipping", "returns", "other"] = Field(
        description="Qual time deve tratar isso?"
    )


# --- 2. Aponta para o Kev local em vez do Jev pago (ver README.md, seção 2) ----------------


kev_client = TypeSafeClient(api_key="local", base_url="http://127.0.0.1:8009")
modelo_decisao = TypeSafeModel(
    "kev-latest", provider=TypeSafeProvider(typesafe_client=kev_client)
)


class EstadoAgente(TypedDict):
    ticket: str
    decisao: TriagemTicket | None
    resposta: str | None


# --- 3. Nó de decisão: chama o Kev/Jev, não gera texto (ver README.md, seção 3) ------------


def no_triagem(estado: EstadoAgente) -> EstadoAgente:
    agent = Agent(modelo_decisao, output_type=TriagemTicket)
    resultado = agent.run_sync(estado["ticket"])
    print(f"[triagem] {resultado.output}")
    return {**estado, "decisao": resultado.output}


# --- 4. Roteamento condicional pela decisão tipada (ver README.md, seção 4) ----------------


def decidir_proximo(estado: EstadoAgente) -> Literal["automatiza", "escalar_llm"]:
    assert estado["decisao"] is not None
    return "escalar_llm" if estado["decisao"].urgente else "automatiza"


def no_automatiza(estado: EstadoAgente) -> EstadoAgente:
    decisao = estado["decisao"]
    assert decisao is not None
    resposta = f"Roteado automaticamente para {decisao.departamento} (não urgente)."
    print(f"[automatiza] {resposta}")
    return {**estado, "resposta": resposta}


def no_escalar_llm(estado: EstadoAgente) -> EstadoAgente:
    # Padrão do estudo-chatbot: um LLM "System Two" entra só quando o Kev/Jev
    # já sinalizou que o caso precisa de julgamento mais rico que uma decisão tipada.
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not os.environ.get("GOOGLE_API_KEY"):
        resposta = "[sem GOOGLE_API_KEY configurada — pulei a chamada real ao LLM]"
        print(f"[escalar_llm] {resposta}")
        return {**estado, "resposta": resposta}

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    decisao = estado["decisao"]
    prompt = (
        f"Ticket urgente do departamento {decisao.departamento}: '{estado['ticket']}'. "
        "Escreva uma resposta curta e empática confirmando que um atendente humano "
        "vai assumir o caso agora."
    )
    resposta = llm.invoke(prompt).content
    print(f"[escalar_llm] {resposta}")
    return {**estado, "resposta": resposta}


# --- Monta o grafo --------------------------------------------------------------------------


def construir_grafo():
    grafo = StateGraph(EstadoAgente)
    grafo.add_node("triagem", no_triagem)
    grafo.add_node("automatiza", no_automatiza)
    grafo.add_node("escalar_llm", no_escalar_llm)

    grafo.set_entry_point("triagem")
    grafo.add_conditional_edges("triagem", decidir_proximo)
    grafo.add_edge("automatiza", END)
    grafo.add_edge("escalar_llm", END)

    return grafo.compile()


TICKETS_EXEMPLO = [
    "Meu pedido chegou com o tamanho errado, gostaria de trocar quando possível.",
    "Fui cobrado duas vezes no cartão e minha conta ficou negativa. Preciso disso resolvido hoje.",
]


def main() -> None:
    app = construir_grafo()
    for ticket in TICKETS_EXEMPLO:
        print(f"\n=== Ticket: {ticket!r} ===")
        estado_final = app.invoke({"ticket": ticket, "decisao": None, "resposta": None})
        print(f"Resposta final: {estado_final['resposta']}")


if __name__ == "__main__":
    main()
