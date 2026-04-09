from enum import Enum

class LLMProvider(str, Enum):
    GPT = 'gpt'
    GEMINI = 'gemini'
    CLAUDE = 'claude'
    GROQ = 'groq'
    OLLAMA = 'ollama'