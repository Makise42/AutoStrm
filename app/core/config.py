from __future__ import annotations

from pathlib import Path
from typing import Any

from yaml import safe_load


class Settings:
    APP_NAME = "AutoStrm"
    APP_VERSION = "0.1.0"

    def __init__(self) -> None:
        self.config_path = Path("config/config.yaml")
        self._data: dict[str, Any] | None = None

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    "未找到 config/config.yaml，请先复制 config/config.yaml.example 并修改配置。"
                )
            with self.config_path.open("r", encoding="utf-8") as file:
                self._data = safe_load(file) or {}
        return self._data

    @property
    def DEBUG(self) -> bool:
        return bool(self.data.get("Settings", {}).get("DEV", False))

    @property
    def Openlist2Strm(self) -> list[dict[str, Any]]:
        value = self.data.get("Openlist2Strm", [])
        return value if isinstance(value, list) else []

    @property
    def Ani2Openlist(self) -> list[dict[str, Any]]:
        value = self.data.get("Ani2Openlist", [])
        return value if isinstance(value, list) else []


settings = Settings()

