from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import asyncio


@dataclass
class DeviceInfo:
    ip: str
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SensorsState:
    def __init__(self) -> None:
        self._devices: dict[str, DeviceInfo] = {}
        self.training_active: bool = False
        self._lock = asyncio.Lock()

    async def upsert(self, device_id: str, ip: str) -> None:
        async with self._lock:
            self._devices[device_id] = DeviceInfo(ip=ip)

    async def touch(self, device_id: str) -> None:
        async with self._lock:
            if device_id in self._devices:
                self._devices[device_id].last_seen = datetime.now(timezone.utc)

    async def snapshot(self) -> dict[str, DeviceInfo]:
        async with self._lock:
            return dict(self._devices)

    async def prune(self, ttl: timedelta) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            self._devices = {
                did: info for did, info in self._devices.items()
                if now - info.last_seen < ttl
            }
