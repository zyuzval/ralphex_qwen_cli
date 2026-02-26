"""Tests for Qwen CLI executor."""

import asyncio
import json
import pytest
from qwenex.qwen_executor import QwenExecutor, TaskTimeoutError, parse_event


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


class TestQwenExecutorMocked:
    """Tests for QwenExecutor with mocked subprocess."""

    @pytest.mark.asyncio
    async def test_run_task_mocked(self, monkeypatch):
        """Test with mocked subprocess."""
        # Mock subprocess to return fake events
        async def mock_create_subprocess_exec(*args, **kwargs):
            class MockStdout:
                def __init__(self, events):
                    self._events = events
                    self._index = 0

                async def readline(self):
                    if self._index < len(self._events):
                        event = self._events[self._index]
                        self._index += 1
                        return event
                    return b''

            class MockProcess:
                def __init__(self):
                    self.stdout = MockStdout([
                        b'{"type":"system","message":"Starting"}\n',
                        b'{"type":"assistant","message":{"content":[{"type":"text","text":"OK"}]}}\n',
                        b'{"type":"result","result":"Done"}\n',
                    ])

                async def wait(self):
                    pass

                def kill(self):
                    pass

            return MockProcess()

        monkeypatch.setattr(asyncio, 'create_subprocess_exec', mock_create_subprocess_exec)

        executor = QwenExecutor()
        events = []
        async for event in executor.run_task("test"):
            events.append(event)

        assert len(events) == 3
        assert events[0]['type'] == 'system'
        assert events[1]['type'] == 'assistant'
        assert events[2]['type'] == 'result'

    @pytest.mark.asyncio
    async def test_run_task_timeout(self, monkeypatch):
        """Test timeout handling."""
        async def mock_create_subprocess_exec(*args, **kwargs):
            class MockStdout:
                async def readline(self):
                    # Simulate hanging - never returns
                    await asyncio.sleep(100)
                    return b''

            class MockProcess:
                def __init__(self):
                    self.stdout = MockStdout()

                async def wait(self):
                    pass

                def kill(self):
                    pass

            return MockProcess()

        monkeypatch.setattr(asyncio, 'create_subprocess_exec', mock_create_subprocess_exec)

        # Use very short timeout for testing (0.01 min = 0.6 seconds)
        executor = QwenExecutor(timeout_min=0.01)

        with pytest.raises(TaskTimeoutError):
            async for event in executor.run_task("wait"):
                pass

    @pytest.mark.asyncio
    async def test_run_task_handles_malformed_json(self, monkeypatch):
        """Test that malformed JSON lines are skipped."""
        async def mock_create_subprocess_exec(*args, **kwargs):
            class MockStdout:
                def __init__(self, events):
                    self._events = events
                    self._index = 0

                async def readline(self):
                    if self._index < len(self._events):
                        event = self._events[self._index]
                        self._index += 1
                        return event
                    return b''

            class MockProcess:
                def __init__(self):
                    self.stdout = MockStdout([
                        b'not valid json\n',
                        b'{"type":"result","result":"OK"}\n',
                    ])

                async def wait(self):
                    pass

                def kill(self):
                    pass

            return MockProcess()

        monkeypatch.setattr(asyncio, 'create_subprocess_exec', mock_create_subprocess_exec)

        executor = QwenExecutor()
        events = []
        async for event in executor.run_task("test"):
            events.append(event)

        # Only valid event should be returned
        assert len(events) == 1
        assert events[0]['type'] == 'result'


class TestTaskTimeoutError:
    """Tests for TaskTimeoutError exception."""

    def test_timeout_error_message(self):
        """Test TaskTimeoutError message."""
        error = TaskTimeoutError("Task exceeded 10 minutes timeout")
        assert str(error) == "Task exceeded 10 minutes timeout"
