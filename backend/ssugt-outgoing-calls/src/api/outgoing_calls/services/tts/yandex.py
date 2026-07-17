import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import jwt
import time

import aiohttp
import asyncio
from typing import Optional, Tuple, Callable, Awaitable

from dateutil import parser

from api.outgoing_calls.logger import logger
from api.outgoing_calls.services.tts.tools import convert_to_wav

from api.outgoing_calls.services.tts.tools import is_ssml

YANDEX_IAM_URL = urljoin(os.environ.get("IAM_YANDEX_BASE_URL", ""), "/iam/v1/tokens")
YANDEX_TTS_URL = urljoin(
    os.environ.get("TTS_YANDEX_BASE_URL", ""), "/speech/v1/tts:synthesize"
)
OAUTH_TOKEN = os.environ.get("TTS_YANDEX_OAUTH_TOKEN", "")
FOLDER_ID = os.environ.get("TTS_YANDEX_FOLDER_ID", "")
IamTokenFetcher = Callable[[aiohttp.ClientSession], Awaitable[str]]


def make_iam_token_fetcher() -> IamTokenFetcher:
    token: str = ""
    expiry: datetime = datetime.min
    lock = asyncio.Lock()

    async def fetch(client: aiohttp.ClientSession) -> str:
        nonlocal token, expiry

        async with lock:
            if datetime.utcnow() < expiry:
                return token

            # 1. Читаем key.json нашего робота (положи его в корень)
            import json
            with open("key.json", "r") as f:
                key_data = json.load(f)

            # 2. Формируем JWT для Яндекса
            now = int(time.time())
            payload = {
                "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                "iss": key_data["service_account_id"],
                "iat": now,
                "exp": now + 3600
            }
            
            # Подписываем приватным ключом робота
            encoded_jwt = jwt.encode(
                payload, 
                key_data["private_key"], 
                algorithm="PS256", 
                headers={"kid": key_data["id"]}
            )

            # 3. Запрашиваем IAM-токен у Яндекса
            headers = {"Content-Type": "application/json"}
            json_data = {"jwt": encoded_jwt}

            async with client.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens", 
                headers=headers, 
                json=json_data
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Ошибка робота при получении IAM: {response.status}, {error}")

                result = await response.json()
                token = result["iamToken"]
                expires_at = parser.isoparse(result["expiresAt"]).replace(tzinfo=None)
                expiry = expires_at - timedelta(minutes=5)
                return token

    return fetch


async def get_yandex_cloud_balance(
    client: aiohttp.ClientSession, iam_token: str
) -> Optional[float]:
    url = "https://billing.api.cloud.yandex.net/billing/v1/billingAccounts"
    headers = {
        "Authorization": f"Bearer {iam_token}",
    }

    async with client.get(url, headers=headers) as response:
        if response.status != 200:
            error = await response.text()
            return None

        data = await response.json()
        
        logger.info(f"Billing response: {data}")

        accounts = data.get("billingAccounts", [])
        if not accounts:
            return None

        balance = accounts[0].get("balance")
        return float(balance) if balance is not None else 0.0


async def synthesize_speech(
    client: aiohttp.ClientSession,
    iam_token: str,
    text: str,
    lang: str = "ru-RU",
    voice: str = "alena",
    emotion: Optional[str] = "good",
) -> Tuple[bytes, float]:
    headers = {"Authorization": f"Bearer {iam_token}"}

    data = {
        "lang": lang,
        "voice": voice,
        "emotion": emotion,
        "folderId": FOLDER_ID,
        "format": "mp3",
        "sampleRateHertz": "48000",
    }

    if is_ssml(text):
        data.update(dict(ssml=text))
    else:
        data.update(dict(text=text))

    async with client.post(YANDEX_TTS_URL, headers=headers, data=data) as response:
        if response.status != 200:
            error = await response.text()

            error_str = f"Ошибка синтеза: {response.status}, {error}"

            logger.error("Synthesize speech error %s for data %s", error_str, data)

            raise RuntimeError(error_str)

        mp3_data = await response.read()
        wav_data, duration = await convert_to_wav(mp3_data)
        return wav_data, duration


# import os
# import time
# import json
# import base64
# from datetime import datetime, timedelta
# from urllib.parse import urljoin

# import aiohttp
# import asyncio
# from typing import Optional, Tuple, Callable, Awaitable

# from dateutil import parser
# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.primitives.asymmetric import padding
# from cryptography.hazmat.primitives import hashes

# from api.outgoing_calls.logger import logger
# from api.outgoing_calls.services.tts.tools import convert_to_wav
# from api.outgoing_calls.services.tts.tools import is_ssml

# YANDEX_IAM_URL = urljoin(os.environ.get("IAM_YANDEX_BASE_URL", ""), "/iam/v1/tokens")
# YANDEX_TTS_URL = urljoin(os.environ.get("TTS_YANDEX_BASE_URL", ""), "/speech/v1/tts:synthesize")
# FOLDER_ID = os.environ.get("TTS_YANDEX_FOLDER_ID", "")

# # Читаем твои переменные из .env
# SA_KEY_ID = os.environ.get("YANDEX_SA_KEY_ID", "")
# SA_ID = os.environ.get("YANDEX_SA_ID", "")
# SA_PRIVATE_KEY_RAW = os.environ.get("YANDEX_SA_PRIVATE_KEY", "")

# IamTokenFetcher = Callable[[aiohttp.ClientSession], Awaitable[str]]


# def prepare_jwt() -> str:
#     """Формирует железно валидный JWT по стандарту RFC 7519 для Yandex Cloud"""
#     # Исправляем возможные косяки с переносом строк из .env
#     pem_body = SA_PRIVATE_KEY_RAW.replace("\\n", "\n").encode("utf-8")
#     private_key = serialization.load_pem_private_key(pem_body, password=None)

#     now = int(time.time())
#     headers = {"alg": "PS256", "typ": "JWT", "kid": SA_KEY_ID}
#     payload = {
#         "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
#         "iss": SA_ID,
#         "iat": now,
#         "exp": now + 3600
#     }

#     def b64url(data: bytes) -> str:
#         return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

#     # Строго по доке Яндекса: b64(headers) + '.' + b64(payload)
#     json_headers = json.dumps(headers, separators=(",", ":")).encode("utf-8")
#     json_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    
#     signing_input = f"{b64url(json_headers)}.{b64url(json_payload)}".encode("utf-8")
    
#     # Подпись строго PS256 с SHA256
#     signature = private_key.sign(
#         signing_input,
#         padding.PSS(
#             mgf=padding.MGF1(hashes.SHA256()),
#             salt_length=padding.PSS.MAX_LENGTH
#         ),
#         hashes.SHA256()
#     )
    
#     return f"{signing_input.decode('utf-8')}.{b64url(signature)}"


# def make_iam_token_fetcher() -> IamTokenFetcher:
#     token: str = ""
#     expiry: datetime = datetime.min
#     lock = asyncio.Lock()

#     async def fetch(client: aiohttp.ClientSession) -> str:
#         nonlocal token, expiry

#         async with lock:
#             if datetime.utcnow() < expiry:
#                 return token

#             if not SA_KEY_ID or not SA_ID or not SA_PRIVATE_KEY_RAW:
#                 logger.warning("Переменные Yandex SA не заполнены в .env. Падаем в локалку.")
#                 return ""

#             try:
#                 encoded_jwt = prepare_jwt()
#             except Exception as e:
#                 logger.error(f"Ошибка генерации/подписи JWT: {e}. Переходим на локалку.")
#                 return ""

#             headers = {"Content-Type": "application/json"}
#             json_data = {"jwt": encoded_jwt}

#             try:
#                 async with client.post(
#                     YANDEX_IAM_URL, headers=headers, json=json_data
#                 ) as response:
#                     if response.status != 200:
#                         error = await response.text()
#                         logger.error(f"Яндекс вернул статус {response.status} на JWT: {error}. Сброс в локалку.")
#                         return ""

#                     result = await response.json()
#                     token = result["iamToken"]
#                     expires_at = parser.isoparse(result["expiresAt"]).replace(tzinfo=None)
#                     expiry = expires_at - timedelta(minutes=5)
#                     return token
#             except Exception as e:
#                 logger.error(f"Сеть упала при обмене JWT на IAM: {e}. Сброс в локалку.")
#                 return ""

#     return fetch


# async def get_yandex_cloud_balance(
#     client: aiohttp.ClientSession, iam_token: str
# ) -> Optional[float]:
#     # Если токена нет (ушли в локалку), не мучаем баланс
#     if not iam_token:
#         return 0.0
        
#     url = "https://billing.api.cloud.yandex.net/billing/v1/billingAccounts"
#     headers = {"Authorization": f"Bearer {iam_token}"}

#     try:
#         async with client.get(url, headers=headers) as response:
#             if response.status != 200:
#                 return 0.0
#             data = await response.json()
#             accounts = data.get("billingAccounts", [])
#             if not accounts:
#                 return 0.0
#             balance = accounts[0].get("balance")
#             return float(balance) if balance is not None else 0.0
#     except Exception:
#         return 0.0


# async def synthesize_speech(
#     client: aiohttp.ClientSession,
#     iam_token: str,
#     text: str,
#     lang: str = "ru-RU",
#     voice: str = "alena",
#     emotion: Optional[str] = "good",
# ) -> Tuple[bytes, float]:
#     # Если токен не пришел, это значит мы в локалке (менеджер сам перемаршрутизирует, но на случай прямого вызова):
#     headers = {"Authorization": f"Bearer {iam_token}"}

#     data = {
#         "lang": lang,
#         "voice": voice,
#         "emotion": emotion,
#         "folderId": FOLDER_ID,
#         "format": "mp3",
#         "sampleRateHertz": "48000",
#     }

#     if is_ssml(text):
#         data.update(dict(ssml=text))
#     else:
#         data.update(dict(text=text))

#     async with client.post(YANDEX_TTS_URL, headers=headers, data=data) as response:
#         if response.status != 200:
#             error = await response.text()
#             error_str = f"Ошибка синтеза: {response.status}, {error}"
#             logger.error("Synthesize speech error %s for data %s", error_str, data)
#             raise RuntimeError(error_str)

#         mp3_data = await response.read()
#         wav_data, duration = await convert_to_wav(mp3_data)
#         return wav_data, duration