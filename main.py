import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import ADMIN_IDS, BOT_TOKEN, MINECRAFT_LOG_PATH
from handlers import console, mods, start, status, system
from keyboards.main_menu import get_main_menu
from middlewares.auth import AuthMiddleware
from services.log_monitor import tail_log

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Инициализация бота ────────────────────────────────────────────────────────

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher(storage=MemoryStorage())

# Middleware: проверка прав для всех входящих событий
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

# Роутеры: console ПЕРВЫМ — его FSM-фильтры перехватывают сообщения в console_mode
dp.include_router(console.router)
dp.include_router(start.router)
dp.include_router(status.router)
dp.include_router(mods.router)
dp.include_router(system.router)


# ── Фоновая задача мониторинга логов ─────────────────────────────────────────

async def _log_monitor_task() -> None:
    """Читает latest.log и рассылает интересные строки всем администраторам."""
    while True:
        try:
            async for line in tail_log(MINECRAFT_LOG_PATH):
                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(admin_id, f"📋 <code>{line}</code>")
                    except Exception as send_exc:  # noqa: BLE001
                        logger.warning("Не удалось отправить лог-строку admin %s: %s", admin_id, send_exc)
        except FileNotFoundError:
            logger.warning("Лог-файл не найден: %s — повтор через 15 с", MINECRAFT_LOG_PATH)
            await asyncio.sleep(15)
        except Exception as exc:  # noqa: BLE001
            logger.error("Ошибка мониторинга логов: %s — повтор через 10 с", exc)
            await asyncio.sleep(10)


# ── Startup/Shutdown хуки ─────────────────────────────────────────────────────

async def _on_startup() -> None:
    logger.info("Бот запущен. Администраторы: %s", ADMIN_IDS)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "✅ <b>Minecraft Server Manager запущен.</b>\n"
                "Используйте меню ниже или /start для навигации.",
                reply_markup=get_main_menu(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не удалось отправить приветствие admin %s: %s", admin_id, exc)


async def _on_shutdown() -> None:
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "⛔ Бот остановлен.")
        except Exception:  # noqa: BLE001
            pass


# ── Точка входа ───────────────────────────────────────────────────────────────

async def main() -> None:
    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)

    log_task = asyncio.create_task(_log_monitor_task(), name="log_monitor")
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        log_task.cancel()
        try:
            await log_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
