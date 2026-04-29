from __future__ import annotations

from urllib.parse import quote, unquote


class URLUtils:
    SAFE = "/:?&=#%[]@!$&'()*+,;"

    @classmethod
    def encode(cls, url: str) -> str:
        return quote(url, safe=cls.SAFE)

    @staticmethod
    def decode(url: str) -> str:
        return unquote(url)

