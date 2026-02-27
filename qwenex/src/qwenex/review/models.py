"""Data models for review system."""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class ReviewAgent:
    """Configuration for a review agent."""
    name: str
    priority: int  # 1 (highest) - 5 (lowest)
    critical: bool  # Critical agents run in parallel
    prompt_template: str  # Prompt template for the agent


@dataclass
class ReviewResult:
    """Result from a single review agent."""
    agent: str
    success: bool
    findings: list[str]
    review_markers: list[str]
    output: str
    duration_sec: float


@dataclass
class ReviewMarker:
    """Parsed REVIEW marker from agent output."""
    suggestion: str
    reason: str
    awaits: str
    raw: str
    critical: bool = False
    
    @classmethod
    def parse_from_output(cls, output: str) -> list["ReviewMarker"]:
        """Parse all REVIEW markers from agent output."""
        # Match single-line REVIEW markers
        pattern = r'<!-- REVIEW: ([^-]+) — причина: ([^-]+) — ждёт: ([^-]+) -->'
        markers = []
        
        for match in re.finditer(pattern, output):
            suggestion, reason, awaits = match.groups()
            markers.append(cls(
                suggestion=suggestion.strip(),
                reason=reason.strip(),
                awaits=awaits.strip(),
                raw=match.group(0),
                critical="критичных" in awaits.lower() or "critical" in awaits.lower()
            ))
        
        return markers


@dataclass
class ReviewReport:
    """Complete review report for a session."""
    session_id: str
    git_diff: str
    results: list[ReviewResult]
    aggregated_markers: list[ReviewMarker]
    conflicts: list[str]
    summary: str
