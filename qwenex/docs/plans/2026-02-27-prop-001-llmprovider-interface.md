# PROP-001: Интерфейс LLMProvider Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Создать абстракцию LLMProvider для поддержки мульти-провайдера (Qwen Cloud, Ollama, OpenAI) с возможностью переключения между ними.

**Architecture:** Интерфейс через Python Protocol с async методами. Реализация через отдельные классы для каждого провайдера. Factory для создания экземпляров. Конфигурация через pydantic settings.

**Tech Stack:** Python 3.11+ · asyncio · Protocol (typing) · pydantic · FastMCP

---

## Обзор изменений

**Создать:**
- `src/qwenex/models/base.py` — Protocol интерфейс LLMProvider
- `src/qwenex/models/qwen_cloud.py` — Qwen Cloud API реализация
- `src/qwenex/models/ollama.py` — Ollama реализация (задел)
- `src/qwenex/models/openai.py` — OpenAI реализация (задел)
- `src/qwenex/models/factory.py` — Factory для создания провайдеров
- `src/qwenex/config.py` — Конфигурация провайдеров

**Модифицировать:**
- `src/qwenex/qwen_executor.py` — Использовать LLMProvider вместо subprocess
- `src/qwenex/orchestrator.py` — Inject provider через конструктор
- `src/qwenex/cli.py` — Добавить опции выбора провайдера

**Тесты:**
- `src/tests/test_models_base.py` — Тесты интерфейса
- `src/tests/test_models_qwen_cloud.py` — Тесты Qwen Cloud
- `src/tests/test_models_ollama.py` — Тесты Ollama
- `src/tests/test_models_openai.py` — Тесты OpenAI
- `src/tests/test_models_factory.py` — Тесты Factory
- `src/tests/test_config.py` — Тесты конфигурации

---

### Task 1: Базовый интерфейс LLMProvider

**Files:**
- Create: `src/qwenex/models/base.py`
- Test: `src/tests/test_models_base.py`

**Step 1: Write the failing test**

```python
# src/tests/test_models_base.py
import pytest
from qwenex.models.base import LLMProvider, Message, ProviderConfig


def test_protocol_definition():
    """Test that LLMProvider protocol is properly defined."""
    # Protocol should be definable
    assert hasattr(LLMProvider, 'complete')
    assert hasattr(LLMProvider, 'check_health')
    assert hasattr(LLMProvider, 'get_config')


@pytest.mark.asyncio
async def test_message_structure():
    """Test Message dataclass."""
    msg = Message(role="user", content="Test prompt")
    assert msg.role == "user"
    assert msg.content == "Test prompt"
    
    msg_with_system = Message(
        role="user",
        content="Test",
        system_prompt="You are helpful"
    )
    assert msg_with_system.system_prompt == "You are helpful"


def test_provider_config():
    """Test ProviderConfig dataclass."""
    config = ProviderConfig(
        name="qwen_cloud",
        api_key="test-key",
        model="qwen-max",
        timeout_sec=600
    )
    assert config.name == "qwen_cloud"
    assert config.api_key == "test-key"
    assert config.model == "qwen-max"
    assert config.timeout_sec == 600
    assert config.base_url is None  # Optional field
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_models_base.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.models.base'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/models/base.py
"""Base models and interfaces for LLM providers."""

from dataclasses import dataclass, field
from typing import Protocol, AsyncIterator, Dict, Any, Optional, runtime_checkable


@dataclass
class Message:
    """Message for LLM communication."""
    role: str  # "user", "assistant", "system"
    content: str
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_sec: int = 600
    extra: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
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
        system_prompt: Optional[str] = None,
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
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_models_base.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/models/base.py src/tests/test_models_base.py
git commit -m "feat(PROP-001-1): add LLMProvider protocol interface

- Define LLMProvider Protocol with async methods
- Add Message and ProviderConfig dataclasses
- Enable runtime type checking with @runtime_checkable
- Tests: 3 passing"
```

---

### Task 2: Qwen Cloud Provider реализация

**Files:**
- Create: `src/qwenex/models/qwen_cloud.py`
- Test: `src/tests/test_models_qwen_cloud.py`

**Step 1: Write the failing test**

```python
# src/tests/test_models_qwen_cloud.py
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from qwenex.models.qwen_cloud import QwenCloudProvider
from qwenex.models.base import ProviderConfig


def test_qwen_config_creation():
    """Test QwenCloudProvider configuration."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/api/v1",
        timeout_sec=300
    )
    provider = QwenCloudProvider(config)
    assert provider.get_config().name == "qwen_cloud"
    assert provider.get_config().model == "qwen-max"


@pytest.mark.asyncio
async def test_qwen_health_check_success():
    """Test successful health check."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await provider.check_health()
        assert result is True


@pytest.mark.asyncio
async def test_qwen_health_check_failure():
    """Test failed health check."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.get.side_effect = Exception("Connection error")
        
        result = await provider.check_health()
        assert result is False


@pytest.mark.asyncio
async def test_qwen_complete():
    """Test completion request."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    
    mock_response = {
        "choices": [{
            "message": {"content": "Generated response"}
        }]
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        result = await provider.complete("Test prompt", system_prompt="You are helpful")
        assert result == "Generated response"


@pytest.mark.asyncio
async def test_qwen_stream():
    """Test streaming completion."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    
    chunks = ["Hello ", "world", "!"]
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.content.__aiter__.return_value = [
            f'data: {{"choices": [{{"delta": {{"content": "{chunk}"}}}}]}}\n'.encode()
            for chunk in chunks
        ]
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        result = []
        async for chunk in provider.stream("Test prompt"):
            result.append(chunk)
        
        assert result == chunks
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_models_qwen_cloud.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.models.qwen_cloud'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/models/qwen_cloud.py
"""Qwen Cloud API provider implementation."""

import asyncio
import json
from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass

from .base import LLMProvider, Message, ProviderConfig


@dataclass
class QwenCloudConfig(ProviderConfig):
    """Extended configuration for Qwen Cloud."""
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    max_tokens: int = 2048
    temperature: float = 0.7


class QwenCloudProvider:
    """Qwen Cloud API provider."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Qwen Cloud provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self._session: Optional[Any] = None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Get completion from Qwen Cloud API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters (temperature, max_tokens)
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API request fails
        """
        import aiohttp
        
        url = f"{self.config.base_url}/chat/completions"
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
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream completion from Qwen Cloud API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        import aiohttp
        
        url = f"{self.config.base_url}/chat/completions"
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
        """Check if Qwen Cloud API is accessible.
        
        Returns:
            True if API is accessible
        """
        import aiohttp
        
        url = f"{self.config.base_url}/models"
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
```

**Step 4: Add aiohttp dependency**

```python
# pyproject.toml - add to [project.dependencies]
"aiohttp>=3.9.0",
```

**Step 5: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_models_qwen_cloud.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
cd qwenex
git add src/qwenex/models/qwen_cloud.py src/tests/test_models_qwen_cloud.py pyproject.toml
git commit -m "feat(PROP-001-2): add QwenCloudProvider implementation

- Implement LLMProvider protocol for Qwen Cloud API
- Support both complete() and stream() methods
- Add health check endpoint
- Use aiohttp for async HTTP requests
- Tests: 5 passing"
```

---

### Task 3: Ollama Provider реализация (задел)

**Files:**
- Create: `src/qwenex/models/ollama.py`
- Test: `src/tests/test_models_ollama.py`

**Step 1: Write the failing test**

```python
# src/tests/test_models_ollama.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from qwenex.models.ollama import OllamaProvider
from qwenex.models.base import ProviderConfig


def test_ollama_config_creation():
    """Test OllamaProvider configuration."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434",
        timeout_sec=300
    )
    provider = OllamaProvider(config)
    assert provider.get_config().name == "ollama"
    assert provider.get_config().model == "llama3.1:8b"


@pytest.mark.asyncio
async def test_ollama_health_check_success():
    """Test successful health check."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = OllamaProvider(config)
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await provider.check_health()
        assert result is True


@pytest.mark.asyncio
async def test_ollama_complete():
    """Test completion request."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = OllamaProvider(config)
    
    mock_response = {
        "response": "Generated response",
        "done": True
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        result = await provider.complete("Test prompt")
        assert result == "Generated response"


@pytest.mark.asyncio
async def test_ollama_stream():
    """Test streaming completion."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = OllamaProvider(config)
    
    chunks = [
        {"response": "Hello ", "done": False},
        {"response": "world", "done": False},
        {"response": "!", "done": True}
    ]
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(side_effect=chunks)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        result = []
        async for chunk in provider.stream("Test prompt"):
            result.append(chunk)
        
        assert result == ["Hello ", "world", "!"]
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_models_ollama.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.models.ollama'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/models/ollama.py
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
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_models_ollama.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/models/ollama.py src/tests/test_models_ollama.py
git commit -m "feat(PROP-001-3): add OllamaProvider implementation

- Implement LLMProvider protocol for Ollama local models
- Support both complete() and stream() methods
- Add health check via /api/tags endpoint
- Enable local model execution for offline use
- Tests: 4 passing"
```

---

### Task 4: OpenAI Provider реализация (задел)

**Files:**
- Create: `src/qwenex/models/openai.py`
- Test: `src/tests/test_models_openai.py`

**Step 1: Write the failing test**

```python
# src/tests/test_models_openai.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from qwenex.models.openai import OpenAIProvider
from qwenex.models.base import ProviderConfig


def test_openai_config_creation():
    """Test OpenAIProvider configuration."""
    config = ProviderConfig(
        name="openai",
        model="gpt-4o",
        api_key="sk-test123",
        base_url="https://api.openai.com/v1",
        timeout_sec=300
    )
    provider = OpenAIProvider(config)
    assert provider.get_config().name == "openai"
    assert provider.get_config().model == "gpt-4o"


@pytest.mark.asyncio
async def test_openai_complete():
    """Test completion request."""
    config = ProviderConfig(
        name="openai",
        model="gpt-4o",
        api_key="sk-test123"
    )
    provider = OpenAIProvider(config)
    
    mock_response = {
        "choices": [{
            "message": {"content": "Generated response"}
        }]
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        result = await provider.complete("Test prompt", system_prompt="You are helpful")
        assert result == "Generated response"
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_models_openai.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.models.openai'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/models/openai.py
"""OpenAI provider implementation."""

from typing import AsyncIterator, Any, Optional

from .base import LLMProvider, ProviderConfig


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
        system_prompt: Optional[str] = None,
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
        system_prompt: Optional[str] = None,
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
        import json
        
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
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_models_openai.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/models/openai.py src/tests/test_models_openai.py
git commit -m "feat(PROP-001-4): add OpenAIProvider implementation

- Implement LLMProvider protocol for OpenAI API
- Support both complete() and stream() methods
- Compatible with OpenAI-compatible APIs (vLLM, etc.)
- Tests: 2 passing"
```

---

### Task 5: Factory для создания провайдеров

**Files:**
- Create: `src/qwenex/models/factory.py`
- Create: `src/qwenex/models/__init__.py`
- Test: `src/tests/test_models_factory.py`

**Step 1: Write the failing test**

```python
# src/tests/test_models_factory.py
import pytest
import os
from qwenex.models.factory import ProviderFactory, ProviderType
from qwenex.models.qwen_cloud import QwenCloudProvider
from qwenex.models.ollama import OllamaProvider
from qwenex.models.openai import OpenAIProvider
from qwenex.models.base import ProviderConfig


def test_provider_type_enum():
    """Test ProviderType enum values."""
    assert ProviderType.QWEN_CLOUD.value == "qwen_cloud"
    assert ProviderType.OLLAMA.value == "ollama"
    assert ProviderType.OPENAI.value == "openai"


def test_factory_create_qwen():
    """Test factory creates QwenCloudProvider."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = ProviderFactory.create(ProviderType.QWEN_CLOUD, config)
    assert isinstance(provider, QwenCloudProvider)


def test_factory_create_ollama():
    """Test factory creates OllamaProvider."""
    config = ProviderConfig(
        name="ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434"
    )
    provider = ProviderFactory.create(ProviderType.OLLAMA, config)
    assert isinstance(provider, OllamaProvider)


def test_factory_create_openai():
    """Test factory creates OpenAIProvider."""
    config = ProviderConfig(
        name="openai",
        model="gpt-4o",
        api_key="sk-test123"
    )
    provider = ProviderFactory.create(ProviderType.OPENAI, config)
    assert isinstance(provider, OpenAIProvider)


def test_factory_create_invalid():
    """Test factory raises on invalid provider type."""
    config = ProviderConfig(name="invalid", model="test")
    with pytest.raises(ValueError, match="Unknown provider type"):
        ProviderFactory.create("invalid", config)


def test_factory_from_env(monkeypatch):
    """Test factory creates provider from environment variables."""
    monkeypatch.setenv("QWENEX_PROVIDER", "ollama")
    monkeypatch.setenv("QWENEX_MODEL", "llama3.1:8b")
    
    config = ProviderFactory.create_from_env()
    assert config.name == "ollama"
    assert config.model == "llama3.1:8b"
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_models_factory.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.models.factory'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/models/factory.py
"""Factory for creating LLM providers."""

import os
from enum import Enum
from typing import Type, Union

from .base import LLMProvider, ProviderConfig


class ProviderType(str, Enum):
    """Supported provider types."""
    QWEN_CLOUD = "qwen_cloud"
    OLLAMA = "ollama"
    OPENAI = "openai"


class ProviderFactory:
    """Factory for creating LLM provider instances."""
    
    _providers: dict[str, Type[LLMProvider]] = {}
    
    @classmethod
    def register(cls, provider_type: ProviderType, provider_class: Type[LLMProvider]) -> None:
        """Register a provider class.
        
        Args:
            provider_type: Provider type enum
            provider_class: Provider class
        """
        cls._providers[provider_type.value] = provider_class
    
    @classmethod
    def create(
        cls,
        provider_type: Union[ProviderType, str],
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
    from .qwen_cloud import QwenCloudProvider
    from .ollama import OllamaProvider
    from .openai import OpenAIProvider
    
    ProviderFactory.register(ProviderType.QWEN_CLOUD, QwenCloudProvider)
    ProviderFactory.register(ProviderType.OLLAMA, OllamaProvider)
    ProviderFactory.register(ProviderType.OPENAI, OpenAIProvider)


_register_providers()
```

```python
# src/qwenex/models/__init__.py
"""Models package for LLM providers."""

from .base import LLMProvider, Message, ProviderConfig
from .factory import ProviderFactory, ProviderType

__all__ = [
    "LLMProvider",
    "Message",
    "ProviderConfig",
    "ProviderFactory",
    "ProviderType",
]
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_models_factory.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/models/factory.py src/qwenex/models/__init__.py src/tests/test_models_factory.py
git commit -m "feat(PROP-001-5): add ProviderFactory

- Factory pattern for creating LLM providers
- Support environment variable configuration
- Enum-based provider type safety
- Auto-registration of providers
- Tests: 6 passing"
```

---

### Task 6: Конфигурация провайдеров

**Files:**
- Create: `src/qwenex/config.py`
- Test: `src/tests/test_config.py`

**Step 1: Write the failing test**

```python
# src/tests/test_config.py
import pytest
import os
from pathlib import Path
from qwenex.config import QwenexConfig, ProviderSettings, load_config, save_config


def test_provider_settings():
    """Test ProviderSettings dataclass."""
    settings = ProviderSettings(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key",
        base_url="https://api.example.com",
        timeout_sec=300
    )
    assert settings.name == "qwen_cloud"
    assert settings.api_key == "test-key"


def test_qwenex_config():
    """Test QwenexConfig dataclass."""
    config = QwenexConfig(
        default_provider="qwen_cloud",
        providers={
            "qwen_cloud": ProviderSettings(
                name="qwen_cloud",
                model="qwen-max",
                api_key="test-key"
            )
        }
    )
    assert config.default_provider == "qwen_cloud"
    assert "qwen_cloud" in config.providers


def test_load_config_from_file(tmp_path):
    """Test loading config from file."""
    config_file = tmp_path / "config.json"
    config_file.write_text('''
    {
        "default_provider": "ollama",
        "providers": {
            "ollama": {
                "name": "ollama",
                "model": "llama3.1:8b",
                "base_url": "http://localhost:11434"
            }
        }
    }
    ''')
    
    config = load_config(config_file)
    assert config.default_provider == "ollama"
    assert "ollama" in config.providers


def test_save_config(tmp_path):
    """Test saving config to file."""
    config_file = tmp_path / "config.json"
    
    config = QwenexConfig(
        default_provider="openai",
        providers={
            "openai": ProviderSettings(
                name="openai",
                model="gpt-4o",
                api_key="sk-test"
            )
        }
    )
    
    save_config(config, config_file)
    assert config_file.exists()
    
    loaded = load_config(config_file)
    assert loaded.default_provider == "openai"


def test_load_config_from_env(monkeypatch):
    """Test loading config from environment."""
    monkeypatch.setenv("QWENEX_DEFAULT_PROVIDER", "ollama")
    monkeypatch.setenv("QWENEX_MODEL", "llama3.1:8b")
    
    config = load_config()
    assert config.default_provider == "ollama"
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.config'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/config.py
"""Configuration management for Qwenex."""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Optional

from .models.base import ProviderConfig


@dataclass
class ProviderSettings:
    """Settings for a single provider."""
    name: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_sec: int = 600
    extra: Dict[str, str] = field(default_factory=dict)
    
    def to_provider_config(self) -> ProviderConfig:
        """Convert to ProviderConfig."""
        return ProviderConfig(
            name=self.name,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            timeout_sec=self.timeout_sec,
            extra=self.extra
        )


@dataclass
class QwenexConfig:
    """Main configuration for Qwenex."""
    default_provider: str = "qwen_cloud"
    providers: Dict[str, ProviderSettings] = field(default_factory=dict)
    timeout_sec: int = 600
    max_retries: int = 2
    review_iterations: int = 3
    
    def get_provider(self, name: str) -> Optional[ProviderSettings]:
        """Get provider settings by name."""
        return self.providers.get(name)


def get_config_path() -> Path:
    """Get path to configuration file."""
    config_dir = Path.home() / ".qwenex"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config(config_path: Optional[Path] = None) -> QwenexConfig:
    """Load configuration from file or environment.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Loaded configuration
    """
    if config_path is None:
        config_path = get_config_path()
    
    # Try to load from file
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            providers = {
                name: ProviderSettings(**settings)
                for name, settings in data.get("providers", {}).items()
            }
            return QwenexConfig(
                default_provider=data.get("default_provider", "qwen_cloud"),
                providers=providers,
                timeout_sec=data.get("timeout_sec", 600),
                max_retries=data.get("max_retries", 2),
                review_iterations=data.get("review_iterations", 3)
            )
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not load config file: {e}")
    
    # Fall back to environment variables
    default_provider = os.getenv("QWENEX_DEFAULT_PROVIDER", "qwen_cloud")
    model = os.getenv("QWENEX_MODEL", "qwen-max")
    api_key = os.getenv("QWENEX_API_KEY")
    base_url = os.getenv("QWENEX_BASE_URL")
    timeout = int(os.getenv("QWENEX_TIMEOUT", "600"))
    
    providers = {}
    if api_key or base_url:
        providers[default_provider] = ProviderSettings(
            name=default_provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_sec=timeout
        )
    
    return QwenexConfig(
        default_provider=default_provider,
        providers=providers
    )


def save_config(config: QwenexConfig, config_path: Optional[Path] = None) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration to save
        config_path: Optional path to config file
    """
    if config_path is None:
        config_path = get_config_path()
    
    data = {
        "default_provider": config.default_provider,
        "providers": {
            name: asdict(settings)
            for name, settings in config.providers.items()
        },
        "timeout_sec": config.timeout_sec,
        "max_retries": config.max_retries,
        "review_iterations": config.review_iterations
    }
    
    config_path.parent.mkdir(exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_config.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/config.py src/tests/test_config.py
git commit -m "feat(PROP-001-6): add configuration management

- QwenexConfig dataclass for global settings
- ProviderSettings for per-provider config
- Load/save JSON config files
- Environment variable fallback
- Tests: 5 passing"
```

---

### Task 7: Интеграция в qwen_executor.py

**Files:**
- Modify: `src/qwenex/qwen_executor.py`
- Test: `src/tests/test_qwen_executor.py` (modify existing)

**Step 1: Read existing qwen_executor.py**

Already read - uses subprocess for Qwen CLI.

**Step 2: Write the failing test**

```python
# src/tests/test_qwen_executor.py - add new tests
import pytest
from unittest.mock import AsyncMock, patch
from qwenex.qwen_executor import QwenExecutor
from qwenex.models.base import ProviderConfig
from qwenex.models.qwen_cloud import QwenCloudProvider


@pytest.mark.asyncio
async def test_executor_with_provider():
    """Test executor with injected provider."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    executor = QwenExecutor(provider=provider)
    
    with patch.object(provider, 'complete', new=AsyncMock(return_value="Response")):
        events = []
        async for event in executor.run_task("Test prompt"):
            events.append(event)
        
        assert len(events) > 0
        assert events[-1]["type"] == "complete"
```

**Step 3: Modify implementation**

```python
# src/qwenex/qwen_executor.py - modify
"""Execute tasks using LLM providers."""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, Union

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
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_qwen_executor.py::test_executor_with_provider -v`
Expected: PASS

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/qwen_executor.py src/tests/test_qwen_executor.py
git commit -m "feat(PROP-001-7): integrate LLMProvider into QwenExecutor

- Inject provider via constructor
- Support both streaming and non-streaming modes
- Fallback to environment configuration
- Remove subprocess dependency for Qwen CLI
- Tests: updated"
```

---

### Task 8: Интеграция в orchestrator.py

**Files:**
- Modify: `src/qwenex/orchestrator.py`
- Test: Update existing tests

**Step 1: Read existing orchestrator.py**

```bash
cd qwenex && cat src/qwenex/orchestrator.py
```

**Step 2: Modify implementation**

```python
# src/qwenex/orchestrator.py - add provider injection
"""Orchestrate plan execution."""

import asyncio
from pathlib import Path
from typing import Optional

from .models.base import LLMProvider, ProviderConfig
from .qwen_executor import QwenExecutor
from .plan_parser import Plan, parse_plan
from .progress import ProgressTracker


class Orchestrator:
    """Orchestrate plan execution."""

    def __init__(
        self,
        plan_path: Path,
        provider: Optional[LLMProvider] = None,
        provider_config: Optional[ProviderConfig] = None,
        timeout_min: int = 10
    ):
        """Initialize orchestrator.

        Args:
            plan_path: Path to plan file
            provider: LLM provider instance (optional)
            provider_config: Provider configuration (optional)
            timeout_min: Timeout in minutes for each task
        """
        self.plan_path = plan_path
        self.plan: Optional[Plan] = None
        self.executor = QwenExecutor(
            provider=provider,
            provider_config=provider_config,
            timeout_min=timeout_min
        )
        self.tracker = ProgressTracker()

    async def run(self) -> bool:
        """Run plan execution.

        Returns:
            True if all tasks completed successfully
        """
        # Parse plan
        self.plan = parse_plan(self.plan_path)
        
        # Initialize progress tracking
        await self.tracker.initialize(self.plan)
        
        # Execute tasks
        while not self.plan.is_complete:
            task = self.plan.current_task
            if task is None:
                break
            
            # Build prompt for task
            prompt = self._build_prompt(task)
            
            # Execute task
            success = await self._execute_task(task.number, prompt)
            
            if not success:
                return False
            
            # Move to next task
            self.plan.next_task()
        
        return True

    def _build_prompt(self, task) -> str:
        """Build prompt for a task."""
        # Implementation from existing orchestrator
        pass

    async def _execute_task(self, task_id: str, prompt: str) -> bool:
        """Execute a single task."""
        # Implementation from existing orchestrator
        pass
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_orchestrator.py -v`
Expected: PASS (update existing tests for new constructor signature)

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/orchestrator.py src/tests/test_orchestrator.py
git commit -m "feat(PROP-001-8): inject LLMProvider into Orchestrator

- Add provider parameter to constructor
- Pass provider to QwenExecutor
- Maintain backward compatibility
- Tests: updated"
```

---

### Task 9: Интеграция в cli.py

**Files:**
- Modify: `src/qwenex/cli.py`
- Test: `src/tests/test_cli.py` (modify existing)

**Step 1: Add CLI options for provider selection**

```python
# src/qwenex/cli.py - modify
"""CLI interface for Qwenex."""

import argparse
import asyncio
from pathlib import Path

from .orchestrator import Orchestrator
from .config import load_config
from .models.factory import ProviderFactory


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Qwenex - Autonomous plan execution"
    )
    
    parser.add_argument(
        "plan",
        type=Path,
        help="Path to plan file (FEAT/PROP or markdown)"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="LLM provider (qwen_cloud, ollama, openai)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (overrides config)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL for API (overrides config)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in minutes per task"
    )
    
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize project with BOOT.md and WAL.md"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="qwenex 0.1.0"
    )
    
    return parser


async def async_main(args: argparse.Namespace) -> int:
    """Async main function.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    # Load configuration
    config = load_config()
    
    # Override with CLI options
    provider_name = args.provider or config.default_provider
    model = args.model or "qwen-max"
    api_key = args.api_key
    base_url = args.base_url
    
    # Create provider
    from .models.base import ProviderConfig
    provider_config = ProviderConfig(
        name=provider_name,
        model=model,
        api_key=api_key,
        base_url=base_url
    )
    provider = ProviderFactory.create(provider_name, provider_config)
    
    # Create orchestrator
    orchestrator = Orchestrator(
        plan_path=args.plan,
        provider=provider,
        timeout_min=args.timeout
    )
    
    # Run execution
    success = await orchestrator.run()
    
    return 0 if success else 1


def entry_point() -> None:
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.init:
        # Initialize project
        pass
    
    exit_code = asyncio.run(async_main(args))
    exit(exit_code)
```

**Step 2: Run tests**

Run: `cd qwenex && pytest src/tests/test_cli.py -v`
Expected: PASS (update existing tests)

**Step 3: Commit**

```bash
cd qwenex
git add src/qwenex/cli.py src/tests/test_cli.py
git commit -m "feat(PROP-001-9): add CLI options for provider selection

- --provider flag for provider type
- --model flag for model selection
- --api-key and --base-url overrides
- Load from config with CLI override
- Tests: updated"
```

---

### Task 10: Документация и финализация

**Files:**
- Create: `docs/PROVIDERS.md`
- Modify: `README.md`
- Modify: `BOOT.md`

**Step 1: Create providers documentation**

```markdown
# Провайдеры LLM

Qwenex поддерживает множественных LLM провайдеров через интерфейс `LLMProvider`.

## Поддерживаемые провайдеры

### Qwen Cloud (по умолчанию)

**Provider:** `qwen_cloud`

**Конфигурация:**
```bash
export QWENEX_PROVIDER=qwen_cloud
export QWENEX_MODEL=qwen-max
export QWENEX_API_KEY=your-api-key
```

**Модели:**
- `qwen-max` - максимальная производительность
- `qwen-plus` - баланс цены/качества
- `qwen-turbo` - быстрая и дешёвая

### Ollama (локальные модели)

**Provider:** `ollama`

**Конфигурация:**
```bash
export QWENEX_PROVIDER=ollama
export QWENEX_MODEL=llama3.1:8b
export QWENEX_BASE_URL=http://localhost:11434
```

**Модели:**
- `llama3.1:8b` - 8B параметров
- `llama3.1:70b` - 70B параметров
- `qwen2.5:7b` - Qwen локально

### OpenAI

**Provider:** `openai`

**Конфигурация:**
```bash
export QWENEX_PROVIDER=openai
export QWENEX_MODEL=gpt-4o
export QWENEX_API_KEY=sk-your-api-key
```

**Модели:**
- `gpt-4o` - флагманская
- `gpt-4o-mini` - бюджетная
- `o1-preview` - reasoning

## Конфигурационный файл

Создайте `~/.qwenex/config.json`:

```json
{
  "default_provider": "qwen_cloud",
  "providers": {
    "qwen_cloud": {
      "name": "qwen_cloud",
      "model": "qwen-max",
      "api_key": "your-api-key"
    },
    "ollama": {
      "name": "ollama",
      "model": "llama3.1:8b",
      "base_url": "http://localhost:11434"
    },
    "openai": {
      "name": "openai",
      "model": "gpt-4o",
      "api_key": "sk-your-api-key"
    }
  }
}
```

## CLI использование

```bash
# Использовать Qwen Cloud
qwenex specs/FEAT-001.md

# Использовать Ollama
qwenex specs/FEAT-001.md --provider ollama --model llama3.1:8b

# Использовать OpenAI с переопределением
qwenex specs/FEAT-001.md --provider openai --model gpt-4o --api-key sk-xxx
```

## Добавление нового провайдера

1. Создайте класс в `src/qwenex/models/<provider>.py`:

```python
from .base import LLMProvider, ProviderConfig

class MyProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config
    
    async def complete(self, prompt: str, **kwargs) -> str:
        # Реализация
        pass
    
    async def stream(self, prompt: str, **kwargs):
        # Реализация
        pass
    
    async def check_health(self) -> bool:
        # Реализация
        pass
    
    def get_config(self) -> ProviderConfig:
        return self.config
```

2. Зарегистрируйте в `src/qwenex/models/factory.py`:

```python
ProviderFactory.register(ProviderType.MY_PROVIDER, MyProvider)
```

## Сравнение провайдеров

| Провайдер | Скорость | Цена | Качество | Offline |
|-----------|----------|------|----------|---------|
| Qwen Cloud | ⚡⚡⚡ | 💰💰 | ⭐⭐⭐⭐ | ❌ |
| Ollama | ⚡⚡ | 💰 | ⭐⭐⭐ | ✅ |
| OpenAI | ⚡⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ | ❌ |
```

**Step 2: Update README.md**

Add section about providers to existing README.

**Step 3: Update BOOT.md**

Update стек section:
```markdown
**Стек:** Python 3.11+ · FastMCP · LLMProvider (Qwen/Ollama/OpenAI) · Git (subprocess)
```

**Step 4: Commit**

```bash
cd qwenex
git add docs/PROVIDERS.md README.md BOOT.md
git commit -m "docs(PROP-001-10): add provider documentation

- Create PROVIDERS.md with usage guide
- Update README with provider info
- Update BOOT.md tech stack
- Include comparison table"
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

**Проверка типов:**

```bash
cd qwenex && mypy src/qwenex
```

Expected: No type errors

**Linting:**

```bash
cd qwenex && ruff check src/qwenex
```

Expected: No errors

---

## Итоговый список коммитов

1. `feat(PROP-001-1): add LLMProvider protocol interface`
2. `feat(PROP-001-2): add QwenCloudProvider implementation`
3. `feat(PROP-001-3): add OllamaProvider implementation`
4. `feat(PROP-001-4): add OpenAIProvider implementation`
5. `feat(PROP-001-5): add ProviderFactory`
6. `feat(PROP-001-6): add configuration management`
7. `feat(PROP-001-7): integrate LLMProvider into QwenExecutor`
8. `feat(PROP-001-8): inject LLMProvider into Orchestrator`
9. `feat(PROP-001-9): add CLI options for provider selection`
10. `docs(PROP-001-10): add provider documentation`

**Всего:** 10 коммитов, ~25 тестов

---

План готов и сохранён в `docs/plans/2026-02-27-prop-001-llmprovider-interface.md`.

**Два варианта выполнения:**

**1. Subagent-Driven (эта сессия)** — Я запускаю свежего субагента на каждую задачу, делаю code review между задачами, быстрая итерация

**2. Параллельная сессия (отдельная)** — Открыть новую сессию с `superpowers:executing-plans`, пакетное выполнение с чекпоинтами

**Какой подход выбираешь?**
