# 03 — Calibração e RLCD (🚧 em construção)

Objetivo: explicar RLCD (Reinforcement Learning for Calibrated Decisions) em contraste direto
com RLHF/DPO, e então **medir** — não só descrever — a calibração de um Kev real usando os
números publicados no [model card do Kev-0.8B](https://huggingface.co/jaredpalmer/kev-0.8b)
(accuracy, ECE, Brier Score em "new sources" vs. "trained sources").

Planejado:
- `README.md`: RLCD vs. RLHF vs. RLVR — tabela + por que "confiança declarada = taxa de acerto
  real" é um objetivo de treino diferente de "resposta que humanos preferem".
- `medir_calibracao.py`: roda um pequeno conjunto de perguntas com resposta certa conhecida
  contra o Kev local (do tópico 02), agrupa por faixa de confiança e calcula ECE na mão —
  para comparar com o ECE publicado no model card e entender o que o número realmente mede.

Ver conceitos já definidos em [`docs/glossario.md`](../docs/glossario.md#rlcd-reinforcement-learning-for-calibrated-decisions).
