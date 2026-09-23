# 独立只读前端示例

这个 SVG 查看器没有导入官方 renderer、app 或内核 JavaScript，也不接收身份令牌。
它只调用世界 HTTP API，独立解释相同的已确认路径、公开角色、脚本来源与灯塔状态。
它是协议互通示例，不是第二个正式游戏客户端，不包含控制、私有任务、相机或对话代理。

在仓库根目录分别启动：

```sh
python -m lantern_hollow.server --port 8840 --observer-origin http://127.0.0.1:9001
python -m http.server 9001 --bind 127.0.0.1 --directory examples/observer
```

打开本机 `http://127.0.0.1:9001`，填入 `http://127.0.0.1:8840`，连接公开世界。
公网部署使用 HTTPS 和准确的 `--observer-origin`，不是通配域名。其他 origin 默认无 CORS。

## 使用的契约

首次 GET `/play/map`，验证 `world_id=lantern-hollow` 和 `presentation_version=1`。
地图包含 width/height、tiles、targets、buildings，坐标按格，x 右、y 下。
随后 GET `/watch/session`，按 spectator snapshot 重绘角色状态，使用 server_time 与本地单调时钟插值。
前台约一秒读取一次，隐藏页五秒一次；帧动画没有网络请求。不是吞吐量优化或压测成绩。

所有 fetch 都使用 `credentials: omit`。示例只展示有限近期事件为记录，不把历史补读变成实时气泡，
不依赖完整历史重放还原当前状态。不包含永久消息归档。官方客户端仍使用原来的增量/历史游标。

服务器可对配置 origin 开放 `/play/map`、`/watch/session`、`/watch/sync`、`/watch/history` 的
公开读取；POST sync/history 需要原有 `X-Lantern-Client: 1`。控制接口没有因此开放 CORS。
公开投影始终 `meta.self=null`，不会因 Cookie 自动升级权限。鉴权、写入和私有前端跨域不在这个示例中。

验证：`python tools/check_semantic_presentation.py` 在临时世界通过真实 MCP 提交 move/look/say/interact，
同时观察官方像素页面与本示例，检查一致位置、原文、脚本标识、重复操作、版本拒绝和无凭据请求。
这里的测试驱动不是模型，也不是 Sub-Agent。

## Shared static art (0.4.0)

This independent renderer now reads `assets.manifest` from `/play/map` and loads
the public PNG/JSON sample pack. It imports no official renderer or kernel code.
PNG decoding and dimensions are checked; missing assets show the existing basic
markers with an explicit notice. World facts continue to come from public HTTP.
No credentials are used for either images or state. Artwork is optional, not a
new control protocol; this example remains read-only.
