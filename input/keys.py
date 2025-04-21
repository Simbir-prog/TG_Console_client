"""
Файл: input/keys.py
Холст: tg_cli-input-keys.py
Описание: Чтение клавиш в Windows‑консоли через msvcrt.getwch() и
асинхронная очередь событий.
"""
from __future__ import annotations

import asyncio
import msvcrt
from enum import Enum, auto
from typing import Optional


class Key(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    ENTER = auto()
    CHAR = auto()
    ESC = auto()

    # пользовательские
    OTHER = auto()


_SPECIAL_MAP = {
    "H": Key.UP,  # 0x48 — стрелка вверх после префикса 0xE0
    "P": Key.DOWN,
    "K": Key.LEFT,
    "M": Key.RIGHT,
}


class KeyReader:
    """Асинхронный генератор событий клавиатуры для cmd/PowerShell."""

    def __init__(self):
        self._queue: asyncio.Queue[Key | str] = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._reader())

    async def _reader(self):
        loop = asyncio.get_running_loop()
        while True:
            await loop.run_in_executor(None, self._poll_key)

    def _poll_key(self):
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch == "\x00" or ch == "\xe0":
                # спец‑клавиша, следующий символ — код
                ch2 = msvcrt.getwch()
                key = _SPECIAL_MAP.get(ch2, Key.OTHER)
                asyncio.create_task(self._queue.put(key))
            elif ch == "\r":
                asyncio.create_task(self._queue.put(Key.ENTER))
            elif ch == "\x1b":
                asyncio.create_task(self._queue.put(Key.ESC))
            else:
                asyncio.create_task(self._queue.put(ch))  # обычный символ

    async def get_next_key(self):
        return await self._queue.get()
