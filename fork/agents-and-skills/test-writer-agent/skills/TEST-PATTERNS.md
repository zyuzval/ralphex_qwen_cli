# TEST-PATTERNS

## Для кого
TestWriterAgent — паттерны написания тестов для tg-stats.

---

## Структура тестового файла

```python
# tests/analysis/test_sentiment.py
import pytest
import json
from pathlib import Path


# ─── Фикстуры ──────────────────────────────────────────

@pytest.fixture
def sample_messages():
    """Минимальный набор сообщений для большинства тестов."""
    return [
        {"id": 1, "from": "Alice", "text": "Отлично, всё работает!"},
        {"id": 2, "from": "Bob", "text": "Это ужасно и плохо"},
        {"id": 3, "from": "Alice", "text": "Ок"},
    ]


@pytest.fixture
def large_messages():
    """Для тестов производительности — не менее 10000 сообщений."""
    return [
        {"id": i, "from": f"User{i % 5}", "text": "тест " * 10}
        for i in range(10000)
    ]


# ─── Happy Path ────────────────────────────────────────

def test_positive_sentiment_detected(sample_messages):
    from src.analysis.sentiment import analyze_messages
    result = analyze_messages([sample_messages[0]])
    assert result.sentiment == "positive"


# ─── Error Cases ───────────────────────────────────────

def test_empty_messages_returns_neutral():
    from src.analysis.sentiment import analyze_messages
    result = analyze_messages([])
    assert result.sentiment == "neutral"
    assert result.total == 0


def test_none_text_handled_gracefully(sample_messages):
    from src.analysis.sentiment import analyze_messages
    messages = [{"id": 1, "from": "Alice", "text": None}]
    # не должен падать с AttributeError
    result = analyze_messages(messages)
    assert result is not None
```

---

## Паттерны для типов кода

### Файловые операции — всегда tmp_path

```python
def test_loader_reads_json(tmp_path):
    from src.core.loader import TelegramLoader
    
    # Создать тестовый файл
    data = {"name": "Test Chat", "messages": []}
    test_file = tmp_path / "result.json"
    test_file.write_text(json.dumps(data))
    
    loader = TelegramLoader(test_file)
    result = loader.load()
    
    assert result.name == "Test Chat"
```

### Async функции

```python
import pytest

@pytest.mark.asyncio
async def test_upload_endpoint(tmp_path):
    from httpx import AsyncClient
    from src.api.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/stats/basic")
        assert response.status_code == 200
```

### Большие данные — тест производительности

```python
import time

def test_loader_performance_1m_messages(tmp_path):
    """Загрузка 1М сообщений должна завершаться за разумное время."""
    # Генерируем тестовый файл
    messages = [{"id": i, "text": "test"} for i in range(100_000)]
    data = {"messages": messages}
    test_file = tmp_path / "large.json"
    test_file.write_text(json.dumps(data))
    
    from src.core.loader import TelegramLoader
    start = time.time()
    loader = TelegramLoader(test_file)
    loader.load()
    elapsed = time.time() - start
    
    assert elapsed < 30, f"Загрузка заняла {elapsed:.1f}s — слишком долго"
```

### Словарные множества — проверка пересечений

```python
def test_sentiment_dictionaries_no_overlap():
    """Позитивные и негативные слова не должны пересекаться."""
    from src.analysis.sentiment import POSITIVE_WORDS, NEGATIVE_WORDS
    
    overlap = POSITIVE_WORDS & NEGATIVE_WORDS
    assert len(overlap) == 0, f"Пересечение словарей: {overlap}"
```

---

## Что тестировать по coverage уровням

### basic (минимум)
- Happy path каждой публичной функции
- Один error case (пустой вход или None)

### edge-cases (добавить к basic)
- Пустые коллекции
- None значения
- Граничные числа (0, 1, очень большое)
- Строки с эмодзи и Unicode
- Файлы нулевого размера

### full (добавить к edge-cases)
- Производительность на больших данных
- Конкурентный доступ (если async)
- Все ветки if/else
- Все исключения которые функция может поднять

---

## Что НЕ тестировать

- Сторонние библиотеки (pymorphy2, D3, SQLAlchemy)
- FastAPI routing (только логику обработчиков)
- React рендеринг (если нет настроенного Jest)

## Что НЕ входит в этот скилл

- Как запускать тесты (это TESTING.md для FixAgent)
- E2E тестирование в браузере
- Нагрузочное тестирование
