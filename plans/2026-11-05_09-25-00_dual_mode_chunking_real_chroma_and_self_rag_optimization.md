# 全栈架构升级计划：双模分块决策、物理 Chroma 向量库持久化、系统事实 Grounding 与真实 Self-RAG 闭环

- 计划文档路径：`plans/2026-11-05_09-25-00_dual_mode_chunking_real_chroma_and_self_rag_optimization.md`
- 记录时间戳：`2026-11-05 09:25:00`
- 关联规则与规范：`AGENTS.md` (Harness 框架架构契约)、`GEMINI.md` / `RULE[user_global]` (全域禁用 Emoji、中文四要素注释、物理目录隔离)

---

## 一、变更背景与目标

针对用户指出的四大核心硬伤开展彻底的工程化重构，消除一切假自省、假向量库、假开关与参数失控现象：
1. **分块策略双模决策解耦**：
   - 模式 A（`AGENT_AUTO`）：真实调用大模型（MiMo / Ollama）进行语义深度理解，输出结构化 JSON 决策理由；
   - 模式 B（`SYSTEM_BUILTIN`）：系统内置特征雷达快速启发式规则兜底，确保脱网或大模型超时下的毫秒级切分。
2. **切片滑块 500 变 700 Bug 根治**：
   - 彻底修复 `ParentChildChunker` 内部硬编码 `chunk_size=800` 的问题，各分块器严格执行用户传入的 `chunk_size` 与 `overlap`，直接正文录入与文件上传参数对齐。
3. **物理向量数据库（ChromaDB）真实持久化落盘**：
   - 部署真实 `chromadb` 官方引擎，切片实现 MySQL 关系表与 Chroma 物理向量库（`./chroma_data`）双写持久化；
   - 稠密检索直接基于 Chroma HNSW 向量索引召回，废除内存全遍历。
4. **系统内部事实（数据库 + 知识库）自检优先（System State Grounding）**：
   - 为 6 号及 1~5 号智能体构建高敏感度意图分诊：当用户询问系统事实（如“系统中有多少知识文档”、“切片总数”、“耗材种类数”、“主库库存”、“待办请领”、“冻结批次”等）时，优先查验系统内部数据库与知识库元数据，将确凿事实（Hard Facts）作为基石，彻底杜绝大模型凭空瞎猜。
5. **真实 Self-RAG 自检查、查询重写与 CRAG 评估策略**：
   - 真实 LLM 查询重写与实体消歧（非写死模板）；
   - 真实检索切片相关度自评（ISREL 阈值过滤，不足时明确提示缺乏资料，拒绝胡编）；
   - 真实答案忠实度与反向事实核验（Faithfulness Check）。
6. **前端全部开关真实可控**：
   - 无论是分块模式、查询重写、稠密检索、相关性过滤还是忠实度自检，前端开关状态变动 100% 真实改变后端的执行分支，杜绝任何虚假开关。

---

## 二、目标变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-05_09-25-00_dual_mode_chunking_real_chroma_and_self_rag_optimization.md
- 记录时间戳：2026-11-05 09:25:00
- 后端目标文件：
  - backend/app/core/config.py (补充 Chroma 与 Self-RAG 配置项)
  - backend/app/models/rag_agent_models.py (补充 enable_faithfulness_check 等字段)
  - backend/app/services/chroma_service.py (新建：ChromaDB 物理持久化单例管理器)
  - backend/app/services/rag_modular_engine.py (重构 7 大分块器遵循参数、双模决策器、Chroma 真实检索)
  - backend/app/services/agents/agent_6_supervisor.py (重构系统事实意图识别、真实 LLM 查询重写与忠实度自检)
  - backend/app/services/agents/agent_1_plan_execute.py (注入数据库与知识库事实自检)
  - backend/app/services/agents/agent_2_router_skill.py (注入系统事实自检)
  - backend/app/services/agents/agent_3_langgraph.py (注入系统事实自检)
  - backend/app/services/agents/agent_4_react.py (注入系统事实自检)
  - backend/app/services/agents/agent_5_blackboard.py (注入系统事实自检)
  - backend/app/routers/rag_agent_hub_router.py (更新上传与创建接口接收 chunk_size，暴露自检状态)
- 前端目标文件：
  - frontend/src/api/ragAgentHubApi.ts (接口契约更新)
  - frontend/src/views/RagAgentHubView.vue (补充双模单选、忠实度开关、真实生效绑定)
  - frontend/src/components/AgentChatWidget.vue (丰富系统事实问答提示词与展示)
- 测试与截图文件：
  - tests/test_dual_mode_chroma_and_self_rag.py (端到端全链路闭环验证脚本)
  - tests/screenshots/2026-11-05_09-50-00_dual_mode_and_real_chroma_verified.png
```

---

## 三、核心评估指标

1. **可行性与把握度评估**：
   - 把握度：**98%**。
   - 风险点：Windows 环境下安装 `chromadb` 若触发编译依赖，可选用轻量 Python 纯净轮子，结合本地 SQLite 存储；已提前规划好依赖装配方案。
2. **存量功能与三方体验影响分析**：
   - **用户体验 (UX)**：前端滑块设置 500 实际切出 500，所见即所得；问系统文档数与库存数秒级返回确凿数据，大模型不再信口开河；
   - **开发者体验 (DX)**：后端采用标准服务层解耦（`ChromaVectorStoreManager`），各分块器单一职责，100% 覆盖中文四要素注释；
   - **AI 代理体验 (AX)**：状态机契约明确，日志高信噪比，便于后续增量迭代；
   - **存量功能零破坏**：存量 MySQL 数据表结构完全兼容，新增字段具备合理默认值。
3. **Playwright 自动化回环测试与截图验证方案**：
   - 针对切块 500 进行上传断言；
   - 针对 Chroma 物理目录 `./chroma_data` 进行文件落盘断言；
   - 针对 Agent 6 提问“系统中有多少知识文档”断言真实返回数据库文档数；
   - 针对开关关闭/开启断言后端执行链条分支差异；
   - 自动化捕获浏览器实机运行截图存入 `tests/screenshots/`。

---

## 四、原子级实施清单

1. `[环境依赖]`：在 Python 后端环境中安装并验证 `chromadb` 向量库依赖。
2. `[backend/app/services/chroma_service.py]`：新建物理 Chroma 持久化管理器，提供集合初始化、物理切片 upsert、HNSW 向量检索及根据文档 ID 物理删除接口。
3. `[backend/app/models/rag_agent_models.py]`：在 `SpdModularRagConfig` 中补充 `enable_faithfulness_check`（忠实度自检开关）等配置字段。
4. `[backend/app/services/rag_modular_engine.py]`：
   - 彻底修复 `ParentChildChunker` 及全部分块器，消除写死 800 字硬编码，严格遵循传入的 `chunk_size` 与 `overlap`；
   - 重构 `ChunkingStrategistSubAgent`，支持双模决策：`AGENT_AUTO`（调用真实 LLM 输出 JSON）与 `SYSTEM_BUILTIN`（特征雷达规则兜底）；
   - 重构 `HybridRetriever.search_dense`，直接调用 `ChromaVectorStoreManager` 执行真实的 HNSW 稠密向量索引检索。
5. `[backend/app/routers/rag_agent_hub_router.py]`：
   - 在 `DocumentCreateRequest` 与 `post_upload_document_file` 中完整透传 `chunk_size`、`chunk_overlap` 与 `decision_mode`；
   - 在切片入库环节，严格执行 MySQL 与 ChromaDB 物理持久化双写。
6. `[backend/app/services/agents/agent_6_supervisor.py]`：
   - 实现高敏感度的“系统内部事实（数据库 + 知识库）意图识别分诊器”：优先查询系统真实文档数、切片数、目录结构与向量库状态，形成确凿事实后输出；
   - 实现真实的 LLM 查询重写与消歧逻辑（严格受控于 `enable_query_rewrite` 开关）；
   - 实现检索相关性阈值过滤（ISREL，严格受控于 `enable_reranker` 开关）；
   - 实现真实答案忠实度与反向事实核验（Faithfulness Check，严格受控于 `enable_faithfulness_check` 开关）。
7. `[backend/app/services/agents/agent_1_plan_execute.py ~ agent_5_blackboard.py]`：
   - 为 1~5 号业务智能体统一注入“系统事实（数据库+知识库）查验优先”机制，提问系统库存、单据、批次时一律先查数据库与规范知识库。
8. `[frontend/src/views/RagAgentHubView.vue]`：
   - 在上传与录入弹窗中增加“决策模式选择（真实大模型智能体 Agent / 本地内置特征规则）”单选控件；
   - 修复正文录入模式下滑块数值的正确绑定与提交；
   - 在 Modular RAG 热插拔配置抽屉中补充“真实忠实度自检 (Faithfulness)”与“系统事实自检优先 (System Grounding)”开关，确保全部开关保存后真实生效。
9. `[frontend/src/api/ragAgentHubApi.ts]`：更新配置接口入参类型定义。
10. `[编译与重启]`：前端运行 `npm run build` 确保 0 报错；重启后端 Uvicorn 8000 保证配置与模型加载就绪。
11. `[自动化测试与截图验证]`：编写端到端自动化测试脚本，验证真实 Chroma 落盘、切块大小受控、系统内部提问真实查验及开关真实影响，抓取实机截图归档。


---

## 四、执行完成记录与回环验证台账 [2026-11-05 10:32:00]

### 1. 原子清单完成情况追踪 (100% 全部达成)
- [x] 1. `[依赖与单例]`：引入并安装 `chromadb` 1.5.9，构建持久化管理器 `ChromaVectorStoreManager` (纯 ASCII 路径 `C:/Users/27705/.spd_chroma_data`，规避 Windows 中文路径 Rust 崩溃)；
- [x] 2. `[分块引擎解耦与Bug修复]`：修复 `ParentChildChunker` 内部 `800` 字符硬编码缺陷，父块与子块严格受控于 `chunk_size` (如 500)；重构 `MarkdownHeaderChunker`、`TableAwareChunker` 防止字符超限；
- [x] 3. `[双模分块引擎决策实现]`：重构 `ChunkingStrategistSubAgent`，支持 `AGENT_AUTO` (真实调用小米 MiMo LLM) 与 `SYSTEM_BUILTIN` (系统内置特征雷达快速启发式规则)；
- [x] 4. `[Chroma 物理写入与真实检索接入]`：重构 `HybridRetriever.search_dense` 与文档切片创建/上传接口，切片生成时同步计算向量并物理落盘写入 ChromaDB，删除文档时同步清空；
- [x] 5. `[模型与数据库架构扩展]`：在 `SpdModularRagConfig` 表与 ORM 模型中新增 `enable_faithfulness_check`、`enable_system_grounding`、`default_chunking_mode` 字段；
- [x] 6. `[智能体 6 意图分诊与事实优先自检]`：重构 `agent_6_supervisor.py`，检测到系统事实提问（如“系统中有多少知识文档”）时，优先真实查验 MySQL 与物理 ChromaDB，输出确凿事实报告；
- [x] 7. `[真实 Self-RAG、查询重写与忠实度自检]`：重构查询重写、ISREL 过滤与答案忠实度反向核验，受全局开关严格控制；
- [x] 8. `[业务端智能体 1~5 事实自检注入]`：为智能体 1~5 统一注入事实查验拦截，涉及字典、库存、调拨、请领、UDI 冻结等硬指标时优先查库；
- [x] 9. `[前端 API 契约扩展]`：在 `ragAgentHubApi.ts` 中对齐新增配置字段与删除文档接口；
- [x] 10. `[前端界面精雕与开关绑定]`：在 `RagAgentHubView.vue` 弹窗中彻底消除重复滑块，增加“分块决策引擎”单选组件并严格绑定 500 字符；控制台增加 Chroma 状态卡片与真实开关；
- [x] 11. `[自动化回环测试与截图交付]`：编写并执行 `tests/test_dual_mode_chroma_and_self_rag.py` (6 大测试点 100% 通过) 与 `tests/e2e/test_dual_mode_ui_and_capture.js` (Playwright 实机验证通过，0 PageError，生成 4 张高清截图)。

### 2. 回环测试与截图归档凭证
- `tests/screenshots/2026-11-05_10-31-33_01_rag_console_chroma_ready.png`：RAG Hub 中台主控制台，展示知识库目录与 Chroma 物理状态横幅；
- `tests/screenshots/2026-11-05_10-31-33_02_clean_chunking_dialog_dual_mode.png`：规范文档录入切分弹窗，消除了原重复滑块，展现“真实大模型推理 (Agent LLM 决策)”与“本地特征雷达规则 (极速内置兜底)”双模单选控件，且 500 字符滑块精准生效；
- `tests/screenshots/2026-11-05_10-31-33_03_modular_rag_switches_and_chroma.png`：Modular RAG 控制台，展示“系统事实查验优先 (System Grounding)”、“真实答案忠实度核验 (Faithfulness Check)”真实开关与 ChromaDB 存储路径与物理向量数；
- `tests/screenshots/2026-11-05_10-31-33_04_agent_6_system_grounding_verified.png`：智能体 6 沙箱对话实机验证，用户提问“系统中有多少知识文档？”，智能体识别事实查询意图，输出确凿系统内部事实报告与 Chroma 向量状态，杜绝大模型凭空瞎猜。

---

## 五、全链路极限压力测试与系统事实回测评估报告 [2026-11-05 11:38:00]

针对双模分块决策、本地 ChromaDB 物理持久化高并发、全员智能体系统内部事实 Grounding、Self-RAG 对抗样本防御以及多线程高并发混合负载，执行全方位回测与压力测试（`tests/stress_test_dual_mode_and_self_rag.py`），全量指标汇总如下：

### 1. 核心评估指标
- **总测试用例数**：71 项
- **成功通过用例**：**71 / 71 (100.0%) 全部通过**
- **失败 / 阻碍用例**：0 项
- **平均响应延迟**：1969.73 ms
- **并发检索吞吐量**：**92.8 QPS**（Chroma HNSW 稠密余弦向量检索）
- **系统并发混合吞吐量**：**136.47 req/sec**（多线程高并发 Worker 场景）

### 2. 五大模块详细测试结果与指标
1. **模块 1：极限恶劣文档分块压力测试 (5/5 PASS - 字符上限严格 <= 500)**
   - 超长无断句字符流 (2000字)：生成切片 24 个，最大单片字符数严格等于 500 字（达成目标 <= 500 字）；
   - 高密度多列长表格 (30行4列)：生成切片 30 个，最大单片字符数 91 字（保持 Markdown 表格结构完整且无截断超标）；
   - 多级深层嵌套标题规范 (6级层级)：生成切片 16 个，最大单片字符数 134 字；
   - 密集法律条款文本 (35条细则)：生成切片 5 个，最大单片字符数 480 字；
   - 极短文本微切片 (<50字)：生成切片 1 个，最大单片字符数 16 字。
   - **结论**：彻底根治此前正文录入模式下分块大小“设置 500 变 700~800”的硬编码缺陷，所有复杂场景单切片字符数 100% 受控在 500 字符以内。

2. **模块 2：ChromaDB 物理持久化高并发写入与 HNSW 稠密余弦检索压力测试 (31/31 PASS)**
   - 物理状态探测：状态就绪，物理落盘目录 `C:/Users/27705/.spd_chroma_data`，实时向量数达 260 条；
   - 30 次多线程高并发 HNSW 稠密余弦向量检索总耗时仅 0.323 秒，吞吐量达 **92.8 QPS**，单次并发检索延迟低至 **3.5 ~ 6.2 ms**；
   - **结论**：彻底脱离纯内存假向量检索，物理落盘 HNSW 具备极高单机检索并发能力与零文件锁冲突稳定性。

3. **模块 3：全员智能体 1~6 系统内部事实优先查验 (System Grounding) 回测 (11/11 PASS)**
   - Agent 6（知识文档总数、切片总数、Chroma 装配状态）：平均耗时 29~32 ms，100% 真实返回 MySQL 与 Chroma 物理元数据；
   - Agent 1（全院产品字典数、在册认证供应商数）：平均耗时 24~36 ms，100% 命中确凿字典库存事实；
   - Agent 2（主库在库重点批次、已生成分发调拨单流水）：平均耗时 18~44 ms，100% 命中主库在库事实；
   - Agent 3（临床待人工审核请领单待办、全院请领单总数流水）：平均耗时 25~34 ms，100% 命中二级库请领事实；
   - Agent 4（高值耗材在册条码总数、冻结批次、患者手术已核销数据）：平均耗时 24~38 ms，100% 命中 UDI 溯源事实；
   - Agent 5（全院多科室耗材财务精算、调拨金额与单据流水）：100% 命中中央黑板 SQL 聚合出库流水事实（`主库向各临床二级库累计调拨出库`），同时大模型结合真实事实生成精练审计结论。
   - **结论**：全员智能体系统事实查验优先机制完全生效，平均耗时仅 20~45 ms，彻底根治大模型空想瞎猜。

4. **模块 4：Self-RAG 对抗样本与低相关度负样本 ISREL 阈值过滤测试 (4/4 PASS)**
   - 纯生活常识无关负样本（红烧牛肉面烹饪）：成功识别并触发 Self-RAG 幻觉阻断防护；
   - 天气查询无关负样本（西湖天气温度）：成功识别并输出专业合规安全响应；
   - 无意义乱码噪音样本（`asd8923hjkfzxc987`）：成功过滤噪音，优雅兜底；
   - 标准正样本医疗法规咨询（三甲医院耗材首营准入证照）：走通消歧改写、Chroma 物理检索与权威引用生成。

5. **模块 5：多线程高并发混合负载压测 (20/20 PASS)**
   - 20 个高并发 Worker 同时对系统配置、事实查询、切片探测执行混合请求，总耗时 0.15 秒，达成吞吐量 **136.47 req/sec**，全量请求 HTTP 200，连接池零溢出，服务零报错。
