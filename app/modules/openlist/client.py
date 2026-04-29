from __future__ import annotations

from asyncio import sleep
from time import time
from typing import AsyncGenerator, Callable

from httpx import Response

from app.core import logger
from app.modules.openlist.path import OpenlistPath
from app.modules.openlist.storage import OpenlistStorage
from app.utils import RequestUtils


class OpenlistClient:
    def __init__(
        self,
        url: str,
        username: str = "",
        password: str = "",
        token: str = "",
    ) -> None:
        if not url.startswith("http"):
            url = "https://" + url
        self.url = url.rstrip("/")
        self.username = str(username)
        self.password = str(password)
        self._token = token
        self._token_expires = -1 if token else 0
        self.base_path = ""
        self.id = 0

        if not self._token and (not self.username or not self.password):
            raise ValueError("Openlist 需要 username/password 或 token")

    async def initialize(self) -> None:
        await self.api_me()

    async def _request(
        self, method: str, path: str, auth: bool = True, **kwargs
    ) -> Response:
        headers = kwargs.pop("headers", {})
        if auth:
            headers["Authorization"] = await self._get_token()
        return await RequestUtils.request(
            method, f"{self.url}{path}", headers=headers, **kwargs
        )

    async def _get_token(self) -> str:
        if self._token_expires == -1:
            return self._token

        now = int(time())
        if self._token and self._token_expires > now:
            return self._token

        response = await RequestUtils.post(
            f"{self.url}/api/auth/login",
            json={"username": self.username, "password": self.password},
        )
        if response.status_code != 200:
            raise RuntimeError(f"登录 Openlist 失败，HTTP 状态码：{response.status_code}")

        result = response.json()
        if result.get("code") != 200:
            raise RuntimeError(f"登录 Openlist 失败：{result.get('message')}")

        self._token = result["data"]["token"]
        self._token_expires = now + 2 * 24 * 60 * 60 - 5 * 60
        return self._token

    async def api_me(self) -> None:
        response = await self._request("GET", "/api/me")
        self._ensure_ok(response, "获取用户信息")
        data = response.json().get("data") or {}
        self.base_path = data.get("base_path") or ""
        self.id = data.get("id") or 0

    async def async_api_fs_list(self, dir_path: str) -> list[OpenlistPath]:
        payload = {
            "path": dir_path,
            "password": "",
            "page": 1,
            "per_page": 0,
            "refresh": False,
        }
        response = await self._request("POST", "/api/fs/list", json=payload)
        self._ensure_ok(response, f"获取目录 {dir_path}")
        data = response.json().get("data") or {}
        content = data.get("content") or []
        paths: list[OpenlistPath] = []
        prefix = dir_path.rstrip("/")
        for item in content:
            paths.append(
                OpenlistPath(
                    server_url=self.url,
                    base_path=self.base_path,
                    full_path=f"{prefix}/{item['name']}",
                    **item,
                )
            )
        return paths

    async def async_api_fs_get(self, path: str) -> OpenlistPath:
        payload = {
            "path": path,
            "password": "",
            "page": 1,
            "per_page": 0,
            "refresh": False,
        }
        response = await self._request("POST", "/api/fs/get", json=payload)
        self._ensure_ok(response, f"获取路径 {path}")
        return OpenlistPath(
            server_url=self.url,
            base_path=self.base_path,
            full_path=path,
            **response.json()["data"],
        )

    async def iter_path(
        self,
        dir_path: str,
        wait_time: float | int = 0,
        is_detail: bool = False,
        filter_func: Callable[[OpenlistPath], bool] = lambda _: True,
    ) -> AsyncGenerator[OpenlistPath, None]:
        for path in await self.async_api_fs_list(dir_path):
            await sleep(wait_time)
            if path.is_dir:
                async for child in self.iter_path(
                    path.full_path, wait_time, is_detail, filter_func
                ):
                    yield child
                continue

            if filter_func(path):
                yield await self.async_api_fs_get(path.full_path) if is_detail else path

    async def async_api_admin_storage_list(self) -> list[OpenlistStorage]:
        response = await self._request("GET", "/api/admin/storage/list")
        self._ensure_ok(response, "获取存储列表")
        data = response.json().get("data") or {}
        return [OpenlistStorage(**item) for item in data.get("content", [])]

    async def async_api_admin_storage_create(self, storage: OpenlistStorage) -> None:
        response = await self._request(
            "POST", "/api/admin/storage/create", json=self._storage_payload(storage)
        )
        self._ensure_ok(response, f"创建存储 {storage.mount_path}")

    async def async_api_admin_storage_update(self, storage: OpenlistStorage) -> None:
        payload = self._storage_payload(storage)
        payload["id"] = storage.id
        payload["status"] = storage.status
        payload["modified"] = storage.modified
        payload["disabled"] = storage.disabled
        response = await self._request(
            "POST", "/api/admin/storage/update", json=payload
        )
        self._ensure_ok(response, f"更新存储 {storage.mount_path}")

    async def get_storage_by_mount_path(
        self, mount_path: str, create: bool = False, **kwargs
    ) -> OpenlistStorage | None:
        for storage in await self.async_api_admin_storage_list():
            if storage.mount_path == mount_path:
                return storage

        logger.info(f"未找到 Openlist 存储 {mount_path}")
        if not create:
            return None

        storage = OpenlistStorage(mount_path=mount_path, **kwargs)
        await self.async_api_admin_storage_create(storage)
        for item in await self.async_api_admin_storage_list():
            if item.mount_path == mount_path:
                return item
        return storage

    @staticmethod
    def _storage_payload(storage: OpenlistStorage) -> dict:
        return {
            "mount_path": storage.mount_path,
            "order": storage.order,
            "remark": storage.remark,
            "cache_expiration": storage.cache_expiration,
            "web_proxy": storage.web_proxy,
            "webdav_policy": storage.webdav_policy,
            "down_proxy_url": storage.down_proxy_url,
            "enable_sign": storage.enable_sign,
            "driver": storage.driver,
            "order_by": storage.order_by,
            "order_direction": storage.order_direction,
            "extract_folder": storage.extract_folder,
            "addition": storage.addition,
        }

    @staticmethod
    def _ensure_ok(response: Response, action: str) -> None:
        if response.status_code != 200:
            raise RuntimeError(f"{action}失败，HTTP 状态码：{response.status_code}")
        result = response.json()
        if result.get("code") != 200:
            raise RuntimeError(f"{action}失败：{result.get('message')}")
