"""Download, extração de texto e segmentação por dispositivo do corpus da Fase 3."""

from __future__ import annotations

import hashlib
import html.parser
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from src.fase3.sources import FONTES, Fonte

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "data" / "corpus_fase3"
RAW_DIR = CORPUS_DIR / "raw"
MANIFEST = CORPUS_DIR / "manifest.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"


# ---------------------------------------------------------------- download

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _check_payload(fonte: Fonte, content: bytes, content_type: str) -> None:
    """Falha se o servidor devolveu uma página no lugar do PDF (erro comum no gov.br)."""
    if fonte.formato == "pdf" and not content.startswith(b"%PDF"):
        raise ValueError(f"esperava PDF, veio {content_type or 'desconhecido'} ({len(content)} B)")
    if fonte.formato != "pdf" and b"<html" not in content[:5000].lower():
        raise ValueError(f"esperava HTML, veio {content_type or 'desconhecido'}")


def download(fontes: list[Fonte] = FONTES, force: bool = False) -> dict[str, str]:
    """Baixa as fontes para raw/ e atualiza o manifest. Retorna {id: status}."""
    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    status: dict[str, str] = {}

    for fonte in fontes:
        dest = RAW_DIR / fonte.arquivo
        try:
            # verify=False: vários portais públicos têm cadeia de certificados incompleta
            resp = requests.get(fonte.url, headers={"User-Agent": USER_AGENT}, verify=False, timeout=90)
            resp.raise_for_status()
            _check_payload(fonte, resp.content, resp.headers.get("Content-Type", ""))
        except Exception as e:
            status[fonte.id] = f"ERRO: {type(e).__name__}: {e}"
            continue

        novo_hash = sha256(resp.content)
        anterior = manifest.get(fonte.id, {})
        if dest.exists() and anterior.get("sha256") == novo_hash and not force:
            status[fonte.id] = "inalterado"
        else:
            dest.write_bytes(resp.content)
            status[fonte.id] = "atualizado" if anterior else "novo"
        manifest[fonte.id] = {
            **anterior,
            "sigla": fonte.sigla,
            "url": fonte.url,
            "arquivo": fonte.arquivo,
            "bytes": len(resp.content),
            "sha256": novo_hash,
            "last_modified": resp.headers.get("Last-Modified"),
            "baixado_em": (datetime.now().isoformat(timespec="seconds")
                           if status[fonte.id] != "inalterado" else anterior.get("baixado_em")),
        }
    save_manifest(manifest)
    return status


# ---------------------------------------------------------------- extração

_BLOCK_TAGS = {"p", "br", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "blockquote"}
# Planalto marca a redação revogada com <strike>; ela não pode entrar no corpus
_SKIP_TAGS = {"script", "style", "strike", "s", "del", "head", "title"}


class _TextExtractor(html.parser.HTMLParser):
    def __init__(self, only_class: str | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.only_class = only_class
        self.capture_depth = 0 if only_class else 1  # >0 = capturando
        self.stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("br",):
            self.parts.append("\n")
            return
        if tag in ("img", "meta", "link", "input", "hr"):
            return
        self.stack.append(tag)
        if self.only_class and self.capture_depth == 0:
            classes = (dict(attrs).get("class") or "").split()
            if self.only_class in classes:
                self.capture_depth = len(self.stack)
        if tag in _SKIP_TAGS:
            self.skip_depth += 1
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag not in self.stack:
            return
        while self.stack:
            t = self.stack.pop()
            if t in _SKIP_TAGS:
                self.skip_depth = max(0, self.skip_depth - 1)
            if t in _BLOCK_TAGS:
                self.parts.append("\n")
            if self.only_class and self.capture_depth and len(self.stack) < self.capture_depth:
                self.capture_depth = -1  # terminou o bloco alvo; não captura mais
            if t == tag:
                break

    def handle_data(self, data):
        if self.skip_depth == 0 and self.capture_depth > 0:
            self.parts.append(data)


def normalize(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def html_to_text(raw: bytes, only_class: str | None = None) -> str:
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        decoded = raw.decode("iso-8859-1")  # Planalto
    ex = _TextExtractor(only_class=only_class)
    ex.feed(decoded)
    return normalize("".join(ex.parts))


_SUMARIO = re.compile(r"^.*\.{8,}\s*\d*\s*$\n?", re.MULTILINE)  # "CAPÍTULO II........ 23"


def pdf_pages(path: Path) -> list[str]:
    from pypdf import PdfReader

    return [normalize(_SUMARIO.sub("", p.extract_text() or "")) for p in PdfReader(path).pages]


def extract(fonte: Fonte) -> list[tuple[int, str]]:
    """Retorna [(página, texto)]. HTML vira página única (0)."""
    path = RAW_DIR / fonte.arquivo
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe; rode o download")
    if fonte.formato == "pdf":
        return [(i + 1, t) for i, t in enumerate(pdf_pages(path)) if t]
    only = "texto-dou" if fonte.formato == "dou" else None
    return [(0, html_to_text(path.read_bytes(), only_class=only))]


# ---------------------------------------------------------------- segmentação

# Aceita "Art. 1.000" (ponto de milhar, usado no Código de Normas do CE)
_ART = re.compile(r"^Art\.?\s*(\d{1,3}(?:\.\d{3})+|\d{1,4})(?:\s*[º°o])?\.?(?:\s*-\s*([A-Z]{1,2})\b)?",
                  re.MULTILINE)
_HEADING = re.compile(
    r"^(LIVRO|PARTE|T[ÍI]TULO|CAP[ÍI]TULO|SE[ÇC][ÃA]O|Se[çc][ãa]o|SUBSE[ÇC][ÃA]O|Subse[çc][ãa]o)"
    r"\s+[IVXLCDM\d]+[\w\-]*\b.*$", re.MULTILINE)
MAX_SALTO = 25  # número de artigo que pula mais que isso é citação, não início de artigo
# Ato de aprovação (Art. 1-4) seguido do Código anexo, que recomeça no Art. 1
_RESTART = re.compile(r"^C[ÓO]DIGO\b[^\n]{0,80}NORMAS", re.MULTILINE)
ATO_APROVACAO = " (ato de aprovação)"


@dataclass
class Dispositivo:
    fonte_id: str
    dispositivo: str  # "Art. 17", "Art. 213-A", "Preâmbulo", "p. 12"
    secao: str  # último título/capítulo/seção visto
    pagina: int
    texto: str


def _art_key(num: int, suf: str | None) -> tuple[int, int, str]:
    # "440-Z" < "440-AA": sufixo ordena primeiro pelo tamanho
    return (num, len(suf or ""), suf or "")


def segment_articles(fonte_id: str, pages: list[tuple[int, str]]) -> list[Dispositivo]:
    """Quebra o texto em artigos, aceitando só números crescentes (evita citações no meio do texto)."""
    out: list[Dispositivo] = []
    atual = Dispositivo(fonte_id, "Preâmbulo", "", pages[0][0] if pages else 0, "")
    ultimo = (0, 0, "")
    secao = ""
    pode_reiniciar = False

    for pagina, texto in pages:
        pos = 0
        head_start: int | None = None  # títulos entre dois artigos pertencem ao artigo seguinte
        eventos = sorted(
            [(m.start(), "art", m) for m in _ART.finditer(texto)]
            + [(m.start(), "head", m) for m in _HEADING.finditer(texto)]
            + [(m.start(), "restart", m) for m in _RESTART.finditer(texto)],
            key=lambda e: e[0],
        )
        for start, kind, m in eventos:
            if kind == "restart":
                pode_reiniciar = ultimo[0] > 0  # só depois de já ter visto artigos
                continue
            if kind == "head":
                if head_start is None:
                    head_start = start
                secao = m.group(0).strip()[:120]
                continue
            num, suf = int(m.group(1).replace(".", "")), m.group(2)
            key = _art_key(num, suf)
            if pode_reiniciar and num == 1 and not suf:
                for d in out + [atual]:
                    if d.dispositivo.startswith("Art.") and not d.dispositivo.endswith(ATO_APROVACAO):
                        d.dispositivo += ATO_APROVACAO
                ultimo, pode_reiniciar = (0, 0, ""), False
            if not (key > ultimo and num - ultimo[0] <= MAX_SALTO):
                continue  # citação ("Art. 5º da Lei...") ou numeração fora de ordem
            corte = head_start if head_start is not None else start
            atual.texto += texto[pos:corte]
            if atual.texto.strip():
                out.append(atual)
            rotulo = f"Art. {num}" + (f"-{suf}" if suf else "")
            atual = Dispositivo(fonte_id, rotulo, secao, pagina, texto[corte:start])
            ultimo = key
            pos, head_start = start, None
        atual.texto += texto[pos:] + "\n"

    if atual.texto.strip():
        out.append(atual)
    for d in out:
        d.texto = normalize(d.texto)
    return out


def segment_pages(fonte_id: str, pages: list[tuple[int, str]]) -> list[Dispositivo]:
    return [Dispositivo(fonte_id, f"p. {p}", "", p, t) for p, t in pages if t.strip()]


def segment(fonte: Fonte) -> list[Dispositivo]:
    pages = extract(fonte)
    return segment_articles(fonte.id, pages) if fonte.por_artigo else segment_pages(fonte.id, pages)


def to_jsonl(dispositivos: list[Dispositivo]) -> str:
    return "\n".join(json.dumps(asdict(d), ensure_ascii=False) for d in dispositivos) + "\n"
