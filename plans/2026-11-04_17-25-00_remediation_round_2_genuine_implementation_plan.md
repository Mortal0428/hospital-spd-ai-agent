# 医院医疗物资系统 —— 第二轮缺陷整改与真实性加固研发实施计划书

[变更计划]
- 计划文档路径：plans/2026-11-04_17-25-00_remediation_round_2_genuine_implementation_plan.md
- 记录时间戳：2026-11-04 17:25:00
- 前端目标文件：
  1. `frontend/src/views/HospitalProcurementView.vue` —— 修复 `digitUppercase` 函数对 `jiao === 0 && fen > 0` 场景的“零”缺失问题，确保 `1000000.05` 精确转换为 `壹佰万元零伍分`，`100.05` 转换为 `壹佰元零伍分`。
  2. `frontend/src/components/PrintVoucherDialog.vue` —— 同步修复 `digitUppercase` 函数并补齐四要素文档注释，去除硬编码前缀使输出纯净对齐。
- 后端目标文件：
  1. `backend/app/services/six_agents_orchestrator.py` —— 彻底根治 Facade 假实现：
     - Agent 1 (`PlanAndExecuteDictAgent`): `mutate_db` 执行真实 SQLAlchemy ORM 写入 `SpdProductDict` 并 commit 入库；
     - Agent 3 (`LangGraphSecondaryAgent`): 补齐持久化 `SpdAgentExecutionTrace` 记录并 commit；
     - Agent 4 (`ReActHighValueTraceAgent`): 穿透真实查询 `SpdHighValueLifecycleOrder` 与 `SpdWorkflowLog`，提取真实状态、操作人和时间戳；
     - Agent 5 (`BlackboardFinanceAuditAgent`): 真实查询 `SpdSecondaryInventory`, `SpdMainInventory`, `SpdStocktakeAndTransferOrder`, `SpdInboundAndOutboundOrder` 进行动态聚合运算。
  2. `backend/app/services/rag_modular_engine.py` —— 修复余弦相似度非单调数学缺陷，采用统一线性归一化公式；重构 `PreRetrievalJudgeSubAgent.evaluate` 依据医学关键词、语义长度与模糊词惩罚输出真实动态评分；加固 `TableAwareChunker` 对双行无虚线表格的解析与自动降级；为 7 大切片算子 100% 补齐中文四要素注释。
  3. `backend/app/routers/rag_agent_hub_router.py` —— 在 `RagConfigUpdateRequest` 增加数值上下限范围约束（如 `top_k_retrieval` 1~100, `max_rewrite_loops` 1~5, `rewrite_threshold` 0.0~1.0），防御 MySQL 语法崩溃；为 `check_connectivity` 接口补齐四要素注释。
- 测试目标：
  1. `tests/test_challenger_2_empirical.py` —— 验证并发 6 智能体、LangSmith Trace 覆盖度、中文大写金额计算及采供发货至入库闭环；
  2. `tests/verify_rag_remediation.py` —— 验证稠密余弦单调性、BM25 分词打分、动态改写与管道算子。

---

## 核心评估指标

1. **可行性与把握度评估**：**把握度：99%**
   - 依赖的数据库模型（`SpdProductDict`, `SpdWorkflowLog`, `SpdHighValueLifecycleOrder`, `SpdSecondaryInventory`, `SpdMainInventory`, `SpdAgentExecutionTrace`）均已在 MySQL 8.0 物理就绪，字段与索引完备；
   - 算法公式经过严格离线数学与 Node 原生推导测试，边界条件已完全闭合；
   - 风险控制：所有写库操作均带异常回滚（`db.rollback()`）与优雅降级兜底，不阻断业务调用。

2. **存量功能与三方体验（UX / DX / AX）影响分析**：
   - **UX（用户体验）**：采购计划录入台与四联随货同行单中文大写金额严格符合中国人民银行规范，彻底根除漏“零”缺陷；
   - **DX（开发者体验）**：所有切片算子与接口补全中文四要素注释（`@param`, `@returns`, `@route`, `@throws`），彻底消除静态字符串 Mock，保持代码工业级可读性与健壮性；
   - **AX（AI 代理体验）**：Agent 1、3、4、5 均有真实数据库状态和 Trace 轨迹，便于跨轮次审计与链路追踪。

3. **自动化回环测试与验证方案**：
   - 针对余弦得分公式单调性进行数值断言（-1.0 -> 0.0, 0.0 -> 0.5, 0.01 -> 0.505, 1.0 -> 1.0）；
   - 针对无虚线双行表格调用 `TableAwareChunker.chunk()` 断言切片数大于 0；
   - 针对配置更新接口提交负数 `top_k_retrieval` 断言触发 Pydantic 422 验证异常而非 MySQL 1064；
   - 针对 `digitUppercase(1000000.05)` 与 `100.05` 执行 Node 原生断言验证；
   - 针对前端执行 `cd frontend; npm run build` 确保 0 报错；
   - 运行 `python tests/verify_rag_remediation.py` 与 `python tests/test_challenger_2_empirical.py` 确保 100% 通过。

---

## 原子实施清单

1. [backend/] 修改 `backend/app/services/six_agents_orchestrator.py`：
   - Agent 1: 在 `mutate_db` 实例化并提交真实的 `SpdProductDict` 记录；
   - Agent 3: 在 `run_step` 结尾实例化 `SpdAgentExecutionTrace` 并调用 `db.add` 与 `db.commit`；
   - Agent 4: 在 `trace_udi_lifecycle` 真实查询 `SpdHighValueLifecycleOrder` 与 `SpdWorkflowLog` 并提取实机数据；
   - Agent 5: 在 `audit_finance_ledger` 真实聚合 `SpdSecondaryInventory` 与 `SpdMainInventory` 数据。
2. [backend/] 修改 `backend/app/services/rag_modular_engine.py`：
   - 修复 `HybridRetriever.search_dense` 的余弦得分计算公式；
   - 重构 `PreRetrievalJudgeSubAgent.evaluate` 实现动态评分；
   - 完善 `TableAwareChunker.chunk` 支持无虚线表格与自动降级；
   - 为 7 大切片算子补齐标准化中文四要素注释。
3. [backend/] 修改 `backend/app/routers/rag_agent_hub_router.py`：
   - 为 `RagConfigUpdateRequest` 增加数值区间 Field 校验；
   - 为 `check_connectivity` 补齐 `@param` 中文四要素注释。
4. [frontend/] 修改 `frontend/src/views/HospitalProcurementView.vue` 与 `frontend/src/components/PrintVoucherDialog.vue`：
   - 重构 `digitUppercase` 函数的小数处理逻辑，显式判断 `jiao === 0 && fen > 0` 拼接 `零`。
5. [tests/] 校验与回归测试：
   - 验证单调性、切片解析、Pydantic 422、大写金额 Node 运行；
   - 执行 `npm run build`；
   - 运行 `python tests/verify_rag_remediation.py` 与 `python tests/test_challenger_2_empirical.py`。
