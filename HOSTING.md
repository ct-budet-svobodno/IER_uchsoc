# Hosting guide

## Что нужно в `.env`

Скопируй пример:

```bash
cp .env.example .env
```

Заполни минимум:

```env
BOT_TOKEN=токен_бота_от_BotFather
DATABASE_URL=sqlite+aiosqlite:////app/data/bot_data.db
```

Остальные поля опциональны:

- `ADMIN_IDS` - Telegram ID админов через запятую. Узнать свой ID можно командой `/admin` в боте.
- `QUESTIONS_CHAT_ID` - чат, куда бот пересылает вопросы пользователей.
- `SUGGESTIONS_CHAT_ID` - чат, куда бот пересылает предложения пользователей.
- `MEME_STORAGE_CHAT_ID` - чат/канал для хранения `file_id` мемов. Бота нужно добавить туда заранее.

Для групп и каналов ID обычно выглядит как отрицательное число, например `-1001234567890`.

## Локальный запуск без Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m bot.main
```

## Хостинг на VPS через Docker Compose

Подойдет любой VPS с Linux, например Ubuntu 22.04/24.04.

1. Установи Docker и Docker Compose на сервере.
2. Скопируй проект на сервер.
3. В папке проекта создай `.env`:

```bash
cp .env.example .env
```

4. Открой `.env` и впиши реальные значения, особенно `BOT_TOKEN`.
5. Запусти бота:

```bash
docker compose up -d --build
```

6. Посмотреть логи:

```bash
docker compose logs -f bot
```

7. Остановить:

```bash
docker compose down
```

8. Обновить после изменений в коде:

```bash
docker compose up -d --build
```

Бот работает через polling, поэтому домен, HTTPS и webhook не нужны. Главное, чтобы сервер имел доступ в интернет и Telegram не был заблокирован на стороне хостинга.

## Важное про данные

В `docker-compose.yml` уже подключена папка `./data:/app/data`. Поэтому для хостинга лучше оставить:

```env
DATABASE_URL=sqlite+aiosqlite:////app/data/bot_data.db
```

Так база будет храниться в папке `data` на сервере и не пропадет при пересборке контейнера.
