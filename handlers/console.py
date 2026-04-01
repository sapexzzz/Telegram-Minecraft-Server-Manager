from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from keyboards.inline import console_exit_keyboard
from keyboards.main_menu import get_main_menu
from services.rcon import send_rcon_command

router = Router()


class ConsoleStates(StatesGroup):
    console_mode = State()


# ── Вход в консоль ────────────────────────────────────────────────────────────

@router.message(F.text == "💻 Консоль")
async def enter_console(message: Message, state: FSMContext) -> None:
    await state.set_state(ConsoleStates.console_mode)
    await message.answer(
        "💻 <b>Режим консоли активирован.</b>\n"
        "Введите любую команду Minecraft — она будет выполнена через RCON.\n\n"
        "Нажмите кнопку ниже, чтобы выйти.",
        parse_mode="HTML",
        reply_markup=console_exit_keyboard(),
    )


# ── Выход из консоли (inline-кнопка) ─────────────────────────────────────────

@router.callback_query(F.data == "exit_console")
async def exit_console_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("✅ Вы вышли из режима консоли.")
    await callback.message.answer("Главное меню:", reply_markup=get_main_menu())
    await callback.answer()


# ── Отправка команды в RCON, пока активен console_mode ───────────────────────

@router.message(ConsoleStates.console_mode)
async def handle_console_input(message: Message, state: FSMContext) -> None:
    command = (message.text or "").strip()
    if not command:
        return

    response = await send_rcon_command(command)
    await message.answer(
        f"<code>$ {command}</code>\n\n"
        f"<pre>{response}</pre>",
        parse_mode="HTML",
        reply_markup=console_exit_keyboard(),
    )
