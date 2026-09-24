"""Tests du gestionnaire WebSocket (suivi temps réel)."""

from app.live import ConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.sent: list[dict] = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        self.sent.append(message)


async def test_connect_and_broadcast():
    manager = ConnectionManager()
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    await manager.connect("abc", ws1)
    await manager.connect("abc", ws2)
    await manager.broadcast("abc", {"type": "workshop_updated", "numero": 1})

    assert ws1.accepted and ws2.accepted
    assert ws1.sent == [{"type": "workshop_updated", "numero": 1}]
    assert ws2.sent == [{"type": "workshop_updated", "numero": 1}]


async def test_broadcast_scoped_per_analysis():
    manager = ConnectionManager()
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    await manager.connect("etudeA", ws1)
    await manager.connect("etudeB", ws2)
    await manager.broadcast("etudeA", {"type": "ping"})
    assert ws1.sent == [{"type": "ping"}]
    assert ws2.sent == []


async def test_disconnect_removes_socket():
    manager = ConnectionManager()
    ws1 = FakeWebSocket()
    await manager.connect("abc", ws1)
    manager.disconnect("abc", ws1)
    await manager.broadcast("abc", {"type": "ping"})
    assert ws1.sent == []
