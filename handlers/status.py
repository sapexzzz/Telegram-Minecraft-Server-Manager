from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from services.rcon import send_rcon_command

router = Router()


@router.message(F.text == "📊 Статус")
async def server_status(message: Message) -> None:
    """Запрашивает список игроков через RCON и показывает статус."""
    players = await send_rcon_command("list")
    motd = await send_rcon_command("say §6[BOT]§r Проверка статуса…")  # noqa: RUF001
    # 'say' не возвращает ничего полезного — только список игроков нам нужен
    _ = motd

    await message.answer(
        f"📊 <b>Статус сервера</b>\n\n"
        f"👥 {players}",
        parse_mode="HTML",
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    await server_status(message)
