# Outgoing Calls System

Система автоматизированного обзвона для СГУГиТ (Сибирский государственный университет геосистем и технологий). Позволяет управлять массовыми телефонными рассылками с поддержкой синтеза речи, контрольных звонков и email-отчетности.

## 📋 Содержание

- [Описание проекта](#-описание-проекта)
- [Архитектура](#-архитектура)
- [Требования](#-требования)
- [Установка и запуск](#-установка-и-запуск)
- [Backend](#-backend)
  - [ssugt-outgoing-calls](#-ssugt-outgoing-calls)
  - [ssugt-edge-tts](#-ssugt-edge-tts)
  - [ssugt-synthesizer](#-ssugt-synthesizer)
- [Frontend](#-frontend)
  - [ssugt-outgoing-calls-ui](#-ssugt-outgoing-calls-ui)
- [API](#-api)
- [Конфигурация](#-конфигурация)
- [Разработка](#-разработка)

## 📖 Описание проекта

Система предназначена для автоматизации исходящих телефонных звонков с возможностью:
- Массовой рассылки голосовых сообщений по списку номеров
- Синтеза речи (TTS) с использованием различных провайдеров (Yandex, Edge TTS, Silero)
- Контрольных звонков для проверки каналов связи
- Автоматической генерации отчетов по email
- Управления звонками через веб-интерфейс
- Интеграции с Asterisk ARI для управления звонками

## 🏗 Архитектура

```
outgoing-calls/
├── backend/
│   ├── ssugt-edge-tts/       # Сервис TTS на базе Microsoft Edge
│   ├── ssugt-outgoing-calls/ # Основной API сервис
│   └── ssugt-synthesizer/    # Сервис TTS на базе Silero
└── frontend/
    └── ssugt-outgoing-calls-ui/ # Веб-интерфейс
```

### Компоненты системы

| Компонент | Описание | Порт |
|-----------|----------|------|
| **outgoing_calls** | Основной API сервис | 8191 |
| **storage** | Сервис для хранения аудио | 8190 |
| **synthesizer** | TTS (Silero) | 8194 |
| **edge_tts** | TTS (Microsoft Edge) | 8195 |
| **PostgreSQL** | База данных | 5432 |
| **RabbitMQ** | Очередь сообщений | 5672 |
| **Mailpit** | SMTP сервер для тестов | 1025 |

## 🛠 Требования

- Docker и Docker Compose
- Python 3.10+ (для backend)
- Node.js 18+ (для frontend)
- NVIDIA GPU (опционально, для ускорения синтеза речи)

## 🚀 Установка и запуск

### Полный запуск (рекомендуется)

```bash
# Запуск всех сервисов
cd outgoing-calls/backend/ssugt-outgoing-calls
docker-compose up -d
```

### Запуск отдельных компонентов

#### Backend - ssugt-outgoing-calls

```bash
cd outgoing-calls/backend/ssugt-outgoing-calls
docker-compose up -d
# Или локально:
pip install -r requirements.txt
python -m api.outgoing_calls.main
```

#### Backend - ssugt-synthesizer

```bash
cd outgoing-calls/backend/ssugt-synthesizer
docker-compose up -d
# Требуется GPU для ускоренной работы
```

#### Backend - ssugt-edge-tts

```bash
cd outgoing-calls/backend/ssugt-edge-tts
docker-compose up -d
```

#### Frontend

```bash
cd outgoing-calls/frontend/ssugt-outgoing-calls-ui
npm install
npm run dev
```

## 🔧 Backend

### ssugt-outgoing-calls

Основной сервис системы обзвона. Предоставляет REST API и AMQP для управления звонками.

**Основные функции:**
- Управление очередью звонков
- Интеграция с Asterisk ARI
- REST API для клиентского приложения
- AMQP для асинхронной обработки
- Генерация отчетов

**API эндпоинты:**
- `GET /calls/` - Список звонков
- `POST /calls/` - Создание новой рассылки
- `GET /phone_calls/{call_id}` - Список телефонных звонков
- `PATCH /calls/{call_id}` - Редактирование звонка
- `DELETE /calls/{call_id}` - Удаление звонка

### ssugt-edge-tts

Сервис синтеза речи на базе Microsoft Edge TTS.

**Эндпоинты:**
- `POST /speech/v1/tts:synthesize` - Синтез речи
- `GET /voices` - Список доступных голосов
- `GET /health` - Проверка состояния

**Поддерживаемые голоса:**
- `ru-RU-SvetlanaNeural` (Русский)
- `ru-RU-DmitryNeural` (Русский)
- `en-US-JennyNeural` (Английский)
- И другие

### ssugt-synthesizer

Сервис синтеза речи на базе Silero TTS (русский язык).

**Эндпоинты:**
- `POST /speech/v1/tts:synthesize` - Синтез речи
- `GET /health` - Проверка состояния

**Доступные голоса:**
- `aidar`, `baya`, `kseniya`, `xenia`, `eugene`

## 💻 Frontend

### ssugt-outgoing-calls-ui

Веб-интерфейс для управления системой обзвона.

**Технологии:**
- React 19
- TypeScript
- Vite
- Material UI (MUI)
- Redux Toolkit

**Основные страницы:**
- **LoginPage** - Авторизация
- **MainPage** - Управление звонками

**Скрипты:**
```bash
npm run dev      # Запуск в режиме разработки
npm run build    # Сборка
npm run preview  # Предпросмотр
npm run lint     # Проверка кода
```

## 🔌 API

### Создание рассылки

```http
POST /calls/
Content-Type: application/json

{
  "name": "Название рассылки",
  "is_paused": false,
  "retry_limit": 3,
  "schedule": [...],
  "tts_type": "yandex",
  "categories": ["ru_mobile_numbers", "ru_city_numbers"],
  "calls": [
    {
      "phone_number": "+7 (XXX) XXX-XX-XX",
      "text": "Текст сообщения"
    }
  ],
  "control_call_number": "+7 (XXX) XXX-XX-XX",
  "control_call_interval": 10,
  "control_call_enabled": true,
  "email_report_address": "admin@example.com",
  "email_report_interval": 3600,
  "email_report_enabled": true
}
```

### Получение списка звонков

```http
GET /calls/?offset=0&limit=10
Authorization: Bearer <token>
```

## ⚙️ Конфигурация

### Переменные окружения

#### ssugt-outgoing-calls (.env)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OUTGOING_CALLS_SERVER_PORT` | Порт API сервера | 8191 |
| `POSTGRES_HOST` | Хост PostgreSQL | pg |
| `POSTGRES_USER` | Пользователь БД | postgres |
| `POSTGRES_PASSWORD` | Пароль БД | - |
| `POSTGRES_DB` | Имя БД | outgoing_calls |
| `RABBITMQ_HOST` | Хост RabbitMQ | rmq |
| `RABBITMQ_USER` | Пользователь RabbitMQ | admin |
| `RABBITMQ_PASSWORD` | Пароль RabbitMQ | - |
| `ARI_URL` | URL Asterisk ARI | http://10.1.202.253:8088 |
| `ARI_USERNAME` | Пользователь ARI | ariuser |
| `ARI_PASSWORD` | Пароль ARI | - |
| `TTS_YANDEX_OAUTH_TOKEN` | OAuth токен Yandex TTS | - |
| `TTS_YANDEX_FOLDER_ID` | Folder ID Yandex | - |

#### ssugt-synthesizer (.env)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SYNTHESIZER_SERVER_PORT` | Порт сервера | 8194 |
| `SYNTHESIZER_SAMPLE_RATE` | Частота дискретизации | 48000 |
| `TORCH_HOME` | Путь к моделям | /models |

#### ssugt-edge-tts (.env)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `EDGE_TTS_SERVER_PORT` | Порт сервера | 8195 |

#### Frontend (.env)

| Переменная | Описание |
|------------|----------|
| `VITE_API_URL` | URL API сервера |
| `UI_PORT` | Порт веб-интерфейса | 8193 |

## 👨‍💻 Разработка

### Структура проекта

```
ssugt-outgoing-calls/
├── src/
│   ├── api/
│   │   ├── outgoing_calls/
│   │   │   ├── main.py              # Точка входа
│   │   │   ├── deps.py              # Зависимости
│   │   │   ├── schemas.py           # Pydantic схемы
│   │   │   ├── database/            # Модели и работа с БД
│   │   │   ├── routes/              # API роуты
│   │   │   │   ├── http/            # HTTP эндпоинты
│   │   │   │   └── amqp/            # AMQP обработчики
│   │   │   └── services/            # Бизнес-логика
│   │   └── storage/                 # Сервис хранения
│   ├── scripts/                     # Вспомогательные скрипты
│   ├── tests/                       # Тесты
│   └── docker/                      # Docker конфигурации
```

### Тесты

```bash
cd outgoing-calls/backend/ssugt-outgoing-calls
python -m pytest tests/
```

## 📄 Лицензия

Сибирский государственный университет геосистем и технологий
