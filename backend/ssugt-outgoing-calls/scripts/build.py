import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

CYRILLIC_MONTHS = [
    "янв",
    "фев",
    "мар",
    "апр",
    "май",
    "июн",
    "июл",
    "авг",
    "сен",
    "окт",
    "ноя",
    "дек",
]
EXECUTABLE_NAME = "СГУГиТ Обзвоны"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")
GOOGLE_FOLDER_ID = os.getenv("GOOGLE_FOLDER_ID", "")


def get_google_access_token(
    client_id: str, client_secret: str, refresh_token: str
) -> str:
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise Exception(f"Get google access token error: {response.text}")

    return response.json()["access_token"]


def upload_file_to_google_drive(file_path: str, file_name: str) -> None:
    access_token = get_google_access_token(
        GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
    )

    endpoint = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    headers = {"Authorization": f"Bearer {access_token}"}

    metadata = {"name": file_name, "parents": [GOOGLE_FOLDER_ID]}

    files = {
        "metadata": ("metadata", str(metadata).replace("'", '"'), "application/json"),
        "file": (file_name, open(file_path, "rb"), "application/zip"),
    }

    response = requests.post(endpoint, headers=headers, files=files)

    if response.status_code != 200:
        print("Upload file to google drive error:", response.status_code, response.text)
        return

    print("Upload file to google drive successfully")


def build_date_for_zip(date: datetime) -> str:
    day = date.day
    month = CYRILLIC_MONTHS[date.month - 1]
    year = date.year
    time = date.strftime("%H-%M")

    return f"{day:02d}-{month}-{year}_{time}"


def build_with_pyinstaller():
    base_dir = os.getcwd()

    cache_build = os.path.join(base_dir, "build")
    build_dir = os.path.join(base_dir, "resources", "build")
    main_script = os.path.join(base_dir, "src", "ui", "main.py")
    icon_path = os.path.join(base_dir, "resources", "logo.ico")
    arial_font = os.path.join(base_dir, "resources", "arial.ttf")
    paths = os.path.join(base_dir, "src", "ui")

    build_date_path = os.path.join(paths, "build_date.py")

    api_outgoing_calls_url_path = os.path.join(paths, "api_outgoing_calls_url.py")

    current_datetime = datetime.now()

    with open(build_date_path, "w", encoding="utf-8") as f:
        f.write(f'BUILD_DATE = "{current_datetime.strftime("%d.%m.%y %H:%M")}"\n')

    with open(api_outgoing_calls_url_path, "w", encoding="utf-8") as f:
        f.write(
            f'API_OUTGOING_CALLS_URL_DEFAULT = "{os.getenv("SSUGT_API_OUTGOING_CALLS_KEY")}"\n'  # noqa
        )

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

    os.makedirs(build_dir, exist_ok=True)

    command = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        f"--add-data={arial_font};resources/",
        f"--paths={paths}",
        f"--distpath={build_dir}",
        f"--name={EXECUTABLE_NAME}",
        main_script,
    ]

    print(" ".join(command))

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    else:
        cache_spec_file = f"{EXECUTABLE_NAME}.spec"

        if os.path.exists(cache_build):
            shutil.rmtree(cache_build)
        if os.path.isfile(cache_spec_file):
            os.remove(cache_spec_file)
        if os.path.isfile(build_date_path):
            os.remove(build_date_path)
        if os.path.isfile(api_outgoing_calls_url_path):
            os.remove(api_outgoing_calls_url_path)

        exe_name = f"{EXECUTABLE_NAME}.exe"

        exe_path = os.path.join(build_dir, exe_name)

        zip_name = f"{EXECUTABLE_NAME}_{build_date_for_zip(current_datetime)}.zip"

        zip_path = os.path.join(build_dir, zip_name)

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(exe_path, arcname=exe_name)
        except Exception:
            sys.exit(1)

        google_creds = [
            GOOGLE_CLIENT_ID,
            GOOGLE_CLIENT_SECRET,
            GOOGLE_REFRESH_TOKEN,
            GOOGLE_FOLDER_ID,
        ]

        if not all(google_creds):
            return

        upload_file_to_google_drive(file_path=zip_path, file_name=zip_name)


if __name__ == "__main__":
    build_with_pyinstaller()
