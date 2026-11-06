# Milestone 1 迭代 4 缺陷修复实施计划 (Milestone 1 Iteration 4 Defect Remediation Plan)

[变更计划]
- 计划文档路径：plans/2026-11-05_18-27-00_milestone_m1_it4_defect_remediation_plan.md
- 记录时间戳：2026-11-05 18:27:00
- 后端目标文件：
  - `backend/app/services/mcp_tools/schema.py` (核验 BaseToolInput extra="forbid")
  - `backend/app/services/mcp_tools/requisition_tools.py` (移除全默认与自动取首条物资回退)
  - `backend/app/services/coze_service.py` (chat_stream 循环退出兜底推送 done: True)
- 测试与验证文件：
  - `tests/test_coze_adversarial_challenge.py` (同步 test_10 与 test_11 验证修复效果)
  - `tests/test_mcp_adversarial_stress.py` (回归验证)
  - `tests/test_all_agents_mcp_and_feishu_coze.py` (回归验证)
  - `tests/test_challenger_m1_adversarial.py` (回归验证)

## 核心评估指标
- 可行性与把握度评估：把握度 100%。修改点定位极其清晰，属于标准参数强校验与生成器流式状态机闭环补齐。
- 存量功能与三方体验影响分析：
  - UX：彻底消除 Coze 异常响应下游打字机无休止悬挂死锁问题；
  - DX：消除空参数假执行漏洞，强化 Pydantic V2 契约，提高接口鲁棒性；
  - AX：保证 MCP 工具在遇到非法参数时返回标准 ToolResult(success=False, error="INVALID_ARGUMENTS")，防止 Agent 产生幻觉假成功。
- 零破坏性保护：存量正常调用均传入完整参数，不受影响。

## 实施清单
1. 检查并确认 `backend/app/services/mcp_tools/schema.py` 中 `BaseToolInput` 的 `model_config = ConfigDict(extra="forbid", populate_by_name=True)`。
2. 修改 `backend/app/services/mcp_tools/requisition_tools.py`：
   - 将 `SubmitRequisitionInput` 的 `product_name` 设为必填（无默认值）：`product_name: str = Field(..., min_length=1, description="申领物资名称(必填，支持模糊自动匹配产品字典)")`；
   - 彻底移除 `mcp_submit_sec_requisition` 中的回退逻辑：`if not product: product = db.query(SpdProductDict).filter(SpdProductDict.is_deleted == 0).first()`；未找到物资直接返回 `PRODUCT_NOT_FOUND`。
3. 修改 `backend/app/services/coze_service.py`：
   - 在 `chat_stream` 的响应循环前初始化 `has_completed = False`；
   - 在已触发的完成事件 (`conversation.chat.failed` 与 `conversation.chat.completed`) 中标记 `has_completed = True`；
   - 在 `for line in response.iter_lines():` 循环退出后，若 `not has_completed`，兜底 yield:
     `{"type": "completed", "delta": "", "role": "assistant", "conversation_id": current_conv_id or "conv-end", "done": True}`。
4. 同步更新 `tests/test_coze_adversarial_challenge.py` 中 `test_10` 与 `test_11` 的断言，验证在空 body 和 `[DONE]` 提前收到时，最后一个分包成功包含 `done: True` 与 `type: "completed"`。
5. 运行真实全量 4 套回归测试套件（58 项用例），验证 100% 物理通过：
   `pytest tests/test_all_agents_mcp_and_feishu_coze.py tests/test_challenger_m1_adversarial.py tests/test_coze_adversarial_challenge.py tests/test_mcp_adversarial_stress.py -v`
6. 执行 AST 语法树中文四要素注释扫描与 Unicode Emoji 静态扫描，确保 0 违规。
7. 在工作目录下生成自包含 handoff.md 报告，并通过 send_message 回传给主协调器 Orchestrator。
