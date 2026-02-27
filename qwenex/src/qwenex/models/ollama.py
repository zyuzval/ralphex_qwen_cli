"""Ollama provider implementation for local models."""

import json
from typing import AsyncIterator, Any, Optional

from .base import LLMProvider, ProviderConfig


class OllamaProvider:
    """Ollama provider for local LLM execution."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Ollama provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Get completion from Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters (temperature, num_predict)
            
        Returns:
            Generated text response
        """
        import aiohttp
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048)
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_sec)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data["response"]
    
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream completion from Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        import aiohttp
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048)
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_sec)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                async for line in response.content:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        content = chunk.get("response", "")
                        if content:
                            yield content
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
    
    async def check_health(self) -> bool:
        """Check if Ollama server is accessible.
        
        Returns:
            True if Ollama is accessible
        """
        import aiohttp
        
        url = f"{self.base_url}/api/tags"
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def get_config(self) -> ProviderConfig:
        """Get provider configuration.
        
        Returns:
            Provider configuration
        """
        return self.config
