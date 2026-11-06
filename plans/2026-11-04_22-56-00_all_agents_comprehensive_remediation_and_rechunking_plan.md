# 1~5号业务智能体闭环修复与6号智能体全库巡检重切实施计划书

- 计划文档路径：`plans/2026-11-04_22-56-00_all_agents_comprehensive_remediation_and_rechunking_plan.md`
- 记录时间戳：`2026-11-04 22:56:00`
- 关联诉求：
  1. 彻底解决 1~5 号智能体“能输出完美建议但未在业务数据库物理写入单据”的问题，实现调拨单、请领单、批次冻结与动态财务核算的物理闭环；
  2. 修复智能体品名写死、意图关键词匹配、黑板数据静态化等问题；
  3. 为 1~5 号智能体落实细粒度 RBAC 权限硬拦截（科室隔离、角色鉴权、患者隐私脱敏）；
  4. 为 6 号智能体落地“全库文档健康巡检（检测未切分/切分异常文档）与自动智能重新切片（Auto Re-chunking）”功能，实现前端图形化与沙箱自然语言双模联动。

---

## 一、核心评估指标

- **方案把握度**：98%（所有 ORM 模型 `SpdDistributionOrder`、`SpdRequisitionOrder`、`SpdHighValueItem`、`SpdWorkflowLog` 均已完备定义，物理读写与状态流转契约明确，技术死角为 0）。
- **存量功能与三方体验影响**：
  - **用户体验 (UX)**：操作形成真正生产力闭环，用户在沙箱或工作台触发调拨/申领/冻结后，切换到对应仓库页面能真实查看到新生成的单据与状态变动；知识库顶部新增体检状态条，直观可视；
  - **开发者体验 (DX)**：1~6 号智能体全部对齐《AGENTS.md》契约，函数 100% 具备四要素中文注释，业务层逻辑高内聚低耦合；
  - **AI 代理体验 (AX)**：智能体工具链具备真实的物理读写输入输出，杜绝虚假返回，大幅提升多智能体协作与 Trace 追踪信噪比；
  - **零破坏性与向后兼容**：严格遵循开闭原则，不破坏现有存量 API 与页面已有数据。

---

## 二、目标变更范围

```markdown
[变更计划范围]
- 前端目标文件：
  - frontend/src/api/ragAgentHubApi.ts (新增巡检与重新切片 API 契约)
  - frontend/src/views/RagAgentHubView.vue (知识库顶部装配健康巡检条幅与单文档重新切片弹窗)
  - frontend/src/components/AgentChatWidget.vue (沙箱快捷问题增加巡检与重切预设)
- 后端目标文件：
  - backend/app/services/agents/agent_1_plan_execute.py (动态品名解析、真实资质查验与权限拦截)
  - backend/app/services/agents/agent_2_router_skill.py (真实写入 SpdDistributionOrder 调拨单与仓库品类权限隔离)
  - backend/app/services/agents/agent_3_langgraph.py (动态科室绑定、确认审批后物理写入 SpdRequisitionOrder 请领单)
  - backend/app/services/agents/agent_4_react.py (物理调用 mcp_freeze_problem_batch 冻结高值条目、穿透查询 6W 日志与患者隐私脱敏)
  - backend/app/services/agents/agent_5_blackboard.py (从数据库动态 SQL 统计成本金额、增加财务角色强校验)
  - backend/app/services/agents/agent_6_supervisor.py (实现全库未切片异常巡检与自动重新切片服务)
  - backend/app/routers/rag_agent_hub_router.py (暴露巡检与重切 RESTful 路由)
- 测试与截图目标文件：
  - tests/e2e/test_all_agents_closed_loop_and_rechunk.js (Playwright 回环自动化脚本)
  - tests/screenshots/2026-11-04_all_agents_closed_loop_verified.png (实机证据截图)
```

---

## 三、各智能体详细技术规范与整改细节

### 1. Agent 01 (Plan & Execute): 产品字典归类与入库审查
- **动态品名与规格提取**：利用大模型结构化抽取用户指令中的具体品规名（如“骨水泥输送枪”），不再固定赋值为“智能归类心血管支架”；
- **真实供应商资质审查 (`mcp_check_supplier_cert`)**：查询 `spd_supplier_credential` 表，校验供应商是否有有效《医疗器械经营许可证》且未过期，未通过则拦截入库并提示风险；
- **细粒度 RBAC 权限拦截**：
  - 检查 `operator_role`，若为 `secondary_user` 或 `supplier_user`，抛出权限拦截错误；
  - 若品规单价超过 10,000 元，自动设置 `audit_status = 'NEEDS_DIRECTOR_REVIEW'`。

### 2. Agent 02 (Router + Skill): 主库智能分发调拨
- **物理单据真实落盘 (`mcp_create_dispatch_order`)**：
  - 当命中 `skill_fefo_dispatch` 且完成库存扫描后，在 `spd_distribution_order` 表中物理创建一条状态为 `PENDING_PICKING`（待拣货）的调拨单据，单号格式 `DISP-YYYYMMDD-XXXX`，明确记录出库仓库（耗材主库/设备高值仓）与目标科室二级库；
- **品类与仓库责任隔离**：耗材科账号只能调拨普通耗材，设备科账号只能调拨高值耗材。

### 3. Agent 03 (LangGraph + HITL): 临床二级库自然语言申领
- **物理单据真实落盘 (`mcp_submit_sec_requisition`)**：
  - 当用户在人机回环节点点击【确认提交申领单】（`resume_action == "CONFIRM"`）后，系统调用数据库事务向 `spd_requisition_order` 表插入物理记录，单号 `REQ-YYYYMMDD-XXXX`，状态置为 `SUBMITTED`；
- **病区科室动态绑定与行级隔离**：
  - 从 `user_ctx` 中提取当前护士登录账号绑定的实际病区（如骨科/心内科），禁止跨病区代领物资。

### 4. Agent 04 (ReAct): 高值耗材一物一码全链路溯源
- **真实物理批次冻结 (`mcp_freeze_problem_batch`)**：
  - 若指令中包含“冻结”或召回命中，真实执行 `db.query(SpdHighValueItem).filter(...).update({"status": "FROZEN"})`，彻底阻断问题耗材被手术核销；
- **穿透真实 6W 日志流**：
  - 检索 `spd_workflow_log` 表中该 UDI 的真实轨迹记录（入库、分发、接收、核销人与时间）；
- **患者个人隐私脱敏 (Skill 04)**：
  - 若非系统管理员，患者姓名进行脱敏掩码（如 `张*丰`），隐藏身份证与病历号前缀。

### 5. Agent 05 (Blackboard): 多科室耗材财务精算审计
- **真实动态 SQL 聚合统计**：
  - 成本精算专家：执行 `SELECT SUM(total_amount), main_dept_code FROM spd_main_inventory ...` 真实汇总耗材出库消耗额；
  - 盘点与损耗专家：从 `spd_high_value_item` 统计核销金额与报损记录；
- **财务专属角色强校验**：
  - 仅授权 `finance_auditor` 与 `sys_admin` 角色访问，普通临床护士与供应商调用时抛出 403 权限拒绝。

### 6. Agent 06 (Multi-Agent + Modular RAG): 离线文档巡检与智能重新切片
- **异常文档巡检引擎 (`inspect_unindexed_documents`)**：
  - 扫描全库 `spd_rag_document`，标记未切分（`chunk_count == 0`）或切片过大/过小异常的文档；
- **自动重新切片与策略决策 (`auto_rechunk_document`)**：
  - 提取文档正文，由 Sub-Agent 6A 重新进行特征雷达分析并确定最佳策略；
  - 在数据库物理事务内删除旧切片，重新切片并写入 `spd_rag_chunk`，更新切片数量与就绪状态；
- **双模联动前端呈现**：
  - 知识库界面顶部增加【知识库健康体检状态横幅】与【一键巡检重切】按钮；
  - 智能体 6 号挂载对应 MCP 工具，支持对话框自然语言调度。

---

## 四、原子级实施清单与执行进度台账

- 最新执行时间戳：2026-11-04 23:55:00
- 整体进度：12 / 12 (100% 全部完成，回环验证通过)

1. [已完成] `[backend/app/services/agents/agent_1_plan_execute.py]`：实现动态品名规格抽取、真实供应商资质查验、细粒度 RBAC 角色鉴权与高价值复核标记。
2. [已完成] `[backend/app/services/agents/agent_2_router_skill.py]`：实现真实写入 `SpdDistributionOrder` 物理调拨单与品类仓库隔离校验。
3. [已完成] `[backend/app/services/agents/agent_3_langgraph.py]`：实现动态科室绑定、HITL 人机回环 4 节点流程中断挂起与批示确认后物理写入 `SpdRequisitionOrder` 请领单。
4. [已完成] `[backend/app/services/agents/agent_4_react.py]`：实现物理调用 `mcp_freeze_problem_batch` 冻结高值条目、穿透物理 6W 日志表与患者隐私脱敏。
5. [已完成] `[backend/app/services/agents/agent_5_blackboard.py]`：实现真实 SQL 聚合统计各科室耗材消耗与财务角色防越权鉴权。
6. [已完成] `[backend/app/services/agents/agent_6_supervisor.py]`：实现全库异常切片巡检与自动重新切片（Auto Re-chunking）服务。
7. [已完成] `[backend/app/routers/rag_agent_hub_router.py]`：暴露知识库健康巡检与重新切片 RESTful 接口及审批参数透传。
8. [已完成] `[frontend/src/api/ragAgentHubApi.ts]`：补充巡检与重切 API 契约声明。
9. [已完成] `[frontend/src/views/RagAgentHubView.vue]`：在知识库顶部增加健康体检状态横幅、一键巡检重切按钮及单文档重切弹窗。
10. [已完成] `[frontend/src/components/AgentChatWidget.vue]`：实现 LangGraph 4 步流程图、人工批示意见输入、同意/驳回物理回环与预设巡检药丸。
11. [已完成] `[编译与重启]`：执行 `npm run build` 确保 0 报错，重启 Uvicorn 8000。
12. [已完成] `[Playwright 回环验证与截图]`：运行端到端自动化验证脚本，检验 1~5 号物理单据落盘、RBAC 权限拦截、6 号智能体一键巡检重切功能，截取实机证据图片归档至 `tests/screenshots/`。
