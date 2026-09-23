"""Fontes oficiais do corpus da Fase 3 (Registro de Imóveis CE × LAI × LGPD).

Critério: somente legislação, atos normativos e orientações de órgãos públicos.
URLs verificadas em 2026-09-23. Ao trocar uma URL, rode `build_corpus.py download`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Formato = Literal["html", "pdf", "dou"]


@dataclass(frozen=True)
class Fonte:
    id: str
    sigla: str  # como a fonte aparece na citação: "Lei 6.015/1973"
    titulo: str
    esfera: Literal["federal", "cnj", "estadual_ce", "anpd"]
    tipo: Literal["lei", "decreto", "provimento", "codigo_normas", "resolucao", "guia"]
    url: str
    formato: Formato
    por_artigo: bool = True  # False: guias sem articulado, fatiados por página

    @property
    def arquivo(self) -> str:
        return f"{self.id}.{'pdf' if self.formato == 'pdf' else 'html'}"


PLANALTO = "https://www.planalto.gov.br/ccivil_03"
ANPD = "https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes"

FONTES: list[Fonte] = [
    Fonte("lei_6015_1973", "Lei 6.015/1973", "Lei de Registros Públicos", "federal", "lei",
          f"{PLANALTO}/leis/l6015compilada.htm", "html"),
    Fonte("lei_13709_2018", "LGPD (Lei 13.709/2018)", "Lei Geral de Proteção de Dados Pessoais",
          "federal", "lei", f"{PLANALTO}/_ato2015-2018/2018/lei/l13709compilado.htm", "html"),
    Fonte("lei_12527_2011", "LAI (Lei 12.527/2011)", "Lei de Acesso à Informação", "federal", "lei",
          f"{PLANALTO}/_ato2011-2014/2011/lei/l12527.htm", "html"),
    Fonte("decreto_7724_2012", "Decreto 7.724/2012", "Regulamento da LAI no Poder Executivo federal",
          "federal", "decreto", f"{PLANALTO}/_ato2011-2014/2012/decreto/d7724.htm", "html"),
    Fonte("lei_8935_1994", "Lei 8.935/1994", "Lei dos Notários e Registradores", "federal", "lei",
          f"{PLANALTO}/leis/l8935.htm", "html"),
    Fonte("prov_cnj_149_2023", "Provimento CNJ 149/2023",
          "Código Nacional de Normas da Corregedoria Nacional — Foro Extrajudicial (compilado 20/08/2026)",
          "cnj", "provimento",
          "https://atos.cnj.jus.br/files/compilado131723202608206a86fe6344e53.pdf", "pdf"),
    Fonte("codigo_normas_ce", "Código de Normas CGJ-CE",
          "Código de Normas do Serviço Notarial e Registral do Ceará (versão atualizada, set/2026)",
          "estadual_ce", "codigo_normas",
          "https://portal.tjce.jus.br/uploads/2022/07/Codigo-de-Normas-Extrajudial-Versao-Atualizada-1789148558.pdf",
          "pdf"),
    Fonte("prov_cgjce_15_2026", "Provimento 15/2026/CGJCE",
          "Altera o Código de Normas do CE (qualificação das partes)", "estadual_ce", "provimento",
          "https://portal.tjce.jus.br/uploads/2022/07/Provimento-no-15-2026-CGJCE-1789148866.pdf", "pdf"),
    Fonte("res_anpd_15_2024", "Resolução CD/ANPD 15/2024",
          "Regulamento de Comunicação de Incidente de Segurança", "anpd", "resolucao",
          "https://www.in.gov.br/en/web/dou/-/resolucao-cd/anpd-n-15-de-24-de-abril-de-2024-556243024",
          "dou"),
    Fonte("anpd_guia_agentes", "Guia ANPD — Agentes de Tratamento",
          "Guia Orientativo para Definições dos Agentes de Tratamento e do Encarregado (2ª versão)",
          "anpd", "guia",
          f"{ANPD}/Segunda_Versao_do_Guia_de_Agentes_de_Tratamento_retificada.pdf/@@download/file",
          "pdf", por_artigo=False),
    Fonte("anpd_guia_seguranca", "Guia ANPD — Segurança da Informação",
          "Guia de Segurança da Informação para Agentes de Tratamento de Pequeno Porte",
          "anpd", "guia", f"{ANPD}/guia-vf.pdf/@@download/file", "pdf", por_artigo=False),
]

FONTES_POR_ID = {f.id: f for f in FONTES}
