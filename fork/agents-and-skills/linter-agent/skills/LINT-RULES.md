# LINT-RULES

## Для кого
LinterAgent — конфигурация и команды линтеров в tg-stats.

---

## Python

### Инструменты и команды

```bash
# flake8 — стиль и базовые ошибки
flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__

# mypy — типы
mypy src/ --ignore-missing-imports --strict

# black — форматирование (только проверка)
black src/ tests/ --check --line-length=100

# black — применить форматирование (только при fix=true)
black src/ tests/ --line-length=100
```

### Приоритеты ошибок Python

| Код | Тип | Приоритет |
|-----|-----|-----------|
| E9xx, F8xx | Синтаксис, неиспользуемый импорт | Error |
| mypy error | Неверные типы | Error |
| E7xx | Отступы, пустые строки | Warning |
| W | Предупреждения стиля | Warning |
| E5xx | Длина строки | Style |

---

## TypeScript

### Инструменты и команды

```bash
# TypeScript compiler — типы
cd web && npx tsc --noEmit

# ESLint — стиль и паттерны
cd web && npx eslint src/ --ext .ts,.tsx

# Prettier — форматирование (только проверка)
cd web && npx prettier --check src/

# Prettier — применить (только при fix=true)
cd web && npx prettier --write src/
```

### Приоритеты ошибок TypeScript

| Тип | Приоритет |
|-----|-----------|
| TS compiler error | Error |
| ESLint error | Error |
| ESLint warning | Warning |
| Prettier diff | Style |

---

## Конфигурации

Конфиги находятся в:
- `setup.cfg` или `.flake8` — flake8
- `mypy.ini` или `pyproject.toml` — mypy
- `web/.eslintrc.json` — ESLint
- `web/.prettierrc` — Prettier

Не изменять конфиги — только использовать существующие.

---

## Что НЕ входит в этот скилл

- Как исправлять найденные ошибки (это для FixAgent)
- Настройка новых линтеров
- CI/CD интеграция
