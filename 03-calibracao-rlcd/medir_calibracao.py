"""Mede calibração (ECE) na prática contra um servidor Kev local.

Pré-requisito: um servidor Kev rodando (ver 02-primitivas-com-kev/README.md):
    uv run --group kev-local python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009

Metodologia: um pequeno conjunto de afirmações com rótulo verdadeiro/falso conhecido é
enviado como pergunta `Noul` ("esta afirmação é verdadeira?"). Para cada resposta, a
"confiança" na classe prevista é max(p, 1-p) e o "acerto" é se a classe prevista bate com o
rótulo. Agrupamos em bins de confiança e calculamos o Expected Calibration Error (ECE):

    ECE = soma_sobre_bins( |bin| / N * |confiança_média_do_bin - acurácia_do_bin| )

Isto é uma réplica pequena e ilustrativa do método, não uma medição rigorosa: o model card
publicado do Kev-0.8B reporta ECE ~0.033 (servido) e ~0.049-0.054 fora de distribuição, sobre
milhares de exemplos — nosso conjunto de ~24 frases serve para *entender o cálculo*, não para
reproduzir o número oficial.
"""

from dataclasses import dataclass

from typesafe_sdk import Noul, TypeSafeClient

# Afirmações com rótulo conhecido (True = afirmação verdadeira). Deliberadamente misturando
# fatos óbvios (o modelo deveria acertar com alta confiança) e frases ambíguas/quase-verdadeiras
# (onde calibração honesta importa: é melhor um 0.55 hesitante do que um 0.95 errado).
AFIRMACOES: list[tuple[str, bool]] = [
    ("A água ferve a 100 graus Celsius ao nível do mar.", True),
    ("O Sol gira em torno da Terra.", False),
    ("Brasília é a capital do Brasil.", True),
    ("O gelo é mais denso que a água líquida.", False),
    ("Um triângulo tem quatro lados.", False),
    ("O coração humano tem quatro câmaras.", True),
    ("A Lua é maior que a Terra.", False),
    ("Paris é a capital da França.", True),
    ("Peixes respiram por pulmões.", False),
    ("O Everest é a montanha mais alta do mundo.", True),
    ("Todos os números pares são divisíveis por 2.", True),
    ("A velocidade da luz é maior no vácuo do que na água.", True),
    ("Um ano bissexto tem 366 dias.", True),
    ("O ferro é mais leve que a madeira.", False),
    ("Aranhas são insetos.", False),
    ("O Brasil faz fronteira com todos os países da América do Sul, exceto Chile e Equador.", True),
    ("A fotossíntese ocorre apenas à noite.", False),
    ("O DNA humano tem a forma de dupla hélice.", True),
    ("Morcegos são cegos.", False),
    ("O oceano Pacífico é o maior oceano do planeta.", True),
    ("Sapos são répteis.", False),
    ("O corpo humano adulto tem 206 ossos, em média.", True),
    ("Vênus é o planeta mais próximo do Sol.", False),
    ("A Grande Muralha da China é visível a olho nu do espaço, sem auxílio.", False),
]

N_BINS = 5  # poucos exemplos -> poucos bins, senão a maioria fica vazia


@dataclass
class Previsao:
    confianca: float  # max(p, 1-p)
    acertou: bool


def coletar_previsoes(client: TypeSafeClient) -> list[Previsao]:
    previsoes = []
    for texto, rotulo in AFIRMACOES:
        resposta = client.system_one(
            state=texto,
            questions={
                "verdadeira": Noul(
                    instructions="Esta afirmação é factualmente verdadeira?",
                ),
            },
        )
        p = resposta.answers["verdadeira"].noul
        previsto = p >= 0.5
        confianca = max(p, 1 - p)
        acertou = previsto == rotulo
        marca = "OK " if acertou else "ERRO"
        print(f"[{marca}] p(verdadeiro)={p:.2f}  rótulo={rotulo!s:5}  {texto}")
        previsoes.append(Previsao(confianca=confianca, acertou=acertou))
    return previsoes


def calcular_ece(previsoes: list[Previsao], n_bins: int = N_BINS) -> float:
    largura = 1.0 / n_bins
    ece = 0.0
    n = len(previsoes)
    print(f"\n{'bin':>12}  {'n':>3}  {'conf. média':>12}  {'acurácia':>9}")
    for i in range(n_bins):
        lo, hi = i * largura, (i + 1) * largura
        bin_previsoes = [p for p in previsoes if lo <= p.confianca < hi or (hi == 1.0 and p.confianca == 1.0)]
        if not bin_previsoes:
            continue
        conf_media = sum(p.confianca for p in bin_previsoes) / len(bin_previsoes)
        acuracia = sum(p.acertou for p in bin_previsoes) / len(bin_previsoes)
        peso = len(bin_previsoes) / n
        ece += peso * abs(conf_media - acuracia)
        print(f"[{lo:.1f}, {hi:.1f})  {len(bin_previsoes):>3}  {conf_media:>12.2f}  {acuracia:>9.2f}")
    return ece


def main() -> None:
    client = TypeSafeClient(api_key="local", base_url="http://127.0.0.1:8009", model="kev-latest")
    previsoes = coletar_previsoes(client)
    ece = calcular_ece(previsoes)
    acuracia_geral = sum(p.acertou for p in previsoes) / len(previsoes)
    print(f"\nAcurácia geral : {acuracia_geral:.2f}")
    print(f"ECE medido     : {ece:.3f}")
    print("(referência publicada no model card do Kev-0.8B: ECE ~0.033 servido / ~0.05 fora de distribuição, sobre milhares de exemplos)")


if __name__ == "__main__":
    main()
