"""
LLM wrapper - handles all provider connections.
Supports Ollama, OpenAI, Anthropic, and Google.
"""

import time
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

try:
    from litellm import completion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    import requests

from config import (
    LLM_PROVIDER,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    GOOGLE_API_KEY, GOOGLE_MODEL,
    TEMPERATURE, MAX_TOKENS,
    RETRY_ATTEMPTS, RETRY_DELAY_BASE,
)

logger = logging.getLogger(__name__)


class Response(BaseModel):
    content: str
    provider: str
    model: str
    tokens: Optional[int] = None
    latency_ms: Optional[float] = None


def provider_info() -> Dict[str, Any]:
    """What provider/model we're using."""
    models = {
        "ollama": OLLAMA_MODEL,
        "openai": OPENAI_MODEL,
        "anthropic": ANTHROPIC_MODEL,
        "google": GOOGLE_MODEL,
    }
    return {
        "provider": LLM_PROVIDER,
        "model": models.get(LLM_PROVIDER, "unknown"),
        "litellm": HAS_LITELLM,
    }


def _model_name() -> str:
    """Convert to litellm format."""
    prefixes = {
        "ollama": "ollama",
        "openai": "openai",
        "anthropic": "anthropic",
        "google": "gemini",
    }
    models = {
        "ollama": OLLAMA_MODEL,
        "openai": OPENAI_MODEL,
        "anthropic": ANTHROPIC_MODEL,
        "google": GOOGLE_MODEL,
    }
    return f"{prefixes[LLM_PROVIDER]}/{models[LLM_PROVIDER]}"


def _ollama_direct(prompt: str, system: str = None) -> str:
    """Direct Ollama call (fallback)."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_predict": MAX_TOKENS,
        }
    }
    if system:
        payload["system"] = system

    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json().get("response", "")


def _call(messages: list[Dict[str, str]], use_litellm: bool = True) -> Response:
    """Make the actual API call with retries."""
    provider = LLM_PROVIDER
    models = {
        "ollama": OLLAMA_MODEL,
        "openai": OPENAI_MODEL,
        "anthropic": ANTHROPIC_MODEL,
        "google": GOOGLE_MODEL,
    }
    model = models.get(provider, "unknown")

    for attempt in range(RETRY_ATTEMPTS):
        try:
            start = time.time()

            if use_litellm and HAS_LITELLM:
                import os

                # set keys
                if provider == "openai":
                    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
                elif provider == "anthropic":
                    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
                elif provider == "google":
                    os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY

                resp = completion(
                    model=_model_name(),
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )

                content = resp.choices[0].message.content
                tokens = getattr(resp.usage, "total_tokens", None)

            else:
                # fallback to direct ollama
                if provider != "ollama":
                    raise ImportError(f"Need litellm for {provider}")

                system = None
                user = ""
                for m in messages:
                    if m["role"] == "system":
                        system = m["content"]
                    elif m["role"] == "user":
                        user = m["content"]

                content = _ollama_direct(user, system)
                tokens = None

            latency = (time.time() - start) * 1000

            return Response(
                content=content,
                provider=provider,
                model=model,
                tokens=tokens,
                latency_ms=latency,
            )

        except Exception as e:
            delay = RETRY_DELAY_BASE ** attempt
            logger.warning(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS} failed: {e}. Retry in {delay}s")
            time.sleep(delay)

    raise RuntimeError(f"All {RETRY_ATTEMPTS} attempts failed")


def complete(prompt: str, system: str = None, use_litellm: bool = True) -> Response:
    """
    Unified completion interface.

    prompt: user message
    system: system instructions
    use_litellm: whether to use litellm (falls back to direct)
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    return _call(messages, use_litellm)


def structured_complete(prompt: str, system: str = None, json_mode: bool = True) -> str:
    """
    Get a response, enforcing JSON format if needed.
    """
    if json_mode and system:
        system = system + "\n\nRespond with valid JSON only. No markdown, no extra text."

    return complete(prompt, system).content
