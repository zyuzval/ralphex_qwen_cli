"""Fallback provider for auto-switching between providers."""

from collections.abc import AsyncIterator
from typing import Any

from .base import ProviderConfig
from .ollama import OllamaProvider
from .qwen_cloud import QwenCloudProvider


class FallbackProvider:
    """Provider with automatic fallback.

    Tries primary provider first, falls back to secondary
    if primary is unavailable.
    """

    def __init__(
        self,
        primary_config: ProviderConfig,
        fallback_config: ProviderConfig,
    ):
        """Initialize fallback provider.

        Args:
            primary_config: Primary provider configuration
            fallback_config: Fallback provider configuration

        """
        self.primary_config = primary_config
        self.fallback_config = fallback_config

        # Create providers based on config
        from .factory import ProviderFactory

        try:
            self.primary = ProviderFactory.create(
                primary_config.name,
                primary_config
            )
        except ValueError:
            # If primary type unknown, use Ollama as default
            self.primary = OllamaProvider(primary_config)

        try:
            self.fallback = ProviderFactory.create(
                fallback_config.name,
                fallback_config
            )
        except ValueError:
            # If fallback type unknown, use Qwen Cloud as default
            self.fallback = QwenCloudProvider(fallback_config)

        self._use_fallback = False

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        """Get completion with automatic fallback.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Generated text response

        """
        if not self._use_fallback:
            # Check primary health
            try:
                healthy = await self.primary.check_health()
                if healthy:
                    return await self.primary.complete(
                        prompt, system_prompt, **kwargs
                    )
            except Exception:
                pass

            # Switch to fallback
            self._use_fallback = True

        # Use fallback provider
        return await self.fallback.complete(
            prompt, system_prompt, **kwargs
        )

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream completion with automatic fallback.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text

        """
        if not self._use_fallback:
            try:
                healthy = await self.primary.check_health()
                if healthy:
                    async for chunk in self.primary.stream(
                        prompt, system_prompt, **kwargs
                    ):
                        yield chunk
                    return
            except Exception:
                pass

            self._use_fallback = True

        async for chunk in self.fallback.stream(
            prompt, system_prompt, **kwargs
        ):
            yield chunk

    async def check_health(self) -> bool:
        """Check if either provider is available."""
        if not self._use_fallback:
            try:
                if await self.primary.check_health():
                    return True
            except Exception:
                pass
            self._use_fallback = True

        return await self.fallback.check_health()

    def get_config(self) -> ProviderConfig:
        """Get current provider configuration."""
        if self._use_fallback:
            return self.fallback_config
        return self.primary_config

    def reset(self) -> None:
        """Reset to primary provider."""
        self._use_fallback = False
