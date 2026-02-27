"""Broadcast service for WebSocket updates."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

from fastapi import WebSocket


@dataclass
class ProgressUpdate:
    """Progress update data."""

    percent: float
    current_task: str | None = None
    message: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class BroadcastService:
    """Service for broadcasting updates to WebSocket clients."""

    _instance: Optional['BroadcastService'] = None

    def __init__(self):
        """Initialize broadcast service."""
        self.clients: list[WebSocket] = []
        self.current_update: ProgressUpdate | None = None

    @classmethod
    def get_instance(cls) -> 'BroadcastService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self, websocket: WebSocket) -> None:
        """Add client to broadcast list."""
        self.clients.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove client from broadcast list."""
        if websocket in self.clients:
            self.clients.remove(websocket)

    async def broadcast(self, update: ProgressUpdate) -> None:
        """Broadcast update to all connected clients."""
        self.current_update = update

        disconnected = []
        for client in self.clients:
            try:
                await client.send_json(update.to_dict())
            except Exception:
                disconnected.append(client)

        # Clean up disconnected clients
        for client in disconnected:
            self.disconnect(client)

    async def send_progress(self, percent: float, task: str | None = None) -> None:
        """Send progress update."""
        update = {
            "type": "progress",
            "percent": percent,
            "task": task
        }
        self.current_update = update  # Store for status endpoint

        disconnected = []
        for client in self.clients:
            try:
                await client.send_json(update)
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            self.disconnect(client)

    async def send_log(self, message: str, level: str = "info") -> None:
        """Send log entry."""
        update = {
            "type": "log",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "level": level
        }

        disconnected = []
        for client in self.clients:
            try:
                await client.send_json(update)
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            self.disconnect(client)
