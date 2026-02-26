# Извлечённые знания о ralphex v0.18.0

**Дата:** 2026-02-27  
**Версия:** 1.0  
**Статус:** Завершено

---

## 📋 Обзор

Этот документ суммирует знания о ralphex v0.18.0, извлечённые в процессе анализа для Qwenex.

---

## 🏗️ Архитектура ralphex v0.18.0

### Ключевые компоненты

```
ralphex/
├── cmd/ralphex/
│   └── main.go              # Точка входа, worktree integration
├── pkg/
│   ├── executor/
│   │   ├── executor.go      # Базовый интерфейс
│   │   ├── claude.go        # Claude executor
│   │   └── codex.go         # Codex executor
│   ├── git/
│   │   └── service.go       # Git service с worktree операциями
│   ├── config/
│   │   └── config.go        # Конфигурация с VcsCommand
│   ├── progress/
│   │   └── progress.go      # Progress tracking
│   └── web/
│       └── dashboard.go     # Web dashboard
```

---

## 🔑 Ключевые функции v0.18.0

### 1. Worktree Isolation Mode

**Файл:** `cmd/ralphex/main.go`  
**Функции:**
- `runWithWorktree(ctx, o, req)` — запуск в worktree
- `worktreeCleanupFn` — функция очистки
- `CreateWorktreeForPlan(planFile)` — создание worktree для плана

**Алгоритм:**
```
1. Создать worktree: git worktree add -b <branch> <path>
2. Скопировать план в worktree
3. Chdir в worktree
4. Выполнить план
5. Очистить worktree после завершения
```

**Конфигурация:**
```ini
[ralphex]
use_worktree = true
```

**CLI флаг:**
```bash
ralphex --worktree docs/plans/feature.md
```

**Применение для Qwenex:**
```python
# src/qwenex/git_wrapper.py
def create_worktree(branch: str, path: str):
    subprocess.run(["git", "worktree", "add", "-b", branch, path])

def remove_worktree(path: str):
    subprocess.run(["git", "worktree", "remove", "--force", path])
```

---

### 2. ensureGitIgnored

**Файл:** `cmd/ralphex/main.go`  
**Функция:** `ensureGitIgnored(gitSvc, patternPairs...)`

**Алгоритм:**
```
1. Проверить .gitignore на изменения (FileHasChanges)
2. Для каждой пары (pattern, probePath):
   - Добавить pattern в .gitignore
3. Если .gitignore было чисто → закоммитить изменения
```

**Применение:**
```go
// В ralphex
ensureGitIgnored(gitSvc,
    ".ralphex/progress/", ".ralphex/progress/progress-test.txt",
    ".ralphex/worktrees/", ".ralphex/worktrees/test")
```

**Применение для Qwenex:**
```python
# src/qwenex/git_wrapper.py
def ensure_git_ignored(patterns: list[str]):
    """Добавить паттерны в .gitignore и закоммитить если чисто"""
    # 1. Проверить git status .gitignore
    # 2. Добавить паттерны
    # 3. Закоммитить если было чисто
```

---

### 3. VCS абстракция

**Файл:** `pkg/config/config.go`  
**Поле:** `VcsCommand string`

**Конфигурация:**
```ini
[ralphex]
vcs_command = git
# или
vcs_command = /path/to/hg
```

**Применение:**
```go
// pkg/git/service.go
func NewService(root string, logger *log.Logger, vcsCommand string) (*Service, error)
```

**Применение для Qwenex:**
```python
# src/qwenex/config.py
class Config:
    vcs_command: str = "git"  # или путь к wrapper скрипту
```

---

### 4. MaxExternalIterations

**Файл:** `pkg/config/config.go`  
**Поле:** `MaxExternalIterations int`

**Конфигурация:**
```ini
[ralphex]
max_external_iterations = 3
```

**CLI флаг:**
```bash
ralphex --max-external-iterations=5 docs/plans/feature.md
```

**Применение для Qwenex:**
```python
# src/qwenex/config.py
class Config:
    max_external_iterations: int = 0  # 0 = auto
```

---

### 5. Host config для Web dashboard

**Файл:** `cmd/ralphex/main.go`  
**Поле:** `Host string`

**Конфигурация:**
```ini
[ralphex]
host = 127.0.0.1
```

**CLI флаг:**
```bash
ralphex --serve --host 0.0.0.0 --port 8080 docs/plans/feature.md
```

**Применение для Qwenex:**
```python
# src/qwenex/dashboard.py
class Dashboard:
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
```

---

## 📊 Что заимствуем для Qwenex

### ✅ Концепции (заимствуем архитектуру)

| Функция | ralphex реализация | Qwenex реализация |
|---------|-------------------|-------------------|
| **Worktree isolation** | `runWithWorktree()` | `create_worktree()` (Python subprocess) |
| **ensureGitIgnored** | `ensureGitIgnored()` | `ensure_git_ignored()` (Python subprocess) |
| **VCS абстракция** | `VcsCommand` конфиг | `vcs_command` в config.py |
| **5-агентное ревью** | Параллельно (Claude Task) | Гибридно (2+3 asyncio) |
| **Progress tracking** | `.ralphex/progress/*.txt` | `.qwenex/progress/*.txt` |
| **Web dashboard** | Go + SSE | Python + FastMCP (задел) |

### ❌ НЕ заимствуем (пишем с нуля)

| Компонент | Почему |
|-----------|--------|
| **Код** | Пишем на Python, не копируем Go |
| **Executor** | QwenExecutor уже написан, не нужен Claude/Codex |
| **MCP сервер** | Уникальная фича Qwenex, нет в ralphex |
| **BOOT/WAL/FEAT/PROP** | Уникальная система спецификаций |
| **Трансформация планов** | AI-фича, проще на Python |

---

## 🎯 Архитектурные параллели

### ralphex (Go) → Qwenex (Python)

```
ralphex                              Qwenex
├── cmd/ralphex/main.go             ├── src/qwenex/cli.py
├── pkg/executor/executor.go        ├── src/qwenex/orchestrator.py
├── pkg/executor/claude.go          ├── src/qwenex/qwen_executor.py
├── pkg/git/service.go              ├── src/qwenex/git_wrapper.py
├── pkg/config/config.go            ├── src/qwenex/config.py
├── pkg/progress/progress.go        ├── src/qwenex/progress.py
├── pkg/web/dashboard.go            ├── src/qwenex/dashboard.py (задел)
└── (нет MCP)                       └── src/mcp/server.py ✅ Уникальное
```

---

## 📚 Ссылки на файлы ralphex

| Файл | Назначение | Строки |
|------|------------|--------|
| `cmd/ralphex/main.go` | Точка входа, worktree, ensureGitIgnored | 1-1052 |
| `pkg/git/service.go` | Git service, worktree операции | 1-490 |
| `pkg/config/config.go` | Конфигурация с VcsCommand | 1-324 |
| `pkg/executor/executor.go` | Базовый интерфейс executor | 1-200+ |

---

## 💡 Уроки из ralphex

### ✅ Что делаем так же

1. **Worktree isolation** — изоляция задач через git worktree
2. **ensureGitIgnored** — авто-коммит .gitignore изменений
3. **Progress файлы** — `.qwenex/progress/*.txt` для web dashboard
4. **5-агентное ревью** — гибридное выполнение (2+3)
5. **CLI флаги** — аналогичные ralphex (--worktree, --serve, --port)

### ❌ Что делаем иначе

1. **Язык** — Python вместо Go (MCP SDK, AI-экосистема)
2. **MCP сервер** — нативный Python (уникальная фича)
3. **BOOT/WAL/FEAT/PROP** — структурированные спецификации
4. **Трансформация планов** — AI из простого плана → FEAT/PROP
5. **Qwen executor** — поддержка Qwen CLI вместо Claude

---

## 🔒 Лицензионная чистота

**ralphex лицензия:** MIT  
**Qwenex лицензия:** MIT

**Правила заимствования:**
- ✅ Заимствуем концепции (архитектура, алгоритмы)
- ✅ Заимствуем идеи (worktree isolation, ensureGitIgnored)
- ❌ НЕ копируем код (пишем свой на Python)
- ❌ НЕ копируем структуру файлов (своя организация)

**Обоснование:**
- Архитектурные решения не защищаются авторским правом
- Алгоритмы (worktree, ensureGitIgnored) — общие идеи
- Реализация на Python — оригинальный код

---

## 📈 Метрики заимствования

| Аспект | % заимствования | Комментарий |
|--------|-----------------|-------------|
| **Архитектура** | 60% | Заимствуем концепции ralphex |
| **Код** | 0% | Пишем свой на Python |
| **Тесты** | 0% | Пишем свои (pytest) |
| **Документация** | 20% | Ссылки на ralphex как референс |
| **CLI интерфейс** | 40% | Похожие флаги (--worktree, --serve) |

---

## История версий

| Версия | Дата | Изменение |
|--------|------|-----------|
| 1.0 | 2026-02-27 | Initial version — извлечённые знания о ralphex v0.18.0 |
