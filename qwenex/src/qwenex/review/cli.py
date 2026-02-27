"""CLI interface for review system."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click

from .hybrid_executor import HybridExecutor
from .aggregator import ReviewAggregator

logger = logging.getLogger(__name__)


@click.command()
@click.option("--session", "-s", help="Session ID for review")
@click.option("--diff", "-d", type=click.Path(exists=True), help="Path to diff file")
@click.option("--auto", "-a", is_flag=True, help="Auto-approve non-critical REVIEW markers")
@click.option("--interactive", "-i", is_flag=True, help="Interactive approval mode")
@click.option("--agents", "-g", help="Specific agents to run (comma-separated)")
@click.option("--timeout", "-t", type=int, default=5, help="Timeout per agent (minutes)")
async def review_command(
    session: Optional[str],
    diff: Optional[str],
    auto: bool,
    interactive: bool,
    agents: Optional[str],
    timeout: int,
):
    """
    Run code review with 5 AI agents.
    
    Hybrid execution: 2 critical agents in parallel + 3 sequential.
    
    Examples:
    
        qwenex review --session test-123
        
        qwenex review --diff changes.patch
        
        qwenex review --session test-123 --auto
        
        qwenex review --session test-123 --agents quality,testing
    """
    # Validate arguments
    if not session and not diff:
        click.echo("Error: Either --session or --diff is required")
        return
    
    # Read git diff
    if diff:
        git_diff = Path(diff).read_text()
    else:
        # TODO: Get diff from session (requires session storage)
        git_diff = ""
        click.echo(f"Warning: Session-based diff not implemented yet")
    
    # Parse agents list
    agent_list = None
    if agents:
        agent_list = [a.strip() for a in agents.split(",")]
    
    # Run review
    click.echo(f"Starting review (timeout: {timeout} min per agent)...")
    
    executor = HybridExecutor()
    executor.timeout_min = timeout
    
    report = await executor.run_review(
        session_id=session or "cli-review",
        git_diff=git_diff,
        agents=agent_list,
    )
    
    # Print summary
    click.echo("\n" + "=" * 60)
    click.echo("REVIEW SUMMARY")
    click.echo("=" * 60)
    click.echo(report.summary)
    
    # Print findings by agent
    click.echo("\nFINDINGS BY AGENT:")
    for result in report.results:
        status = "✅" if result.success else "❌"
        click.echo(f"\n{status} {result.agent.upper()} ({result.duration_sec:.1f}s):")
        for finding in result.findings:
            click.echo(f"  - {finding}")
    
    # Print REVIEW markers
    if report.aggregated_markers:
        click.echo("\n" + "=" * 60)
        click.echo("REVIEW MARKERS")
        click.echo("=" * 60)
        
        for i, marker in enumerate(report.aggregated_markers, 1):
            click.echo(f"\n[{i}] {marker.suggestion}")
            click.echo(f"    Reason: {marker.reason}")
            click.echo(f"    Awaits: {marker.awaits}")
            
            if auto and not marker.critical:
                click.echo(f"    Status: AUTO-APPROVED")
            elif interactive:
                # Interactive approval (TODO: implement)
                click.echo(f"    Status: PENDING (interactive not implemented)")
    
    # Print conflicts
    if report.conflicts:
        click.echo("\n" + "=" * 60)
        click.echo("CONFLICTS DETECTED")
        click.echo("=" * 60)
        for conflict in report.conflicts:
            click.echo(f"  ⚠️  {conflict}")
    
    click.echo("\n" + "=" * 60)
