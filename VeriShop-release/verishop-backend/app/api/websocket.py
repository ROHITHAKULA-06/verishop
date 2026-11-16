"""WebSocket endpoint for real-time search progress."""
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.models.schemas import SearchRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)
ws_router = APIRouter()

@ws_router.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        params = json.loads(data)
        search_request = SearchRequest(**params)

        # Send progress
        await websocket.send_json({"type": "progress", "data": {"step": "processing_input", "progress": 10}, "timestamp": datetime.utcnow().isoformat()})

        pipeline = websocket.app.state.pipeline
        if not pipeline:
            await websocket.send_json({"type": "error", "data": {"message": "Pipeline not initialized"}, "timestamp": datetime.utcnow().isoformat()})
            return

        await websocket.send_json({"type": "progress", "data": {"step": "analyzing", "progress": 40}, "timestamp": datetime.utcnow().isoformat()})

        result = await pipeline.search(search_request)

        await websocket.send_json({"type": "progress", "data": {"step": "ranking", "progress": 80}, "timestamp": datetime.utcnow().isoformat()})

        result_data = result.model_dump(mode="json")
        await websocket.send_json({"type": "result", "data": result_data, "timestamp": datetime.utcnow().isoformat()})

    except WebSocketDisconnect:
        logger.info("websocket_disconnected")
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        try:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}, "timestamp": datetime.utcnow().isoformat()})
        except Exception:
            pass
