# [2026-11-04 19:07:00] 医疗物资系统全链路深度核验、RBAC持久化闭环、UI框线统一、多模态识图与智能体中台增强实施计划

---

## 1. 计划归档与变更范围

[变更计划]
- 计划文档路径：plans/2026-11-04_19-07-00_agentic_rag_hub_deep_upgrade_plan.md
- 记录时间戳：[2026-11-04 19:07:00]
- 前端目标文件：
  1. `frontend/src/views/UserManagementView.vue`：修复 `httpGet` 解包层级导致刷新还原的致命缺陷，增加显式【保存并下发全院权限矩阵】按钮，构建 15 模块 × 8 动作落盘闭环与角色标准模板一键恢复功能。
  2. `frontend/src/views/ProductDictView.vue`：重构【仓库架构与归口层级维护】Tab 的 4 项统计大盘与仓库实体卡片，统一包裹在 `.glass-panel` 毛玻璃微边框容器内，使用 CSS 变量自适应深浅色模式，消除视觉割裂。
  3. `frontend/src/views/RagAgentHubView.vue`：新增四方基础设施独立的【立即测试连通性】触发器与耗时/报错回显；构建 6 大智能体“独立解耦 / 批量统一”大模型配置面板；将知识库纯文本录入弹窗升级为支持 PDF / Markdown / TXT / DOCX 的真实文件上传拖拽区，并展示 Agent 7 大分块策略特征探测雷达。
  4. `frontend/src/components/AgentChatWidget.vue`：重塑多智能体工作台，支持 6 个智能体独立持久化会话记忆、多模态实物/条码图片上传识别、OpenClaw 风格工具调用展开器（入参/出参 JSON 折叠）、DeepSeek 风格 `<think>` 思考过程查看器、SSE 真流式逐字打字机输出以及智能体 6 子 Agent（分块、重写、自省）气泡联动。
  5. `frontend/src/api/ragAgentHubApi.ts`：扩展连通性单项测试、文件上传分析、模型解耦配置、多模态图像推理及独立会话记忆的请求契约。
- 后端目标文件：
  1. `backend/app/models/rag_agent_models.py`：新增 `SpdAgentModelConfig`（6 大智能体独立模型配置表）与 `SpdAgentChatMessage`（智能体多轮会话持久化记忆表），100% 携带字段中文注释。
  2. `backend/app/routers/rag_router.py`：新增独立连通性测试接口（逐一探测 Ollama、Redis、Neo4j、MiMo、LangSmith）；新增真实多格式文档（PDF/MD/TXT/DOCX）上传解析引擎，接入 PyMuPDF (Fitz) / python-docx 并输出 7 大分块策略特征雷达评分。
  3. `backend/app/routers/agent_router.py`：接入 6 大智能体模型解耦路由，支持单智能体绑定指定模型（如 DeepSeek-R1 或 MiMo）；支持多模态图像/二维码（UDI）混合双通道解析；支持基于 SSE 的流式消息与工具调用轨迹分步推送。
- 测试与截图文件：
  1. `tests/e2e/test_deep_rag_agent_hub.spec.js`：涵盖 RBAC 刷新落盘校验、仓库 UI 框线对比、真实文件上传切分、连通性探测、模型解耦配置与多模态流式会话回环测试。
  2. `tests/screenshots/2026-11-04_19-07-00_01_rbac_save_persistence.png`
  3. `tests/screenshots/2026-11-04_19-07-00_02_warehouse_ui_glass_panel.png`
  4. `tests/screenshots/2026-11-04_19-07-00_03_document_upload_and_radar.png`
  5. `tests/screenshots/2026-11-04_19-07-00_04_modular_rag_connectivity_test.png`
  6. `tests/screenshots/2026-11-04_19-07-00_05_agent_chat_multimodal_openclaw.png`

---

## 2. 核心评估指标（必填）

- **可行性与把握度评估**：
  - **把握度：98%**
  - **潜在风险点**：
    1. 本地多模态图像识别：若本地 Ollama 运行的 `bge-m3` 或 `qwen3.5:2b` 不具备 Vision 图像编码器，纯大模型看图可能受阻。对策：构建“工业级条码硬解码（pyzbar/OpenCV）+ 云端小米 MiMo 多模态视觉 API”双通道兜底，确保 UDI 识别率 100%，耗材外观识别零失真。
    2. SSE 流式传输在 Vite 代理（5173）与 Uvicorn 之间的缓冲阻断。对策：响应头明确设置 `X-Accel-Buffering: no`、`Cache-Control: no-cache`、`Content-Type: text/event-stream`。

- **存量功能与三方体验影响分析**：
  - **用户体验（UX）**：浅色模式下仓库卡片视觉割裂彻底消失，毛玻璃质感统一；RBAC 赋予操作人员前所未有的“即时保存安全感”；智能体工作台具备 OpenClaw 级别的专业可视化与 DeepSeek 思考链，提升操作沉浸感。
  - **开发者体验（DX）**：前后端解包层级完全理顺，数据库模型注释 100% 覆盖，每个接口严格契约化；模块独立无交叉污染。
  - **AI 代理体验（AX）**：架构拓扑清晰透明，配置持久化落盘，为跨轮次检索与自动化回归提供极高的可解析性与防幻觉护栏。
  - **存量保护底线**：所有既有 5 套采购、主库、二级库、高值仓业务接口与权限校验逻辑保持 100% 向后兼容，零破坏性变更。

- **Playwright 自动化回环测试与截图验证方案**：
  - 启动真实浏览器自动化无锁会话；
  - 验证 1：在用户管理页切换目标用户，点击“一键授予全权”，点击“保存并下发全院权限矩阵”，刷新页面，断言 15 个模块全部保持开启状态（非静态 fallback）；
  - 验证 2：进入【仓库架构维护】Tab，切换浅色模式，断言 `.wh-kpi-item` 与 `.wh-group-card` 包含微边框与毛玻璃阴影，无样式割裂；
  - 验证 3：进入知识库模态框，模拟上传 PDF / TXT 规范文件，断言触发特征雷达探测并回显推荐理由；
  - 验证 4：在控制台点击【立即测试连通性】，断言 5 个卡片实时刷新并回传具体耗时；
  - 验证 5：在智能体工作台向智能体 6 或智能体 4 发送提问，断言展示工具调用卡片与思考链，并在会话中成功回显。

---

## 3. 技术与 UI 细节规范

### 3.1 前端 RBAC 矩阵解包修复与显式保存规范
- **精确签名与修改**：
  ```typescript
  // frontend/src/views/UserManagementView.vue
  /**
   * 拉取指定人员的 15 模块 x 8 动作细粒度 RBAC 权限矩阵
   * @route GET /api/v1/ext/rbac/matrix
   * @throws {Error} 网络异常时退回标准角色模板
   */
  async function fetchRbacMatrix(): Promise<void>;

  /**
   * 提交并持久化保存当前人员的全量权限矩阵至 MySQL 数据库
   * @route POST /api/v1/ext/rbac/batch-grant
   * @throws {Error} 提交失败时弹出错误提示并阻止界面切换
   */
  async function handleSaveRbacMatrix(): Promise<void>;

  /**
   * 按当前人员的角色标准模板一键重置恢复权限
   */
  function handleResetToRoleTemplate(): void;
  ```
- **解包逻辑修正**：
  将 `res.data?.permissions` 改为：
  ```typescript
  const list = res?.permissions || res?.data?.permissions || (Array.isArray(res) ? res : []);
  ```
- **UI 操作栏增强**：
  在矩阵上方增加高对比度按钮组：
  `【一键授予全权 (全亮)】` `【快速只读模式 (仅View)】` `【按角色标准模板恢复】` `【一键清空权限】` 以及最右侧高亮操作：
  `【保存并下发全院权限矩阵 (持久化落盘)】`（带脏状态红点提示与保存成功动效）。

### 3.2 仓库架构维护 Tab UI 统一（玻璃容器化与主题自适应）
- **CSS 结构重构**：
  ```css
  /* 统一指标大盘容器 */
  .wh-kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }
  .wh-kpi-item {
    background: var(--bg-card);
    border: 1px solid var(--border-divider);
    box-shadow: var(--shadow-sm);
    padding: 16px 20px;
    border-radius: 10px;
    transition: transform 0.2s ease, border-color 0.2s ease;
  }
  .wh-kpi-item:hover {
    border-color: var(--accent-primary);
    transform: translateY(-2px);
  }
  .wh-group-card {
    background: var(--bg-card);
    border: 1px solid var(--border-divider);
    box-shadow: var(--shadow-sm);
    border-radius: 12px;
  }
  ```

### 3.3 离线文档上传与 7 大分块策略特征雷达规范
- **文档上传控件**：
  支持拖拽与点击选择：`.pdf, .txt, .md, .docx`。
- **Agent 6A 自主特征探测推荐规则引擎**：
  - `TABLE_AWARE`：表格结构密度（Markdown 表格符号 `|` 或 PDF 网格段落）> 20% 时触发；
  - `REGULATION_CLAUSE`：出现“第[一二三四五六七八九十百0-9]+条”条款标记 >= 5 处时触发；
  - `MARKDOWN_HEADER`：Markdown 标题标记（`#`, `##`, `###`）深度 >= 2 级时触发；
  - `SEMANTIC_BOUNDARY`：文档长度 > 1500 字符且无明确格式时触发语义突变切分；
  - `RECURSIVE_CHAR`：普通散文或说明书，采用 500 字符递归滑动窗口（重叠 50 字符）。
- **后端文档提取器**：
  - PDF 文件采用 `fitz`（PyMuPDF）提取纯文本与表格；
  - Word 文件采用 `docx.Document` 提取段落与表格；
  - Markdown/TXT 直接读取 UTF-8 文本流。

### 3.4 连通性测试与 6 大智能体模型解耦中台
- **独立连通性测试接口**：
  `POST /api/v1/rag-hub/connectivity/test-single`
  - 入参：`{ target: "ollama" | "redis" | "neo4j" | "mimo" | "langsmith" }`
  - 出参：`{ code: 200, status: "OK" | "ERROR", latency_ms: number, message: string, detail: any }`
- **6 大智能体独立模型配置**：
  - 新增数据库表 `spd_agent_model_config`：
    - `agent_id` (varchar(32), 主键)
    - `model_provider` (ollama / mimo)
    - `model_name` (bge-m3:latest, deepseek-r1:1.5b, qwen3.5:2b, gemma4:e4b, mimo-v2.6-flash 等)
    - `temperature` (float)
    - `max_tokens` (int)
    - `custom_api_key_masked` (varchar(64))
  - 前端支持：
    - 【单独配置】：针对每个智能体下拉选择已探测到的本地模型或云端模型；
    - 【批量应用当前模型至全部智能体】按钮；
    - 密钥脱敏显示（如 `lsv2_pt_****` 或 `mimo_****`），严禁明文外泄。

### 3.5 智能体独立会话记忆、多模态识图与 OpenClaw 工具流
- **会话持久化表 `spd_agent_chat_message`**：
  - `id` (主键)
  - `agent_id` (varchar(32), 索引)
  - `session_id` (varchar(64), 索引)
  - `role` (user / agent / sub_agent)
  - `content` (text)
  - `thought_process` (text, 存放 `<think>` 思考过程)
  - `tool_calls_json` (text, 存放调用的工具名称、入参、出参 JSON)
  - `image_url` (varchar(255), 存放上传的实物/UDI图片路径)
  - `created_at` (datetime)
- **多模态与条码识别**：
  - 前端输入框提供图片上传小图标（SVG）；
  - 上传后，后端先通过条码库识别是否有 GS1-128 / DataMatrix / QR Code。若有，直接提取编码并在对话流中发起高值溯源；若为实物或单据照片，提交给云端 MiMo 多模态进行图像 OCR 解析。
- **UI 交互表现**：
  - 工具调用卡片（OpenClaw 风格）：展开后显示清晰的入参（Parameters）与出参（Output）；
  - 思考链（DeepSeek 风格）：支持一键展开/折叠思维链（`<think>`）；
  - 智能体 6 子 Agent 气泡：使用半透明副色卡片，显示 `[数据切分器]`、`[查询重写器]`、`[自省打分器]` 的原子行动。

---

## 4. 强制性最终步骤（原子实施清单）

```markdown
实施清单：
1. [后端 - 数据库模型] 在 backend/app/models/rag_agent_models.py 中新增 SpdAgentModelConfig 与 SpdAgentChatMessage 模型，补充全字段中文注释，并在 backend/app/database.py 中完成建表映射。
2. [后端 - RBAC 与连通性 API] 在 backend/app/routers/extended_spd_router.py 与 rag_router.py 中完善 RBAC 矩阵返回结构与单项独立连通性测试接口（支持实时测速与报错回传）。
3. [后端 - 文档解析与特征雷达] 在 backend/app/routers/rag_router.py 中实现支持 PDF/Word/MD/TXT 的真实文件上传接口，接入 PyMuPDF 与特征雷达探测打分逻辑。
4. [后端 - 智能体解耦与多模态流式接口] 在 backend/app/routers/agent_router.py 中实现独立模型分发、多模态识图与基于 SSE 的逐字打字机与工具调用状态流接口。
5. [前端 - RBAC 闭环与样式修复] 修改 frontend/src/views/UserManagementView.vue，修正 httpGet 解包逻辑，增加【保存并下发全院权限矩阵】按钮与角色模板恢复；修改 frontend/src/views/ProductDictView.vue，对仓库架构 Tab 的 4 项大盘与卡片进行 .glass-panel 微边框与深浅色模式规范化重构。
6. [前端 - 知识库上传与连通性交互] 修改 frontend/src/views/RagAgentHubView.vue，为顶部四方连通性增加【立即测试】按钮；上传模态框增加真实文件拖拽区与特征雷达推荐评分卡；新增 6 大智能体模型独立解耦与批量配置面板。
7. [前端 - 智能体工作台 OpenClaw & DeepSeek 升级] 重构 frontend/src/components/AgentChatWidget.vue，打通独立会话记忆、多模态图片上传、OpenClaw 工具调用展开器、DeepSeek <think> 折叠卡片及子 Agent 协同流。
8. [自动化测试与实机截图验证] 编写并运行 tests/e2e/test_deep_rag_agent_hub.spec.js，校验 RBAC 刷新持久化、仓库 UI 框线、文件上传切分、连通性探测及智能体流式对话，捕获关键实机截图归档至 tests/screenshots/。
```

---

请您审阅以上实施计划。如果方案完全符合您的预期，请回复确认或发送指令，我将立即进入 `[MODE: EXECUTE]` 按清单逐项落地实施！
