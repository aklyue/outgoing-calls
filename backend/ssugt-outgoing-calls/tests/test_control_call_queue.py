import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from api.outgoing_calls.services.control_call_queue import ControlCallQueueGate


def test_gate_blocks_regular_queue_while_control_call_pending() -> None:
    async def _run() -> None:
        gate = ControlCallQueueGate()

        assert await gate.should_block_regular_calls(is_control=False) is False

        await gate.begin_control_call(phone_call_id="control-1")
        assert await gate.should_block_regular_calls(is_control=False) is True
        assert await gate.should_block_regular_calls(is_control=True) is False

        await gate.finish_control_call(phone_call_id="control-1")
        assert await gate.should_block_regular_calls(is_control=False) is False

    asyncio.run(_run())
