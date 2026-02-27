# Провайдеры LLM

Qwenex поддерживает множественных LLM провайдеров через интерфейс `LLMProvider`.

## Поддерживаемые провайдеры

### Qwen Cloud (по умолчанию)

**Provider:** `qwen_cloud`

**Конфигурация:**
```bash
export QWENEX_PROVIDER=qwen_cloud
export QWENEX_MODEL=qwen-max
export QWENEX_API_KEY=your-api-key
```

**Модели:**
- `qwen-max` - максимальная производительность
- `qwen-plus` - баланс цены/качества
- `qwen-turbo` - быстрая и дешёвая

### Ollama (локальные модели)

**Provider:** `ollama`

**Конфигурация:**
```bash
export QWENEX_PROVIDER=ollama
export QWENEX_MODEL=llama3.1:8b
export QWENEX_BASE_URL=http://localhost:11434
```

**Модели:**
- `llama3.1:8b` - 8B параметров
- `llama3.1:70b` - 70B параметров
- `qwen2.5:7b` - Qwen локально

### OpenAI

**Provider:** `openai`

**Конфигурация:**
```bash
export QWENEX_PROVIDER=openai
export QWENEX_MODEL=gpt-4o
export QWENEX_API_KEY=sk-your-api-key
```

**Модели:**
- `gpt-4o` - флагманская
- `gpt-4o-mini` - бюджетная
- `o1-preview` - reasoning

## Конфигурационный файл

Создайте `~/.qwenex/config.json`:

```json
{
  "default_provider": "qwen_cloud",
  "providers": {
    "qwen_cloud": {
      "name": "qwen_cloud",
      "model": "qwen-max",
      "api_key": "your-api-key"
    },
    "ollama": {
      "name": "ollama",
      "model": "llama3.1:8b",
      "base_url": "http://localhost:11434"
    },
    "openai": {
      "name": "openai",
      "model": "gpt-4o",
      "api_key": "sk-your-api-key"
    }
  }
}
```

## CLI использование

```bash
# Использовать Qwen Cloud
qwenex specs/FEAT-001.md

# Использовать Ollama
qwenex specs/FEAT-001.md --provider ollama --model llama3.1:8b

# Использовать OpenAI с переопределением
qwenex specs/FEAT-001.md --provider openai --model gpt-4o --api-key sk-xxx

# Fallback режим (Ollama с облачным резервом)
qwenex specs/FEAT-001.md --provider ollama --fallback qwen_cloud
```

## Fallback режим

Автоматический фоллбэк при недоступности основного провайдера:

```bash
# Ollama с фоллбэком на Qwen Cloud
qwenex plan.md --provider ollama --fallback qwen_cloud

# Локальная модель с облачным фоллбэком
qwenex plan.md --provider ollama --model llama3.1:8b --fallback qwen_cloud
```

**Поведение:**
1. Проверяется доступность Ollama (GET /api/tags)
2. Если доступен — используется Ollama
3. Если недоступен — автоматический переход на Qwen Cloud
4. Все последующие запросы идут через фоллбэк

## Ollama CLI

Прямое взаимодействие с Ollama:

```bash
# Проверка доступности
qwenex-ollama --check

# Список моделей
qwenex-ollama --list

# Единичный запрос
qwenex-ollama "What is Python?"

# Интерактивный режим
qwenex-ollama
> Hello!
> quit
```

## Добавление нового провайдера

1. Создайте класс в `src/qwenex/models/<provider>.py`:

```python
from .base import LLMProvider, ProviderConfig

class MyProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config
    
    async def complete(self, prompt: str, **kwargs) -> str:
        # Реализация
        pass
    
    async def stream(self, prompt: str, **kwargs):
        # Реализация
        pass
    
    async def check_health(self) -> bool:
        # Реализация
        pass
    
    def get_config(self) -> ProviderConfig:
        return self.config
```

2. Зарегистрируйте в `src/qwenex/models/factory.py`:

```python
ProviderFactory.register(ProviderType.MY_PROVIDER, MyProvider)
```

## Сравнение провайдеров

| Провайдер | Скорость | Цена | Качество | Offline |
|-----------|----------|------|----------|---------|
| Qwen Cloud | ⚡⚡⚡ | 💰💰 | ⭐⭐⭐⭐ | ❌ |
| Ollama | ⚡⚡ | 💰 | ⭐⭐⭐ | ✅ |
| OpenAI | ⚡⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ | ❌ |
