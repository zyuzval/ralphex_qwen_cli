"""Tests for spec registry."""

import pytest
from pathlib import Path
from qwenex.spec_registry import SpecRegistry, get_next_spec_number


def test_get_next_feat_number(tmp_path):
    """Test getting next FEAT number."""
    # Create fake specs directory
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "FEAT-001.md").write_text("# FEAT-001")
    (specs_dir / "FEAT-002.md").write_text("# FEAT-002")
    (specs_dir / "FEAT-005.md").write_text("# FEAT-005")
    
    number = get_next_spec_number(str(specs_dir), "FEAT")
    assert number == "003"


def test_get_next_prop_number(tmp_path):
    """Test getting next PROP number."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "PROP-001.md").write_text("# PROP-001")
    
    number = get_next_spec_number(str(specs_dir), "PROP")
    assert number == "002"


def test_no_existing_specs(tmp_path):
    """Test with no existing specs."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    
    number = get_next_spec_number(str(specs_dir), "FEAT")
    assert number == "001"
