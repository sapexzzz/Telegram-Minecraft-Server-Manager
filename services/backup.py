import asyncio
import logging
import os
import shutil
from datetime import datetime

from config import BACKUP_DIR, WORLD_DIR

logger = logging.getLogger(__name__)


async def create_backup() -> str:
    """Создаёт zip-архив папки мира в BACKUP_DIR.

    Операция выполняется в пуле потоков, чтобы не блокировать event loop.
    Возвращает строку с результатом.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_stem = os.path.join(BACKUP_DIR, f"world_backup_{timestamp}")
    world_parent = os.path.dirname(os.path.abspath(WORLD_DIR))
    world_name = os.path.basename(os.path.abspath(WORLD_DIR))

    loop = asyncio.get_running_loop()
    try:
        archive_path = await loop.run_in_executor(
            None,
            lambda: shutil.make_archive(
                archive_stem,
                "zip",
                root_dir=world_parent,
                base_dir=world_name,
            ),
        )
        size_mb = os.path.getsize(archive_path) / 1024 / 1024
        logger.info("Backup created: %s (%.1f MB)", archive_path, size_mb)
        return f"✅ Бэкап создан:\n<code>{archive_path}</code>\nРазмер: {size_mb:.1f} МБ"
    except FileNotFoundError:
        return f"❌ Папка мира не найдена: <code>{WORLD_DIR}</code>"
    except Exception as exc:  # noqa: BLE001
        logger.exception("Backup failed")
        return f"❌ Ошибка создания бэкапа: {exc}"
