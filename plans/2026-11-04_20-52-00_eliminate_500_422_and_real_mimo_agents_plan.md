# 彻底消除 500/422 报错、全量挂载小米 MiMo 大模型、RBAC 矩阵保存与多模态智能体全物理分层实施计划

- 计划文档路径：`plans/2026-11-04_20-52-00_eliminate_500_422_and_real_mimo_agents_plan.md`
- 记录时间戳：`2026-11-04 20:52:00`
- 关联问题与截图：
  - 图一：大量 500 报错（ORM 模型未导出导致表缺失、字段未对齐抛异常）
  - 图二：RBAC 矩阵无保存按钮、刷新重置（前端构建产物滞后）
  - 图七/图十：上传文档与图片报 422（AxiosHeaders Content-Type 未彻底剔除）
  - 图九：知识库表格右侧操作按钮截断遮挡（表格弹性最小宽度缺失）
  - 图六/图八：智能体秒回假象（需全量接入云端小米 MiMo 与本地真实大模型、展示思考链与工具调用卡片）

---

## 一、核心评估指标

- **方案把握度**：99%（根因全部定位至具体文件和代码行，修复路径清晰原子化）。
- **存量功能与三方体验影响**：
  - **UX**：彻底消除报错红弹窗，知识库操作按钮不再截断，RBAC 矩阵增加未保存提示条幅与保存按钮，智能体呈现真实流式推理耗时与 DeepSeek/<think> 思考折叠卡片。
  - **DX**：后端全面物理分层解耦（`services/rag/` 与 `services/agents/`），函数 100% 具备标准化中文四要素注释。
  - **AX**：各智能体与 RAG 算子具备清晰的 Pydantic V2 契约与时间戳追踪，杜绝伪造数据。

---

## 二、目标变更范围

### 1. 后端目标文件
- `backend/app/models/__init__.py`：导出 `SpdAgentModelConfig` 与 `SpdAgentChatMessage`，确保启动建表。
- `backend/app/services/agents/llm_client.py`：增强大模型统一调用客户端，默认配置小米 MiMo (`mimo-v2.6-flash`)，并兼容本地 Ollama。
- `backend/app/services/agents/agent_2_router_skill.py`：智能体 2 (Router + Skill) 独立物理模块，真实调用 LLM 分诊意图。
- `backend/app/services/agents/agent_3_langgraph.py`：智能体 3 (LangGraph + HITL) 独立物理模块，真实调用 LLM 问答与人机回环。
- `backend/app/services/agents/agent_4_react.py`：智能体 4 (ReAct) 独立物理模块，真实调用 LLM 推理与 UDI 穿透查库。
- `backend/app/services/agents/agent_5_blackboard.py`：智能体 5 (Blackboard) 独立物理模块，真实调用 LLM 执行财务精算与合规审计。
- `backend/app/services/agents/agent_6_supervisor.py`：智能体 6 (Agentic RAG) 独立物理模块，真实调用 LLM 执行多轮自省与多路问答。
- `backend/app/services/agents/__init__.py`：统一导出 6 大智能体类与统一客户端。
- `backend/app/routers/rag_agent_hub_router.py`：精简路由逻辑，修正文档上传入库字段，多模态识图接入 OpenCV 与大模型分析，默认智能体模型设为小米 MiMo。

### 2. 前端目标文件
- `frontend/src/api/request.ts`：彻底修正 FormData 请求头拦截器，兼容 AxiosHeaders 的 `.delete()` 与多种大小写变体。
- `frontend/src/views/UserManagementView.vue`：固化 RBAC 矩阵保存按钮，新增 `hasUnsavedChanges` 变动检测与提示条幅。
- `frontend/src/views/RagAgentHubView.vue`：表格增加保底 `min-width: 880px` 与操作列宽扩展至 `120px`，自适应滚动，杜绝遮挡。

### 3. 测试与验证目标
- `tests/e2e/test_mimo_agents_and_fixes.spec.js`：编写端到端自动化验证脚本。
- `tests/screenshots/`：捕获实机运行截图，验收 0 报错、无遮挡及真实模型推理。

---

## 三、原子级实施清单

1. **[后端] 补全 ORM 导出与模型对齐**：修改 `backend/app/models/__init__.py`，确保应用启动时自动在 MySQL 中补建 `spd_agent_model_config` 和 `spd_agent_chat_message` 表。
2. **[后端] 编写智能体 2 至 6 的独立物理模块**：在 `backend/app/services/agents/` 下依次实现 `agent_2_router_skill.py`、`agent_3_langgraph.py`、`agent_4_react.py`、`agent_5_blackboard.py`、`agent_6_supervisor.py` 并接入真实小米 MiMo / Ollama。
3. **[后端] 重构路由层并修复 ORM 入库字段**：更新 `backend/app/routers/rag_agent_hub_router.py`，修正 `post_upload_document_file` 中的字段赋值，完善多模态图片识别接口，并将默认模型初始化为云端小米 MiMo。
4. **[前端] 彻底修复 Axios FormData 拦截器**：修改 `frontend/src/api/request.ts`，确保删除所有的 Content-Type 请求头，杜绝 422。
5. **[前端] 完善 RBAC 矩阵保存交互与未保存提示**：修改 `frontend/src/views/UserManagementView.vue`，添加未保存状态监控与持久化保存通知。
6. **[前端] 修复知识库表格自适应与操作列截断**：修改 `frontend/src/views/RagAgentHubView.vue`，给表格容器声明最小宽度与操作列充足宽度。
7. **[编译] 执行前端构建**：在 `frontend/` 下执行 `npm run build`，确保 0 报错并刷新 `dist/` 生产静态文件。
8. **[服务] 重启后端与前端服务**：启动 Uvicorn (8000) 与 Vite preview (5173)。
9. **[测试] 运行 Playwright 自动化回环验证**：执行端到端脚本，验证文档上传（无 422/500）、图片上传、智能体真实耗时思考链与 RBAC 保存，截取实机证据图片。
