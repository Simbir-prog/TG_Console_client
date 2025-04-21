"""
Файл: state.py
Холст: tg_cli-state.py (ID будет выдан системой)
Описание: Общие структуры данных, описывающие текущее состояние приложения
и курсоры/смещения. Содержит перечисления режимов и dataclass‑ы.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ViewMode(Enum):
    DIALOGS = auto()
    CHAT = auto()
    HELP = auto()


@dataclass
class DialogCursor:
    page_size: int = 20
    offset: int = 0  # позиция в списке всех диалогов
    only_unread: bool = False


@dataclass
class ChatCursor:
    dialog_id: Optional[int] = None  # peer ID текущего чата
    message_offset: int = 0  # сколько сообщений пролистали вверх
    selected_index: int = 0  # индекс выделенного сообщения в буфере


@dataclass
class AppState:
    view_mode: ViewMode = ViewMode.DIALOGS
    dialogs: list = field(default_factory=list)  # кэш списка диалогов (Dialog)
    chat_messages: list = field(default_factory=list)  # текущий буфер сообщений
    dialog_cursor: DialogCursor = field(default_factory=DialogCursor)
    chat_cursor: ChatCursor = field(default_factory=ChatCursor)
