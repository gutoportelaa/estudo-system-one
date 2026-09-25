"""Compara o Kev local (grátis) com o Jev hospedado (pago) no mesmo ticket.

Pré-requisitos:
    - Um servidor Kev local rodando (ver 02-primitivas-com-kev/README.md).
    - TYPESAFE_API_KEY no ambiente (ou em .env) para o Jev real. Sem a chave, o script
      roda só a parte do Kev e avisa que pulou o Jev.

O ponto do script: o MESMO schema de perguntas (Choice/Score/Noul) é enviado aos dois
back-ends, só trocando o cliente. Isso é o que a documentação da TypeSafe chama de "drop-in":
o Kev serve o mesmo contrato /v1/systemone do Jev.
"""

import os
import time

from dotenv import load_dotenv
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

load_dotenv()

TICKET = (
    "Shoes arrived two weeks late and in the wrong size. "
    "Also I see two charges on my card."
)

QUESTIONS = {
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
}


def rodar(nome: str, client: TypeSafeClient) -> None:
    inicio = time.perf_counter()
    resposta = client.system_one(state=TICKET, questions=QUESTIONS)
    latencia_ms = (time.perf_counter() - inicio) * 1000

    departamento = resposta.answers["departamento"]
    frustracao = resposta.answers["frustracao"]
    print(f"\n=== {nome} (modelo servido: {resposta.model}) ===")
    print(f"Departamento : {departamento.choice}  (confiança {departamento.confidence:.2f})")
    print(f"  distribuição: {departamento.probabilities}")
    print(f"Escalar (Noul): {resposta.answers['escalar'].noul:.2f}")
    print(f"Frustração    : {frustracao.score:.2f}  ({frustracao.legend})")
    print(f"Latência      : {latencia_ms:.0f} ms")
    print(f"Tokens entrada: {resposta.usage.input_tokens}")


def main() -> None:
    kev = TypeSafeClient(api_key="local", base_url="http://127.0.0.1:8009", model="kev-latest")
    rodar("Kev local", kev)

    if os.environ.get("TYPESAFE_API_KEY"):
        jev = TypeSafeClient()  # sem base_url: usa https://api.typesafe.ai + jev-latest
        rodar("Jev hospedado", jev)
    else:
        print(
            "\n[pulei o Jev: defina TYPESAFE_API_KEY em .env para comparar com a API real "
            "-- ver 04-jev-api/.env.example]"
        )


if __name__ == "__main__":
    main()
