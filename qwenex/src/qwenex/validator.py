"""Validate task results using shell commands."""

import asyncio
from dataclasses import dataclass
from typing import List


@dataclass
class ValidationResult:
    """Result of validation."""
    success: bool
    output: str
    commands: List[str]

    def __str__(self) -> str:
        status = "PASS" if self.success else "FAIL"
        return f"Validation {status}:\n{self.output}"


class Validator:
    """Run validation commands."""

    async def run(self, commands: List[str]) -> ValidationResult:
        """Run validation commands.

        Args:
            commands: List of shell commands to run

        Returns:
            ValidationResult with success status and output
        """
        if not commands:
            return ValidationResult(
                success=True,
                output="No validation commands",
                commands=[]
            )

        all_output = []
        all_success = True

        for cmd in commands:
            try:
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )

                stdout, _ = await process.communicate()
                output = stdout.decode('utf-8', errors='replace')
                all_output.append(f"$ {cmd}\n{output}")

                if process.returncode != 0:
                    all_success = False

            except Exception as e:
                all_output.append(f"$ {cmd}\nError: {e}")
                all_success = False

        return ValidationResult(
            success=all_success,
            output="\n".join(all_output),
            commands=commands
        )
