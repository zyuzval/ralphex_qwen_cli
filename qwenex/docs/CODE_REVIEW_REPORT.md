# Code Review Report: qwenex

**Дата:** 2026-02-27  
**Инструменты:** mypy, ruff (pending), bandit (pending)  
**Статус:** 🟡 В работе

---

## 📊 Summary

| Метрика | Значение |
|---------|----------|
| **Всего ошибок mypy** | 91 |
| **Файлов с ошибками** | 23 из 42 |
| **Critical** | 12 |
| **Major** | 35 |
| **Minor** | 44 |

---

## 🔴 Critical Issues (12)

### 1. Protocol mismatch: LLMProvider.stream()

**Файлы:** `models/fallback.py:41,50`, `cli.py:236,245`

**Проблема:**
```python
# Ожидается (Protocol):
async def stream(...) -> Coroutine[Any, Any, AsyncIterator[str]]

# Получено:
async def stream(...) -> AsyncIterator[str]
```

**Решение:** Исправить signature методов stream() во всех provider classes.

---

### 2. Missing await в progress.py

**Файлы:** `progress.py:70,80,90,94,102,110,114,123,126`

**Проблема:**
```python
async def task_started(...):
    self.log(...)  # ← coroutine not awaited
    await self._notify(...)
```

**Решение:** Добавить `await` перед `self.log(...)`.

---

### 3. Missing await в orchestrator.py

**Файлы:** `orchestrator.py:114,151,161,181,184,192,195,201,210,220,235,243,264,274`

**Проблема:**
```python
async def execute_task_with_retry(...):
    self.progress.task_started(...)  # ← not awaited
```

**Решение:** Добавить `await` перед вызовами `self.progress.*`.

---

### 4. Async iterator error в qwen_executor.py

**Файлы:** `qwen_executor.py:78`, `fallback.py:109,119`

**Проблема:**
```python
async for chunk in self.provider.stream(prompt, system_prompt):
    # ← "Coroutine" has no attribute "__aiter__"
```

**Решение:** Добавить `await` перед `self.provider.stream(...)`.

---

## 🟡 Major Issues (35)

### 5. Missing type parameters

**Файлы:** `git_wrapper.py:39`, `progress.py:26`, `transformer.py:143`, `broadcast.py:16`, `cli.py:19,145`, `mcp/tools/*.py`

**Проблема:**
```python
def get_config() -> dict:  # ← Missing type parameters
    ...
```

**Решение:** Заменить на `dict[str, Any]` или конкретные типы.

---

### 6. Returning Any from function

**Файлы:** `git_wrapper.py:157,166`, `qwen_cloud.py:66`, `openai.py:64`, `ollama.py:60`, `transformer.py:163`, `config.py:30`

**Проблема:**
```python
def last_commit_hash(self) -> str:
    result = self._run(...)
    return result.stdout.strip()  # ← Returning Any
```

**Решение:** Добавить cast или изменить тип возвращаемого значения.

---

### 7. Missing return type annotations

**Файлы:** `review/cli.py:23`, `web/cli.py:7`, `web/server.py:22,27,32`, `web/broadcast.py:26`, `cli.py:135,272,277`, `mcp/cli.py:31,48`

**Проблема:**
```python
def entry_point():  # ← Missing return type
    ...
```

**Решение:** Добавить `-> None` для функций без возврата значения.

---

## 🟢 Minor Issues (44)

### 8. Incompatible types в stream parsing

**Файлы:** `qwen_cloud.py:111,112,114`, `openai.py:109,110,112`

**Проблема:**
```python
async for line in response.content:  # line is bytes
    if line.startswith('data: '):  # ← str vs bytes
```

**Решение:** Использовать bytes для сравнения: `b'data: '`.

---

### 9. Missing type annotations в MCP tools

**Файлы:** `mcp/tools/wal.py:53,88`, `mcp/tools/qwen.py:31,47`, `mcp/tools/ollama.py:27,43`, `mcp/tools/git.py:10`, `mcp/tools/config.py:15,54`

**Проблема:**
```python
async def wal_start_session() -> str:
    ...
    return {"error": "..."}  # ← dict, not str
```

**Решение:** Исправить return type на `str | dict`.

---

## 📋 План исправлений

### P0 (Critical)
1. Исправить `LLMProvider.stream()` signature
2. Добавить `await` в progress.py (9 мест)
3. Добавить `await` в orchestrator.py (14 мест)
4. Исправить async iterator в qwen_executor.py

### P1 (Major)
5. Добавить type parameters для dict, list
6. Исправить Returning Any (6 мест)
7. Добавить return type annotations (9 мест)

### P2 (Minor)
8. Исправить bytes vs str в stream parsing
9. Добавить type annotations в MCP tools

---

## ✅ Следующие шаги

1. Исправить P0 critical issues
2. Запустить mypy снова
3. Исправить P1 major issues
4. Запустить ruff для style checks
5. Запустить bandit для security checks
