# CODE-QUALITY

## Для кого
ReviewAgent — критерии качества кода специфичные для стека tg-stats (Python + FastAPI + React + TypeScript).

## Контекст
Общие критерии качества агент знает. Этот скилл — про специфику этого проекта: что считать Critical, что Low, какие исключения допустимы.

---

## Severity шкала для этого проекта

| Severity | Критерий | Примеры |
|----------|----------|---------|
| Critical | Ломает функционал или роняет приложение на реальных данных | OOM на 1GB файле, неверная структура D3, SQL injection |
| High | Даёт неверные результаты или утечки ресурсов | Неправильный sentiment, WebSocket без cleanup |
| Medium | Снижает производительность или читаемость заметно | Отсутствие кэша лемматизатора, дублирование кода |
| Low | Стиль, конвенции, мелкие улучшения | Нейминг, лишние комментарии, неиспользуемые импорты |

---

## Python: Специфика проекта

### Типизация
В проекте используется Pydantic для валидации данных. Отсутствие типов — Medium. Неверные типы — High.

✅ Правильно:
```python
class TelegramMessage(BaseModel):
    id: int
    date: datetime
    text: Optional[str] = None
    from_id: Optional[int] = None
```

❌ Неправильно:
```python
def process_message(msg):  # нет типов
    return msg['text']     # нет проверки на None
```

### Async/sync смешение
FastAPI использует async. Синхронные тяжёлые операции в async-обработчиках блокируют event loop.

✅ Правильно:
```python
@app.post("/upload")
async def upload(file: UploadFile):
    # тяжёлую работу в executor
    result = await asyncio.get_event_loop().run_in_executor(
        None, process_file_sync, file_path
    )
```

❌ Неправильно:
```python
@app.post("/upload")
async def upload(file: UploadFile):
    result = process_large_file(file_path)  # блокирует event loop
```

**Severity:** High

### SQLite в многопоточном контексте
FastAPI с несколькими workers + SQLite = проблемы с блокировками.

Проверять: `check_same_thread=False` и `timeout` при создании connection.

✅ Правильно:
```python
engine = create_engine(
    "sqlite:///./stats.db",
    connect_args={"check_same_thread": False, "timeout": 30}
)
```

---

## TypeScript: Специфика проекта

### Строгие типы vs any
В проекте включён strict TypeScript. `any` допустим только с явным комментарием почему.

```typescript
// ❌ Неправильно
const data: any = response.data;

// ✅ Если any необходим
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const rawData: any = legacyApiResponse; // TODO: типизировать после обновления API
```

**Severity за голый any:** Medium

### i18n строки
Проект поддерживает RU/EN. Хардкоженные строки в компонентах — Medium.

```typescript
// ❌ Неправильно
<Typography>Загрузка файла</Typography>

// ✅ Правильно
<Typography>{t('upload.title')}</Typography>
```

---

## Тесты

### Что считается достаточным покрытием
В проекте: 146 тестов для ~15 модулей. Норма — минимум 5 тестов на публичный модуль.

Отсутствие тестов на критическую логику (sentiment, загрузчик) — High.  
Отсутствие тестов на утилиты — Low.

### Моки для внешних зависимостей
Тесты не должны обращаться к реальным файлам или сети.

✅ Правильно:
```python
@pytest.fixture
def sample_messages(tmp_path):
    data = {"messages": [...]}  # тестовые данные
    f = tmp_path / "result.json"
    f.write_text(json.dumps(data))
    return f
```

❌ Неправильно:
```python
def test_loader():
    loader = TelegramLoader("data/result.json")  # реальный файл
```

---

## Что НЕ входит в этот скилл

- Как исправлять найденные проблемы
- Архитектурные паттерны проекта (это ARCH-PATTERNS.md)
- Специфика D3 графа (это REVIEW-PATTERNS.md)
