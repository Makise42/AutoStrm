# AutoStrm

AutoStrm 是一个面向 Openlist 的轻量工具，只做两件事：

1. `Openlist2Strm`：扫描 Openlist 里的视频文件，在本地生成 `.strm` 文件。
2. `Ani2Openlist`：把 [Ani Open](https://openani.an-i.workers.dev) 的番剧挂载到 Openlist 的 `UrlTree` 存储里。

项目面向 Linux 和 Docker 部署，不提供 Web UI。

## 名词说明

- Openlist：一个网盘聚合和文件列表服务，AutoStrm 通过它的 API 读取文件、更新存储。
- `.strm`：一个文本文件，里面通常只有一行播放地址。Jellyfin、Emby 等媒体库可以通过它播放远程视频。
- Ani Open：公开的番剧文件索引，本项目默认使用 `https://openani.an-i.workers.dev`。
- UrlTree：Openlist 的一种存储驱动，可以用一段“目录树文本”挂载远程 URL。
- 季度：Ani Open 用 `年份-季度月` 表示新番季度，例如 `2019-1`、`2026-4`。季度月只会是 `1、4、7、10`。

## 快速开始

复制配置文件：

```bash
cp config/config.yaml.example config/config.yaml
```

编辑 `config/config.yaml`，至少修改 Openlist 地址、账号或 token、挂载目录和本地媒体目录。

使用 Docker Compose：

```bash
cp docker-compose.yml.example docker-compose.yml
docker compose build
docker compose up -d
```

默认启动后会执行：

```bash
python -m app.main server
```

也就是按配置里的 `cron` 定时运行。

## 手动运行

在主机直接运行：

```bash
python3 -m app.main o2s
python3 -m app.main a2o
python3 -m app.main a2o-all
```

在 Docker Compose 中运行：

```bash
docker compose run --rm autostrm python -m app.main o2s
docker compose run --rm autostrm python -m app.main a2o
docker compose run --rm autostrm python -m app.main a2o-all
```

也可以使用 Linux 菜单：

```bash
chmod +x run.sh
./run.sh
```

菜单包含：

- `1. 手动运行 Openlist2Strm`
- `2. 手动运行 Ani2Openlist`
- `3. 拉取所有Ani Open番剧`
- `4. 退出脚本`

## 三个短命令

- `o2s`：运行 `Openlist2Strm`，适合手动刷新 STRM。
- `a2o`：运行 `Ani2Openlist`，适合手动刷新 RSS 或指定季度。
- `a2o-all`：从 `2019-1` 拉取到当前季度，适合新部署后一次性补齐历史番剧。OpenAni 没有 `2019-4`，程序会跳过它。

## 常见问题

### Openlist 地址填内网还是公网？

`url` 建议填容器或服务器能访问到的 Openlist 地址，例如 `http://openlist:5244`。`Openlist2Strm` 的 `public_url` 用来替换生成在 `.strm` 里的播放地址，适合填播放器能访问的公网地址。

### `other_ext` 为什么会下载？

视频后缀默认会生成 `.strm`。如果你把某个后缀写进 `other_ext`，表示这个后缀的文件需要保存原文件，例如 `.zip` 字幕包，或者你明确希望下载的 `.mkv`。

### 为什么跳过 `2019-4`？

`https://openani.an-i.workers.dev` 上没有 `2019-4` 这个季度目录，所以 `a2o-all` 会直接跳过，避免新部署时卡在不存在的数据上。

更多配置说明见 [docs/config.md](docs/config.md)，命令说明见 [docs/commands.md](docs/commands.md)。
