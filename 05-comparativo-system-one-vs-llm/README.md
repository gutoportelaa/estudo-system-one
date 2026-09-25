# 05 — System One vs. LLM com Structured Output

## Por que "JSON mode" num LLM não é a mesma coisa

`with_structured_output` (LangChain/Gemini), `response_format` (OpenAI) ou grammars
(Outlines/SGLang/llama.cpp) resolvem o problema de **sintaxe** — garantem que a saída seja um
JSON válido contra um schema. Nenhum deles resolve dois problemas que o Jev/Kev atacam
diretamente:

1. **Latência escala com o tamanho da resposta.** Mesmo em JSON mode, o LLM ainda gera token a
   token — só que os tokens são restritos a caber no schema. Menos que texto livre, mas ainda
   sequencial.
2. **Não há probabilidade calibrada por padrão.** A API do Gemini (ou de qualquer LLM de chat
   comum) devolve o campo `departamento: "returns"` como uma string — não uma distribuição de
   probabilidade sobre `returns`/`shipping`/`billing` que você possa comparar contra um
   threshold de confiança. Para ter isso com um LLM, você precisaria de acesso a logprobs por
   token (nem toda API expõe) e ainda assim eles não passam pelo treino de calibração (RLCD) que
   o Jev/Kev recebem — ver [`03-calibracao-rlcd/`](../03-calibracao-rlcd/).

## Rodando

```bash
uv sync --group llm-comparativo --group kev-local
cp 05-comparativo-system-one-vs-llm/.env.example 05-comparativo-system-one-vs-llm/.env
# preencher GOOGLE_API_KEY (grátis) e, opcionalmente, TYPESAFE_API_KEY
uv run python 05-comparativo-system-one-vs-llm/comparar_latencia_custo.py
```

Roda em cima do Kev local por padrão (tópico 02); se `TYPESAFE_API_KEY` estiver definida, usa o
Jev real em vez do Kev. Sem `GOOGLE_API_KEY`, pula a parte do LLM e avisa.

## Leitura honesta do resultado

Não espere ver os "193x mais rápido" ou "444x mais barato" que a TypeSafe divulga: esses números
comparam o Jev contra **LLMs frontier com reasoning** (GPT-6 Astra, Claude Fable 5.1) em tarefas
com múltiplas perguntas — não contra um modelo rápido como o Gemini 2.0 Flash respondendo um
JSON curto. A vantagem relativa do System One cresce em três eixos que este script deixa visíveis
mas não maximiza de propósito:

- **quantidade de perguntas por chamada** (aqui só 3 — tente aumentar e observar que a latência
  do Kev quase não muda, enquanto a do LLM cresce);
- **tamanho/velocidade do modelo do outro lado** (um LLM de raciocínio lento sofre muito mais);
- **necessidade real de probabilidade calibrada** (se seu caso de uso só precisa do rótulo, sem
  agir de forma diferente conforme a confiança, a vantagem do Jev/Kev cai bastante).
