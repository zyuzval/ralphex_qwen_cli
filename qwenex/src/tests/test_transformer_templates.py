"""Tests for transformer templates."""

import pytest
from qwenex.transformer.templates import load_template, TemplateError


def test_load_feat_template():
    """Test loading FEAT template."""
    template = load_template("feat")
    assert template is not None
    assert "{{ title }}" in template
    assert "{{ goal }}" in template
    assert "{% for req in requirements %}" in template


def test_load_prop_template():
    """Test loading PROP template."""
    template = load_template("prop")
    assert template is not None
    assert "{{ title }}" in template
    assert "{{ decision }}" in template


def test_load_unknown_template():
    """Test loading unknown template raises error."""
    with pytest.raises(TemplateError):
        load_template("unknown")
