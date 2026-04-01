import asyncio
import logging
import subprocess

import psutil
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config import SYSTEMD_SERVICE_NAME
from keyboards.inline import server_action_confirm_keyboard, system_keyboard
from services.backup import create_backup

router = Router()
logger = logging.getLogger(__name__)


def _collect_sys_info() -> dict:
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {"cpu": cpu, "ram": ram, "disk": disk}


def _format_sys_text(info: dict) -> str:
    ram = info["ram"]
    disk = info["disk"]
    return (
        "⚙️ <b>Системная информация</b>\n\n"
        f"🖥  CPU:  <code>{info['cpu']:.1f}%</code>\n"
        f"💾 RAM:  <code>{ram.used / 1024**3:.1f} / {ram.total / 1024**3:.1f} ГБ  "
        f"({ram.percent}%)</code>\n"
        f"💿 Диск: <code>{disk.used / 1024**3:.1f} / {disk.total / 1024**3:.1f} ГБ  "
        f"({disk.percent}%)</code>"
    )


async def _run_systemctl(action: str) -> str:
    """Выполняет sudo systemctl {action} {SERVICE}. Возвращает текст результата."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["sudo", "systemctl", action, SYSTEMD_SERVICE_NAME],
                check=True,
                timeout=60,
                capture_output=True,
                text=True,
            ),
        )
        return "ok"
    except subprocess.CalledProcessError as exc:
        return f"❌ Ошибка:\n<code>{exc.stderr or exc}</code>"
    except subprocess.TimeoutExpired:
        return "❌ Превышено время ожидания."
    except Exception as exc:  # noqa: BLE001
        logger.exception("systemctl %s unexpected error", action)
        return f"❌ Неожиданная ошибка: {exc}"


# ── Кнопка «⚙️ Система» ───────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Система")
async def system_menu(message: Message) -> None:
    loop = asyncio.get_running_loop()
    info = await loop.run_in_executor(None, _collect_sys_info)
    await message.answer(
        _format_sys_text(info),
        parse_mode="HTML",
        reply_markup=system_keyboard(),
    )


@router.message(Command("sys"))
async def cmd_sys(message: Message) -> None:
    loop = asyncio.get_running_loop()
    info = await loop.run_in_executor(None, _collect_sys_info)
    await message.answer(_format_sys_text(info), parse_mode="HTML")


# ── Бэкап ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "create_backup")
async def callback_create_backup(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("⏳ Создаю бэкап, подождите…")
    result = await create_backup()
    await callback.message.answer(result, parse_mode="HTML")


# ── Запрос подтверждения (старт / стоп / рестарт) ────────────────────────────

_CONFIRM_TEXTS = {
    "confirm_start":   ("▶️", "запустить",    "start"),
    "confirm_stop":    ("⏹",  "остановить",   "stop"),
    "confirm_restart": ("🔁", "перезапустить", "restart"),
}

@router.callback_query(F.data.in_(set(_CONFIRM_TEXTS)))
async def callback_confirm_action(callback: CallbackQuery) -> None:
    icon, verb, action = _CONFIRM_TEXTS[callback.data]
    await callback.message.answer(
        f"{icon} <b>Вы уверены, что хотите {verb} сервер?</b>\n"
        "Все игроки будут отключены.",
        parse_mode="HTML",
        reply_markup=server_action_confirm_keyboard(action),
    )
    await callback.answer()


# ── Отмена ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.in_({"cancel_start", "cancel_stop", "cancel_restart"}))
async def callback_cancel_action(callback: CallbackQuery) -> None:
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()


# ── Выполнение (старт / стоп / рестарт) ──────────────────────────────────────

_ACTION_LABELS = {
    "start_server":   ("▶️", "start",   "запущен",        "запуска"),
    "stop_server":    ("⏹",  "stop",    "остановлен",     "остановки"),
    "restart_server": ("🔁", "restart", "перезапущен",    "перезапуска"),
}

@router.callback_query(F.data.in_(set(_ACTION_LABELS)))
async def callback_execute_action(callback: CallbackQuery) -> None:
    icon, action, done_word, fail_word = _ACTION_LABELS[callback.data]
    await callback.answer()
    await callback.message.edit_text(f"{icon} Выполняю…")

    result = await _run_systemctl(action)
    if result == "ok":
        await callback.message.answer(f"✅ Сервер успешно {done_word}.")
        logger.info("systemctl %s executed by user %s", action, callback.from_user.id)
    else:
        await callback.message.answer(
            f"❌ Ошибка {fail_word}:\n{result}",
            parse_mode="HTML",
        )

