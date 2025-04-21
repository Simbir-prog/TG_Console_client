"""
Файл: config.py
Холст: tg_cli‑config.py (ID 6802449954c881919b3d0a11f991caf6)
Описание: Загрузка пользовательского YAML‑конфига ~/.tg_cli.yaml и установка дефолтов.
Исправлена запись файла: используем контекстный менеджер и dump в поток.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import ruamel.yaml as yaml

_DEFAULTS: Dict[str, Any] = {
    "page_size": 20,
    "theme": "default",
    "only_unread": False,
    # api_id / api_hash задаёт пользователь
}


def _config_path() -> Path:
    return Path.home() / ".tg_cli.yaml"


def get_config() -> Dict[str, Any]:
    """Читает YAML‑файл или создаёт его с дефолтами."""
    path = _config_path()
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        # Создаём файл с параметрами по умолчанию
        with path.open("w", encoding="utf-8") as f:
            yaml.YAML().dump(_DEFAULTS, f)
        return dict(_DEFAULTS)

    # Читаем существующий
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # Объединяем дефолты и пользовательские значения
    merged: Dict[str, Any] = {**_DEFAULTS, **data}
    return merged
