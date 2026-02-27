# FEAT-007: Code Review qwenex

**URI:** spec://qwenex/FEAT-007
**Версия:** 0.1.0 · **Статус:** Черновик

---

## 1. Цель

Провести полную проверку кода проекта qwenex на качество, безопасность и соответствие best practices.

---

## 2. Пользовательские сценарии

- **Сценарий 1:** Запуск статического анализа (mypy, ruff, bandit)
- **Сценарий 2:** Проверка покрытия тестами
- **Сценарий 3:** Поиск undocumented public API
- **Сценарий 4:** Проверка обработки ошибок
- **Сценарий 5:** Генерация отчёта с приоритетами

---

## 3. Функциональные требования

### 3.1 Статический анализ

Запуск mypy, ruff, bandit, pylint для всех модулей qwenex.

**Почему:** Автоматическое выявление проблем кода

### 3.2 Проверка тестов

Запуск pytest с coverage, поиск слабых тестов.

**Почему:** Обеспечение качества тестовой базы

### 3.3 Проверка документации

Проверка docstrings, актуальности README, ссылок.

**Почему:** Документация должна быть полной

### 3.4 Отчёт

Сбор всех находок, приоритизация (critical, major, minor).

**Почему:** Удобство исправления

---

## 4. Out of scope

- Автоматические фиксы (только отчёт)
- Интеграция с CI (отдельная задача)

---

## 5. Тестовые сценарии

- `test_mypy_pass`: mypy не выдаёт ошибок
- `test_ruff_pass`: ruff не выдаёт ошибок
- `test_coverage_threshold`: coverage >= 80%
- `test_docstrings_present`: все public API имеют docstrings

---

## 6. Validation Commands

- `mypy src/qwenex --ignore-missing-imports`
- `ruff check src/qwenex`
- `pytest src/tests/ -v --cov=src/qwenex --cov-report=term-missing`
- `bandit -r src/qwenex`
