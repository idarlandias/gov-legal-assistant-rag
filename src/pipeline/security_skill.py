"""Módulo de segurança, secrets, prompt management e logging."""

from __future__ import annotations

import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("security_skill")

def get_env_secret(key_name: str) -> str:
    """Obtém um secret do ambiente de forma segura. Em produção, usa as variáveis da plataforma."""
    val = os.getenv(key_name)
    if not val:
        raise RuntimeError(f"Erro Crítico: Variável de ambiente '{key_name}' não configurada! Por favor, defina-a.")
    return val

def build_secure_prompt(context: str, query: str) -> str:
    """Monta o prompt seguro com ancoragem estrita e mitigação de injeção de prompt."""
    # Sanitização básica para evitar injeção simples
    sanitized_query = query.replace("CONTEXTO:", "").replace("PERGUNTA:", "").strip()
    
    return f"""Voce e um assistente tecnico. Responda APENAS com base no contexto abaixo.
Se a informacao nao estiver no contexto, diga "Nao encontrado no corpus".
Sempre cite a fonte usando o formato [arquivo:pagina].

CONTEXTO:
{context}

PERGUNTA: {sanitized_query}

RESPOSTA:"""

def log_query(dominio: str, query: str) -> None:
    """Registra logs estruturados sobre a consulta e o domínio selecionado."""
    logger.info(f"[Query Log] Domínio: {dominio} | Consulta: {query}")

def log_model_choice(model_choice: str) -> None:
    """Registra logs estruturados sobre o modelo de LLM escolhido (cheap vs premium)."""
    logger.info(f"[Model Routing Log] Modelo Escolhido: {model_choice}")
