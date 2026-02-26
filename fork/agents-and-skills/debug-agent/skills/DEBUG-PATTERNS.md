# DEBUG-PATTERNS

## Для кого
DebugAgent — типичные ошибки в tg-stats и как их быстро диагностировать.

---

## Категории ошибок и гипотезы

### 1. MemoryError / Killed при загрузке файла

**Типичный стектрейс:**
```
MemoryError
  File "src/core/loader.py", line 45, in load
    data = json.load(f)
```

**Гипотеза H1 (High):** Файл читается целиком в память вместо стриминга
```bash
# Проверить
grep -n "json.load" src/core/loader.py
grep -n "json.loads" src/core/loader.py
# Ожидаем: найти строку с прямым json.load(file)
```

**Гипотеза H2 (Medium):** batch_size слишком большой
```bash
grep -n "batch_size" src/core/loader.py
# Ожидаем: значение > 10000
```

---

### 2. AssertionError в sentiment тестах

**Типичный стектрейс:**
```
AssertionError: assert result.negative > 0
  где result — анализ очевидно позитивного текста
```

**Гипотеза H1 (High):** Пересечение словарей POSITIVE и NEGATIVE
```bash
python3 -c "
from src.analysis.sentiment import POSITIVE_WORDS, NEGATIVE_WORDS
overlap = POSITIVE_WORDS & NEGATIVE_WORDS
print(f'Overlap: {overlap}')
"
# Ожидаем: непустое множество если H1 верна
```

**Гипотеза H2 (Medium):** Лемматизатор даёт неожиданную форму
```bash
python3 -c "
import pymorphy2
morph = pymorphy2.MorphAnalyzer()
word = 'ТВОЁ_СЛОВО'
print(morph.parse(word)[0].normal_form)
"
```

---

### 3. D3 граф не рендерится (пустой экран)

**Гипотеза H1 (High):** Неверная структура данных
```javascript
// Проверить в браузерной консоли
console.log(JSON.stringify(graphData.nodes[0]))
// Ожидаем: {id, label, weight} — если нет label или weight, это причина
```

**Гипотеза H2 (Medium):** SVG container не найден в момент инициализации
```javascript
// В компоненте NetworkGraph добавить:
console.log('container:', d3.select(svgRef.current).node())
// Ожидаем: не null
```

**Гипотеза H3 (Low):** Симуляция не запускается из-за пустых данных
```javascript
console.log('nodes count:', graphData.nodes.length)
console.log('links count:', graphData.links.length)
```

---

### 4. WebSocket не получает обновления прогресса

**Гипотеза H1 (High):** URL WebSocket неверный
```javascript
// В компоненте
console.log('ws url:', wsUrl)
// Должно быть: ws://localhost:8000/ws/upload-progress
```

**Гипотеза H2 (Medium):** CORS для WebSocket не настроен в FastAPI
```python
# Проверить в main.py
grep -n "CORSMiddleware\|allow_origins" src/api/main.py
```

**Гипотеза H3 (Low):** Компонент unmount до получения всех сообщений
```javascript
// Добавить в cleanup
return () => {
  console.log('ws cleanup called, state:', ws.readyState)
  ws.close()
}
```

---

### 5. SQLite: database is locked

**Гипотеза H1 (High):** Несколько соединений без `check_same_thread=False`
```python
# Проверить
grep -n "create_engine\|connect_args" src/core/storage.py
# Должно быть: connect_args={"check_same_thread": False, "timeout": 30}
```

**Гипотеза H2 (Medium):** Незакрытая транзакция в тестах
```python
# В тестах проверить что есть teardown
@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.close()  # ← должно быть
```

---

### 6. ImportError после добавления нового модуля

**Гипотеза H1 (High):** Циклический импорт
```bash
python3 -c "import src.analysis.sentiment" 2>&1
# Если ImportError с трейсом через несколько модулей — циклический импорт
```

**Проверить граф импортов:**
```bash
pip install pydeps
pydeps src/ --max-bacon 3
```

---

## Минимальный воспроизводящий пример (шаблон)

```python
# minimal_repro.py — изолировать проблему от остального кода
import pytest

def test_minimal():
    # 1. Только нужные импорты
    from src.analysis.sentiment import analyze_text
    
    # 2. Минимальные данные
    text = "хорошо"  # не 1 миллион сообщений
    
    # 3. Прямая проверка
    result = analyze_text(text)
    assert result.sentiment == "positive"
```

Если минимальный пример не воспроизводит ошибку — проблема в данных или окружении, не в логике.

---

## Что НЕ входит в этот скилл

- Как исправлять найденные проблемы (это FIX-PATTERNS.md)
- Общие принципы отладки Python/JS
- Профилирование производительности (это отдельная тема)
