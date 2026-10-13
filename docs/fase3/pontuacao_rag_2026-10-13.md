# Pontuação da coleta: assistente_registral_ce

> Gerado por `scripts/pontuar_coleta.py`, sem LLM, verificador v2. Origem: `data/benchmark/respostas_externas/assistente_registral_ce/`.
> Este documento NÃO é um comparativo entre sistemas: as respostas dos concorrentes ainda não foram coletadas.

## Camada 1: existência da citação no corpus oficial

Cada artigo citado foi conferido contra o corpus inteiro (11 fontes, sem filtro de especialidade).

| Classe | Citações | % |
|---|---:|---:|
| EXISTE | 52 | 95% |
| ARTIGO_INEXISTENTE_NA_NORMA | 2 | 4% |
| NORMA_FORA_DO_CORPUS | 1 | 2% |
| **Total** | **55** | |

- Citações sem norma declarada (classificadas pela existência do artigo em alguma norma): 14
- Respostas pontuadas: 25
- Respostas que citam norma estadual do CE (Código de Normas CGJ-CE ou Prov. 15/2026/CGJCE): 13
- Respostas que citam o Prov. 15/2026/CGJCE ou o Art. 1.103 do Código de Normas: 2
- Recusas ou respostas sem nenhum dispositivo: 6
- Comprimento mediano da resposta: 172 palavras

### Citações que não existem na norma citada ou estão fora do corpus

- #5: Art. 1103 (Provimento 15/2026/CGJCE) → ARTIGO_INEXISTENTE_NA_NORMA
- #14: Art. 543 (OUTRA: codigo civil) → NORMA_FORA_DO_CORPUS
- #25: Art. 178 (LGPD (Lei 13.709/2018)) → ARTIGO_INEXISTENTE_NA_NORMA

## Camada 2: ancoragem nos trechos recuperados (só o RAG próprio)

Mede se o artigo citado estava entre os trechos que o próprio RAG recuperou. Não é comparável com outros sistemas, que não expõem contexto, e por isso nunca entra em tabela comparativa.

| Status (verificador v2) | Citações |
|---|---:|
| VERIFICADA | 47 |
| NORMA_DIVERGENTE | 1 |
| NAO_RECUPERADA | 6 |
| FORA_DO_CORPUS | 1 |
| **Total** | **55** |

Perguntas com ao menos uma citação ancorada: 18 de 25.

## Limitações

- A camada 1 mede a existência da citação, não a correção jurídica do conteúdo, que depende do gabarito do Oficial, ainda não coletado.
- O corpus da Lei 6.015/1973 foi compilado sem trechos revogados: citar artigo revogado aparece como ARTIGO_INEXISTENTE_NA_NORMA.
- A associação artigo → norma segue as regras do extrator do verificador v2 (norma mais próxima na frase; herança só de títulos).
