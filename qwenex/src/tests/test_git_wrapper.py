"""Tests for git wrapper."""

import pytest
import tempfile
import os
import subprocess
from qwenex.git_wrapper import GitWrapper, GitError, GitStatus


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            # Initialize git repo
            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
            # Create initial commit so HEAD exists
            with open("README.md", "w") as f:
                f.write("# Test")
            subprocess.run(["git", "add", "README.md"], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)
            yield tmpdir
        finally:
            os.chdir(old_cwd)


class TestGitStatus:
    """Tests for GitStatus dataclass."""

    def test_git_status_str_clean(self):
        """Test GitStatus string representation."""
        status = GitStatus(is_clean=True, branch="main", changed_files=[])
        assert "clean" in str(status).lower()

    def test_git_status_str_dirty(self):
        """Test GitStatus string representation with changes."""
        status = GitStatus(is_clean=False, branch="main", changed_files=["file.txt"])
        assert "dirty" in str(status).lower() or "changed" in str(status).lower()


class TestGitWrapper:
    """Tests for GitWrapper class."""

    def test_git_status_clean(self, temp_git_repo):
        """Test git status on clean repo."""
        git = GitWrapper()
        status = git.status()

        assert status.is_clean is True
        assert status.branch in ["master", "main"]

    def test_git_status_dirty(self, temp_git_repo):
        """Test git status with uncommitted changes."""
        # Create a file
        with open("test.txt", "w") as f:
            f.write("test")

        git = GitWrapper()
        status = git.status()

        assert status.is_clean is False

    def test_git_add(self, temp_git_repo):
        """Test git add."""
        # Create a file
        with open("test.txt", "w") as f:
            f.write("test")

        git = GitWrapper()
        git.add(["test.txt"])

        status = git.status()
        # File should be staged
        assert "test.txt" in status.changed_files or status.is_clean is True

    def test_git_commit(self, temp_git_repo):
        """Test git commit."""
        # Create and stage a file
        with open("test.txt", "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "test.txt"], check=True, capture_output=True)

        git = GitWrapper()
        git.commit("Test commit")

        status = git.status()
        assert status.is_clean is True

    def test_git_commit_nothing(self, temp_git_repo):
        """Test git commit with nothing staged."""
        git = GitWrapper()
        
        # Should not raise, but may fail gracefully
        with pytest.raises(GitError):
            git.commit("Empty commit")

    def test_ensure_git_ignored(self, temp_git_repo):
        """Test ensure_git_ignored pattern."""
        git = GitWrapper()

        # Add a pattern
        git.ensure_git_ignored(["*.tmp", ".cache/"])

        # Check .gitignore contains patterns
        with open(".gitignore", "r") as f:
            content = f.read()

        assert "*.tmp" in content
        assert ".cache/" in content

    def test_ensure_git_ignored_appends(self, temp_git_repo):
        """Test ensure_git_ignored appends to existing .gitignore."""
        git = GitWrapper()
        
        # First call
        git.ensure_git_ignored(["*.tmp"])
        
        # Second call
        git.ensure_git_ignored(["*.log"])
        
        with open(".gitignore", "r") as f:
            content = f.read()
        
        assert "*.tmp" in content
        assert "*.log" in content

    def test_git_create_worktree(self, temp_git_repo):
        """Test git worktree creation."""
        # Get current branch name (master or main)
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                check=True, capture_output=True, text=True)
        current_branch = result.stdout.strip()
        
        # Create a branch
        subprocess.run(["git", "checkout", "-b", "test-branch"], check=True, capture_output=True)
        subprocess.run(["git", "checkout", current_branch], check=True, capture_output=True)

        git = GitWrapper()
        worktree_path = os.path.join(temp_git_repo, "wt-test")

        git.create_worktree("test-branch", worktree_path)

        assert os.path.exists(worktree_path)
        assert os.path.isdir(worktree_path)


class TestGitError:
    """Tests for GitError exception."""

    def test_git_error_message(self):
        """Test GitError message."""
        error = GitError("Something went wrong")
        assert str(error) == "Something went wrong"
