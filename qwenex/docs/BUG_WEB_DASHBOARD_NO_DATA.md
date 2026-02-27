# Bug Report: Web Dashboard не отображает данные

**Дата:** 2026-02-27  
**Приоритет:** P2 (Medium)  
**Статус:** 🔴 Open

---

## Описание

Web dashboard показывает статус "Connected", но не отображает данные прогресса и логов.

---

## Воспроизведение

1. Запустить `qwenex-web --port 8000`
2. Открыть http://localhost:8000
3. Выполнить `curl http://localhost:8000/demo/start`
4. Наблюдать dashboard

**Ожидаемый результат:**
- Progress bar заполняется 0% → 100%
- Current Task обновляется
- Logs показывает 6 сообщений

**Фактический результат:**
- Status: "Connected"
- Progress: 0%
- Current Task: "No active task"
- Logs: пусто

---

## Диагностика

### ✅ Что работает:

1. **Сервер запущен:**
   ```bash
   curl http://localhost:8000/health
   # {"status":"ok"}
   ```

2. **WebSocket подключается:**
   ```javascript
   const ws = new WebSocket("ws://localhost:8000/ws");
   ws.onopen = () => console.log("✅ Connected!");
   // Вывод: ✅ Connected!
   ```

3. **Демо запускается:**
   ```bash
   curl http://localhost:8000/demo/start
   # {"status":"started","message":"Demo progress started"}
   ```

4. **Данные генерируются (проверено через Python):**
   ```python
   from qwenex.web.server import send_demo_progress
   from qwenex.web.broadcast import BroadcastService
   
   async def test():
       b = BroadcastService.get_instance()
       await send_demo_progress()
       print(b.current_update)
   
   asyncio.run(test())
   # Вывод: {'type': 'progress', 'percent': 100, 'task': 'Генерация отчёта...'}
   ```

### ❌ Что не работает:

1. **`/demo/status` возвращает 500:**
   ```bash
   curl http://localhost:8000/demo/status
   # Internal Server Error
   ```

2. **Данные не отправляются в WebSocket:**
   - BroadcastService.clients = 0 (нет подключений)
   - Данные генерируются но не отправляются

---

## Гипотезы

### Гипотеза 1: Race condition

Демо запускается и завершается ДО того как браузер подключается к WebSocket.

**Проверка:**
```python
# Запустить демо
curl http://localhost:8000/demo/start
# Подождать 10 секунд
# Подключиться через браузер
# Данные уже не актуальны
```

**Решение:** Сохранять историю прогресса, а не только текущее состояние.

---

### Гипотеза 2: BroadcastService не видит WebSocket подключения

WebSocket подключается к одному экземпляру BroadcastService, демо запускается в другом.

**Проверка:**
```python
from qwenex.web.broadcast import BroadcastService
b1 = BroadcastService.get_instance()  # В демо
b2 = BroadcastService.get_instance()  # В WebSocket
print(b1 is b2)  # Должно быть True
```

**Решение:** Убедиться что singleton работает корректно.

---

### Гипотеза 3: Данные отправляются ДО подключения клиента

Демо запускается сразу при `/demo/start`, но браузер ещё не подключился к WebSocket.

**Проверка:**
```
T0: curl /demo/start (демо запущено)
T1: Браузер открыт, WebSocket подключается
T2: Демо завершилось (через 10 сек)
T3: Данные потеряны
```

**Решение:** Задерживать старт демо до первого подключения или сохранять историю.

---

## План исправления

### P0: Добавить логирование

```python
# broadcast.py
async def send_progress(self, percent: float, task: Optional[str] = None) -> None:
    print(f"[DEBUG] Sending progress: {percent}% - {task}")
    print(f"[DEBUG] Connected clients: {len(self.clients)}")
    ...
```

### P1: Сохранять историю прогресса

```python
# broadcast.py
class BroadcastService:
    def __init__(self):
        self.history: List[dict] = []  # История всех событий
    
    async def send_progress(self, percent: float, task: str) -> None:
        event = {"type": "progress", "percent": percent, "task": task}
        self.history.append(event)
        ...
    
    def get_history(self) -> List[dict]:
        return self.history
```

### P2: Исправить /demo/status

```python
# server.py
@app.get("/demo/status")
async def demo_status():
    broadcast = BroadcastService.get_instance()
    return {
        "status": "running" if broadcast.current_update else "idle",
        "update": broadcast.current_update,
        "clients": len(broadcast.clients),
        "history": broadcast.history[-5:]  # Последние 5 событий
    }
```

### P3: Запуск демо после подключения

```javascript
// dashboard.html
ws.onopen = () => {
    console.log("Connected!");
    // Запуск демо после подключения
    fetch("/demo/start");
};
```

---

## Workaround (текущий)

Для тестирования используйте прямой вызов через Python:

```bash
cd qwenex
python test_demo.py
```

Данные генерируются но не отображаются в UI.

---

## Ссылки

- Файл: `src/qwenex/web/broadcast.py`
- Файл: `src/qwenex/web/server.py`
- Файл: `src/qwenex/web/templates/dashboard.html`
- Тест: `test_demo.py`
