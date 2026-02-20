from typing import List
from fastapi import WebSocket

class LogManager:
    def __init__(self):
        self.logs: List[str] = []
        self.clients: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.clients:
            self.clients.remove(ws)

    async def push(self, msg: str):
        self.logs.append(msg)
        for c in self.clients:
            await c.send_text(msg)

log_manager = LogManager()