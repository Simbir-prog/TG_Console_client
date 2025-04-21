"""
Файл: cli.py
Холст: tg_cli-cli.py
Описание: Точка входа для setuptools entry‑point «tgcli». Запускает app.main().
"""
from __future__ import annotations

import asyncio

from tg_cli.app import TGCLIApplication


def main():  # noqa: D401
    app = TGCLIApplication()
    asyncio.run(app.start())


if __name__ == "__main__":
    main()
