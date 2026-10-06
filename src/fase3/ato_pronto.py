"""Gerador de Ato Pronto de Balcão (Fase 3).

Transfere o valor do RAG para o fluxo de trabalho real do cartório de Registro de Imóveis:
- Substitui o chat conversacional por triagem objetiva de balcão (Semáforo Alfândega: Verde, Amarelo, Vermelho).
- Devolve veredito, fundamentação vinculante (TJCE/CNJ), minuta cartorial pronta e registro de auditoria LGPD (ROPA).
"""

from __future__ import annotations

import json
import re
import time
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.fase3.pipeline import Fase3Pipeline


# ---------------------------------------------------------------- Modelos de Dados


class CanalRisco(str, Enum):
    VERDE = "VERDE"        # Liberação direta (baixo risco / dever legal / próprio titular)
    AMARELO = "AMARELO"    # Liberação condicionada (tarjamento obrigatório de dados pessoais excessivos)
    VERMELHO = "VERMELHO"  # Bloqueio / Exigência formal (Nota Devolutiva fundamentada)


class PedidoBalcao(BaseModel):
    """Entrada estruturada do pedido recebido no balcão da serventia."""

    tipo_pedido: str = Field(
        ...,
        description="Ex: Certidão de Matrícula (Inteiro Teor), Busca por Indicador Pessoal, "
                    "Cópia de Título Arquivado, Informação Verbal, Pedido de Exclusão LGPD"
    )
    solicitante: str = Field(
        ...,
        description="Ex: Próprio Titular / Proprietário, Terceiro sem vínculo comprovado, "
                    "Cônjuge / Herdeiro, Advogado com procuração, Órgão Público / Polícia"
    )
    dados_sensiveis: list[str] = Field(
        default_factory=list,
        description="Dados sob risco ou proteção (CPF, RG, Regime de bens, Filiação, Saúde/Curatela, Ônus cancelados)"
    )
    detalhes_caso: str = Field(
        default="",
        description="Contexto fático ou detalhes adicionais da solicitação"
    )
    protocolo: str = Field(
        default="BALCAO-AUTO",
        description="Identificador de protocolo ou atendimento do balcão"
    )


class DispositivoLegal(BaseModel):
    norma: str = Field(..., description="Nome da norma (ex: Código de Normas CGJ-CE, Provimento CNJ 149/2023, Lei 6.015/1973, LGPD)")
    artigo: str = Field(..., description="Artigo, parágrafo ou inciso exato (ex: Art. 1131, §10)")
    aplicacao: str = Field(..., description="Aplicação prática e vinculante ao caso concreto")


class RegistroAuditoriaLGPD(BaseModel):
    """Ficha de Registro das Atividades de Tratamento (ROPA - Art. 37 da LGPD)."""

    finalidade: str = Field(..., description="Finalidade legítima do ato (ex: Publicidade registral imobiliária / Segurança jurídica)")
    base_legal_lgpd: str = Field(..., description="Base legal da LGPD (ex: Art. 7º, II - Cumprimento de obrigação legal ou regulatória)")
    categoria_titular: str = Field(..., description="Titular dos dados (ex: Proprietário do imóvel, Requerente)")
    dados_tratados: list[str] = Field(..., description="Dados pessoais afetados no ato")
    salvaguardas_adotadas: str = Field(..., description="Medidas técnicas e de compliance (ex: Tarjamento prévio, protocolo retido)")
    conformidade_cnj_149: str = Field(default="Em conformidade com as diretrizes de proteção de dados do Provimento CNJ 149/2023.")


class AtoProntoOutput(BaseModel):
    """Saída completa do Ato Pronto para o escrevente no balcão."""

    canal: CanalRisco = Field(..., description="Classificação de risco da analogia da alfândega (VERDE, AMARELO ou VERMELHO)")
    veredito: str = Field(..., description="Veredito direto: DEFERIDO INTEGRAL, DEFERIDO COM TARJAMENTO ou INDEFERIDO (NOTA DEVOLUTIVA)")
    instrucao_balcao: str = Field(..., description="Instrução em até 2 linhas para execução imediata no balcão")
    fundamentacao: list[DispositivoLegal] = Field(default_factory=list, description="Artigos vigentes aplicáveis")
    minuta_ato: str = Field(..., description="Texto pronto formatado para colar no sistema do cartório ou imprimir (Despacho ou Nota Devolutiva)")
    auditoria_lgpd: RegistroAuditoriaLGPD
    fontes_corpus: list[str] = Field(default_factory=list, description="Lista de fontes normativas oficiais recuperadas pelo RAG")
    latencia_s: float = Field(default=0.0, description="Tempo total de processamento em segundos")


# ---------------------------------------------------------------- Query & Prompt


def gerar_query_recuperacao(pedido: PedidoBalcao) -> str:
    """Monta consulta semântica e lexical direcionada ao acervo normativo da CGJ-CE e CNJ."""
    termos = [pedido.tipo_pedido, pedido.solicitante]
    if pedido.dados_sensiveis:
        termos.extend(pedido.dados_sensiveis)
    if pedido.detalhes_caso:
        termos.append(pedido.detalhes_caso)
    return " ".join(termos)


def build_ato_pronto_prompt(context: str, pedido: PedidoBalcao) -> str:
    dados_str = ", ".join(pedido.dados_sensiveis) if pedido.dados_sensiveis else "Nenhum informado"
    
    return f"""Você é o Assessor Técnico Especialista em Registro de Imóveis do Ceará e Compliance Registral (LGPD × Lei 6.015/1973 × Provimento CNJ 149/2023 × Código de Normas da Corregedoria Geral da Justiça do Ceará - CGJ-CE).

Sua missão é emitir um ATO PRONTO OPERACIONAL para o escrevente de balcão utilizando a analogia da alfândega:
- Canal VERDE: Pedido seguro, obrigação de publicidade imediata e integral (ex: próprio titular requerendo sua matrícula, terceiro pedindo certidão de situação jurídica atual sem dados excessivos).
- Canal AMARELO: Fornecimento permitido, mas com TARJAMENTO OBRIGATÓRIO de dados pessoais excessivos (ex: terceiro requerendo certidão de inteiro teor com CPF, documentos, regime de bens ou filiação de outras pessoas — fornece a certidão, porém tarjando dados que não dizem respeito à publicidade real).
- Canal VERMELHO: Bloqueio ou Exigência Formal (ex: busca ampla por CPF sem justificativa legal; pedido de exclusão de dados da matrícula com base na LGPD — livros registrais têm guarda perpétua e dever legal; informação verbal por telefone; dados sob segredo judicial). Deve gerar NOTA DEVOLUTIVA formal fundamentada.

REGRAS DE CONFORMIDADE:
1. Baseie-se ESTRITAMENTE no contexto normativo fornecido abaixo. NUNCA cite normas revogadas (como Provimento CNJ 134/2022). Cite as normas vigentes (Provimento CNJ 149/2023, Código de Normas da CGJ-CE, Lei 6.015/73, LGPD).
2. A minuta_ato deve ser um texto formal, profissional e completo para uso imediato pelo escrevente (incluindo número de protocolo `{pedido.protocolo}`, fundamentação e conclusão formal).
3. A auditoria_lgpd deve atender com rigor aos artigos 37 e 38 da LGPD (ROPA).
4. Retorne APENAS um objeto JSON válido, sem texto explicativo adicional fora do JSON.

FORMATO OBRIGATÓRIO (JSON):
{{
  "canal": "VERDE" | "AMARELO" | "VERMELHO",
  "veredito": "DEFERIDO INTEGRAL" | "DEFERIDO COM TARJAMENTO" | "INDEFERIDO (NOTA DEVOLUTIVA)",
  "instrucao_balcao": "Texto conciso de até 2 linhas orientando a ação física imediata no balcão.",
  "fundamentacao": [
    {{
      "norma": "Nome da Norma",
      "artigo": "Art. ...",
      "aplicacao": "Aplicação no caso concreto"
    }}
  ],
  "minuta_ato": "Texto completo da minuta (Despacho de Deferimento ou Nota Devolutiva Registral)",
  "auditoria_lgpd": {{
    "finalidade": "Finalidade específica do ato registral",
    "base_legal_lgpd": "Dispositivo da LGPD (ex: Art. 7º, II)",
    "categoria_titular": "Categoria do titular afetado",
    "dados_tratados": ["lista", "de", "dados"],
    "salvaguardas_adotadas": "Salvaguardas aplicadas (ex: tarjamento, arquivo do protocolo)",
    "conformidade_cnj_149": "Conformidade com o Livro I do Prov. CNJ 149/2023"
  }}
}}

CONTEXTO NORMATIVO DO CARTÓRIO (CGJ-CE / CNJ / LEGISLAÇÃO):
{context}

DADOS DO CASO NO BALCÃO:
- Protocolo: {pedido.protocolo}
- Tipo de Pedido: {pedido.tipo_pedido}
- Solicitante: {pedido.solicitante}
- Dados Sensíveis / Pessoais Envolvidos: {dados_str}
- Detalhes Adicionais: {pedido.detalhes_caso or "Nenhum"}

RESPOSTA (JSON):"""


# ---------------------------------------------------------------- Execução


def _limpar_json(texto: str) -> str:
    """Extrai conteúdo JSON limpo caso venha encapsulado em blocos markdown."""
    texto = texto.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    start = texto.find("{")
    end = texto.rfind("}")
    if start != -1 and end != -1 and end > start:
        return texto[start : end + 1]
    return texto


def processar_ato_pronto(pipeline: Fase3Pipeline, pedido: PedidoBalcao, k: int = 5) -> AtoProntoOutput:
    """Processa o pedido no pipeline da Fase 3 e gera o Ato Pronto estruturado."""
    t0 = time.perf_counter()

    # 1. Recuperação Híbrida especializada
    query = gerar_query_recuperacao(pedido)
    hits = pipeline.retrieve(query, k=k)

    contexto = "\n\n---\n\n".join(
        f"[{h.get('dispositivo') or h['source']}:p{h['page']}]\n{h['text']}"
        for h in hits
    )

    # 2. Prompt Estruturado
    prompt = build_ato_pronto_prompt(context=contexto, pedido=pedido)
    messages = [{"role": "user", "content": prompt}]

    api_kwargs: dict[str, Any] = {
        "model": pipeline.llm_model,
        "messages": messages,
        "temperature": 0.0,
    }

    # Tenta usar json_object se suportado pelo provedor
    try:
        api_kwargs["response_format"] = {"type": "json_object"}
        response = pipeline._call_chat_completions(**api_kwargs)
    except Exception:
        # Fallback sem response_format se der erro de parâmetro
        api_kwargs.pop("response_format", None)
        response = pipeline._call_chat_completions(**api_kwargs)

    conteudo_bruto = response.choices[0].message.content or "{}"
    conteudo_json = _limpar_json(conteudo_bruto)

    try:
        dados = json.loads(conteudo_json)
        # Converte o canal para maiúsculo se necessário
        if "canal" in dados and isinstance(dados["canal"], str):
            dados["canal"] = dados["canal"].upper()
        saida = AtoProntoOutput.model_validate(dados)
    except Exception as e:
        # Fallback seguro caso o LLM falhe no formato estruturado
        canal_fallback = CanalRisco.AMARELO
        if any(w in conteudo_bruto.lower() for w in ["negar", "devolutiva", "indeferid", "vedado", "proibido"]):
            canal_fallback = CanalRisco.VERMELHO
        elif any(w in conteudo_bruto.lower() for w in ["deferido integral", "liberado", "sem restrição"]):
            canal_fallback = CanalRisco.VERDE

        saida = AtoProntoOutput(
            canal=canal_fallback,
            veredito="ANÁLISE DE BALCÃO REALIZADA",
            instrucao_balcao="Verifique o teor da resposta e aplique as salvaguardas de conformidade.",
            fundamentacao=[
                DispositivoLegal(
                    norma="Provimento CNJ 149/2023 / Código de Normas CGJ-CE",
                    artigo="Regras de Publicidade Registral e LGPD",
                    aplicacao="Aplicação da proteção de dados aos registros imobiliários."
                )
            ],
            minuta_ato=conteudo_bruto,
            auditoria_lgpd=RegistroAuditoriaLGPD(
                finalidade="Publicidade registral imobiliária",
                base_legal_lgpd="Art. 7º, II da LGPD",
                categoria_titular="Titular do imóvel",
                dados_tratados=pedido.dados_sensiveis or ["Dados da matrícula"],
                salvaguardas_adotadas="Verificação de interesse e aplicação de sigilo legal.",
            ),
        )

    saida.latencia_s = round(time.perf_counter() - t0, 2)
    saida.fontes_corpus = [
        f"{h.get('dispositivo') or h['source']} (pág. {h['page']})" for h in hits
    ]
    return saida
