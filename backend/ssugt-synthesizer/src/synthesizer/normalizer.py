import re
from typing import List

MONTHS_GEN = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)
ORD_GEN_MASC = {
    1: "первого",
    2: "второго",
    3: "третьего",
    4: "четвёртого",
    5: "пятого",
    6: "шестого",
    7: "седьмого",
    8: "восьмого",
    9: "девятого",
    10: "десятого",
    11: "одиннадцатого",
    12: "двенадцатого",
    13: "тринадцатого",
    14: "четырнадцатого",
    15: "пятнадцатого",
    16: "шестнадцатого",
    17: "семнадцатого",
    18: "восемнадцатого",
    19: "девятнадцатого",
    20: "двадцатого",
    21: "двадцать первого",
    22: "двадцать второго",
    23: "двадцать третьего",
    24: "двадцать четвёртого",
    25: "двадцать пятого",
    26: "двадцать шестого",
    27: "двадцать седьмого",
    28: "двадцать восьмого",
    29: "двадцать девятого",
    30: "тридцатого",
    31: "тридцать первого",
}
DIGIT_WORD = {
    "0": "ноль",
    "1": "один",
    "2": "два",
    "3": "три",
    "4": "четыре",
    "5": "пять",
    "6": "шесть",
    "7": "семь",
    "8": "восемь",
    "9": "девять",
}


def split_text(text: str, max_len: int = 250) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return [text]
    parts = re.split(r"(?<=[\.\!\?\:\;])\s+", text)
    chunks: List[str] = []
    buf = ""
    for part in parts:
        if not part:
            continue
        candidate = (buf + " " + part).strip() if buf else part.strip()
        if len(candidate) <= max_len:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            if len(part) > max_len:
                sub = re.split(r"(?<=,)\s+|\s", part)
                sbuf = ""
                for token in sub:
                    cand = (sbuf + " " + token).strip() if sbuf else token
                    if len(cand) <= max_len:
                        sbuf = cand
                    else:
                        if sbuf:
                            chunks.append(sbuf)
                        sbuf = token
                if sbuf:
                    chunks.append(sbuf)
                buf = ""
            else:
                buf = part
    if buf:
        chunks.append(buf)
    return [c for c in chunks if c]


def normalize_dates_ru(text: str) -> str:
    def repl(m):
        day = int(m.group(1))
        month = m.group(2)
        if 1 <= day <= 31:
            dayw = ORD_GEN_MASC.get(day, m.group(1))
            return f"{dayw} {month}"
        return m.group(0)

    pattern = rf"\b([1-3]?\d)\s+({'|'.join(MONTHS_GEN)})\b"
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def _read_digits(s: str) -> str:
    return " ".join(DIGIT_WORD[ch] for ch in s if ch.isdigit())


def normalize_digits_ru(text: str) -> str:
    def repl_group(m):
        grp = m.group(0)
        only_digits = re.sub(r"\D+", " ", grp).strip()
        parts = [p for p in only_digits.split() if p]
        spoken = []
        for p in parts:
            spoken.append(_read_digits(p))
        return " ".join(spoken)

    text = re.sub(r"\b(?:\d{1,}(?:[ -]\d{1,}){1,})\b", repl_group, text)

    def repl_single(m):
        return _read_digits(m.group(0))

    text = re.sub(r"\b\d+\b", repl_single, text)
    return text


def replace_pauses(text: str) -> str:
    return re.sub(
        r"\[\s*пауза\s*(\d+)\s*\]",
        lambda m: f'<break time="{m.group(1)}ms"/>',
        text,
        flags=re.IGNORECASE,
    )


def preprocess_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = replace_pauses(text)
    text = normalize_dates_ru(text)
    text = normalize_digits_ru(text)
    return text
