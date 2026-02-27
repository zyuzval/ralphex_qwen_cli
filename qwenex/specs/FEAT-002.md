# FEAT-002: Система ревью

**Версия:** 1.0
**Дата:** 2026-02-27
**Статус:** Черновик
**Приоритет:** P0 (MVP Фаза 1)
**Зависимости:** FEAT-001 ✅

---

## Цель

Реализовать систему из 5 агентов ревью для автономной проверки кода: quality, implementation, testing, simplification, documentation.

---

## Контекст

После выполнения каждой задачи Qwenex должен автоматически проверить качество изменений через 5 специализированных агентов.

**Решения из ADR:**
- **ADR-003:** Гибридные субагенты (2 параллельно + 3 последовательно)
- **ADR-014:** Требуется исследование — почему гибридный подход, не все 5 параллельно
- **ADR-018:** WAL.md обновляется через MCP инструменты

**Архитектурный паттерн:** Task Loop with Validation (бывший Agentic RAG)

---

## Требования

### Функциональные

**F-001: 5 агентов ревью**

| Агент | Тип | Критичность | Описание |
|-------|-----|-------------|----------|
| **quality** | Параллельно (Фаза 1) | Критичный | Проверка качества кода, стандарты, best practices |
| **implementation** | Параллельно (Фаза 1) | Критичный | Соответствие реализации спеке (FEAT/PROP) |
| **testing** | Последовательно (Фаза 2) | Высокий | Проверка тестов (покрытие, корректность) |
| **simplification** | Последовательно (Фаза 2) | Средний | Поиск упрощений, удаление лишнего |
| **documentation** | Последовательно (Фаза 2) | Низкий | Проверка документации, комментарии |

**F-002: Гибридное выполнение**

```
Фаза 1 (параллельно):
  - quality (критичный)
  - implementation (критичный)
  ↓
Фаза 2 (последовательно):
  - testing
  - simplification
  - documentation
  ↓
Агрегация результатов → REVIEW-маркеры
```

**F-003: REVIEW-маркеры**

Формат предложений изменений:
```markdown
<!-- REVIEW: [предложение] — причина: [почему] — ждёт: решения человека -->
```

**F-004: Агрегация результатов**

- Сбор результатов от всех 5 агентов
- Приоритизация конфликтов (quality > implementation > testing > simplification > documentation)
- Генерация единого отчёта с REVIEW-маркерами

**F-005: Режимы ревью**

- `--auto` — REVIEW-маркеры авто-утверждаются (кроме критичных)
- `--interactive` — пауза на каждом REVIEW-маркере для утверждения человеком

### Нефункциональные

**NF-001: Производительность**

- Гибридное выполнение: ~40% быстрее последовательного
- Параллельные агенты: не более 2 одновременных Qwen CLI процессов

**NF-002: Надёжность**

- Graceful degradation: если агент упал — продолжить без него
- Логирование результатов каждого агента

**NF-003: Тестируемость**

- Покрытие тестами: 80%+
- Unit тесты на каждый компонент
- Integration тесты на гибридное выполнение

---

## Архитектура

### Компоненты

```
src/qwenex/
├── review/
│   ├── __init__.py
│   ├── agents.py           # 5 агентов ревью (prompts, execution)
│   ├── hybrid_executor.py  # Гибридное выполнение (2+3)
│   ├── aggregator.py       # Агрегация результатов, REVIEW-маркеры
│   └── config.py           # Конфигурация агентов (приоритеты, критичность)
├── mcp/
│   └── tools/
│       └── review.py       # MCP инструменты для ревью
└── tests/
    ├── test_agents.py
    ├── test_hybrid_executor.py
    └── test_aggregator.py
```

### Модели данных

#### ReviewAgent

```python
@dataclass
class ReviewAgent:
    name: str  # "quality", "implementation", "testing", "simplification", "documentation"
    priority: int  # 1 (highest) - 5 (lowest)
    critical: bool  # Критичный агент (параллельное выполнение)
    prompt_template: str  # Шаблон промпта для агента
```

#### ReviewResult

```python
@dataclass
class ReviewResult:
    agent: str
    success: bool
    findings: list[str]  # Найденные проблемы/предложения
    review_markers: list[str]  # <!-- REVIEW: ... -->
    output: str  # Полный output агента
    duration_sec: float
```

#### ReviewReport

```python
@dataclass
class ReviewReport:
    session_id: str
    git_diff: str  # Diff для ревью
    results: list[ReviewResult]
    aggregated_markers: list[str]
    conflicts: list[str]  # Конфликтующие рекомендации
    summary: str
```

### Поток данных

```
Git diff (изменения задачи)
    ↓
[Hybrid Executor]
    ↓
Фаза 1 (параллельно):
  ├─→ quality agent ──→ ReviewResult
  └─→ implementation agent ──→ ReviewResult
    ↓
Фаза 2 (последовательно):
  ├─→ testing agent ──→ ReviewResult
  ├─→ simplification agent ──→ ReviewResult
  └─→ documentation agent ──→ ReviewResult
    ↓
[Aggregator]
  ├─→ Сбор результатов
  ├─→ Приоритизация конфликтов
  └─→ Генерация REVIEW-маркеров
    ↓
[Review Report] → WAL.md update → Git commit
```

---

## Промпты агентов

### quality

```
You are a code quality reviewer. Review the following git diff for:
- Code style consistency (PEP 8 for Python)
- Best practices and design patterns
- Potential bugs and edge cases
- Security issues
- Performance concerns

Format findings as:
- [QUALITY-1] Brief description
- [QUALITY-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.

Git diff:
{git_diff}
```

### implementation

```
You are an implementation reviewer. Check if the code changes match the specification (FEAT/PROP).

Review criteria:
- Does the implementation match the spec requirements?
- Are all acceptance criteria met?
- Any missing functionality?
- Any over-engineering (YAGNI)?

Format findings as:
- [IMPL-1] Brief description
- [IMPL-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.

Specification:
{spec_content}

Git diff:
{git_diff}
```

### testing

```
You are a testing reviewer. Review the test changes for:
- Test coverage (80%+ target)
- Test quality (specific, isolated, repeatable)
- Edge cases covered
- Mock/stub usage appropriate

Format findings as:
- [TEST-1] Brief description
- [TEST-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.

Git diff:
{git_diff}

Test coverage report:
{coverage_report}
```

### simplification

```
You are a simplification reviewer. Look for:
- Over-engineering (YAGNI violations)
- Complex code that can be simpler
- Duplicate code
- Unused code (dead code, unused imports)
- Opportunities for DRY

Format findings as:
- [SIMPL-1] Brief description
- [SIMPL-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.

Git diff:
{git_diff}
```

### documentation

```
You are a documentation reviewer. Check for:
- Missing docstrings (public API)
- Missing comments (complex logic)
- README/docs updates for new features
- CHANGELOG updates
- Inline comments (why, not what)

Format findings as:
- [DOC-1] Brief description
- [DOC-2] Brief description

For each finding, suggest a fix with <!-- REVIEW: ... --> marker.

Git diff:
{git_diff}
```

---

## Интерфейсы

### CLI интерфейс

```bash
# Запуск ревью после задачи
qwenex review --session <session_id>

# Ревью с авто-утверждением (кроме критичных)
qwenex review --session <session_id> --auto

# Ревью с интерактивным утверждением
qwenex review --session <session_id> --interactive

# Ревью конкретного diff файла
qwenex review --diff path/to/diff.patch
```

### CLI аргументы

| Аргумент | Описание | По умолчанию |
|----------|----------|--------------|
| `--session` | ID сессии для ревью | Обязательный (или --diff) |
| `--diff` | Путь к diff файлу | Обязательный (или --session) |
| `--auto` | Авто-утверждение REVIEW (кроме критичных) | false |
| `--interactive` | Интерактивное утверждение | false |
| `--agents` | Запустить конкретных агентов (comma-separated) | all |
| `--parallel` | Запустить все агенты параллельно | false (гибридно) |
| `--timeout` | Таймаут на агента (мин) | 5 |

---

## Обработка ошибок

### Таймауты

```python
# src/qwenex/review/hybrid_executor.py
async def run_agent(self, agent: ReviewAgent, session_id: str, timeout_min: int = 5):
    try:
        await asyncio.wait_for(
            self._run_agent_impl(agent, session_id),
            timeout=timeout_min * 60
        )
    except asyncio.TimeoutError:
        logger.warning(f"Agent {agent.name} timed out")
        return ReviewResult(
            agent=agent.name,
            success=False,
            findings=[f"Agent timed out after {timeout_min} minutes"],
            review_markers=[],
            output="",
            duration_sec=timeout_min * 60
        )
```

### Graceful degradation

```python
# Если агент упал — продолжить без него
async def run_phase1_parallel(self, session_id: str):
    tasks = [
        self.run_agent(self.agents["quality"], session_id),
        self.run_agent(self.agents["implementation"], session_id)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Обработка исключений
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Agent {list(self.agents.keys())[i]} failed: {result}")
            # Создать пустой результат
            processed_results.append(self._empty_result(list(self.agents.keys())[i]))
        else:
            processed_results.append(result)
    
    return processed_results
```

### Конфликты между агентами

```python
# src/qwenex/review/aggregator.py
def detect_conflicts(self, results: list[ReviewResult]) -> list[str]:
    """Обнаружить конфликтующие рекомендации"""
    conflicts = []
    
    # Пример: quality требует добавить проверку, simplification — удалить
    quality_findings = {f.text for f in results[0].findings if "QUALITY" in f}
    simpl_findings = {f.text for f in results[3].findings if "SIMPL" in f}
    
    # Эвристика конфликтов
    if self._are_conflicting(quality_findings, simpl_findings):
        conflicts.append("quality vs simplification: conflicting recommendations")
    
    return conflicts
```

---

## Тесты

### Unit тесты

```python
# tests/test_agents.py
def test_quality_agent_prompt():
    agent = ReviewAgent(name="quality", ...)
    prompt = agent.render_prompt(git_diff="diff content")
    
    assert "code quality reviewer" in prompt.lower()
    assert "PEP 8" in prompt
    assert "diff content" in prompt

def test_review_result_parsing():
    output = """
- [QUALITY-1] Missing docstring
<!-- REVIEW: Add docstring — причина: PEP 257 — ждёт: решения человека -->
"""
    result = parse_review_output(output)
    
    assert len(result.findings) == 1
    assert len(result.review_markers) == 1
```

### Integration тесты

```python
# tests/test_hybrid_executor.py
async def test_hybrid_execution():
    executor = HybridExecutor()
    report = await executor.run_review(session_id="test-123")
    
    assert len(report.results) == 5
    assert report.results[0].agent == "quality"
    assert report.results[1].agent == "implementation"
    # Фаза 1 параллельно
    assert abs(report.results[0].duration_sec - report.results[1].duration_sec) < 2.0
```

---

## MCP инструменты

```python
# src/mcp/tools/review.py
from fastmcp import FastMCP

mcp = FastMCP("qwenex-review")

@mcp.tool()
async def launch_review(session_id: str, agents: list[str] = None) -> str:
    """Запустить 5 агентов ревью для сессии"""
    executor = HybridExecutor()
    report = await executor.run_review(session_id, agents=agents)
    return report.summary

@mcp.tool()
async def get_review_report(session_id: str) -> ReviewReport:
    """Получить полный отчёт ревью"""
    return load_review_report(session_id)

@mcp.tool()
async def apply_review_marker(session_id: str, marker_index: int, approve: bool) -> str:
    """Применить REVIEW-маркер (утвердить/отклонить)"""
    report = load_review_report(session_id)
    marker = report.aggregated_markers[marker_index]
    
    if approve:
        apply_marker_fix(marker)
        return f"Applied: {marker}"
    else:
        return f"Rejected: {marker}"

@mcp.tool()
async def resolve_conflicts(session_id: str, resolutions: dict[int, str]) -> str:
    """Разрешить конфликты между агентами"""
    report = load_review_report(session_id)
    
    for conflict_idx, resolution in resolutions.items():
        report.conflicts[conflict_idx].resolution = resolution
    
    save_review_report(session_id, report)
    return f"Resolved {len(resolutions)} conflicts"
```

---

## Интеграция с FEAT-001

### Orchestrator → Review

```python
# src/qwenex/orchestrator.py
async def execute_task(self, task: Task) -> TaskResult:
    # 1. Выполнить задачу через Qwen CLI
    result = await self.executor.run_task(task.prompt)
    
    # 2. Запустить ревью
    review_report = await self.reviewer.run_review(
        session_id=self.session_id,
        git_diff=result.git_diff
    )
    
    # 3. Применить REVIEW-маркеры (режим --auto)
    if self.auto_mode:
        for marker in review_report.aggregated_markers:
            if not marker.critical:
                apply_marker_fix(marker)
    
    # 4. Обновить WAL.md
    await self.wal.complete_task(task.id, review_report.summary)
    
    return result
```

### Progress → Review

```python
# src/qwenex/progress.py
def update_with_review(self, review_report: ReviewReport):
    """Обновить прогресс с результатами ревью"""
    self.log(f"Review completed: {len(review_report.aggregated_markers)} markers")
    
    for agent_result in review_report.results:
        self.log(f"  {agent_result.agent}: {len(agent_result.findings)} findings")
```

---

## Критерии приёмки

- [ ] 5 агентов ревью реализованы (quality, implementation, testing, simplification, documentation)
- [ ] Гибридное выполнение (2 параллельно + 3 последовательно)
- [ ] REVIEW-маркеры генерируются корректно
- [ ] Агрегация результатов с приоритизацией конфликтов
- [ ] Режимы --auto и --interactive работают
- [ ] MCP инструменты для ревью (launch_review, get_review_report, apply_review_marker)
- [ ] Graceful degradation (если агент упал — продолжить)
- [ ] Таймауты на агентов (5 мин)
- [ ] Покрытие тестами 80%+
- [ ] Интеграция с orchestrator (FEAT-001)

---

## Зависимости

### Внешние

| Зависимость | Версия | Цель |
|-------------|--------|------|
| `qwen` | 0.10.6+ | Выполнение агентов |
| `git` | 2.x | Git diff generation |

### Python пакеты

| Пакет | Версия | Цель |
|-------|--------|------|
| `fastmcp` | latest | MCP сервер |
| `pydantic` | 2.x | Модели данных |
| `pytest` | 7.x+ | Тесты |
| `pytest-asyncio` | 0.21+ | Async тесты |

---

## Связанные документы

| Документ | Описание |
|----------|----------|
| [BOOT.md](../BOOT.md) | Конституция проекта |
| [WAL.md](../WAL.md) | Текущий статус |
| [FEAT-001](./FEAT-001.md) | Ядро оркестратора |
| [ADR-003](../docs/DECISIONS.md) | Гибридные субагенты |
| [ADR-014](../docs/DECISIONS.md) | Исследование гибридного ревью |
| [ADR-018](../docs/DECISIONS.md) | Процесс обновления WAL.md |
| [RISK_ANALYSIS.md](../docs/RISK_ANALYSIS.md) | Риски (RISK-006) |

---

## История версий

| Версия | Дата | Изменение |
|--------|------|-----------|
| 1.0 | 2026-02-27 | Initial version — spec на основе ADR-003, ADR-014, ADR-018 |
