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

import ast
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


# ---------------------------------------------------------------- texto de interface (src/ui)
PASTAS_UI = (RAIZ / "src" / "ui",)
# O problema é a afirmação jurídica, não a palavra: "tarj" e "vinculante" sempre; supressão só quando
# a mesma string fala de certidão/matrícula/inteiro teor/CPF/dado pessoal.
SEMPRE_UI = re.compile(r"tarj|vinculante", re.IGNORECASE)
SUPRESSAO = re.compile(r"suprim|supress", re.IGNORECASE)  # "supress" cobre supressão/supressões
ALVO_SUPRESSAO = re.compile(r"certid[ãa]o|matr[íi]cula|inteiro teor|\bcpf\b|dados? pessoa(l|is)", re.IGNORECASE)
# chave de session_state, key=, variável de ambiente e nome de arquivo: identificadores, não texto exibido
IDENTIFICADOR = re.compile(r"^(?:[a-z0-9_]+|[A-Z0-9_]+)$")


def _textos_de_interface(codigo: str):
    """Literais de string do arquivo, sem docstrings nem identificadores (chaves e nomes)."""
    arvore = ast.parse(codigo)
    docstrings = {
        id(no.body[0].value)
        for no in ast.walk(arvore)
        if isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and no.body and isinstance(no.body[0], ast.Expr) and isinstance(no.body[0].value, ast.Constant)
    }
    for no in ast.walk(arvore):
        if (isinstance(no, ast.Constant) and isinstance(no.value, str) and id(no) not in docstrings
                and not IDENTIFICADOR.match(no.value)):
            yield no.lineno, no.value


def _suspeitos_ui(pastas=PASTAS_UI) -> list[str]:
    achados = []
    for pasta in pastas:
        for arquivo in sorted(pasta.rglob("*.py")):
            for linha, texto in _textos_de_interface(arquivo.read_text(encoding="utf-8")):
                if SEMPRE_UI.search(texto) or (SUPRESSAO.search(texto) and ALVO_SUPRESSAO.search(texto)):
                    nome = arquivo.relative_to(RAIZ) if arquivo.is_relative_to(RAIZ) else arquivo.name
                    achados.append(f"{nome}:{linha}: {texto.strip()[:120]}")
    return achados


def test_ui_sem_tarja_supressao_ou_vinculante():
    achados = _suspeitos_ui()
    assert not achados, "Texto de interface com tarj/suprim/vinculante:\n" + "\n".join(achados)


def test_guarda_ui_reprova_texto_exibido(tmp_path):
    (tmp_path / "app.py").write_text('st.expander("Fundamentação Legal Vinculante")\n'
                                     'st.button("Aplicar Tarjamento")\n', encoding="utf-8")
    assert len(_suspeitos_ui([tmp_path])) == 2


def test_guarda_ui_supressao_so_reprova_junto_de_certidao_ou_dado_pessoal(tmp_path):
    (tmp_path / "app.py").write_text('st.markdown("Aplica supressões no texto da matrícula")\n'
                                     'st.markdown("Suprimir o CPF")\n'
                                     'st.caption("Avisos suprimidos nesta sessão")\n'
                                     'st.caption("Verificação automática de citações")\n', encoding="utf-8")
    assert len(_suspeitos_ui([tmp_path])) == 2


def test_guarda_ui_ignora_chaves_docstrings_e_comentarios(tmp_path):
    (tmp_path / "app.py").write_text('"""Módulo do tarjador."""\n'
                                     '# aba do tarjador\n'
                                     'st.text_input("Protocolo:", key="tarja_protocolo")\n', encoding="utf-8")
    assert not _suspeitos_ui([tmp_path])
