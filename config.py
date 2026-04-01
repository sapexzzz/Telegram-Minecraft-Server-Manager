import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

_raw_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(i.strip()) for i in _raw_ids.split(",") if i.strip().isdigit()]

RCON_HOST: str = os.getenv("RCON_HOST", "localhost")
RCON_PORT: int = int(os.getenv("RCON_PORT", "25575"))
RCON_PASSWORD: str = os.getenv("RCON_PASSWORD", "")

MINECRAFT_LOG_PATH: str = os.getenv("MINECRAFT_LOG_PATH", "/opt/minecraft/logs/latest.log")
MODS_DIR: str = os.getenv("MODS_DIR", "/opt/minecraft/mods")
WORLD_DIR: str = os.getenv("WORLD_DIR", "/opt/minecraft/world")
BACKUP_DIR: str = os.getenv("BACKUP_DIR", "/opt/minecraft/backups")
SERVER_JAR: str = os.getenv("SERVER_JAR", "/opt/minecraft/fabric-server-launch.jar")
SYSTEMD_SERVICE_NAME: str = os.getenv("SYSTEMD_SERVICE_NAME", "minecraft")
