# 落地真实流式输出、深度思考开关、超时与分块参数前端调节及 RAG 全链路动态热插拔实施计划

- 计划文档路径：`plans/2026-11-04_21-57-00_genuine_modular_rag_streaming_and_controls_plan.md`
- 记录时间戳：`2026-11-04 21:57:00`
- 关联诉求：
  1. 流式输出（Streaming）在前端提供真实开关，开启后逐字打字机渲染，关闭为整包返回；
  2. 深度思考（Deep Thinking）在前端提供开关，开启时展示长思考链与多维推理，关闭时直接输出精炼正文；
  3. 大模型兜底超时时间（Timeout）在前端提供滑块（10s ~ 180s）自由调节，后端真实动态使用；
  4. 分块大小（Chunk Size）与重叠（Overlap）在前端提供调节控件，上传切分时真实生效；
  5. Modular RAG 所有热插拔开关实现“变动即秒级落盘 MySQL”，彻底杜绝刷新重置；
  6. RAG 各算子开关（重写、Dense、BM25、Graph、Rerank）真实影响后端执行分支，并在回答中显式打印生效算子拓扑。

---

## 一、核心评估指标

- **方案把握度**：99%（全栈逻辑清晰解耦，SSE 流式接口、OpenAI streaming 协议与动态算子装配均有成熟模式）。
- **存量功能与三方体验影响**：
  - **UX**：彻底消除“死开关”假象，用户完全掌控流式打字速度、思考深度、超时时长与切片粒度；刷新页面 100% 保持状态；
  - **DX**：模型超参（超时、Token、思考、流式）统一由配置中心管理，杜绝任何硬编码；
  - **AX**：智能体执行轨迹具备显式的“动态算子拓扑图”，每步调用真实有据可查。

---

## 二、目标变更范围

### 1. 数据库与后端模型
- `backend/app/models/rag_agent_models.py`：
  - 在 `SpdModularRagConfig` 中新增 `enable_streaming`、`enable_deep_thinking`、`llm_timeout_seconds`、`default_chunk_size`、`default_chunk_overlap` 5 个物理字段。
- 数据库落盘校准：执行建表/ALTER 脚本，确保 MySQL 字段同步生成。

### 2. 后端服务与路由
- `backend/app/services/agents/llm_client.py`：
  - 动态读取用户设定的 `llm_timeout_seconds` 超时；
  - 支持 `enable_deep_thinking` 开关调控（开启请求长推理，关闭直接输出）；
  - 新增 SSE 流式生成生成器 `generate_stream()`；
- `backend/app/services/rag/chunkers.py`：
  - 7 大分块算子全面支持动态传入 `chunk_size` 与 `chunk_overlap` 参数；
- `backend/app/services/agents/agent_6_supervisor.py`：
  - 严格依据当前配置动态剪枝：
    - 若 `enable_query_rewrite == 0`，完全跳过重写自省；
    - 若 `enable_bm25_sparse == 0`，跳过 BM25 检索；
    - 若 `enable_graph_rag == 0`，跳过 Neo4j 图谱；
    - 若 `enable_reranker == 0`，跳过 Cross-Encoder 重排；
  - 结构化输出当前真实激活的“算子拓扑清单”；
- `backend/app/routers/rag_agent_hub_router.py`：
  - 新增 `/rag-hub/agent/execute-stream` 流式 SSE 路由；
  - 完善 `/rag-hub/document/upload-file` 与 `/config/update`，支持动态超时、分块参数与秒级自动持久化。

### 3. 前端控制台与智能体沙箱
- `frontend/src/views/RagAgentHubView.vue`：
  - 增加“流式输出开关”、“深度思考开关”、“兜底超时调节滑块 (10s ~ 180s)”、“默认分块大小 (200~1500)”与“重叠度 (0~300)”；
  - 为所有配置项增加 `@change="handleAutoSaveConfig"`，实现**秒级自动落盘保存**；
  - 顶部显式增加“配置已同步至 MySQL”实时徽章；
  - 文档上传弹窗增加分块参数高级自定义；
- `frontend/src/components/AgentChatWidget.vue`：
  - 接入 SSE 流式文本接收与打字机动效；
  - 增加顶部微控开关：可独立临时切换当前智能体的“流式打字”与“深度思考”。

### 4. 测试与验收目标
- 运行 Playwright 验证：
  1. 拨动开关并刷新，验证状态 100% 保持；
  2. 修改分块参数上传文件，验证生成的切片字符数符合指定大小；
  3. 切换深度思考开关，验证思考链有/无状态与时延差异；
  4. 截取实机证据图片。

---

## 三、原子级实施清单与验收状态

1. [x] `[backend/app/models/rag_agent_models.py]`：扩展 `SpdModularRagConfig` 模型，新增流式、思考开关、超时时长与分块大小重叠度字段，并在 MySQL 中完成同步；
2. [x] `[backend/app/services/agents/llm_client.py]`：实现动态超时控制与流式 SSE 生成器；
3. [x] `[backend/app/services/rag/chunkers.py]`：让 7 大分块策略算子全面支持动态 `chunk_size` 与 `chunk_overlap`；
4. [x] `[backend/app/services/agents/agent_6_supervisor.py]`：实现 RAG 算子的真实动态剪枝装配（重写/向量/BM25/图谱/重排根据数据库开关真正开启与跳过）；
5. [x] `[backend/app/routers/rag_agent_hub_router.py]`：挂载 SSE 流式端点，升级上传与配置更新接口；
6. [x] `[frontend/src/views/RagAgentHubView.vue]`：丰富控制台参数卡片，实现变动即自动落盘（Auto-Save），并在文档上传弹窗中暴露分块大小调节；
7. [x] `[frontend/src/components/AgentChatWidget.vue]`：适配 SSE 流式打字与深度思考热切换；
8. [x] `[编译与重启]`：执行 `npm run build` 确保 0 报错（9.48s 构建完成），重启 Uvicorn 8000 与 preview 服务；
9. [x] `[自动化验证与截图]`：运行端到端回环测试（`tests/e2e/test_genuine_modular_rag_and_controls.js`），验收热插拔刷新持久化、分块参数生效、流式输出与真实算子拓扑，截取实机证据图归档至 `tests/screenshots/`。

---

## 四、执行总结与归档记录

- 记录时间戳：`2026-11-04 22:20:00`
- 状态：**全部验收通过 (100% DONE)**
- 自动化回环测试：`tests/e2e/test_genuine_modular_rag_and_controls.js` (0 控制台报错)
- 实机截图证据：
  - `tests/screenshots/2026-11-04_modular_rag_controls_and_autosave.png`
  - `tests/screenshots/2026-11-04_genuine_modular_rag_streaming_verified.png`
