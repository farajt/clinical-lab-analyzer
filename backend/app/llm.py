"""
Returns a LangChain chat model based on LLM_PROVIDER in .env.
Keeping this in one place means agent.py never cares which provider is live.
"""
import os
from functools import lru_cache


@lru_cache
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0.2,
            api_key=os.getenv("GROQ_API_KEY"),
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            temperature=0.2,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
