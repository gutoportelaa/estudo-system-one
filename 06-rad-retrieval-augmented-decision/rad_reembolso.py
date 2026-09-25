"""RAD (Retrieval-Augmented Decision): retrieve -> filtrar em código -> decidir (Kev/Jev) -> agir.

Contraste direto com o pipeline do RAG-estudo (https://github.com/gutoportelaa/RAG-estudo):
lá, o passo final é um LLM *gerando texto* a partir do contexto recuperado. Aqui, o passo final
é o Kev/Jev *decidindo* (Noul/Choice) a partir do mesmo tipo de contexto recuperado -- sem
risco de alucinação textual na resposta final, ao custo de não haver uma explicação em prosa.

Pré-requisitos:
    - GOOGLE_API_KEY em .env (para os embeddings de busca -- grátis).
    - Um servidor Kev local rodando (ver 02-primitivas-com-kev/README.md), OU TYPESAFE_API_KEY.
"""

import math
import os

from dotenv import load_dotenv
from typesafe_sdk import Choice, Noul, TypeSafeClient

load_dotenv()

# "Base de conhecimento" da política de reembolso -- pequena de propósito, para caber no
# state sem virar "context rot" (ver 01-arquitetura-system-one/README.md).
POLITICA_CHUNKS = [
    "Itens podem ser devolvidos em até 30 dias corridos da data de entrega, com nota fiscal.",
    "Itens em promoção de liquidação final (tag 'venda final') não são elegíveis para reembolso.",
    "Roupas íntimas e itens de higiene pessoal não são elegíveis para devolução, por questões sanitárias.",
    "Produtos com defeito de fabricação podem ser trocados ou reembolsados a qualquer momento, "
    "mesmo fora do prazo de 30 dias, mediante laudo técnico.",
    "Reembolsos aprovados são processados em até 10 dias úteis, no mesmo método de pagamento usado na compra.",
    "Pedidos cancelados antes do envio são reembolsados integralmente, sem necessidade de devolução física.",
]


def _cosine(a: list[float], b: list[float]) -> float:
    produto = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    return produto / (norma_a * norma_b)


def retrieve(pergunta: str, top_k: int = 2) -> list[str]:
    """Busca por similaridade de embeddings -- o 'R' do RAD."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    embutir = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vetor_pergunta = embutir.embed_query(pergunta)
    vetores_chunks = embutir.embed_documents(POLITICA_CHUNKS)

    pontuados = sorted(
        zip(POLITICA_CHUNKS, vetores_chunks),
        key=lambda par: _cosine(vetor_pergunta, par[1]),
        reverse=True,
    )
    return [chunk for chunk, _ in pontuados[:top_k]]


def decide(pedido: str, politica_relevante: list[str]) -> None:
    """Filtra em código (junta só o que foi recuperado) e decide -- o 'AD' do RAD."""
    state = {
        "pedido": pedido,
        "politica_aplicavel": politica_relevante,  # só os trechos relevantes, não a base inteira
    }

    client = TypeSafeClient(
        api_key=os.environ.get("TYPESAFE_API_KEY", "local"),
        base_url=None if os.environ.get("TYPESAFE_API_KEY") else "http://127.0.0.1:8009",
        model=None if os.environ.get("TYPESAFE_API_KEY") else "kev-latest",
    )

    resposta = client.system_one(
        state=state,
        questions={
            "elegivel": Noul(
                instructions="O pedido é elegível para reembolso, segundo a política aplicável?",
            ),
            "motivo": Choice(
                instructions="Qual o principal motivo da decisão?",
                criteria={
                    "dentro_do_prazo": "Está dentro do prazo normal de devolução",
                    "defeito": "É um caso de defeito de fabricação",
                    "item_nao_elegivel": "É um tipo de item que a política exclui",
                    "fora_do_prazo": "Passou do prazo e não é caso de defeito",
                },
            ),
        },
    )

    print(f"\nPedido: {pedido!r}")
    print(f"Política recuperada (top-{len(politica_relevante)}):")
    for chunk in politica_relevante:
        print(f"  - {chunk}")
    print(f"Elegível para reembolso (Noul): {resposta.answers['elegivel'].noul:.2f}")
    print(f"Motivo (Choice)               : {resposta.answers['motivo'].choice}")


def main() -> None:
    pedidos = [
        "Comprei um tênis há 5 dias e ele veio com a sola descolando. Quero reembolso.",
        "Comprei uma roupa íntima há 3 dias, só não gostei do caimento.",
    ]
    for pedido in pedidos:
        contexto = retrieve(pedido)
        decide(pedido, contexto)


if __name__ == "__main__":
    main()
