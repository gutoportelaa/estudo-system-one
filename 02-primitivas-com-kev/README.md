# 02 — Primitivas na prática, com o Kev

Objetivo: rodar `Choice`, `Score` e `Noul` de verdade — sem simulação — contra um servidor local
que fala o mesmo contrato de API que o Jev (`/v1/systemone`). Como a API paga do Jev é fechada,
usamos o [Kev](https://github.com/jaredpalmer/kev), a réplica open-source mantida por Jared
Palmer, que serve exatamente esse contrato.

## Por que Kev-0.8B (e não 4B/9B)

Esta máquina de estudo tem ~2.8GB de RAM total e nenhuma GPU. Olhando a tabela de modelos do
Kev:

| Modelo | Base | Roda em |
| --- | --- | --- |
| Kev-0.8B | Qwen3.5-0.8B-Base | qualquer Mac Apple Silicon, L4 — **o único candidato realista em CPU com pouca RAM** |
| Kev-4B / 9B / 27B | Qwen3.5/3.8 maiores | precisam de GPU dedicada (32GB+ de RAM unificada ou VRAM) |

Kev-0.8B ainda assim baixa ~1.6–2GB de pesos (base + adapter) e pode ser apertado nesta máquina.
Se der OOM, a alternativa é rodar este tópico num ambiente com mais RAM (Colab grátis, por
exemplo) — o código não muda, só o `--run`.

## Passo 1 — subir o servidor Kev

Numa aba de terminal, na raiz do repo:

```bash
uv sync --group kev-local
uv run --group kev-local python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
```

Isso baixa o adapter + a base Qwen3.5-0.8B na primeira execução e sobe um servidor HTTP local
em `http://127.0.0.1:8009` respondendo em `/v1/systemone` — o mesmo endpoint que o Jev hospedado
expõe.

## Passo 2 — chamar com o SDK oficial da TypeSafe

Este é o ponto central do exercício: **o mesmo `typesafe-sdk` que fala com o Jev pago fala com o
Kev local**, só muda o `base_url`. É por isso que dá para prototipar de graça contra o Kev e só
trocar de endpoint quando (e se) migrar para o Jev — ver [`04-jev-api/`](../04-jev-api/).

```bash
uv run python 02-primitivas-com-kev/testar_primitivas.py
```

Veja o script: [`testar_primitivas.py`](testar_primitivas.py). Ele reaproveita o exemplo de
triagem de ticket de suporte (o mesmo domínio que os relatórios de pesquisa usam), pedindo as
três primitivas na mesma chamada:

- `Noul` — "isso precisa de atenção humana urgente?"
- `Choice` — "qual time deve tratar isso?"
- `Score` — "qual o nível de frustração do cliente, numa escala de 3 níveis?"

## O que observar na saída

1. **`probabilities` do Choice não soma 1 só na opção vencedora** — o ticket de exemplo (compra
   com defeito + atraso + cobrança duplicada) toca em `returns`, `shipping` e `billing` ao mesmo
   tempo. É esperado: a primitiva devolve a distribuição inteira, não só o vencedor, justamente
   para seu código decidir se a confiança é alta o bastante para automatizar ou se deve escalar
   para um humano.
2. **`score` pode cair entre níveis** (ex. `1.44` numa escala de 3 níveis `0/1/2`) — é o "valor
   esperado" da distribuição, não uma classificação discreta.
3. **Latência round-trip** (medida no script com `time.perf_counter`, já que o `typesafe-sdk`
   não expõe `latency_ms` como campo tipado — o servidor Kev devolve isso no JSON cru, mas o
   SDK ignora campos fora do schema `SystemOneResponse`). Compare com a latência de uma chamada
   equivalente a um LLM gerando o mesmo JSON em
   [`05-comparativo-system-one-vs-llm/`](../05-comparativo-system-one-vs-llm/).

## Experimento sugerido: sensibilidade à ordem/fraseado

Os relatórios de pesquisa mencionam que System One models são sensíveis à ordem e ao fraseado
das opções (sem chain-of-thought para "corrigir" ambiguidade). Teste isso você mesmo: rode
`testar_primitivas.py` reordenando as chaves do dicionário `criteria` do `Choice` e comparando
a distribuição de probabilidades resultante — ela deveria ser idêntica (a ordem das *chaves* de
um dict não deveria importar), mas vale testar se reformular a *descrição* de uma opção muda o
resultado de forma desproporcional.

## Nota sobre calibração

Os números de calibração deste Kev específico (accuracy, ECE) **não são teoria** — estão
medidos e publicados no [model card](https://huggingface.co/jaredpalmer/kev-0.8b). O tópico
seguinte ([`03-calibracao-rlcd/`](../03-calibracao-rlcd/)) usa esses números reais para explicar
o que ECE/Brier Score significam e por que RLCD é diferente de RLHF.
