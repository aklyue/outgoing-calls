import asyncio
from dataclasses import dataclass
from typing import Optional


def should_trigger_control_call(*, counter: int, interval: int) -> bool:
    if interval <= 0:
        return False
    return counter >= interval


@dataclass
class ControlCallQueueGate:
    """Blocks the main queue while a control call is pending."""

    def __init__(self) -> None:
        self._control_call_pending = False
        self._active_control_phone_call_id: Optional[str] = None
        self._lock = asyncio.Lock()

    async def begin_control_call(self, *, phone_call_id: Optional[str] = None) -> None:
        async with self._lock:
            self._control_call_pending = True
            self._active_control_phone_call_id = phone_call_id

    async def finish_control_call(self, *, phone_call_id: Optional[str] = None) -> None:
        async with self._lock:
            if phone_call_id is None or self._active_control_phone_call_id == phone_call_id:
                self._control_call_pending = False
                self._active_control_phone_call_id = None

    async def should_block_regular_calls(self, *, is_control: bool) -> bool:
        if is_control:
            return False
        async with self._lock:
            return self._control_call_pending
