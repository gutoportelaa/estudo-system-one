# 06 — RAD: Retrieval-Augmented Decision (🚧 em construção)

Objetivo: adaptar o pipeline de [`RAG-estudo`](https://github.com/gutoportelaa/RAG-estudo)
(ChromaDB + embeddings) trocando o passo final — em vez de um LLM gerar uma resposta em texto a
partir do contexto recuperado, um modelo System One (Kev/Jev) **decide** (Choice/Score/Noul)
sobre esse mesmo contexto, já filtrado para caber no `state`.

Planejado:
- reaproveitar a base vetorial do `RAG-estudo` (ou uma nova, menor);
- pipeline: `retrieve` (busca por similaridade) → `filtrar em código` (reduzir context rot) →
  `decide` (Kev/Jev) → `agir`;
- comparar com a resposta que o RAG tradicional daria para a mesma pergunta.
