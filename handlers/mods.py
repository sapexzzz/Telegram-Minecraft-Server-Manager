import os
import re

from aiogram import F, Router
from aiogram.types import CallbackQuery, Document, Message

from config import MODS_DIR
from keyboards.inline import mod_delete_confirm_keyboard, mods_list_keyboard

router = Router()

# Разрешённые символы в имени файла .jar (защита от path traversal)
_SAFE_NAME_RE = re.compile(r'^[\w\-. +\[\]()@#]+\.jar$', re.ASCII)


def _is_safe_jar_name(name: str) -> bool:
    return bool(_SAFE_NAME_RE.match(name)) and "/" not in name and "\\" not in name


def _sorted_jars() -> list[str] | None:
    """None = папка не найдена, [] = пуста."""
    try:
        return sorted(f for f in os.listdir(MODS_DIR) if f.endswith(".jar"))
    except FileNotFoundError:
        return None


def _mods_text(files: list[str]) -> str:
    if not files:
        return (
            "📂 <b>Папка модов пуста.</b>\n\n"
            "Отправьте <b>.jar файл</b> в этот чат, чтобы добавить мод."
        )
    lines = "\n".join(f"{i + 1}. <code>{f}</code>" for i, f in enumerate(files))
    return (
        f"🧩 <b>Установленные моды ({len(files)}):</b>\n\n"
        f"{lines}\n\n"
        "Нажмите <b>🗑 N</b>, чтобы удалить мод №N.\n"
        "Отправьте <b>.jar файл</b>, чтобы добавить новый мод."
    )


# ── Список модов ──────────────────────────────────────────────────────────────

@router.message(F.text == "🧩 Моды")
async def list_mods(message: Message) -> None:
    files = _sorted_jars()
    if files is None:
        await message.answer(
            f"❌ Папка модов не найдена:\n<code>{MODS_DIR}</code>",
            parse_mode="HTML",
        )
        return
    kb = mods_list_keyboard(len(files)) if files else None
    await message.answer(_mods_text(files), parse_mode="HTML", reply_markup=kb)


# ── Запрос подтверждения удаления ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("dm:"))
async def ask_delete_mod(callback: CallbackQuery) -> None:
    idx = int(callback.data.split(":", 1)[1])
    files = _sorted_jars()
    if files is None or idx >= len(files):
        await callback.answer("❌ Список модов изменился, нажмите '🧩 Моды' снова.", show_alert=True)
        return
    mod_name = files[idx]
    await callback.message.answer(
        f"🗑 Удалить <code>{mod_name}</code>?",
        parse_mode="HTML",
        reply_markup=mod_delete_confirm_keyboard(idx),
    )
    await callback.answer()


# ── Подтверждённое удаление ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("dm_ok:"))
async def confirm_delete_mod(callback: CallbackQuery) -> None:
    idx = int(callback.data.split(":", 1)[1])
    files = _sorted_jars()
    if files is None or idx >= len(files):
        await callback.message.edit_text("❌ Список модов изменился.")
        await callback.answer()
        return

    mod_name = files[idx]
    if not _is_safe_jar_name(mod_name):
        await callback.answer("❌ Некорректное имя файла.", show_alert=True)
        return

    mod_path = os.path.join(MODS_DIR, mod_name)
    real_mods = os.path.realpath(MODS_DIR)
    real_target = os.path.realpath(mod_path)
    if not real_target.startswith(real_mods + os.sep):
        await callback.answer("❌ Недопустимый путь.", show_alert=True)
        return

    try:
        os.remove(mod_path)
    except FileNotFoundError:
        await callback.answer("❌ Файл уже удалён.", show_alert=True)
        await callback.answer()
        return
    except PermissionError:
        await callback.answer("❌ Нет прав на удаление.", show_alert=True)
        return
    except Exception as exc:  # noqa: BLE001
        await callback.answer(f"❌ Ошибка: {exc}", show_alert=True)
        return

    # Показываем обновлённый список
    new_files = _sorted_jars() or []
    text = f"✅ <code>{mod_name}</code> удалён.\n\n" + _mods_text(new_files)
    kb = mods_list_keyboard(len(new_files)) if new_files else None
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "dm_cancel")
async def cancel_delete_mod(callback: CallbackQuery) -> None:
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.answer()


# ── Загрузка .jar через документ ─────────────────────────────────────────────

@router.message(F.document)
async def upload_mod(message: Message) -> None:
    doc: Document = message.document

    if not doc.file_name or not doc.file_name.lower().endswith(".jar"):
        await message.answer("❌ Разрешена загрузка только файлов <b>.jar</b>.", parse_mode="HTML")
        return

    safe_name = os.path.basename(doc.file_name)
    if not _is_safe_jar_name(safe_name):
        await message.answer("❌ Имя файла содержит недопустимые символы.")
        return

    os.makedirs(MODS_DIR, exist_ok=True)
    save_path = os.path.join(MODS_DIR, safe_name)

    status_msg = await message.answer("⏳ Загружаю файл…")
    await message.bot.download(doc, destination=save_path)

    files = _sorted_jars() or []
    text = (
        f"✅ Мод <code>{safe_name}</code> загружен.\n"
        f"Не забудьте перезапустить сервер!\n\n"
        + _mods_text(files)
    )
    kb = mods_list_keyboard(len(files)) if files else None
    await status_msg.edit_text(text, parse_mode="HTML", reply_markup=kb)

