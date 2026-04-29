# 命令说明

## Python CLI

```bash
python3 -m app.main server
python3 -m app.main o2s
python3 -m app.main a2o
python3 -m app.main a2o-all
```

- `server`：按配置里的 `cron` 启动定时服务，适合 Docker 常驻运行。
- `o2s`：手动运行 `Openlist2Strm`。
- `a2o`：手动运行 `Ani2Openlist`。
- `a2o-all`：拉取所有 Ani Open 番剧，从 `2019-1` 到当前季度，跳过不存在的 `2019-4`。

## run.sh

```bash
chmod +x run.sh
./run.sh
```

菜单选项：

```text
1. 手动运行 Openlist2Strm
2. 手动运行 Ani2Openlist
3. 拉取所有Ani Open番剧
4. 退出脚本
```

## Docker Compose

常驻服务：

```bash
docker compose up -d
```

一次性命令：

```bash
docker compose run --rm autostrm python -m app.main o2s
docker compose run --rm autostrm python -m app.main a2o
docker compose run --rm autostrm python -m app.main a2o-all
```
