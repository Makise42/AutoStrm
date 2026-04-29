from __future__ import annotations

import argparse
import asyncio
from typing import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core import logger, settings
from app.modules import Ani2Openlist, Openlist2Strm
from app.utils import RequestUtils


async def run_openlist2strm() -> None:
    await _run_configured_tasks("Openlist2Strm", settings.Openlist2Strm, Openlist2Strm)


async def run_ani2openlist() -> None:
    await _run_configured_tasks("Ani2Openlist", settings.Ani2Openlist, Ani2Openlist)


async def run_ani2openlist_all() -> None:
    if not settings.Ani2Openlist:
        logger.warning("未检测到 Ani2Openlist 配置")
        return

    total_success = 0
    total_failed = 0
    for config in settings.Ani2Openlist:
        task_id = config.get("id", config.get("target_dir", "未命名任务"))
        logger.info(f"开始执行 a2o-all：{task_id}")
        try:
            success, failed = await Ani2Openlist(**config).run_all()
            total_success += success
            total_failed += failed
        except Exception:
            total_failed += 1
            logger.exception(f"a2o-all 任务失败：{task_id}")

    logger.info(f"a2o-all 执行结束：成功 {total_success}，失败 {total_failed}")


async def _run_configured_tasks(
    name: str,
    configs: list[dict],
    factory: Callable[..., object],
) -> None:
    if not configs:
        logger.warning(f"未检测到 {name} 配置")
        return

    for config in configs:
        task_id = config.get("id", config.get("target_dir", "未命名任务"))
        logger.info(f"开始执行 {name}：{task_id}")
        try:
            task = factory(**config)
            await task.run()  # type: ignore[attr-defined]
        except Exception:
            logger.exception(f"{name} 任务失败：{task_id}")


async def run_server() -> None:
    scheduler = AsyncIOScheduler()
    add_jobs(scheduler, "Openlist2Strm", settings.Openlist2Strm, Openlist2Strm)
    add_jobs(scheduler, "Ani2Openlist", settings.Ani2Openlist, Ani2Openlist)

    if not scheduler.get_jobs():
        logger.warning("没有可运行的定时任务，程序退出")
        return

    scheduler.start()
    logger.info("AutoStrm 定时服务已启动")

    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()


def add_jobs(
    scheduler: AsyncIOScheduler,
    name: str,
    configs: list[dict],
    factory: Callable[..., object],
) -> None:
    if not configs:
        logger.warning(f"未检测到 {name} 配置")
        return

    for config in configs:
        task_id = config.get("id", config.get("target_dir", "未命名任务"))
        cron = config.get("cron")
        if not cron:
            logger.warning(f"{name} {task_id} 未设置 cron，跳过定时任务")
            continue

        task = factory(**config)
        scheduler.add_job(
            task.run,  # type: ignore[attr-defined]
            trigger=CronTrigger.from_crontab(cron),
            id=f"{name}-{task_id}",
            replace_existing=True,
        )
        logger.info(f"{name} {task_id} 已加入定时任务：{cron}")


async def amain() -> None:
    parser = argparse.ArgumentParser(description="AutoStrm")
    parser.add_argument(
        "command",
        nargs="?",
        default="server",
        choices=("server", "o2s", "a2o", "a2o-all"),
        help="server=定时服务, o2s=手动 Openlist2Strm, a2o=手动 Ani2Openlist, a2o-all=拉取所有 Ani Open 番剧",
    )
    args = parser.parse_args()

    commands: dict[str, Callable[[], Awaitable[None]]] = {
        "server": run_server,
        "o2s": run_openlist2strm,
        "a2o": run_ani2openlist,
        "a2o-all": run_ani2openlist_all,
    }
    try:
        logger.info(f"AutoStrm {settings.APP_VERSION} 启动，命令：{args.command}")
        await commands[args.command]()
    finally:
        await RequestUtils.close()


def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        logger.info("AutoStrm 已退出")


if __name__ == "__main__":
    main()

