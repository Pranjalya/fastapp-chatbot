from typing import Optional
from langchain_openai import ChatOpenAI
from app.config import settings

def get_chat_model(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.2,
    streaming: bool = True
) -> ChatOpenAI:
    """
    Factory creating a ChatOpenAI client compatible with:
    - Google Gemini (via OpenAI compatibility endpoint)
    - NVIDIA NIM
    - OpenAI
    - Local vLLM / Ollama
    """
    selected_provider = (provider or settings.DEFAULT_PROVIDER).lower()
    
    if selected_provider == "gemini":
        endpoint = base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        selected_model = model_name or settings.DEFAULT_MODEL or "gemini-3.5-flash"
        key = api_key or settings.GEMINI_API_KEY or ""
    elif selected_provider == "nvidia":
        endpoint = base_url or "https://integrate.api.nvidia.com/v1"
        selected_model = model_name or "meta/llama-3.1-70b-instruct"
        key = api_key or settings.NVIDIA_NIM_KEY or ""
    elif selected_provider == "openai":
        endpoint = base_url or "https://api.openai.com/v1"
        selected_model = model_name or "gpt-4o-mini"
        key = api_key or settings.OPENAI_API_KEY or ""
    elif selected_provider == "local":
        endpoint = base_url or "http://localhost:11434/v1"
        selected_model = model_name or "llama3.1"
        key = api_key or "ollama"
    else:
        endpoint = base_url
        selected_model = model_name or "gpt-4o-mini"
        key = api_key or ""

    if not key and selected_provider != "local":
        raise ValueError(f"No API key configured for provider '{selected_provider}'. Please provide an API key in .env or Settings.")

    return ChatOpenAI(
        model=selected_model,
        api_key=key,
        base_url=endpoint,
        temperature=temperature,
        streaming=streaming,
        timeout=60,
        max_retries=3,
    )
