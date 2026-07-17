import asyncio
import os
from contextlib import suppress

import httpx
from imgui_bundle import immapp
from imgui_bundle import hello_imgui
from imgui_bundle._imgui_bundle.hello_imgui import WindowPositionMode, WindowSizeState

from ui.gui.base import BaseGui
from ui.gui.imgui import menu
from ui.tools import get_resource_path


class ImGui(BaseGui):

    def __init__(self, *, app_name: str, client: httpx.Client):
        self._client = client

        hello_imgui.set_assets_folder(get_resource_path("resources"))

        self._runner_params = hello_imgui.RunnerParams(
            ini_filename_use_app_window_title=False
        )
        self._runner_params.fps_idling.enable_idling = False
        self._runner_params.app_window_params.window_geometry.window_size_state = (
            WindowSizeState.maximized
        )
        self._runner_params.app_window_params.window_geometry.position_mode = (
            WindowPositionMode.monitor_center
        )

        self._runner_params.callbacks.load_additional_fonts = (
            self._load_additional_fonts
        )
        self._runner_params.callbacks.show_gui = self._render
        self._runner_params.app_window_params.window_title = app_name

    def run(self) -> None:
        try:
            immapp.run(self._runner_params)
        finally:
            with suppress(FileNotFoundError):
                os.remove("imgui.ini")

            menu.render.state.is_stopped = True
            self._client.close()

    def _load_additional_fonts(self) -> None:
        hello_imgui.load_font_ttf(
            "arial.ttf",
            font_size=18.0,
            use_full_glyph_range=True,
        )

    def _render(self) -> None:
        menu.render(client=self._client)
