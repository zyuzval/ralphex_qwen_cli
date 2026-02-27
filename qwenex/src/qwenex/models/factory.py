"""Factory for creating LLM providers."""

import os
from enum import StrEnum

from .base import LLMProvider, ProviderConfig


class ProviderType(StrEnum):
    """Supported provider types."""

    QWEN_CLOUD = "qwen_cloud"
    OLLAMA = "ollama"
    OPENAI = "openai"


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, provider_type: ProviderType, provider_class: type[LLMProvider]) -> None:
        """Register a provider class.

        Args:
            provider_type: Provider type enum
            provider_class: Provider class

        """
        cls._providers[provider_type.value] = provider_class

    @classmethod
    def create(
        cls,
        provider_type: ProviderType | str,
        config: ProviderConfig
    ) -> LLMProvider:
        """Create a provider instance.

        Args:
            provider_type: Type of provider to create
            config: Provider configuration

        Returns:
            Configured provider instance

        Raises:
            ValueError: If provider type is unknown

        """
        if isinstance(provider_type, str):
            provider_type = ProviderType(provider_type)

        provider_class = cls._providers.get(provider_type.value)
        if provider_class is None:
            raise ValueError(f"Unknown provider type: {provider_type}")

        return provider_class(config)

    @classmethod
    def create_from_env(cls) -> tuple[LLMProvider, ProviderConfig]:
        """Create provider from environment variables.

        Environment variables:
            QWENEX_PROVIDER: Provider type (qwen_cloud, ollama, openai)
            QWENEX_MODEL: Model name
            QWENEX_API_KEY: API key (optional)
            QWENEX_BASE_URL: Base URL (optional)
            QWENEX_TIMEOUT: Timeout in seconds (optional)

        Returns:
            Tuple of (provider, config)

        """
        provider_type = os.getenv("QWENEX_PROVIDER", "qwen_cloud")
        model = os.getenv("QWENEX_MODEL", "qwen-max")
        api_key = os.getenv("QWENEX_API_KEY")
        base_url = os.getenv("QWENEX_BASE_URL")
        timeout = int(os.getenv("QWENEX_TIMEOUT", "600"))

        config = ProviderConfig(
            name=provider_type,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_sec=timeout
        )

        provider = cls.create(provider_type, config)
        return provider, config


# Register providers
def _register_providers() -> None:
    """Register all available providers."""
    from .ollama import OllamaProvider
    from .openai import OpenAIProvider
    from .qwen_cloud import QwenCloudProvider

    ProviderFactory.register(ProviderType.QWEN_CLOUD, QwenCloudProvider)
    ProviderFactory.register(ProviderType.OLLAMA, OllamaProvider)
    ProviderFactory.register(ProviderType.OPENAI, OpenAIProvider)


_register_providers()
