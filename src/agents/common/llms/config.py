from .enums import LLMProvider

PROVIDER_DEFAULTS = {
    LLMProvider.GPT:    {"model": 'gpt-5.4',                    "temperature": 0},
    LLMProvider.GEMINI: {"model": 'gemini-2.5-flash',             "temperature": 0.7},
    LLMProvider.CLAUDE: {"model": 'claude-sonnet-4-6',          "temperature": 0.7},
    LLMProvider.GROQ:   {"model": "llama-3.3-70b-versatile",    "temperature": 0},
    LLMProvider.OLLAMA: {"model": "llama3.2",                   "temperature": 0},
}