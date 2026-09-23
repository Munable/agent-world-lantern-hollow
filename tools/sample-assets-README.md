# 灯溪镇示例素材包

本包用于前端加载与演绎验收，不是世界状态或角色决策。

- sample-atlas.png：透明 PNG 图集；6 套外观，每套 4 方向 × 4 动作 × 4 帧；另含 6 种地块与 10 个场景物件，共 400 帧。
- sample-assets.json：schema、版本、图集尺寸、帧矩形、脚底锚点、动作帧率、来源与 SHA-256。
- 坐标单位为像素，世界每格 16 像素。PNG 不决定碰撞、路径或交互距离。
- idle / walk / talk / work 只表示画面。移动与工作以世界确认的状态为准；说话仅来自未过期的实际发言，不解析台词来执行操作。
- 没有模型、Sub-Agent、逐帧服务器请求或借用商业游戏素材。
- 来源：此仓库的原创程序化示例绘图，按附带 LICENSE 使用；这不是第三方素材版权审核证书。

在任意 Canvas/SVG/游戏引擎中，用帧矩形读取图集，以 anchor 对齐角色脚底即可。2D 图集不是 3D 模型，不承诺自动适配未知世界或生成骨骼。

复现：在仓库安装测试用 Playwright 后运行 python tools/build_sample_assets.py。运行 python tools/check_sample_assets.py 可录制受控场景的前端验收影片。正式游戏运行只需已经生成的 PNG/JSON，不需要 Playwright 或重新绘图。
