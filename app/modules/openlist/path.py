from __future__ import annotations

from datetime import datetime
from re import sub
from typing import Any, Optional

from pydantic import BaseModel

from app.utils import URLUtils


class OpenlistPath(BaseModel):
    server_url: str
    base_path: str = ""
    full_path: str

    id: Optional[str] = None
    path: Optional[str] = None
    name: str
    size: int = 0
    is_dir: bool = False
    modified: str = ""
    created: str = ""
    sign: str = ""
    thumb: str = ""
    type: int = 0
    hashinfo: str = ""
    hash_info: Optional[dict] = None
    raw_url: Optional[str] = None
    readme: Optional[str] = None
    header: Optional[str] = None
    provider: Optional[str] = None
    related: Any = None

    @property
    def abs_path(self) -> str:
        return self.base_path.rstrip("/") + self.full_path

    @property
    def download_url(self) -> str:
        url = f"{self.server_url}/d{self.abs_path}"
        if self.sign:
            url = f"{url}?sign={self.sign}"
        return URLUtils.encode(url)

    @property
    def proxy_download_url(self) -> str:
        return sub("/d/", "/p/", self.download_url, 1)

    @property
    def suffix(self) -> str:
        if self.is_dir or "." not in self.name:
            return ""
        return "." + self.name.rsplit(".", 1)[-1]

    @property
    def modified_timestamp(self) -> float:
        if not self.modified:
            return 0
        return datetime.fromisoformat(self.modified.replace("Z", "+00:00")).timestamp()
