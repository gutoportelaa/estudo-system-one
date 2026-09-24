# estudo-system-one

Repositório de estudo sobre o **Jev** (TypeSafe AI) e o paradigma emergente de modelos
**"System One"**: modelos que não geram texto — eles respondem perguntas tipadas
(`Choice`, `Score`, `Noul`) com probabilidades calibradas, em uma única passagem
forward (sem loop autorregressivo).

Segue a mesma linha dos meus outros repositórios de estudo:
[`estudo-chatbot`](https://github.com/gutoportelaa/estudo-chatbot) (LLM conversacional) e
[`RAG-estudo`](https://github.com/gutoportelaa/RAG-estudo) (Retrieval-Augmented Generation).
Aqui o objeto de estudo é o oposto do chatbot: um modelo desenhado para **decidir, não conversar**.

## Por que isso importa

LLMs tradicionais ("System Two") são caros e lentos quando usados só para tomar uma
decisão estruturada dentro de um sistema (classificar um ticket, decidir se um texto é spam,
dar um score de urgência). O Jev propõe um modelo especializado só nisso: sem geração de
texto, sem chain-of-thought, com latência de ~70–500ms e custo ~40x menor, mas com uma
promessa forte — as probabilidades que ele devolve são **calibradas** (0.8 de confiança
realmente acerta ~80% das vezes), graças a um método de pós-treinamento próprio chamado
**RLCD** (Reinforcement Learning for Calibrated Decisions), em contraste com o RLHF/DPO
usado em LLMs de chat.

## Como o repo está organizado

Cada pasta numerada é um tópico de estudo autocontido: um `README.md` com a teoria e,
quando aplicável, código para testar o conceito na prática.

| Pasta | Tópico | Status |
| --- | --- | --- |
| [`docs/`](docs/) | Glossário e mapa de referências (os PDFs de pesquisa que originaram este repo) | ✅ |
| [`01-arquitetura-system-one/`](01-arquitetura-system-one/) | Como o Jev funciona por dentro: single forward pass, block-causal attention, primitivas tipadas | ✅ |
| [`02-primitivas-com-kev/`](02-primitivas-com-kev/) | Prática: rodar `Choice`/`Score`/`Noul` de verdade contra o **Kev** (réplica open-source do Jev) | ✅ |
| [`03-calibracao-rlcd/`](03-calibracao-rlcd/) | RLCD vs. RLHF/DPO, Brier Score, ECE — e medir a calibração do Kev empiricamente | 🚧 |
| [`04-jev-api/`](04-jev-api/) | Testar a API paga real do Jev via `typesafe-sdk` | 🚧 |
| [`05-comparativo-system-one-vs-llm/`](05-comparativo-system-one-vs-llm/) | Jev/Kev vs. LLM com JSON mode/structured output — latência, custo, taxa de erro | 🚧 |
| [`06-rad-retrieval-augmented-decision/`](06-rad-retrieval-augmented-decision/) | RAD (Retrieval-Augmented Decision) — o "RAG" do mundo System One, ligando com o [`RAG-estudo`](https://github.com/gutoportelaa/RAG-estudo) | 🚧 |
| [`07-app-langgraph-pydantic/`](07-app-langgraph-pydantic/) | **Capstone**: agente de triagem de tickets em LangGraph, com Pydantic definindo as decisões tipadas do Kev/Jev e roteando o grafo por elas. Cada integração nova é explicada junto do conceito de LangGraph que ela usa | 🚧 |

✅ = conteúdo pronto · 🚧 = em construção

### Sobre o capstone (`07-app-langgraph-pydantic`)

Une o que já construí em [`estudo-chatbot`](https://github.com/gutoportelaa/estudo-chatbot) (LangGraph
como orquestrador) com o Jev/Kev como camada de decisão. A ideia central: um `BaseModel` do Pydantic
descreve o schema de uma decisão (ex.: `is_spam: bool`, `departamento: Literal[...]`, `urgencia: float`) e
esse mesmo schema vira, ao mesmo tempo, (a) a pergunta tipada enviada ao Kev/Jev e (b) o tipo de retorno de
um nó do LangGraph — sem duplicar a definição em dois lugares. O grafo então roteia (`add_conditional_edges`)
com base no `Score`/`Noul` retornado (ex.: `confidence > 0.8` → automatiza; caso contrário → nó de LLM
"System Two" para lidar com o caso ambíguo). Cada peça nova (state, node, edge condicional, integração
Pydantic↔TypeSafe) ganha uma seção curta de "fundamentos" no README da pasta antes do código.

## Stack

| Camada | Ferramenta |
| --- | --- |
| Gerenciador Python | [`uv`](https://docs.astral.sh/uv/) |
| SDK oficial | [`typesafe-sdk`](https://pypi.org/project/typesafe-sdk/) (fala com Jev **e** com Kev — mesmo contrato de API) |
| Modelo local de estudo | [Kev](https://github.com/jaredpalmer/kev) (LoRA sobre Qwen, código aberto, réplica do Jev) |

> **Nota sobre hardware:** esta máquina de desenvolvimento tem ~2.8GB de RAM e nenhuma GPU.
> Isso é insuficiente para rodar o Kev-4B/9B (os modelos mais próximos do Jev em acurácia)
> localmente. As instruções em `02-primitivas-com-kev/` cobrem tanto a opção local (Kev-0.5B,
> o menor, se você tiver mais RAM disponível) quanto a opção remota (Hugging Face Space,
> zero instalação) — use a que fizer sentido para sua máquina.

## Referências originais

Este repositório nasceu de dois relatórios de pesquisa (Perplexity) guardados em `docs/pesquisa/`,
usados como ponto de partida — e depois verificados/corrigidos contra as fontes primárias reais
(PyPI, Hugging Face, GitHub) conforme o estudo avançou.
