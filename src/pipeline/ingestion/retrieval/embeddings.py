from __future__ import annotations

from langchain_core.embeddings import Embeddings

EMBEDDING_DEFAULTS: dict[str, str] = {
    "openai": "text-embedding-3-small",
    "gpt": "text-embedding-3-small",
    "gemini": "models/gemini-embedding-001",
    "google": "models/gemini-embedding-001",
    "ollama": "nomic-embed-text",
    "fake": "deterministic",
}


def create_embeddings(
    provider: str,
    *,
    model: str | None = None,
) -> Embeddings:
    """Build a LangChain embeddings model for dense retrieval."""
    key = provider.lower().strip()
    model_name = model or EMBEDDING_DEFAULTS.get(key, EMBEDDING_DEFAULTS["openai"])

    match key:
        case "fake" | "deterministic":
            from langchain_core.embeddings import DeterministicFakeEmbedding

            size = 384 if model_name == "deterministic" else int(model_name)
            return DeterministicFakeEmbedding(size=size)
        case "openai" | "gpt":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model=model_name)
        case "gemini" | "google":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            return GoogleGenerativeAIEmbeddings(model=model_name)
        case "ollama":
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings(model=model_name)
        case _:
            msg = f"Unsupported embedding provider: {provider}"
            raise ValueError(msg)
