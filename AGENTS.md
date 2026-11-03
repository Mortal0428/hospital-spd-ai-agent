# AGENTS.md - 专业化 Agent 职责契约与业务端 5 大智能体架构定义

> 本文件承载 **Harness 组件②（Agent 专业化分工）** 与 **项目交付核心要求（5 大业务智能体 + LangGraph + MCP + Chroma RAG + MySQL）**。

---

## 第一部分：研发协同子 Agent 专业化分工（Engineering Agents）

在项目全生命周期开发中，遵循单一职责原则（SRP），将研发职能划分为 5 个窄角色专业化 Agent，严禁跨界越权修改：

### 1. 【主调度与架构统筹 Agent (Orchestrator Agent)】
- **核心职责**：解析用户指令、维护 `plans/` 时间戳进度台账、执行 `plans/archive/` 熵管理归档、拆解原子任务并协调各专项 Agent。
- **按需挂载全局 Skills**：`edu-pm-workflow`（阶段 1 业务流与 PRD 梳理）、`minimax-docx`（阶段 5 导出项目验收报告与 5 分钟演讲逐字稿 `.docx`）、`permissioned-github`（远程仓库交付）、`agy-customizations`。
- **允许范围**：读取全局状态、更新 `plans/` 与 `docs/` 文档、触发 `tests/harness/runner.js` 回环验证。
- **禁止行为**：未经规划直接篡改业务源码、跳过回环验证直接宣告交付。

### 2. 【ORM 数据建模与存储 Agent (Database & ORM Agent)】
- **核心职责**：依据 `docs/db_schema.md` 编写 `backend/app/models/` 下的 SQLAlchemy 2.0 声明式 ORM 模型、维护 Redis 缓存键结构与初始化种子数据。
- **按需挂载项目 Skills**：`Skill 01: sqlalchemy_orm_with_comment`（`@SKILL.md`）。
- **强制契约**：每个表与每个字段必须 100% 携带清晰的中文 `comment="..."` 注释；确保产品字典双维分类、主库、高值仓、二级库及 6W 全流程日志表外键与索引完备。
- **禁止行为**：手写无注释裸 SQL、执行未授权的 `DROP / TRUNCATE` 高危操作、触碰 `frontend/` 目录。

### 3. 【后端 FastAPI 与 MCP 智能体编排 Agent (Backend & AI Agent)】
- **核心职责**：开发 `backend/app/routers/` 下的 5 套核心 CRUD 接口、封装基于 MCP 协议的业务数据库读写工具与 Chroma RAG 检索工具、使用 LangChain + LangGraph 编排 5 大业务智能体工作流（对接本地 Ollama、云端小米 MiMo 及 Coze）。
- **按需挂载项目 Skills**：`Skill 02: fastapi_restful_crud_router`、`Skill 03: main_to_high_value_split_code`、`Skill 04: patient_and_user_privacy_desensitize`、`Skill 05: workflow_6w_trace_logger`（`@SKILL.md`）。
- **强制契约**：统一返回 `{code, msg, data}`；所有入参出参通过 Pydantic V2 校验；100% 编写函数级中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。
- **禁止行为**：硬编码数据库密码或大模型 API Key、明文暴露患者未脱敏隐私信息。

### 4. 【前端 Vue3 + TS 工作台与打印引擎 Agent (Frontend UI Agent)】
- **核心职责**：在 `frontend/src/` 下开发三级角色工作台、产品字典管理、普通耗材主库与按需分发、高值耗材管理、临床二级库管理、全流程日志时间轴、统计看板、5 类医院标准四联签字单据打印组件及 5 大智能体可视化对话与节点流程图面板。
- **按需挂载全局与项目 Skills（见 `@SKILL.md` 第二、三章）**：
  - *视觉精雕与设计工程*：`emil-design-eng`、`apple-design`、`emil-apple-design`、`prototype`、`pick-ui-library`、`ask-sonner`、`mobile-native`；
  - *动效决策与 60fps 性能*：`animate`、`animation-performance`、`find-animation-opportunities`、`improve-animations`、`review-animations`；
  - *打印与极限数据压测*：`Skill 06: medical_voucher_print_engine`、`break-ui`。
- **强制契约**：全域禁用 Emoji，统一采用 Element Plus 图标或内联矢量 SVG；全面使用 CSS 变量适配亮暗主题；高频操作按钮增加防抖与 Loading 锁；**严禁照搬 `docs/design/*.html` 功能线框图的简易样式，必须按照 `emil-design-eng` 与 `apple-design` 标准打造高质感生产级界面**。
- **禁止行为**：滥用 `any` 跳过 TypeScript 类型检查、硬编码后端接口域名。

### 5. 【质量护栏与 Playwright 回环验证 Agent (QA & Harness Agent)】
- **核心职责**：维护并执行 `tests/harness/runner.js` 与 `tests/e2e/` 自动化测试脚本，驱动持久化无锁浏览器校验 DOM 渲染、拦截 Console Error / PageError，并将带时间戳的实机截图归档至 `tests/screenshots/`。
- **按需挂载全局 Skills**：`break-ui`（极限恶劣医疗数据 UI 压测）、`ego-browser`。
- **禁止行为**：伪造测试通过结果、遗留未关闭的浏览器孤儿进程。

---

## 第二部分：系统内置 5 大医疗物资业务智能体契约（Business LangGraph Agents）

本项目在业务端落地 **5 个独立的智能体工作流**（基于 LangChain + LangGraph 构建 `StateGraph`），每个智能体均通过 **MCP 协议** 同时调用 **本地 Chroma 向量库（RAG）** 与 **本地 MySQL 8.0 业务数据库（ORM 模型）**：

| 智能体编号 | 智能体标识与名称 | 对应服务的人员角色 | 挂载的 MCP 业务库工具 (MySQL) | 挂载的 RAG 知识库工具 (Chroma) | 核心业务产出 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Agent 01** | `dict_inbound_guard_agent`<br>**产品字典智能归类与主库入库审查智能体** | 耗材科管理员<br>设备科管理员 | `mcp_query_product_dict`<br>`mcp_check_supplier_cert` | `rag_search_medical_catalog`<br>（医疗器械分类目录与主库验收规范） | 自动判定产品归口主科室（耗材科/设备科）与普通/高值分类；入库时校验效期与注册证，拦截违规批次 |
| **Agent 02** | `main_stock_dispatch_agent`<br>**主库全部物资智能按需分发与补货调拨智能体** | 耗材科管理员<br>设备科管理员 | `mcp_scan_main_and_sec_stock`<br>`mcp_create_dispatch_order` | `rag_search_dispatch_fefo_rule`<br>（院内二级库补货与 FEFO 近效期先出规则） | 扫描主库总仓与各二级库水位，按 FEFO 原则自动生成《主库向二级库/高值仓按需分发调拨单》 |
| **Agent 03** | `secondary_apply_qa_agent`<br>**临床二级库自然语言申领与耗材规范问答智能体** | 临床二级库人员<br>（各科室护士/技师） | `mcp_check_main_available`<br>`mcp_submit_sec_requisition` | `rag_search_surgery_pack_manual`<br>（临床手术定数包标准与耗材使用说明书） | 解析临床自然语言申领需求，匹配标准耗材包并核验主库余量，自动写入二级库申领单及流转日志 |
| **Agent 04** | `high_value_udi_trace_agent`<br>**高值耗材一物一码与跨用户流转日志全链路溯源智能体**<br>*(支持原生 LangGraph + Coze 双模调用)* | 信息科系统管理员<br>耗材科/设备科管理员 | `mcp_trace_udi_full_logs`<br>`mcp_freeze_problem_batch` | `rag_search_recall_regulation`<br>（医疗器械不良事件监测与召回法规） | 输入 UDI 唯一码或批号，穿透还原“主库入库->按需分发->二级库接收->患者核销”完整人物流转链并冻结问题批次 |
| **Agent 05** | `finance_stat_audit_agent`<br>**多科室耗材统计精算与财务流转合规审计智能体** | 财务科管理员<br>信息科系统管理员 | `mcp_aggregate_dept_cost`<br>`mcp_scan_abnormal_flow_logs` | `rag_search_finance_audit_rule`<br>（医院耗占比考核与财务内控审计制度） | 聚合统计各二级库普通/高值耗材消耗金额，排查异常流转日志，自动输出财务月度成本核算与审计报告 |
| **Agent 06 (离线知识工程)** | `data_cleaning_agent`<br>**Agentic RAG 离线文档清洗与 Graph-RAG 实体关系抽取智能体** | 信息科系统管理员<br>耗材科/设备科管理员 | `mcp_write_knowledge_graph_triples` | `chroma_recursive_chunk_indexer`<br>（递归分块与 Graph-RAG 实体联系文档） | 对上传的原始医疗规范文档执行去噪清洗、表格转译、敏感脱敏、递归分块写入 Chroma，并抽取实体关系图谱三元组 |

---

## 第三部分：五大业务角色与细粒度解耦权限契约（含外部供应商门户）

1. **`sys_admin`（信息科系统管理员）**：全院账号管理、15 大业务模块 × 8 项原子动作（查/增/改/删/二次确认/取消提交/审批/打印）细粒度解耦权限分配、Agentic RAG 与 CRAG 评估调优。
2. **`dept_manager`（主库房管理科室：耗材科/设备科）**：产品字典双树管理、供应商《医疗器械经营许可证》资质准入审核、临床采购计划审批与订单下发、普通耗材与高值耗材主仓管理、请领受理审批（自动触发出库）。
3. **`secondary_user`（临床二级库人员：心血管科/骨科等）**：科室采购计划申请、耗材请领、科室期初数据一次性建账、二级库出入库/发料/调拨/独立盘点、高值接收入库/退货出库（提交即锁死）/一物一码二维码扫码核销。
4. **`finance_auditor`（财务科核算审计人员）**：全院多科室耗材成本核算、高值扫码核销记账审计、盘点盈亏与 6W 异常流转合规审计。
5. **`supplier_user`（外部供应商协同角色）**：首次登录强制上传《医疗器械经营许可证》等经营资质并绑定医院（院方审核通过后解锁接单权限），在线接收采购订单、执行拣货配货、录入批号效期并通过二次确认提交发货（自动同步生成医院端待验收入库单）。
