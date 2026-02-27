"""Tests for review agent configurations and prompts."""

import pytest
from qwenex.review.config import get_agent_config, AGENT_PROMPTS


def test_all_agents_configured():
    """Test all 5 agents are configured"""
    expected_agents = ["quality", "implementation", "testing", "simplification", "documentation"]
    
    for agent_name in expected_agents:
        config = get_agent_config(agent_name)
        assert config is not None, f"Agent {agent_name} not configured"
        assert config.name == agent_name
        assert config.prompt_template is not None
        assert len(config.prompt_template) > 50  # Reasonable prompt length


def test_agent_priorities():
    """Test agent priorities are correct (1-5)"""
    for agent_name in ["quality", "implementation", "testing", "simplification", "documentation"]:
        config = get_agent_config(agent_name)
        assert 1 <= config.priority <= 5


def test_critical_agents():
    """Test critical agents are marked correctly"""
    quality = get_agent_config("quality")
    implementation = get_agent_config("implementation")
    
    assert quality.critical is True
    assert implementation.critical is True
    
    # Non-critical
    testing = get_agent_config("testing")
    assert testing.critical is False


def test_quality_agent_prompt():
    """Test quality agent prompt contains required elements"""
    config = get_agent_config("quality")
    prompt = config.prompt_template
    
    assert "code quality reviewer" in prompt.lower()
    assert "PEP 8" in prompt
    assert "best practices" in prompt.lower()
    assert "security" in prompt.lower()
    assert "Git diff:" in prompt


def test_implementation_agent_prompt():
    """Test implementation agent prompt contains required elements"""
    config = get_agent_config("implementation")
    prompt = config.prompt_template
    
    assert "implementation reviewer" in prompt.lower()
    assert "specification" in prompt.lower()
    assert "acceptance criteria" in prompt.lower()
    assert "YAGNI" in prompt
    assert "Specification:" in prompt
    assert "Git diff:" in prompt


def test_testing_agent_prompt():
    """Test testing agent prompt contains required elements"""
    config = get_agent_config("testing")
    prompt = config.prompt_template
    
    assert "testing reviewer" in prompt.lower()
    assert "test coverage" in prompt.lower()
    assert "80%" in prompt
    assert "edge cases" in prompt.lower()
    assert "Git diff:" in prompt


def test_simplification_agent_prompt():
    """Test simplification agent prompt contains required elements"""
    config = get_agent_config("simplification")
    prompt = config.prompt_template
    
    assert "simplification reviewer" in prompt.lower()
    assert "YAGNI" in prompt
    assert "DRY" in prompt
    assert "duplicate code" in prompt.lower()
    assert "unused code" in prompt.lower()
    assert "Git diff:" in prompt


def test_documentation_agent_prompt():
    """Test documentation agent prompt contains required elements"""
    config = get_agent_config("documentation")
    prompt = config.prompt_template
    
    assert "documentation reviewer" in prompt.lower()
    assert "docstrings" in prompt.lower()
    assert "comments" in prompt.lower()
    assert "README" in prompt
    assert "Git diff:" in prompt


def test_agent_prompts_structure():
    """Test all prompts follow the same structure"""
    for agent_name, prompt in AGENT_PROMPTS.items():
        # All prompts should end with Git diff placeholder
        assert "Git diff:" in prompt or "{git_diff}" in prompt
        
        # All prompts should mention REVIEW marker format
        assert "REVIEW" in prompt or "<!-- REVIEW:" in prompt
