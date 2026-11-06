# 三甲医院智能医疗物资与全流程耗材供应链管理系统 (Smart Hospital SPD & AI Agent System)

> 基于 FastAPI + Vue 3 + TypeScript 构建的新一代三甲医院精细化医疗物资供应链管理系统（SPD）。系统深度融合 LangGraph 多智能体协同网络、Chroma 向量检索增强生成（Agentic RAG）、Model Context Protocol (MCP) 标准协议、飞书 WebSocket 企业级双向协同及 15×8 细粒度解耦 RBAC 权限中心，实现从供应商准入、采购验收入库、主库按需分发、临床二级库领用、高值 UDI 一物一码扫码核销、不良事件患者全链路召回追访到财务内控精算与 6W 溯源合规审计的端到端数字化闭环。

---

## 目录索引 (Table of Contents)

- [1. 系统核心架构与全景业务拓扑](#1-系统核心架构与全景业务拓扑)
- [2. 核心技术栈与架构选型](#2-核心技术栈与架构选型)
- [3. 十二大核心功能模块深度图文剖析](#3-十二大核心功能模块深度图文剖析)
  - [模块 01：产品字典标准体系与两级分类管理](#模块-01产品字典标准体系与两级分类管理)
  - [模块 02：普通耗材主库全生命周期与按需分发](#模块-02普通耗材主库全生命周期与按需分发)
  - [模块 03：临床科室二级库房与科室物理隔离流转](#模块-03临床科室二级库房与科室物理隔离流转)
  - [模块 04：高值耗材一物一码 (UDI) 与不良事件患者召回追访](#模块-04高值耗材一物一码-udi-与不良事件患者召回追访)
  - [模块 05：采购计划编制、多级审批与全流程下发](#模块-05采购计划编制多级审批与全流程下发)
  - [模块 06：外部供应商协同门户与资质审核拦截](#模块-06外部供应商协同门户与资质审核拦截)
  - [模块 07：医院财务核算精算看板与国家四联单据打印引擎](#模块-07医院财务核算精算看板与国家四联单据打印引擎)
  - [模块 08：6W 医疗物资全流程流转审计台账](#模块-086w-医疗物资全流程流转审计台账)
  - [模块 09：人员管理与 15×8 细粒度解耦 RBAC 权限中心](#模块-09人员管理与-158-细粒度解耦-rbac-权限中心)
  - [模块 10：Agentic RAG 知识库检索与外部 MCP 工具控制中心](#模块-10agentic-rag-知识库检索与外部-mcp-工具控制中心)
  - [模块 11：8 大医疗专业化智能体协同沙箱](#模块-118-大医疗专业化智能体协同沙箱)
  - [模块 12：飞书企业协作机器人双向打通](#模块-12飞书企业协作机器人双向打通)
- [4. 八大医疗业务智能体契约与 MCP / RAG 映射](#4-八大医疗业务智能体契约与-mcp--rag-映射)
- [5. 权限模型与全角色演示账号矩阵](#5-权限模型与全角色演示账号矩阵)
- [6. 本地极速部署与运行指南](#6-本地极速部署与运行指南)
- [7. 自动化测试护栏与工程规范](#7-自动化测试护栏与工程规范)

---

## 1. 系统核心架构与全景业务拓扑

系统遵循现代医院物流供应链（SPD）标准业务规范，打通“供应商 - 主库房 - 临床二级科室 - 患者 - 财务审计”完整链路：

```mermaid
flowchart TD
    subgraph S1["外部供应链协同层"]
        SUP["外部供应商 (Supplier)"] -->|"上传资质证明 / 订单发货"| SUP_PORTAL["供应商协同门户"]
    end

    subgraph S2["院内主库物资调度层"]
        SUP_PORTAL -->|"待验收审核入库"| MAIN_STOCK["主库总仓 (耗材科/设备科)"]
        DICT["产品字典三树工作台"] -->|"基础规格与UDI属性"| MAIN_STOCK
        MAIN_STOCK -->|"FEFO近效期先出 / 按需分发"| DISPATCH["主库向二级库调拨"]
    end

    subgraph S3["临床科室二级库消耗层"]
        DISPATCH -->|"科室接收入库"| SEC_STOCK["临床科室二级库 (心内科/骨科/ICU)"]
        SEC_STOCK -->|"扫码核销 / 计费消耗"| PATIENT["患者使用 (一物一码UDI)"]
        PATIENT -->|"不良事件监测"| RECALL["患者全链路召回与随访中枢"]
    end

    subgraph S4["财务核算与合规监管层"]
        PATIENT -->|"消耗流水沉淀"| FINANCE["财务精算中心 (月度成本/百元耗占比)"]
        MAIN_STOCK -->|"流转痕迹"| TRACE_6W["6W全流程审计台账 (Who/When/Where/What/Why/Which)"]
        SEC_STOCK -->|"流转痕迹"| TRACE_6W
        FINANCE -->|"防伪水印/动态条码"| PRINT_ENG["国家标准四联签字单据打印引擎"]
    end

    subgraph S5["AI 智能体编排与生态协同层"]
        AGENTS["8大医疗专业化智能体工作流 (LangGraph)"]
        RAG["Chroma 向量知识库 (Agentic RAG)"]
        MCP["MCP 标准协议工具中心 (MySQL / 外部服务)"]
        FEISHU["飞书机器人 (WebSocket双向免穿透)"]

        AGENTS <-->|"语义检索与规范对齐"| RAG
        AGENTS <-->|"业务库安全执行"| MCP
        FEISHU <-->|"自然语言流转与审批联动"| AGENTS
    end

    MAIN_STOCK <--> AGENTS
    SEC_STOCK <--> AGENTS
    FINANCE <--> AGENTS
```

---

## 2. 核心技术栈与架构选型

| 层次维度 | 核心选型 | 版本/规范 | 架构特性与工程考量 |
| :--- | :--- | :--- | :--- |
| **前端应用** | Vue 3 + TypeScript + Vite | Vue 3.5+, TS 5.6+ | Composition API, `<script setup>` 组合式语法，严格类型校验，零 `any` 污染 |
| **UI 组件库** | Element Plus + 矢量 SVG | 2.8+ | 沉浸式毛玻璃卡片设计，全域禁用 Emoji，纯矢量图标自适应父级文本与主题色 |
| **样式与主题** | CSS Variables + PostCSS | 原生自适应 | 全面解耦浅色/深色主题，色彩由系统设计变量统一驱动，严禁绝对值硬编码 |
| **后端服务** | Python FastAPI + Uvicorn | Python 3.10+, FastAPI 0.115+ | 异步非阻塞高并发架构，自动生成 OpenAPI / Swagger 规范契约 |
| **数据持久化** | MySQL 8.0 + SQLAlchemy | 2.0 声明式 ORM | 字段级 100% 中文注释，外键索引完整约束，严格保证事务一致性 |
| **智能体编排** | LangChain + LangGraph | 最新稳定版 | 基于 `StateGraph` 构建确定性医疗状态机，支持流式气泡对话与状态分支流转 |
| **向量检索库** | Chroma Vector DB | 0.5+ | 医疗器械规范分块向量化检索，支持专家纠偏样本与人机反馈自演化 |
| **协议标准** | Model Context Protocol (MCP) | JSON-RPC 2.0 标准 | 跨进程/跨系统统一工具调用，支持动态鉴权、入参白名单校验与结构化返回 |
| **企业协作** | 飞书开放平台 SDK | WebSocket 长连接 | 免公网域名与 NAT 穿透，支持群聊动态 `@` 唤醒、私聊问答与业务审批推送 |
| **质量防护** | Playwright + 自研测试护栏 | 1.48+ | 真实 Chromium 环境端到端 E2E 验证，拦截 Console Error，自动保存实机截图 |

---

## 3. 十二大核心功能模块深度图文剖析

### 模块 01：产品字典标准体系与两级分类管理
- **核心功能**：建立全院医疗物资唯一商品档案，支持按“管理科室（耗材科/设备科）”与“价值属性（普通耗材/高值耗材）”双维度分类管理；集成规格型号树、医保医用耗材统一编码匹配与国家医疗器械注册证有效期预警。
- **业务价值**：杜绝一物多码与规格混乱，从源头保障医疗物资入库合法合规。

![产品字典规格与分类体系](tests/screenshots/subview_01_dict_specs.png)
*图 1-1：产品字典两级多维树形筛选与规格明细视图*

![产品字典三树工作台](tests/screenshots/03_product_dict_three_tree_workspace.png)
*图 1-2：产品字典三树联动管理、医保耗材代码与注册证全生命周期工作台*

---

### 模块 02：普通耗材主库全生命周期与按需分发
- **核心功能**：实现耗材科普通物资总仓的采购验收入库、批次跟踪、效期临期色块预警、动态安全水位监控；支持依据临床科室请领单执行先进先出（FEFO）智能拣货与按需调拨分发。
- **业务价值**：防止耗材积压与近效期报废，提升院内物资周转率。

![普通耗材主库库存穿透视图](tests/screenshots/02_general_material_all_stock_penetrated.png)
*图 2-1：普通耗材主库全库存穿透、批号效期分布与库位监控*

![普通耗材请领审批与分发工作台](tests/screenshots/03_general_requisition_approval_workbench.png)
*图 2-2：临床科室请领审批、批次分配与按需分发出库工作台*

---

### 模块 03：临床科室二级库房与科室物理隔离流转
- **核心功能**：实现心血管内科、骨科、重症医学科等临床科室二级库的科室物理级数据隔离；支持科室期初建账、主库分发接收入库、科室内部调拨、损耗登记与自主盘点对账。
- **业务价值**：责任明确到科室护士长与耗材管理员，解决临床“只领不消、账实不符”的管理顽疾。

![二级科室独立切换与物理隔离](tests/screenshots/04_secondary_dept_switching_isolation.png)
*图 3-1：二级科室专属库房动态无缝切换与库存台账物理隔离*

![科室间物资调拨与双向审批](tests/screenshots/05_transfer_auto_order_and_two_way_audit.png)
*图 3-2：临床二级库调拨单自动生成、调出方出库与调入方接收双向审批*

---

### 模块 04：高值耗材一物一码 (UDI) 与不良事件患者召回追访
- **核心功能**：对心脏支架、人工关节、起搏器等高值植入介入耗材实施国家标准 UDI 唯一码赋码；支持手术室扫码核销、患者信息脱敏绑定；专设【不良事件召回患者追访中枢】，输入召回批号即刻逆向穿透患者完整用药记录，并联动打印国家卫健委四联召回报告单。
- **业务价值**：满足国家高值耗材“一物一码、全程可溯、召回定人”的最高合规监管要求。

![高值耗材一物一码库存穿透](tests/screenshots/06_high_value_all_stock_penetrated.png)
*图 4-1：高值耗材 UDI 唯一码状态机追踪、灭菌批次与定点存放监控*

![不良事件召回患者全链路追访中枢](tests/screenshots/2026-11-06_19-50-00_recall_patient_trace_ledger.png)
*图 4-2：召回批次逆向穿透、患者隐私脱敏追访与国家标准四联召回报告打印单*

---

### 模块 05：采购计划编制、多级审批与全流程下发
- **核心功能**：汇总临床科室补货需求与主库安全水位差额，自动生成采购建议计划；支持耗材科管理员复核、分管院长多级审批流；审批通过后自动解耦下发为面向供应商的采购采购单。
- **业务价值**：采购全流程留痕，防范廉洁风险与盲目超量采购。

![采购计划编制与明细录入](tests/screenshots/01_procurement_bill_entry_dialog.png)
*图 5-1：采购计划编制对话框、耗材自动带出与金额实时校验*

![院方采购计划审核与订单下发](tests/screenshots/2026-11-06_17-05-00_hospital_audit_approve_unlocked.png)
*图 5-2：院方多级审核流批注驳回/通过，审核通过后自动解锁供应商接单权限*

---

### 模块 06：外部供应商协同门户与资质审核拦截
- **核心功能**：为外部医疗器械供应商提供专属外部协同门户。首次登录强制上传《医疗器械经营许可证》等经营资质并提交院方审核；审核通过前严格锁定接单权限；审核通过后方可在途接收订单、录入批号效期并发货。
- **业务价值**：将院内质量控制关口前移至供应链源头，防止无证或过期经营企业供货。

![供应商资质证书上传界面](tests/screenshots/2026-11-06_17-05-00_supplier_portal_upload_modal.png)
*图 6-1：外部供应商资质证明材料上传、许可证号登记与资质合规性声明*

![供应商在线配货发货成功通知](tests/screenshots/03_supplier_portal_ship_success.png)
*图 6-2：供应商确认订单配货、登记批号效期并提交发货，同步生成院内待验收单*

---

### 模块 07：医院财务核算精算看板与国家四联单据打印引擎
- **核心功能**：集成财务精算多维 BI 看板，实时统计各二级科室耗占比、普通/高值物资支出趋势及库存资金沉淀；搭载自研高保真单据打印引擎，支持采购入库单、领料出库单、高值植入单、盘点对账单及召回追访单 5 类国家卫健委标准四联签字单据打印，自带防伪水印与动态条形码。
- **业务价值**：为医院经济运行分析提供精确数据支撑，满足三甲评审与医保飞行检查对纸质存根的严苛要求。

![医院财务精算多维看板](tests/screenshots/2026-11-06_13-55-00_finance_bi_charts.png)
*图 7-1：财务科全院耗占比趋势、科室消耗支出对比与物资分类占比看板*

![国家标准四联签字单据打印预览](tests/screenshots/05_finance_voucher_print_preview_with_details.png)
*图 7-2：医疗物资四联防伪单据打印引擎（存根联/记账联/保管联/使用联）*

---

### 模块 08：6W 医疗物资全流程流转审计台账
- **核心功能**：系统底层拦截所有物资状态流转事件，结构化沉淀 6W 要素审计日志（Who 操作人、When 操作时间、Where 物理库位、What 物资与批号、Why 业务原因、Which 单据关联凭据）；提供跨时间段、跨科室、跨物资的高级检索与异常行为筛查。
- **业务价值**：全生命周期证据链不可篡改，实现物资全链路阳光透明运行。

![6W全流程医疗物资流转审计台账](tests/screenshots/06_hospital_workflow_trace_ledger.png)
*图 8-1：6W 医疗物资流转全生命周期不可篡改审计台账*

---

### 模块 09：人员管理与 15×8 细粒度解耦 RBAC 权限中心
- **核心功能**：构建 15 大业务模块 × 8 项原子操作（查看/新增/修改/删除/二次确认/取消提交/审批/打印）权限控制矩阵；支持单用户跨多库房授权与顶部全局库房动态无缝切换；前端路由、按钮级指令与后端 API 鉴权中间件三层联动校验。
- **业务价值**：实现细粒度职责解耦与最小权限原则，保障三甲医疗数据安全可控。

![多库房授权与数据中心](tests/screenshots/2026-11-06_15-30-00_multi_warehouse_perm_center.png)
*图 9-1：用户账号多库房归属授权、角色绑定与激活状态控制中心*

![15x8 细粒度 RBAC 权限配置矩阵](tests/screenshots/2026-11-04_rbac_matrix_persisted.png)
*图 9-2：15 大业务模块与 8 大原子操作指令级权限解耦配置面板*

---

### 模块 10：Agentic RAG 知识库检索与外部 MCP 工具控制中心
- **核心功能**：基于本地 Chroma 向量库沉淀《国家医疗器械监督管理条例》、《医疗物资编码规则》等专业知识库；支持文档切片、混合语义检索与向量相似度重排；集成标准 Model Context Protocol (MCP) 控制中心，实现业务工具安全暴露、参数验证与调用耗时监控。
- **业务价值**：为上层业务大模型提供可溯源的真实知识底座，杜绝大模型幻觉。

![Agentic RAG 知识库检索控制台](tests/screenshots/01_rag_console_chroma_ready.png)
*图 10-1：Chroma 向量知识库状态监控、医疗法规切片检索与向量相似度评分*

![MCP 外部工具服务控制中心](tests/screenshots/2026-11-06_18-55-00_mcp_control_center.png)
*图 10-2：标准 MCP 外部工具注册、连通性心跳检测与参数模式契约控制台*

---

### 模块 11：8 大医疗专业化智能体协同沙箱
- **核心功能**：提供 GroupChat 多智能体协同对话工作台，支持智能体意图识别、自主调用 MCP 工具查询业务库；提供【知识自演化引擎】，支持临床专家对智能体回答执行“采纳建议”或“专家纠偏”，纠偏样本毫秒级写入本地 Chroma 向量库形成闭环自迭代。
- **业务价值**：推动医疗业务从“被动检索”向“主动建议、持续自进化”的智能化跃迁。

![8大医疗智能体协同沙箱总览](tests/screenshots/2026-11-05_21-25-00_8_agents_sandbox_overview.png)
*图 11-1：8 大业务智能体协同沙箱架构总览与状态机拓扑*

![GroupChat 多智能体流式会话气泡](tests/screenshots/16-10-00_groupchat_stream_bubbles.png)
*图 11-2：LangGraph 智能体群聊流式推演、中间思考链与协同解答过程*

![智能体自主调用 MCP 工具卡片展开](tests/screenshots/2026-11-06_18-55-00_agent_mcp_tool_call_expanded.png)
*图 11-3：智能体在推理过程中自主调度 MCP 数据库工具与参数透明展示*

![智能体专家反馈与知识自演化引擎](tests/screenshots/2026-11-06_19-50-00_agent_human_feedback_evolution.png)
*图 11-4：人机协同知识自演化引擎（专家纠偏即时入库与正向强化采纳）*

---

### 模块 12：飞书企业协作机器人双向打通
- **核心功能**：采用飞书开放平台官方 WebSocket 长连接机制，无需公网固定 IP 与域名 NAT 穿透；支持在医院飞书群中 `@智能体` 或私聊对话，机器人自动解析意图并调用院内系统数据完成库存查询、审批进度催办与临期物资警报推送。
- **业务价值**：打通医院移动端办公生态，实现业务与即时通讯软件的无缝融合。

![飞书 WebSocket 长连接成功连接](tests/screenshots/2026-11-06_14-25-00_feishu_ws_connected_and_saved.png)
*图 12-1：飞书 WebSocket 企业网关免穿透双向长连接配置与在线状态*

![飞书群聊多轮对话与意图识别](tests/screenshots/2026-11-05_23-50-00_feishu_dynamic_intent_and_at.png)
*图 12-2：飞书群聊 `@机器人` 动态意图识别、数据查询卡片与即时回传*

---

## 4. 八大医疗业务智能体契约与 MCP / RAG 映射

系统内置基于 LangGraph 编排的 8 大专用智能体，每个智能体均绑定专属的 MCP 数据库工具与 Chroma 知识库检索能力：

| 智能体标识与名称 | 核心职责 | 挂载 MCP 业务数据库工具 | 挂载 RAG 知识库检索工具 |
| :--- | :--- | :--- | :--- |
| **Agent 01: `dict_inbound_guard_agent`**<br>字典归类与入库审查智能体 | 研判耗材归口科室与分类，校验生产资质与注册证效期，拦截违规物资入库 | `mcp_query_product_dict`<br>`mcp_check_supplier_cert` | `rag_search_medical_catalog`<br>（医疗器械分类与入库标准） |
| **Agent 02: `main_stock_dispatch_agent`**<br>主库物资分发与补货智能体 | 监控主库与各二级库水位，依据 FEFO 近效期先出原则自动制定调拨分发单 | `mcp_scan_main_and_sec_stock`<br>`mcp_create_dispatch_order` | `rag_search_dispatch_fefo_rule`<br>（院内物资周转与补货规则） |
| **Agent 03: `secondary_apply_qa_agent`**<br>二级库申领与耗材规范智能体 | 解析护士自然语言申领诉求，匹配定数包并校验库存，生成请领单 | `mcp_check_main_available`<br>`mcp_submit_sec_requisition` | `rag_search_surgery_pack_manual`<br>（手术室定数包耗材配置规范） |
| **Agent 04: `high_value_udi_trace_agent`**<br>高值耗材一物一码溯源智能体 | 追踪 UDI 全生命周期流转轨迹，执行召回溯源并一键锁定问题批次 | `mcp_trace_udi_full_logs`<br>`mcp_freeze_problem_batch` | `rag_search_recall_regulation`<br>（医疗器械召回与不良事件监测） |
| **Agent 05: `finance_stat_audit_agent`**<br>财务统计精算与合规审计智能体 | 聚合科室消耗成本，核算百元医疗收入耗材占比，排查流转异常 | `mcp_aggregate_dept_cost`<br>`mcp_scan_abnormal_flow_logs` | `rag_search_finance_audit_rule`<br>（公立医院财务内控审计制度） |
| **Agent 06: `data_cleaning_agent`**<br>离线文档清洗与图谱构建智能体 | 医疗规范文档去噪清洗、敏感数据脱敏、递归切片入库与实体关系提取 | `mcp_write_knowledge_graph` | `chroma_recursive_chunk_indexer`<br>（多源异构文档解析与向量化） |
| **Agent 07: `feishu_collaborator_agent`**<br>飞书多模态协作与意图分发智能体 | 接收飞书 WebSocket 消息，路由至专业智能体并组装结构化卡片回传 | `mcp_post_feishu_card_message` | `rag_search_general_faq`<br>（医院全域常见问题知识库） |
| **Agent 08: `human_feedback_evolution_agent`**<br>人机协同与知识自演化引擎 | 接收专家点赞/采纳/纠偏输入，生成高质量微调纠偏对，沉淀为置顶知识 | `mcp_persist_expert_correction` | `chroma_feedback_self_evolving`<br>（专家纠偏知识向量增量库） |

---

## 5. 权限模型与全角色演示账号矩阵

系统预置全套三甲医院业务角色，初始密码均为 `123456`，可在登录页直接切换体验：

| 登录账号 | 所属角色 | 职能范围 | 可操作模块与数据权限 |
| :--- | :--- | :--- | :--- |
| `sysadmin` | **信息科系统管理员** | 掌控全院系统底层配置与安全审计 | 15 大模块全权限、15×8 RBAC 矩阵配置、多库房授权、系统监控 |
| `consumable_mgr` | **耗材科管理员 (主库房)** | 普通医用耗材全流程入库与调度 | 产品字典管理、普通耗材主库、请领审批与出库分发、供应商订单下发 |
| `equipment_mgr` | **设备科管理员 (主库房)** | 医用器械与高值耗材入库核验 | 高值耗材主库管理、器械入库验收、UDI 一物一码赋码管理、召回中枢 |
| `nurse_cardiology` | **心血管内科护士长 (二级库)** | 心内科专科二级库房消耗与维护 | 心内科二级库房、科室采购请领、心血管支架扫码核销、科室自主盘点 |
| `nurse_orthopedics` | **骨科二级库管理员 (二级库)** | 骨科植入耗材消耗与维护 | 骨科二级库房、关节脊柱类耗材扫码核销、科室调拨申领 |
| `finance_user` | **财务科审计核算员** | 医院财务内控合规与经济运营分析 | 财务核算精算看板、消耗成本对账、四联单据打印、6W 溯源合规审计 |
| `supplier_01` | **国药控股器械供应商 (外部)** | 外部供应商准入对接与订单协同 | 供应商协同门户、企业资质上传、待发货订单处理、发货批次录入 |

---

## 6. 本地极速部署与运行指南

### 环境依赖要求
- **Node.js**: >= 18.0.0 (推荐 Node 20 LTS)
- **Python**: >= 3.10
- **MySQL**: >= 8.0 (字符集推荐 `utf8mb4`)
- **Git**: 推荐 Git 2.30+

### 第一步：克隆代码仓库
```bash
git clone https://github.com/your-username/hospital-spd-ai-agent.git
cd hospital-spd-ai-agent
```

### 第二步：数据库初始化
1. 在 MySQL 8.0 中创建系统专用数据库：
```sql
CREATE DATABASE hospital_spd DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
2. 修改后端配置文件中的数据库连接字符串（`backend/app/core/config.py` 或环境变量）：
```ini
DATABASE_URL=mysql+pymysql://root:your_password@127.0.0.1:3306/hospital_spd
```

### 第三步：后端服务安装与启动 (FastAPI)
```bash
# 1. 切换至后端目录
cd backend

# 2. 创建并激活 Python 虚拟环境 (Windows)
python -m venv venv
.\venv\Scripts\activate

# 3. 安装后端核心依赖
pip install -r requirements.txt

# 4. 运行数据库迁移与种子数据填充 (自动注入初始字典与全角色账号)
python init_db.py

# 5. 启动 FastAPI 后端服务 (端口 8000)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*后端 API 契约文档（Swagger UI）：访问 http://127.0.0.1:8000/docs*

### 第四步：前端工作台安装与启动 (Vue 3 + Vite)
```bash
# 1. 打开新终端，进入前端目录
cd frontend

# 2. 安装前端依赖
npm install

# 3. 启动 Vite 本地开发服务器 (端口 5173)
npm run dev
```
*前端工作台访问地址：浏览器打开 http://127.0.0.1:5173*

---

## 7. 自动化测试护栏与工程规范

本项目在持续集成中落地基于 **Playwright** 的真实浏览器自动化回环验证护栏：

```bash
# 运行端到端 E2E 自动化回归测试脚本
node tests/harness/runner.js
```

### 工程质量底线保证
1. **0 Console Error**：页面渲染与交互全过程无任何控制台未捕获异常。
2. **零硬编码样式**：全域采用 CSS 变量，确保浅色与深色模式视觉层级严谨平滑。
3. **全域禁用 Emoji**：所有界面图标、按钮及提示信息统一采用 Element Plus 原生图标或高精矢量 SVG。
4. **函数级中文注释**：所有核心模型与业务接口 100% 具备规范入参、返回值与异常说明。

---

## 开源许可证 (License)

本项目遵循 [MIT License](LICENSE) 开源协议。
