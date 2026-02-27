"""Hybrid executor for review agents (2 parallel + 3 sequential)."""

import asyncio
import logging
import time

from ..qwen_executor import QwenExecutor
from .config import (
    get_agent_config,
    get_critical_agents,
    get_sequential_agents,
)
from .models import ReviewMarker, ReviewReport, ReviewResult

logger = logging.getLogger(__name__)


class HybridExecutor:
    """Hybrid executor for review agents.

    Phase 1: Run critical agents in parallel (quality, implementation)
    Phase 2: Run non-critical agents sequentially (testing, simplification, documentation)
    """

    def __init__(self, qwen_executor: QwenExecutor | None = None):
        self.qwen_executor = qwen_executor or QwenExecutor()
        self.timeout_min = 5  # Default timeout per agent

    async def run_agent(
        self,
        agent_name: str,
        git_diff: str,
        spec_content: str = "",
        coverage_report: str = "",
    ) -> ReviewResult:
        """Run a single review agent with timeout and error handling."""
        config = get_agent_config(agent_name)
        if config is None:
            logger.error(f"Unknown agent: {agent_name}")
            return self._empty_result(agent_name)

        # Render prompt
        prompt = config.prompt_template.format(
            git_diff=git_diff,
            spec_content=spec_content,
            coverage_report=coverage_report,
        )

        start_time = time.time()

        try:
            # Run agent with timeout
            output = await asyncio.wait_for(
                self.qwen_executor.run_task(prompt),
                timeout=self.timeout_min * 60,
            )

            # Parse REVIEW markers
            markers = ReviewMarker.parse_from_output(output)

            # Parse findings (lines starting with - [AGENT-])
            findings = self._parse_findings(output, agent_name.upper())

            duration_sec = time.time() - start_time

            logger.info(f"Agent {agent_name} completed in {duration_sec:.1f}s")

            return ReviewResult(
                agent=agent_name,
                success=True,
                findings=findings,
                review_markers=[m.raw for m in markers],
                output=output,
                duration_sec=duration_sec,
            )

        except TimeoutError:
            logger.warning(f"Agent {agent_name} timed out after {self.timeout_min} minutes")
            return ReviewResult(
                agent=agent_name,
                success=False,
                findings=[f"Agent timed out after {self.timeout_min} minutes"],
                review_markers=[],
                output="",
                duration_sec=self.timeout_min * 60,
            )

        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            return ReviewResult(
                agent=agent_name,
                success=False,
                findings=[f"Agent failed: {str(e)}"],
                review_markers=[],
                output="",
                duration_sec=time.time() - start_time,
            )

    async def run_phase1(self, session_id: str, git_diff: str) -> list[ReviewResult]:
        """Phase 1: Run critical agents in parallel.

        Returns list of ReviewResult from quality and implementation agents.
        """
        critical_agents = get_critical_agents()
        logger.info(f"Phase 1: Running {len(critical_agents)} critical agents in parallel")

        # Run critical agents in parallel
        tasks = [
            self.run_agent(agent.name, git_diff)
            for agent in critical_agents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {critical_agents[i].name} failed: {result}")
                processed_results.append(self._empty_result(critical_agents[i].name))
            else:
                processed_results.append(result)

        return processed_results

    async def run_phase2(self, session_id: str, git_diff: str) -> list[ReviewResult]:
        """Phase 2: Run non-critical agents sequentially.

        Returns list of ReviewResult from testing, simplification, documentation agents.
        """
        sequential_agents = get_sequential_agents()
        logger.info(f"Phase 2: Running {len(sequential_agents)} agents sequentially")

        results = []
        for agent in sequential_agents:
            result = await self.run_agent(agent.name, git_diff)
            results.append(result)

        return results

    async def run_review(
        self,
        session_id: str,
        git_diff: str,
        spec_content: str = "",
        coverage_report: str = "",
        agents: list[str] | None = None,
    ) -> ReviewReport:
        """Run full review (Phase 1 + Phase 2).

        Args:
            session_id: Session identifier
            git_diff: Git diff to review
            spec_content: Optional spec content for implementation agent
            coverage_report: Optional coverage report for testing agent
            agents: Optional list of specific agents to run (default: all)

        Returns:
            ReviewReport with all results

        """
        logger.info(f"Starting review for session {session_id}")

        # If specific agents requested, filter
        if agents:
            all_results = []
            for agent_name in agents:
                result = await self.run_agent(agent_name, git_diff, spec_content, coverage_report)
                all_results.append(result)
        else:
            # Run hybrid execution
            phase1_results = await self.run_phase1(session_id, git_diff)
            phase2_results = await self.run_phase2(session_id, git_diff)
            all_results = phase1_results + phase2_results

        # Aggregate markers
        all_markers = []
        for result in all_results:
            all_markers.extend(ReviewMarker.parse_from_output(result.output))

        # Detect conflicts
        conflicts = self._detect_conflicts(all_results)

        # Generate summary
        total_findings = sum(len(r.findings) for r in all_results)
        successful_agents = sum(1 for r in all_results if r.success)

        summary = (
            f"Review completed: {successful_agents}/{len(all_results)} agents successful, "
            f"{total_findings} findings, {len(all_markers)} REVIEW markers"
        )

        return ReviewReport(
            session_id=session_id,
            git_diff=git_diff,
            results=all_results,
            aggregated_markers=all_markers,
            conflicts=conflicts,
            summary=summary,
        )

    def _parse_findings(self, output: str, agent_prefix: str) -> list[str]:
        """Parse findings from agent output (lines like - [AGENT-1] Description)."""
        findings = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith(f"- [{agent_prefix}-"):
                # Extract finding text
                finding = line.split("] ", 1)[-1] if "] " in line else line
                findings.append(finding)
        return findings

    def _empty_result(self, agent_name: str) -> ReviewResult:
        """Create empty result for failed agent."""
        return ReviewResult(
            agent=agent_name,
            success=False,
            findings=[],
            review_markers=[],
            output="",
            duration_sec=0.0,
        )

    def _detect_conflicts(self, results: list[ReviewResult]) -> list[str]:
        """Detect conflicting recommendations between agents."""
        conflicts = []

        # Example: quality vs simplification conflicts
        quality_result = next((r for r in results if r.agent == "quality"), None)
        simpl_result = next((r for r in results if r.agent == "simplification"), None)

        if quality_result and simpl_result:
            # Heuristic: if quality suggests adding code and simplification suggests removing
            quality_adds = any("add" in f.lower() for f in quality_result.findings)
            simpl_removes = any("remove" in f.lower() or "delete" in f.lower() for f in simpl_result.findings)

            if quality_adds and simpl_removes:
                conflicts.append("quality vs simplification: conflicting recommendations (add vs remove)")

        return conflicts
