"""Manifesto das normas exibidas na barra lateral (data/corpus_manifest.json)."""

from __future__ import annotations

import json
from pathlib import Path

MANIFESTO = Path(__file__).resolve().parents[2] / "data" / "corpus_manifest.json"
CAMPOS = ("norma", "baixado_em", "versao_norma", "criterio")
TOTAL_FONTES = 11

AVISO_NORMAS = (
    "Corpus baixado das fontes oficiais em 23/09/2026. As versões indicadas são as que constam do texto de "
    "cada documento. A vigência deve ser conferida pelo Oficial Registrador."
)


def carregar_normas(caminho: Path = MANIFESTO) -> list[dict]:
    """Lê as fontes do manifesto; falha se faltar fonte ou se algum dos quatro campos estiver vazio."""
    fontes = json.loads(Path(caminho).read_text(encoding="utf-8")).get("fontes", [])
    if len(fontes) < TOTAL_FONTES:
        raise ValueError(f"manifesto com {len(fontes)} fontes; esperado {TOTAL_FONTES}")
    for i, fonte in enumerate(fontes):
        vazios = [c for c in CAMPOS if not str(fonte.get(c) or "").strip()]
        if vazios:
            raise ValueError(f"fonte {fonte.get('id', i)} sem {', '.join(vazios)}")
    return fontes
