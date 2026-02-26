# TESTING

## Для кого
FixAgent — как запускать тесты и интерпретировать результаты в контексте исправлений.

## Контекст
Тесты — единственный объективный критерий что исправление не сломало ничего лишнего. Важно знать не только как запустить, но и как правильно интерпретировать результат.

---

## Команды запуска

```bash
# Все тесты
python -m pytest tests/ -v --tb=short

# Конкретный модуль
python -m pytest tests/analysis/ -v
python -m pytest tests/api/ -v
python -m pytest tests/core/ -v

# Конкретный файл
python -m pytest tests/analysis/test_sentiment.py -v

# Конкретный тест
python -m pytest tests/analysis/test_sentiment.py::test_negative_words -v

# С покрытием
python -m pytest tests/ --cov=src --cov-report=term-missing
```

Через MCP: `run_tests(module="tests/analysis/")` — предпочтительно.

---

## Интерпретация результатов

### Тест прошёл — всё ли хорошо?

Не всегда. Тест может проходить и при неверном поведении если он плохо написан. Дополнительно проверять:

- Тест проверяет именно то что мы исправили?
- Нет ли в тесте хардкоженных значений которые совпали случайно?

### Тест упал — мой ли это баг?

```bash
# Проверить состояние до исправления
git stash
python -m pytest tests/путь -v
# Если тест падал до — это не мой баг
git stash pop
```

### Типичные причины падения тестов после исправления

| Причина | Симптом | Решение |
|---------|---------|---------|
| Изменил публичный интерфейс | `TypeError: function() got unexpected argument` | Вернуть старую сигнатуру |
| Изменил формат данных | `KeyError: 'old_field'` | Проверить что все поля на месте |
| Изменил поведение кэша | Тесты падают недетерминированно | Сбросить кэш между тестами |
| Сломал импорт | `ImportError` | Проверить что импорты актуальны |

---

## Особенности тестов этого проекта

### 146 тестов разбиты по модулям

```
tests/
├── analysis/     # sentiment, stats, network
├── api/          # FastAPI endpoints
├── core/         # loader, storage
└── web/          # если есть frontend тесты
```

Запускай только тесты релевантного модуля после исправления — быстрее.  
Полный запуск — только перед итоговым status.json.

### Фикстуры с временными файлами

Тесты используют `tmp_path` из pytest. Не должны обращаться к реальным данным в `data/`.

Если тест падает с `FileNotFoundError: data/result.json` — это проблема теста, не твоего исправления. Зафиксировать в issues.

### Async тесты

```python
# Тесты с async используют pytest-asyncio
@pytest.mark.asyncio
async def test_something():
    result = await some_async_function()
```

Если `pytest.mark.asyncio` не работает — проверить что `pytest-asyncio` установлен и настроен в `pytest.ini`.

---

## Формат отчёта о тестах в report.md

```markdown
## Test Results

**Run:** python -m pytest tests/ -v --tb=short
**Timestamp:** YYYY-MM-DD HH:MM

### Summary
- Total: 146
- Passed: 144
- Failed: 2
- Errors: 0

### Failed Tests
1. `tests/analysis/test_sentiment.py::test_negative_overlap`
   ```
   AssertionError: Overlap found: {'золот'}
   ```
   **Cause:** Expected — testing the fix I applied

2. `tests/core/test_loader.py::test_large_file`
   ```
   FileNotFoundError: data/result.json
   ```
   **Cause:** Pre-existing issue, not related to this fix
```

---

## Что НЕ входит в этот скилл

- Как писать новые тесты (это TEST-PATTERNS.md для TestWriterAgent)
- Как исправлять падающие тесты (только если тест сам неверен и указано в session.md)
