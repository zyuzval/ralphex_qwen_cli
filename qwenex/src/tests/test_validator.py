"""Tests for validator."""

import pytest
from qwenex.validator import Validator, ValidationResult


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_success(self):
        """Test ValidationResult with success."""
        result = ValidationResult(
            success=True,
            output="Test output",
            commands=["echo test"]
        )
        assert result.success is True
        assert result.output == "Test output"
        assert result.commands == ["echo test"]

    def test_validation_result_str(self):
        """Test ValidationResult string representation."""
        result = ValidationResult(
            success=True,
            output="Test output",
            commands=["echo test"]
        )
        assert "PASS" in str(result)
        assert "Test output" in str(result)

    def test_validation_result_str_failure(self):
        """Test ValidationResult string representation on failure."""
        result = ValidationResult(
            success=False,
            output="Error occurred",
            commands=["exit 1"]
        )
        assert "FAIL" in str(result)
        assert "Error occurred" in str(result)


class TestValidator:
    """Tests for Validator class."""

    @pytest.mark.asyncio
    async def test_validate_success(self):
        """Test successful validation."""
        validator = Validator()

        # Use a command that always succeeds
        result = await validator.run(["echo test"])

        assert result.success is True
        assert "test" in result.output

    @pytest.mark.asyncio
    async def test_validate_failure(self):
        """Test failed validation."""
        validator = Validator()

        # Use a command that always fails
        result = await validator.run(["exit 1"])

        assert result.success is False

    @pytest.mark.asyncio
    async def test_validate_multiple_commands(self):
        """Test multiple validation commands."""
        validator = Validator()

        result = await validator.run([
            "echo first",
            "echo second",
        ])

        assert result.success is True
        assert "first" in result.output
        assert "second" in result.output

    @pytest.mark.asyncio
    async def test_validate_mixed_commands(self):
        """Test validation with mixed success/failure commands."""
        validator = Validator()

        # First succeeds, second fails
        result = await validator.run([
            "echo success",
            "exit 1",
        ])

        assert result.success is False
        assert "success" in result.output

    @pytest.mark.asyncio
    async def test_validate_no_commands(self):
        """Test validation with no commands."""
        validator = Validator()

        result = await validator.run([])

        assert result.success is True
        assert "No validation commands" in result.output

    @pytest.mark.asyncio
    async def test_validate_command_with_output(self):
        """Test validation command with multi-line output."""
        validator = Validator()

        result = await validator.run(["echo line1\nline2"])

        assert result.success is True
        assert "line1" in result.output
