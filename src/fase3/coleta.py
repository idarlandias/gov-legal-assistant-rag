"""Coleta comparativa: schema das respostas, caminhos e perguntas.

Uma resposta por arquivo: data/benchmark/respostas_externas/<sistema>/<pergunta_id>.json.
Todos os sistemas (inclusive o nosso RAG, exportado do benchmark) passam pelo mesmo schema
e pelo mesmo pontuador.
"""

from __future__ import annotations

import json
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

RAIZ = Path(__file__).resolve().parents[2]
DIR_COLETA = RAIZ / "data" / "benchmark" / "respostas_externas"
PERGUNTAS_JSON = RAIZ / "docs" / "fase3" / "benchmark" / "perguntas.json"

FUSO_COLETA = timezone(timedelta(hours=-3))

SISTEMA_PROPRIO = "assistente_registral_ce"
# Ordem das colunas em qualquer saída comparativa
SISTEMAS = (SISTEMA_PROPRIO, "jus_ia", "juridico_ai", "llm_generico")
# Nome antigo do produto, aceito só na leitura (arquivos coletados antes da renomeação)
ALIASES_SISTEMA = {"cartorioseguro": SISTEMA_PROPRIO}

# Pergunta do comparativo, externa ao benchmark (não entra em perguntas.json)
PERGUNTA_26_ID = 26
PERGUNTA_26 = ("O Provimento 15/2026/CGJCE alterou a redação do Art. 1.103 do Código de Normas do Ceará. "
               "O que mudou na qualificação das partes?")


def perguntas_oficiais() -> dict[int, str]:
    """{id: texto} das 25 perguntas do benchmark + a 26, externa."""
    dados = json.loads(PERGUNTAS_JSON.read_text(encoding="utf-8"))
    textos = {p["id"]: p["pergunta"] for p in dados["perguntas"]}
    textos[PERGUNTA_26_ID] = PERGUNTA_26
    return textos


PERGUNTAS_COLETA_MD = RAIZ / "data" / "benchmark" / "perguntas_coleta.md"
ORDEM_COLETA_JSON = RAIZ / "data" / "benchmark" / "ordem_coleta.json"
SEED_ORDEM = 20261013


def ordem_por_sistema(seed: int = SEED_ORDEM) -> dict[str, list[int]]:
    """Ordem de aplicação das 26 perguntas, diferente por sistema e reproduzível pela seed."""
    ordens = {}
    for sistema in SISTEMAS:
        ids = sorted(perguntas_oficiais())
        random.Random(f"{seed}:{sistema}").shuffle(ids)
        ordens[sistema] = ids
    return ordens


def perguntas_coleta_md() -> str:
    """Folha de coleta: cada pergunta num bloco próprio, com o texto idêntico ao oficial."""
    partes = [
        "# Perguntas para a coleta comparativa",
        "",
        "Copie o texto de cada bloco **sem alterar nada** e cole numa **sessão nova** do sistema avaliado.",
        "A ordem de aplicação de cada sistema está em `ordem_coleta.json`. Registre cada resposta com "
        "`scripts/registrar_resposta.py`.",
        "",
        "Perguntas 1 a 25: texto idêntico a `docs/fase3/benchmark/perguntas.json`.",
        "",
    ]
    for pid, texto in sorted(perguntas_oficiais().items()):
        titulo = f"## Pergunta {pid}"
        if pid == PERGUNTA_26_ID:
            titulo += " (externa ao benchmark)"
        partes += [titulo, "", "```text", texto, "```", ""]
    return "\n".join(partes)


def normalizar_sistema(valor: str) -> str:
    v = valor.strip().lower()
    return ALIASES_SISTEMA.get(v, v)


class RespostaColetada(BaseModel):
    pergunta_id: int = Field(..., ge=1, le=PERGUNTA_26_ID)
    pergunta_texto: str
    sistema: str
    modelo_ou_plano: str
    coletado_em: str = Field(..., description="ISO 8601 com fuso -03:00, ex.: 2026-10-13T11:31:32-03:00")
    resposta_integral: str
    citacoes_declaradas: list[str] = Field(default_factory=list)
    recusou_responder: bool = False
    observacao: str = ""
    # Só o RAG próprio expõe o contexto: base da camada 2 (ancoragem). Concorrentes: None.
    trechos_recuperados: list[str] | None = None

    @field_validator("sistema")
    @classmethod
    def _sistema_conhecido(cls, v: str) -> str:
        v = normalizar_sistema(v)
        if v not in SISTEMAS:
            raise ValueError(f"sistema desconhecido: {v!r}; use um de {SISTEMAS}")
        return v

    @field_validator("coletado_em")
    @classmethod
    def _iso_com_fuso_de_brasilia(cls, v: str) -> str:
        if not re.search(r"[+-]\d{2}:\d{2}$", v):
            raise ValueError("coletado_em precisa de fuso explícito (-03:00)")
        if datetime.fromisoformat(v).utcoffset() != timedelta(hours=-3):
            raise ValueError("coletado_em deve estar em -03:00")
        return v

    @field_validator("modelo_ou_plano", "pergunta_texto")
    @classmethod
    def _nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("campo obrigatório vazio")
        return v

    @model_validator(mode="after")
    def _coerencia(self) -> "RespostaColetada":
        oficial = perguntas_oficiais().get(self.pergunta_id)
        if self.pergunta_texto != oficial:
            raise ValueError(f"pergunta_texto difere do texto oficial da pergunta {self.pergunta_id}")
        if not self.resposta_integral.strip() and not self.recusou_responder:
            raise ValueError("resposta_integral vazia sem recusou_responder")
        if self.trechos_recuperados is not None and self.sistema != SISTEMA_PROPRIO:
            raise ValueError("trechos_recuperados só se aplica ao RAG próprio")
        return self


def caminho(sistema: str, pergunta_id: int, base: Path = DIR_COLETA) -> Path:
    return base / normalizar_sistema(sistema) / f"{pergunta_id}.json"


def gravar(resp: RespostaColetada, base: Path = DIR_COLETA, force: bool = False) -> Path:
    destino = caminho(resp.sistema, resp.pergunta_id, base)
    if destino.exists() and not force:
        raise FileExistsError(f"{destino} já existe; use --force para sobrescrever")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resp.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destino


def ler_todas(base: Path = DIR_COLETA) -> dict[str, dict[int, RespostaColetada]]:
    """{sistema: {pergunta_id: resposta}}; pastas com o nome antigo são lidas como o nome novo."""
    saida: dict[str, dict[int, RespostaColetada]] = {}
    if not base.exists():
        return saida
    for arq in sorted(base.glob("*/*.json")):
        resp = RespostaColetada.model_validate_json(arq.read_text(encoding="utf-8"))
        saida.setdefault(resp.sistema, {})[resp.pergunta_id] = resp
    return saida
