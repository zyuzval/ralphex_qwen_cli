"""Tests for CLI interface."""

import pytest
import argparse
from unittest.mock import patch, MagicMock, AsyncMock
from qwenex.cli import main, parse_args, setup_signal_handlers


class TestParseArgs:
    """Tests for argument parsing."""

    def test_parse_plan_file_only(self):
        """Test parsing with only plan file."""
        args = parse_args(["docs/plans/feature.md"])
        
        assert args.plan_file == "docs/plans/feature.md"
        assert args.auto is False
        assert args.interactive is False
        assert args.max_iterations == 3
        assert args.timeout == 10

    def test_parse_auto_mode(self):
        """Test parsing with --auto flag."""
        args = parse_args(["--auto", "docs/plans/feature.md"])
        
        assert args.auto is True
        assert args.interactive is False

    def test_parse_interactive_mode(self):
        """Test parsing with --interactive flag."""
        args = parse_args(["--interactive", "docs/plans/feature.md"])
        
        assert args.interactive is True
        assert args.auto is False

    def test_parse_max_iterations(self):
        """Test parsing with --max-iterations flag."""
        args = parse_args(["--max-iterations", "5", "docs/plans/feature.md"])
        
        assert args.max_iterations == 5

    def test_parse_timeout(self):
        """Test parsing with --timeout flag."""
        args = parse_args(["--timeout", "15", "docs/plans/feature.md"])
        
        assert args.timeout == 15

    def test_parse_debug_mode(self):
        """Test parsing with --debug flag."""
        args = parse_args(["--debug", "docs/plans/feature.md"])
        
        assert args.debug is True

    def test_parse_no_color(self):
        """Test parsing with --no-color flag."""
        args = parse_args(["--no-color", "docs/plans/feature.md"])
        
        assert args.no_color is True

    def test_parse_all_options(self):
        """Test parsing with all options."""
        args = parse_args([
            "--auto",
            "--max-iterations", "5",
            "--timeout", "20",
            "--debug",
            "--no-color",
            "docs/plans/feature.md"
        ])
        
        assert args.auto is True
        assert args.max_iterations == 5
        assert args.timeout == 20
        assert args.debug is True
        assert args.no_color is True

    def test_parse_no_plan_file(self):
        """Test parsing without plan file should fail."""
        with pytest.raises(SystemExit):
            parse_args([])


class TestMain:
    """Tests for main function."""

    @pytest.mark.asyncio
    async def test_main_success(self):
        """Test successful execution."""
        with patch('qwenex.cli.parse_args') as mock_parse, \
             patch('qwenex.cli.parse_plan_file') as mock_parse_plan, \
             patch('qwenex.cli.Orchestrator') as MockOrchestrator, \
             patch('qwenex.cli.setup_signal_handlers'):
            
            # Setup mocks
            mock_parse.return_value = argparse.Namespace(
                plan_file="docs/plans/feature.md",
                auto=False,
                interactive=False,
                max_iterations=3,
                timeout=10,
                debug=False,
                no_color=False
            )
            
            mock_plan = MagicMock()
            mock_plan.title = "Test Plan"
            mock_parse_plan.return_value = mock_plan
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.run = AsyncMock(return_value=MagicMock(
                tasks_completed=2,
                tasks_failed=0,
                validation_passed=True
            ))
            
            # Run main
            result = await main()
            
            assert result == 0
            mock_parse_plan.assert_called_once()
            mock_orchestrator.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_file_not_found(self):
        """Test execution with missing plan file."""
        with patch('qwenex.cli.parse_args') as mock_parse, \
             patch('qwenex.cli.parse_plan_file') as mock_parse_plan:
            
            mock_parse.return_value = argparse.Namespace(
                plan_file="nonexistent.md",
                auto=False,
                interactive=False,
                max_iterations=3,
                timeout=10,
                debug=False,
                no_color=False
            )
            
            mock_parse_plan.side_effect = FileNotFoundError("File not found")
            
            result = await main()
            
            assert result == 1

    @pytest.mark.asyncio
    async def test_main_orchestrator_error(self):
        """Test execution with orchestrator error."""
        with patch('qwenex.cli.parse_args') as mock_parse, \
             patch('qwenex.cli.parse_plan_file') as mock_parse_plan, \
             patch('qwenex.cli.Orchestrator') as MockOrchestrator, \
             patch('qwenex.cli.setup_signal_handlers'):
            
            mock_parse.return_value = argparse.Namespace(
                plan_file="docs/plans/feature.md",
                auto=False,
                max_iterations=3,
                timeout=10,
                debug=False,
                no_color=False
            )
            
            mock_plan = MagicMock()
            mock_parse_plan.return_value = mock_plan
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_orchestrator.run = MagicMock(side_effect=Exception("Orchestrator failed"))
            
            result = await main()
            
            assert result == 1


class TestSetupSignalHandlers:
    """Tests for signal handler setup."""

    def test_setup_signal_handlers(self):
        """Test signal handlers are set up."""
        with patch('qwenex.cli.signal.signal') as mock_signal:
            setup_signal_handlers()
            
            # Should register handlers for SIGINT and SIGTERM
            assert mock_signal.call_count >= 2
