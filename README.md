# Minecraft Server Manager — Telegram Bot

A Telegram bot running **aiogram 3.x** for managing a Minecraft Fabric server on Linux.

## Project Structure

```
.
├── main.py # Entry point, polling + background log monitoring
├── config.py # Reading configuration from .env
├── requirements.txt
├── .env.example # Environment variable template
├── handlers/
│ ├── start.py # /start
│ ├── status.py # 📊 Status — list command via RCON
│ ├── console.py # 💻 Console — FSM console emulator via RCON
│ ├── mods.py # 🧩 Mods — list, delete, load .jar
│ └── system.py # ⚙️ System — CPU/RAM/disk, backup, restart
├── keyboards/
│ ├── main_menu.py # ReplyKeyboard for the main menu
│ └── inline.py # InlineKeyboard for actions
├── middlewares/
│ └── auth.py # Check user_id against the ADMIN_IDS list
└── services/
├── rcon.py # Asynchronous RCON client (aiomcrcon)
├── log_monitor.py # Async tail -f generator for latest.log
└── backup.py # Create a zip archive of the world folder
```

---

## Quick Start

### 1. Cloning and Environment

```bash
cd ~/telegram_bot_manage_server_minecraft
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

```bash
cp .env.example .env
nano .env
```

Fill in all variables:

| Variable | Description |
|----------------------|-----------------------------------------------|
| `BOT_TOKEN` | Bot token from @BotFather |
| `ADMIN_IDS` | Telegram user_id separated by commas |
| `RCON_HOST` | Server address (usually `localhost`) |
| `RCON_PORT` | RCON port from `server.properties` (default 25575) |
| `RCON_PASSWORD` | RCON password from `server.properties` |
| `MINECRAFT_LOG_PATH` | Path to `latest.log` |
| `MODS_DIR` | Mods folder |
| `WORLD_DIR` | World backup folder |
| `BACKUP_DIR` | Where to save backups |

Make sure to enable RCON in `server.properties`:

```properties
enable-rcon=true
rcon.port=25575
rcon.password=YOUR_PASSWORD
```

### 3. Launching

```bash
python main.py
```

To launch via systemd, see the section below.

---

## Adding the Bot User to Sudoers

To allow the bot to execute `sudo systemctl restart minecraft` **without entering a password**, you need to create a sudoers rule.

### Step 1: Find out which user the bot is running as

```bash
# If running manually
whoami

# If running via systemd (see User= in the unit file)
systemctl show telegram-mc-bot.service -p User
```

Let's say the bot is running as user **`mcbotuser`**.

### Step 2: Create a sudoers file (via visudo — the safe way)

```bash
sudo visudo -f /etc/sudoers.d/minecraft-bot
```

Add the line:

```sudoers
mcbotuser ALL=(ALL) NOPASSWD: /bin/systemctl restart minecraft
```

> **Important:** Never use `NOPASSWD: ALL`. Limit it to exactly one command.

### Step 3: Check file permissions

```bash
sudo chmod 0440 /etc/sudoers.d/minecraft-bot
sudo visudo -c # syntax check
```

### Step 4: Test operation

```bash
sudo -u mcbotuser sudo systemctl restart minecraft
```

---

## Starting via systemd

Create the file `/etc/systemd/system/telegram-mc-bot.service`:

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

## Bot features

| Section | What it can do |
|--------------|---------------------------------------------------------------------------------|
| 📊 Status | Shows a list of online players via RCON (`list`) |
| 💻 Console | FSM mode: any message → RCON → server response |
| 🧩 Mods | List of .jar files, delete with a button, upload .jar files via a document |
| ⚙️ System | CPU / RAM / Disk, backup creation, server restart (with confirmation) |
| 📋 Logs | Automatic chat broadcast: player logins/logouts, messages, deaths |

---

## Security

- Access - only `ADMIN_IDS` from `.env` (middleware for all events).
- Downloadable files — only `.jar` files with name validation (protection against path traversal).

- Mod removal — check via `os`
