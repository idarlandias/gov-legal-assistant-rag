"""Guarda contra o fundamento invertido: o Art. 1.131 §10 da CGJ-CE manda reproduzir TODO o
conteúdo da certidão de inteiro teor; ele não pode ser citado como base para omitir dados."""

import re
from pathlib import Path

FASE3 = Path(__file__).resolve().parents[1] / "src" / "fase3"
ARTIGO = re.compile(r"\b1\.?131\b")
OMISSAO = re.compile(r"omit|omiss|tarj|suprim|ocult|exclu|reda[cç]|proteg|sem cpf", re.IGNORECASE)
JANELA = 2  # linhas antes e depois da menção ao artigo


def _ocorrencias_suspeitas(pasta: Path = FASE3) -> list[str]:
    achados = []
    for arquivo in sorted(pasta.rglob("*.py")):
        linhas = arquivo.read_text(encoding="utf-8").splitlines()
        for i, linha in enumerate(linhas):
            if not ARTIGO.search(linha):
                continue
            trecho = "\n".join(linhas[max(0, i - JANELA): i + JANELA + 1])
            if OMISSAO.search(trecho):
                achados.append(f"{arquivo.name}:{i + 1}: {linha.strip()}")
    return achados


def test_nenhuma_citacao_do_1131_associada_a_omissao():
    achados = _ocorrencias_suspeitas()
    assert not achados, "Art. 1.131 citado junto de omissão/tarja:\n" + "\n".join(achados)


def test_o_detector_pega_o_caso_antigo(tmp_path):
    # Garante que o guarda não passa por estar cego: o texto antigo tem que ser pego
    (tmp_path / "x.py").write_text('subst = "[CPF OMITIDO - ART. 1131 CGJ-CE]"\n', encoding="utf-8")
    assert _ocorrencias_suspeitas(tmp_path)
