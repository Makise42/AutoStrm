from __future__ import annotations

import asyncio
from pathlib import Path
from re import Pattern, compile as re_compile

from app.core import logger
from app.modules.openlist import OpenlistClient, OpenlistPath
from app.modules.openlist2strm.exts import IMAGE_EXTS, NFO_EXTS, SUBTITLE_EXTS, VIDEO_EXTS
from app.utils import RequestUtils


class Openlist2Strm:
    def __init__(
        self,
        id: str = "",
        cron: str | None = None,
        url: str = "http://localhost:5244",
        username: str = "",
        password: str = "",
        token: str = "",
        public_url: str = "",
        source_dir: str = "/",
        target_dir: str = ".",
        flatten_mode: bool = False,
        subtitle: bool = False,
        image: bool = False,
        nfo: bool = False,
        mode: str = "OpenlistURL",
        overwrite: bool = False,
        sync_server: bool = False,
        sync_ignore: str | None = None,
        other_ext: str = "",
        max_workers: int = 50,
        max_downloaders: int = 5,
        wait_time: float | int = 0,
        **_: object,
    ) -> None:
        self.id = id or "Openlist2Strm"
        self.cron = cron
        self.client = OpenlistClient(url, username, password, token)
        self.source_dir = "/" + source_dir.strip("/")
        self.target_dir = Path(target_dir)
        self.flatten_mode = flatten_mode
        self.mode = self._normalize_mode(mode)
        self.overwrite = overwrite
        self.sync_server = sync_server
        self.wait_time = wait_time
        self.max_workers = max(1, int(max_workers))
        self.max_downloaders = max(1, int(max_downloaders))

        if public_url and not public_url.startswith("http"):
            public_url = "https://" + public_url
        self.public_url = public_url.rstrip("/") if public_url else ""

        if flatten_mode:
            subtitle = image = nfo = False

        self.download_exts: set[str] = set()
        if subtitle:
            self.download_exts |= set(SUBTITLE_EXTS)
        if image:
            self.download_exts |= set(IMAGE_EXTS)
        if nfo:
            self.download_exts |= set(NFO_EXTS)
        self.download_exts |= self.normalize_exts(other_ext)
        self.process_file_exts = VIDEO_EXTS | frozenset(self.download_exts)
        self.sync_ignore_pattern: Pattern[str] | None = (
            re_compile(sync_ignore) if sync_ignore else None
        )
        self.processed_local_paths: set[Path] = set()

    @staticmethod
    def normalize_exts(value: str | list[str] | tuple[str, ...] | None) -> set[str]:
        if not value:
            return set()
        items = value if isinstance(value, (list, tuple)) else str(value).split(",")
        normalized = set()
        for item in items:
            ext = str(item).strip().lower()
            if not ext:
                continue
            normalized.add(ext if ext.startswith(".") else f".{ext}")
        return normalized

    @staticmethod
    def _normalize_mode(mode: str) -> str:
        aliases = {
            "openlisturl": "OpenlistURL",
            "openlistpath": "OpenlistPath",
            "rawurl": "RawURL",
        }
        normalized = aliases.get(str(mode).lower())
        if not normalized:
            raise ValueError("mode 仅支持 OpenlistURL、OpenlistPath、RawURL")
        return normalized

    async def run(self) -> None:
        logger.info(f"开始运行 Openlist2Strm：{self.id}")
        await self.client.initialize()

        semaphore = asyncio.Semaphore(self.max_workers)
        download_semaphore = asyncio.Semaphore(self.max_downloaders)
        self.processed_local_paths = set()

        def should_process(path: OpenlistPath) -> bool:
            if path.is_dir:
                return False
            if any(part in path.full_path for part in ("@eaDir", "Thumbs.db", ".DS_Store")):
                return False
            if path.suffix.lower() not in self.process_file_exts:
                return False

            local_path = self.get_local_path(path)
            self.processed_local_paths.add(local_path)

            if self.overwrite or not local_path.exists():
                return True

            if path.suffix.lower() in self.download_exts:
                stat = local_path.stat()
                return stat.st_mtime < path.modified_timestamp or stat.st_size != path.size

            return False

        async def process(path: OpenlistPath) -> None:
            async with semaphore:
                await self.process_file(path, download_semaphore)

        tasks: list[asyncio.Task] = []
        is_detail = self.mode == "RawURL"
        async for path in self.client.iter_path(
            self.source_dir, self.wait_time, is_detail, should_process
        ):
            tasks.append(asyncio.create_task(process(path)))

        if tasks:
            await asyncio.gather(*tasks)

        if self.sync_server:
            await self.cleanup_local_files()

        logger.info(f"Openlist2Strm 运行完成：{self.id}")

    def get_local_path(self, path: OpenlistPath) -> Path:
        if self.flatten_mode:
            local_path = self.target_dir / path.name
        else:
            relative = path.full_path.removeprefix(self.source_dir).lstrip("/")
            local_path = self.target_dir / relative

        if path.suffix.lower() in VIDEO_EXTS and path.suffix.lower() not in self.download_exts:
            return local_path.with_suffix(".strm")
        return local_path

    async def process_file(
        self, path: OpenlistPath, download_semaphore: asyncio.Semaphore
    ) -> None:
        local_path = self.get_local_path(path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if local_path.suffix == ".strm":
            content = self.build_strm_content(path)
            local_path.write_text(content, encoding="utf-8")
            logger.info(f"已生成 STRM：{local_path}")
            return

        async with download_semaphore:
            await RequestUtils.download(path.download_url, local_path)
            logger.info(f"已下载文件：{local_path}")

    def build_strm_content(self, path: OpenlistPath) -> str:
        if self.mode == "OpenlistURL":
            content = path.download_url
            if self.public_url:
                content = content.replace(self.client.url, self.public_url, 1)
            return content
        if self.mode == "OpenlistPath":
            return path.full_path
        if self.mode == "RawURL":
            if not path.raw_url:
                raise RuntimeError(
                    f"RawURL 模式需要 Openlist 返回 raw_url，但 {path.full_path} 没有 raw_url"
                )
            return path.raw_url
        raise ValueError(f"未知模式：{self.mode}")

    async def cleanup_local_files(self) -> None:
        if not self.target_dir.exists():
            return

        all_files = (
            {path for path in self.target_dir.iterdir() if path.is_file()}
            if self.flatten_mode
            else {path for path in self.target_dir.rglob("*") if path.is_file()}
        )
        stale_files = all_files - self.processed_local_paths

        for file_path in stale_files:
            if self.sync_ignore_pattern and self.sync_ignore_pattern.search(file_path.name):
                continue
            file_path.unlink(missing_ok=True)
            logger.info(f"已删除本地过期文件：{file_path}")
            parent = file_path.parent
            while parent != self.target_dir and parent.exists():
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent

