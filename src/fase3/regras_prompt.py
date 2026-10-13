"""Regras de decisão comuns ao prompt do chat (pipeline.py) e ao do Ato Pronto (ato_pronto.py).

Uma constante só, para que os dois caminhos não voltem a divergir: o chat ainda mandava
"condicionar com tarjamento protetivo" depois de o Ato Pronto ter sido corrigido.
"""

REGRA_INTEIRO_TEOR = (
    "Nunca instrua a suprimir, tarjar ou omitir dados de uma certidão de inteiro teor. Se o caso parecer "
    "exigir conteúdo reduzido, indique a certidão de situação jurídica atual (Prov. CNJ 149/2023, Art. 125) "
    "como alternativa."
)

DECISOES = (
    "DEFERIR",
    "DEFERIR MEDIANTE EXIGÊNCIA PRÉVIA (identificação e finalidade, com ficha do Art. 1.128, §3º, "
    "do Código de Normas da CGJ-CE)",
    "INDEFERIR (nota devolutiva fundamentada)",
)

REGRAS_DECISAO = f"Indique uma das três decisões: {' / '.join(DECISOES)}. {REGRA_INTEIRO_TEOR}"
