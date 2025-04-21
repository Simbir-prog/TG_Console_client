"""
Файл: api/client.py
Холст: tg_cli-api-client.py (ID выдаётся системой)
Описание: Тонкая обёртка над TelegramClient (Telethon) с включённым tgcrypto
и методами, которые нужны UI‑слою.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Optional

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Dialog

logger = logging.getLogger(__name__)


class TelegramClientWrapper:
    """Упрощённый фасад для Telethon с методами, используемыми в tg_cli."""

    def __init__(self, client: TelegramClient):
        self._client = client

    # Атрибут‑проксирование, чтобы при необходимости вызывать любой метод Telethon
    def __getattr__(self, item):  # noqa: D401
        return getattr(self._client, item)

    async def __aenter__(self):  # noqa: D401
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # noqa: D401
        await self._client.disconnect()

    # -- High‑level helpers -------------------------------------------------

    async def iter_dialogs(self, limit: int = 100) -> AsyncIterator[Dialog]:
        async for dialog in self._client.iter_dialogs(limit=limit):
            yield dialog

    # Дополнительные методы (send_reply, mark_read) можно добавить по мере надобности


# ---------------------------------------------------------------------------
# Функция‑фабрика: создаёт и авторизует TelegramClient, возвращает обёртку
# ---------------------------------------------------------------------------


async def create_client(session_path: Path, config: dict) -> TelegramClientWrapper:
    """Создаёт TelegramClient + tgcrypto, при необходимости запрашивает логин."""

    # Важный момент: tgcrypto подгружается автоматически при установке telethon‑tgcrypto
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    if not api_id or not api_hash:
        raise RuntimeError("api_id/api_hash не заданы в конфиге")

    session_path.parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(session_path), api_id, api_hash)

    await client.connect()
    if not await client.is_user_authorized():
        phone = input("Введите номер телефона: ")
        await client.send_code_request(phone)
        code = input("Код из Telegram: ")
        await client.sign_in(phone, code)
        # Можно сохранить строковую сессию для удобства
        string_session = StringSession.save(client.session)
        (session_path.parent / "session.txt").write_text(string_session)

    logger.info("Telegram клиент готов")
    return TelegramClientWrapper(client)
