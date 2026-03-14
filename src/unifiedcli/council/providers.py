"""LLM provider abstraction for the council."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM provider for council roles."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate a response from the LLM."""
        ...


class MockLLMProvider(LLMProvider):
    """Mock provider for testing."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = list(responses or ["Mock LLM response."])
        self._call_count = 0

    async def generate(self, prompt: str, system: str = "") -> str:
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]


class ClaudeProvider(LLMProvider):
    """Claude API provider (planner role)."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        messages = [{"role": "user", "content": prompt}]
        response = await client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system or "You are a planning agent in a multi-agent system.",
            messages=messages,
        )
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (balancer role)."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        return response.choices[0].message.content or ""


class GeminiProvider(LLMProvider):
    """Google Gemini API provider (critic role)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        from google import genai

        client = genai.Client(api_key=self._api_key)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = await client.aio.models.generate_content(
            model=self._model,
            contents=full_prompt,
        )
        return response.text or ""
