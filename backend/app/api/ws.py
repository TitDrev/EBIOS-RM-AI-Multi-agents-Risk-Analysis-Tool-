"""Route WebSocket de suivi temps réel d'une étude."""

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.deps import user_can_access
from app.core.security import decode_token
from app.database import async_session_factory
from app.live import manager
from app.models.analysis import Analysis
from app.models.user import User

router = APIRouter()


@router.websocket("/ws/analyses/{analysis_id}")
async def ws_analysis(websocket: WebSocket, analysis_id: str) -> None:
    token = websocket.query_params.get("token", "")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_token(token)
        user_id = uuid.UUID(payload.get("sub", ""))
    except (JWTError, ValueError):
        await websocket.close(code=4401)
        return

    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        analysis = await session.get(Analysis, uuid.UUID(analysis_id))
        if user is None or analysis is None or not user_can_access(user, analysis.created_by):
            await websocket.close(code=4403)
            return

    await manager.connect(analysis_id, websocket)
    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(analysis_id, websocket)
    except Exception:
        manager.disconnect(analysis_id, websocket)
