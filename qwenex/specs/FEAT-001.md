# FEAT-001: Ядро оркестратора

**Версия:** 1.0  
**Дата:** 2026-02-27  
**Статус:** Черновик  
**Приоритет:** P0 (MVP Фаза 1)  
**Зависимости:** BOOTSTRAP-001 ✅

---

## Цель

Реализовать базовую оркестрацию задач через Qwen CLI: чтение плана, выполнение задач, валидация, прогресс-трекинг.

---

## Контекст

Qwenex — оркестратор для автономного выполнения планов разработки. Ядро отвечает за:
- Чтение планов из markdown файлов
- Выполнение задач через Qwen CLI (stream-json output)
- Валидацию через команды из плана
- Прогресс-трекинг (обновление чекбоксов, коммиты)

**Решения из brainstorming (2026-02-27):**
- **RISK-002:** Qwen CLI проверен — `stream-json` работает (v0.10.6)
- **RISK-003:** MCP в одном процессе (не sidecar) для MVP
- **RISK-004:** Двухфазное MVP — Фаза 1 (8-12 недель): ядро + ревью + MCP
- **RISK-005:** Два режима — `--auto` (REVIEW авто-утверждаются) и `--interactive` (пауза на REVIEW)

---

## Требования

### Функциональные

**F-001: Чтение плана**
- Парсинг markdown плана (заголовок, задачи, чекбоксы, валидация)
- Поддержка формата: `### Task N:` + `- [ ]` / `- [x]`
- Извлечение validation commands из `## Validation Commands`

**F-002: Выполнение задач**
- Запуск Qwen CLI с `--yolo --output-format stream-json --prompt`
- Парсинг streaming JSON output (типы: `system`, `assistant`, `result`)
- Обработка таймаутов (max 10 мин на задачу)

**F-003: Валидация**
- Запуск validation commands после каждой задачи
- Повтор задачи при провале валидации (max 3 итерации)
- Логирование результатов валидации

**F-004: Прогресс-трекинг**
- Обновление чекбоксов в плане (`- [ ]` → `- [x]`)
- Запись прогресса в `.qwenex/progress/progress-<plan>.txt`
- Git commit после каждой задачи

**F-005: Режимы работы**
- `--auto`: REVIEW-маркеры авто-утверждаются
- `--interactive`: пауза на REVIEW-маркерах для утверждения человеком

### Нефункциональные

**NF-001: Производительность**
- Запуск задачи: < 5 сек overhead (не считая Qwen API)
- Парсинг stream-json: в реальном времени (streaming)

**NF-002: Надёжность**
- Graceful shutdown по SIGINT/SIGTERM
- Сохранение прогресса перед выходом
- Таймауты на Qwen CLI вызовы

**NF-003: Кроссплатформенность**
- Поддержка Windows, macOS, Linux
- Git через subprocess (не библиотеки)

**NF-004: Тестируемость**
- Покрытие тестами: 80%+
- pytest для unit/integration тестов

---

## Архитектура

### Компоненты

```
src/qwenex/
├── cli.py              # CLI интерфейс (argparse, entry point)
├── orchestrator.py     # Оркестрация задач (Task Loop with Validation)
├── plan_parser.py      # Парсинг markdown плана
├── qwen_executor.py    # Выполнение Qwen CLI (subprocess, stream-json)
├── validator.py        # Валидация команд
├── progress.py         # Прогресс-трекинг
├── git_wrapper.py      # Git операции (subprocess)
└── models/
    ├── base.py         # LLMProvider интерфейс (задел на v0.2)
    └── qwen_cloud.py   # Qwen Cloud API (MVP)
```

### Поток данных

```
Plan file (.md)
    ↓
[Plan Parser] → Plan object (tasks, validation commands)
    ↓
[Orchestrator] → Task Loop with Validation
    ↓
[Qwen Executor] → Qwen CLI (subprocess, stream-json)
    ↓
[Validator] → Validation commands (subprocess)
    ↓
[Progress Tracker] → Update checkboxes, git commit
    ↓
[Repeat] → Next task or done
```

### Task Loop with Validation

```
Plan → Parse → [Task N] → Execute via Qwen CLI → Validate
 ↑                                              │
 └──────────────── Fix Loop (max 3) ────────────┘
    ↓
 Update WAL.md → Commit → Next task
```

---

## Интерфейсы

### CLI интерфейс

```bash
# Базовое использование
qwenex docs/plans/feature.md

# Автономный режим (REVIEW авто-утверждаются)
qwenex --auto docs/plans/feature.md

# Интерактивный режим (пауза на REVIEW)
qwenex --interactive docs/plans/feature.md

# Только задачи (без ревью)
qwenex --tasks-only docs/plans/feature.md

# С веб-дашбордом
qwenex --serve --port 8080 docs/plans/feature.md
```

### CLI аргументы

| Аргумент | Описание | По умолчанию |
|----------|----------|--------------|
| `plan_file` | Путь к плану | Обязательный |
| `--auto` | Автономный режим (REVIEW авто-утверждаются) | false |
| `--interactive` | Интерактивный режим (пауза на REVIEW) | false |
| `--tasks-only` | Только задачи, без ревью | false |
| `--max-iterations` | Максимум итераций на задачу | 3 |
| `--timeout` | Таймаут на задачу (мин) | 10 |
| `--serve` | Веб-дашборд | false |
| `--port` | Порт веб-дашборда | 8080 |
| `--debug` | Debug логирование | false |
| `--no-color` | Без цветов | false |

---

## Модели данных

### Plan

```python
@dataclass
class Plan:
    title: str
    file_path: str
    validation_commands: list[str]
    tasks: list[Task]
    current_task_index: int = 0

@dataclass
class Task:
    number: str  # "1", "2", "2.5", "2a"
    title: str
    checkboxes: list[Checkbox]

@dataclass
class Checkbox:
    text: str
    completed: bool  # [ ] = False, [x] = True
```

### TaskResult

```python
@dataclass
class TaskResult:
    task: Task
    success: bool
    output: str  # Qwen CLI output
    validation_output: str | None
    iterations: int
    review_markers: list[str]  # <!-- REVIEW: ... -->
```

---

## Обработка ошибок

### Таймауты

```python
# src/qwenex/qwen_executor.py
async def run_task(self, prompt: str, timeout_min: int = 10):
    try:
        process = await asyncio.create_subprocess_exec(...)
        await asyncio.wait_for(process.communicate(), timeout=timeout_min * 60)
    except asyncio.TimeoutError:
        process.kill()
        raise TaskTimeoutError(f"Task exceeded {timeout_min} minutes")
```

### Graceful shutdown

```python
# src/qwenex/cli.py
import signal

def handle_signal(signum, frame):
    logger.info(f"Received signal {signum}, saving progress...")
    progress_tracker.save()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)
```

### Retry логика

```python
# src/qwenex/orchestrator.py
async def execute_task_with_retry(self, task: Task, max_iterations: int = 3):
    for iteration in range(max_iterations):
        result = await self.executor.run_task(task.prompt)
        validation_result = await self.validator.run(task.validation_commands)
        
        if validation_result.success:
            return result
        
        logger.warning(f"Validation failed, retry {iteration + 1}/{max_iterations}")
    
    raise MaxIterationsExceededError(f"Task failed after {max_iterations} iterations")
```

---

## Тесты

### Unit тесты

```python
# tests/test_plan_parser.py
def test_parse_plan_with_checkboxes():
    plan = parse_plan("""
# Plan: Feature

## Validation Commands
- pytest

### Task 1: Implement
- [ ] Add feature
- [x] Done
""")
    assert plan.title == "Feature"
    assert plan.tasks[0].checkboxes[0].completed == False
    assert plan.tasks[0].checkboxes[1].completed == True

# tests/test_qwen_executor.py
async def test_parse_stream_json():
    executor = QwenExecutor()
    events = await executor.run_task("Say OK")
    
    assert any(e["type"] == "assistant" for e in events)
    assert any(e["type"] == "result" for e in events)
```

### Integration тесты

```python
# tests/test_orchestrator.py
async def test_full_task_loop():
    orchestrator = Orchestrator(plan_file="test_plan.md")
    result = await orchestrator.run()
    
    assert result.tasks_completed > 0
    assert result.validation_passed
```

---

## Прогресс-трекинг

### Формат прогресс файла

```
# Progress: docs/plans/feature.md
# Started: 2026-02-27 10:30:00

[10:30:05] Started task 1: Implement feature
[10:30:10] Qwen CLI started
[10:35:00] Qwen CLI completed
[10:35:05] Running validation: pytest
[10:35:30] Validation passed
[10:35:35] Updated checkboxes
[10:35:40] Committed changes
[10:35:45] Completed task 1

[10:35:50] Started task 2: Add tests
...
```

### WAL.md обновление

```python
# src/mcp/tools/wal.py
async def complete_task(task_id: str, notes: str) -> str:
    """Отметить задачу завершённой в WAL.md"""
    # Обновить секцию "✅ Завершено (последние сессии)"
    # Добавить: - [x] **[FEAT-001: Ядро оркестратора]** — Описание · дата
```

---

## Зависимости

### Внешние

| Зависимость | Версия | Цель |
|-------------|--------|------|
| `qwen` | 0.10.6+ | Выполнение задач |
| `git` | 2.x | Git операции |
| `python` | 3.11+ | Runtime |

### Python пакеты

| Пакет | Версия | Цель |
|-------|--------|------|
| `fastmcp` | latest | MCP сервер |
| `pydantic` | 2.x | Модели данных |
| `pytest` | 7.x+ | Тесты |
| `pytest-asyncio` | 0.21+ | Async тесты |

---

## Критерии приёмки

- [ ] План парсится корректно (задачи, чекбоксы, валидация)
- [ ] Qwen CLI запускается с stream-json output
- [ ] Stream-json парсится в реальном времени
- [ ] Валидация работает (команды из плана)
- [ ] Retry логика (max 3 итерации)
- [ ] Прогресс сохраняется (.qwenex/progress/)
- [ ] Git commit после каждой задачи
- [ ] Graceful shutdown (SIGINT/SIGTERM)
- [ ] Таймауты на задачи (10 мин)
- [ ] Режимы `--auto` и `--interactive` работают
- [ ] Покрытие тестами 80%+

---

## Связанные документы

| Документ | Описание |
|----------|----------|
| [BOOT.md](../BOOT.md) | Конституция проекта |
| [WAL.md](../WAL.md) | Текущий статус |
| [ADR-001](../docs/DECISIONS.md) | Выбор Python |
| [ADR-002](../docs/DECISIONS.md) | MCP архитектура |
| [ADR-017](../docs/DECISIONS.md) | Qwen CLI интерфейс |
| [RISK_ANALYSIS.md](../docs/RISK_ANALYSIS.md) | Риски (RISK-002, RISK-003) |

---

## История версий

| Версия | Дата | Изменение |
|--------|------|-----------|
| 1.0 | 2026-02-27 | Initial version — spec на основе brainstorming |
