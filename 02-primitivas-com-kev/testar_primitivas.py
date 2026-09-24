"""Testa as três primitivas (Choice, Score, Noul) contra um servidor Kev local.

Pré-requisito: um servidor Kev rodando em outra aba de terminal.
    uv sync --group kev-local
    uv run --group kev-local python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009

O ponto central deste script: é o MESMO typesafe-sdk que fala com o Jev hospedado
(ver 04-jev-api/). Só o base_url muda.
"""

import time

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

# Ticket de exemplo: propositalmente ambíguo (toca em três departamentos ao
# mesmo tempo), para observar a distribuição de probabilidades do Choice,
# não só o vencedor.
TICKET = (
    "Shoes arrived two weeks late and in the wrong size. "
    "Also I see two charges on my card."
)


def main() -> None:
    client = TypeSafeClient(
        api_key="local",
        base_url="http://127.0.0.1:8009",
        model="kev-latest",
    )

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
            "escalar": Noul(
                instructions="Isso precisa de atenção humana urgente?",
            ),
            "frustracao": Score(
                instructions="Qual o nível de frustração do cliente?",
                criteria=["Calmo", "Frustrado", "Muito irritado"],
            ),
        },
    )
    latencia_ms = (time.perf_counter() - inicio) * 1000

    departamento = resposta.answers["departamento"]
    print(f"Departamento escolhido : {departamento.choice}")
    print(f"Confiança               : {departamento.confidence:.2f}")
    print(f"Distribuição completa   : {departamento.probabilities}")
    print()
    print(f"Precisa escalar (Noul)  : {resposta.answers['escalar'].noul:.2f}")
    print()
    frustracao = resposta.answers["frustracao"]
    print(f"Frustração (Score)      : {frustracao.score:.2f}  ({frustracao.legend})")
    print()
    print(f"Latência (round-trip)   : {latencia_ms:.0f} ms")
    print(f"Tokens de entrada       : {resposta.usage.input_tokens}")
    print(f"Tokens de saída         : {resposta.usage.output_tokens}  (esperado: 0 — Jev/Kev não gera texto)")


if __name__ == "__main__":
    main()
