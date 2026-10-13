"""Guarda contra o fundamento invertido do Art. 1.131 §10 do Código de Normas CGJ-CE.

O §10 manda a certidão de inteiro teor reproduzir TODO o conteúdo da matrícula. Ele nunca pode
aparecer como base para omitir/suprimir dados NEM para vedar/recusar o fornecimento.

Varre src/ e tests/. Casa "1131", "1.131", "Art 1131", "art. 1.131" quando, na mesma linha ou no
mesmo bloco (linhas contíguas não vazias, até RAIO de cada lado), aparece um termo de omissão
(omit, tarj, suprim, CPF) ou de restrição (veda, recus, indefer).

Os termos de restrição existem porque o payload que motivou esta guarda usava o §10 para
"Veda o fornecimento…" num ato INDEFERIDO, sem nenhuma palavra de omissão nem "CPF".

Menção correta e documentada: marcar a linha com "guarda-1131: ok".
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTAS = (RAIZ / "src", RAIZ / "tests")
ESTE_ARQUIVO = Path(__file__).resolve()

ARTIGO = re.compile(r"\b1\.?131\b")
TERMOS = re.compile(r"omit|tarj|suprim|cpf|\bveda|vedad|recus|indefer", re.IGNORECASE)
RAIO = 8
LIBERADO = "guarda-1131: ok"

PAYLOAD_ANTIGO = '''    payload = {
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
    }
'''


def _bloco(linhas: list[str], i: int) -> str:
    a = i
    while a > 0 and linhas[a - 1].strip() and i - a < RAIO:
        a -= 1
    b = i
    while b < len(linhas) - 1 and linhas[b + 1].strip() and b - i < RAIO:
        b += 1
    return "\n".join(linhas[a:b + 1])


def _suspeitos(pastas=PASTAS) -> list[str]:
    achados = []
    for pasta in pastas:
        for arquivo in sorted(p for ext in ("*.py", "*.txt") for p in pasta.rglob(ext)):
            if arquivo.resolve() == ESTE_ARQUIVO or ".venv" in arquivo.parts:
                continue
            linhas = arquivo.read_text(encoding="utf-8", errors="ignore").splitlines()
            for i, linha in enumerate(linhas):
                if ARTIGO.search(linha) and LIBERADO not in linha and TERMOS.search(_bloco(linhas, i)):
                    achados.append(f"{arquivo.relative_to(RAIZ) if arquivo.is_relative_to(RAIZ) else arquivo.name}"
                                   f":{i + 1}: {linha.strip()}")
    return achados


def test_nenhum_1131_associado_a_omissao_ou_restricao_em_src_e_tests():
    achados = _suspeitos()
    assert not achados, "Art. 1.131 junto de omissão/restrição:\n" + "\n".join(achados)


def test_guarda_reprova_o_payload_antigo(tmp_path):
    (tmp_path / "x.py").write_text(PAYLOAD_ANTIGO, encoding="utf-8")
    assert _suspeitos([tmp_path])


def test_guarda_reprova_a_marcacao_antiga_do_tarjador(tmp_path):
    (tmp_path / "x.py").write_text('subst = "[CPF OMITIDO - ART. 1131 CGJ-CE]"\n', encoding="utf-8")
    assert _suspeitos([tmp_path])


def test_guarda_casa_as_variantes_de_escrita(tmp_path):
    for i, variante in enumerate(("1131", "1.131", "Art 1131", "art. 1.131")):
        (tmp_path / f"v{i}.py").write_text(f"# base: {variante} para suprimir dados\n", encoding="utf-8")
    assert len(_suspeitos([tmp_path])) == 4


def test_mencao_sem_omissao_nem_restricao_passa(tmp_path):
    (tmp_path / "x.py").write_text("# inteiro teor: art. 1.131 §10 manda reproduzir todo o conteúdo\n",
                                   encoding="utf-8")
    assert not _suspeitos([tmp_path])
