# [2026-11-04 19:44:26] 医疗物资系统后端 RAG 物理分层解耦、真实大模型推理与前端 422 及自适应彻底修复实施计划

---

## 1. 计划归档与变更范围

[变更计划]
- 计划文档路径：plans/2026-11-04_19-44-26_modular_rag_and_real_llm_agents_plan.md
- 记录时间戳：[2026-11-04 19:44:26]
- 前端目标文件：
  1. `frontend/src/api/request.ts`：在请求拦截器中增加针对 `FormData` 的动态头处理（当请求体为 `FormData` 时强制移除默认的 `Content-Type: application/json`，让浏览器原生自适应构建带有 Boundary 的 `multipart/form-data`），彻底根治文件与图片上传 422 报错。
  2. `frontend/src/views/RagAgentHubView.vue`：重构 `.doc-main-table-wrap` 样式，设置 `min-width: 0; width: 0; flex: 1 1 0%; overflow-x: auto;` 消除表格右侧操作按钮被视口硬遮挡缺陷；为每个文档增加醒目的切分策略色彩徽章与动态切片数显示。
  3. `frontend/src/components/AgentChatWidget.vue`：在对话面板顶部与消息流中增加“真实大模型推理状态指示器”（展示当前调用的模型如 `deepseek-r1:1.5b`、真实推理耗时毫秒数与生成的 Token 总量），确保思考过程与工具调用过程真实透明。
- 后端目标文件：
  1. 新建 `backend/app/services/rag/` 物理分层独立包：
     - `backend/app/services/rag/__init__.py`
     - `backend/app/services/rag/document_loader.py`：高精度文档提取器（PyMuPDF 处理 PDF、python-docx 处理 Word、UTF-8 纯文本处理 MD/TXT）。
     - `backend/app/services/rag/chunkers.py`：7 大分块策略独立类（RecursiveCharChunker, TableAwareChunker, MarkdownHeaderChunker 等）。
     - `backend/app/services/rag/feature_radar.py`：Agent 6A 自主特征探测雷达算法（表格密度、条款密度、标题层级）。
     - `backend/app/services/rag/hybrid_retriever.py`：Chroma 稠密向量 + BM25 稀疏词频 + Neo4j 知识图谱三元组混合检索器。
  2. 新建 `backend/app/services/agents/` 物理分层独立包：
     - `backend/app/services/agents/__init__.py`
     - `backend/app/services/agents/llm_client.py`：工业级真实大模型调用客户端，统一接入本地 Ollama (`http://127.0.0.1:11434/api/generate`) 与云端小米 MiMo，支持提取 DeepSeek `<think>` 思考链、统计真实 Token 数量与采样耗时。
     - `backend/app/services/agents/agent_1_plan_execute.py`：智能体 1 真实调用 LLM 生成 3 步计划，执行查库建档，再调用 LLM 生成汇总报告。
     - `backend/app/services/agents/agent_2_router_skill.py`：智能体 2 真实调用 LLM 意图识别并分发技能。
     - `backend/app/services/agents/agent_3_langgraph.py`：智能体 3 真实 LangGraph 状态图与人机回环挂起恢复。
     - `backend/app/services/agents/agent_4_react.py`：智能体 4 真实 ReAct 循环推理（Thought -> Action -> Observation -> Final Answer）。
     - `backend/app/services/agents/agent_5_blackboard.py`：智能体 5 真实公共黑板多专家协同与 LLM 审计总结。
     - `backend/app/services/agents/agent_6_supervisor.py`：智能体 6 Agentic RAG 主管智能体。
  3. `backend/app/routers/rag_agent_hub_router.py`：精简重构，全面引入上述模块化包，消除千行单文件反模式，严格遵循单一职责原则（SRP）。
- 测试与截图文件：
  1. `tests/verify_real_llm_and_fixes.js`：自动化端到端测试，覆盖文件上传（200 OK，无 422）、图片上传（无 422）、知识库表格自适应无截断及真实 LLM 推理耗时验证。
  2. `tests/screenshots/2026-11-04_19-44-26_01_upload_file_200_success.png`
  3. `tests/screenshots/2026-11-04_19-44-26_02_knowledge_table_responsive_full.png`
  4. `tests/screenshots/2026-11-04_19-44-26_03_real_llm_inference_thinking.png`

---

## 2. 核心评估指标（必填）

- **可行性与把握度评估**：
  - **把握度：99%**
  - **潜在风险与规避策略**：
    - Ollama 本地模型冷启动或并发超时：在 `llm_client.py` 中设置 30 秒 HTTP 超时，并自带优雅的超时捕获与多级安全降级（若本地模型未运行，无缝使用快速回退响应并给出醒目的离线提示，绝不抛出 500 异常崩溃）。
- **存量功能与三方体验影响分析**：
  - **用户体验（UX）**：422 报错彻底绝迹，文件与图片拖拽即传；知识库表格右侧按钮完整呈现，不再遮挡；智能体回答具备真实的思考延迟与 Token 吞吐反馈，消除虚假秒回感。
  - **开发者体验（DX）**：后端实现彻底的物理目录分包（`rag/` 和 `agents/`），高内聚低耦合，符合 GEMINI.md 架构规范，极易阅读、维护与扩展。
  - **AI 代理体验（AX）**：模块划分清晰分明，函数入参出参 100% 具备标准化中文四要素注释，上下文检索效率大幅提升。
  - **存量保护底线**：所有既有业务 API 路径、请求参数与响应模型保持 100% 兼容。

- **Playwright 自动化回环测试与截图验证方案**：
  - 断言 1：模拟上传 `测试规范.txt`，验证 HTTP 状态码为 200，且成功生成切片并在表格中动态展示切片数与策略；
  - 断言 2：检查知识库表格右侧操作按钮可见性（`isIntersectingViewport: true`），断言无截断；
  - 断言 3：模拟向智能体提问，断言响应中包含 `model_used`、`latency_ms > 0` 与真实的推理内容，捕获实机截图保存至 `tests/screenshots/`。

---

## 3. 技术与 UI 细节规范

### 3.1 前端 Axios 拦截器 422 修复规范
```typescript
// frontend/src/api/request.ts
service.interceptors.request.use((config) => {
  // 当传递载荷为 FormData 时，强制删除 Content-Type，使浏览器自适应注入 multipart/form-data; boundary=...
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  // 其余 token 与身份注入逻辑保持向后兼容
  return config;
});
```

### 3.2 知识库表格自适应布局修复
```css
/* frontend/src/views/RagAgentHubView.vue */
.doc-main-table-wrap {
  flex: 1 1 0%;
  min-width: 0;
  width: 0;
  display: flex;
  flex-direction: column;
  overflow-x: auto;
}
```

### 3.3 真实 LLM 调用客户端 (`backend/app/services/agents/llm_client.py`)
```python
class RealLlmClient:
    """工业级真实大模型统一调用客户端 (Ollama / MiMo)"""
    
    @staticmethod
    def generate(
        prompt: str,
        system_prompt: str = "",
        model_name: str = "qwen3.5:2b",
        provider: str = "ollama",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """向真实本地 Ollama 或云端 MiMo 发起推理请求
        @param prompt: str 用户指令或任务内容
        @param system_prompt: str 系统角色提示词
        @param model_name: str 模型名称
        @param provider: str 提供商 (ollama / mimo)
        @param temperature: float 采样温度
        @param max_tokens: int 最大生成 Token 上限
        @returns Dict[str, Any] 包含 final_text, thought_process, latency_ms, total_tokens, model_used
        @route internal://services/agents/llm_client/generate
        @throws 遇到模型离线时自动捕获并返回合规兜底
        """
```

---

## 4. 强制性最终步骤（原子实施清单）

```markdown
实施清单：
1. [前端 - 请求层 422 根治] 修改 frontend/src/api/request.ts，在请求拦截器中增加针对 FormData 的 Header 清理逻辑，彻底解决文件与图片上传 422 报错。
2. [前端 - 知识库布局与表格自适应] 修改 frontend/src/views/RagAgentHubView.vue，重塑 .doc-main-table-wrap 样式为 min-width: 0 并优化列宽，确保操作列 100% 完整可见；表格动态展示策略色彩徽章与真实切片块数。
3. [后端 - RAG 物理分层解耦] 新建 backend/app/services/rag/ 目录，将文档提取（document_loader.py）、7大分块策略（chunkers.py）、特征雷达（feature_radar.py）与多路检索（hybrid_retriever.py）物理拆离为独立高内聚模块。
4. [后端 - 真实 LLM 客户端] 新建 backend/app/services/agents/llm_client.py，实现对本地 Ollama (POST /api/generate) 与云端 MiMo 的真实 HTTP 调用，解析 DeepSeek <think> 思考链，统计真实耗时与 Token 数。
5. [后端 - 6 大智能体物理分包重构] 在 backend/app/services/agents/ 目录下分别实现 agent_1 到 agent_6 的独立子模块，全面接入 RealLlmClient 与真实的数据库工具调用链路。
6. [后端 - 路由层收敛] 重构 backend/app/routers/rag_agent_hub_router.py，彻底移除臃肿内嵌代码，统一导入 rag/ 与 agents/ 包，恢复简洁清晰的路由中枢架构。
7. [服务重启与编译] 执行前端 npm run build 验证 0 错误编译，重启后端 Uvicorn 与前端预览服务。
8. [自动化回环验证与实机截图] 编写并运行 tests/verify_real_llm_and_fixes.js，验证文件上传 200 OK、图片上传 200 OK、表格自适应正常及智能体真实模型推理，捕获关键实机截图归档至 tests/screenshots/。
```

---

请您审阅以上实施计划。如果方案完全符合您的要求，请批准进入 `[MODE: EXECUTE]`，我将立即按照清单逐项实施并交付实机截图凭证！
