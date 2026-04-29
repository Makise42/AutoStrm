from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Final

from feedparser import parse

from app.core import logger
from app.modules.openlist import OpenlistClient
from app.modules.ani2openlist.seasons import iter_ani_open_seasons, season_month_for
from app.utils import RequestUtils, URLUtils, UrlTreeUtils

VIDEO_MIMES: Final = frozenset({"video/mp4", "video/x-matroska"})
SUBTITLE_MIMES: Final = frozenset({"application/octet-stream"})
ZIP_MIMES: Final = frozenset({"application/zip", "application/x-zip-compressed"})
FILE_MIMES: Final = VIDEO_MIMES | SUBTITLE_MIMES | ZIP_MIMES
FOLDER_MIME: Final = "application/vnd.google-apps.folder"


class Ani2Openlist:
    def __init__(
        self,
        id: str = "",
        cron: str | None = None,
        url: str = "http://localhost:5244",
        username: str = "",
        password: str = "",
        token: str = "",
        target_dir: str = "/Anime",
        rss_update: bool = True,
        year: int | None = None,
        month: int | None = None,
        src_domain: str = "openani.an-i.workers.dev",
        rss_domain: str = "api.ani.rip",
        key_word: str | None = None,
        **_: object,
    ) -> None:
        self.id = id or "Ani2Openlist"
        self.cron = cron
        self.client = OpenlistClient(url, username, password, token)
        self.target_dir = "/" + target_dir.strip("/")
        self.rss_update = rss_update
        self.year = int(year) if year else None
        self.month = int(month) if month else None
        self.src_domain = src_domain.strip().rstrip("/")
        self.rss_domain = rss_domain.strip().rstrip("/")
        self.key_word = key_word

    async def run(self) -> None:
        logger.info(f"开始运行 Ani2Openlist：{self.id}")
        await self.client.initialize()
        url_dict = await self.load_url_dict()

        if self.rss_update:
            await self.update_rss_anime_dict(url_dict)
        else:
            await self.update_season_anime_dict(url_dict)

        await self.save_url_dict(url_dict)
        logger.info(f"Ani2Openlist 运行完成：{self.id}")

    async def run_all(self) -> tuple[int, int]:
        logger.info(f"开始拉取所有 Ani Open 番剧：{self.id}")
        await self.client.initialize()
        url_dict = await self.load_url_dict()
        success = 0
        failed = 0

        for year, month in iter_ani_open_seasons():
            try:
                await self.update_season_anime_dict(url_dict, year=year, month=month)
                success += 1
            except Exception as exc:
                failed += 1
                logger.error(f"拉取 {year}-{month} 失败：{exc}")

        await self.save_url_dict(url_dict)
        logger.info(f"所有 Ani Open 番剧拉取完成：成功 {success} 个季度，失败 {failed} 个季度")
        return success, failed

    async def load_url_dict(self) -> dict:
        storage = await self.client.get_storage_by_mount_path(
            self.target_dir,
            create=True,
            driver="UrlTree",
        )
        if storage is None:
            raise RuntimeError(f"无法创建或读取 UrlTree 存储：{self.target_dir}")
        self._storage = storage
        addition = storage.addition2dict
        return UrlTreeUtils.structure2dict(addition.get("url_structure", ""))

    async def save_url_dict(self, url_dict: dict) -> None:
        storage = self._storage
        addition = storage.addition2dict
        addition["url_structure"] = UrlTreeUtils.dict2structure(url_dict)
        storage.set_addition_by_dict(addition)
        await self.client.async_api_admin_storage_update(storage)

    async def update_season_anime_dict(
        self,
        url_dict: dict,
        year: int | None = None,
        month: int | None = None,
    ) -> None:
        key = self.get_season_key(year, month)
        logger.info(f"开始拉取 Ani Open 季度：{key}")
        url_dict.setdefault(key, {})
        await self._update_data(f"https://{self.src_domain}/{key}/", url_dict[key])

    def get_season_key(self, year: int | None = None, month: int | None = None) -> str:
        if self.key_word and year is None and month is None:
            return self.key_word

        if year is None:
            year = self.year
        if month is None:
            month = self.month

        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = season_month_for(now.month)
        else:
            month = season_month_for(month)

        if (year, month) == (2019, 4):
            raise ValueError("OpenAni 上没有 2019-4 数据，已跳过")
        if (year, month) < (2019, 1):
            raise ValueError("Ani Open 仅支持 2019-1 及之后的数据")
        return f"{year}-{month}"

    async def _update_data(self, url: str, url_dict: dict) -> None:
        response = await RequestUtils.post(url)
        if response.status_code != 200:
            raise RuntimeError(f"请求 Ani Open 失败，HTTP 状态码：{response.status_code}")

        result = response.json()
        for file in result.get("files", []):
            mime_type = file.get("mimeType", "")
            name = file.get("name", "")
            if not name:
                continue

            quoted_name = URLUtils.encode(name)
            if mime_type in FILE_MIMES:
                file_url = f"{url}{quoted_name}?d=true"
                url_dict[name] = [
                    str(file.get("size", "0")),
                    str(self._parse_openani_timestamp(file.get("createdTime", ""))),
                    file_url,
                ]
            elif mime_type == FOLDER_MIME:
                url_dict.setdefault(name, {})
                await self._update_data(f"{url}{quoted_name}/", url_dict[name])
            else:
                logger.debug(f"跳过未知 Ani Open 类型：{mime_type} {name}")

    async def update_rss_anime_dict(self, url_dict: dict) -> None:
        response = await RequestUtils.get(f"https://{self.rss_domain}/ani-download.xml")
        if response.status_code != 200:
            raise RuntimeError(f"请求 RSS 失败，HTTP 状态码：{response.status_code}")

        feeds = parse(response.text)
        for entry in feeds.entries:
            self._insert_rss_entry(url_dict, entry)

    def _insert_rss_entry(self, url_dict: dict, entry) -> None:
        parents = URLUtils.decode(entry.link).split("/")[3:]
        current = url_dict
        for index, name in enumerate(parents):
            if index == len(parents) - 1:
                current[entry.title] = [
                    str(self._size_to_bytes(entry.get("anime_size", "0 B"))),
                    str(int(parsedate_to_datetime(entry.published).timestamp())),
                    entry.link,
                ]
            else:
                current.setdefault(name, {})
                current = current[name]

    @staticmethod
    def _parse_openani_timestamp(value: str) -> int:
        if not value:
            return 0
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())

    @staticmethod
    def _size_to_bytes(value: str) -> int:
        units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        number, unit = value.split()
        return int(float(number) * units[unit.upper()])
