from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def console_exit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Выйти из консоли", callback_data="exit_console")]
        ]
    )


def system_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="▶️ Запуск", callback_data="confirm_start"),
                InlineKeyboardButton(text="⏹ Остановка", callback_data="confirm_stop"),
            ],
            [InlineKeyboardButton(text="🔁 Рестарт", callback_data="confirm_restart")],
            [InlineKeyboardButton(text="💾 Создать бэкап", callback_data="create_backup")],
        ]
    )


def server_action_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """action: 'start' | 'stop' | 'restart'"""
    labels = {
        "start":   ("▶️ Да, запустить",  "start_server"),
        "stop":    ("⏹ Да, остановить", "stop_server"),
        "restart": ("🔁 Да, рестарт",   "restart_server"),
    }
    yes_text, yes_cb = labels[action]
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=yes_text, callback_data=yes_cb),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{action}"),
        ]]
    )


def mods_list_keyboard(count: int) -> InlineKeyboardMarkup:
    """Кнопки 🗑 N для каждого мода, ряды по 5."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i in range(count):
        row.append(InlineKeyboardButton(text=f"🗑 {i + 1}", callback_data=f"dm:{i}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mod_delete_confirm_keyboard(idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"dm_ok:{idx}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="dm_cancel"),
        ]]
    )

