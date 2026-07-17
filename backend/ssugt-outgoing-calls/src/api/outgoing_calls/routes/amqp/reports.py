import asyncio
import json
from datetime import datetime
import os
from io import BytesIO

import pandas as pd
from faststream import Context
from faststream.rabbit import RabbitRouter, RabbitQueue, RabbitBroker, RabbitMessage
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

# Импортируем утилиты отправки почты и работы с базой
from api.outgoing_calls.database.postgres.tools import sa_inject_holder
from api.outgoing_calls.logger import logger
from api.outgoing_calls.database.postgres.models.phone_call import PhoneCall

# Импортируем утилиты работы с Excel, которые ты предоставил
from api.outgoing_calls.services.xlsx import merge_tables

# Базовая конфигурация SMTP (можно вынести в env-переменные)
SMTP_HOST = os.getenv("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() in ("true", "1", "yes")

reports_router = RabbitRouter()
report_queue = RabbitQueue("send_email", durable=True)


async def send_email_with_attachment(to_email: str, subject: str, body_text: str, filename: str, attachment_bytes: bytes):
    """Фоновая асинхронная отправка письма с XLSX-файлом во вложении."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    import aiosmtplib

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment_bytes)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{filename}"',
    )
    msg.attach(part)

    try:
        # Формируем аргументы для отправки на основе конфига .env
        send_kwargs = {
            "hostname": SMTP_HOST,
            "port": SMTP_PORT,
            "use_tls": SMTP_USE_TLS, 
        }

        # Авторизацию запрашиваем только если передан пароль
        if SMTP_PASSWORD:
            send_kwargs["username"] = SMTP_USER
            send_kwargs["password"] = SMTP_PASSWORD

        # Передаем msg ПЕРВЫМ позиционным аргументом, а остальное распаковываем через **
        await aiosmtplib.send(msg, **send_kwargs)
            
        logger.info("Отчет успешно отправлен на почту %s", to_email)
    except Exception as e:
        logger.error("Ошибка при отправке email на %s: %s", to_email, e)


@reports_router.subscriber(report_queue)
async def process_report_request(
    message: RabbitMessage,
    session_factory: async_sessionmaker[AsyncSession] = Context(),
):
    body = json.loads(message.body)
    call_id = body.get("call_id")
    email = body.get("email")
    trigger_type = body.get("trigger")  # 'interval' или 'final'

    if not call_id or not email:
        logger.warning("Запрос отчета пропущен: отсутствуют call_id или email в теле сообщения.")
        return

    injector = sa_inject_holder(session_factory)

    async with injector() as pg_holder:
        # 1. Вытаскиваем кампанию для получения имени
        call_campaign = await pg_holder.call_crud.get_by_id(call_id)
        if not call_campaign:
            logger.error("Кампания %s для генерации отчета не найдена", call_id)
            return

        # 2. Выгружаем все звонки этой кампании
        query = select(PhoneCall).where(PhoneCall.call_id == call_id)
        result = await pg_holder._session.execute(query)
        phone_calls = result.scalars().all()

    if not phone_calls:
        logger.info("Для кампании %s нет звонков. Отчет не будет сгенерирован.", call_campaign.name)
        return

    # 3. Формируем сырой плоский список словарей для pandas DataFrame
    data = []
    for pc in phone_calls:
        data.append({
            "Номер телефона": pc.phone_number,
            "Статус": pc.status,
            "Код ответа": pc.code if pc.code is not None else "-",
            "Причина завершения": pc.cause or "-",
            "Кол-во попыток": pc.retry_count,
            "Время звонка": pc.picked_up_at.strftime("%Y-%m-%d %H:%M:%S") if pc.picked_up_at else "-",
            "Завершено": pc.completed_at.strftime("%Y-%m-%d %H:%M:%S") if pc.completed_at else "-",
        })

    df = pd.DataFrame(data)

    # 4. Генерируем xlsx в память (BytesIO)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Вызовы", index=False)
    
    raw_xlsx_bytes = output.getvalue()

    # 5. Если требуется объединение/нормализация таблиц через твою утилиту merge_tables:
    # (Если структуры сложные — передаем конфиг, иначе оставляем сырой сгенерированный xlsx)
    try:
        # Для базового плоского отчета merge_tables вернет исходный байт-код, если список правил пуст
        final_xlsx_bytes = merge_tables(raw_xlsx_bytes, concat_columns=[])
    except Exception as e:
        logger.warning("Ошибка обработки структуры через merge_tables: %s. Отправляем исходный файл.", e)
        final_xlsx_bytes = raw_xlsx_bytes

    # 6. Настраиваем метаданные письма в зависимости от триггера
    trigger_rus = "Промежуточный" if trigger_type == "interval" else "Итоговый"
    subject = f"[{trigger_rus} отчет] Обзвон кампании: {call_campaign.name}"
    
    body_text = (
        f"Здравствуйте!\n\n"
        f"Направляем вам {trigger_rus.lower()} отчет по результатам автоматического обзвона.\n"
        f"Кампания: {call_campaign.name}\n"
        f"Дата генерации отчета: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"Файл со статистикой находится во вложении."
    )
    
    filename = f"report_{call_id}_{trigger_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # 7. Отправляем адресату
    await send_email_with_attachment(
        to_email=email,
        subject=subject,
        body_text=body_text,
        filename=filename,
        attachment_bytes=final_xlsx_bytes
    )