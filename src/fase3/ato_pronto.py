"""Gerador de Ato Pronto de Balcão (Fase 3).

Transfere o valor do RAG para o fluxo de trabalho real do cartório de Registro de Imóveis:
- Substitui o chat conversacional por triagem objetiva de balcão (Semáforo Alfândega: Verde, Amarelo, Vermelho).
- Devolve veredito, fundamentação vinculante (TJCE/CNJ), minuta cartorial pronta e registro de auditoria LGPD (ROPA).
"""

from __future__ import annotations

import json
import logging
import re
import time
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.fase3.retrieval import rotulo_fonte
from src.fase3.verificador_citacoes import RelatorioCitacoes, verificar

if TYPE_CHECKING:
    from src.fase3.pipeline import Fase3Pipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------- Modelos de Dados


class CanalRisco(str, Enum):
    VERDE = "VERDE"        # Liberação direta (baixo risco / dever legal / próprio titular)
    AMARELO = "AMARELO"    # Fornecimento mediante exigência prévia: identificação + finalidade (CE Art. 1.128 §2º)
    VERMELHO = "VERMELHO"  # Bloqueio / Exigência formal (Nota Devolutiva fundamentada)
    INDEFINIDO = "INDEFINIDO"  # Falha na análise: nada é decidido, exige revisão manual


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
    salvaguardas_adotadas: str = Field(..., description="Medidas técnicas e de compliance (ex: identificação do requerente, protocolo retido)")
    conformidade_cnj_149: str = Field(default="Em conformidade com as diretrizes de proteção de dados do Provimento CNJ 149/2023.")


class RegistroFalha(BaseModel):
    """Registro de uma análise que falhou: só o motivo, sem campos de auditoria inventados."""

    falha: str = Field(..., description="Tipo da exceção ou motivo (ex: 'contexto vazio')")


class AtoProntoOutput(BaseModel):
    """Saída completa do Ato Pronto para o escrevente no balcão."""

    canal: CanalRisco = Field(..., description="Classificação de risco da analogia da alfândega (VERDE, AMARELO ou VERMELHO)")
    veredito: str = Field(..., description="Sugestão: SUGESTÃO: DEFERIR, SUGESTÃO: DEFERIR MEDIANTE EXIGÊNCIA PRÉVIA "
                                           "ou SUGESTÃO: INDEFERIR (NOTA DEVOLUTIVA)")
    instrucao_balcao: str = Field(..., description="Instrução em até 2 linhas para execução imediata no balcão")
    fundamentacao: list[DispositivoLegal] = Field(default_factory=list, description="Artigos vigentes aplicáveis")
    minuta_ato: str = Field(..., description="Texto pronto formatado para colar no sistema do cartório ou imprimir (Despacho ou Nota Devolutiva)")
    auditoria_lgpd: RegistroAuditoriaLGPD | RegistroFalha
    fontes_corpus: list[str] = Field(default_factory=list, description="Lista de fontes normativas oficiais recuperadas pelo RAG")
    latencia_s: float = Field(default=0.0, description="Tempo total de processamento em segundos")
    citacoes: RelatorioCitacoes | None = Field(
        default=None, description="Conferência das citações contra os trechos recuperados (preenchida pelo sistema)")

    @field_validator("veredito")
    @classmethod
    def _veredito_como_sugestao(cls, v: str) -> str:
        """Todo veredito é sugestão ao Oficial; formato antigo é convertido, supressão de dados é rejeitada."""
        v = v.strip()
        if v == VEREDITO_FALHA:
            return v
        if re.search(r"tarj|suprim", v, re.IGNORECASE):
            # vira INDEFINIDO no processar_ato_pronto: o prompt proíbe sugerir supressão no inteiro teor
            raise ValueError("veredito sugere suprimir dados da certidão")
        if not v.upper().startswith("SUGESTÃO"):
            v = re.sub(r"^indeferid[oa]", "SUGESTÃO: INDEFERIR", v, flags=re.IGNORECASE)
            v = re.sub(r"^deferid[oa]", "SUGESTÃO: DEFERIR", v, flags=re.IGNORECASE)
            if not v.upper().startswith("SUGESTÃO"):
                v = f"SUGESTÃO: {v}"
        return v

    @model_validator(mode="after")
    def _falha_so_com_indefinido(self) -> "AtoProntoOutput":
        # Impede que o LLM devolva um ato decidido (VERDE/AMARELO/VERMELHO) sem auditoria real
        if isinstance(self.auditoria_lgpd, RegistroFalha) != (self.canal == CanalRisco.INDEFINIDO):
            raise ValueError("RegistroFalha só é válido com canal INDEFINIDO, e vice-versa")
        return self


# ---------------------------------------------------------------- Query & Prompt


# Cada opção de "tipo de pedido" da UI → vocabulário das normas (CE Art. 1.128, CNJ 149 Arts. 123-128).
# Os rótulos crus da UI não recuperavam o CNJ 123 nem o CE 1.128 nem no top-8 (medido em 13/10/2026).
EXPANSAO_TIPO_PEDIDO: dict[str, str] = {
    "certidão de inteiro teor de matrícula":
        "certidão de matrícula registro averbação identificação do requerente independentemente de finalidade",
    "certidão de situação jurídica atual (vigente)":
        "certidão situação jurídica atual do imóvel titularidade ônus reais não cancelados independentemente de "
        "finalidade",
    "histórico de ônus / cadeia filiatória / ônus cancelados":
        "certidão de atos anteriores da cadeia filiatória identificação segura finalidade",
    "busca por indicador pessoal (pesquisa de bens por cpf/nome)":
        "requisição de busca indicador pessoal ou real identificação segura indicação da finalidade",
    "cópia de título / documento arquivado no cartório":
        "certidão de documento arquivado previsão legal específica de expedição",
    "informação verbal no balcão ou por telefone":
        "fornecimento de informações sobre o registro não veiculadas por certidão identificação finalidade",
    "pedido de exclusão de dados da matrícula com base na lgpd":
        "direitos do titular eliminação dos dados pessoais tratados guarda dos livros do registro",
    "pedido de retificação de dado pessoal na matrícula":
        "retificação do registro averbação correção de dados incompletos inexatos",
    "requisição por órgão público / polícia / prefeitura sem ordem judicial":
        "compartilhamento de dados com órgãos públicos requisição identificação finalidade",
    "acesso em lote / convênio com empresa imobiliária ou fintech":
        "pedidos de certidão busca e informações apresentados em bloco dados pessoais de mais de uma matrícula",
}


def gerar_query_recuperacao(pedido: PedidoBalcao) -> str:
    """Consulta = vocabulário normativo do tipo de pedido + rótulos da UI + termos livres ao final."""
    tipo = pedido.tipo_pedido.strip()
    expansao = EXPANSAO_TIPO_PEDIDO.get(tipo.lower())
    if expansao is None:
        logger.warning("Tipo de pedido sem expansão normativa, usando o rótulo: %r", tipo)
        expansao = tipo
    termos = [expansao, pedido.solicitante, *pedido.dados_sensiveis]
    if pedido.detalhes_caso:
        termos.append(pedido.detalhes_caso)  # texto livre do escrevente sempre ao final
    return " ".join(t for t in termos if t)


# Definição dos canais: nenhuma menção a supressão de dados (não há norma no corpus que a autorize
# na certidão de inteiro teor; o CE Art. 1.131 §10 manda reproduzir todo o conteúdo).
CANAIS_PROMPT = """- Canal VERDE: Pedido seguro, obrigação de publicidade imediata e integral (ex: próprio titular requerendo sua matrícula, terceiro pedindo certidão de situação jurídica atual sem dados excessivos).
- Canal AMARELO: Fornecimento permitido mediante EXIGÊNCIA PRÉVIA — identificação do requerente e indicação da finalidade — nas hipóteses do Art. 1.128, §2º, I a V, do Código de Normas da CGJ-CE, com abertura da ficha prevista no §3º do mesmo artigo.
- Canal VERMELHO: Bloqueio ou Exigência Formal (ex: busca ampla por CPF sem justificativa legal; pedido de exclusão de dados da matrícula com base na LGPD — livros registrais têm guarda perpétua e dever legal; dados sob segredo judicial). Deve gerar NOTA DEVOLUTIVA formal fundamentada."""

REGRA_INTEIRO_TEOR = (
    "Nunca instrua a suprimir, tarjar ou omitir dados de uma certidão de inteiro teor. Se o caso parecer "
    "exigir conteúdo reduzido, indique a certidão de situação jurídica atual (Prov. CNJ 149/2023, Art. 125) "
    "como alternativa."
)

VEREDITOS = (
    "SUGESTÃO: DEFERIR",
    "SUGESTÃO: DEFERIR MEDIANTE EXIGÊNCIA PRÉVIA",
    "SUGESTÃO: INDEFERIR (NOTA DEVOLUTIVA)",
)
AVISO_RESPONSABILIDADE = "Sugestão de ato. A decisão e a responsabilidade são do Oficial Registrador."


def build_ato_pronto_prompt(context: str, pedido: PedidoBalcao) -> str:
    dados_str = ", ".join(pedido.dados_sensiveis) if pedido.dados_sensiveis else "Nenhum informado"
    vereditos = " | ".join(f'"{v}"' for v in VEREDITOS)

    return f"""Você é o Assessor Técnico Especialista em Registro de Imóveis do Ceará e Compliance Registral (LGPD × Lei 6.015/1973 × Provimento CNJ 149/2023 × Código de Normas da Corregedoria Geral da Justiça do Ceará - CGJ-CE).

Sua missão é emitir uma SUGESTÃO DE ATO OPERACIONAL para o escrevente de balcão utilizando a analogia da alfândega:
{CANAIS_PROMPT}

REGRAS DE CONFORMIDADE:
1. Baseie-se ESTRITAMENTE no contexto normativo fornecido abaixo. NUNCA cite normas revogadas (como Provimento CNJ 134/2022). Cite as normas vigentes (Provimento CNJ 149/2023, Código de Normas da CGJ-CE, Lei 6.015/73, LGPD).
2. A minuta_ato deve ser um texto formal, profissional e completo para uso imediato pelo escrevente (incluindo número de protocolo `{pedido.protocolo}`, fundamentação e conclusão formal).
3. A auditoria_lgpd deve atender com rigor aos artigos 37 e 38 da LGPD (ROPA).
4. Retorne APENAS um objeto JSON válido, sem texto explicativo adicional fora do JSON.
5. {REGRA_INTEIRO_TEOR}

FORMATO OBRIGATÓRIO (JSON):
{{
  "canal": "VERDE" | "AMARELO" | "VERMELHO",
  "veredito": {vereditos},
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
    "salvaguardas_adotadas": "Salvaguardas aplicadas (ex: identificação do requerente, registro da finalidade, arquivo do protocolo)",
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


VEREDITO_FALHA = "FALHA NA ANÁLISE — REVISÃO MANUAL NECESSÁRIA"


def _ato_indefinido(motivo: str) -> AtoProntoOutput:
    """Saída de falha: nenhum canal decidido, nenhuma fundamentação ou minuta inventada."""
    return AtoProntoOutput(
        canal=CanalRisco.INDEFINIDO,
        veredito=VEREDITO_FALHA,
        instrucao_balcao="",
        fundamentacao=[],
        minuta_ato="",
        auditoria_lgpd=RegistroFalha(falha=motivo),
    )


K_ATO_PRONTO = 8  # top-8: com 5, normas-chave ficavam de fora no caso mais comum


def processar_ato_pronto(pipeline: Fase3Pipeline, pedido: PedidoBalcao, k: int = K_ATO_PRONTO) -> AtoProntoOutput:
    """Processa o pedido no pipeline da Fase 3 e gera o Ato Pronto estruturado."""
    t0 = time.perf_counter()

    # 1. Recuperação Híbrida especializada
    query = gerar_query_recuperacao(pedido)
    hits = pipeline.retrieve(query, k=k)
    logger.info("Ato Pronto %s · consulta expandida: %s", pedido.protocolo, query)
    logger.info("Ato Pronto %s · trechos recuperados (k=%d): %s", pedido.protocolo, k,
                "; ".join(rotulo_fonte(h) for h in hits) or "nenhum")

    if not hits:
        # Sem norma recuperada o LLM só poderia inventar: não chama o modelo
        saida = _ato_indefinido("contexto vazio")
        saida.latencia_s = round(time.perf_counter() - t0, 2)
        return saida

    contexto = "\n\n---\n\n".join(f"[{rotulo_fonte(h)}]\n{h['text']}" for h in hits)

    # 2. Prompt Estruturado
    prompt = build_ato_pronto_prompt(context=contexto, pedido=pedido)
    messages = [{"role": "user", "content": prompt}]

    from src.pipeline.routing import GROQ_MODEL_FALLBACKS
    model_name = GROQ_MODEL_FALLBACKS.get(pipeline.llm_model, pipeline.llm_model)

    api_kwargs: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.0,
    }


    try:
        # Tenta usar json_object se suportado pelo provedor
        try:
            api_kwargs["response_format"] = {"type": "json_object"}
            response = pipeline._call_chat_completions(**api_kwargs)
        except Exception:
            # Fallback sem response_format se der erro de parâmetro
            api_kwargs.pop("response_format", None)
            response = pipeline._call_chat_completions(**api_kwargs)

        conteudo_bruto = response.choices[0].message.content or "{}"
        dados = json.loads(_limpar_json(conteudo_bruto))
        # Converte o canal para maiúsculo se necessário
        if "canal" in dados and isinstance(dados["canal"], str):
            dados["canal"] = dados["canal"].upper()
        dados.pop("citacoes", None)  # a conferência é do sistema, nunca do LLM
        saida = AtoProntoOutput.model_validate(dados)
        texto_citado = "\n\n".join(
            [f"{f.norma} — {f.artigo}" for f in saida.fundamentacao] + [saida.instrucao_balcao, saida.minuta_ato])
        saida.citacoes = verificar(texto_citado, hits)
    except Exception as e:
        # Rede, JSON inválido ou schema inválido: nunca decide canal no escuro
        logger.exception("Falha ao gerar Ato Pronto (protocolo %s)", pedido.protocolo)
        saida = _ato_indefinido(type(e).__name__)

    saida.latencia_s = round(time.perf_counter() - t0, 2)
    saida.fontes_corpus = [
        f"{rotulo_fonte(h)} (pág. {h['page']})" for h in hits
    ]
    return saida
