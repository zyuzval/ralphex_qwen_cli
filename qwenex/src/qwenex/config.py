"""Configuration management for Qwenex."""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .models.base import ProviderConfig


@dataclass
class ProviderSettings:
    """Settings for a single provider."""

    name: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
    timeout_sec: int = 600
    extra: dict[str, str] = field(default_factory=dict)

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
    providers: dict[str, ProviderSettings] = field(default_factory=dict)
    timeout_sec: int = 600
    max_retries: int = 2
    review_iterations: int = 3

    def get_provider(self, name: str) -> ProviderSettings | None:
        """Get provider settings by name."""
        return self.providers.get(name)


def get_config_path() -> Path:
    """Get path to configuration file."""
    config_dir = Path.home() / ".qwenex"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config(config_path: Path | None = None) -> QwenexConfig:
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


def save_config(config: QwenexConfig, config_path: Path | None = None) -> None:
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
