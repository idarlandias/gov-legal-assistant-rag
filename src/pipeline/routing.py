"""Model routing cheap-first com fallback.

Reaproveita o notebook 05. Voce vai preencher 1 TODO aqui.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI
from src.pipeline.security_skill import get_env_secret


@dataclass(frozen=True)
class RouteDecision:
    model: str
    complexity: str  # "simple" | "complex"
    reason: str


# ------------------------------------------------------------------ TODO 6
def classify_complexity(query: str) -> RouteDecision:
    """Classifica complexidade da query para escolher modelo (cheap vs premium)."""
    cheap_model = os.environ.get("CHEAP_MODEL", "gemini-2.5-flash-lite")
    premium_model = os.environ.get("PREMIUM_MODEL", "gemini-2.5-pro")

    query_lower = query.lower()

    # Heurística de classificação de complexidade
    complex_words = ["explique", "compare", "analise", "projete", "detalhe", "diferença", "diferenca", "quais os casos", "como funciona", "interprete"]
    is_complex_by_keywords = any(word in query_lower for word in complex_words)
    is_complex_by_length = len(query) > 100

    if is_complex_by_keywords or is_complex_by_length:
        reason = "A consulta exige raciocínio complexo ou análise detalhada." if is_complex_by_keywords else "A consulta é longa e contextualizada."
        return RouteDecision(model=premium_model, complexity="complex", reason=reason)

    reason = "A consulta é curta e direta."
    return RouteDecision(model=cheap_model, complexity="simple", reason=reason)


def make_client() -> OpenAI:
    """Cliente OpenAI-compatible para o provider configurado."""
    try:
        gemini_key = get_env_secret("GEMINI_API_KEY")
        return OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    except RuntimeError:
        try:
            openai_key = get_env_secret("OPENAI_API_KEY")
            return OpenAI(api_key=openai_key)
        except RuntimeError:
            return OpenAI()
