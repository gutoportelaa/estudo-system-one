# 04 — API real do Jev

## Rodando sem chave (padrão)

```bash
uv run python 04-jev-api/comparar_kev_vs_jev.py
```

Sem `TYPESAFE_API_KEY`, o script roda normalmente contra o Kev local (tópico 02) e avisa que
pulou o Jev — não é preciso ter conta na TypeSafe para usar este repositório.

## Rodando com a API paga

```bash
cp 04-jev-api/.env.example 04-jev-api/.env
# preencher TYPESAFE_API_KEY=...
uv run python 04-jev-api/comparar_kev_vs_jev.py
```

O script então roda o **mesmo** `state` + `questions` contra o Kev local *e* contra o Jev
hospedado (`https://api.typesafe.ai`, resolvido automaticamente pelo `typesafe-sdk` quando não
se passa `base_url`), e imprime os dois lado a lado.

## O que comparar

- **`confidence`/`probabilities` do Choice**: o Jev, sendo o modelo frontier fechado, deveria
  produzir uma distribuição mais "decidida" (menos achatada) no mesmo ticket ambíguo — é
  justamente a vantagem de calibração/acurácia que os relatórios de pesquisa atribuem ao
  Jev sobre o Kev (~0.857 vs. ~0.848 de accuracy em "new sources", segundo o
  [README do Kev](https://github.com/jaredpalmer/kev#models) — a diferença é pequena para
  Kev-27B, mas maior para Kev-0.8B/4B).
- **Latência**: ambos devem ficar na faixa de dezenas a algumas centenas de ms — o Jev não é
  necessariamente mais rápido que um Kev rodando localmente (a chamada ao Jev inclui rede);
  a vantagem de latência do paradigma System One é *versus LLMs*, não *versus Kev*.
- **Custo**: o Kev é grátis (roda na sua máquina); o Jev cobra ~US$0,042/milhão de tokens de
  entrada. Para prototipagem, o Kev é estritamente melhor em custo — o Jev entra quando a
  acurácia/calibração adicional compensa o preço.

## Nota

Este tópico foi deixado sem chave configurada de propósito — decidir gerar uma conta paga na
TypeSafe é uma escolha (com custo real, ainda que pequeno) que cabe a quem for rodar o repo, não
algo que o repositório deveria assumir por padrão.
