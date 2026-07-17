import asyncio
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import List
import aiohttp

OUTGOING_CALLS_URL = "http://127.0.0.1:8191/"
OUTGOING_CALLS_TEXT = "Здравствуйте {name}, Вас беспокоит голосовой помощник Сибирского государственного университета геосистем и технологий, напоминаю Вам, двадцатого июня стартует приемная кампания в нашем вузе. Увидимся на открытии. До свидания."
TEST_OUTGOING_CALLS_FILE = "test_outgoing_calls.txt"


@dataclass
class OutgoingCall:
    name: str
    phone: str
    is_called: bool


def read_outgoing_calls() -> List[OutgoingCall]:
    outgoing_calls = []

    with open(TEST_OUTGOING_CALLS_FILE, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if not line:
                continue

            line = line.rstrip("\n")
            line = line.split(",")

            name, phone = line[0], line[1]

            is_called = False
            if len(line) == 3:
                is_called = bool(int(line[2]))

            outgoing_calls.append(
                OutgoingCall(
                    name=name.strip(), phone=phone.strip(), is_called=is_called
                )
            )

    return outgoing_calls


def save_outgoing_calls(outgoing_calls: List[OutgoingCall]) -> None:
    with open(TEST_OUTGOING_CALLS_FILE, "w", encoding="utf-8") as f:
        lines = [
            f"{outgoing_call.name},{outgoing_call.phone},{int(outgoing_call.is_called)}"
            for outgoing_call in outgoing_calls
        ]

        f.writelines("\n".join(lines))


async def do_call(session: aiohttp.ClientSession, outgoing_call: OutgoingCall) -> None:
    current_time = datetime.now().strftime("%H:%M")

    print(
        f"[!] Do call for {outgoing_call.name} ({outgoing_call.phone}), current time: {current_time}"
    )

    text = OUTGOING_CALLS_TEXT.format(name=outgoing_call.name)

    async with session.post(
        "/calls/", json=[{"phone_number": outgoing_call.phone, "text": text}]
    ) as response:
        response.raise_for_status()

        outgoing_call.is_called = True

        print(
            f"[!] Call for {outgoing_call.name} ({outgoing_call.phone}) was sent successfully"
        )


async def main() -> None:
    outgoing_calls = read_outgoing_calls()

    print(f"[!] Start outgoing calls with {len(outgoing_calls)} calls")

    async with aiohttp.ClientSession(base_url=OUTGOING_CALLS_URL) as session:
        try:
            for outgoing_call in outgoing_calls:
                if outgoing_call.is_called:
                    print(
                        f"[!] Skip outgoing call for {outgoing_call.name} ({outgoing_call.phone})"
                    )

                    continue

                await asyncio.sleep(60)  # 1 минута

                await do_call(session=session, outgoing_call=outgoing_call)
        except BaseException as e:
            print(f"Exception raised: {e}")
            print(traceback.format_exc())
        finally:
            print(f"[!] Save outgoing calls {len(outgoing_calls)}")
            save_outgoing_calls(outgoing_calls)


if __name__ == "__main__":
    asyncio.run(main())
