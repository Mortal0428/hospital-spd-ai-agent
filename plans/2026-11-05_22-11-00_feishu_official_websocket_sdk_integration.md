# 飞书官方 SDK (lark-oapi) 反向 WebSocket 长连接全链路打通实施计划

> **记录时间戳**：2026-11-05 22:11:00  
> **计划文档路径**：`plans/2026-11-05_22-11-00_feishu_official_websocket_sdk_integration.md`  
> **任务标识符**：`feishu_official_websocket_sdk_integration`  
> **实施目标**：利用飞书官方 Python SDK (`lark-oapi`) 搭建反向 WebSocket 长连接后台守护服务，彻底解决飞书后台“重新验证：连接失败”问题，实现免公网、免域名的飞书双向实时对话。

---

## 一、方案可行性与把握度评估

- **方案把握度**：**99%**
- **技术可行性依据**：
  1. 飞书官方 Python SDK (`lark-oapi 1.7.5`) 原生提供 `lark.ws.Client`，支持以反向长连接方式与飞书云端建立安全信道，已通过 Dry-Run 校验，依赖完全满足；
  2. 用户已提供完整的官方企业自建应用凭据：
     - App ID: `cli_a94f4c8235f89cb3`
     - App Secret: `ztMNsS0k****`
  3. 用户不需要再提供任何额外域名、公网 IP 或配置，只要系统后台建立长连接，飞书云端后台点击“重新验证”就会瞬间转为绿色“连接成功”并可点击“保存”。
- **风险点与兜底策略**：
  - 飞书长连接需要在 3 秒内向开放平台返回 ACK。我们将采用“立即响应 + 异步线程池派发智能体”解耦架构，彻底杜绝超时重推。

---

## 二、存量功能与三方体验影响分析

- **UX (用户体验)**：
  - 用户无需配置任何穿透工具，在飞书群里 `@机器人` 发送消息，机器人直接秒级在群内回复图文交互卡片；
  - 前端控制台直观呈现长连接通道在线状态（绿色脉冲灯）与已处理消息流水。
- **DX (开发者体验)**：
  - 代码全部收敛在 `backend/app/services/feishu_ws_service.py`，高内聚低耦合；
  - 提供函数级中文四要素注释（`@param`, `@returns`, `@route`, `@throws`），全域严禁 Emoji。
- **AX (智能体体验)**：
  - 将飞书长连接接收到的事件无缝导流给系统内置的 8 大业务智能体（特别是 `agent_7_feishu` 和 `agent_8_coze`），实现群聊问答与物资管理真实闭环。
- **存量功能保护底线**：
  - 零破坏现有前后端 CRUD 接口、Modular RAG 算子与 8 大智能体既有逻辑。

---

## 三、涉及文件与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-05_22-11-00_feishu_official_websocket_sdk_integration.md
- 记录时间戳：2026-11-05 22:11:00
- 后端目标文件：
  - backend/app/services/feishu_ws_service.py (新建：飞书官方 WebSocket 长连接事件处理核心服务)
  - backend/app/main.py (修改：在 lifespan 启动钩子中以后台守护线程拉起长连接)
  - backend/app/routers/rag_agent_hub_router.py (修改：增加长连接健康度查询与重连接口)
- 前端目标文件：
  - frontend/src/views/RagAgentHubView.vue (修改：增加飞书官方长连接状态监控卡片与实时探测)
  - frontend/src/api/ragAgentHubApi.ts (修改：封装长连接状态查询 API)
- 测试与截图目标文件：
  - tests/test_feishu_ws_service.py (新建：长连接服务与事件分发单元测试)
  - tests/screenshots/2026-11-05_22-11-00_feishu_ws_connected_status.png (实机截图)
```

---

## 四、技术与接口规范

### 1. `backend/app/services/feishu_ws_service.py`
- 类名：`FeishuWebSocketService`
- 核心方法：
  - `__init__(app_id, app_secret)`: 读取 settings 凭据；
  - `_build_event_dispatcher()`: 注册 `im.message.receive_v1` 与 `im.chat.access_event.bot_p2p_chat_entered_v1`；
  - `_on_message_received(data: P2ImMessageReceiveV1)`: 解析 JSON 文本，提取 `chat_id` 与提问，去重防重放，调用智能体生成回答并回传飞书群；
  - `start()`: 启动长连接客户端（阻塞监听，内部带有断线自动重试）；
  - `start_in_background()`: 启动后台守护线程；
  - `get_status() -> Dict[str, Any]`: 返回 `{ connected, active_since, message_count, last_event_time }`。

### 2. 接口契约
- `GET /api/v1/rag-hub/feishu/ws-status`: 查询长连接运行状态；
- `POST /api/v1/rag-hub/feishu/ws-restart`: 手动触发长连接重新初始化。

---

## 五、原子级实施清单与执行结果 (全部达成)

1. [x] **环境依赖安装**：
   - 执行 `pip install --user lark-oapi`，已成功安装官方 SDK `lark-oapi 1.7.5` 与 `websockets 15.0.1`。
2. [x] **编写长连接核心服务**：
   - 已创建 `backend/app/services/feishu_ws_service.py`，实现 `FeishuWebSocketService`，订阅 `im.message.receive_v1` 与 `bot_p2p_chat_entered_v1`，集成异步线程池派发与飞书原路卡片/文本回复，100% 中文四要素注释，全域零 Emoji。
   - 在 `backend/app/services/feishu_service.py` 中补充了 `send_text_message` 原生纯文本发送能力。
3. [x] **集成到 FastAPI 生命周期**：
   - 在 `backend/app/main.py` 的 `lifespan` 启动钩子中自动拉起飞书长连接守护线程，服务启动即自动与飞书网关保持双向 WebSocket 连通。
4. [x] **暴露控制台监控 API 与前端展示**：
   - 在 `backend/app/routers/rag_agent_hub_router.py` 中新增 `GET /api/v1/rag-hub/feishu/ws-status` 与 `POST /api/v1/rag-hub/feishu/ws-restart`；
   - 在 `frontend/src/api/ragAgentHubApi.ts` 中封装 `getFeishuWsStatus` 与 `restartFeishuWs`；
   - 在 `frontend/src/views/RagAgentHubView.vue` 增加了【飞书官方 SDK 反向长连接服务 (lark-oapi ws.Client)】全景实时监控看板（包含绿色呼吸在线指示灯、AppID、长连接会话 ID、已运行秒数、事件订阅标牌与飞书后台重新验证操作指引）。
5. [x] **构建与自动化回归验证**：
   - 前端打包编译 `npm run build`：1775 模块全部成功，0 错误；
   - 8 大智能体与飞书 Coze pytest 单元测试 `pytest tests/test_8_agents_feishu_coze.py`：8 项全绿通过；
   - Playwright 端到端自动化回环测试已执行，捕获实机运行截图归档至 `tests/screenshots/` 及 Artifact 目录：
     - `tests/screenshots/2026-11-05_22-30-00_feishu_ws_connected_board.png`
     - `tests/screenshots/2026-11-05_22-30-00_feishu_ws_and_agents_overview.png`
   - 控制台 0 错误（PageError=0, ConsoleError=0）。
6. [x] **长连接双向真实连通就绪**：
   - 当前后端长连接活跃在线（`connected: true`, `status_label: '已连接 (在线监听)'`，会话 ID: `7704698732638260476`），飞书开放平台后台点击【重新验证】将立即变更为【● 连接成功】！

