"""
Файл: app.py
Холст: tg_cli-app.py (ID 68024313bf48819193a5a06b142524f9)
Актуальная версия: добавлен import aioconsole и реализованы
многозначный ввод, прокрутка, загрузка старых сообщений и ответ.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, Union

import aioconsole  # <— импорт добавлен
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from tg_cli.config import get_config
from tg_cli.state import AppState, ViewMode
from tg_cli.views.dialogs import render_dialog_list
from tg_cli.views.chat import render_chat_view
from tg_cli.api.client import create_client, TelegramClientWrapper
from tg_cli.input.keys import KeyReader, Key


class TGCLIApplication:
    """Главный класс приложения."""

    def __init__(self, session_path: Optional[Path] = None):
        self.console = Console()
        self.config = get_config()
        self.state = AppState()
        self.state.dialog_cursor.page_size = self.config.get("page_size", 20)
        self.client: Optional[TelegramClientWrapper] = None
        self.session_path = session_path or Path.home() / ".tg_cli" / "session.session"

    async def start(self) -> None:  # noqa: D401
        self.client = await create_client(self.session_path, self.config)

        key_reader = KeyReader()
        await key_reader.start()

        layout = Layout(name="root")
        with Live(layout, refresh_per_second=15, console=self.console, screen=True):
            while True:
                await self._update_view(layout)
                key = await key_reader.get_next_key()
                await self._handle_key(key)

    async def _update_view(self, layout: Layout):
        if self.state.view_mode == ViewMode.DIALOGS:
            table = await render_dialog_list(self.client, self.state)
            footer = Text("n/p – страницы  u – непроч.  цифры+Enter – открыть чат  q – выход")
            if self.state.numeric_buffer:
                footer.append(f"  ▶ {self.state.numeric_buffer}")
            layout.update(Panel(table, title="Диалоги", footer=footer))
        elif self.state.view_mode == ViewMode.CHAT:
            chat_panel = await render_chat_view(self.client, self.state)
            layout.update(chat_panel)
        else:
            layout.update(Panel("[bold red]Неизвестный режим[/]"))

    async def _handle_key(self, key: Union[Key, str]):
        if self.state.view_mode == ViewMode.DIALOGS:
            await self._handle_dialog_keys(key)
        elif self.state.view_mode == ViewMode.CHAT:
            await self._handle_chat_keys(key)

    # ------------------------------------------------------------------
    # Диалоги
    # ------------------------------------------------------------------
    async def _handle_dialog_keys(self, key: Union[Key, str]):
        if isinstance(key, str) and key.isdigit():
            if key == "0" and not self.state.numeric_buffer:
                return
            self.state.numeric_buffer += key
            return

        if key == Key.ENTER and self.state.numeric_buffer:
            num = int(self.state.numeric_buffer)
            self.state.numeric_buffer = ""
            start = self.state.dialog_cursor.offset
            if 1 <= num <= self.state.dialog_cursor.page_size:
                idx = start + num - 1
                if idx < len(self.state.dialogs):
                    dlg = self.state.dialogs[idx]
                    self.state.chat_cursor.dialog_id = getattr(dlg, "id", dlg.entity.id)
                    self.state.chat_messages.clear()
                    self.state.chat_cursor.selected_index = 0
                    self.state.view_mode = ViewMode.CHAT
            return

        if isinstance(key, str):
            lk = key.lower()
            if lk in {"n", "p", "u", "q"}:
                self.state.numeric_buffer = ""

            if lk == "n" and self.state.dialog_cursor.offset + self.state.dialog_cursor.page_size < len(self.state.dialogs):
                self.state.dialog_cursor.offset += self.state.dialog_cursor.page_size
            elif lk == "p" and self.state.dialog_cursor.offset >= self.state.dialog_cursor.page_size:
                self.state.dialog_cursor.offset -= self.state.dialog_cursor.page_size
            elif lk == "u":
                self.state.dialog_cursor.only_unread = not self.state.dialog_cursor.only_unread
                self.state.dialog_cursor.offset = 0
                self.state.dialogs.clear()
            elif lk == "q":
                await self.client.disconnect()
                raise SystemExit

    # ------------------------------------------------------------------
    # Чат
    # ------------------------------------------------------------------
    async def _handle_chat_keys(self, key: Union[Key, str]):
        if key == Key.UP and self.state.chat_cursor.selected_index < len(self.state.chat_messages) - 1:
            self.state.chat_cursor.selected_index += 1
        elif key == Key.DOWN and self.state.chat_cursor.selected_index > 0:
            self.state.chat_cursor.selected_index -= 1
        elif isinstance(key, str):
            lk = key.lower()
            if lk == "u":
                last_id = self.state.chat_messages[-1].id if self.state.chat_messages else None
                if last_id:
                    older = await self.client.get_messages(
                        self.state.chat_cursor.dialog_id,
                        limit=100,
                        offset_id=last_id,
                    )
                    if older:
                        self.state.chat_messages.extend(reversed(older))
                        self.state.chat_cursor.message_offset += len(older)
            elif lk == "r" and self.state.chat_messages:
                target = self.state.chat_messages[self.state.chat_cursor.selected_index]
                text = await aioconsole.ainput("reply> ")
                if text:
                    await self.client.send_message(
                        self.state.chat_cursor.dialog_id,
                        text,
                        reply_to=target.id,
                    )
            elif lk == "b":
                if self.state.chat_messages:
                    max_id = max(m.id for m in self.state.chat_messages)
                    await self.client.send_read_acknowledge(
                        self.state.chat_cursor.dialog_id, max_id=max_id
                    )
                self.state.view_mode = ViewMode.DIALOGS
                self.state.chat_cursor = type(self.state.chat_cursor)()
                self.state.chat_messages.clear()
                self.state.numeric_buffer = ""


# ------------------------------------------------------------------
# Entry‑point
# ------------------------------------------------------------------

def main():  # noqa: D401
    app = TGCLIApplication()
    asyncio.run(app.start())


if __name__ == "__main__":
    main()
