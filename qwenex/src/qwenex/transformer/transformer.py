"""Transform simple plans to FEAT/PROP specifications."""

import json
from typing import Optional, Any
from jinja2 import Template

from ..models.base import LLMProvider, ProviderConfig
from ..models.factory import ProviderFactory
from .templates import load_template, TemplateError


class TransformError(Exception):
    """Transformation error."""
    pass


class PlanTransformer:
    """Transform simple plans to structured specifications."""
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        provider_config: Optional[ProviderConfig] = None,
    ):
        """Initialize transformer.
        
        Args:
            provider: LLM provider instance
            provider_config: Provider configuration
        """
        if provider is not None:
            self.provider = provider
        elif provider_config is not None:
            self.provider = ProviderFactory.create(
                provider_config.name,
                provider_config
            )
        else:
            self.provider, _ = ProviderFactory.create_from_env()
    
    async def transform(
        self,
        simple_plan: str,
        spec_number: str,
        spec_type: str = "FEAT",
        module: str = "module",
        **kwargs: Any
    ) -> str:
        """Transform simple plan to specification.
        
        Args:
            simple_plan: Simple markdown plan
            spec_number: Specification number (e.g., "001")
            spec_type: Type of specification (FEAT, PROP)
            module: Module name for URI
            **kwargs: Additional template variables
            
        Returns:
            Generated specification markdown
            
        Raises:
            TransformError: If transformation fails
        """
        # Load appropriate template
        template_name = spec_type.lower()
        try:
            template_str = load_template(template_name)
        except TemplateError as e:
            raise TransformError(f"Template error: {e}")
        
        # Build prompt for LLM
        prompt = self._build_transform_prompt(
            simple_plan, spec_number, spec_type, module
        )
        
        # Get structured data from LLM
        response = await self.provider.complete(prompt)
        
        # Parse LLM response to extract structured data
        data = self._parse_llm_response(response, spec_type)
        
        # Add standard fields
        data["number"] = spec_number
        data["module"] = module
        
        # Merge with kwargs
        data.update(kwargs)
        
        # Render template
        template = Template(template_str)
        return template.render(**data)
    
    def _build_transform_prompt(
        self,
        simple_plan: str,
        spec_number: str,
        spec_type: str,
        module: str
    ) -> str:
        """Build prompt for LLM transformation.
        
        Args:
            simple_plan: Simple plan to transform
            spec_number: Specification number
            spec_type: Type of specification
            module: Module name
            
        Returns:
            Prompt string
        """
        return f"""Transform this simple plan into a structured {spec_type} specification.

**Input Plan:**
{simple_plan}

**Output Format:**
Extract the following information and return as JSON:

For FEAT:
{{
    "title": "Specification title",
    "goal": "One sentence goal",
    "scenarios": ["Scenario 1", "Scenario 2"],
    "requirements": [{{"name": "Req name", "description": "Description", "why": "Why needed"}}],
    "out_of_scope": ["Item 1"],
    "tests": [{{"name": "test_name", "description": "What it tests"}}]
}}

For PROP:
{{
    "title": "Decision title",
    "decision": "Description of the decision",
    "alternatives": [{{"name": "Alt name", "description": "Description", "why_rejected": "Why rejected"}}],
    "consequences": "Implications of this decision"
}}

Return ONLY valid JSON, no markdown formatting."""
    
    def _parse_llm_response(
        self,
        response: str,
        spec_type: str
    ) -> dict:
        """Parse LLM response to extract structured data.
        
        Args:
            response: LLM response
            spec_type: Type of specification
            
        Returns:
            Parsed data dictionary
        """
        # Clean response (remove markdown code blocks if present)
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            data = json.loads(cleaned)
            return data
        except json.JSONDecodeError as e:
            raise TransformError(f"Failed to parse LLM response: {e}")
