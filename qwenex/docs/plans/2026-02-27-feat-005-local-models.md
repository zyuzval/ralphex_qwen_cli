# FEAT-005: Локальные модели Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Интеграция Ollama для локального выполнения моделей — CLI команда, проверка доступности, автофоллбэк.

**Architecture:** OllamaProvider уже реализован в PROP-001. Добавляем CLI команду `qwenex-ollama` для прямого взаимодействия, health check при старте, автофоллбэк на Qwen Cloud если Ollama недоступен.

**Tech Stack:** Python 3.11+ · aiohttp · argparse · Ollama API (/api/tags, /api/generate)

---

### Task 1: Ollama CLI команда

**Files:**
- Create: `src/qwenex/ollama_cli.py`
- Test: `src/tests/test_ollama_cli.py`

**Step 1: Write the failing test**

```python
# src/tests/test_ollama_cli.py
"""Tests for Ollama CLI command."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_ollama_cli.py -v --no-cov`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.ollama_cli'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/ollama_cli.py
"""CLI for Ollama local models."""

import argparse
import asyncio
import sys
from typing import Optional

from .models.base import ProviderConfig
from .models.ollama import OllamaProvider
from .models.factory import ProviderFactory, ProviderType


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="qwenex-ollama",
        description="Chat with Ollama local models"
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt to send (interactive mode if not provided)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.1:8b",
        help="Model name (default: llama3.1:8b)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama base URL"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available models"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check Ollama availability"
    )
    
    return parser.parse_args(args)


async def run_ollama_chat(
    provider: OllamaProvider,
    prompt: str,
) -> str:
    """Run chat with Ollama provider.
    
    Args:
        provider: Ollama provider instance
        prompt: User prompt
        
    Returns:
        Model response
    """
    return await provider.complete(prompt)


async def list_models(provider: OllamaProvider) -> None:
    """List available Ollama models."""
    import aiohttp
    
    url = f"{provider.base_url}/api/tags"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                models = data.get("models", [])
                print(f"Available models ({len(models)}):")
                for model in models:
                    name = model.get("name", "unknown")
                    size = model.get("size", 0) / (1024**3)  # GB
                    print(f"  - {name} ({size:.1f} GB)")
            else:
                print(f"Error: {response.status}")


async def check_health(provider: OllamaProvider) -> bool:
    """Check Ollama availability."""
    healthy = await provider.check_health()
    if healthy:
        print(f"✅ Ollama is available at {provider.base_url}")
    else:
        print(f"❌ Ollama is not available at {provider.base_url}")
        print("   Make sure Ollama is running: ollama serve")
    return healthy


async def async_main(args: argparse.Namespace) -> int:
    """Async main function."""
    config = ProviderConfig(
        name="ollama",
        model=args.model,
        base_url=args.base_url
    )
    provider = OllamaProvider(config)
    
    if args.check:
        healthy = await check_health(provider)
        return 0 if healthy else 1
    
    if args.list:
        await list_models(provider)
        return 0
    
    if args.prompt:
        # Single prompt mode
        response = await run_ollama_chat(provider, args.prompt)
        print(response)
        return 0
    
    # Interactive mode
    print(f"Ollama Chat ({args.model})")
    print("Type 'quit' or 'exit' to stop\n")
    
    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in ("quit", "exit"):
                break
            if not user_input:
                continue
            
            response = await run_ollama_chat(provider, user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break
    
    return 0


def ollama_entry_point(args: Optional[list] = None) -> None:
    """Console script entry point."""
    parsed_args = parse_args(args)
    exit_code = asyncio.run(async_main(parsed_args))
    sys.exit(exit_code)


if __name__ == "__main__":
    ollama_entry_point()
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_ollama_cli.py::test_run_ollama_chat -v --no-cov`
Expected: PASS

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/ollama_cli.py src/tests/test_ollama_cli.py
git commit -m "feat(FEAT-005-1): add Ollama CLI command

- qwenex-ollama entry point for local models
- Interactive and single-prompt modes
- --list to show available models
- --check to verify Ollama availability
- Tests: 2 passing"
```

---

### Task 2: Интеграция в pyproject.toml

**Files:**
- Modify: `pyproject.toml`

**Step 1: Modify pyproject.toml**

```toml
# Add to [project.scripts]
qwenex-ollama = "qwenex.ollama_cli:ollama_entry_point"
```

**Step 2: Reinstall package**

Run: `cd qwenex && pip install -e .`
Expected: Package installed with new entry point

**Step 3: Verify entry point**

Run: `qwenex-ollama --help`
Expected: Help message displayed

**Step 4: Commit**

```bash
cd qwenex
git add pyproject.toml
git commit -m "feat(FEAT-005-2): add qwenex-ollama entry point

- Register CLI command in pyproject.toml
- Reinstall package to activate"
```

---

### Task 3: Автофоллбэк на Qwen Cloud

**Files:**
- Create: `src/qwenex/models/fallback.py`
- Test: `src/tests/test_models_fallback.py`

**Step 1: Write the failing test**

```python
# src/tests/test_models_fallback.py
"""Tests for fallback provider."""

import pytest
from unittest.mock import AsyncMock, patch
from qwenex.models.fallback import FallbackProvider
from qwenex.models.base import ProviderConfig
from qwenex.models.ollama import OllamaProvider
from qwenex.models.qwen_cloud import QwenCloudProvider


@pytest.mark.asyncio
async def test_fallback_primary_available():
    """Test fallback uses primary when available."""
    primary_config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    fallback_config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    
    fallback = FallbackProvider(primary_config, fallback_config)
    
    # Mock primary health check to succeed
    with patch.object(fallback.primary, 'check_health', new=AsyncMock(return_value=True)):
        with patch.object(fallback.primary, 'complete', new=AsyncMock(return_value="Primary")):
            result = await fallback.complete("Test")
            assert result == "Primary"


@pytest.mark.asyncio
async def test_fallback_primary_unavailable():
    """Test fallback uses secondary when primary fails."""
    primary_config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    fallback_config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    
    fallback = FallbackProvider(primary_config, fallback_config)
    
    # Mock primary health check to fail
    with patch.object(fallback.primary, 'check_health', new=AsyncMock(return_value=False)):
        with patch.object(fallback.fallback, 'complete', new=AsyncMock(return_value="Fallback")):
            result = await fallback.complete("Test")
            assert result == "Fallback"


@pytest.mark.asyncio
async def test_fallback_health_check():
    """Test fallback health check."""
    primary_config = ProviderConfig(name="ollama", model="llama3.1:8b")
    fallback_config = ProviderConfig(name="qwen_cloud", model="qwen-max", api_key="key")
    
    fallback = FallbackProvider(primary_config, fallback_config)
    
    with patch.object(fallback.primary, 'check_health', new=AsyncMock(return_value=False)):
        with patch.object(fallback.fallback, 'check_health', new=AsyncMock(return_value=True)):
            result = await fallback.check_health()
            assert result is True
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_models_fallback.py -v --no-cov`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/qwenex/models/fallback.py
"""Fallback provider for auto-switching between providers."""

from typing import Any, Optional, AsyncIterator

from .base import LLMProvider, ProviderConfig
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
        system_prompt: Optional[str] = None,
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
        system_prompt: Optional[str] = None,
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
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_models_fallback.py -v --no-cov`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/models/fallback.py src/tests/test_models_fallback.py
git commit -m "feat(FEAT-005-3): add FallbackProvider

- Automatic fallback from primary to secondary provider
- Health check before each request
- Stream and complete support
- Manual reset to retry primary
- Tests: 3 passing"
```

---

### Task 4: Интеграция FallbackProvider в CLI

**Files:**
- Modify: `src/qwenex/cli.py`
- Test: Modify `src/tests/test_cli.py`

**Step 1: Add --fallback option**

```python
# src/qwenex/cli.py - add argument
parser.add_argument(
    "--fallback",
    type=str,
    default=None,
    help="Fallback provider (e.g., qwen_cloud when using ollama)"
)
```

**Step 2: Update provider creation logic**

```python
# src/qwenex/cli.py - update main()
from .models.fallback import FallbackProvider

# Create provider configuration
provider_name = parsed_args.provider or "qwen_cloud"
model = parsed_args.model or "qwen-max"

provider_config = ProviderConfig(
    name=provider_name,
    model=model,
    api_key=parsed_args.api_key,
    base_url=parsed_args.base_url,
    timeout_sec=parsed_args.timeout * 60
)

# Create fallback provider if specified
if parsed_args.fallback:
    fallback_name = parsed_args.fallback
    fallback_config = ProviderConfig(
        name=fallback_name,
        model="qwen-max" if fallback_name == "qwen_cloud" else "llama3.1:8b",
        api_key=parsed_args.api_key,
    )
    provider = FallbackProvider(provider_config, fallback_config)
    print(f"Using provider: {provider_name} with {fallback_name} fallback")
else:
    provider = ProviderFactory.create(provider_name, provider_config)
    print(f"Using provider: {provider_name} (model: {model})")
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_cli.py -v --no-cov`
Expected: PASS (update existing tests if needed)

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/cli.py src/tests/test_cli.py
git commit -m "feat(FEAT-005-4): add --fallback option to CLI

- FallbackProvider integration
- --fallback flag for secondary provider
- Auto-switch on primary failure
- Tests: updated"
```

---

### Task 5: Документация

**Files:**
- Modify: `docs/PROVIDERS.md`
- Modify: `README.md`

**Step 1: Update PROVIDERS.md**

```markdown
# Add to PROVIDERS.md after CLI usage section

## Fallback режим

Автоматический фоллбэк при недоступности основного провайдера:

```bash
# Ollama с фоллбэком на Qwen Cloud
qwenex plan.md --provider ollama --fallback qwen_cloud

# Локальная модель с облачным фоллбэком
qwenex plan.md --provider ollama --model llama3.1:8b --fallback qwen_cloud
```

**Поведение:**
1. Проверяется доступность Ollama (GET /api/tags)
2. Если доступен — используется Ollama
3. Если недоступен — автоматический переход на Qwen Cloud
4. Все последующие запросы идут через фоллбэк

## Ollama CLI

Прямое взаимодействие с Ollama:

```bash
# Проверка доступности
qwenex-ollama --check

# Список моделей
qwenex-ollama --list

# Единичный запрос
qwenex-ollama "What is Python?"

# Интерактивный режим
qwenex-ollama
> Hello!
> quit
```
```

**Step 2: Update README.md**

```markdown
# Add to README.md features section
- **Автофоллбэк** — переключение на облако при недоступности локальной модели
```

**Step 3: Commit**

```bash
cd qwenex
git add docs/PROVIDERS.md README.md
git commit -m "docs(FEAT-005-5): add Ollama and fallback documentation

- Fallback mode usage examples
- Ollama CLI commands
- Update README with new features"
```

---

### Task 6: MCP инструмент для Ollama

**Files:**
- Create: `src/qwenex/mcp/tools/ollama.py`
- Modify: `src/qwenex/mcp/server.py`

**Step 1: Create Ollama MCP tools**

```python
# src/qwenex/mcp/tools/ollama.py
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
```

**Step 2: Register tools in server.py**

```python
# src/qwenex/mcp/server.py - add import and registration
from .tools.ollama import register_ollama_tools

# In create_server() or similar:
register_ollama_tools(mcp)
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_mcp_server.py -v --no-cov`
Expected: PASS

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/mcp/tools/ollama.py src/qwenex/mcp/server.py
git commit -m "feat(FEAT-005-6): add Ollama MCP tools

- ollama_check: verify Ollama availability
- ollama_list_models: list available models
- ollama_run: execute prompt through Ollama
- Integration with MCP server"
```

---

## Завершение плана

**Проверка покрытия тестов:**

```bash
cd qwenex && pytest --cov=src/qwenex --cov-report=term-missing
```

Expected: 80%+ покрытие

**Запуск всех тестов:**

```bash
cd qwenex && pytest -v
```

Expected: Все тесты проходят

---

## Итоговый список коммитов

1. `feat(FEAT-005-1): add Ollama CLI command`
2. `feat(FEAT-005-2): add qwenex-ollama entry point`
3. `feat(FEAT-005-3): add FallbackProvider`
4. `feat(FEAT-005-4): add --fallback option to CLI`
5. `docs(FEAT-005-5): add Ollama and fallback documentation`
6. `feat(FEAT-005-6): add Ollama MCP tools`

**Всего:** 6 коммитов, ~10 тестов

---

План готов и сохранён в `docs/plans/2026-02-27-feat-005-local-models.md`.

**Два варианта выполнения:**

**1. Subagent-Driven (эта сессия)** — Запускаю свежего субагента на каждую задачу, code review между задачами, быстрая итерация

**2. Параллельная сессия (отдельная)** — Открыть новую сессию с `superpowers:executing-plans`, пакетное выполнение с чекпоинтами

**Какой подход выбираешь?**
