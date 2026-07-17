import io
import os
import time
import wave
from copy import deepcopy
from zoneinfo import ZoneInfo

import httpx
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

import numpy as np
import simpleaudio
from dateutil import parser
from imgui_bundle import imgui as im_gui, ImVec2, ImVec4
from imgui_bundle import portable_file_dialogs as pfd
from threading import Thread

from imgui_bundle._imgui_bundle.imgui import (
    Cond_,
    WindowFlags_,
    ChildFlags_,
    TableFlags_,
    TableColumnFlags_,
    SortDirection_,
    InputTextFlags_,
    InputTextCallbackData,
    TableBgTarget_,
    SelectableFlags_,
    SliderFlags_,
    StyleVar_,
)
from imgui_bundle.immapp import static

from io import BytesIO

import openpyxl
from simpleaudio._simpleaudio import SimpleaudioError

from ui.gui.imgui.themes import set_soft_light_theme
from ui.tools import (
    extract_and_normalize_first_phone,
    open_file_or_folder,
    is_valid_time,
    time_to_minutes,
    check_time_overlap,
)

VISIBLE_PHONE_CALLS_STEP = 50
VISIBLE_PHONE_CALLS_INITIAL = 50
REFRESHER_TIME_SECONDS = 3.0
PHONE_COLUMN_NAME = "Телефон"
ON_TEXT_TEMPLATE_MAX_LINE_PX = 420
STATUS_COLORS = {
    "Завершено": (0.0, 0.8, 0.0, 1.0),  # ярко-зеленый
    "Неудачно": (0.9, 0.1, 0.1, 1.0),  # насыщенный красный
    "Идет вызов": (1.0, 0.5, 0.0, 1.0),  # глубокий оранжевый
    "В очереди": (0.4, 0.4, 0.4, 1.0),  # темный серый
    "неизвестно": (0.6, 0.6, 0.6, 1.0),  # контрастный светло-серый
}
RETRY_LIMIT_MIN_VALUE = 1
RETRY_LIMIT_MAX_VALUE = 10
NUM_CHANNELS_OCCUPIED_MIN = 1
NUM_CHANNELS_OCCUPIED_MAX = 5
WEEKDAY_NAMES = {
    "monday": "Понедельник",
    "tuesday": "Вторник",
    "wednesday": "Среда",
    "thursday": "Четверг",
    "friday": "Пятница",
    "saturday": "Суббота",
    "sunday": "Воскресенье",
}
CALL_SCHEDULE_DEFAULT = [
    {
        "weekday": "monday",
        "time_ranges": [
            {
                "start_time_at": "09:00",
                "end_time_at": "17:00",
                "max_num_channels_occupied": 2,
            },
            {
                "start_time_at": "00:00",
                "end_time_at": "09:00",
                "max_num_channels_occupied": 5,
            },
            {
                "start_time_at": "17:00",
                "end_time_at": "23:59",
                "max_num_channels_occupied": 5,
            },
        ],
    },
    {
        "weekday": "tuesday",
        "time_ranges": [
            {
                "start_time_at": "09:00",
                "end_time_at": "17:00",
                "max_num_channels_occupied": 2,
            },
            {
                "start_time_at": "00:00",
                "end_time_at": "09:00",
                "max_num_channels_occupied": 5,
            },
            {
                "start_time_at": "17:00",
                "end_time_at": "23:59",
                "max_num_channels_occupied": 5,
            },
        ],
    },
    {
        "weekday": "wednesday",
        "time_ranges": [
            {
                "start_time_at": "09:00",
                "end_time_at": "17:00",
                "max_num_channels_occupied": 2,
            },
            {
                "start_time_at": "00:00",
                "end_time_at": "09:00",
                "max_num_channels_occupied": 5,
            },
            {
                "start_time_at": "17:00",
                "end_time_at": "23:59",
                "max_num_channels_occupied": 5,
            },
        ],
    },
    {
        "weekday": "thursday",
        "time_ranges": [
            {
                "start_time_at": "09:00",
                "end_time_at": "17:00",
                "max_num_channels_occupied": 2,
            },
            {
                "start_time_at": "00:00",
                "end_time_at": "09:00",
                "max_num_channels_occupied": 5,
            },
            {
                "start_time_at": "17:00",
                "end_time_at": "23:59",
                "max_num_channels_occupied": 5,
            },
        ],
    },
    {
        "weekday": "friday",
        "time_ranges": [
            {
                "start_time_at": "09:00",
                "end_time_at": "17:00",
                "max_num_channels_occupied": 2,
            },
            {
                "start_time_at": "00:00",
                "end_time_at": "09:00",
                "max_num_channels_occupied": 5,
            },
            {
                "start_time_at": "17:00",
                "end_time_at": "23:59",
                "max_num_channels_occupied": 5,
            },
        ],
    },
    {
        "weekday": "saturday",
        "time_ranges": [
            {
                "start_time_at": "00:00",
                "end_time_at": "23:59",
                "max_num_channels_occupied": 5,
            }
        ],
    },
    {
        "weekday": "sunday",
        "time_ranges": [
            {
                "start_time_at": "00:00",
                "end_time_at": "23:59",
                "max_num_channels_occupied": 5,
            }
        ],
    },
]


def get_default_call_schedule():
    return CALL_SCHEDULE_DEFAULT


def read_excel_bytes_to_dicts(excel_bytes: bytes) -> List[Dict[str, Any]]:
    try:
        wb = openpyxl.load_workbook(BytesIO(excel_bytes), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        columns = [str(col) for col in rows[0]]
        return [{columns[i]: row[i] for i in range(len(columns))} for row in rows[1:]]
    except Exception:
        return []


@dataclass
class ThreadReturnValue:
    value: Any = None
    is_running: bool = False
    is_completed: bool = False

    def clear(self):
        self.value = None
        self.is_completed = False


@dataclass
class RenderState:
    is_first_frame: bool = False
    is_thread_error: bool = False
    is_notification: bool = False
    is_stopped: bool = False
    notification: str = ""
    open_modal: bool = False
    step: int = 0
    balance: float = 0
    call_name: str = f"Тестовый обзвон от {datetime.now().strftime('%d.%m.%y')}"
    current_call: Dict[str, Any] = field(default_factory=dict)
    calls: List[Dict[str, Any]] = field(default_factory=list)
    phone_calls: List[Dict[str, Any]] = field(default_factory=list)
    file_dialog: Any = None
    save_phone_calls_dialog: Any = None
    call_schedule: List[Dict[str, Any]] = field(
        default_factory=get_default_call_schedule
    )
    open_call_schedule: bool = False
    is_call_patched: bool = False
    excel_path: str = ""
    excel_name: str = ""
    df: List[Dict[str, Any]] = field(default_factory=list)
    final_df: List[Dict[str, Any]] = field(default_factory=list)
    phone_column: str = ""
    text_template: str = ""
    is_paused: bool = False
    retry_limit: int = 3
    phone_calls_shown: int = VISIBLE_PHONE_CALLS_INITIAL
    synthesize_play: Any = None
    refresher_thread: ThreadReturnValue = field(default_factory=ThreadReturnValue)
    get_balance_thread: ThreadReturnValue = field(default_factory=ThreadReturnValue)
    get_calls_thread: ThreadReturnValue = field(default_factory=ThreadReturnValue)
    patch_call_thread: ThreadReturnValue = field(default_factory=ThreadReturnValue)
    get_phone_calls_thread: ThreadReturnValue = field(default_factory=ThreadReturnValue)
    download_phone_calls_xlsx_thread: ThreadReturnValue = field(
        default_factory=ThreadReturnValue
    )
    normalize_call_list_thread: ThreadReturnValue = field(
        default_factory=ThreadReturnValue
    )
    play_synthesize_text_thread: ThreadReturnValue = field(
        default_factory=ThreadReturnValue
    )
    create_calls_thread: ThreadReturnValue = field(default_factory=ThreadReturnValue)


def lazy_load_simpleaudio():
    """Воспроизводим тишину, чтобы simpleaudio подгрузился ленивой загрузкой."""

    silence = (np.zeros(2205)).astype(np.int16).tobytes()

    try:
        simpleaudio.play_buffer(silence, 1, 2, 44100)
    except SimpleaudioError:
        pass


def audio_hard_stop(audio_play: Any) -> Any:
    if not audio_play:
        return

    try:
        audio_play.stop()
        simpleaudio.stop_all()
    except SimpleaudioError:
        pass


def reformat_datetime_text(value: Optional[str]) -> str:
    if value is None:
        return "неизвестно"

    try:
        dt_utc = parser.parse(value)
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
        else:
            dt_utc = dt_utc.astimezone(ZoneInfo("UTC"))

        dt_local = dt_utc.astimezone(ZoneInfo("Asia/Novosibirsk"))

        return dt_local.strftime("%d.%m.%y %H:%M")
    except Exception:
        return "неизвестно"


def reformat_status_text(value: str) -> str:
    if value == "done":
        return "Завершено"
    elif value == "ringing":
        return "Идет вызов"
    elif value == "failed":
        return "Неудачно"
    elif value == "in_queue":
        return "В очереди"

    return "неизвестно"


def reformat_column_text(value: Any) -> str:
    if value is None:
        return "неизвестно"
    return str(value)


def reformat_synthesize_text(text: str) -> str:
    text = text.replace("\n", "")

    return text.strip()


def build_calls(
    *, final_df: List[Dict[str, Any]], text_template: str, phone_column: str
) -> List[Dict[str, Any]]:
    calls = []
    for row in final_df:
        text = text_template
        for col in row.keys():
            text = text.replace(f"[{col}]", str(row[col]))

        phone_number = row.get(phone_column)

        if phone_number is None:
            continue

        phone_number = str(phone_number).strip()

        if not phone_number:
            continue

        if not text:
            continue

        calls.append({"phone_number": phone_number, "text": text})

    return calls


def thread_worker(
    func: Callable,
    container: ThreadReturnValue,
    state: RenderState,
    *args: Any,
    **kwargs: Any,
) -> None:
    container.is_running = True

    try:
        container.value = func(state, *args, **kwargs)
    except Exception as e:
        container.is_completed = False
        state.is_thread_error = True

        return
    finally:
        container.is_running = False

    container.is_completed = True


def normalize_call_list(
    state: RenderState, client: httpx.Client, excel_path: str
) -> bytes:
    with open(excel_path, "rb") as f:
        files = {"file": (os.path.basename(excel_path), f.read())}

    merge_config = [
        {
            "concated_column": "Телефон",
            "columns": ["Телефон мобильный", "Телефон", "Мобильный телефон"],
            "priority_column": "Телефон мобильный",
        }
    ]

    response = client.post("/normalize_xlsx/", files=files, json=merge_config)
    response.raise_for_status()

    return response.content


def create_calls(
    state: RenderState,
    client: httpx.Client,
    final_df: List[Dict[str, Any]],
    call_name: str,
    text_template: str,
    phone_column: str,
    is_paused: bool,
    retry_limit: int,
    call_schedule: List[Dict[str, Any]],
) -> Dict[str, Any]:
    text_template = reformat_synthesize_text(text_template)

    calls = build_calls(
        final_df=final_df, text_template=text_template, phone_column=phone_column
    )

    payload = {
        "name": call_name,
        "start_at": datetime.utcnow().isoformat() + "Z",
        "calls": calls,
        "is_paused": is_paused,
        "retry_limit": retry_limit,
        "schedule": call_schedule,
    }

    response = client.post("/calls/", json=payload)

    response.raise_for_status()

    return response.json()


def get_balance(state: RenderState, client: httpx.Client) -> float:
    response = client.get("/balance/")
    response.raise_for_status()

    return response.json()["balance"]


def get_calls(state: RenderState, client: httpx.Client) -> List[Dict[str, Any]]:
    response = client.get("/calls/")
    response.raise_for_status()

    return response.json()


def patch_call(
    state: RenderState,
    client: httpx.Client,
    call_id: str,
    is_paused: bool,
    retry_limit: int,
    schedule: List[Dict[str, Any]],
) -> Dict[str, Any]:
    response = client.patch(
        f"/calls/{call_id}",
        json={"is_paused": is_paused, "retry_limit": retry_limit, "schedule": schedule},
    )
    response.raise_for_status()

    return response.json()


def get_phone_calls(
    state: RenderState, client: httpx.Client, call_id: str
) -> List[Dict[str, Any]]:
    response = client.get(f"/phone_calls/{call_id}")
    response.raise_for_status()

    phone_calls = response.json()

    return [
        {**phone_call, "id": index + 1} for index, phone_call in enumerate(phone_calls)
    ]


def download_phone_calls_xlsx(
    state: RenderState, client: httpx.Client, call: Dict[str, Any], path: str
) -> None:
    call_id = call["id"]

    response = client.get(f"/phone_calls/{call_id}?format=xlsx")
    response.raise_for_status()

    with open(path, "wb") as f:
        f.write(response.content)


def play_synthesize_text(state: RenderState, client: httpx.Client) -> None:
    if state.synthesize_play and state.synthesize_play.is_playing():
        audio_hard_stop(state.synthesize_play)

    text = reformat_synthesize_text(state.text_template)

    if not text:
        return

    calls = build_calls(
        final_df=state.final_df, text_template=text, phone_column=state.phone_column
    )

    if not calls:
        return

    text = calls[0]["text"]

    response = client.post(f"/synthesize/", json={"text": text}, timeout=60)
    response.raise_for_status()

    byte_stream = io.BytesIO(response.content)
    with wave.open(byte_stream, "rb") as wav_file:
        audio_data = wav_file.readframes(wav_file.getnframes())

        state.synthesize_play = simpleaudio.play_buffer(
            audio_data,
            num_channels=wav_file.getnchannels(),
            bytes_per_sample=wav_file.getsampwidth(),
            sample_rate=wav_file.getframerate(),
        )


def refresh_calls_with_balance(client: httpx.Client, state: RenderState) -> None:
    Thread(
        target=lambda: thread_worker(
            get_balance, state.get_balance_thread, state, client
        )
    ).start()

    Thread(
        target=lambda: thread_worker(get_calls, state.get_calls_thread, state, client)
    ).start()


def refresh_phone_calls(client: httpx.Client, state: RenderState) -> None:
    if not state.current_call:
        return

    Thread(
        target=lambda: thread_worker(
            get_phone_calls,
            state.get_phone_calls_thread,
            state,
            client,
            state.current_call["id"],
        )
    ).start()


def refresher(state: RenderState, client: httpx.Client) -> None:
    while True:
        if state.is_stopped:
            break

        refresh_calls_with_balance(client, state)
        refresh_phone_calls(client, state)

        time.sleep(REFRESHER_TIME_SECONDS)


def on_text_template_callback(data: InputTextCallbackData) -> int:
    if not data.buf:
        return 0

    ch = chr(data.event_char)

    line_before = data.buf[: data.cursor_pos].split("\n")[-1]

    new_width = im_gui.calc_text_size(line_before + ch).x

    if new_width >= ON_TEXT_TEMPLATE_MAX_LINE_PX:
        data.insert_chars(data.cursor_pos, "\n", None)

    return 0


def im_gui_set_center_x_with_text(text: str):
    text_width = im_gui.calc_text_size(text).x
    window_width = im_gui.get_content_region_avail().x

    im_gui.set_cursor_pos_x(max((window_width - text_width) * 0.5, 0.0))


def render_schedule(schedule: List[Dict[str, Any]]):
    range_to_delete = None
    current_group_index = 0
    day_groups = [
        {"index_days": [0, 1, 2], "is_center": False},
        {"index_days": [3, 4, 5], "is_center": False},
        {"index_days": [6], "is_center": True},
    ]
    card_width = 350

    for day_idx, day_schedule in enumerate(schedule):
        weekday = day_schedule["weekday"]
        im_gui.push_id(f"day_{day_idx}")

        for group_index, day_group in enumerate(day_groups):
            if day_idx in day_group["index_days"]:
                if current_group_index != group_index:
                    im_gui.spacing()

                    if day_group["is_center"]:
                        available_width = im_gui.get_content_region_avail().x
                        offset_x = (available_width - card_width) / 2 + 10
                        if offset_x < 0:
                            offset_x = 0

                        im_gui.set_cursor_pos_x(offset_x)

                    current_group_index = group_index

                break

        im_gui.push_style_color(
            im_gui.Col_.child_bg.value, ImVec4(0.15, 0.15, 0.15, 0.1)
        )
        im_gui.begin_child(
            f"day_block_{day_idx}",
            ImVec2(card_width, 280),
            ChildFlags_.borders,
        )

        im_gui.begin_group()

        text = WEEKDAY_NAMES.get(weekday, weekday)
        im_gui_set_center_x_with_text(text=text)

        im_gui.text(text)
        im_gui.end_group()

        has_overlap = check_time_overlap(day_schedule["time_ranges"])
        if has_overlap:
            text = "Есть пересечения интервалов"

            im_gui_set_center_x_with_text(text)
            im_gui.text_colored(ImVec4(1.0, 0.4, 0.4, 1.0), text)

        for range_idx, time_range in enumerate(day_schedule["time_ranges"]):
            im_gui.push_id(f"range_{range_idx}")
            im_gui.separator_text(f"Интервал {range_idx + 1}")

            im_gui.text("Начало")

            im_gui.same_line()

            im_gui.set_next_item_width(80)
            _, time_range["start_time_at"] = im_gui.input_text(
                "##start",
                time_range["start_time_at"],
                flags=InputTextFlags_.chars_decimal,
            )

            im_gui.same_line()

            im_gui.text("Конец")

            im_gui.same_line()

            im_gui.set_next_item_width(80)
            _, time_range["end_time_at"] = im_gui.input_text(
                "##end",
                time_range["end_time_at"],
                flags=InputTextFlags_.chars_decimal,
            )

            im_gui.spacing()

            im_gui.text("Каналы")

            im_gui.same_line()

            im_gui.set_next_item_width(100)
            _, time_range["max_num_channels_occupied"] = im_gui.slider_int(
                "##channels",
                time_range["max_num_channels_occupied"],
                NUM_CHANNELS_OCCUPIED_MIN,
                NUM_CHANNELS_OCCUPIED_MAX,
                "%d",
            )

            is_valid_start_time = is_valid_time(time_range["start_time_at"])
            is_valid_end_time = is_valid_time(time_range["end_time_at"])

            if not is_valid_start_time or not is_valid_end_time:
                im_gui.text_colored(
                    ImVec4(1.0, 0.4, 0.4, 1.0),
                    "Неверный формат времени",
                )
            elif time_to_minutes(time_range["end_time_at"]) <= time_to_minutes(
                time_range["start_time_at"]
            ):
                im_gui.text_colored(
                    ImVec4(1.0, 0.4, 0.4, 1.0),
                    "Конец должен быть позже начала",
                )

            im_gui.spacing()

            text = "Удалить интервал"
            im_gui_set_center_x_with_text(text)

            if im_gui.button(text):
                range_to_delete = (day_idx, range_idx)

            im_gui.pop_id()

        im_gui.separator()

        text = "Добавить интервал"

        im_gui_set_center_x_with_text(text)

        if im_gui.button(f"{text}##{day_idx}"):
            day_schedule["time_ranges"].append(
                {
                    "start_time_at": "09:00",
                    "end_time_at": "18:00",
                    "max_num_channels_occupied": 1,
                }
            )

        im_gui.end_child()
        im_gui.pop_style_color()
        im_gui.same_line()
        im_gui.pop_id()

    if range_to_delete:
        day_idx, range_idx = range_to_delete
        if day_idx < len(schedule):
            schedule[day_idx]["time_ranges"].pop(range_idx)


def render_do_calls(client: httpx.Client, state: RenderState) -> None:
    center = im_gui.get_main_viewport().get_center()
    im_gui.set_next_window_pos(center, cond=Cond_.always, pivot=ImVec2(0.5, 0.5))

    is_open, _ = im_gui.begin_popup_modal(
        "Создание обзвона",
        True,
        WindowFlags_.always_auto_resize
        | WindowFlags_.no_resize
        | WindowFlags_.horizontal_scrollbar,
    )

    if is_open:
        if im_gui.begin_tab_bar("CreateCallTabs"):
            if im_gui.begin_tab_item("Настройки")[0]:
                im_gui.spacing()
                _, state.call_name = im_gui.input_text(
                    "Название обзвона", state.call_name
                )

                im_gui.spacing()
                if im_gui.button("Загрузить лист обзвона", ImVec2(290, 30)):
                    state.file_dialog = pfd.open_file(
                        "Выбрать файл",
                        filters=["Файлы Excel", "*.csv *.xls *.xlsx"],
                    )

                if state.excel_name:
                    im_gui.same_line()

                    built_excel_name = state.excel_name

                    excel_name_calculated = im_gui.calc_text_size(built_excel_name)

                    if im_gui.selectable(
                        state.excel_name,
                        False,
                        flags=SelectableFlags_.no_auto_close_popups,
                        size=ImVec2(excel_name_calculated.x, excel_name_calculated.y),
                    )[0]:
                        open_file_or_folder(state.excel_path)

                if state.file_dialog and state.file_dialog.ready():
                    result = state.file_dialog.result()
                    if result:
                        state.excel_path = result[0]
                        state.excel_name = os.path.basename(state.excel_path)

                        Thread(
                            target=lambda: thread_worker(
                                normalize_call_list,
                                state.normalize_call_list_thread,
                                state,
                                client,
                                state.excel_path,
                            )
                        ).start()
                    state.file_dialog = None

                im_gui.spacing()
                if state.final_df:
                    im_gui.push_id("text_template")
                    changed, state.text_template = im_gui.input_text_multiline(
                        "Текст синтеза",
                        state.text_template,
                        ImVec2(500.0, 150),
                        flags=InputTextFlags_.allow_tab_input
                        | InputTextFlags_.callback_edit
                        | InputTextFlags_.callback_char_filter,
                        callback=on_text_template_callback,
                    )

                    if changed and state.text_template.endswith("["):
                        im_gui.open_popup("AutoCompleteColumns")

                    if im_gui.begin_popup("AutoCompleteColumns"):
                        for col in state.final_df[0].keys():
                            label = f"[{col}]"
                            if im_gui.selectable(label, False)[0]:
                                state.text_template = (
                                    state.text_template[:-1] + label + " "
                                )
                                im_gui.close_current_popup()
                                im_gui.set_keyboard_focus_here()
                        im_gui.end_popup()
                    im_gui.pop_id()

                    im_gui.spacing()

                    synthesize_play = state.synthesize_play

                    if synthesize_play and synthesize_play.is_playing():
                        if im_gui.button("Остановить синтез речи", ImVec2(290, 30)):
                            audio_hard_stop(state.synthesize_play)
                    else:
                        is_synthesize_running = (
                            synthesize_play and synthesize_play.is_playing()
                        ) or state.play_synthesize_text_thread.is_running

                        im_gui.begin_disabled(is_synthesize_running)

                        if im_gui.button("Прослушать синтез речи", ImVec2(290, 30)):
                            Thread(
                                target=lambda: thread_worker(
                                    play_synthesize_text,
                                    state.play_synthesize_text_thread,
                                    state,
                                    client,
                                )
                            ).start()

                        im_gui.end_disabled()

                    im_gui.spacing()

                    cols = list(state.final_df[0].keys())
                    index = (
                        cols.index(state.phone_column)
                        if state.phone_column in cols
                        else 0
                    )
                    changed, idx = im_gui.combo("Колонка телефона", index, cols)
                    if changed:
                        state.final_df = deepcopy(state.df)

                        state.phone_column = cols[idx]
                        for row in state.final_df:
                            if state.phone_column in row:
                                row[state.phone_column] = (
                                    extract_and_normalize_first_phone(
                                        str(row[state.phone_column])
                                    )
                                )

                    im_gui.spacing()

                    _, state.is_paused = im_gui.checkbox(
                        "Приостановлен", state.is_paused
                    )

                    im_gui.spacing()

                    _, state.retry_limit = im_gui.slider_int(
                        "Кол-во попыток дозвона",
                        state.retry_limit,
                        RETRY_LIMIT_MIN_VALUE,
                        RETRY_LIMIT_MAX_VALUE,
                    )

                    im_gui.spacing()

                    if im_gui.button("Создать обзвон", ImVec2(290, 35)):
                        if not all(
                            [
                                state.call_name,
                                state.text_template,
                                state.final_df,
                                state.phone_column,
                            ]
                        ):
                            if not state.call_name:
                                state.notification = "Укажите название обзвона"
                            elif not state.text_template:
                                state.notification = "Введите текст синтеза"
                            elif not state.final_df:
                                state.notification = "Данные не загружены"
                            elif not state.phone_column:
                                state.notification = "Не выбрана колонка с телефоном"
                            state.open_modal = False
                            state.is_notification = True
                        else:
                            Thread(
                                target=lambda: thread_worker(
                                    create_calls,
                                    state.create_calls_thread,
                                    state,
                                    client,
                                    state.final_df,
                                    state.call_name,
                                    state.text_template,
                                    state.phone_column,
                                    state.is_paused,
                                    state.retry_limit,
                                    state.call_schedule,
                                )
                            ).start()

                im_gui.end_tab_item()

            if im_gui.begin_tab_item("Расписание")[0]:
                im_gui.spacing()

                render_schedule(state.call_schedule)

                im_gui.end_tab_item()

            if im_gui.begin_tab_item("Предпросмотр")[0]:
                im_gui.spacing()
                if state.final_df:
                    columns = list(state.final_df[0].keys())

                    if im_gui.begin_table(
                        "PreviewTable",
                        len(columns),
                        flags=TableFlags_.resizable | TableFlags_.sizing_stretch_prop,
                    ):
                        for col in columns:
                            im_gui.table_setup_column(col)
                        im_gui.table_headers_row()

                        for row in state.final_df:
                            im_gui.table_next_row()
                            for col in columns:
                                im_gui.table_next_column()
                                cell_text = reformat_column_text(row.get(col, ""))
                                if col == state.phone_column:
                                    im_gui.table_set_bg_color(
                                        TableBgTarget_.cell_bg,
                                        im_gui.get_color_u32(
                                            ImVec4(0.8, 1.0, 0.8, 1.0)
                                        ),
                                    )
                                im_gui.text(cell_text)
                        im_gui.end_table()
                else:
                    im_gui.text("Нет данных для отображения. Загрузите лист обзвона")

                im_gui.end_tab_item()

            im_gui.end_tab_bar()

        im_gui.end_popup()


@static(state=RenderState())
def render(client: httpx.Client):
    state: RenderState = render.state

    spacing = 10
    button_width = 150

    if not state.is_first_frame:
        set_soft_light_theme()

        Thread(
            target=lambda: thread_worker(
                refresher, state.refresher_thread, state, client
            )
        ).start()

        lazy_load_simpleaudio()

        state.is_first_frame = True

    if state.is_thread_error:
        state.notification = "Произошла ошибка, повторите попытку позже"
        im_gui.open_popup("##Уведомление")

        state.is_thread_error = False

    if state.is_notification:
        im_gui.open_popup("##Уведомление")

        state.is_notification = False

    if state.normalize_call_list_thread.is_completed:
        state.df = read_excel_bytes_to_dicts(state.normalize_call_list_thread.value)

        state.final_df = deepcopy(state.df)

        state.phone_column = ""

        if state.final_df:
            cols = list(state.final_df[0].keys())

            for col in cols:
                if PHONE_COLUMN_NAME.lower() in col.strip().lower():
                    state.phone_column = col
                    break

            if cols and not state.phone_column:
                state.phone_column = cols[0]

        if state.phone_column:
            for row in state.final_df:
                if state.phone_column in row:
                    row[state.phone_column] = extract_and_normalize_first_phone(
                        str(row[state.phone_column])
                    )

        state.step = 1
        state.normalize_call_list_thread.clear()

    if state.create_calls_thread.is_completed:
        state.open_modal = False
        state.notification = "Обзвон успешно создан"
        state.is_notification = True

        state.create_calls_thread.clear()

        refresh_calls_with_balance(client=client, state=state)

    if state.get_balance_thread.is_completed:
        state.balance = round(state.get_balance_thread.value, 2)
        state.get_balance_thread.clear()

    if state.get_calls_thread.is_completed:
        state.calls = state.get_calls_thread.value
        state.get_calls_thread.clear()

    if state.get_phone_calls_thread.is_completed:
        state.phone_calls = state.get_phone_calls_thread.value
        state.get_phone_calls_thread.clear()

    if state.play_synthesize_text_thread.is_completed:
        state.play_synthesize_text_thread.clear()

    if state.save_phone_calls_dialog and state.save_phone_calls_dialog.ready():
        path = state.save_phone_calls_dialog.result()

        if path:
            Thread(
                target=lambda: thread_worker(
                    download_phone_calls_xlsx,
                    state.download_phone_calls_xlsx_thread,
                    state,
                    client,
                    state.current_call,
                    path,
                )
            ).start()

        state.save_phone_calls_dialog = None

    if state.download_phone_calls_xlsx_thread.is_completed:
        state.download_phone_calls_xlsx_thread.clear()

    if state.patch_call_thread.is_completed:
        state.is_call_patched = True
        state.current_call = state.patch_call_thread.value
        state.patch_call_thread.clear()

    available_size = im_gui.get_content_region_avail()
    im_gui.set_cursor_pos_x(spacing)
    im_gui.set_cursor_pos_y(5)

    if im_gui.button("Начать обзвон", ImVec2(button_width, 30)):
        state.open_modal = True
        state.step = 0
        im_gui.open_popup("Создание обзвона")

    if state.open_call_schedule:
        im_gui.open_popup("Расписание")
        state.open_call_schedule = False

    im_gui.same_line(spacing=spacing)

    balance_text = f"Баланс: {state.balance} ₽"

    im_gui.same_line(spacing=spacing)
    im_gui.set_cursor_pos_x(
        available_size.x - im_gui.calc_text_size(balance_text).x - spacing
    )

    im_gui.text(balance_text)

    if state.open_modal:
        render_do_calls(client=client, state=state)

    im_gui.separator()

    left_panel_width = 500
    right_panel_width = available_size.x - left_panel_width - 25
    button_area_height = 60 + spacing * 2
    panel_height = available_size.y - button_area_height

    im_gui.set_cursor_pos_x(spacing)
    im_gui.begin_group()
    im_gui.text_colored((0, 0, 0, 1), "Список обзвонов")

    im_gui.begin_child(
        "Call list",
        ImVec2(left_panel_width, panel_height),
        child_flags=ChildFlags_.borders,
    )

    if not state.calls:
        im_gui.text("Нет обзвонов")
    else:
        for call in state.calls:
            im_gui.push_id(call["id"])

            if im_gui.selectable(call["name"], False):
                if im_gui.is_item_clicked():
                    state.phone_calls_shown = VISIBLE_PHONE_CALLS_INITIAL
                    state.current_call = call
                    refresh_phone_calls(client=client, state=state)

            im_gui.pop_id()

    im_gui.end_child()
    im_gui.end_group()

    im_gui.same_line(spacing=spacing)
    im_gui.begin_group()
    im_gui.text_colored((0, 0, 0, 1), "Содержимое обзвона")
    im_gui.begin_child(
        "Call information",
        ImVec2(right_panel_width, panel_height),
        child_flags=ChildFlags_.borders,
    )

    if state.phone_calls:
        im_gui.push_item_width(200)

        im_gui.begin_disabled(state.patch_call_thread.is_running)

        retry_limit_changed, state.current_call["retry_limit"] = im_gui.slider_int(
            "Кол-во попыток дозвона",
            state.current_call["retry_limit"],
            RETRY_LIMIT_MIN_VALUE,
            RETRY_LIMIT_MAX_VALUE,
        )

        im_gui.same_line(spacing=spacing)

        if im_gui.button("Расписание"):
            state.open_call_schedule = True

        im_gui.same_line(spacing=spacing)

        available_width = im_gui.get_content_region_avail().x
        im_gui.set_cursor_pos_x(available_width - button_width + 365)

        is_paused_changed, state.current_call["is_paused"] = im_gui.checkbox(
            "Приостановлен", state.current_call["is_paused"]
        )

        im_gui.end_disabled()

        if retry_limit_changed or is_paused_changed:
            Thread(
                target=lambda: thread_worker(
                    patch_call,
                    state.patch_call_thread,
                    state,
                    client,
                    state.current_call["id"],
                    state.current_call["is_paused"],
                    state.current_call["retry_limit"],
                    state.current_call["schedule"],
                )
            ).start()

        im_gui.same_line(spacing=spacing)

        if (
            im_gui.button("Выгрузить в Excel", ImVec2(button_width, 30))
            and not state.download_phone_calls_xlsx_thread.is_running
        ):
            state.save_phone_calls_dialog = pfd.save_file(
                "Сохранить обзвон",
                default_path=f"{state.current_call['name']}.xlsx",
                filters=["Файлы Excel", "*.xlsx"],
            )

        visible_rows = state.phone_calls_shown
        all_calls = state.phone_calls
        calls_to_show = all_calls[:visible_rows]

        if im_gui.begin_table(
            "PhoneCallsTable",
            10,
            TableFlags_.resizable
            | TableFlags_.sizing_stretch_prop
            | TableFlags_.sortable,
        ):
            im_gui.table_setup_column("№", TableColumnFlags_.default_sort)
            im_gui.table_setup_column("Телефон")
            im_gui.table_setup_column("Текст синтеза", TableColumnFlags_.no_sort)
            im_gui.table_setup_column("Начало звонка")
            im_gui.table_setup_column("Поднял трубку")
            im_gui.table_setup_column("Завершен")
            im_gui.table_setup_column("% прослушивания")
            im_gui.table_setup_column("Статус")
            im_gui.table_setup_column("Причина", TableColumnFlags_.no_sort)
            im_gui.table_setup_column("Кол-во попыток дозвона")
            im_gui.table_headers_row()

            sort_specs = im_gui.table_get_sort_specs()
            if sort_specs and sort_specs.specs_count > 0:
                spec = sort_specs.specs
                column_index = spec.column_index
                descending = spec.sort_direction == SortDirection_.descending

                column_sort_keys = {
                    0: lambda c: c.get("id") if c.get("id") is not None else 0,
                    1: lambda c: c.get("phone_number") or "",
                    3: lambda c: c.get("ringing_at") or "",
                    4: lambda c: c.get("picked_up_at") or "",
                    5: lambda c: c.get("completed_at") or "",
                    6: lambda c: c.get("progress") or "",
                    7: lambda c: c.get("status") or "",
                    8: lambda c: c.get("cause") or "",
                    9: lambda c: (
                        c.get("retry_count") if c.get("retry_count") is not None else 0
                    ),
                }

                if column_index in column_sort_keys:
                    all_calls.sort(
                        key=column_sort_keys[column_index], reverse=descending
                    )
                    calls_to_show = all_calls[:visible_rows]

            for call in calls_to_show:
                im_gui.table_next_row()
                im_gui.table_next_column()
                im_gui.text(reformat_column_text(call.get("id", 0)))
                im_gui.table_next_column()
                im_gui.text(reformat_column_text(call.get("phone_number", "")))
                im_gui.table_next_column()
                im_gui.text_wrapped(reformat_column_text(call.get("synthesis", "")))
                im_gui.table_next_column()
                im_gui.text(reformat_datetime_text(call.get("ringing_at", "")))
                im_gui.table_next_column()
                im_gui.text(reformat_datetime_text(call.get("picked_up_at", "")))
                im_gui.table_next_column()
                im_gui.text(reformat_datetime_text(call.get("completed_at", "")))
                im_gui.table_next_column()
                im_gui.text(reformat_column_text(call.get("progress", "")))
                im_gui.table_next_column()
                status_text = reformat_status_text(call.get("status", ""))
                im_gui.push_style_color(
                    im_gui.Col_.text.value,
                    ImVec4(*STATUS_COLORS.get(status_text, (1.0, 1.0, 1.0, 1.0))),
                )
                im_gui.text(status_text)
                im_gui.pop_style_color()
                im_gui.table_next_column()
                im_gui.text(reformat_column_text(call.get("cause", "")))
                im_gui.table_next_column()
                im_gui.text(reformat_column_text(call.get("retry_count", "")))

            im_gui.end_table()

            if im_gui.get_scroll_y() >= im_gui.get_scroll_max_y() - 10:
                if visible_rows < len(all_calls):
                    state.phone_calls_shown += VISIBLE_PHONE_CALLS_STEP
    else:
        im_gui.text("Нет данных по выбранному обзвону")

    im_gui.end_child()
    im_gui.end_group()

    center = im_gui.get_main_viewport().get_center()

    im_gui.set_next_window_pos(
        center,
        cond=Cond_.always,
        pivot=ImVec2(0.5, 0.5),
    )

    if im_gui.begin_popup_modal(
        "Расписание",
        True,
        WindowFlags_.no_resize | WindowFlags_.no_move | WindowFlags_.always_auto_resize,
    )[0]:
        if state.is_call_patched:
            im_gui.close_current_popup()
            state.is_call_patched = False

        window_width, _ = im_gui.get_window_size()

        render_schedule(state.current_call.get("schedule", []))

        im_gui.spacing()

        im_gui.set_cursor_pos_x((window_width - button_width) / 2.0)

        im_gui.begin_disabled(state.patch_call_thread.is_running)

        if im_gui.button("Сохранить", ImVec2(button_width, 30)):
            Thread(
                target=lambda: thread_worker(
                    patch_call,
                    state.patch_call_thread,
                    state,
                    client,
                    state.current_call["id"],
                    state.current_call["is_paused"],
                    state.current_call["retry_limit"],
                    state.current_call["schedule"],
                )
            ).start()

        im_gui.end_disabled()

        im_gui.end_popup()

    if im_gui.begin_popup_modal(
        "##Уведомление",
        True,
        WindowFlags_.no_title_bar
        | WindowFlags_.no_resize
        | WindowFlags_.no_move
        | WindowFlags_.always_auto_resize,
    )[0]:
        window_width, _ = im_gui.get_window_size()

        text = state.notification
        text_width = im_gui.calc_text_size(text).x

        im_gui.set_cursor_pos_x((window_width - text_width) / 2.0)
        im_gui.text(text)

        im_gui.spacing()

        im_gui.set_cursor_pos_x((window_width - button_width) / 2.0)
        if im_gui.button("Закрыть", ImVec2(button_width, 30)):
            im_gui.close_current_popup()

        im_gui.end_popup()
