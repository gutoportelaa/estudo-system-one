# 04 — API real do Jev (🚧 em construção)

Objetivo: trocar o `base_url` local do Kev (tópico 02) pela API hospedada do Jev
(`https://typesafe.ai`) e comparar resultado real, custo e latência lado a lado — mesmo código,
dois modelos.

Pré-requisito: conta na TypeSafe AI e `TYPESAFE_API_KEY` (custo ~US$0,042/milhão de tokens de
entrada; a decidir junto se/quando vale gerar a chave). Enquanto isso não acontece, este tópico
fica como placeholder — o script de `02-primitivas-com-kev/` já foi escrito para funcionar sem
alteração de código contra o Jev real, bastando:

```python
client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])  # sem base_url = usa o Jev hospedado
```

Planejado quando tivermos a chave:
- repetir o experimento de `02-primitivas-com-kev/testar_primitivas.py` contra o Jev real;
- comparar `confidence`/`probabilities` do Jev com o Kev-0.8B no mesmo ticket;
- registrar custo real da chamada.
