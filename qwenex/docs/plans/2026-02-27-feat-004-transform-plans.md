# FEAT-004: Трансформация планов Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Трансформация простых markdown планов в полноценные FEAT/PROP спецификации через LLM.

**Architecture:** Новый модуль transformer.py принимает простой план, использует LLM для генерации структурированной FEAT/PROP спецификации с целями, требованиями и тестами. CLI опция `--transform` для запуска трансформации перед выполнением.

**Tech Stack:** Python 3.11+ · LLMProvider (PROP-001) · Jinja2 templates · Pydantic для валидации

---

### Task 1: Шаблон FEAT спецификации

**Files:**
- Create: `src/qwenex/transformer/templates/feat_template.md`
- Test: `src/tests/test_transformer_templates.py`

**Step 1: Write the failing test**

```python
# src/tests/test_transformer_templates.py
"""Tests for transformer templates."""

import pytest
from pathlib import Path
from qwenex.transformer.templates import load_template, TemplateError


def test_load_feat_template():
    """Test loading FEAT template."""
    template = load_template("feat")
    assert template is not None
    assert "{{ title }}" in template
    assert "{{ goal }}" in template
    assert "{{ requirements }}" in template


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
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_transformer_templates.py -v --no-cov`
Expected: FAIL with "ModuleNotFoundError: No module named 'qwenex.transformer'"

**Step 3: Write minimal implementation**

```python
# src/qwenex/transformer/templates/__init__.py
"""Template loader for transformer."""

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
```

```markdown
<!-- src/qwenex/transformer/templates/feat_template.md -->
# FEAT-{{ number }}: {{ title }}

**URI:** spec://{{ module }}/FEAT-{{ number }}
**Версия:** 0.1.0 · **Статус:** Черновик

---

## 1. Цель

{{ goal }}

---

## 2. Пользовательские сценарии

{% for scenario in scenarios %}
- **Сценарий {{ loop.index }}:** {{ scenario }}
{% endfor %}

---

## 3. Функциональные требования

{% for req in requirements %}
### 3.{{ loop.index }} {{ req.name }}

{{ req.description }}

**Почему:** {{ req.why }}
{% endfor %}

---

## 4. Out of scope

{% for item in out_of_scope %}
- {{ item }}
{% endfor %}

---

## 5. Тестовые сценарии

{% for test in tests %}
- `{{ test.name }}`: {{ test.description }}
{% endfor %}
```

```markdown
<!-- src/qwenex/transformer/templates/prop_template.md -->
# PROP-{{ number }}: {{ title }}

**URI:** spec://{{ module }}/PROP-{{ number }}
**Версия:** 0.1.0 · **Статус:** Черновик

---

## 1. Решение

{{ decision }}

---

## 2. Альтернативы

{% for alt in alternatives %}
### {{ alt.name }}

{{ alt.description }}

**Почему не выбрали:** {{ alt.why_rejected }}
{% endfor %}

---

## 3. Последствия

{{ consequences }}
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_transformer_templates.py -v --no-cov`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/transformer/templates/ src/tests/test_transformer_templates.py
git commit -m "feat(FEAT-004-1): add FEAT/PROP templates

- Jinja2 templates for spec generation
- feat_template.md with sections for goal, scenarios, requirements
- prop_template.md for technical decisions
- Template loader with error handling
- Tests: 3 passing"
```

---

### Task 2: Transformer модуль

**Files:**
- Create: `src/qwenex/transformer/__init__.py`
- Create: `src/qwenex/transformer/transformer.py`
- Test: `src/tests/test_transformer.py`

**Step 1: Write the failing test**

```python
# src/tests/test_transformer.py
"""Tests for plan transformer."""

import pytest
from unittest.mock import AsyncMock, patch
from qwenex.transformer import PlanTransformer
from qwenex.models.base import ProviderConfig
from qwenex.models.qwen_cloud import QwenCloudProvider


@pytest.mark.asyncio
async def test_transform_simple_plan():
    """Test transforming a simple plan."""
    config = ProviderConfig(
        name="qwen_cloud",
        model="qwen-max",
        api_key="test-key"
    )
    provider = QwenCloudProvider(config)
    transformer = PlanTransformer(provider=provider)
    
    simple_plan = """# Plan: Add login

## Tasks
1. Create login form
2. Add API endpoint
3. Write tests
"""
    
    mock_response = """# FEAT-001: Login System

## 1. Цель
Implement user authentication

## 2. Пользовательские сценарии
- **Сценарий 1:** User logs in with credentials

## 3. Функциональные требования
### 3.1 Login Form
Login form with username and password

**Почему:** Required for authentication

## 5. Тестовые сценарии
- `test_login_success`: Valid credentials log in user
"""
    
    with patch.object(provider, 'complete', new=AsyncMock(return_value=mock_response)):
        result = await transformer.transform(simple_plan, "FEAT-001")
        assert "FEAT-001" in result
        assert "Login System" in result


@pytest.mark.asyncio
async def test_transform_preserves_structure():
    """Test that transformation preserves FEAT structure."""
    config = ProviderConfig(name="qwen_cloud", model="qwen-max", api_key="key")
    provider = QwenCloudProvider(config)
    transformer = PlanTransformer(provider=provider)
    
    simple_plan = "# Plan: Test\n\n## Tasks\n1. Do something"
    mock_response = "# FEAT-001: Test\n\n## 1. Цель\nTest goal"
    
    with patch.object(provider, 'complete', new=AsyncMock(return_value=mock_response)):
        result = await transformer.transform(simple_plan, "FEAT-001")
        assert "## 1. Цель" in result
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_transformer.py -v --no-cov`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/qwenex/transformer/__init__.py
"""Plan transformer package."""

from .transformer import PlanTransformer

__all__ = ["PlanTransformer"]
```

```python
# src/qwenex/transformer/transformer.py
"""Transform simple plans to FEAT/PROP specifications."""

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
        import json
        
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
```

**Step 4: Add jinja2 dependency**

```toml
# pyproject.toml - add to [project.dependencies]
"jinja2>=3.1.0",
```

**Step 5: Run test to verify it passes**

Run: `cd qwenex && pip install -e . && pytest src/tests/test_transformer.py -v --no-cov`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
cd qwenex
git add src/qwenex/transformer/ pyproject.toml src/tests/test_transformer.py
git commit -m "feat(FEAT-004-2): add PlanTransformer module

- PlanTransformer class with async transform method
- LLM-powered plan to spec conversion
- Jinja2 template rendering
- JSON response parsing
- FEAT and PROP support
- Tests: 2 passing"
```

---

### Task 3: CLI опция --transform

**Files:**
- Modify: `src/qwenex/cli.py`
- Test: Modify `src/tests/test_cli.py`

**Step 1: Add --transform argument**

```python
# src/qwenex/cli.py - add to parse_args()
parser.add_argument(
    "--transform",
    action="store_true",
    help="Transform simple plan to FEAT/PROP before execution"
)

parser.add_argument(
    "--spec-type",
    type=str,
    default="FEAT",
    choices=["FEAT", "PROP"],
    help="Type of specification to generate"
)

parser.add_argument(
    "--spec-number",
    type=str,
    default=None,
    help="Specification number (e.g., 001)"
)
```

**Step 2: Update main() to handle transform**

```python
# src/qwenex/cli.py - update async_main()
from .transformer import PlanTransformer

# ... in async_main() ...

# Transform if requested
if parsed_args.transform:
    from .models.base import ProviderConfig
    
    provider_config = ProviderConfig(
        name=provider_name,
        model=model,
        api_key=parsed_args.api_key,
    )
    
    transformer = PlanTransformer(provider_config=provider_config)
    
    # Read original plan
    with open(parsed_args.plan_file, 'r', encoding='utf-8') as f:
        simple_plan = f.read()
    
    # Generate spec number if not provided
    spec_number = parsed_args.spec_number or "001"
    
    print(f"Transforming plan to {parsed_args.spec_type}-{spec_number}...")
    spec = await transformer.transform(
        simple_plan,
        spec_number,
        spec_type=parsed_args.spec_type
    )
    
    # Save transformed spec
    spec_path = f"specs/{parsed_args.spec_type}-{spec_number}.md"
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec)
    
    print(f"Generated: {spec_path}")
    
    # Update plan_file to use transformed spec
    parsed_args.plan_file = spec_path
```

**Step 3: Run tests**

Run: `cd qwenex && pytest src/tests/test_cli.py -v --no-cov`
Expected: PASS (update existing tests if needed)

**Step 4: Commit**

```bash
cd qwenex
git add src/qwenex/cli.py src/tests/test_cli.py
git commit -m "feat(FEAT-004-3): add --transform CLI option

- --transform flag for plan transformation
- --spec-type for FEAT/PROP selection
- --spec-number for specification numbering
- Auto-save to specs/ directory
- Tests: updated"
```

---

### Task 4: Extract spec number from existing specs

**Files:**
- Create: `src/qwenex/spec_registry.py`
- Test: `src/tests/test_spec_registry.py`

**Step 1: Write the failing test**

```python
# src/tests/test_spec_registry.py
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
```

**Step 2: Run test to verify it fails**

Run: `cd qwenex && pytest src/tests/test_spec_registry.py -v --no-cov`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/qwenex/spec_registry.py
"""Specification registry for auto-numbering."""

import re
from pathlib import Path
from typing import List


class SpecRegistry:
    """Registry of existing specifications."""
    
    def __init__(self, specs_dir: str = "specs"):
        """Initialize registry.
        
        Args:
            specs_dir: Path to specs directory
        """
        self.specs_dir = Path(specs_dir)
    
    def get_existing_specs(self, spec_type: str = "FEAT") -> List[str]:
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
```

**Step 4: Run test to verify it passes**

Run: `cd qwenex && pytest src/tests/test_spec_registry.py -v --no-cov`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
cd qwenex
git add src/qwenex/spec_registry.py src/tests/test_spec_registry.py
git commit -m "feat(FEAT-004-4): add SpecRegistry for auto-numbering

- SpecRegistry class to track existing specs
- get_next_number() finds gaps in numbering
- Auto-increment FEAT/PROP numbers
- Tests: 3 passing"
```

---

### Task 5: Интеграция registry в CLI

**Files:**
- Modify: `src/qwenex/cli.py`

**Step 1: Update CLI to use registry**

```python
# src/qwenex/cli.py - update the transform section
from .spec_registry import get_next_spec_number

# ... in async_main() when transform is requested ...

# Generate spec number if not provided
if parsed_args.spec_number:
    spec_number = parsed_args.spec_number
else:
    # Auto-generate from existing specs
    spec_number = get_next_spec_number("specs", parsed_args.spec_type)
    print(f"Auto-generated spec number: {parsed_args.spec_type}-{spec_number}")
```

**Step 2: Run tests**

Run: `cd qwenex && pytest src/tests/test_cli.py::test_transform_auto_number -v --no-cov`
Expected: PASS (add new test for auto-numbering)

**Step 3: Commit**

```bash
cd qwenex
git add src/qwenex/cli.py src/qwenex/spec_registry.py
git commit -m "feat(FEAT-004-5): integrate SpecRegistry into CLI

- Auto-generate spec numbers from existing specs
- Find gaps in numbering sequence
- Fallback to next available number
- Tests: updated"
```

---

### Task 6: Документация

**Files:**
- Create: `docs/TRANSFORM.md`
- Modify: `README.md`

**Step 1: Create TRANSFORM.md**

```markdown
# Трансформация планов

Qwenex может автоматически превращать простые markdown планы в полноценные FEAT/PROP спецификации.

## Быстрый старт

```bash
# Трансформировать план в FEAT спецификацию
qwenex plan.md --transform

# С указанием типа и номера
qwenex plan.md --transform --spec-type FEAT --spec-number 001

# Трансформировать в PROP спецификацию
qwenex plan.md --transform --spec-type PROP
```

## Формат входного плана

```markdown
# Plan: Добавить login

## Задачи
1. Создать форму login
2. Добавить API endpoint /auth/login
3. Написать тесты

## Validation
- `pytest tests/test_login.py`
```

## Результат трансформации

Qwenex создаст файл `specs/FEAT-001.md`:

```markdown
# FEAT-001: Добавить login

**URI:** spec://module/FEAT-001

## 1. Цель
Реализовать аутентификацию пользователей...

## 2. Пользовательские сценарии
- **Сценарий 1:** Пользователь вводит credentials...

## 3. Функциональные требования
...
```

## Алгоритм

1. Чтение простого плана
2. LLM анализирует задачи и извлекает:
   - Цель (goal)
   - Пользовательские сценарии
   - Функциональные требования
   - Тестовые сценарии
3. Рендеринг Jinja2 шаблона
4. Сохранение в specs/

## Конфигурация

Используйте те же переменные окружения что и для основного провайдера:

```bash
export QWENEX_PROVIDER=qwen_cloud
export QWENEX_MODEL=qwen-max
export QWENEX_API_KEY=your-api-key
```

## Советы

- Пишите задачи подробно — LLM использует это для генерации требований
- Указывайте validation команды — они перейдут в спецификацию
- Проверяйте сгенерированные спеки перед коммитом
```

**Step 2: Update README.md**

```markdown
# Add to README features section
- **Трансформация планов** — простые планы → FEAT/PROP спецификации
```

```markdown
# Add to README usage section
### Трансформация планов

```bash
# Автоматическая генерация спецификации
qwenex my-plan.md --transform

# С явным указанием номера
qwenex my-plan.md --transform --spec-number 005
```
```

**Step 3: Commit**

```bash
cd qwenex
git add docs/TRANSFORM.md README.md
git commit -m "docs(FEAT-004-6): add transformation documentation

- TRANSFORM.md with usage guide
- Examples of input/output formats
- Update README with new feature
- Algorithm description"
```

---

## Завершение плана

**Проверка покрытия тестов:**

```bash
cd qwenex && pytest --cov=src/qwenex --cov-report=term-missing
```

Expected: 80%+ покрытие

**Запуск всех тестов:**

```bash
cd qwenex && pytest -v
```

Expected: Все тесты проходят

---

## Итоговый список коммитов

1. `feat(FEAT-004-1): add FEAT/PROP templates`
2. `feat(FEAT-004-2): add PlanTransformer module`
3. `feat(FEAT-004-3): add --transform CLI option`
4. `feat(FEAT-004-4): add SpecRegistry for auto-numbering`
5. `feat(FEAT-004-5): integrate SpecRegistry into CLI`
6. `docs(FEAT-004-6): add transformation documentation`

**Всего:** 6 коммитов, ~10 тестов

---

План готов и сохранён в `docs/plans/2026-02-27-feat-004-transform-plans.md`.

**Два варианта выполнения:**

**1. Subagent-Driven (эта сессия)** — Запускаю свежего субагента на каждую задачу, code review между задачами, быстрая итерация

**2. Параллельная сессия (отдельная)** — Открыть новую сессию с `superpowers:executing-plans`, пакетное выполнение с чекпоинтами

**Какой подход выбираешь?**
