# REFACTOR-PATTERNS

## Для кого
RefactorAgent — безопасные паттерны рефакторинга для Python и TypeScript в tg-stats.

## Контекст
Рефакторинг без тестов — это переписывание. Этот скилл про то как изменить структуру не сломав поведение.

---

## Золотое правило рефакторинга

```
Тесты ДО → Изменение → Тесты ПОСЛЕ → Результат тот же → Коммит
```

Если тесты не проходят до рефакторинга — остановиться. Сначала тесты, потом рефакторинг.

---

## Python: безопасные паттерны

### Извлечение функции (Extract Function)

```python
# Было: длинная функция
def analyze_messages(messages):
    # 20 строк подготовки данных
    ...
    # 30 строк анализа
    ...
    # 15 строк форматирования результата
    ...

# Стало: три маленькие функции с той же публичной сигнатурой
def analyze_messages(messages):
    prepared = _prepare_messages(messages)
    analyzed = _run_analysis(prepared)
    return _format_result(analyzed)

def _prepare_messages(messages): ...  # префикс _ = приватная
def _run_analysis(prepared): ...
def _format_result(analyzed): ...
```

**Проверка безопасности:** публичная сигнатура `analyze_messages(messages)` не изменилась.

### Устранение дублирования (DRY)

```python
# Было: одинаковая логика батчинга в трёх местах
def import_csv(file):
    batch = []
    for row in csv.reader(file):
        batch.append(row)
        if len(batch) >= 1000:
            db.insert_many(batch)
            batch = []
    if batch:
        db.insert_many(batch)

def import_json(file): 
    # точно то же самое

# Стало: общая утилита
def _process_in_batches(items, handler, batch_size=1000):
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            handler(batch)
            batch = []
    if batch:
        handler(batch)

def import_csv(file):
    _process_in_batches(csv.reader(file), db.insert_many)

def import_json(file):
    _process_in_batches(json_items(file), db.insert_many)
```

### Замена магических чисел на константы

```python
# Было
if len(text) > 280:
    truncate(text)

# Стало
MAX_TEXT_LENGTH = 280  # Twitter-style limit

if len(text) > MAX_TEXT_LENGTH:
    truncate(text)
```

---

## TypeScript: безопасные паттерны

### Извлечение хука (Extract Custom Hook)

```typescript
// Было: логика WebSocket прямо в компоненте
function UploadProgress({ uploadId }) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  
  useEffect(() => {
    const ws = new WebSocket(`/ws/${uploadId}`);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setProgress(data.progress);
      setStatus(data.status);
    };
    return () => ws.close();
  }, [uploadId]);
  
  return <div>{progress}%</div>;
}

// Стало: логика в хуке, компонент только рендерит
function useUploadProgress(uploadId: string) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  
  useEffect(() => {
    const ws = new WebSocket(`/ws/${uploadId}`);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setProgress(data.progress);
      setStatus(data.status);
    };
    return () => ws.close();
  }, [uploadId]);
  
  return { progress, status };
}

function UploadProgress({ uploadId }) {
  const { progress } = useUploadProgress(uploadId);
  return <div>{progress}%</div>;
}
```

**Проверка безопасности:** компонент рендерит то же самое, хук можно переиспользовать.

---

## Что НЕ является безопасным рефакторингом

❌ Изменение сигнатуры публичной функции:
```python
# Было
def analyze(messages: list) -> dict:

# Это НЕ рефакторинг — это изменение интерфейса
def analyze(messages: list, config: Config = None) -> SentimentResult:
```

❌ Изменение формата возвращаемых данных:
```python
# Было
return {"positive": 0.6, "negative": 0.2, "neutral": 0.2}

# Это сломает всех потребителей
return SentimentResult(positive=0.6, ...)
```

❌ Оптимизация алгоритма под видом рефакторинга:
```python
# Замена O(n²) алгоритма на O(n) может изменить порядок результатов
# Это изменение поведения, не рефакторинг
```

---

## Если тест упал после рефакторинга

1. **Не паниковать** — это нормально, тест нас защитил
2. `git diff` — посмотреть точно что изменилось
3. Откатить изменение: `git checkout -- file.py`
4. Зафиксировать в отчёте: "refactoring caused test failure, reverted"
5. Человек решает что делать дальше

---

## Что НЕ входит в этот скилл

- Оптимизация производительности (это другая задача)
- Изменение архитектуры (это ArchReviewAgent)
- Исправление багов (это FixAgent)
