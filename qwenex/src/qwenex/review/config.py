"""Configuration for review agents."""

from .models import ReviewAgent


# Prompt templates for each agent
AGENT_PROMPTS = {
    "quality": """You are a code quality reviewer. Review the following git diff for:
- Code style consistency (PEP 8 for Python)
- Best practices and design patterns
- Potential bugs and edge cases
- Security issues
- Performance concerns

Format findings as:
- [QUALITY-1] Brief description
- [QUALITY-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}
""",

    "implementation": """You are an implementation reviewer. Check if the code changes match the specification (FEAT/PROP).

Review criteria:
- Does the implementation match the spec requirements?
- Are all acceptance criteria met?
- Any missing functionality?
- Any over-engineering (YAGNI)?

Format findings as:
- [IMPL-1] Brief description
- [IMPL-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Specification:
{spec_content}

Git diff:
{git_diff}
""",

    "testing": """You are a testing reviewer. Review the test changes for:
- Test coverage (80%+ target)
- Test quality (specific, isolated, repeatable)
- Edge cases covered
- Mock/stub usage appropriate

Format findings as:
- [TEST-1] Brief description
- [TEST-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}

Test coverage report:
{coverage_report}
""",

    "simplification": """You are a simplification reviewer. Look for:
- Over-engineering (YAGNI violations)
- Complex code that can be simpler
- Duplicate code
- Unused code (dead code, unused imports)
- Opportunities for DRY

Format findings as:
- [SIMPL-1] Brief description
- [SIMPL-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}
""",

    "documentation": """You are a documentation reviewer. Check for:
- Missing docstrings (public API)
- Missing comments (complex logic)
- README/docs updates for new features
- CHANGELOG updates
- Inline comments (why, not what)

Format findings as:
- [DOC-1] Brief description
- [DOC-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.
Use format: <!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->

Git diff:
{git_diff}
""",
}


# Agent configurations
AGENT_CONFIGS = {
    "quality": ReviewAgent(
        name="quality",
        priority=1,
        critical=True,
        prompt_template=AGENT_PROMPTS["quality"],
    ),
    "implementation": ReviewAgent(
        name="implementation",
        priority=2,
        critical=True,
        prompt_template=AGENT_PROMPTS["implementation"],
    ),
    "testing": ReviewAgent(
        name="testing",
        priority=3,
        critical=False,
        prompt_template=AGENT_PROMPTS["testing"],
    ),
    "simplification": ReviewAgent(
        name="simplification",
        priority=4,
        critical=False,
        prompt_template=AGENT_PROMPTS["simplification"],
    ),
    "documentation": ReviewAgent(
        name="documentation",
        priority=5,
        critical=False,
        prompt_template=AGENT_PROMPTS["documentation"],
    ),
}


def get_agent_config(agent_name: str) -> ReviewAgent | None:
    """Get configuration for a specific review agent."""
    return AGENT_CONFIGS.get(agent_name)


def get_all_agents() -> list[ReviewAgent]:
    """Get all review agents sorted by priority."""
    return sorted(AGENT_CONFIGS.values(), key=lambda a: a.priority)


def get_critical_agents() -> list[ReviewAgent]:
    """Get critical agents (run in parallel)."""
    return [a for a in get_all_agents() if a.critical]


def get_sequential_agents() -> list[ReviewAgent]:
    """Get non-critical agents (run sequentially)."""
    return [a for a in get_all_agents() if not a.critical]
