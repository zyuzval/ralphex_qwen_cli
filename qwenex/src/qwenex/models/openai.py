"""OpenAI provider implementation."""

import json
from collections.abc import AsyncIterator
from typing import Any

from .base import ProviderConfig


class OpenAIProvider:
    """OpenAI API provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration

        """
        self.config = config
        self.base_url = config.base_url or "https://api.openai.com/v1"

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        """Get completion from OpenAI API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters (temperature, max_tokens)

        Returns:
            Generated text response

        """
        import aiohttp

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": False
        }

        timeout = aiohttp.ClientTimeout(total=self.config.timeout_sec)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream completion from OpenAI API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text

        """
        import aiohttp

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True
        }

        timeout = aiohttp.ClientTimeout(total=self.config.timeout_sec)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def check_health(self) -> bool:
        """Check if OpenAI API is accessible.

        Returns:
            True if API is accessible

        """
        import aiohttp

        url = f"{self.base_url}/models"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}"
        }

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False

    def get_config(self) -> ProviderConfig:
        """Get provider configuration.

        Returns:
            Provider configuration

        """
        return self.config
