# AGENTS — Реестр агентов проекта

## Начало каждой сессии — обязательно

1. Прочитай `BOOT.md` — структура проекта, запреты, архитектура
2. Прочитай `WAL.md` — текущая задача и состояние
3. Если в WAL есть ссылка на спеку — прочитай только указанную секцию

## Правила работы (для всех агентов)

- Работай только в рамках текущей задачи из WAL#current-task
- Не трогай файлы вне задачи, даже если видишь «улучшения»
- Не добавляй зависимости без явного запроса
- При конфликте: Человек > Спека > Код > Тесты
- Спека кажется ошибочной → добавь `# REVIEW: [описание]` в коде, не трогай спеку
- После выполнения → обнови WAL.md (раздел «Завершено» и «Текущая задача»)

---

## Реестр агентов

### Код

| Агент | Файл | Роль | Запускает |
|-------|------|------|-----------|
| ReviewAgent | `agents/review-agent/AGENT.md` | Находит проблемы в коде | Coordinator / человек |
| FixAgent | `agents/fix-agent/AGENT.md` | Применяет исправления из сессии | Coordinator |
| RefactorAgent | `agents/refactor-agent/AGENT.md` | Улучшает структуру без изменения поведения | Человек |
| LinterAgent | `agents/linter-agent/AGENT.md` | Статический анализ всего проекта | Человек |
| TestWriterAgent | `agents/test-writer-agent/AGENT.md` | Пишет тесты для существующего кода | Человек |
| DebugAgent | `agents/debug-agent/AGENT.md` | Диагностирует ошибки и упавшие тесты | Человек / FixAgent |

### Процесс

| Агент | Файл | Роль | Запускает |
|-------|------|------|-----------|
| CommitAgent | `agents/commit-agent/AGENT.md` | Проверяет и создаёт коммиты | Coordinator |
| ContextAgent | `agents/context-agent/AGENT.md` | Сводка состояния проекта | Человек (начало сессии) |
| ArchReviewAgent | `agents/arch-review-agent/AGENT.md` | Проверяет соответствие архитектуре | Человек (периодически) |
| DocsAgent | `agents/docs-agent/AGENT.md` | Синхронизирует документацию с кодом | Человек |
| PRAgent | `agents/pr-agent/AGENT.md` | Описание изменений для changelog | Человек |

---

## Типичные цепочки

### Ревью → Исправление → Коммит (основной workflow)

```
Человек запускает ReviewAgent
    ↓ docs/reviews/YYYY-MM-DD-module-review.md
Coordinator создаёт SESSION-XXX из review
    ↓ docs/sessions/SESSION-XXX/session.md
FixAgent применяет исправления
    ↓ docs/sessions/SESSION-XXX/iteration-01/status.json
CommitAgent коммитит если ready_to_commit: true
    ↓ git commit
Coordinator обновляет WAL.md
```

### Начало рабочей сессии

```
Человек запускает ContextAgent
    ↓ сводка в stdout
Человек принимает решение что делать дальше
```

### Диагностика заблокированной сессии

```
FixAgent заблокирован (3 итерации)
    ↓ status: blocked
Человек запускает DebugAgent с ошибкой из report.md
    ↓ гипотезы и шаги проверки
Человек исправляет вручную или создаёт новую сессию
```

---

## Карта скиллов

| Скилл | Используется в |
|-------|----------------|
| `agents/review-agent/skills/REVIEW-PATTERNS.md` | ReviewAgent |
| `agents/review-agent/skills/CODE-QUALITY.md` | ReviewAgent |
| `agents/fix-agent/skills/FIX-PATTERNS.md` | FixAgent |
| `agents/fix-agent/skills/TESTING.md` | FixAgent, TestWriterAgent |
| `agents/commit-agent/skills/COMMIT-CONVENTIONS.md` | CommitAgent, PRAgent |
| `agents/context-agent/skills/PROJECT-CONTEXT.md` | ContextAgent |
| `agents/arch-review-agent/skills/ARCH-PATTERNS.md` | ArchReviewAgent |
| `agents/docs-agent/skills/DOCS-PATTERNS.md` | DocsAgent |
| `agents/pr-agent/skills/PR-PATTERNS.md` | PRAgent |
| `agents/debug-agent/skills/DEBUG-PATTERNS.md` | DebugAgent |
| `agents/linter-agent/skills/LINT-RULES.md` | LinterAgent |
| `agents/test-writer-agent/skills/TEST-PATTERNS.md` | TestWriterAgent |
| `agents/refactor-agent/skills/REFACTOR-PATTERNS.md` | RefactorAgent |
