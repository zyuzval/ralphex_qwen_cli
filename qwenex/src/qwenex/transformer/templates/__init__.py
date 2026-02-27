"""Transformer templates package."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


class TemplateError(Exception):
    """Template loading error."""
    pass


def load_template(name: str) -> str:
    """Load template by name.
    
    Args:
        name: Template name (feat, prop)
        
    Returns:
        Template content
        
    Raises:
        TemplateError: If template not found
    """
    template_path = TEMPLATES_DIR / f"{name}_template.md"
    
    if not template_path.exists():
        raise TemplateError(f"Template '{name}' not found")
    
    return template_path.read_text(encoding="utf-8")
