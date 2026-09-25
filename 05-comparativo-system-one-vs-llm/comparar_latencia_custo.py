"""Compara Kev/Jev (System One) com um LLM em modo JSON estruturado (System Two), no mesmo
ticket de triagem — mesma tarefa, duas arquiteturas.

Pré-requisitos:
    - Um servidor Kev local rodando (ver 02-primitivas-com-kev/README.md), OU
      TYPESAFE_API_KEY em .env para usar o Jev real (ver 04-jev-api/).
    - GOOGLE_API_KEY em .env para o lado LLM (grátis em https://aistudio.google.com/app/apikey).

O que o script mede, não só descreve:
    - latência round-trip de cada abordagem na mesma tarefa;
    - se o LLM, mesmo sob "JSON mode" (with_structured_output), consegue produzir uma
      probabilidade calibrada por si só, ou se ele só devolve um rótulo sem noção de confiança
      real (a maioria dos LLMs de chat não expõe logprobs por padrão nesse modo).
"""

import os
import time

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

load_dotenv()

TICKET = (
    "Shoes arrived two weeks late and in the wrong size. "
    "Also I see two charges on my card."
)


# --- Lado System One: Kev/Jev -----------------------------------------------------------


def rodar_system_one() -> None:
    if os.environ.get("TYPESAFE_API_KEY"):
        client = TypeSafeClient()  # Jev real
        origem = "Jev (hospedado)"
    else:
        client = TypeSafeClient(api_key="local", base_url="http://127.0.0.1:8009", model="kev-latest")
        origem = "Kev (local)"

    inicio = time.perf_counter()
    resposta = client.system_one(
        state=TICKET,
        questions={
            "departamento": Choice(
                instructions="Qual time deve tratar este ticket?",
                criteria={
                    "returns": "Trocas, reembolsos, itens errados ou danificados",
                    "shipping": "Status de entrega, atrasos, pacotes perdidos",
                    "billing": "Cobranças, faturas, problemas de pagamento",
                },
            ),
            "escalar": Noul(instructions="Isso precisa de atenção humana urgente?"),
            "frustracao": Score(
                instructions="Qual o nível de frustração do cliente?",
                criteria=["Calmo", "Frustrado", "Muito irritado"],
            ),
        },
    )
    latencia_ms = (time.perf_counter() - inicio) * 1000

    departamento = resposta.answers["departamento"]
    print(f"\n=== System One: {origem} ===")
    print(f"Departamento : {departamento.choice}  (confiança calibrada: {departamento.confidence:.2f})")
    print(f"Latência     : {latencia_ms:.0f} ms")
    print(f"Custo        : {'US$0,042/MTok entrada, saída grátis' if 'Jev' in origem else 'US$0 (roda na sua máquina)'}")


# --- Lado System Two: LLM com JSON estruturado ------------------------------------------


class TriagemLLM(BaseModel):
    """Triagem de um ticket de suporte."""

    departamento: str = Field(description="returns, shipping ou billing")
    escalar: bool = Field(description="Precisa de atenção humana urgente?")
    frustracao_0_a_2: int = Field(description="Nível de frustração do cliente, de 0 (calmo) a 2 (muito irritado)")


def rodar_system_two() -> None:
    if not os.environ.get("GOOGLE_API_KEY"):
        print("\n[pulei o LLM: defina GOOGLE_API_KEY em .env -- ver .env.example]")
        return

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    llm_estruturado = llm.with_structured_output(TriagemLLM)

    prompt = f"Classifique este ticket de suporte: {TICKET!r}"
    inicio = time.perf_counter()
    resultado: TriagemLLM = llm_estruturado.invoke(prompt)
    latencia_ms = (time.perf_counter() - inicio) * 1000

    print("\n=== System Two: Gemini 2.0 Flash (JSON estruturado) ===")
    print(f"Departamento : {resultado.departamento}  (sem probabilidade calibrada exposta pela API)")
    print(f"Latência     : {latencia_ms:.0f} ms")
    print("Custo        : cobrado por tokens de entrada E saída (a resposta inteira é gerada)")


def main() -> None:
    rodar_system_one()
    rodar_system_two()
    print(
        "\nNote: a diferença de latência aqui tende a ser bem menor que os ~193x reportados "
        "pela TypeSafe contra LLMs frontier com reasoning -- Gemini Flash é um modelo rápido "
        "e de resposta curta. A vantagem do System One fica mais clara quanto maior/mais lento "
        "for o LLM do outro lado, e quanto mais perguntas forem empacotadas na mesma chamada."
    )


if __name__ == "__main__":
    main()
