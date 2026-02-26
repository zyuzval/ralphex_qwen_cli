# DOCS-PATTERNS

## Для кого
DocsAgent — стандарты документации для tg-stats и как их применять при синхронизации.

---

## Python Docstrings

Формат: Google style (используется в проекте).

✅ Правильно:
```python
def analyze_sentiment(messages: list[TelegramMessage]) -> SentimentResult:
    """Анализирует тональность списка сообщений.

    Args:
        messages: Список сообщений Telegram для анализа.

    Returns:
        SentimentResult с распределением по positive/neutral/negative
        и разбивкой по участникам.

    Raises:
        ValueError: Если messages пустой список.
    """
```

❌ Неправильно:
```python
def analyze_sentiment(messages):
    # анализируем сентимент
    pass
```

### Когда обновлять docstring

Обновлять если изменилось:
- Сигнатура функции (параметры, возвращаемое значение)
- Поведение (raises, side effects)
- Смысл параметра

НЕ обновлять если изменилась только внутренняя реализация с тем же интерфейсом.

---

## README.md структура

README проекта имеет фиксированные секции. Обновлять только релевантные.

```markdown
# tg-stats

## Установка       ← обновлять если изменились зависимости
## Запуск          ← обновлять если изменилась команда запуска
## Возможности     ← обновлять если добавлена новая функция
## API             ← обновлять если изменились endpoints
## Разработка      ← ссылка на README-DEV.md
```

Не трогать секции которые не затронуты изменениями в коммите.

---

## FastAPI Endpoints документация

FastAPI генерирует /docs автоматически из аннотаций. Помогать ему:

✅ Правильно:
```python
@app.post(
    "/api/upload",
    summary="Загрузить Telegram экспорт",
    description="Принимает result.json до 2GB. Обрабатывает асинхронно.",
    response_model=UploadResponse,
    responses={
        413: {"description": "Файл слишком большой"},
        422: {"description": "Неверный формат файла"},
    }
)
async def upload_file(file: UploadFile):
    ...
```

---

## TypeScript: JSDoc для публичных хуков и утилит

```typescript
/**
 * Хук для загрузки файла с отслеживанием прогресса через WebSocket.
 *
 * @param onProgress - Callback вызывается при каждом обновлении прогресса (0-100)
 * @returns Объект с функцией upload и текущим статусом
 *
 * @example
 * const { upload, status } = useFileUpload({ onProgress: setProgress });
 */
export function useFileUpload({ onProgress }: UseFileUploadOptions) {
```

Обновлять только если изменилась сигнатура хука.

---

## Что никогда не документировать автоматически

- Архитектурные решения — только человек
- WAL.md и BOOT.md — живые документы, только человек
- Комментарии с `# REVIEW:` — оставить как есть, это пометки для ревью

## Что НЕ входит в этот скилл

- Как писать документацию с нуля
- Контент технических решений (PROP-001.md)
- Стиль написания для пользовательской документации
