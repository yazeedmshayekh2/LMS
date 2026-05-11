from __future__ import annotations

import logging
import os
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai.llms.enums import LLMProvider
from ai.llms.factory import create_llm
from pipeline.ingestion.normalize.models import NormalizeBatch
from pipeline.ingestion.normalize.prompts import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^```(?:markdown|md)?\s*|\s*```$", re.MULTILINE)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = _FENCE_RE.sub("", stripped).strip()
    return stripped


def provider_from_name(name: str) -> LLMProvider:
    normalized = name.strip().lower()
    mapping = {
        "gpt": LLMProvider.GPT,
        "openai": LLMProvider.GPT,
        "gemini": LLMProvider.GEMINI,
        "google": LLMProvider.GEMINI,
        "claude": LLMProvider.CLAUDE,
        "anthropic": LLMProvider.CLAUDE,
        "groq": LLMProvider.GROQ,
        "ollama": LLMProvider.OLLAMA,
    }
    try:
        return mapping[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported provider: {name}") from exc


def create_normalizer_llm(
    provider_name: str,
    *,
    model: str | None = None,
    temperature: float = 0.0,
) -> tuple[BaseChatModel, LLMProvider, str]:
    provider = provider_from_name(provider_name)
    llm = create_llm(provider, model=model, temperature=temperature)
    resolved_model = model or llm.model_name if hasattr(llm, "model_name") else model or provider.value
    return llm, provider, str(resolved_model)


def normalize_batch_markdown(
    llm: BaseChatModel,
    batch: NormalizeBatch,
) -> str:
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(batch)
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    content = getattr(response, "content", response)
    if isinstance(content, list):
        text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        content = "\n".join(text_parts)
    return _strip_code_fence(str(content))


def provider_is_configured(provider: LLMProvider) -> bool:
    env_keys = {
        LLMProvider.GPT: ("OPENAI_API_KEY",),
        LLMProvider.GEMINI: ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        LLMProvider.CLAUDE: ("ANTHROPIC_API_KEY",),
        LLMProvider.GROQ: ("GROQ_API_KEY",),
        LLMProvider.OLLAMA: ("OLLAMA_HOST",),
    }
    keys = env_keys.get(provider, ())
    if provider == LLMProvider.OLLAMA:
        return True
    return any(os.getenv(key) for key in keys)
