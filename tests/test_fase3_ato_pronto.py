"""Testes do Gerador de Ato Pronto de Balcão (Fase 3)."""

from unittest.mock import MagicMock

from src.fase3.ato_pronto import (
    AtoProntoOutput,
    CanalRisco,
    DispositivoLegal,
    PedidoBalcao,
    RegistroAuditoriaLGPD,
    _limpar_json,
    gerar_query_recuperacao,
    processar_ato_pronto,
)


def test_pedido_balcao_validation():
    pedido = PedidoBalcao(
        tipo_pedido="Certidão de Inteiro Teor de Matrícula",
        solicitante="Terceiro sem vínculo comprovado",
        dados_sensiveis=["CPF", "Regime de bens"],
        detalhes_caso="Requerente solicitou no balcão sem apresentar documento de interesse",
    )
    assert pedido.protocolo == "BALCAO-AUTO"
    assert "CPF" in pedido.dados_sensiveis


def test_gerar_query_recuperacao():
    pedido = PedidoBalcao(
        tipo_pedido="Busca por Indicador Pessoal",
        solicitante="Credor / Instituição Financeira",
        dados_sensiveis=["CPF"],
        detalhes_caso="Localizar bens de devedor",
    )
    q = gerar_query_recuperacao(pedido)
    assert "Busca por Indicador Pessoal" in q
    assert "Credor" in q
    assert "CPF" in q
    assert "Localizar bens" in q


def test_limpar_json_com_markdown_fences():
    bruto = """Aqui está a análise:
```json
{
  "canal": "AMARELO",
  "veredito": "DEFERIDO COM TARJAMENTO",
  "instrucao_balcao": "Emitir com tarja de CPF.",
  "fundamentacao": [],
  "minuta_ato": "Minuta teste",
  "auditoria_lgpd": {
    "finalidade": "Publicidade registral",
    "base_legal_lgpd": "Art. 7, II",
    "categoria_titular": "Proprietário",
    "dados_tratados": ["CPF"],
    "salvaguardas_adotadas": "Tarjamento",
    "conformidade_cnj_149": "Conforme"
  }
}
```
Atenciosamente."""
    limpo = _limpar_json(bruto)
    assert limpo.startswith("{")
    assert limpo.endswith("}")
    assert '"canal": "AMARELO"' in limpo


def test_ato_pronto_output_model_validate():
    payload = {
        "canal": "VERMELHO",
        "veredito": "INDEFERIDO (NOTA DEVOLUTIVA)",
        "instrucao_balcao": "Recusar verbalmente e emitir Nota Devolutiva formal.",
        "fundamentacao": [
            {
                "norma": "Código de Normas CGJ-CE",
                "artigo": "Art. 1131, §10",
                "aplicacao": "Veda o fornecimento de informação direta sem requerimento formal.",
            }
        ],
        "minuta_ato": "NOTA DEVOLUTIVA Nº 01/2026...",
        "auditoria_lgpd": {
            "finalidade": "Controle de legalidade",
            "base_legal_lgpd": "Art. 7º, II",
            "categoria_titular": "Proprietário",
            "dados_tratados": ["Dados da matrícula"],
            "salvaguardas_adotadas": "Bloqueio de acesso não justificado",
            "conformidade_cnj_149": "Aderência ao Prov. CNJ 149/2023",
        },
    }
    saida = AtoProntoOutput.model_validate(payload)
    assert saida.canal == CanalRisco.VERMELHO
    assert saida.veredito == "INDEFERIDO (NOTA DEVOLUTIVA)"
    assert len(saida.fundamentacao) == 1
    assert saida.fundamentacao[0].artigo == "Art. 1131, §10"


def test_processar_ato_pronto_com_mock():
    mock_pipeline = MagicMock()
    mock_pipeline.llm_model = "mock-model"
    mock_pipeline.retrieve.return_value = [
        {
            "id": "1",
            "text": "Art. 17. Qualquer pessoa pode requerer certidão do registro sem informar o motivo...",
            "source": "Lei 6.015/1973",
            "page": 0,
            "dispositivo": "Lei 6.015/1973, Art. 17",
        }
    ]

    resposta_mock = MagicMock()
    resposta_mock.choices = [
        MagicMock(
            message=MagicMock(
                content="""{
  "canal": "VERDE",
  "veredito": "DEFERIDO INTEGRAL",
  "instrucao_balcao": "Emitir certidão sem restrições ao proprietário.",
  "fundamentacao": [
    {
      "norma": "Lei 6.015/1973",
      "artigo": "Art. 17",
      "aplicacao": "Princípio da publicidade registral para o titular."
    }
  ],
  "minuta_ato": "DESPACHO DE BALCÃO: Certidão deferida.",
  "auditoria_lgpd": {
    "finalidade": "Publicidade registral",
    "base_legal_lgpd": "Art. 7º, II",
    "categoria_titular": "Proprietário",
    "dados_tratados": ["Nome", "Matrícula"],
    "salvaguardas_adotadas": "Conferência de identidade",
    "conformidade_cnj_149": "Conforme"
  }
}"""
            )
        )
    ]
    mock_pipeline._call_chat_completions.return_value = resposta_mock

    pedido = PedidoBalcao(
        tipo_pedido="Certidão de Matrícula",
        solicitante="Próprio Titular / Proprietário",
        dados_sensiveis=[],
        protocolo="TESTE-001",
    )

    resultado = processar_ato_pronto(mock_pipeline, pedido)
    assert resultado.canal == CanalRisco.VERDE
    assert resultado.veredito == "DEFERIDO INTEGRAL"
    assert "Lei 6.015/1973" in resultado.fundamentacao[0].norma
    assert len(resultado.fontes_corpus) == 1
    assert resultado.latencia_s >= 0.0


def test_processar_ato_pronto_fallback():
    mock_pipeline = MagicMock()
    mock_pipeline.llm_model = "mock-model"
    mock_pipeline.retrieve.return_value = []
    
    # Simula o LLM devolvendo texto corrido sem JSON
    resposta_mock = MagicMock()
    resposta_mock.choices = [
        MagicMock(message=MagicMock(content="Recomendo negar e emitir nota devolutiva por falta de amparo legal."))
    ]
    mock_pipeline._call_chat_completions.return_value = resposta_mock

    pedido = PedidoBalcao(
        tipo_pedido="Busca por CPF",
        solicitante="Terceiro sem vínculo",
        dados_sensiveis=["CPF"],
    )

    resultado = processar_ato_pronto(mock_pipeline, pedido)
    assert resultado.canal == CanalRisco.VERMELHO  # detectou 'negar'/'devolutiva'
    assert resultado.auditoria_lgpd.finalidade != ""
