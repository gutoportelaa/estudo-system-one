# Glossário — System One / Jev

Termos na ordem em que costumam aparecer quando você lê sobre o Jev pela primeira vez.

### System One / System Two
Nomenclatura de Diogo Almeida (TypeSafe AI) emprestada da teoria dual de Daniel Kahneman.
**System Two** = LLM tradicional: raciocínio sequencial, gera texto token a token (lento, caro,
explicável via chain-of-thought). **System One** = Jev/Kev: "intuição" rápida e paralela — uma
única passagem forward que devolve uma decisão tipada, sem gerar texto.

### Single forward pass
O Jev/Kev não tem loop autorregressivo. O encoder processa o `state` + todas as `questions` de
uma vez e lê a resposta direto dos estados ocultos, em vez de gerar a resposta token a token.
Ver [`01-arquitetura-system-one/`](../01-arquitetura-system-one/).

### Block-causal attention (máscara de atenção em blocos)
Mecanismo que permite empacotar várias perguntas na mesma chamada sem que uma "veja" a outra:
todos os tokens veem o `state` compartilhado, mas cada pergunta só vê a si mesma. Evita
vazamento de contexto entre perguntas e permite reaproveitar o cache do `state` (calculado uma
vez) entre todas elas. Ver [`01-arquitetura-system-one/`](../01-arquitetura-system-one/).

### Pointer head / decision head
Substitui o LM Head de um LLM comum. Em vez de projetar para o vocabulário inteiro e gerar um
token, projeta o estado oculto de cada opção candidata para um vetor pequeno e faz um produto
escalar contra a pergunta — daí sai a distribuição de probabilidade sobre as opções.

### Choice / Score / Noul
As três primitivas tipadas que o Jev/Kev devolvem — o "contrato de dados" da API:

| Primitiva | O que é | Retorno | Limite |
| --- | --- | --- | --- |
| `Noul` | Pergunta booleana calibrada | probabilidade `[0, 1]` de "sim" | — |
| `Choice` | Escolha entre opções nomeadas | opção vencedora + distribuição completa + confiança | até 255 opções |
| `Score` | Avaliação numa escala ordinal | valor esperado (pode cair *entre* níveis, ex. `1.43`) | 2 a 10 níveis |

Ver prática em [`02-primitivas-com-kev/`](../02-primitivas-com-kev/).

### RLCD (Reinforcement Learning for Calibrated Decisions)
Método de pós-treinamento da TypeSafe. Em vez de otimizar para "o que um humano prefere ler"
(RLHF/DPO), otimiza para que a probabilidade declarada bata com a taxa de acerto real: se o
modelo diz 0.8 de confiança, ele deve acertar ~80% das vezes num conjunto grande de decisões
parecidas. Ver [`03-calibracao-rlcd/`](../03-calibracao-rlcd/).

### Calibração / ECE (Expected Calibration Error) / Brier Score
**Calibração** é o quanto a probabilidade declarada corresponde à frequência real de acerto.
**ECE** agrupa previsões em faixas de confiança (bins) e mede o desvio médio entre confiança
declarada e acurácia observada em cada faixa. **Brier Score** é o erro quadrático médio entre a
probabilidade prevista e o resultado real (0 ou 1) — quanto menor, melhor calibrado. Ambos são
medidos de verdade no Kev-0.5B (valores reais no model card), não só descritos em teoria.

### Context Rot (fadiga de atenção)
Como não há chain-of-thought para "filtrar o ruído" antes de decidir, conteúdo irrelevante no
`state` degrada a precisão das primitivas — quanto mais lixo no contexto, mais achatada a
distribuição de probabilidade fica. Recomendação prática: filtrar em código antes de mandar
para o modelo, mandando só os campos relevantes para cada pergunta.

### RAD (Retrieval-Augmented Decision)
Variante do RAG onde o passo final não é um LLM gerando texto a partir do contexto recuperado,
mas um modelo System One decidindo (Choice/Score/Noul) a partir dele. Elimina o risco de
alucinação textual na resposta final, ao custo de não poder "explicar" a decisão em prosa. Ver
[`06-rad-retrieval-augmented-decision/`](../06-rad-retrieval-augmented-decision/).

### Kev
Réplica open-source da arquitetura do Jev, mantida por Jared Palmer
([github.com/jaredpalmer/kev](https://github.com/jaredpalmer/kev)): LoRA + pointer head sobre
modelos Qwen (0.5B a 27B), servido com o mesmo contrato de API `/v1/systemone` do Jev — dá para
apontar o `typesafe-sdk` oficial para um servidor Kev local sem mudar código. É o que usamos
neste repo para a prática, já que a API paga do Jev é fechada.

### TypeSafe AI / typesafe-sdk
TypeSafe AI é o laboratório (fundado por Diogo Almeida) que treina e hospeda o Jev.
`typesafe-sdk` é o cliente Python oficial (`pip install typesafe-sdk` — real, no PyPI), usado
tanto para falar com o Jev hospedado quanto com um servidor Kev local (mesmo contrato de API).
