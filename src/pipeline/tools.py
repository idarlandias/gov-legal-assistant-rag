"""Function-calling / tool-use — registro de tools usadas pelo agente.

Reaproveita o LAB-001. Contém as ferramentas de domínio para o Assistente Jurídico RAG.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from typing import Any, Callable

# ============================================================================
# Ferramentas do domínio do Assistente Jurídico RAG
# ============================================================================

def cite_lgpd_article(numero_artigo: int) -> str:
    """Busca o texto integral de um artigo específico da LGPD no banco ChromaDB."""
    import chromadb
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    import os

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    embed_fn = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=os.environ.get("EMBED_MODEL", "gemini-embedding-001"),
        api_base="https://generativelanguage.googleapis.com/v1beta/openai/" if "GEMINI_API_KEY" in os.environ else None
    )
    chroma = chromadb.PersistentClient(path="data/chroma")
    collection = chroma.get_or_create_collection("docs", embedding_function=embed_fn)

    res = collection.query(
        query_texts=[f"Art. {numero_artigo}", f"Artigo {numero_artigo}"],
        n_results=3,
        where={"dominio": "lgpd"}
    )
    if res and res.get("documents") and res["documents"][0]:
        pattern = re.compile(rf"\b(Art\.|Artigo)\s*{numero_artigo}\b", re.IGNORECASE)
        for doc in res["documents"][0]:
            if pattern.search(doc):
                return doc
        return res["documents"][0][0]
    return f"Artigo {numero_artigo} não encontrado na LGPD."


def cite_14133_article(numero_artigo: int) -> str:
    """Busca o texto integral de um artigo específico da Lei 14.133 no banco ChromaDB."""
    import chromadb
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    import os

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    embed_fn = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=os.environ.get("EMBED_MODEL", "gemini-embedding-001"),
        api_base="https://generativelanguage.googleapis.com/v1beta/openai/" if "GEMINI_API_KEY" in os.environ else None
    )
    chroma = chromadb.PersistentClient(path="data/chroma")
    collection = chroma.get_or_create_collection("docs", embedding_function=embed_fn)

    res = collection.query(
        query_texts=[f"Art. {numero_artigo}", f"Artigo {numero_artigo}"],
        n_results=3,
        where={"dominio": "licitacoes"}
    )
    if res and res.get("documents") and res["documents"][0]:
        pattern = re.compile(rf"\b(Art\.|Artigo)\s*{numero_artigo}\b", re.IGNORECASE)
        for doc in res["documents"][0]:
            if pattern.search(doc):
                return doc
        return res["documents"][0][0]
    return f"Artigo {numero_artigo} não encontrado na Lei 14.133."


def cite_ctb_article(numero_artigo: int | str) -> str:
    """Busca o texto integral de um artigo específico do Código de Trânsito Brasileiro (CTB) diretamente do arquivo de texto para evitar fragmentação e alucinações."""
    import re
    from pathlib import Path
    
    file_path = Path("data/corpus/ctb/CTB_compilado.txt")
    if not file_path.exists():
        # Fallback para caminho absoluto se o relativo falhar
        file_path = Path(__file__).resolve().parents[2] / "data" / "corpus" / "ctb" / "CTB_compilado.txt"
        
    if not file_path.exists():
        return f"Arquivo do CTB não encontrado localmente para extrair o Artigo {numero_artigo}."
        
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Erro ao ler o arquivo do CTB: {e}"
        
    # Regex para localizar: Art. <numero_artigo> (ex: Art. 20.)
    pattern = re.compile(rf"\b(Art\.|Artigo)\s*{numero_artigo}\b", re.IGNORECASE)
    match = pattern.search(content)
    if not match:
        return f"Artigo {numero_artigo} não encontrado no Código de Trânsito Brasileiro."
        
    start_pos = match.start()
    
    # Encontra o início do próximo artigo (Art. <qualquer_numero>) para definir o fim deste artigo
    # Usa re.MULTILINE e ^ para garantir que só casa no início da linha (evitando referências no meio de incisos)
    next_pattern = re.compile(r"^\s*(?:Art\.|Artigo)\s*\d+", re.MULTILINE | re.IGNORECASE)
    next_match = None
    for m in next_pattern.finditer(content, pos=start_pos + 10):
        next_match = m
        break
        
    if next_match:
        end_pos = next_match.start()
        article_text = content[start_pos:end_pos].strip()
    else:
        article_text = content[start_pos:].strip()
        
    return article_text


def simular_enquadramento(valor: float, objeto: str) -> str:
    """Simula se uma contratação pública enquadra-se em dispensa por valor ou exige licitação."""
    objeto_lower = objeto.lower()
    
    # Determina se é obra/engenharia ou serviço de veículo automotor
    is_engineering_or_vehicle = any(word in objeto_lower for word in ["engenharia", "obra", "reforma", "veículo", "veiculo"])
    
    if is_engineering_or_vehicle:
        limit = 119812.02
        tipo = "obras, serviços de engenharia ou manutenção de veículos"
    else:
        limit = 59906.02
        tipo = "outras compras e serviços comuns"
        
    if valor <= limit:
        result = {
            "valor_estimado": valor,
            "tipo_objeto": tipo,
            "modalidade_provavel": "Dispensa de Licitação por Valor",
            "fundamento_legal": "Art. 75, I" if is_engineering_or_vehicle else "Art. 75, II",
            "observacao": f"O valor estimado de R$ {valor:,.2f} está abaixo do limite de R$ {limit:,.2f} para {tipo}."
        }
    else:
        result = {
            "valor_estimado": valor,
            "tipo_objeto": tipo,
            "modalidade_provavel": "Licitação Obrigatória (Pregão, Concorrência ou Diálogo Competitivo)",
            "fundamento_legal": "Art. 75, I e II a contrario sensu",
            "observacao": f"O valor estimado de R$ {valor:,.2f} supera o limite de R$ {limit:,.2f} para dispensa por valor. Licitação necessária."
        }
    return json.dumps(result, ensure_ascii=False)


def build_transparency_link(municipio: str, ano: int, funcao: str) -> str:
    """Constrói o link direto para a consulta de despesas públicas filtrando por município, ano e função."""
    municipio_clean = municipio.strip().lower()
    funcao_clean = funcao.strip().lower()
    
    # Mapeamento de funções orçamentárias brasileiras
    funcoes_map = {
        "saude": "10",
        "saúde": "10",
        "educacao": "12",
        "educação": "12",
        "seguranca": "06",
        "segurança": "06",
        "administracao": "04",
        "administração": "04",
        "assistência": "08",
        "assistencia": "08",
        "urbanismo": "15",
        "transporte": "26",
    }
    
    code = funcoes_map.get(funcao_clean, "")
    
    if municipio_clean in ["brasil", "federal", "uniao", "união"]:
        url = "https://transparencia.gov.br/despesas/recursos-recebidos"
        params = {"ano": ano}
        if code:
            params["funcao"] = code
        return f"{url}?{urllib.parse.urlencode(params)}"
    else:
        url = f"https://portaldatransparencia.{municipio_clean}.gov.br/despesas"
        params = {"ano": ano}
        if code:
            params["funcao"] = code
        return f"{url}?{urllib.parse.urlencode(params)}"


def listar_documentos(servico: str) -> str:
    """Retorna checklist de documentos necessários para um serviço público específico (cartório, prefeitura, INSS simulado),
    extraído de manuais do domínio 'procedimentos' via LLM (Gemini Flash-Lite).
    """
    import chromadb
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    import os
    import json
    from openai import OpenAI
    from src.pipeline.security_skill import get_env_secret

    # 1. Obter API Key de forma segura
    try:
        api_key = get_env_secret("GEMINI_API_KEY")
    except RuntimeError:
        try:
            api_key = get_env_secret("OPENAI_API_KEY")
        except RuntimeError:
            api_key = None

    if not api_key:
        return "[]"

    # 2. Configurar embeddings e consultar o ChromaDB no domínio 'procedimentos'
    embed_fn = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=os.environ.get("EMBED_MODEL", "gemini-embedding-001"),
        api_base="https://generativelanguage.googleapis.com/v1beta/openai/" if "GEMINI_API_KEY" in os.environ else None
    )
    chroma = chromadb.PersistentClient(path="data/chroma")
    collection = chroma.get_or_create_collection("docs", embedding_function=embed_fn)

    res = collection.query(
        query_texts=[servico],
        n_results=4,
        where={"dominio": "procedimentos"}
    )
    
    if not res or not res.get("documents") or not res["documents"][0]:
        return "[]"

    context = "\n\n---\n\n".join(doc for doc in res["documents"][0])

    # 3. Prompt de extração estruturada via LLM
    prompt = (
        "Você é um assistente que extrai requisitos de documentos a partir de manuais "
        "de serviços públicos (INSS, prefeituras, cartórios).\n\n"
        "Leia o texto abaixo e devolva APENAS um JSON válido contendo uma lista de objetos, no seguinte formato:\n"
        "[\n"
        "  {\"documento\": \"RG ou CNH\", \"obrigatorio\": true},\n"
        "  {\"documento\": \"Comprovante de residência\", \"obrigatorio\": true},\n"
        "  {\"documento\": \"Laudo médico recente\", \"obrigatorio\": false}\n"
        "]\n\n"
        "Considere 'obrigatorio': true para documentos explicitamente exigidos, "
        "e false para documentos opcionais ou situacionais.\n"
        "Se o texto não trouxer nenhum documento claro, devolva [].\n"
        "Não adicione nenhuma introdução, explicação ou formatação markdown (como ```json ou ```). Apenas o JSON puro.\n\n"
        f"TEXTO DO MANUAL:\n{context}\n"
    )

    # 4. Inicializar cliente OpenAI e fazer a chamada para o Gemini Flash-Lite
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/" if "GEMINI_API_KEY" in os.environ else None,
    )
    
    model_name = os.environ.get("LLM_MODEL", "gemini-2.5-flash-lite")
    if "GEMINI_API_KEY" not in os.environ:
        model_name = "gpt-4o-mini"

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip()
        
        # Limpa blocos de código se o modelo ignorar a instrução
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        checklist = json.loads(raw)
        if isinstance(checklist, list):
            return json.dumps(checklist, ensure_ascii=False)
        return "[]"
    except Exception:
        # Fallback defensivo em caso de erro de parsing ou timeout da API
        return "[]"


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "cite_lgpd_article",
            "description": "Retorna o texto integral de um artigo específico da LGPD (Lei 13.709/2018) para evitar alucinações.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_artigo": {
                        "type": "integer",
                        "description": "O número do artigo da LGPD que se deseja citar (ex: 7, 23, 26)."
                    }
                },
                "required": ["numero_artigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cite_14133_article",
            "description": "Retorna o texto integral de um artigo específico da Nova Lei de Licitações (Lei 14.133/2021) para evitar alucinações.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_artigo": {
                        "type": "integer",
                        "description": "O número do artigo da Lei 14.133 que se deseja citar (ex: 75, 11, 28)."
                    }
                },
                "required": ["numero_artigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simular_enquadramento",
            "description": "Simula o enquadramento provável de uma contratação na Lei 14.133/2021 (ex: dispensa por valor vs licitação obrigatória).",
            "parameters": {
                "type": "object",
                "properties": {
                    "valor": {
                        "type": "number",
                        "description": "O valor estimado da contratação pública em Reais (BRL)."
                    },
                    "objeto": {
                        "type": "string",
                        "description": "Descrição sucinta do objeto da contratação (ex: 'compra de resmas de papel', 'reforma do gabinete')."
                    }
                },
                "required": ["valor", "objeto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "build_transparency_link",
            "description": "Constrói o link direto para a página de consultas de despesas do Portal da Transparência com filtros de ano e área.",
            "parameters": {
                "type": "object",
                "properties": {
                    "municipio": {
                        "type": "string",
                        "description": "O nome do município de interesse, ou 'brasil'/'federal' para o Portal da Transparência da União."
                    },
                    "ano": {
                        "type": "integer",
                        "description": "O ano dos dados a serem pesquisados (ex: 2024)."
                    },
                    "funcao": {
                        "type": "string",
                        "description": "A área de governo de interesse (ex: 'saude', 'educacao', 'seguranca')."
                    }
                },
                "required": ["municipio", "ano", "funcao"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_documentos",
            "description": "Retorna checklist de documentos necessários para um serviço público específico (cartório, prefeitura, INSS simulado).",
            "parameters": {
                "type": "object",
                "properties": {
                    "servico": {
                        "type": "string",
                        "description": "Nome do serviço, ex.: 'auxílio-doença', 'alvará de funcionamento', '2a via de certidão de nascimento'."
                    }
                },
                "required": ["servico"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cite_ctb_article",
            "description": "Retorna o texto integral de um artigo específico do Código de Trânsito Brasileiro (CTB) para responder com todas as competências sem fragmentação.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_artigo": {
                        "type": "integer",
                        "description": "O número do artigo do CTB que se deseja citar (ex: 20, 24, 29)."
                    }
                },
                "required": ["numero_artigo"]
            }
        }
    }
]

TOOL_REGISTRY: dict[str, Callable[..., str]] = {
    "cite_lgpd_article": cite_lgpd_article,
    "cite_14133_article": cite_14133_article,
    "cite_ctb_article": cite_ctb_article,
    "simular_enquadramento": simular_enquadramento,
    "build_transparency_link": build_transparency_link,
    "listar_documentos": listar_documentos,
}


def run_tool_call(name: str, arguments_json: str) -> str:
    """Executa uma tool call e retorna o resultado como string."""
    if name not in TOOL_REGISTRY:
        return f"ERROR: tool '{name}' nao registrada"
    try:
        kwargs = json.loads(arguments_json)
        return TOOL_REGISTRY[name](**kwargs)
    except Exception as e:
        return f"ERROR ao executar {name}: {e}"
