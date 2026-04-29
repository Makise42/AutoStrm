from __future__ import annotations

from json import dumps, loads
from typing import Literal

from pydantic import BaseModel


class OpenlistStorage(BaseModel):
    id: int = 0
    status: Literal["work", "disabled"] = "work"
    remark: str = ""
    modified: str = ""
    disabled: bool = False
    mount_path: str = ""
    order: int = 0
    driver: str = "Local"
    cache_expiration: int = 30
    addition: str = "{}"
    enable_sign: bool = False
    order_by: str = "name"
    order_direction: str = "asc"
    extract_folder: str = "front"
    web_proxy: bool = False
    webdav_policy: str = "native_proxy"
    down_proxy_url: str = ""

    @property
    def addition2dict(self) -> dict:
        try:
            return loads(self.addition or "{}")
        except Exception:
            return {}

    def set_addition_by_dict(self, addition: dict) -> None:
        self.addition = dumps(addition, ensure_ascii=False)

