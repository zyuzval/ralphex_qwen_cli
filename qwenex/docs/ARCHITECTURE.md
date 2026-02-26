# Архитектура Qwenex

**Дата:** 2026-02-26  
**Версия:** 1.0  
**Статус:** Черновик

---

## 📋 Обзор

**Qwenex** — это оркестратор для автономного выполнения планов разработки через Qwen CLI с системой спецификаций (BOOT/WAL/FEAT/PROP) и MCP-инструментами.

---

## 🏗️ Высокоуровневая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         Пользователь                             │
│              (запускает qwenex <plan.md>)                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Qwenex CLI                                    │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │  Plan Parser  │  │  Orchestrator │  │  Progress Tracker   │ │
│  │  (FEAT/PROP)  │  │  (tasks loop) │  │  (WAL.md updates)   │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌────────────┐ ┌────────────┐ ┌────────────────┐
│ Qwen CLI   │ │ MCP Server │ │ Git (CLI)      │
│ (tasks)    │ │ (tools)    │ │ (worktrees)    │
└────────────┘ └─────┬──────┘ └────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌────────────┐ ┌────────────┐ ┌────────────────┐
│ WAL tools  │ │ Review     │ │ Project        │
│            │ │ tools      │ │ info tools     │
└────────────┘ └────────────┘ └────────────────┘
```

---

## 📦 Компоненты

### 1. Qwenex CLI

**Назначение:** Точка входа, парсинг аргументов, запуск оркестратора.

**Файлы:**
- `src/qwenex/cli.py` — CLI интерфейс (argparse/click)
- `src/qwenex/__init__.py` — версия, константы

**Команды:**
```bash
qwenex <plan.md>              # Выполнение плана
qwenex --review <plan.md>     # Review-only режим
qwenex --init                 # Инициализация проекта (BOOT.md, WAL.md)
qwenex --version              # Версия
qwenex --help                 # Помощь
```

---

### 2. Plan Parser

**Назначение:** Парсинг планов (FEAT/PROP или markdown).

**Файлы:**
- `src/qwenex/plan_parser.py` — парсинг markdown
- `src/qwenex/spec_loader.py` — загрузка FEAT/PROP

**Форматы:**
```markdown
# Формат A: FEAT/PROP
# FEAT-001: Название
**URI:** spec://module/FEAT-001
## 1. Цель
## 3. Пользовательские сценарии
## 4. Функциональные требования

# Формат B: Markdown (как ralphex)
# Plan: Название
## Validation Commands
- `go test ./...`
### Task 1: Название
- [ ] Задача 1
- [ ] Задача 2
```

---

### 3. Orchestrator

**Назначение:** Выполнение задач через Qwen CLI.

**Файлы:**
- `src/qwenex/orchestrator.py` — основной цикл
- `src/qwenex/task_executor.py` — выполнение задачи
- `src/qwenex/validator.py` — валидация (тесты/линтеры)

**Алгоритм:**
```
1. Прочитать план (FEAT/PROP или markdown)
2. Прочитать BOOT.md (контекст проекта)
3. Обновить WAL.md (текущая задача)
4. Для каждой задачи:
   a. Запустить Qwen CLI с промптом задачи
   b. Дождаться завершения
   c. Запустить валидацию (тесты/линтеры)
   d. Если не прошла → retry (max 2)
   e. Обновить прогресс
5. Запустить ревью (5 агентов)
6. Если ревью не прошло → итерация фикса
7. Обновить WAL.md (завершено)
```

---

### 4. Qwen CLI Integration

**Назначение:** Интеграция с Qwen CLI.

**Файлы:**
- `src/qwenex/models/base.py` — интерфейс LLMProvider
- `src/qwenex/models/qwen_cloud.py` — Qwen Cloud API
- `src/qwenex/models/ollama.py` — Ollama (задел на v0.2)
- `src/qwenex/qwen_client.py` — клиент для Qwen CLI

**Интерфейс:**
```python
class LLMProvider(Protocol):
    async def complete(self, prompt: str, **kwargs) -> str:
        """Получить ответ от модели"""
        pass
    
    async def check_health(self) -> bool:
        """Проверить доступность"""
        pass
```

---

### 5. Review System

**Назначение:** 5-агентное ревью (гибридное: 2+3).

**Файлы:**
- `src/qwenex/review.py` — основная логика
- `src/qwenex/review_agents.py` — агенты
- `src/qwenex/review_aggregator.py` — агрегация результатов

**Агенты:**
```
Фаза 1 (параллельно):
  - quality (баги, безопасность)
  - implementation (соответствие целям)

Фаза 2 (последовательно):
  - testing (покрытие тестов)
  - simplification (оверинжиниринг)
  - documentation (документация)
```

**Алгоритм:**
```python
# Параллельно
critical_results = await asyncio.gather(
    run_agent("quality", session_id),
    run_agent("implementation", session_id)
)

# Последовательно
other_results = []
for agent in ["testing", "simplification", "documentation"]:
    result = await run_agent(agent, session_id)
    other_results.append(result)

# Агрегация
all_findings = [*critical_results, *other_results]
```

---

### 6. MCP Server

**Назначение:** Инструменты для AI-агентов (Cline, Roo Code, etc.).

**Файлы:**
- `src/mcp/server.py` — MCP сервер
- `src/mcp/tools/wal.py` — WAL инструменты
- `src/mcp/tools/git.py` — Git инструменты
- `src/mcp/tools/qwen.py` — Qwen CLI инструменты
- `src/mcp/tools/review.py` — Ревью инструменты

**Инструменты:**
```python
# WAL инструменты
get_current_task()              → текущая задача
list_tasks(status?)             → список задач
update_task_status(id, status)  → обновить статус
add_completed_task(task, info)  → добавить в историю

# Git инструменты
git_status()                    → изменённые файлы
git_commit(message, files[])    → коммит
git_create_worktree(branch)     → создать worktree
git_merge(branch)               → merge в main

# Qwen инструменты
run_qwen_task(prompt, model)    → выполнить задачу
check_qwen_health()             → проверить доступность

# Review инструменты
launch_review_agents(session)   → запустить 5 агентов
aggregate_findings(results)     → агрегировать результаты
```

---

### 7. Progress Tracker

**Назначение:** Отслеживание прогресса, обновление WAL.md.

**Файлы:**
- `src/qwenex/progress.py` — трекинг прогресса
- `src/qwenex/wal_updater.py` — обновление WAL.md

**Обновления WAL:**
```python
def update_wal_task(task_id: str, status: str, notes: str = ""):
    """Обновить статус задачи в WAL.md"""
    content = WAL_PATH.read_text()
    
    # Найти задачу
    # Обновить статус
    # Сохранить
    
    WAL_PATH.write_text(updated, encoding="utf-8")
```

---

### 8. Git Integration

**Назначение:** Работа с git (worktrees, коммиты, merge).

**Файлы:**
- `src/qwenex/git_wrapper.py` — обёртка над git CLI

**Команды:**
```python
def create_worktree(branch: str, path: str):
    subprocess.run(["git", "worktree", "add", "-b", branch, path])

def commit(message: str, files: List[str]):
    for f in files:
        subprocess.run(["git", "add", f])
    subprocess.run(["git", "commit", "-m", message])

def merge(branch: str):
    subprocess.run(["git", "merge", branch])
```

---

## 🔄 Поток данных

### Выполнение плана

```
1. Пользователь: qwenex specs/FEAT-001.md
                    │
                    ▼
2. CLI: Парсинг аргументов
                    │
                    ▼
3. Plan Parser: Чтение FEAT-001.md
                    │
                    ▼
4. Orchestrator: Чтение BOOT.md (контекст)
                    │
                    ▼
5. WAL Updater: Обновление WAL.md (текущая задача)
                    │
                    ▼
6. Task Executor: Для каждой задачи:
   ┌────────────────────────────────────┐
   │ a. Qwen CLI: Запуск с промптом     │
   │ b. Validator: Тесты/линтеры        │
   │ c. Git Wrapper: Коммит             │
   │ d. WAL Updater: Обновление прогресса│
   └────────────────────────────────────┘
                    │
                    ▼
7. Review System: 5 агентов (гибридно)
                    │
                    ▼
8. Orchestrator: Если ревью не прошло → итерация
                    │
                    ▼
9. WAL Updater: Обновление WAL.md (завершено)
                    │
                    ▼
10. Конец
```

---

## 📁 Структура данных

### BOOT.md

```markdown
# BOOT: <Проект>

## Проект
[Описание]

## Стек
[язык · фреймворки]

## Принятые архитектурные решения
[Таблица решений]

## ЗАПРЕЩЕНО
[Список запретов]
```

### WAL.md

```markdown
# WAL: <Проект> v[X.X]

## ⚡ Текущая задача
**[FEAT-001]** — Название — в работе
- Следующий шаг: [действие]
- Статус: В работе

## ✅ Завершено
- [x] **[FEAT-NNN]** — описание · дата

## 📋 Очередь
- [ ] **[FEAT-NNN]** — описание · приоритет

## 🧠 Архитектурные решения (ADR)
- **[Дата]** Выбрали [X] — причина: [почему]
```

### FEAT-NNN.md

```markdown
# FEAT-NNN: Название

**URI:** spec://module/FEAT-NNN
**Версия:** X.X · **Статус:** Черновик

## 1. Цель
[1-2 предложения]

## 3. Пользовательские сценарии
- **Сценарий 1:** [действие] → [результат]

## 4. Функциональные требования
### 4.1 Компонент {#functional.name}
- [Требование]
- **Почему:** [причина]

## 6. Out of scope
- [Что не входит]

## 7. Тестовые сценарии
- `test_name`: [условие] → [результат]
```

---

## 🔒 Безопасность

### Изоляция

**Docker (v0.3):**
```dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# Установка qwenex
RUN pip install qwenex

# Монтирование проекта
VOLUME /workspace

# Запуск
ENTRYPOINT ["qwenex"]
```

### Секреты

**Конфигурация:**
```yaml
# ~/.qwenex/config.yaml
providers:
  qwen_cloud:
    api_key: ${QWEN_API_KEY}  # ENV variable
```

---

## 📊 Масштабирование

### Параллелизм

**Гибридные субагенты:**
- 2 параллельно (quality, implementation)
- 3 последовательно (testing, simplification, documentation)

**Параллельные сессии (v0.2 через dmux):**
```bash
dmux new  # Создаёт сессию
qwenex FEAT-001.md  # Запускает в сессии
```

---

## 🧪 Тестирование

### Уровни

**Unit тесты:**
```python
# tests/test_plan_parser.py
def test_parse_feat_spec():
    spec = parse("specs/FEAT-001.md")
    assert spec.goal == "..."
```

**Integration тесты:**
```python
# tests/test_orchestrator.py
async def test_orchestrator_loop():
    orchestrator = Orchestrator(plan="FEAT-001.md")
    await orchestrator.run()
```

**E2E тесты:**
```python
# tests/e2e/test_full_flow.py
def test_full_plan_execution():
    run("qwenex specs/FEAT-001.md")
    assert WAL_PATH.read_text().contains("завершено")
```

---

## 📈 Метрики

### Производительность

| Метрика | Цель | Измерение |
|---------|------|-----------|
| Время задачи | ≤ 10 мин | От запуска до коммита |
| Время ревью | ≤ 5 мин | 5 агентов |
| Итераций на план | 1-3 | До завершения |

### Качество

| Метрика | Цель | Измерение |
|---------|------|-----------|
| Покрытие тестами | 80%+ | pytest-cov |
| Пройдено ревью | 90%+ | С первого раза |
| Успешных планов | 95%+ | Без.failures |

---

## 🔮 Расширяемость

### Новые провайдеры

```python
# src/qwenex/models/openai.py
class OpenAIProvider(LLMProvider):
    async def complete(self, prompt: str, **kwargs) -> str:
        # Реализация
```

### Новые инструменты MCP

```python
# src/mcp/tools/browser.py
class BrowserTools:
    def get_tool_definitions(self):
        return [
            types.Tool(name="open_url", ...),
        ]
```

---

## История версий

| Версия | Дата | Изменение |
|--------|------|-----------|
| 1.0 | 2026-02-26 | Initial version — черновик архитектуры |
