"""Testes do Gerador de Ato Pronto de Balcão (Fase 3)."""

from unittest.mock import MagicMock

import pytest

from src.fase3.ato_pronto import (
    VEREDITO_FALHA,
    AtoProntoOutput,
    CanalRisco,
    DispositivoLegal,
    PedidoBalcao,
    RegistroAuditoriaLGPD,
    RegistroFalha,
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
    # Caso juridicamente correto: certidão de matrícula a requerente identificado, sem exigir finalidade
    payload = {
        "canal": "VERDE",
        "veredito": "SUGESTÃO: DEFERIR",
        "instrucao_balcao": "Conferir a identificação do requerente e emitir a certidão da matrícula.",
        "fundamentacao": [
            {
                "norma": "Código de Normas CGJ-CE",
                "artigo": "Art. 1.128, caput",
                "aplicacao": "Certidão de matrícula a requerente identificado, independentemente de finalidade.",
            },
            {
                "norma": "Prov. CNJ 149/2023",
                "artigo": "Art. 123",
                "aplicacao": "Pedido de certidão de matrícula depende de identificação e independe de finalidade.",
            },
        ],
        "minuta_ato": "DESPACHO: expeça-se a certidão da matrícula ao requerente identificado.",
        "auditoria_lgpd": {
            "finalidade": "Publicidade registral",
            "base_legal_lgpd": "Art. 7º, II",
            "categoria_titular": "Proprietário",
            "dados_tratados": ["Dados da matrícula"],
            "salvaguardas_adotadas": "Identificação do requerente",
            "conformidade_cnj_149": "Aderência ao Prov. CNJ 149/2023",
        },
    }
    saida = AtoProntoOutput.model_validate(payload)
    assert saida.canal == CanalRisco.VERDE
    assert saida.veredito == "SUGESTÃO: DEFERIR"
    assert [(f.norma, f.artigo) for f in saida.fundamentacao] == [
        ("Código de Normas CGJ-CE", "Art. 1.128, caput"), ("Prov. CNJ 149/2023", "Art. 123")]


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
    assert resultado.veredito == "SUGESTÃO: DEFERIR INTEGRAL"  # formato antigo vira sugestão
    assert "Lei 6.015/1973" in resultado.fundamentacao[0].norma
    assert len(resultado.fontes_corpus) == 1
    assert resultado.latencia_s >= 0.0


_HIT = {"id": "1", "text": "trecho normativo", "source": "Lei 6.015/1973, Art. 17", "page": 0,
        "dispositivo": "Art. 17"}
_PEDIDO = PedidoBalcao(tipo_pedido="Busca por CPF", solicitante="Terceiro sem vínculo", dados_sensiveis=["CPF"])


def _pipeline_com_resposta(conteudo: str, hits=None) -> MagicMock:
    mock_pipeline = MagicMock()
    mock_pipeline.llm_model = "mock-model"
    mock_pipeline.retrieve.return_value = [_HIT] if hits is None else hits
    resposta_mock = MagicMock()
    resposta_mock.choices = [MagicMock(message=MagicMock(content=conteudo))]
    mock_pipeline._call_chat_completions.return_value = resposta_mock
    return mock_pipeline


def _assert_indefinido(resultado, motivo: str) -> None:
    assert resultado.canal == CanalRisco.INDEFINIDO
    assert resultado.veredito == VEREDITO_FALHA
    assert resultado.fundamentacao == []
    assert resultado.minuta_ato == ""
    assert isinstance(resultado.auditoria_lgpd, RegistroFalha)
    assert resultado.auditoria_lgpd.falha == motivo


def test_json_invalido_do_llm_gera_indefinido():
    pipe = _pipeline_com_resposta("Recomendo negar e emitir nota devolutiva por falta de amparo legal.")
    _assert_indefinido(processar_ato_pronto(pipe, _PEDIDO), "JSONDecodeError")


def test_excecao_de_rede_gera_indefinido():
    pipe = _pipeline_com_resposta("{}")
    pipe._call_chat_completions.side_effect = ConnectionError("rede caiu")
    _assert_indefinido(processar_ato_pronto(pipe, _PEDIDO), "ConnectionError")


def test_busca_vazia_nao_chama_o_llm():
    pipe = _pipeline_com_resposta("{}", hits=[])
    resultado = processar_ato_pronto(pipe, _PEDIDO)
    assert pipe._call_chat_completions.call_count == 0
    _assert_indefinido(resultado, "contexto vazio")


@pytest.mark.parametrize("conteudo", [
    "DEFERIDO INTEGRAL, liberado sem restrição.",
    '{"canal": "VERDE", "veredito": "DEFERIDO INTEGRAL"}',  # JSON incompleto
    '{"canal": "VERDE", "veredito": "DEFERIDO INTEGRAL", "instrucao_balcao": "x", '
    '"minuta_ato": "x", "auditoria_lgpd": {"falha": "x"}}',  # auditoria de falha com canal decidido
    "",
    "canal VERDE",
])
def test_fallback_nunca_produz_verde(conteudo):
    resultado = processar_ato_pronto(_pipeline_com_resposta(conteudo), _PEDIDO)
    assert resultado.canal == CanalRisco.INDEFINIDO
