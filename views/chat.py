"""
Файл: views/chat.py
Холст: tg_cli-views-chat.py
Описание: Рендеринг сообщений выбранного чата с выделением текущей
строки и счётчиком непрочитанных.
"""
from __future__ import annotations

from datetime import datetime

from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from tg_cli.state import AppState
from tg_cli.api.client import TelegramClientWrapper


async def render_chat_view(client: TelegramClientWrapper, state: AppState) -> Panel:
    """Возвращает Rich‑Panel со списком сообщений текущего чата."""
    if not state.chat_cursor.dialog_id:
        return Panel("[red]Нет выбранного чата[/]")

    if not state.chat_messages:
        state.chat_messages = await client.get_messages(state.chat_cursor.dialog_id, limit=50)

    lines = []
    for idx, msg in enumerate(reversed(state.chat_messages)):
        prefix = "→ " if idx == state.chat_cursor.selected_index else "  "
        ts = datetime.fromtimestamp(msg.date.timestamp()).strftime("%H:%M")
        sender = msg.from_id.user_id if msg.from_id else "?"
        text = msg.message or "<медиа>"
        line = Text(f"{prefix}[dim]{ts}[/] {sender}: {text}")
        if idx == state.chat_cursor.selected_index:
            line.stylize("reverse")
        lines.append(line)

    body = Group(*lines)
    return Panel(body, title=f"Чат {state.chat_cursor.dialog_id}")
