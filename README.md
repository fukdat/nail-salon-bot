# Nail Salon Bot

Telegram-бот для автоматизации записи клиентов к мастеру маникюра. Заменяет переписку в директе — клиенты записываются сами, мастер видит расписание в админке, оплата через СБП.

## Возможности

- Запись клиентов к мастеру с выбором услуги и времени
- Каталог услуг с ценами
- Оплата через СБП прямо в боте
- AI-ассистент на базе Gemini Flash API
- Админ-панель: расписание, список записей, управление услугами
- Задеплоен на Railway — работает 24/7

## Стек

- **Python** + aiogram
- **База данных** — SQLite
- **AI** — Gemini Flash API
- **Деплой** — Railway

## Запуск локально

**1. Клонируй репозиторий**
```bash
git clone https://github.com/fukdat/nail-salon-bot.git
cd nail-salon-bot
```

**2. Установи зависимости**
```bash
pip install -r requirements.txt
```

**3. Создай `.env` файл**
```
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_id
DATABASE_URL=your_database_url
GEMINI_API_KEY=your_gemini_api_key
SBP_PHONE=your_phone_number
SBP_BANK=your_bank_name
```

- `BOT_TOKEN` — получить у [@BotFather](https://t.me/BotFather)
- `ADMIN_ID` — твой Telegram ID (узнать у [@userinfobot](https://t.me/userinfobot))
- `GEMINI_API_KEY` — получить на [aistudio.google.com](https://aistudio.google.com)

**4. Запусти бота**
```bash
python bot.py
```

## Структура проекта

```
nail-salon-bot/
├── bot.py
├── admin.py
├── client.py
├── database.py
├── gemini.py
├── admin_kb.py
├── client_kb.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Деплой на Railway

1. Форкни репозиторий
2. Создай новый проект на [railway.app](https://railway.app)
3. Подключи репозиторий
4. Добавь переменные окружения из `.env`
5. Railway сам задеплоит бота через Dockerfile

## Автор

**fukdat** — [github.com/fukdat](https://github.com/fukdat)
