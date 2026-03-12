import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.pending_tasks: dict[str, str] = {}  

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket connected. Total connections: %d",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "WebSocket disconnected. Total connections: %d",
            len(self.active_connections),
        )

    async def broadcast(self, message: dict[str, Any]) -> None:
        message.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        payload = json.dumps(message, default=str)

        disconnected: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                logger.warning(
                    "Failed to send to a WebSocket client; marking for removal"
                )
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()
