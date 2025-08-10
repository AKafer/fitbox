from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import asyncio
from typing import Optional, Literal


IpMismatchPolicy = Literal['quarantine', 'update', 'drop']


@dataclass
class DeviceInfo:
    ip: str
    last_seen: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    active: bool = True
    ip_mismatch: bool = False
    mismatch_ip: Optional[str] = None


class SensorsState:
    def __init__(
        self, ip_mismatch_policy: IpMismatchPolicy = 'quarantine'
    ) -> None:
        self._devices: dict[str, DeviceInfo] = {}
        self.training_active: bool = False
        self._lock = asyncio.Lock()
        self._ip_mismatch_policy = ip_mismatch_policy

    async def upsert(self, device_id: str, ip: str) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            self._devices[device_id] = DeviceInfo(
                ip=ip,
                last_seen=now,
                active=True,
                ip_mismatch=False,
                mismatch_ip=None,
            )

    async def touch(self, device_id: str, ip: Optional[str] = None) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            info = self._devices.get(device_id)
            if info is None:
                self._devices[device_id] = DeviceInfo(
                    ip=ip or 'unknown', last_seen=now, active=True
                )
                return

            if ip and ip != info.ip:
                if self._ip_mismatch_policy == 'quarantine':
                    info.ip_mismatch = True
                    info.mismatch_ip = ip
                    info.active = False
                    info.last_seen = now
                elif self._ip_mismatch_policy == 'update':
                    info.ip = ip
                    info.ip_mismatch = False
                    info.mismatch_ip = None
                    info.active = True
                    info.last_seen = now
                elif self._ip_mismatch_policy == 'drop':
                    self._devices.pop(device_id, None)
                return
            info.last_seen = now
            if not info.ip_mismatch:
                info.active = True

    async def update_on_hit(self, device_id: str) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            info = self._devices.get(device_id)
            if info is None:
                self._devices[device_id] = DeviceInfo(
                    ip='unknown', last_seen=now, active=True
                )
            else:
                info.last_seen = now
                if not info.ip_mismatch:
                    info.active = True

    async def snapshot(self) -> dict[str, DeviceInfo]:
        async with self._lock:
            return dict(self._devices)

    async def maintain(
        self, inactive_after: timedelta, delete_after: timedelta
    ) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            to_delete = []
            for did, info in self._devices.items():
                age = now - info.last_seen
                if age >= delete_after:
                    to_delete.append(did)
                elif age >= inactive_after:
                    info.active = False
            for did in to_delete:
                self._devices.pop(did, None)
