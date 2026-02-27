# Web Dashboard

Qwenex включает web dashboard для real-time мониторинга выполнения планов.

## Быстрый старт

```bash
# Запустить dashboard сервер
qwenex-web

# На другом порту
qwenex-web --port 9000

# С авто-перезагрузкой (dev режим)
qwenex-web --reload
```

## Интеграция с qwenex

```bash
# Запустить выполнение с web dashboard
qwenex plan.md --web
```

## WebSocket API

Dashboard использует WebSocket для real-time обновлений.

**Подключение:**
```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
```

**События:**
```javascript
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case "connected":
            console.log("Connected to dashboard");
            break;
        case "progress":
            console.log(`Progress: ${data.percent}%`);
            break;
        case "task_started":
            console.log(`Task: ${data.task}`);
            break;
        case "log":
            console.log(`[${data.level}] ${data.message}`);
            break;
    }
};
```

## REST API

**GET /**
- Dashboard HTML страница

**GET /health**
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Архитектура

```
┌─────────────┐     WebSocket      ┌──────────────┐
│   Browser   │ ◄────────────────► │  Broadcast   │
│             │                    │   Service    │
└─────────────┘                    └──────┬───────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │ Orchestrator │
                                   │  Progress    │
                                   └──────────────┘
```

## Функции dashboard

- **Progress bar** — визуализация прогресса выполнения плана
- **Current Task** — отображение текущей задачи
- **Live Logs** — консоль логов в real-time
- **Status Indicator** — статус подключения к WebSocket

## Конфигурация

| Опция | По умолчанию | Описание |
|-------|--------------|----------|
| `--host` | 0.0.0.0 | Host для binding |
| `--port` | 8000 | Порт для сервера |
| `--reload` | false | Auto-reload для разработки |

## Советы

- Откройте dashboard перед запуском `qwenex --web`
- Используйте `--reload` для разработки
- Dashboard работает независимо от выполнения планов
