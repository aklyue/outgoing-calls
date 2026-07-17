import os
import re
import subprocess
import sys


def time_to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def check_time_overlap(ranges):
    ranges = [
        x
        for x in ranges
        if is_valid_time(x["start_time_at"]) and is_valid_time(x["end_time_at"])
    ]

    sorted_ranges = sorted(ranges, key=lambda x: time_to_minutes(x["start_time_at"]))
    for i in range(len(sorted_ranges) - 1):
        current_end = time_to_minutes(sorted_ranges[i]["end_time_at"])
        next_start = time_to_minutes(sorted_ranges[i + 1]["start_time_at"])
        if current_end > next_start:
            return True
    return False


def is_valid_time(time_str: str) -> bool:
    try:
        if len(time_str) != 5 or time_str[2] != ":":
            return False
        hours = int(time_str[:2])
        minutes = int(time_str[3:])
        return 0 <= hours < 24 and 0 <= minutes < 60
    except ValueError:
        return False


def open_file_or_folder(directory: str) -> None:
    if not os.path.exists(directory):
        return

    if os.name == "nt":
        os.startfile(directory)
    elif os.name == "posix":
        subprocess.call(
            ("open", directory) if sys.platform == "darwin" else ("xdg-open", directory)
        )


def extract_and_normalize_first_phone(text):
    match = re.search(r"(\+?\d[\d\s\-\(\)]{6,}\d)", text)
    if not match:
        return None

    raw_phone = match.group()

    digits = re.sub(r"\D", "", raw_phone)

    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    elif digits.startswith("9") and len(digits) == 10:
        digits = "7" + digits

    if not 7 <= len(digits) <= 15:
        return None

    return digits


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("")

    return os.path.join(base_path, relative_path)
