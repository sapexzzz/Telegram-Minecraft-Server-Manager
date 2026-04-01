import asyncio
import logging
import re
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Паттерны строк, которые нужно пересылать в чат
_PATTERNS: list[re.Pattern] = [
    re.compile(r"joined the game"),
    re.compile(r"left the game"),
    # Сообщения чата вида: <PlayerName> текст
    re.compile(r"\[Server thread/INFO\].*?:\s+<\w"),
    # Смерти игроков (стандартные фразы Minecraft)
    re.compile(
        r"\[Server thread/INFO\].*?: \w.+? (was slain|was shot|drowned|starved to death"
        r"|fell|burned|died|hit the ground|was killed|suffocated|was squashed"
        r"|blew up|was fireballed|was pricked|walked into)",
        re.IGNORECASE,
    ),
]


def _is_interesting(line: str) -> bool:
    return any(p.search(line) for p in _PATTERNS)


async def tail_log(path: str) -> AsyncGenerator[str, None]:
    """Асинхронный генератор: читает лог-файл как `tail -f` и
    отдаёт строки, соответствующие паттернам (вход/выход, чат, смерти).

    При отсутствии файла или ошибке чтения поднимает исключение
    (обработка — на стороне вызывающего кода).
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        fh.seek(0, 2)  # перемотка в конец файла
        while True:
            line = fh.readline()
            if line:
                line = line.rstrip()
                if line and _is_interesting(line):
                    yield line
            else:
                await asyncio.sleep(0.5)
