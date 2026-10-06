"""Testes do módulo de Tarjamento Inteligente e Carimbo de Integridade (Fase 3)."""

from src.fase3.tarjador import (
    MATRICULA_EXEMPLO_CE,
    formatar_carimbo,
    gerar_hash_conformidade,
    tarjar_texto_matricula,
)


def test_tarjamento_terceiro():
    resultado = tarjar_texto_matricula(
        texto_matricula=MATRICULA_EXEMPLO_CE,
        solicitante="Terceiro sem vínculo comprovado",
        protocolo="PROT-TESTE-01",
    )

    # Verifica se os dados foram tarjados no texto de saída
    assert "482.910.384-21" not in resultado.texto_tarjado
    assert "[CPF OMITIDO - ART. 1131 CGJ-CE]" in resultado.texto_tarjado
    assert resultado.total_dados_tarjados > 0
    assert resultado.total_dados_detectados >= 3

    # Verifica se gerou o carimbo SHA-256 com código de autenticidade
    assert resultado.carimbo.codigo_autenticidade.startswith("REG-CE-")
    assert len(resultado.carimbo.hash_sha256) == 64
    assert "CANAL AMARELO" in resultado.carimbo.texto_carimbo


def test_tarjamento_proprio_titular():
    resultado = tarjar_texto_matricula(
        texto_matricula=MATRICULA_EXEMPLO_CE,
        solicitante="Próprio Titular / Proprietário do Imóvel",
        protocolo="PROT-TESTE-02",
    )

    # Titular tem direito de ver seus dados na íntegra
    assert "482.910.384-21" in resultado.texto_tarjado
    assert resultado.total_dados_tarjados == 0
    assert all(d.acao_aplicada == "MANTIDO" for d in resultado.dados_detectados)
    assert "CANAL VERDE" in resultado.carimbo.texto_carimbo


def test_gerar_hash_conformidade_imutabilidade():
    h1 = gerar_hash_conformidade("texto A", "PROT-01", "06/10/2026")
    h2 = gerar_hash_conformidade("texto A", "PROT-01", "06/10/2026")
    h3 = gerar_hash_conformidade("texto B", "PROT-01", "06/10/2026")

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64


def test_formatar_carimbo():
    carimbo = formatar_carimbo("PROT-1234", "a" * 64, "06/10/2026 10:00:00", canal="AMARELO")
    assert carimbo.codigo_autenticidade == f"REG-CE-{'A' * 8}"
    assert "PROT-1234" in carimbo.texto_carimbo
    assert "Provimento CNJ 149/2023" in carimbo.texto_carimbo


def test_performance_tarjador():
    resultado = tarjar_texto_matricula(MATRICULA_EXEMPLO_CE)
    # Deve ser quase instantâneo (< 50 milissegundos)
    assert resultado.tempo_processamento_s < 0.05
