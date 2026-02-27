"""Specification registry for auto-numbering."""

import re
from pathlib import Path


class SpecRegistry:
    """Registry of existing specifications."""

    def __init__(self, specs_dir: str = "specs"):
        """Initialize registry.

        Args:
            specs_dir: Path to specs directory

        """
        self.specs_dir = Path(specs_dir)

    def get_existing_specs(self, spec_type: str = "FEAT") -> list[str]:
        """Get list of existing spec numbers.

        Args:
            spec_type: Type of specification (FEAT, PROP)

        Returns:
            List of spec numbers (e.g., ["001", "002"])

        """
        if not self.specs_dir.exists():
            return []

        pattern = re.compile(rf'^{spec_type}-(\d+)\.md$')
        numbers = []

        for file in self.specs_dir.iterdir():
            match = pattern.match(file.name)
            if match:
                numbers.append(match.group(1))

        return sorted(numbers)

    def get_next_number(self, spec_type: str = "FEAT") -> str:
        """Get next available spec number.

        Args:
            spec_type: Type of specification

        Returns:
            Next number (e.g., "003")

        """
        existing = self.get_existing_specs(spec_type)

        if not existing:
            return "001"

        # Find gaps in numbering
        existing_nums = [int(n) for n in existing]
        existing_nums.sort()

        for i, num in enumerate(existing_nums):
            expected = i + 1
            if num != expected:
                return f"{expected:03d}"

        # No gaps, return next number
        next_num = existing_nums[-1] + 1
        return f"{next_num:03d}"


def get_next_spec_number(specs_dir: str, spec_type: str) -> str:
    """Get next spec number for directory.

    Args:
        specs_dir: Path to specs directory
        spec_type: Type of specification

    Returns:
        Next spec number

    """
    registry = SpecRegistry(specs_dir)
    return registry.get_next_number(spec_type)
