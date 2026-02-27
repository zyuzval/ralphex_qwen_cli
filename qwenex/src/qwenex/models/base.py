"""Base models and interfaces for LLM providers."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class Message:
    """Message for LLM communication."""

    role: str  # "user", "assistant", "system"
    content: str
    system_prompt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
    timeout_sec: int = 600
    extra: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        """Get completion from the provider.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        """
        ...

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream completion from the provider.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Yields:
            Chunks of generated text

        """
        ...

    async def check_health(self) -> bool:
        """Check if provider is available.

        Returns:
            True if provider is accessible

        """
        ...

    def get_config(self) -> ProviderConfig:
        """Get provider configuration.

        Returns:
            Provider configuration

        """
        ...
