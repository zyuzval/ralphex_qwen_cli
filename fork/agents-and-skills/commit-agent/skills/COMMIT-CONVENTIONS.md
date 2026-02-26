# COMMIT-CONVENTIONS

## Для кого
CommitAgent и PRAgent — формат коммит-сообщений и правила для этого проекта.

## Контекст
История коммитов tg-stats должна быть читаемой и связанной с сессиями. Из лога должно быть понятно: что изменили, в рамках какой сессии, без чтения кода.

---

## Формат сообщения

```
<type>(<scope>): <description>

[SESSION-XXX если применимо]
[Опциональное тело: что именно изменено]
```

### Типы (type)

| Тип | Когда использовать |
|-----|-------------------|
| `feat` | Новая функциональность |
| `fix` | Исправление бага |
| `refactor` | Изменение кода без изменения поведения |
| `test` | Добавление или исправление тестов |
| `docs` | Изменения в документации |
| `chore` | Конфиг, зависимости, скрипты |
| `perf` | Улучшение производительности |

### Scope (область)

Для tg-stats используемые scopes:

| Scope | Область |
|-------|---------|
| `analysis` | src/analysis/ — sentiment, stats, network |
| `api` | FastAPI endpoints |
| `core` | src/core/ — loader, storage |
| `web` | React компоненты |
| `d3` | D3 граф взаимодействий |
| `mcp` | MCP-сервер |
| `config` | Конфигурация, зависимости |
| `tests` | Тесты (когда scope = тесты) |

---

## Примеры правильных сообщений

```bash
# Исправление из сессии
fix(analysis): remove 'золот' from negative sentiment words

SESSION-001
- Removed false positive from NEGATIVE_WORDS set
- Added overlap assertion in tests

# Новая функция
feat(web): add language switcher component

Supports RU/EN via i18next. Toggle in header.

# Производительность
perf(analysis): add lru_cache to lemmatizer

SESSION-004
Cache size: 10000 entries
~40x speedup on repeated words

# Только тесты
test(core): add streaming loader tests for large files

# Документация
docs(mcp): add MCP server setup guide
```

---

## Примеры неправильных сообщений

```bash
# ❌ Слишком общее
fix: fixed stuff

# ❌ Нет типа
sentiment analysis fix

# ❌ Прошедшее время (используй настоящее)
fixed: removed wrong word from negative set

# ❌ Слишком длинный первый заголовок (>72 символов)
fix(analysis): remove the word золот from the NEGATIVE_WORDS dictionary because it was causing false positives

# ❌ Нет scope для кода
fix: websocket cleanup in upload component
```

---

## Правила для этого проекта

1. **Первая строка ≤ 72 символа** — умещается в `git log --oneline`
2. **Настоящее время** — "add", не "added"
3. **SESSION-XXX** — указывать если коммит закрывает сессию исправлений
4. **Тело через пустую строку** — если нужно объяснить что именно изменено
5. **Английский язык** — сообщения на английском, независимо от языка кода

---

## Что никогда не попадает в коммит

Из `.gitignore` этого проекта:
- `data/` — экспорты Telegram (личные и большие)
- `.cache/` — кэш результатов анализа
- `output/` — сгенерированные графики
- `__pycache__/`, `.venv/`, `.env`
- `web/node_modules/`

Если `git status` показывает эти файлы — они не добавляются в `git add`.

---

## Что НЕ входит в этот скилл

- Как делать git branching (не используется в этом проекте)
- GitHub/GitLab PR процесс (нет remote)
- Как откатывать коммиты (это отдельная операция, не автоматизирована)
