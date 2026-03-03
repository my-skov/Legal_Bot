<p align="center">
  <img src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/DeepSeek-chat-5B21B6?style=for-the-badge" alt="DeepSeek"/>
  <img src="https://img.shields.io/badge/Google%20Sheets-34A853?style=for-the-badge&logo=googlesheets&logoColor=white" alt="Google Sheets"/>
</p>

<h1 align="center">⚖️ Legal Telegram Bot</h1>

<p align="center">
  <b>Юридический Telegram-бот с RAG по локальной векторной базе и логированием в Google Sheets</b>
</p>

<p align="center">
  <a href="#-возможности">Возможности</a> •
  <a href="#-быстрый-старт">Быстрый старт</a> •
  <a href="#-установка">Установка</a> •
  <a href="#-деплой-на-ubuntu-через-github">Деплой</a>
</p>

---

## 📋 Описание

Бот принимает вопросы пользователей в Telegram, подбирает релевантные фрагменты из локальной векторной БЗ `legal_DB_768`, отправляет запрос в `deepseek-chat` и возвращает структурированную консультацию.

Дополнительно бот записывает в Google таблицу:
- дату/время;
- `telegram_user_id`;
- вопрос;
- ответ ассистента.

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 🤖 DeepSeek Chat | Генерация юридических ответов в реальном времени |
| 🧠 RAG по Chroma | Поиск контекста в локальной базе `legal_DB_768` |
| 📊 Google Sheets | Логирование всех вопросов/ответов |
| 🔁 Retry + Backoff | Авто-повторы при временных сбоях DeepSeek/Sheets |
| 🛡️ Rate-limit | Защита от флуда и параллельных запросов |
| ⚙️ Systemd | Готовый unit для production-запуска |

---

## 🚀 Быстрый старт

### Windows (локально)

```powershell
cd D:\Legal_Bot
python -m venv venv
.\venv\Scripts\activate
pip install --no-cache-dir -r requirements.txt
copy env_example .env
python bot.py
```

### Linux/macOS (локально)

```bash
cd /path/to/legal-bot
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
cp env_example .env
python bot.py
```

---

## 📦 Установка

### Требования

- **Python** 3.10+
- **Telegram Bot Token** (через BotFather)
- **DeepSeek API Key**
- **Google Service Account JSON** (для записи в Google Sheets)
- **Локальная база знаний** `legal_DB_768`

### Шаг 1: Клонирование

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
```

### Шаг 2: Установка зависимостей

```bash
pip install --no-cache-dir -r requirements.txt
```

`requirements.txt` уже фиксирует CPU-ветку `torch` для Linux, чтобы на VPS не подтягивались тяжелые `nvidia/*` и `triton`.

### Шаг 3: Настройка `.env`

```bash
cp env_example .env
```

Заполни `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

LEGAL_DB_PATH=./legal_DB_768
LEGAL_DB_CONFIG_PATH=./legal_DB_768/config.json
RETRIEVAL_TOP_K=5

GOOGLE_SHEET_ENABLED=true
GOOGLE_SPREADSHEET_ID=your_google_sheet_id
GOOGLE_WORKSHEET_NAME=Sheet1
GOOGLE_SERVICE_ACCOUNT_FILE=./google-service-account.json
```

---

## 💬 Использование

### Команды бота

- `/start` — запуск и краткая информация
- `/help` — справка
- `/ask` — режим явного ввода вопроса

Обычный текст без команды тоже обрабатывается как вопрос.

### Формат ответа

Бот возвращает:
- краткий вывод;
- пошаговые рекомендации;
- ссылки на нормы права (если доступны);
- альтернативные пути решения.

---

## 🛡️ Production-ready функции

### Retry/Backoff

- DeepSeek: retries + timeout через `app/retry.py`
- Google Sheets: retries на open/update/append

### Anti-flood / Rate-limit

- лимит запросов на пользователя в временном окне;
- минимальный интервал между вопросами;
- запрет параллельной обработки двух вопросов от одного пользователя;
- ограничение длины вопроса.

### Systemd

Готовый unit в `deploy/systemd/legal-telegram-bot.service`.

---

## ⚙️ Настройки

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | — |
| `DEEPSEEK_API_KEY` | Ключ DeepSeek API | — |
| `DEEPSEEK_MODEL` | Модель DeepSeek | `deepseek-chat` |
| `DEEPSEEK_BASE_URL` | Базовый URL API | `https://api.deepseek.com` |
| `DEEPSEEK_TIMEOUT_SECONDS` | Таймаут запроса в DeepSeek | `45` |
| `DEEPSEEK_MAX_RETRIES` | Кол-во retry для DeepSeek | `4` |
| `DEEPSEEK_RETRY_BASE_DELAY_SECONDS` | Базовая задержка retry | `1.0` |
| `LEGAL_DB_PATH` | Путь к папке Chroma БЗ | `./legal_DB_768` |
| `LEGAL_DB_CONFIG_PATH` | Путь к конфигу БЗ | `./legal_DB_768/config.json` |
| `RETRIEVAL_TOP_K` | Кол-во фрагментов контекста | `5` |
| `GOOGLE_SHEET_ENABLED` | Включить логирование в Sheets | `true` |
| `GOOGLE_SPREADSHEET_ID` | ID Google таблицы | — |
| `GOOGLE_WORKSHEET_NAME` | Лист внутри таблицы | `Sheet1` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | JSON ключ service account | `./google-service-account.json` |
| `SHEETS_MAX_RETRIES` | Кол-во retry для Sheets | `4` |
| `SHEETS_RETRY_BASE_DELAY_SECONDS` | Задержка retry для Sheets | `1.0` |
| `USER_RATE_LIMIT_WINDOW_SECONDS` | Окно rate-limit | `60` |
| `USER_RATE_LIMIT_MAX_REQUESTS` | Лимит запросов в окне | `6` |
| `USER_MIN_INTERVAL_SECONDS` | Мин. пауза между запросами | `2.0` |
| `MAX_QUESTION_LENGTH` | Макс. длина вопроса | `4000` |

---

## 🚢 Деплой на Ubuntu через GitHub

### 1) Подготовка репозитория (локально)

```powershell
cd D:\Legal_Bot
git init
git add .
git commit -m "Initial legal telegram bot"
git branch -M main
git remote add origin https://github.com/<your-user>/<your-repo>.git
git push -u origin main
```

### 2) Подготовка сервера

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
sudo useradd --system --create-home --home-dir /opt/legal-bot --shell /bin/bash legalbot || true
```

### 3) Клонирование и установка

```bash
cd /opt
sudo -u legalbot git clone https://github.com/<your-user>/<your-repo>.git legal-bot
cd /opt/legal-bot
sudo -u legalbot python3 -m venv venv
sudo -u legalbot /opt/legal-bot/venv/bin/pip install --no-cache-dir -r requirements.txt
```

### 4) Секреты и база знаний

1. Создай `/opt/legal-bot/.env` из `env_example`.
2. Загрузи `/opt/legal-bot/google-service-account.json`.
3. Дай service account доступ к Google таблице (Editor).
4. Убедись, что `legal_DB_768` находится в `/opt/legal-bot/legal_DB_768`.

Если БЗ не в GitHub:

```bash
# команда с локальной Windows-машины
scp -r D:\Legal_Bot\legal_DB_768 <server-user>@<server-ip>:/opt/legal-bot/
```

Фиксация прав:

```bash
sudo chown -R legalbot:legalbot /opt/legal-bot
chmod 600 /opt/legal-bot/.env /opt/legal-bot/google-service-account.json
```

### 5) Установка systemd unit

```bash
sudo cp /opt/legal-bot/deploy/systemd/legal-telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable legal-telegram-bot
sudo systemctl start legal-telegram-bot
```

Проверка:

```bash
sudo systemctl status legal-telegram-bot
journalctl -u legal-telegram-bot -f
```

### 6) Обновления

```bash
cd /opt/legal-bot
sudo -u legalbot git pull origin main
sudo -u legalbot /opt/legal-bot/venv/bin/pip install --no-cache-dir -r requirements.txt
sudo systemctl restart legal-telegram-bot
sudo systemctl status legal-telegram-bot
```

---

## 📁 Структура проекта

```text
legal-bot/
├── app/
│   ├── assistant.py
│   ├── config.py
│   ├── rate_limit.py
│   ├── retry.py
│   ├── sheets_logger.py
│   └── vector_db.py
├── deploy/systemd/legal-telegram-bot.service
├── legal_DB_768/
├── bot.py
├── env_example
├── requirements.txt
└── README.md
```

---

## ⚠️ Важно

- Не публикуй `.env` и `google-service-account.json`.
- Для стабильной работы на сервере обязательно запускай через `systemd`.
- Если включен `GOOGLE_SHEET_ENABLED=true`, но нет доступа к таблице, бот продолжит работу без логирования.
- Для VPS с маленьким диском всегда используй установку с `--no-cache-dir` (это сильно снижает пиковое потребление диска).

---

<p align="center">
  Сделано для production-запуска юридического Telegram-бота ⚖️
</p>
