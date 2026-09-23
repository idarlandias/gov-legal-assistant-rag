# Benchmark da Fase 3

| Arquivo | Papel |
|---|---|
| `perguntas.json` | Fonte única das 25 perguntas e da lista de ferramentas |
| `planilha_benchmark.xlsx` | Coleta e avaliação: Perguntas (gabarito), Respostas (125 linhas = 25 × 5 ferramentas), Parametros, Resumo e Gate 1 |
| `results/rag-*.json` | Saídas brutas do RAG, com modelo, commit, latência e tokens |

## Fluxo
1. O oficial/DPO preenche o gabarito na aba **Perguntas**.
2. Coleta manual no Jus IA, no Jurídico AI e no LLM genérico: cole a resposta integral na aba **Respostas**.
3. Coleta automática do RAG:
   ```bash
   uv pip install -e ".[eval]"          # openpyxl
   python scripts/benchmark/run_rag_benchmark.py --dry-run
   python scripts/benchmark/run_rag_benchmark.py --xlsx
   ```
   Opções: `--ids 1,2,11`, `--k 5`, `--sleep 2`, `--overwrite`. Feche a planilha no Excel antes de rodar.
   - Corpus da Fase 3: `--collection fase3`, que preenche as linhas "RAG Fase 3".
   - Repor um resultado salvo sem chamar o LLM: `--xlsx --from-json results/<arquivo>.json`.
4. Dê as notas da rubrica (0 a 2) em todas as linhas. **Resumo** e **Gate 1** se calculam sozinhos.

## Regras
- O script nunca grava notas: a avaliação é humana, contra o gabarito.
- Se uma linha já tiver resposta, ela só é sobrescrita com `--overwrite`.
- Se alguma pergunta falhar, o script sai com código 1 e registra o erro no JSON.
- Para recriar a planilha do zero: `python scripts/benchmark/build_planilha.py --force` (**apaga tudo o que foi preenchido**).
