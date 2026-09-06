"""
LLM configuration for HomeRepair AI Agent.

Reads OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
exclusively from environment variables loaded via python-dotenv.

NO keys or model names are hardcoded here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded reliably from the backend directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def get_llm():
    """
    Return a configured ChatOpenAI instance pointing to OpenRouter.
    Raises ValueError if OPENROUTER_API_KEY is not set.
    """
    from langchain_openai import ChatOpenAI

    # Reload variables to ensure any dynamic changes to .env are picked up
    load_dotenv(dotenv_path=env_path, override=True)

    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("OPENROUTER_MODEL")

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )
    if not model:
        raise ValueError(
            "OPENROUTER_MODEL environment variable is not set. "
            "Please add it to your .env file."
        )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.2,          # Lower temperature for analytical tasks
        max_tokens=2048,
        request_timeout=30.0,
        default_headers={
            "HTTP-Referer": "https://homerepair-ai.local",
            "X-Title": "HomeRepair AI",
        },
    )
