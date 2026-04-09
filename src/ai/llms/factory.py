import logging
from functools import lru_cache
from langchain_core.language_models import BaseChatModel
from .enums import LLMProvider
from .config import PROVIDER_DEFAULTS

def create_llm(
    provider: LLMProvider,
    model:  str | None = None,
    temperature: float | None = None,
    **kwargs,
) -> BaseChatModel:
    
    defaults    = PROVIDER_DEFAULTS[provider]
    model       = model         or  defaults["model"]
    temperature = temperature   or  defaults["temperature"]

    match provider:
        case LLMProvider.GPT:
            try:
                from langchain_openai import ChatOpenAI
            except (ImportError, ModuleNotFoundError):
                    logging.error("Missing dependency: 'langchain-openai' is not installed.")
                    logging.info("Please install it using: pip install langchain-openai or uv add langchain-openai")

            llm = ChatOpenAI(
                model=model, temperature=temperature, **kwargs,
            )

            return llm
        
        case LLMProvider.GEMINI:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except (ImportError, ModuleNotFoundError):
                    logging.error("Missing dependency: 'langchain-google-genai' is not installed.")
                    logging.info("Please install it using: pip install langchain-google-genai or uv add langchain-google-genai")

            llm = ChatGoogleGenerativeAI(
                 model=model, temperature=temperature, **kwargs,
            )

            return llm
         
        case LLMProvider.CLAUDE:
            try:
                from langchain_anthropic import ChatAnthropic
            except (ImportError, ModuleNotFoundError):
                logging.error("Missing dependency: 'langchain-anthropic' is not installed.")
                logging.info("Please install it using: pip install langchain-anthropic or uv add langchain-anthropic")
            
            llm = ChatAnthropic(
                 model=model, temperature=temperature, **kwargs,
            )
            
            return llm
        
        case LLMProvider.GROQ:
            try:
                from langchain_groq import ChatGroq
            except (ImportError, ModuleNotFoundError):
                logging.error("Missing dependency: 'langchain-groq' is not installed.")
                logging.info("Please install it using: pip install langchain-groq or uv add langchain-groq")
            
            llm = ChatGroq(
                 model=model, temperature=temperature, **kwargs,
            )

            return llm

        case LLMProvider.OLLAMA:
            try:
                from langchain_ollama import ChatOllama
            except (ImportError, ModuleNotFoundError):
                logging.error("Missing dependency: 'langchain-ollama' is not installed.")
                logging.info("Please install it using: pip install langchain-ollama or uv add langchain-ollama")

            llm = ChatOllama(
                 model=model, temperature=temperature, **kwargs,
            )

            return llm
        
        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")