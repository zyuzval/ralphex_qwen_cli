"""Aggregator for review results."""

import logging
from typing import Optional

from .models import ReviewResult, ReviewMarker, ReviewReport
from .config import get_agent_config

logger = logging.getLogger(__name__)


class ReviewAggregator:
    """
    Aggregates results from multiple review agents.
    
    Responsibilities:
    - Collect REVIEW markers from all agents
    - Prioritize markers by agent priority
    - Detect conflicts between agents
    - Generate summary report
    """
    
    def aggregate_markers(self, results: list[ReviewResult]) -> list[ReviewMarker]:
        """
        Aggregate all REVIEW markers from agent results.
        
        Returns flat list of all markers from all agents.
        """
        all_markers = []
        for result in results:
            markers = ReviewMarker.parse_from_output(result.output)
            all_markers.extend(markers)
        
        logger.info(f"Aggregated {len(all_markers)} REVIEW markers from {len(results)} agents")
        return all_markers
    
    def prioritize_markers(self, markers: list[ReviewMarker]) -> list[ReviewMarker]:
        """
        Prioritize markers by agent priority.
        
        Markers from higher-priority agents (quality, implementation) come first.
        """
        # Group markers by agent (need to track which agent produced which marker)
        # For now, just return as-is since markers don't track source agent
        # TODO: Enhance ReviewMarker to track source agent
        return markers
    
    def detect_conflicts(self, results: list[ReviewResult]) -> list[str]:
        """
        Detect conflicting recommendations between agents.
        
        Uses heuristics to find conflicts like:
        - quality suggests adding code, simplification suggests removing
        - implementation requires feature, simplification calls it YAGNI
        """
        conflicts = []
        
        # Build findings by agent
        findings_by_agent = {}
        for result in results:
            findings_by_agent[result.agent] = result.findings
        
        # Check quality vs simplification
        if "quality" in findings_by_agent and "simplification" in findings_by_agent:
            quality_findings = " ".join(findings_by_agent["quality"]).lower()
            simpl_findings = " ".join(findings_by_agent["simplification"]).lower()
            
            # Heuristic: quality adds, simplification removes
            if ("add" in quality_findings or "implement" in quality_findings) and \
               ("remove" in simpl_findings or "delete" in simpl_findings):
                conflicts.append("quality vs simplification: conflicting recommendations")
        
        # Check implementation vs simplification
        if "implementation" in findings_by_agent and "simplification" in findings_by_agent:
            impl_findings = " ".join(findings_by_agent["implementation"]).lower()
            simpl_findings = " ".join(findings_by_agent["simplification"]).lower()
            
            # Heuristic: implementation requires, simplification calls YAGNI
            if ("require" in impl_findings or "must" in impl_findings) and \
               ("yagni" in simpl_findings or "unnecessary" in simpl_findings):
                conflicts.append("implementation vs simplification: YAGNI conflict")
        
        logger.info(f"Detected {len(conflicts)} conflicts")
        return conflicts
    
    def generate_summary(self, results: list[ReviewResult]) -> str:
        """
        Generate human-readable summary of review results.
        """
        total_agents = len(results)
        successful_agents = sum(1 for r in results if r.success)
        total_findings = sum(len(r.findings) for r in results)
        total_markers = sum(len(r.review_markers) for r in results)
        
        # Find critical issues
        critical_agents_failed = sum(
            1 for r in results if not r.success and r.agent in ["quality", "implementation"]
        )
        
        summary_parts = [
            f"{successful_agents}/{total_agents} agents successful",
            f"{total_findings} findings",
            f"{total_markers} REVIEW markers",
        ]
        
        if critical_agents_failed > 0:
            summary_parts.append(f"⚠️ {critical_agents_failed} critical agents failed")
        
        return ", ".join(summary_parts)
    
    def generate_report(
        self,
        session_id: str,
        git_diff: str,
        results: list[ReviewResult],
    ) -> ReviewReport:
        """
        Generate full review report.
        """
        # Aggregate markers
        all_markers = self.aggregate_markers(results)
        
        # Detect conflicts
        conflicts = self.detect_conflicts(results)
        
        # Generate summary
        summary = self.generate_summary(results)
        
        return ReviewReport(
            session_id=session_id,
            git_diff=git_diff,
            results=results,
            aggregated_markers=all_markers,
            conflicts=conflicts,
            summary=summary,
        )
