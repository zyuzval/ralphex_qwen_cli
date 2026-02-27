"""Git tools for MCP server."""

from fastmcp import FastMCP
from qwenex.git_wrapper import GitWrapper, GitError

mcp = FastMCP("qwenex-git")


@mcp.tool()
async def git_status() -> dict:
    """
    Статус репозитория.
    
    Returns:
        status: dict with is_clean, branch, changed_files
    """
    try:
        git = GitWrapper()
        status = git.status()
        
        return {
            "is_clean": status.is_clean,
            "branch": status.branch,
            "changed_files": status.changed_files
        }
    except GitError as e:
        return {"error": str(e)}


@mcp.tool()
async def git_commit(message: str, files: list[str]) -> str:
    """
    Создать git commit.
    
    Args:
        message: Commit message
        files: List of files to commit
    
    Returns:
        commit_hash: Short hash (7 chars)
    """
    try:
        git = GitWrapper()
        git.add(files)
        git.commit(message)
        
        return git.last_commit_hash()
    except GitError as e:
        return f"Error: Git commit failed — {str(e)}"


@mcp.tool()
async def git_create_worktree(branch: str, path: str) -> str:
    """
    Создать worktree для ветки.
    
    Args:
        branch: Branch name
        path: Path for worktree
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.create_worktree(branch, path)
        return f"Worktree created at {path}"
    except GitError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def git_remove_worktree(path: str) -> str:
    """
    Удалить worktree.
    
    Args:
        path: Path to worktree
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.remove_worktree(path)
        return f"Worktree removed at {path}"
    except GitError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def git_diff_head() -> str:
    """
    Diff от HEAD.
    
    Returns:
        diff: Git diff string
    """
    try:
        git = GitWrapper()
        return git.diff_head()
    except GitError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def git_merge(branch: str) -> str:
    """
    Merge ветки.
    
    Args:
        branch: Branch to merge
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.merge(branch)
        return f"Merged {branch}"
    except GitError as e:
        return f"Error: Merge failed — {str(e)}"


@mcp.tool()
async def git_ensure_ignored(patterns: list[str]) -> str:
    """
    Добавить паттерны в .gitignore.
    
    Args:
        patterns: List of glob patterns
    
    Returns:
        success message
    """
    try:
        git = GitWrapper()
        git.ensure_git_ignored(patterns)
        return f"Added {len(patterns)} patterns to .gitignore"
    except GitError as e:
        return f"Error: {str(e)}"
