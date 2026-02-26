# Qwenex

**Автономное выполнение планов разработки с Qwen CLI, структурированными спецификациями и MCP-инструментами.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: MVP Development](https://img.shields.io/badge/status-MVP%20development-orange)](./WAL.md)

---

## 📋 О проекте

**Qwenex** — это оркестратор для автономного выполнения планов разработки через Qwen CLI. Напишите план с задачами, запустите Qwenex и вернитесь к готовой реализации с code review.

### Ключевые особенности

- **Спецификации BOOT/WAL/FEAT/PROP** — структурированный контекст для AI-агентов
- **MCP-инструменты** — интеграция с Cline, Roo Code, Continue через Model Context Protocol
- **5-агентное ревью** — гибридное выполнение (2 параллельно + 3 последовательно)
- **Свежий контекст** — каждая задача = новая сессия Qwen CLI (нет деградации)
- **Локальные модели** — задел на Ollama для приватности и экономии
- **Трансформация планов** — простые планы → полноценные FEAT/PROP спецификации (v0.2)

---

## 🚀 Быстрый старт

### Установка (в разработке)

```bash
# Пока не готово к установке
# git clone https://github.com/yourusername/qwenex.git
# cd qwenex
# pip install -e .
```

### Требования

- Python 3.11+
- Qwen CLI (`pip install qwen-coder` или через Ollama)
- Git 2.20+
- tmux (опционально, для параллельных сессий)

### Использование

```bash
# Выполнение плана
qwenex specs/FEAT-001.md

# Review-only режим
qwenex --review specs/FEAT-001.md

# Инициализация проекта
qwenex --init
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [BOOT.md](./BOOT.md) | Конституция проекта — архитектурные решения, правила |
| [WAL.md](./WAL.md) | Текущий статус, задачи, прогресс разработки |
| [docs/COMPETITORS.md](./docs/COMPETITORS.md) | Анализ конкурентов (cmux, dmux, Sim, ralphex) |
| [docs/DECISIONS.md](./docs/DECISIONS.md) | Архитектурные решения (ADR) |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Детальная архитектура системы |

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Qwenex CLI                            │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │  Plan Parser  │  │  Orchestrator │  │  Progress   │ │
│  │  (FEAT/PROP)  │  │  (tasks loop) │  │  Tracker    │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
└────────────────────┬────────────────────────────────────┘
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

## 📊 Сравнение с аналогами

| Функция | Qwenex | ralphex | dmux | Aider |
|---------|--------|---------|------|-------|
| **Оркестрация задач** | ✅ | ✅ | ❌ | ⚠️ |
| **Code review (5 агентов)** | ✅ | ✅ | ❌ | ❌ |
| **Спецификации (FEAT/PROP)** | ✅ | ⚠️ | ❌ | ❌ |
| **MCP-инструменты** | ✅ | ❌ | ❌ | ❌ |
| **Параллельные сессии** | ⚠️ (v0.2) | ❌ | ✅ | ❌ |
| **Локальные модели** | ✅ | ❌ | ⚠️ | ✅ |
| **Трансформация планов** | ✅ | ❌ | ❌ | ❌ |

---

## 🗺️ Roadmap

### MVP (Недели 1-4)

- [x] BOOT.md, WAL.md для Qwenex
- [x] docs/COMPETITORS.md, docs/DECISIONS.md
- [ ] FEAT-001 (Ядро оркестратора)
- [ ] FEAT-002 (Система ревью)
- [ ] FEAT-003 (MCP сервер)
- [ ] Базовые MCP инструменты (WAL, git, Qwen CLI)
- [ ] Unit тесты (80%+ покрытие)

### v0.2 (Недели 5-8)

- [ ] Трансформация планов (план → FEAT/PROP)
- [ ] Локальные модели (Ollama)
- [ ] Интеграция с dmux (параллельные сессии)
- [ ] Другие провайдеры (OpenAI, Anthropic)

### v0.3 (Недели 9-12)

- [ ] Web dashboard (real-time мониторинг)
- [ ] Docker изоляция
- [ ] Интеграция с cmux (уведомления)
- [ ] Уведомления (Telegram, Email, Slack)

---

## 🎯 Принципы

### Spec-driven Development

1. **Спеки > Код** — при конфликте багуется код, не спека
2. **REVIEW-маркеры** — AI предлагает, человек решает
3. **Контекст мотивации** — «Почему» важнее «что»
4. **Одна задача** — только одна активная задача в WAL.md

### Human-in-the-Loop

- AI не меняет спеки молча
- REVIEW-маркеры для предложений
- Человек контролирует критичные изменения

---

## 🤝 Интеграции

### MCP-инструменты

Qwenex предоставляет MCP-сервер для AI-агентов:

```json
// ~/.config/claude/settings.json
{
  "mcpServers": {
    "qwenex": {
      "command": "python",
      "args": ["-m", "qwenex.mcp.server"]
    }
  }
}
```

**Доступные инструменты:**
- `get_current_task()` — текущая задача из WAL
- `update_task_status(id, status)` — обновить статус
- `run_qwen_task(prompt)` — выполнить задачу
- `git_commit(message, files)` — коммит
- `launch_review_agents()` — 5 агентов ревью

### dmux (v0.2)

Параллельные сессии через dmux:

```bash
dmux new  # Создать сессию
qwenex FEAT-001.md  # Запустить в сессии
```

### cmux (v0.3)

Уведомления через OSC последовательности:

```python
# Qwenex отправляет
print("\033]99;Qwenex;Task completed\007")

# cmux перехватывает и показывает уведомление
```

---

## 🛠️ Разработка

### Структура проекта

```
qwenex/
├── BOOT.md                    ← Конституция
├── WAL.md                     ← Текущий статус
├── docs/
│   ├── COMPETITORS.md        ← Анализ конкурентов
│   ├── DECISIONS.md          ← ADR
│   └── ARCHITECTURE.md       ← Архитектура
├── specs/
│   ├── FEAT-001.md           ← Ядро
│   ├── FEAT-002.md           ← Ревью
│   └── FEAT-003.md           ← MCP
├── src/
│   ├── qwenex/
│   │   ├── cli.py
│   │   ├── orchestrator.py
│   │   ├── review.py
│   │   └── models/
│   └── mcp/
│       ├── server.py
│       └── tools/
├── tests/
└── pyproject.toml
```

### Запуск тестов

```bash
# Unit тесты
pytest tests/unit -v

# Integration тесты
pytest tests/integration -v

# Покрытие
pytest --cov=src/qwenex --cov-report=html
```

---

## 📈 Метрики

| Метрика | Цель | Текущее |
|---------|------|---------|
| Покрытие тестами | 80%+ | 0% (MVP) |
| Время задачи | ≤ 10 мин | — |
| Время ревью | ≤ 5 мин | — |
| Успешных планов | 95%+ | — |

---

## 📝 Лицензия

MIT — см. [LICENSE](LICENSE) для деталей.

---

## 🙋 Contributing

### Как помочь

1. Fork репозиторий
2. Создай ветку (`git checkout -b feature/amazing-feature`)
3. Закоммить изменения (`git commit -m 'Add amazing feature'`)
4. Запуш (`git push origin feature/amazing-feature`)
5. Открой Pull Request

### Правила

- Следуй BOOT.md (конституция проекта)
- Обновляй WAL.md (текущий статус)
- Пиши тесты (80%+ покрытие)
- Документируй изменения

---

## 📞 Контакты

- **Issues:** [GitHub Issues](https://github.com/yourusername/qwenex/issues)
- **Обсуждения:** [GitHub Discussions](https://github.com/yourusername/qwenex/discussions)

---

## 📚 Благодарности

- **ralphex** — вдохновение и референс для оркестрации планов
- **dmux** — идея параллельных сессий через worktrees
- **Aider** — Git-native подход к AI-ассистентам
- **Sim** — визуальный конструктор workflows

---

## 📰 История версий

| Версия | Дата | Статус |
|--------|------|--------|
| 0.1.0 | 2026-02-26 | MVP разработка (документация) |

---

**Статус:** 🚧 MVP в разработке. Следите за прогрессом в [WAL.md](./WAL.md).
