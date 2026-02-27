"""Ollama MCP tools."""

from fastmcp import FastMCP

from ...models.base import ProviderConfig
from ...models.ollama import OllamaProvider


def register_ollama_tools(mcp: FastMCP) -> None:
    """Register Ollama tools with MCP server."""

    @mcp.tool()
    async def ollama_check(base_url: str = "http://localhost:11434") -> bool:
        """Check if Ollama server is available.

        Args:
            base_url: Ollama base URL

        Returns:
            True if Ollama is accessible

        """
        config = ProviderConfig(name="ollama", model="llama3.1:8b", base_url=base_url)
        provider = OllamaProvider(config)
        return await provider.check_health()

    @mcp.tool()
    async def ollama_list_models(base_url: str = "http://localhost:11434") -> list[dict]:
        """List available Ollama models.

        Args:
            base_url: Ollama base URL

        Returns:
            List of model dictionaries

        """
        import aiohttp

        url = f"{base_url}/api/tags"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                return []

    @mcp.tool()
    async def ollama_run(
        prompt: str,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434"
    ) -> str:
        """Run prompt through Ollama.

        Args:
            prompt: User prompt
            model: Model name
            base_url: Ollama base URL

        Returns:
            Model response

        """
        config = ProviderConfig(name="ollama", model=model, base_url=base_url)
        provider = OllamaProvider(config)
        return await provider.complete(prompt)
