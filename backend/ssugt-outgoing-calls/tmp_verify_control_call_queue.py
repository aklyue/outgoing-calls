import asyncio
from api.outgoing_calls.services.control_call_queue import ControlCallQueueGate

async def main():
    gate = ControlCallQueueGate()
    print(await gate.should_block_regular_calls(is_control=False))
    await gate.begin_control_call()
    print(await gate.should_block_regular_calls(is_control=False))
    await gate.finish_control_call()
    print(await gate.should_block_regular_calls(is_control=False))

asyncio.run(main())
