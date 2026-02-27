"""Tests for Git MCP tools."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_git_status():
    """Test getting git status"""
    from qwenex.mcp.tools.git import git_status
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        mock_git.status.return_value = MagicMock(
            is_clean=True,
            branch="main",
            changed_files=[]
        )
        MockGit.return_value = mock_git
        
        result = await git_status()
        
        assert result["is_clean"] is True
        assert result["branch"] == "main"


@pytest.mark.asyncio
async def test_git_status_error():
    """Test git status with error"""
    from qwenex.mcp.tools.git import git_status
    from qwenex.git_wrapper import GitError
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        MockGit.side_effect = GitError("Not a git repo")
        
        result = await git_status()
        
        assert "error" in result


@pytest.mark.asyncio
async def test_git_commit():
    """Test git commit"""
    from qwenex.mcp.tools.git import git_commit
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        mock_git.last_commit_hash.return_value = "abc1234"
        MockGit.return_value = mock_git
        
        result = await git_commit("feat: test", ["file.py"])
        
        assert result == "abc1234"


@pytest.mark.asyncio
async def test_git_commit_error():
    """Test git commit with error"""
    from qwenex.mcp.tools.git import git_commit
    from qwenex.git_wrapper import GitError
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        mock_git.add.side_effect = GitError("File not found")
        MockGit.return_value = mock_git
        
        result = await git_commit("feat: test", ["file.py"])
        
        assert "Error" in result


@pytest.mark.asyncio
async def test_git_diff_head():
    """Test git diff from HEAD"""
    from qwenex.mcp.tools.git import git_diff_head
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        mock_git.diff_head.return_value = "diff --git..."
        MockGit.return_value = mock_git
        
        result = await git_diff_head()
        
        assert result.startswith("diff --git")


@pytest.mark.asyncio
async def test_git_ensure_ignored():
    """Test git ensure ignored"""
    from qwenex.mcp.tools.git import git_ensure_ignored
    
    with patch("qwenex.mcp.tools.git.GitWrapper") as MockGit:
        mock_git = MagicMock()
        MockGit.return_value = mock_git
        
        result = await git_ensure_ignored(["*.pyc", "__pycache__/"])
        
        assert "Added" in result
        assert "2" in result
