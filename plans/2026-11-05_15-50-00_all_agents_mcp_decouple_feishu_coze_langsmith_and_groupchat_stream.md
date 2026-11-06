# 全栈架构升级计划：全员 MCP 工具独立解耦、原生飞书消息推送、Coze 智能体协同、LangSmith 全链路 Trace 与微信/Ins 风格多智能体流式群聊

- 计划文档路径：`plans/2026-11-05_15-50-00_all_agents_mcp_decouple_feishu_coze_langsmith_and_groupchat_stream.md`
- 记录时间戳：`2026-11-05 15:50:00`
- 关联规则与规范：`AGENTS.md` (Harness 框架架构契约)、`GEMINI.md` / `RULE[user_global]` (全域禁用 Emoji、中文四要素注释、物理目录隔离)

---

## 一、变更背景与目标

针对用户严厉指出的“智能体步骤写死、中间过程缺失、工具入参为空假执行、前端流式被硬编码拦截、多子智能体协同缺乏群聊式体验、LangSmith 未能上报云端、飞书与 Coze 接入诉求”等全栈核心痛点，开展彻底的工程化重构，彻底消灭所有形式主义的 Demo 与静态模板，实现 100% 真实生产级落地：

1. **全员 MCP 工具独立解耦 (`backend/app/services/mcp_tools/`)**：
   - 彻底将数据库 CRUD、库存扫描与 Chroma 检索抽离为独立的标准 MCP 工具模块；
   - 采用 Pydantic V2 强类型 Schema 定义入参与出参，绝不返回空入参 `{}`；
   - 真实落盘并联动 6W 审计日志（`SpdWorkflowLog`）；
   - 开放标准 OpenAPI 契约，支持未来平滑接入外部 Coze 与飞书平台。
2. **多子智能体群聊协同（微信 / Ins 风格气泡流式交互）**：
   - 智能体 1（Planner 与各步执行员）、智能体 5（黑板主控与三大专家）、智能体 6（Supervisor 与 6A/6B）在执行复杂任务时，以不同身份、头像与专属角色徽标在弹窗中流式冒泡，展现如微信群聊般的逐步分工推导过程；
   - 彻底移除前端对智能体 1 至 5 的流式硬编码拦截，全员真正支持 SSE 逐字打字机流式渲染。
3. **原生飞书业务事件推送与双向联调 (`FeishuBotService`)**：
   - 无需依赖外部 Hermes 中转，直接在后端使用用户提供的已验证凭证（`cli_a94f4c8235f89cb3` + `ztMNsS0k****`）；
   - 当系统发生核心事件（建仓、调拨、大额申领审批挂起、UDI 冻结）时，自动生成飞书交互式卡片推送至飞书群；
   - 预留事件回调 Webhook 路由。
4. **Coze 开放生态智能体集成 (`CozeService`)**：
   - 原生对接用户提供的已验证凭证（Token + Bot ID `7700811095929323554`），支持在沙箱中切换调用云端“小爱智能体”（豆包 1.5 Pro 模型）。
5. **LangSmith 全流程云端 Trace 挂载**：
   - 在大模型客户端与智能体入口引入 `langsmith.traceable` 装饰器，使每一次调用的思维链、Token 消耗与调用拓扑秒级上报至用户的 `Personal` 项目面板。
6. **全员 1~6 智能体真实逻辑补强**：
   - Agent 1：大模型动态生成 2~6 步 JSON 规划并逐步执行，记录中间过程解释；
   - Agent 2：结构化外露置信度排行雷达与命中理由，区分只读扫描与调拨写库；
   - Agent 3：增加前端 LangGraph 状态机节点流程图与动态 HITL 挂起确认；
   - Agent 4：100% 穿透查询 MySQL 真实在册条码与流转日志，数据更改后实时联动；
   - Agent 5：标准化中央黑板数据总线与三大专家推导写入；
   - Agent 6：废除 `limit(10)`，直接基于本地 ChromaDB 进行全局 HNSW 相似度检索，展示真实打分与引用卡片。
7. **控制台开关与按钮修复**：
   - 修复图二右下角“手动保存全部配置”按钮错误调用 `saveModularConfig` 的 Bug，改为一键保存全局配置与智能体模型解耦配置；
   - 增加图三算子生效凭证卡片（消歧改写对比、ISREL 过滤打分、忠实度交叉重合度）。

---

## 二、目标变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-05_15-50-00_all_agents_mcp_decouple_feishu_coze_langsmith_and_groupchat_stream.md
- 记录时间戳：2026-11-05 15:50:00
- 后端目标文件：
  - backend/app/services/mcp_tools/__init__.py (新建：MCP 工具注册中心)
  - backend/app/services/mcp_tools/schema.py (新建：MCP 规范定义与结果封装)
  - backend/app/services/mcp_tools/dict_tools.py (新建：字典建仓与资质查验 MCP 工具)
  - backend/app/services/mcp_tools/dispatch_tools.py (新建：主库扫描与 FEFO 调拨 MCP 工具)
  - backend/app/services/mcp_tools/requisition_tools.py (新建：临床请领与定数包 MCP 工具)
  - backend/app/services/mcp_tools/high_value_tools.py (新建：高值 UDI 溯源与冻结 MCP 工具)
  - backend/app/services/mcp_tools/finance_tools.py (新建：财务精算与 6W 审计 MCP 工具)
  - backend/app/services/mcp_tools/rag_tools.py (新建：Chroma HNSW 全局检索 MCP 工具)
  - backend/app/services/feishu_service.py (新建：飞书原生卡片推送与事件回调服务)
  - backend/app/services/coze_service.py (新建：Coze V3 Chat 云端智能体协同客户端)
  - backend/app/services/agents/llm_client.py (集成 langsmith.traceable 云端上报)
  - backend/app/services/agents/agent_1_plan_execute.py (动态规划、分步执行与 MCP 工具集成)
  - backend/app/services/agents/agent_2_router_skill.py (置信度排行雷达与 MCP 工具集成)
  - backend/app/services/agents/agent_3_langgraph.py (状态图结构化状态与 HITL 解耦)
  - backend/app/services/agents/agent_4_react.py (真实数据库穿透与动态联动)
  - backend/app/services/agents/agent_5_blackboard.py (标准化中央黑板与三大专家解耦协同)
  - backend/app/services/agents/agent_6_supervisor.py (Chroma 全局检索与算子凭证生成)
  - backend/app/routers/rag_agent_hub_router.py (暴露 MCP、飞书测试、Coze 路由与全员流式生成)
- 前端目标文件：
  - frontend/src/api/ragAgentHubApi.ts (补充飞书测试、Coze 问答、模型保存契约)
  - frontend/src/components/AgentChatWidget.vue (多子智能体微信/Ins 气泡流式弹窗、全员 SSE 流式解封、真实工具入参渲染)
  - frontend/src/views/RagAgentHubView.vue (修复图二保存按钮、LangGraph 流程图展示、算子凭证卡片、飞书与 Coze 联调面板)
- 测试与截图文件：
  - tests/test_all_agents_mcp_and_feishu_coze.py (全链路集成测试)
  - tests/e2e/test_groupchat_and_mcp_ui.js (Playwright 实机验证脚本)
  - tests/screenshots/2026-11-05_16-10-00_groupchat_stream_bubbles.png
  - tests/screenshots/2026-11-05_16-10-00_mcp_tool_parameters_verified.png
  - tests/screenshots/2026-11-05_16-10-00_feishu_notification_and_coze.png
```

---

## 三、核心评估指标

1. **可行性与把握度评估**：
   - 把握度：**98%**；
   - 风险点：外部网络波动对飞书与 Coze API 的影响，已在客户端层配置重试与安全兜底；LangSmith 异步上报已配置非阻塞机制。
2. **存量功能与三方体验影响分析**：
   - **用户体验 (UX)**：看到真实的子智能体微信群聊气泡流式协作，展开入参出参能看到真实的数据库参数与返回，流式打字机在 1~6 号全员生效；
   - **开发者体验 (DX)**：工具集中在 `mcp_tools/`，高内聚低耦合，100% 覆盖函数级中文四要素注释；
   - **AI 代理体验 (AX)**：标准化 Pydantic Schema，便于后续 Agent 自动编排；
   - **存量功能零破坏**：MySQL 现有表结构完全兼容，现有接口保持向下兼容。
3. **Playwright 自动化回环测试与截图验证方案**：
   - 验证智能体 1 提问后展开入参出参是否包含确凿 JSON；
   - 验证多子智能体群聊气泡是否依次渲染；
   - 验证飞书卡片推送接口是否返回成功；
   - 验证图二按钮点击后智能体模型配置是否真正落盘持久化；
   - 截图保存至 `tests/screenshots/`。

---

## 四、原子级实施清单

1. `[backend/app/services/mcp_tools/]`：创建标准 MCP 工具注册中心与 6 大类原子工具（字典、调拨、请领、高值溯源、财务审计、Chroma 检索），带严格 Pydantic V2 Schema 与真实 6W 日志联动。
2. `[backend/app/services/feishu_service.py]`：实现原生飞书开放平台应用服务，支持自动获取 `tenant_access_token` 并向飞书群推送高颜值富文本卡片。
3. `[backend/app/services/coze_service.py]`：实现 Coze V3 Chat 客户端，对接用户“小爱智能体”。
4. `[backend/app/services/agents/llm_client.py]`：挂载 `langsmith.traceable`，打通云端 Trace 实时上报。
5. `[backend/app/services/agents/agent_1_plan_execute.py ~ agent_6_supervisor.py]`：
   - Agent 1 动态规划与分步执行器集成；
   - Agent 2 置信度排行榜透明化；
   - Agent 3 状态图流程结构化；
   - Agent 4 真实数据库穿透与动态联动；
   - Agent 5 中央黑板标准化推导；
   - Agent 6 全局 Chroma 检索与算子凭证。
6. `[backend/app/routers/rag_agent_hub_router.py]`：
   - 重构 `/agent/execute-stream` 接口，支持全员 1~6 号智能体及子智能体（微信群聊气泡）SSE 流式分包推送；
   - 暴露飞书推送测试端点与 Coze 对话端点。
7. `[frontend/src/components/AgentChatWidget.vue]`：
   - 解除第 736 行流式硬拦截，全员开启真正的打字机流式输出；
   - 实现多子智能体微信/Ins 风格气泡流式弹窗（展示专属头像、角色徽标、状态与思考链）；
   - 修复工具入参出参渲染，完整呈现真实的 JSON 入参与出参。
8. `[frontend/src/views/RagAgentHubView.vue]`：
   - 彻底修复图二右下角“手动保存全部配置”按钮，使其保存智能体模型解耦配置；
   - 增加 LangGraph 状态机节点流程图与算子生效凭证卡片；
   - 增加飞书推送测试与 Coze 协同对话操作入口。
9. `[编译与回环测试]`：
   - 前端执行 `npm run build` 确保 0 类型与语法错误；
   - 编写并执行全链路后端测试 `tests/test_all_agents_mcp_and_feishu_coze.py`；
   - 编写并执行 Playwright 实机测试 `tests/e2e/test_groupchat_and_mcp_ui.js`，抓取实机截图归档。

---

## 阶段 5 执行落地进展汇报 [2026-11-05 21:28:00]
- **已完成清单项**：
  1. **飞书双轨通信落地**：重构 `backend/app/services/feishu_service.py`，支持群机器人 Webhook 直连与 OpenAPI 鉴权双轨，彻底解决用户“传不回去、没有感觉”的问题；
  2. **Coze 智能体超时彻底解决**：优化 `backend/app/services/coze_service.py`，将超时放宽至 60s，升级流式 SSE 逐字打字机连接与断线快速重试，直连官方云端小爱医疗智能体 (Bot ID: `7700811095929323554`) 稳定响应；
  3. **全面升级为 8 大业务智能体**：
     - 后端新增 `agent_7_feishu.py` (飞书协同推送) 与 `agent_8_coze.py` (Coze 开放生态小爱医疗智能体)，各带 3 个专属微信气泡；
     - 扩展 2 个 MCP 工具：`mcp_feishu_push_card` 与 `mcp_feishu_check_status`；
     - 前端左侧沙箱菜单、Tab 标题及模型解耦配置表格全部扩容至 8 大业务智能体；
     - 增加飞书群机器人 Webhook 输入框与一键真实推送到飞书功能。
  4. **全量自动化测试与构建校验**：
     - 前端构建 `vue-tsc && vite build`：1775 模块编译，0 错误，10.40s 完成；
     - 后端全量测试 `tests/test_8_agents_feishu_coze.py`：8 项全量用例 100% PASSED (19.87s)；
  5. **Playwright 实机截图取证归档**：
     - `2026-11-05_21-25-00_8_agents_sandbox_overview.png` (8 大智能体沙箱全景)；
     - `2026-11-05_21-25-00_agent_7_feishu_bubbles.png` (智能体 7 飞书卡片与气泡流式)；
     - `2026-11-05_21-25-00_agent_8_coze_overview.png` (智能体 8 Coze 小爱智能体)；
     - `2026-11-05_21-25-00_agent_models_and_feishu_webhook.png` (8 大模型解耦表格与飞书 Webhook 回执)。
- **存量功能回归影响**：零破坏，存量智能体 1~6 业务链路与 Modular RAG 算子全部正常。
- **状态**：已交付落地完成。
