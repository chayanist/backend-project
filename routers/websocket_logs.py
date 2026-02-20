from fastapi import WebSocket
from core.log_stream import log_manager

@router.websocket("/logs")
async def websocket_logs(ws: WebSocket):
    await log_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        log_manager.disconnect(ws)