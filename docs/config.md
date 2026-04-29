# 配置说明

AutoStrm 默认读取 `config/config.yaml`。可以从示例文件开始：

```bash
cp config/config.yaml.example config/config.yaml
```

## Settings

```yaml
Settings:
  DEV: false
```

`DEV` 为 `true` 时用于开发调试。普通部署保持 `false` 即可。

## Openlist2Strm

`Openlist2Strm` 是一个列表，可以配置多个任务。

```yaml
Openlist2Strm:
  - id: anime
    cron: "0 3 * * *"
    url: "http://openlist:5244"
    public_url: "https://openlist.example.com"
    username: "admin"
    password: "admin_password"
    token: ""
    source_dir: "/Anime"
    target_dir: "/media/Anime"
    subtitle: true
    image: true
    nfo: true
    other_ext: ".zip,.rar"
    mode: "OpenlistURL"
```

常用字段：

- `id`：任务名称，只用于日志。
- `cron`：定时表达式。只手动运行也可以留空。
- `url`：AutoStrm 访问 Openlist API 的地址。
- `public_url`：写进 `.strm` 的公开访问地址；留空则使用 `url`。
- `username/password`：Openlist 管理员账号。
- `token`：Openlist token。填写后可不填账号密码。
- `source_dir`：Openlist 中要扫描的目录。
- `target_dir`：本地 STRM 输出目录，Docker 部署时要挂载到容器内。
- `mode`：`OpenlistURL` 写下载链接，`OpenlistPath` 写 Openlist 路径，`RawURL` 写直链。
- `other_ext`：额外下载后缀。命中的文件保持原后缀下载，不生成 `.strm`。
- `sync_server`：Openlist 上删除的文件，是否同步删除本地文件。

## Ani2Openlist

`Ani2Openlist` 也是一个列表，可以配置多个目标挂载。

```yaml
Ani2Openlist:
  - id: ani-open
    cron: "30 3 * * *"
    url: "http://openlist:5244"
    username: "admin"
    password: "admin_password"
    token: ""
    target_dir: "/Anime/Ani Open"
    rss_update: true
    src_domain: "openani.an-i.workers.dev"
    rss_domain: "api.ani.rip"
```

常用字段：

- `target_dir`：Openlist 中 UrlTree 存储的挂载路径。不存在时会自动创建。
- `rss_update`：`true` 表示通过 RSS 更新最新番剧；`false` 表示按 `year/month` 拉取指定季度。
- `year/month`：指定季度，例如 `year: 2026`、`month: 4`。
- `src_domain`：Ani Open 数据源域名，默认 `openani.an-i.workers.dev`。
- `key_word`：高级用法，用自定义路径关键字替代季度。

## Docker 路径

示例 Compose 把主机的 `./media` 挂载到容器 `/media`：

```yaml
volumes:
  - ./config/config.yaml:/app/config/config.yaml:ro
  - ./media:/media
```

因此 `target_dir` 可以写成 `/media/Anime`。主机上最终文件会出现在 `./media/Anime`。

