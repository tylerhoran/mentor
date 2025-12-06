"""
Abstraction over different LLM providers.

Supports:
- Ollama (local)
- Together.ai
- OpenRouter
- Anthropic (Claude)
- OpenAI

Features:
- Streaming responses
- Token counting
- Adapter loading for fine-tuned models
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

import httpx
import structlog

from mentor.config import settings

logger = structlog.get_logger()


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate a response from the LLM.

        Args:
            messages: Conversation history as list of {role, content} dicts
            system_prompt: System prompt to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Complete response string or async generator of chunks
        """
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name."""
        pass


class OllamaClient(LLMClient):
    """LLM client for Ollama (local models)."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        adapter_path: str | None = None,
    ):
        """
        Initialize Ollama client.

        Args:
            model: Model name (e.g., "llama3.1:8b")
            base_url: Ollama server URL
            adapter_path: Path to LoRA adapter (if fine-tuned)
        """
        self.model = model or settings.ollama_default_model
        self.base_url = base_url or settings.ollama_base_url
        self.adapter_path = adapter_path
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=120.0,
            )
        return self._client

    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Generate response using Ollama."""
        client = self._get_client()

        # Format messages with system prompt
        formatted_messages = [{"role": "system", "content": system_prompt}]
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": stream,
        }

        if stream:
            return self._stream_response(client, payload)
        else:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def _stream_response(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        import json

        async with client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]

    async def count_tokens(self, text: str) -> int:
        """Estimate token count (Ollama doesn't provide exact counts)."""
        # Rough estimate: ~4 characters per token for English
        return len(text) // 4

    @property
    def model_name(self) -> str:
        return self.model

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class TogetherClient(LLMClient):
    """LLM client for Together.ai."""

    def __init__(
        self,
        model: str = "meta-llama/Llama-3.1-8B-Instruct",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or settings.together_api_key
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.together.xyz/v1",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0,
            )
        return self._client

    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Generate response using Together.ai."""
        client = self._get_client()

        formatted_messages = [{"role": "system", "content": system_prompt}]
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._stream_response(client, payload)
        else:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _stream_response(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        import json

        async with client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    data = json.loads(data_str)
                    if data["choices"][0].get("delta", {}).get("content"):
                        yield data["choices"][0]["delta"]["content"]

    async def count_tokens(self, text: str) -> int:
        """Estimate token count."""
        try:
            import tiktoken

            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            return len(text) // 4

    @property
    def model_name(self) -> str:
        return self.model


class AnthropicClient(LLMClient):
    """LLM client for Anthropic (Claude)."""

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or settings.anthropic_api_key
        self._client = None

    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Generate response using Anthropic API."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

        client = AsyncAnthropic(api_key=self.api_key)

        # Convert message format
        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
            )

        if stream:
            return self._stream_response(
                client, anthropic_messages, system_prompt, temperature, max_tokens
            )
        else:
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=anthropic_messages,
                temperature=temperature,
            )
            return response.content[0].text

    async def _stream_response(
        self,
        client: Any,
        messages: list[dict],
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        async with client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def count_tokens(self, text: str) -> int:
        """Count tokens using Anthropic's tokenizer."""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self.api_key)
            # Anthropic doesn't have a public token counting API
            # Use tiktoken as approximation
            import tiktoken

            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            return len(text) // 4

    @property
    def model_name(self) -> str:
        return self.model


class OpenAIClient(LLMClient):
    """LLM client for OpenAI."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or settings.openai_api_key
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        return self._client

    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Generate response using OpenAI API."""
        client = self._get_client()

        formatted_messages = [{"role": "system", "content": system_prompt}]
        formatted_messages.extend(messages)

        if stream:
            return self._stream_response(client, formatted_messages, temperature, max_tokens)
        else:
            response = await client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

    async def _stream_response(
        self,
        client: Any,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4

    @property
    def model_name(self) -> str:
        return self.model


def get_llm_client(
    provider: str | None = None,
    model: str | None = None,
    **kwargs: Any,
) -> LLMClient:
    """
    Factory function to get an LLM client.

    Args:
        provider: LLM provider ('ollama', 'together', 'anthropic', 'openai')
        model: Model name (provider-specific)
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLMClient instance
    """
    provider = provider or settings.llm_provider

    if provider == "ollama":
        return OllamaClient(model=model, **kwargs)
    elif provider == "together":
        return TogetherClient(model=model or "meta-llama/Llama-3.1-8B-Instruct", **kwargs)
    elif provider == "anthropic":
        return AnthropicClient(model=model or "claude-3-haiku-20240307", **kwargs)
    elif provider == "openai":
        return OpenAIClient(model=model or "gpt-4o-mini", **kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
