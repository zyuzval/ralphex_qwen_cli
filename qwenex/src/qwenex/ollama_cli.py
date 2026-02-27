"""CLI for Ollama local models."""

import argparse
import asyncio
import sys
from typing import Optional

from .models.base import ProviderConfig
from .models.ollama import OllamaProvider


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
