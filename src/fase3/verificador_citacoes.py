"""Verificador determinístico de citações (sem LLM): mede alucinação de fundamento.

Cada "Art. N" citado numa resposta é conferido contra os trechos efetivamente recuperados:
  - VERIFICADA: o artigo está nos trechos E atribuído à mesma norma;
  - NORMA_DIVERGENTE: o artigo está nos trechos, mas a resposta o atribui a outra norma
    (ex.: "Art. 1128 da Lei 6.015/73" quando o 1.128 recuperado é do Código de Normas CGJ-CE);
  - NAO_RECUPERADA: o artigo não aparece em nenhum trecho recuperado.

Associação artigo → norma: a menção de norma mais próxima na mesma frase ("Art. 18 da LGPD",
"LGPD – Art. 18"); sem norma na frase, herda a última do mesmo parágrafo. Sem nenhuma norma,
a citação só é VERIFICADA se o artigo existir em uma única norma recuperada (norma_inferida).
"""

from __future__ import annotations

import re
import unicodedata
from enum import Enum

from pydantic import BaseModel, Field

from src.fase3.retrieval import norma_do_chunk
from src.fase3.sources import FONTES_POR_ID


class StatusCitacao(str, Enum):
    VERIFICADA = "VERIFICADA"
    NORMA_DIVERGENTE = "NORMA_DIVERGENTE"
    NAO_RECUPERADA = "NAO_RECUPERADA"


class Citacao(BaseModel):
    trecho: str = Field(..., description="Texto da citação como apareceu na resposta")
    artigo: str = Field(..., description="Artigo normalizado (ex.: 'Art. 1128', 'Art. 213-A')")
    norma_citada: str | None = Field(None, description="Norma que a resposta atribui ao artigo")
    norma_inferida: bool = Field(False, description="True se a resposta não disse a norma e ela foi inferida")
    status: StatusCitacao
    normas_no_contexto: list[str] = Field(default_factory=list, description="Normas em que o artigo foi recuperado")

    def descricao(self) -> str:
        norma = self.norma_citada or "norma não informada"
        achado = ", ".join(self.normas_no_contexto) or "nenhum trecho recuperado"
        return f"{self.artigo} ({norma}) → {self.status.value} [recuperado em: {achado}]"


class RelatorioCitacoes(BaseModel):
    citacoes: list[Citacao] = Field(default_factory=list)
    total: int = 0
    verificadas: int = 0
    norma_divergente: int = 0
    nao_recuperada: int = 0
    taxa_verificavel: float | None = None  # verificadas / total; None quando total == 0

    @classmethod
    def de(cls, citacoes: list[Citacao]) -> "RelatorioCitacoes":
        def conta(s: StatusCitacao) -> int:
            return sum(c.status == s for c in citacoes)

        total = len(citacoes)
        verificadas = conta(StatusCitacao.VERIFICADA)
        return cls(
            citacoes=citacoes, total=total, verificadas=verificadas,
            norma_divergente=conta(StatusCitacao.NORMA_DIVERGENTE),
            nao_recuperada=conta(StatusCitacao.NAO_RECUPERADA),
            taxa_verificavel=(verificadas / total) if total else None,
        )

    def nao_verificadas(self) -> list[Citacao]:
        return [c for c in self.citacoes if c.status != StatusCitacao.VERIFICADA]


# ---------------------------------------------------------------- normalização

_TRACOS = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-",
                         "\u00a0": " ", "\u202f": " "})


def _normalizar(texto: str) -> str:
    """Remove acentos e unifica traços/espaços preservando caixa e (quase sempre) o comprimento."""
    t = texto.translate(_TRACOS)
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


# ---------------------------------------------------------------- menções de norma

_N = r"(?:n[o.]*\s*)?"  # "nº", "n.", "no"
# Ordem importa: o Provimento 15/2026/CGJCE vem antes do Código de Normas, para "CGJCE" não ser
# atribuído ao Código; o trecho já reivindicado por uma norma não é reaproveitado por outra.
_APELIDOS: list[tuple[str, str]] = [
    ("prov_cgjce_15_2026", rf"prov(?:imento|\.)?\s*{_N}15\s*/\s*2026(?:\s*/\s*cgj\s*-?\s*ce)?"),
    ("prov_cnj_149_2023", rf"prov(?:imento|\.)?\s*(?:cnj\s*)?{_N}149(?:\s*/\s*2023)?|codigo nacional de normas"
                          rf"|\bcnj\s*{_N}149\b"),
    ("codigo_normas_ce", r"codigo de normas|\bcgj\s*-?\s*ce\b|\bcgjce\b"),
    ("lei_6015_1973", rf"\blei\s*{_N}6\.?015\b(?:\s*/\s*(?:19)?73)?|lei de registros publicos|\blrp\b"),
    ("lei_13709_2018", rf"\blgpd\b|\blei\s*{_N}13\.?709\b(?:\s*/\s*(?:20)?18)?|lei geral de protecao de dados"),
    ("lei_12527_2011", rf"\blai\b|\blei\s*{_N}12\.?527\b(?:\s*/\s*(?:20)?11)?|lei de acesso a informacao"),
    ("decreto_7724_2012", rf"\bdecreto\s*{_N}7\.?724\b(?:\s*/\s*(?:20)?12)?"),
    ("lei_8935_1994", rf"\blei\s*{_N}8\.?935\b(?:\s*/\s*(?:19)?94)?|lei dos (?:notarios|cartorios)"),
    ("res_anpd_15_2024", r"resolucao\s*(?:cd\s*/\s*)?anpd|\bres\.?\s*cd\s*/\s*anpd"),
]
_APELIDOS_RE = [(fid, re.compile(p)) for fid, p in _APELIDOS]
# Normas fora do corpus: viram "OUTRA: <texto>" (nunca coincidem com uma norma recuperada)
_GENERICA = re.compile(
    rf"\b(?:lei|decreto|provimento|resolucao|portaria|instrucao normativa)\s*{_N}\d[\d./]*\d"
    r"|codigo civil|codigo de processo civil|\bcpc\b|constituicao federal")


def _mencoes_de_norma(minusculo: str) -> list[tuple[int, int, str]]:
    """[(início, fim, norma)] de cada menção de norma, sem sobreposição."""
    achadas: list[tuple[int, int, str]] = []

    def livre(a: int, b: int) -> bool:
        return all(b <= x or a >= y for x, y, _ in achadas)

    for fid, padrao in _APELIDOS_RE:
        for m in padrao.finditer(minusculo):
            if livre(m.start(), m.end()):
                achadas.append((m.start(), m.end(), FONTES_POR_ID[fid].sigla))
    for m in _GENERICA.finditer(minusculo):
        if livre(m.start(), m.end()):
            achadas.append((m.start(), m.end(), f"OUTRA: {m.group(0)}"))
    return sorted(achadas)


# ---------------------------------------------------------------- artigos

_NUM = r"(?:\d{1,3}(?:\.\d{3})+|\d{1,4})(?:\s*[o°])?(?:\s?-[A-Z]{1,2}\b)?"
_CITACAO = re.compile(rf"(?i:\bart(?:igo)?s?)\.?\s*({_NUM}(?:\s*(?:,|\be\b|\ba\b)\s*{_NUM})*)")
_ITEM = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d{1,4})(?:\s*[o°])?(?:\s?-([A-Z]{1,2})\b)?")
_DISPOSITIVO = re.compile(r"Art\.\s*(\d+)(?:-([A-Z]{1,2}))?")
_CONECTOR_DEPOIS = re.compile(r"^[\s,§\w°.-]{0,30}?\b(?:d[aoe]s?|dest[ae]|conforme|nos termos d[aoe])\b\s*[^\w]*$")
# Fim de frase: ponto seguido de espaço e maiúscula, sem ser o ponto de "Art."
_FRASE = re.compile(r"(?<![Aa]rt)(?<![Aa]rts)\.\s+(?=[A-Z])|[!?;]\s+")


def _chave(num: str, suf: str | None) -> tuple[int, str]:
    return int(num.replace(".", "")), (suf or "")


def _rotulo(chave: tuple[int, str]) -> str:
    return f"Art. {chave[0]}" + (f"-{chave[1]}" if chave[1] else "")


def _norma_da_citacao(ini: int, fim: int, mencoes: list[tuple[int, int, str]], frase: str) -> str | None:
    """Norma da menção mais próxima; prefere a que vem logo depois com conector ("Art. 18 da LGPD")."""
    depois = [m for m in mencoes if m[0] >= fim]
    if depois and _CONECTOR_DEPOIS.match(frase[fim:depois[0][0]]):
        return depois[0][2]
    antes = [m for m in mencoes if m[1] <= ini]
    candidatos = []
    if antes:
        candidatos.append((ini - antes[-1][1], antes[-1][2]))
    if depois:
        candidatos.append((depois[0][0] - fim, depois[0][2]))
    return min(candidatos)[1] if candidatos else None


def _extrair(resposta: str) -> list[tuple[str, tuple[int, str], str | None, bool]]:
    """[(trecho, chave do artigo, norma citada, norma herdada?)] na ordem em que aparecem."""
    out = []
    for paragrafo in re.split(r"\n\s*\n", _normalizar(resposta)):
        ultima_norma: str | None = None
        # cada linha do Markdown é uma unidade; dentro dela, quebra por frases
        frases = [f for linha in paragrafo.split("\n") for f in _FRASE.split(linha)]
        for frase in frases:
            minusculo = frase.lower()
            mencoes = _mencoes_de_norma(minusculo)
            citacoes = list(_CITACAO.finditer(frase))
            for m in citacoes:
                norma = _norma_da_citacao(m.start(), m.end(), mencoes, minusculo)
                herdada = norma is None and ultima_norma is not None
                if herdada:
                    norma = ultima_norma
                for item in _ITEM.finditer(m.group(1)):
                    out.append((m.group(0).strip(), _chave(item.group(1), item.group(2)), norma, herdada))
            # Só herda de "títulos" (frase com norma e sem artigo, ex.: "**Código de Normas CGJ-CE**"),
            # para "O Art. 18 (LGPD). Ver Art. 213-A" não atribuir o 213-A à LGPD
            if mencoes and not citacoes:
                ultima_norma = mencoes[-1][2]
    return out


# ---------------------------------------------------------------- verificação

def _indice_recuperado(chunks: list[dict]) -> dict[tuple[int, str], set[str]]:
    """{chave do artigo: normas em que ele foi recuperado}. Trechos sem norma ficam de fora."""
    indice: dict[tuple[int, str], set[str]] = {}
    for h in chunks:
        m = _DISPOSITIVO.match(h.get("dispositivo") or "")
        norma = h.get("norma") or norma_do_chunk(h)
        if m and norma:
            indice.setdefault(_chave(m.group(1), m.group(2)), set()).add(norma)
    return indice


def verificar(resposta: str, chunks_recuperados: list[dict]) -> RelatorioCitacoes:
    indice = _indice_recuperado(chunks_recuperados)
    vistas: set[tuple[tuple[int, str], str | None]] = set()
    citacoes: list[Citacao] = []

    for trecho, chave, norma, _herdada in _extrair(resposta or ""):
        if (chave, norma) in vistas:
            continue
        vistas.add((chave, norma))
        normas = sorted(indice.get(chave, set()))
        inferida = False
        if not normas:
            status = StatusCitacao.NAO_RECUPERADA
        elif norma in normas:
            status = StatusCitacao.VERIFICADA
        elif norma is None and len(normas) == 1:
            status, norma, inferida = StatusCitacao.VERIFICADA, normas[0], True
        else:
            # norma diferente da recuperada, ou norma não dita com artigo presente em mais de uma
            status = StatusCitacao.NORMA_DIVERGENTE
        citacoes.append(Citacao(trecho=trecho, artigo=_rotulo(chave), norma_citada=norma,
                                norma_inferida=inferida, status=status, normas_no_contexto=normas))
    return RelatorioCitacoes.de(citacoes)
