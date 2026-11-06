# Modular RAG 热插拔引擎与 RAG Agent Hub 缺陷修复与真实性重构计划

- 计划文档路径：plans/2026-11-04_16-52-00_rag_hub_and_modular_engine_remediation.md
- 记录时间戳：2026-11-04 16:52:00
- 目标文件：
  - 后端目标文件 1: backend/app/routers/rag_agent_hub_router.py (补齐 RagConfigUpdateRequest 缺失字段与标准化注释)
  - 后端目标文件 2: backend/app/services/rag_modular_engine.py (真实稠密余弦向量打分、真实BM25打分、动态查询重写、管道算子激活)
  - 后端配置目标文件 3: backend/.env (同步校准真实模型名称与环境变量)
  - 前端目标文件 4: frontend/src/views/RagAgentHubView.vue (引入 useRoute 监听 route.query.tab 自动同步 Tab)

## 核心评估指标
- 可行性与把握度评估：把握度 100%。所依赖的库 (jieba, rank_bm25, numpy, httpx) 与外部模型 (Ollama bge-m3:latest) 均已在本地真实验证可用。
- 存量功能与三方体验影响分析：对用户 (UX)、开发者 (DX)、智能体 (AX) 均为正向增益，保持所有 REST API 协议向后兼容，彻底去除硬编码伪分数 (0.88/0.82)，零破坏性。
- 回环验证方案：
  - 执行 Python 独立自动化脚本验证后端 API：
    1. POST /api/v1/rag-hub/config/update 持久化验证 (top_k_retrieval=25, enable_subquery_decompose=1)
    2. POST /api/v1/rag-hub/agent/execute 验证真实余弦向量打分与真实 BM25 分数、RRF 融合非固定排序、意图识别与多跳拆解
    3. GET /api/v1/rag-hub/connectivity/check 连通性四方检测全绿验证
  - 前端路由参数联动验证 (模拟 query.tab 切换)。

## 技术与工程规范
1. 函数四要素中文注释：所有新增与修改函数 100% 覆盖 @param, @returns, @route, @throws。
2. 全域禁用 Emoji：代码、注释、日志、返回值中严禁出现任何 Emoji。
3. 真实性铁律：严禁硬编码静态分数，采用真实的数学计算 (余弦相似度、BM25Okapi 相关性、RRF 倒数排名融合)。

实施清单：
1. [后端 backend/.env] 同步配置项：OLLAMA_EMBED_MODEL=bge-m3:latest, OLLAMA_CHAT_MODEL=qwen3.5:2b, XIAOMI_MIMO_MODEL=mimo-v2.6-flash, NEO4J_URI/USER/PASSWORD, LANGCHAIN_TRACING_V2/ENDPOINT/API_KEY/PROJECT。
2. [后端 backend/app/routers/rag_agent_hub_router.py] 在 RagConfigUpdateRequest 中补全 top_k_retrieval, enable_subquery_decompose, enable_intent_classify, enable_hyde 字段；在 update_modular_rag_config 中验证持久化逻辑；补齐标准化中文四要素注释。
3. [后端 backend/app/services/rag_modular_engine.py] 真实稠密向量检索：通过 Ollama bge-m3:latest 计算真实 1024 维向量与余弦相似度 (附带内存缓存提升性能与优雅离线特征哈希兜底)；真实 BM25 检索：基于 jieba 分词与 rank_bm25.BM25Okapi 计算词频相关性；动态查询重写：基于历史反馈多轮增量扩展专业术语；算子激活：接入意图分类识别、复杂多跳子问题拆解、上下文冗余去重。
4. [前端 frontend/src/views/RagAgentHubView.vue] 导入 useRoute，在 onMounted 与 watch(route.query.tab) 中实现 tab 联动切换。
5. [后端服务热重载/重启与自动化测试] 重启 uvicorn 进程加载新配置，运行完整自动化回环测试脚本，验证真实打分、配置持久化与连通性。
