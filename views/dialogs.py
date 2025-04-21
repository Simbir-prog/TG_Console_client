"""
Файл: views/dialogs.py
Холст: tg_cli-views-dialogs.py (ID назначается системой)
Описание: Рендеринг Rich‑таблицы с диалогами и счётчиком непрочитанных.
"""
from __future__ import annotations

from typing import List, Any

from rich.table import Table
from rich.text import Text

from tg_cli.state import AppState
from tg_cli.api.client import TelegramClientWrapper


async def render_dialog_list(client: TelegramClientWrapper, state: AppState):
    """Запрашивает список диалогов (при необходимости) и формирует Rich‑таблицу."""
    if not state.dialogs:  # первичная загрузка или принудительное обновление
        dialogs = []
        async for dialog in client.iter_dialogs(limit=100):  # лимитируем, потом пагинация
            if state.dialog_cursor.only_unread and dialog.unread_count == 0:
                continue
            dialogs.append(dialog)
        state.dialogs = dialogs

    start = state.dialog_cursor.offset
    end = start + state.dialog_cursor.page_size
    slice_ = state.dialogs[start:end]

    table = Table(expand=True)
    table.add_column("№", justify="right", width=4)
    table.add_column("Тип", width=2)
    table.add_column("Название", overflow="fold")
    table.add_column("Непр.", justify="right", width=6)
    table.add_column("Последнее сообщение", overflow="ellipsis")

    for idx, dlg in enumerate(slice_, start=start + 1):
        icon = _dialog_icon(dlg)
        last_msg = (dlg.message.text[:40] + "…") if dlg.message and dlg.message.text else "<медиа>"
        table.add_row(
            str(idx),
            icon,
            dlg.name or str(dlg.entity.id),
            str(dlg.unread_count) if dlg.unread_count else "",
            last_msg,
        )
    return table


def _dialog_icon(dlg: Any) -> str:
    if dlg.is_user:
        return "👤"
    if dlg.is_group:
        return "💬"
    if dlg.is_channel:
        return "📢"
    return "?"
