import asyncio
from qwenex.web.server import send_demo_progress
from qwenex.web.broadcast import BroadcastService

async def test():
    b = BroadcastService.get_instance()
    print('Before:', b.current_update)
    await send_demo_progress()
    print('After:', b.current_update)

asyncio.run(test())
