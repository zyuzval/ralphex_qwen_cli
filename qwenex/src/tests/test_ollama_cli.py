"""Tests for Ollama CLI command."""

import pytest
from unittest.mock import AsyncMock, patch
from qwenex.ollama_cli import ollama_entry_point, run_ollama_chat


@pytest.mark.asyncio
async def test_run_ollama_chat():
    """Test Ollama chat execution."""
    from qwenex.models.base import ProviderConfig
    from qwenex.models.ollama import OllamaProvider
    
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = OllamaProvider(config)
    
    with patch.object(provider, 'complete', new=AsyncMock(return_value="Response")):
        result = await run_ollama_chat(provider, "Test prompt")
        assert result == "Response"


def test_ollama_entry_point_help():
    """Test entry point with --help."""
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        with pytest.raises(SystemExit):
            ollama_entry_point(["--help"])
    finally:
        sys.stdout = old_stdout
