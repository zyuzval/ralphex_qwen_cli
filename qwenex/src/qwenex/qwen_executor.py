"""Execute tasks using Qwen CLI."""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any


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
    """Execute tasks using Qwen CLI subprocess."""

    def __init__(self, timeout_min: int = 10):
        """Initialize executor.

        Args:
            timeout_min: Timeout in minutes for each task
        """
        self.timeout_min = timeout_min

    async def run_task(
        self,
        prompt: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a task using Qwen CLI.

        Args:
            prompt: Task prompt to execute

        Yields:
            Stream-json events from Qwen CLI

        Raises:
            TaskTimeoutError: If task exceeds timeout
        """
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                "qwen",
                "-y",  # YOLO mode - auto-approve all actions
                "-o", "stream-json",
                "-p", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Read stdout line by line
            while True:
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=self.timeout_min * 60
                    )
                    if not line:
                        break
                    try:
                        event = parse_event(line.decode('utf-8'))
                        yield event
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Skip malformed lines
                        continue
                except asyncio.TimeoutError:
                    # Timeout on readline - task took too long
                    if process:
                        process.kill()
                    raise TaskTimeoutError(
                        f"Task exceeded {self.timeout_min} minutes timeout"
                    )

            # Wait for process to complete
            await process.wait()

        except TaskTimeoutError:
            raise
        except Exception as e:
            if process:
                process.kill()
            raise TaskTimeoutError(
                f"Task exceeded {self.timeout_min} minutes timeout: {e}"
            )
