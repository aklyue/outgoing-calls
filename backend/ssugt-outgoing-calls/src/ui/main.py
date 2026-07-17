import os

import httpx

from gui.imgui.setup import ImGui

try:
    from build_date import BUILD_DATE
except ImportError:
    BUILD_DATE = "неизвестно"

try:
    from api_outgoing_calls_url import API_OUTGOING_CALLS_URL_DEFAULT
except ImportError:
    API_OUTGOING_CALLS_URL_DEFAULT = "http://127.0.0.1:8191"

API_OUTGOING_CALLS_URL = os.getenv(
    "SSUGT_API_OUTGOING_CALLS_KEY", default=API_OUTGOING_CALLS_URL_DEFAULT  # noqa
)


def main() -> None:
    client = httpx.Client(base_url=API_OUTGOING_CALLS_URL)

    gui = ImGui(app_name=f"СГУГиТ Обзвоны (дата сборки: {BUILD_DATE})", client=client)

    gui.run()


if __name__ == "__main__":
    main()
