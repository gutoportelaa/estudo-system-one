# 05 — System One vs. LLM com Structured Output (🚧 em construção)

Objetivo: comparar, no mesmo ticket de exemplo usado no tópico 02, o Kev/Jev contra um LLM
"System Two" forçado a JSON estruturado (ex. Gemini com `response_schema`, o mesmo modelo já
usado em [`estudo-chatbot`](https://github.com/gutoportelaa/estudo-chatbot) e
[`RAG-estudo`](https://github.com/gutoportelaa/RAG-estudo)) — latência, custo, taxa de erro de
schema e se as probabilidades retornadas fazem sentido como calibração.

Planejado:
- script que roda as duas abordagens no mesmo `TICKET` e imprime latência/custo lado a lado;
- nota sobre por que "JSON mode" ainda não resolve o problema de calibração (o LLM pode ser
  sintaticamente válido e ainda assim overconfident).
