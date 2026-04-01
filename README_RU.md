# Minecraft Server Manager — Telegram Bot

Telegram-бот на **aiogram 3.x** для управления Minecraft Fabric 1.20.1 сервером на Linux.

## Структура проекта

```
.
├── main.py                  # Точка входа, polling + фоновый мониторинг логов
├── config.py                # Чтение конфигурации из .env
├── requirements.txt
├── .env.example             # Шаблон переменных окружения
├── handlers/
│   ├── start.py             # /start
│   ├── status.py            # 📊 Статус — команда list через RCON
│   ├── console.py           # 💻 Консоль — FSM-эмулятор консоли через RCON
│   ├── mods.py              # 🧩 Моды — список, удаление, загрузка .jar
│   └── system.py            # ⚙️ Система — CPU/RAM/диск, бэкап, рестарт
├── keyboards/
│   ├── main_menu.py         # ReplyKeyboard главного меню
│   └── inline.py            # InlineKeyboard для действий
├── middlewares/
│   └── auth.py              # Проверка user_id по списку ADMIN_IDS
└── services/
    ├── rcon.py              # Асинхронный RCON-клиент (aiomcrcon)
    ├── log_monitor.py       # Async-генератор tail -f для latest.log
    └── backup.py            # Создание zip-архива папки мира
```

---

## Быстрый старт

### 1. Клонирование и окружение

```bash
cd ~/telegram_bot_manage_server_minecraft
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Конфигурация

```bash
cp .env.example .env
nano .env
```

Заполните все переменные:

| Переменная           | Описание                                      |
|----------------------|-----------------------------------------------|
| `BOT_TOKEN`          | Токен бота от @BotFather                      |
| `ADMIN_IDS`          | Telegram user_id через запятую                |
| `RCON_HOST`          | Адрес сервера (обычно `localhost`)            |
| `RCON_PORT`          | Порт RCON из `server.properties` (по ум. 25575) |
| `RCON_PASSWORD`      | Пароль RCON из `server.properties`            |
| `MINECRAFT_LOG_PATH` | Путь к `latest.log`                           |
| `MODS_DIR`           | Папка с модами                                |
| `WORLD_DIR`          | Папка мира для бэкапа                         |
| `BACKUP_DIR`         | Куда сохранять бэкапы                         |

В `server.properties` обязательно включите RCON:

```properties
enable-rcon=true
rcon.port=25575
rcon.password=ВАШ_ПАРОЛЬ
```

### 3. Запуск

```bash
python main.py
```

Для запуска через systemd — см. раздел ниже.

---

## Добавление пользователя бота в sudoers

Чтобы бот мог выполнять `sudo systemctl restart minecraft` **без ввода пароля**, нужно создать правило sudoers.

### Шаг 1: Узнайте под каким пользователем работает бот

```bash
# Если запускаете вручную
whoami

# Если через systemd (см. User= в unit-файле)
systemctl show telegram-mc-bot.service -p User
```

Допустим, бот работает от пользователя **`mcbotuser`**.

### Шаг 2: Создайте файл sudoers (через visudo —безопасный способ)

```bash
sudo visudo -f /etc/sudoers.d/minecraft-bot
```

Добавьте строку:

```sudoers
mcbotuser ALL=(ALL) NOPASSWD: /bin/systemctl restart minecraft
```

> **Важно:** никогда не давайте `NOPASSWD: ALL`. Ограничивайте ровно одной командой.

### Шаг 3: Проверьте права файла

```bash
sudo chmod 0440 /etc/sudoers.d/minecraft-bot
sudo visudo -c    # проверка синтаксиса
```

### Шаг 4: Проверьте работу

```bash
sudo -u mcbotuser sudo systemctl restart minecraft
```

---

## Запуск через systemd

Создайте файл `/etc/systemd/system/telegram-mc-bot.service`:

```ini
[Unit]
Description=Minecraft Telegram Bot
After=network.target

[Service]
Type=simple
User=mcbotuser
WorkingDirectory=/home/mentality/scripts/telegram_bot_manage_server_minecraft
ExecStart=/home/mentality/scripts/telegram_bot_manage_server_minecraft/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
EnvironmentFile=/home/mentality/scripts/telegram_bot_manage_server_minecraft/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-mc-bot
sudo systemctl status telegram-mc-bot
```

---

## Возможности бота

| Раздел       | Что умеет                                                                       |
|--------------|---------------------------------------------------------------------------------|
| 📊 Статус    | Показывает список онлайн-игроков через RCON (`list`)                            |
| 💻 Консоль   | FSM-режим: любое сообщение → RCON → ответ сервера                               |
| 🧩 Моды      | Список .jar, удаление по кнопке, загрузка .jar через документ                   |
| ⚙️ Система   | CPU / RAM / Диск, создание бэкапа, перезапуск сервера (с подтверждением)        |
| 📋 Логи      | Автоматическая рассылка в чат: вход/выход игроков, сообщения, смерти            |

---

## Безопасность

- Доступ — только `ADMIN_IDS` из `.env` (middleware на все события).  
- Загружаемые файлы — только `.jar` с валидацией имени (защита от path traversal).  
- Удаление модов — проверка через `os.path.realpath()`, чтобы путь оставался внутри `MODS_DIR`.  
- `sudo` — ограничено одной командой в sudoers.  
- Секреты — только в `.env`, который должен быть в `.gitignore`.
