# 语义 Action 与前端表现：最小切片验收

日期：2026-09-24（UTC+8）。灯溪镇 0.2.5，Agent Guide v5，表现契约 v0.5。
整合起点：主线 `39a66c2` 与文档分支 `9704333`。原文档 PR #1 在实施期间已由另一工作流合入 `932cec3`；本变更基于该主线继续，不重复合并或覆盖原成果。
固定内核：`422fc56fd63d383fb4dd262981810d88e5db0c73`（0.13.1）。
世界定义、函数 schema、定时器版本和地图规则没有修改。身份继续以 [IDENTITY](IDENTITY.md) 为准。

## 本轮交付

**Agent 提交目标和原话，世界提交合法事实，前端解释已获准状态与事件。**
不新造 Action DSL、通用 AgentTurn、动画参数包、第二个后台或强制 Sub-Agent。
`town.look` 是读取；通过 POST 调用不使它变成世界写入 Action。

| 接口 | 服务器事实 | 两个前端的验收 |
|---|---|---|
| `town.move` | 校验 x/y，接受路径，计时结束后提交位置 | 官方像素与独立 SVG 都显示移动，最终位置一致 |
| `town.look` | 返回当前获准状态，不创建角色或动画 | 已认证读取确认自身，两个公开查看器不暴露 meta.self |
| `town.say` | 发布原文、消息引用与回执 | 原文一致，HTML 按文字显示；同 ID 原样重试不重复，改参冲突 |
| `town.interact` | 按已有目标靠近并执行规则 | NPC/旅人第一人称脚本标为游戏脚本，不冒充 Agent 自主发言 |

`tools/check_semantic_presentation.py` 使用实际 MCP 初始化、tools/list、tools/call，
而不是直接调用 Python 世界函数。调用由确定性测试代码发出，**不是自主模型测试**。
独立页面不导入官方 renderer/app 或内核 JS，只访问公开 HTTP API 与地图资源，独立实现路径插值。

## 正确性与边界

- 通用 BubbleQueue 是绝对期限的唯一调度者：过期入队拒绝、积压过期清理、显示期限截断。
  世界适配器只验证来源和时间并传递期限；历史记录不因气泡过期被删除。
- 官方前端按服务端观测 + performance.now 推进时间。本地墙钟大幅向前/后跳变不改变插值时钟。
- 公开关注保存的只有 role_id；不切换玩家 Cookie，不开放控制按钮，也不借用被关注者的私人任务。
  关注的角色未入场时明确提示。刷新恢复关注但不重演历史气泡。
- 跨域只对显式 --observer-origin 开放地图与 watch session/sync/history。默认不开启。
  预检拒绝 Authorization；不允许凭据模式；控制接口和私有读取没有因此放开。
- 独立查看器 fetch 使用 credentials: omit，测试捕获请求中无令牌、Cookie、Authorization。
  未知 presentation_version 明确拒绝，不靠猜测继续显示。

## 执行与证据

运行命令：

```sh
python -m unittest discover -s tests -q
python tools/browser_check.py
python tools/check_edges.py
python tools/check_observation.py
python tools/check_onboarding.py
python tools/check_semantic_presentation.py
python -m pip wheel --no-deps --wheel-dir dist .
```

本轮新增 6 项 Python 契约用例，包含一组实际 Node 表现测试；灯溪镇合计 76 项，最终本地全量通过。
上列五组浏览器脚本和 0.2.5 wheel 构建均通过，页面错误为零。
内核修复单独执行 161 项 foundation 测试、12 组历史套件，以及 view/stream JavaScript 测试。
气泡复现用例没有改弱期望，而是验证第二句过期后不会再开始播放。

浏览器脚本生成不含凭据的 `test-results/semantic-presentation.json`、
`semantic-game.png` 与 `semantic-independent-viewer.png`。完整命令结果由该提交 CI 重跑确认，
不把同名旧文件当成新测试成绩。Windows CI 跑单测和构建；Linux 还跑五组浏览器验收。

既有边缘验收发现 readiness 竞态：仅等待初始隐藏的欢迎框，不能证明只读会话已建立。
现在先确认角色名称及已同步的只读会话再撤销令牌；撤销后清除界面与权限的原断言不变。

## 未做、未声称

原生强模型 canary 的启动请求被执行工具安全检查阻止，未执行；没有绕过检查，
也没有把它计作 provider 故障、模型失败或成功。第二厂商强模型未验证。
本轮真实 MCP 调用可证明传输和服务器合同，不能证明所有纯聊天客户端具备 Action。

完整拖动/缩放/跟随相机、私有跨域读写、任意多流合并、100 窗口负载/长期数据库增长测试，
以及永久历史、离线自动回复，都不在本最小切片交付中。原 30 项路线清单保留逐项边界，
不因为新增几个通过用例就整体标绿。独立 SVG 页是互通示例，不是第二个正式产品。

不新增 FreeAPI 路由、供应商专用重试或工具名修复。世界状态、鉴权、回执幂等与计时器仍是
真实正确性要求，不会因为将来换更好的模型供应商而取消。

操作说明见 [独立查看器](../examples/observer/README.md)；完整规则见 [运行契约](FRONTEND_RUNTIME.md)。
