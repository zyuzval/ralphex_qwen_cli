"""Config tools for MCP server."""

import json
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("qwenex-config")

CONFIG_PATH = Path(".qwenex/config.json")


def get_config() -> dict:
    """Load config from file.
    
    Returns:
        Config dict
    """
    if not CONFIG_PATH.exists():
        return {
            "auto_mode": False,
            "timeout": 10,
            "max_iterations": 3,
            "model": "qwen-max"
        }
    
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def set_config_value(key: str, value) -> bool:
    """Set config value.
    
    Args:
        key: Config key
        value: Config value
    
    Returns:
        True if successful
    """
    config = get_config()
    config[key] = value
    
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    return True


@mcp.tool()
async def config_get() -> dict:
    """
    Получить конфигурацию.
    
    Returns:
        config: dict with settings
    """
    try:
        return get_config()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def config_set(key: str, value) -> str:
    """
    Установить значение конфигурации.
    
    Args:
        key: Config key (auto_mode, timeout, max_iterations, model)
        value: Config value
    
    Returns:
        success message
    """
    try:
        set_config_value(key, value)
        return f"Updated {key} = {value}"
    except Exception as e:
        return f"Error: Failed to update config — {str(e)}"
