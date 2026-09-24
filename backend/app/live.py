"""Gestionnaire de connexions WebSocket (suivi temps réel du pipeline)."""

from fastapi import WebSocket


class ConnectionManager:
    """Mainitent les connexions WebSocket par étude et diffuse les événements."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, analysis_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(analysis_id, set()).add(websocket)

    def disconnect(self, analysis_id: str, websocket: WebSocket) -> None:
        self._connections.get(analysis_id, set()).discard(websocket)

    async def broadcast(self, analysis_id: str, message: dict) -> None:
        """Diffuse `message` à tous les clients connectés à une étude."""
        sockets = self._connections.get(analysis_id, set())
        for websocket in list(sockets):
            try:
                await websocket.send_json(message)
            except Exception:
                sockets.discard(websocket)


manager = ConnectionManager()
