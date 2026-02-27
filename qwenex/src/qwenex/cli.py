"""CLI interface for Qwenex."""

import argparse
import asyncio
import signal
import sys
from typing import Optional

from .plan_parser import parse_plan_file
from .orchestrator import Orchestrator
from .models.base import ProviderConfig
from .models.factory import ProviderFactory
from .models.fallback import FallbackProvider
from .review.cli import review_command as review_cmd


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Arguments to parse (default: sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="qwenex",
        description="Autonomous plan execution with Qwen CLI"
    )

    parser.add_argument(
        "plan_file",
        help="Path to the markdown plan file"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto mode: auto-approve review markers"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode: pause on review markers"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Max retry iterations per task (default: 3)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout per task in minutes (default: 10)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
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
        "--fallback",
        type=str,
        default=None,
        help="Fallback provider (e.g., qwen_cloud when using ollama)"
    )

    return parser.parse_args(args)


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


async def main(args: Optional[list] = None) -> int:
    """Main entry point.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parsed_args = parse_args(args)

    # Setup signal handlers
    setup_signal_handlers()

    # Parse plan file
    try:
        plan = parse_plan_file(parsed_args.plan_file)
        print(f"Loaded plan: {plan.title}")
        print(f"Tasks: {len(plan.tasks)}")
        print(f"Validation commands: {len(plan.validation_commands)}")
    except FileNotFoundError:
        print(f"Error: Plan file not found: {parsed_args.plan_file}")
        return 1
    except Exception as e:
        print(f"Error parsing plan: {e}")
        return 1

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

    # Create provider with optional fallback
    try:
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
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Create orchestrator
    orchestrator = Orchestrator(
        plan=plan,
        provider=provider,
        max_iterations=parsed_args.max_iterations,
        timeout_min=parsed_args.timeout,
        auto_mode=parsed_args.auto,
    )

    # Run orchestration
    try:
        result = await orchestrator.run()
        print(f"\n{result}")
        print(f"Validation: {'PASSED' if result.validation_passed else 'FAILED'}")
        
        if result.review_markers:
            print(f"\nReview markers found: {len(result.review_markers)}")
            for marker in result.review_markers:
                print(f"  - {marker}")

        return 0 if result.validation_passed else 1

    except Exception as e:
        print(f"\nError during execution: {e}")
        if parsed_args.debug:
            import traceback
            traceback.print_exc()
        return 1


def entry_point():
    """Console script entry point."""
    sys.exit(asyncio.run(main()))


def review_entry_point():
    """Review command entry point."""
    review_cmd()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
