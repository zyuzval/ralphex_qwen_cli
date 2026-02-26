# REVIEW-PATTERNS

## Для кого
ReviewAgent — знание о типичных проблемах в этом проекте и как их распознавать.

## Контекст
Без этого скилла агент делает общее ревью по принципам программирования вообще. С этим скиллом — находит проблемы специфичные для tg-stats: неправильный sentiment, проблемы D3-графа, утечки памяти при обработке 1М сообщений.

---

## Python: Анализ и обработка данных

### Правило 1: Словарный sentiment не должен пересекаться с нейтральным

Проект использует dictionary-based sentiment (не ML). Слова в POSITIVE_WORDS и NEGATIVE_WORDS не должны быть в нейтральных стоп-словах.

✅ Правильно:
```python
POSITIVE_WORDS = {"хорошо", "отлично", "супер"}
NEGATIVE_WORDS = {"плохо", "ужасно", "отстой"}
# Множества не пересекаются
assert not POSITIVE_WORDS & NEGATIVE_WORDS
```

❌ Неправильно (реальный баг в проекте):
```python
NEGATIVE_WORDS = {"золот", "плохо"}  # "золот" — часть "золото", это позитив
# Лемматизация даст ложные срабатывания
```

**Severity если нарушено:** High

### Правило 2: Обработка 1М сообщений — только стриминг и батчи

Любой код который читает весь result.json в память — Critical проблема.

✅ Правильно:
```python
def process_messages(file_path, batch_size=1000):
    with open(file_path) as f:
        batch = []
        for line in ijson.items(f, 'messages.item'):
            batch.append(line)
            if len(batch) >= batch_size:
                yield process_batch(batch)
                batch = []
```

❌ Неправильно:
```python
data = json.load(open('result.json'))  # 1GB в память
messages = data['messages']            # OOM на большом файле
```

**Severity если нарушено:** Critical

### Правило 3: lru_cache на лемматизации обязателен

Лемматизатор вызывается на каждое слово. Без кэша — N вызовов для N уникальных слов × M сообщений.

✅ Правильно:
```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_lemma(word: str) -> str:
    return morph.parse(word)[0].normal_form
```

❌ Неправильно:
```python
def get_lemma(word: str) -> str:
    return morph.parse(word)[0].normal_form  # без кэша
```

**Severity если нарушено:** High

---

## React / TypeScript: Компоненты

### Правило 4: useEffect зависимости должны быть полными

Пустой массив зависимостей с использованием внешних переменных внутри — баг.

✅ Правильно:
```typescript
useEffect(() => {
  fetchData(userId);
}, [userId]);  // userId в зависимостях
```

❌ Неправильно:
```typescript
useEffect(() => {
  fetchData(userId);  // userId используется
}, []);              // но не в зависимостях — баг
```

**Severity если нарушено:** High

### Правило 5: WebSocket cleanup обязателен

Каждый компонент который открывает WebSocket должен его закрывать в cleanup.

✅ Правильно:
```typescript
useEffect(() => {
  const ws = new WebSocket(url);
  return () => ws.close();  // cleanup
}, [url]);
```

❌ Неправильно:
```typescript
useEffect(() => {
  const ws = new WebSocket(url);
  // нет return с cleanup → утечка соединения
}, []);
```

**Severity если нарушено:** High

---

## D3: Граф взаимодействий

### Правило 6: D3 симуляция должна останавливаться при unmount

✅ Правильно:
```javascript
useEffect(() => {
  const simulation = d3.forceSimulation(nodes);
  return () => simulation.stop();
}, []);
```

❌ Неправильно:
```javascript
useEffect(() => {
  const simulation = d3.forceSimulation(nodes);
  // нет остановки → утечка CPU после unmount
}, []);
```

**Severity если нарушено:** High

### Правило 7: Данные графа должны иметь точную структуру

D3 NetworkGraph ожидает:
```javascript
nodes: [{id: string, label: string, weight: number}]
links: [{source: string, target: string, value: number}]
```

Любое отклонение (например `name` вместо `label`) — граф не рендерится без ошибки.

**Severity если нарушено:** Critical

---

## Решения по неоднозначным случаям

| Ситуация | Действие |
|----------|----------|
| Код работает но нарушает паттерн | Документировать как Medium с пометкой REVIEW |
| Проблема только в тестах, не в продакшне | Документировать как Low |
| Паттерн из скилла неприменим к этому коду | Пропустить, не натягивать |
| Нашёл проблему не из этого скилла | Документировать как обычно |

## Что НЕ входит в этот скилл

- Общие принципы clean code (агент знает их из обучения)
- Как исправлять найденные проблемы (это для FixAgent)
- Архитектурные решения (это для ArchReviewAgent)
