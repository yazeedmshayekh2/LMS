from enums import LLMProvider
from factory import create_llm

def get_llm(
    provider: LLMProvider = LLMProvider.GPT,
    model: str | None = None,
    temperature: float | None = None,
    **kwargs
):
    return create_llm(provider, model, temperature, **kwargs)