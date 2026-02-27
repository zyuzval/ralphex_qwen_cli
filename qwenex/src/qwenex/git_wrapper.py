"""Git operations wrapper using subprocess."""

import subprocess
from dataclasses import dataclass
from typing import List
from pathlib import Path


class GitError(Exception):
    """Git operation error."""
    pass


@dataclass
class GitStatus:
    """Git repository status."""
    is_clean: bool
    branch: str
    changed_files: List[str]

    def __str__(self) -> str:
        if self.is_clean:
            return f"Git status: clean on branch {self.branch}"
        else:
            return f"Git status: dirty on branch {self.branch} (changed: {', '.join(self.changed_files)})"


class GitWrapper:
    """Wrapper for git CLI operations."""

    def __init__(self, repo_path: str | None = None):
        """Initialize git wrapper.

        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def _run(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run git command.

        Args:
            args: Git arguments (without 'git')
            check: Raise GitError on non-zero exit

        Returns:
            CompletedProcess instance

        Raises:
            GitError: If command fails and check=True
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if check and result.returncode != 0:
                raise GitError(f"Git command failed: {result.stderr.strip()}")
            return result
        except subprocess.SubprocessError as e:
            if check:
                raise GitError(str(e))
            raise

    def status(self) -> GitStatus:
        """Get git status.

        Returns:
            GitStatus with current branch and changed files
        """
        # Get current branch
        branch_result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        branch = branch_result.stdout.strip()

        # Get status
        status_result = self._run(["status", "--porcelain"])
        lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

        changed_files = []
        for line in lines:
            if line.strip():
                # Parse porcelain format: XY filename
                parts = line.split()
                if len(parts) >= 2:
                    changed_files.append(parts[-1])

        is_clean = len(changed_files) == 0

        return GitStatus(
            is_clean=is_clean,
            branch=branch,
            changed_files=changed_files
        )

    def add(self, files: List[str]) -> None:
        """Stage files.

        Args:
            files: List of files to stage
        """
        self._run(["add"] + files)

    def commit(self, message: str) -> None:
        """Create commit.

        Args:
            message: Commit message

        Raises:
            GitError: If commit fails
        """
        self._run(["commit", "-m", message])

    def ensure_git_ignored(self, patterns: List[str]) -> None:
        """Ensure patterns are in .gitignore.

        Args:
            patterns: List of glob patterns to add
        """
        gitignore_path = self.repo_path / ".gitignore"

        # Read existing patterns
        existing = set()
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing = set(line.strip() for line in f if line.strip())

        # Add new patterns
        new_patterns = [p for p in patterns if p not in existing]
        if new_patterns:
            with open(gitignore_path, 'a') as f:
                for pattern in new_patterns:
                    f.write(f"{pattern}\n")

    def create_worktree(self, branch: str, path: str) -> None:
        """Create a worktree for a branch.

        Args:
            branch: Branch name
            path: Path for worktree

        Raises:
            GitError: If worktree creation fails
        """
        self._run(["worktree", "add", path, branch])

    def diff_head(self) -> str:
        """Get git diff from HEAD.

        Returns:
            Git diff string
        """
        result = self._run(["diff", "HEAD"])
        return result.stdout

    def last_commit_hash(self) -> str:
        """Get short hash of last commit.

        Returns:
            Short commit hash
        """
        result = self._run(["rev-parse", "--short", "HEAD"])
        return result.stdout.strip()

    def remove_worktree(self, path: str) -> None:
        """Remove a worktree.

        Args:
            path: Path to worktree

        Raises:
            GitError: If removal fails
        """
        self._run(["worktree", "remove", "--force", path])

    def merge(self, branch: str) -> None:
        """Merge a branch.

        Args:
            branch: Branch name to merge

        Raises:
            GitError: If merge fails
        """
        self._run(["merge", branch])

    def apply_fix(self, suggestion: str) -> None:
        """Apply a review marker fix (placeholder).

        Args:
            suggestion: Fix suggestion from review marker

        Note:
            This is a placeholder for future implementation.
            Actual fix application requires AI assistance.
        """
        # TODO: Implement actual fix application
        # For now, just log the suggestion
        pass
