"""Tests for Qwen CLI executor."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch
from qwenex.qwen_executor import QwenExecutor, TaskTimeoutError, parse_event
from qwenex.models.base import ProviderConfig
from qwenex.models.qwen_cloud import QwenCloudProvider


class TestParseEvent:
    """Tests for parse_event function."""

    def test_parse_stream_json_line(self):
        """Test parsing a single stream-json line."""
        line = '{"type":"assistant","message":{"content":[{"type":"text","text":"OK"}]}}'
        event = parse_event(line)

        assert event['type'] == 'assistant'
        assert event['message']['content'][0]['text'] == 'OK'

    def test_parse_result_event(self):
        """Test parsing result event."""
        line = '{"type":"result","result":"Task completed"}'
        event = parse_event(line)

        assert event['type'] == 'result'
        assert event['result'] == 'Task completed'

    def test_parse_system_event(self):
        """Test parsing system event."""
        line = '{"type":"system","message":"Starting task"}'
        event = parse_event(line)

        assert event['type'] == 'system'
        assert event['message'] == 'Starting task'


class TestTaskTimeoutError:
    """Tests for TaskTimeoutError exception."""

    def test_timeout_error_message(self):
        """Test TaskTimeoutError message."""
        error = TaskTimeoutError("Task exceeded 10 minutes timeout")
        assert str(error) == "Task exceeded 10 minutes timeout"


class TestQwenExecutorWithProvider:
    """Tests for QwenExecutor with injected provider."""

    @pytest.mark.asyncio
    async def test_executor_with_provider_complete(self):
        """Test executor with injected provider using complete mode."""
        config = ProviderConfig(
            name="qwen_cloud",
            model="qwen-max",
            api_key="test-key"
        )
        provider = QwenCloudProvider(config)
        executor = QwenExecutor(provider=provider)
        
        with patch.object(provider, 'complete', new=AsyncMock(return_value="Response")):
            events = []
            async for event in executor.run_task("Test prompt", stream=False):
                events.append(event)
            
            assert len(events) == 1
            assert events[0]["type"] == "complete"
            assert events[0]["content"] == "Response"

    @pytest.mark.asyncio
    async def test_executor_with_provider_stream(self):
        """Test executor with injected provider using stream mode."""
        config = ProviderConfig(
            name="qwen_cloud",
            model="qwen-max",
            api_key="test-key"
        )
        provider = QwenCloudProvider(config)
        executor = QwenExecutor(provider=provider)
        
        async def mock_stream(*args, **kwargs):
            for chunk in ["Hello ", "world", "!"]:
                yield chunk
        
        with patch.object(provider, 'stream', new=mock_stream):
            events = []
            async for event in executor.run_task("Test prompt", stream=True):
                events.append(event)
            
            assert len(events) == 3
            assert events[0]["type"] == "chunk"
            assert events[0]["content"] == "Hello "
            assert events[1]["content"] == "world"
            assert events[2]["content"] == "!"

    @pytest.mark.asyncio
    async def test_executor_with_provider_timeout(self):
        """Test executor timeout with provider."""
        config = ProviderConfig(
            name="qwen_cloud",
            model="qwen-max",
            api_key="test-key"
        )
        provider = QwenCloudProvider(config)
        executor = QwenExecutor(provider=provider, timeout_min=0.01)
        
        async def mock_complete(*args, **kwargs):
            await asyncio.sleep(100)
            return "Response"
        
        with patch.object(provider, 'complete', new=mock_complete):
            with pytest.raises(TaskTimeoutError):
                async for event in executor.run_task("Test prompt", stream=False):
                    pass
