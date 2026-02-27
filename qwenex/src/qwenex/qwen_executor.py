"""Execute tasks using LLM providers."""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional

from .models.base import LLMProvider, ProviderConfig
from .models.factory import ProviderFactory


class TaskTimeoutError(Exception):
    """Raised when a task exceeds the timeout."""
    pass


def parse_event(line: str) -> Dict[str, Any]:
    """Parse a stream-json event line.

    Args:
        line: JSON line from Qwen CLI

    Returns:
        Parsed event dictionary
    """
    return json.loads(line.strip())


class QwenExecutor:
    """Execute tasks using LLM providers."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        provider_config: Optional[ProviderConfig] = None,
        timeout_min: int = 10
    ):
        """Initialize executor.

        Args:
            provider: LLM provider instance (optional)
            provider_config: Provider configuration (creates provider)
            timeout_min: Timeout in minutes for each task
        """
        self.timeout_min = timeout_min
        
        if provider is not None:
            self.provider = provider
        elif provider_config is not None:
            self.provider = ProviderFactory.create(
                provider_config.name,
                provider_config
            )
        else:
            # Default to Qwen Cloud from environment
            self.provider, _ = ProviderFactory.create_from_env()

    async def run_task(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a task using the LLM provider.

        Args:
            prompt: Task prompt to execute
            system_prompt: Optional system prompt
            stream: Whether to stream response

        Yields:
            Events from the provider

        Raises:
            TaskTimeoutError: If task exceeds timeout
        """
        try:
            if stream:
                async for chunk in self.provider.stream(prompt, system_prompt):
                    yield {
                        "type": "chunk",
                        "content": chunk
                    }
            else:
                response = await asyncio.wait_for(
                    self.provider.complete(prompt, system_prompt),
                    timeout=self.timeout_min * 60
                )
                yield {
                    "type": "complete",
                    "content": response
                }
                
        except asyncio.TimeoutError:
            raise TaskTimeoutError(
                f"Task exceeded {self.timeout_min} minutes timeout"
            )
        except Exception as e:
            raise TaskTimeoutError(
                f"Task exceeded {self.timeout_min} minutes timeout: {e}"
            )
