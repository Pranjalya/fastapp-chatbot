from typing import Any, Dict, List
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/models", tags=["Models"])

@router.get("")
async def get_model_providers() -> Dict[str, Any]:
    """Return available LLM provider choices, presets, and server key availability."""
    return {
        "default_provider": settings.DEFAULT_PROVIDER,
        "default_model": settings.DEFAULT_MODEL,
        "default_n_turns": settings.DEFAULT_N_TURNS,
        "providers": [
            {
                "id": "gemini",
                "name": "Google Gemini",
                "default_model": "gemini-3.5-flash",
                "models": ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
                "has_server_key": bool(settings.GEMINI_API_KEY),
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            },
            {
                "id": "nvidia",
                "name": "NVIDIA NIM",
                "default_model": "meta/llama-3.1-70b-instruct",
                "models": [
                    "meta/llama-3.1-70b-instruct",
                    "meta/llama-3.1-8b-instruct",
                    "mistralai/mixtral-8x22b-instruct"
                ],
                "has_server_key": bool(settings.NVIDIA_NIM_KEY),
                "base_url": "https://integrate.api.nvidia.com/v1",
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "default_model": "gpt-4o-mini",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "has_server_key": bool(settings.OPENAI_API_KEY),
                "base_url": "https://api.openai.com/v1",
            },
            {
                "id": "local",
                "name": "Local / Ollama",
                "default_model": "llama3.1",
                "models": ["llama3.1", "mistral", "qwen2.5"],
                "has_server_key": True,
                "base_url": "http://localhost:11434/v1",
            }
        ]
    }
