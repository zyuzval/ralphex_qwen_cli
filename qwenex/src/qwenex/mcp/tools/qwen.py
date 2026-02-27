"""Qwen tools for MCP server."""

from fastmcp import FastMCP
from qwenex.qwen_executor import QwenExecutor

mcp = FastMCP("qwenex-qwen")


@mcp.tool()
async def qwen_run_task(prompt: str, model: str = "qwen-max") -> str:
    """
    Выполнить задачу через Qwen CLI.
    
    Args:
        prompt: Task prompt
        model: Model name (default: qwen-max)
    
    Returns:
        output: Qwen CLI output
    """
    executor = QwenExecutor()
    
    output_lines = []
    async for event in executor.run_task(prompt):
        output_lines.append(str(event))
    
    return "\n".join(output_lines)


@mcp.tool()
async def qwen_check_health() -> dict:
    """
    Проверить доступность Qwen CLI.
    
    Returns:
        health: dict with healthy, version
    """
    try:
        executor = QwenExecutor()
        healthy = await executor.check_health()
        return {"healthy": healthy, "version": "0.10.6+"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


@mcp.tool()
async def qwen_get_models() -> list:
    """
    Список доступных моделей.
    
    Returns:
        models: list of model dicts
    """
    return [
        {"name": "qwen-max", "context_window": 256000, "max_output": 8192},
        {"name": "qwen-plus", "context_window": 131000, "max_output": 8192},
        {"name": "qwen-turbo", "context_window": 32000, "max_output": 8192},
    ]
