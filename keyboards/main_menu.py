from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статус"), KeyboardButton(text="💻 Консоль")],
            [KeyboardButton(text="🧩 Моды"), KeyboardButton(text="⚙️ Система")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел...",
    )
