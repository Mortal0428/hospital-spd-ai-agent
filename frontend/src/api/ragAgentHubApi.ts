/**
 * @file ragAgentHubApi.ts
 * @description Agentic RAG 知识工程与 6 大异构智能体控制中台前端 API 请求封装
 * @param 无
 * @returns 统一数据结构 Promise
 * @route /api/v1/rag-hub/*
 * @throws 统一通过 http 封装抛出异常
 */

import { httpGet, httpPost, httpDelete } from './request';

export interface CategoryTreeNode {
  id: number;
  parent_id: number;
  category_code: string;
  category_name: string;
  sort_order: number;
  description: string;
  icon_name: string;
  doc_count: number;
  children: CategoryTreeNode[];
}

export interface DocumentItem {
  id: number;
  category_id: number;
  doc_code: string;
  doc_title: string;
  file_type: string;
  file_size_kb: number;
  doc_status: string;
  selected_chunk_strategy: string;
  chunk_count: number;
  graph_entity_count: number;
  agent_decision_reason: string;
  created_at: string;
}

export interface ChunkItem {
  id: number;
  chunk_index: number;
  chunk_uid: string;
  parent_chunk_uid?: string;
  chunk_text: string;
  chunk_size: number;
  strategy_applied: string;
  metadata: Record<string, any>;
}

export interface ModularRagConfig {
  enable_intent_classify: number;
  enable_query_rewrite: number;
  max_rewrite_loops: number;
  rewrite_threshold: number;
  enable_subquery_decompose: number;
  enable_dense_vector: number;
  enable_bm25_sparse: number;
  enable_graph_rag: number;
  top_k_retrieval: number;
  enable_reranker: number;
  rerank_threshold: number;
  enable_context_compression: number;
  enable_citation_source: number;
  enable_faithfulness_check?: number;
  enable_system_grounding?: number;
  default_chunking_mode?: string;
  active_embedding_model: string;
  active_llm_provider: string;
  active_chat_model: string;
  mimo_base_url: string;
  mimo_model_name: string;
  has_mimo_env_key: boolean;
  enable_streaming?: number;
  enable_deep_thinking?: number;
  llm_timeout_seconds?: number;
  default_chunk_size?: number;
  default_chunk_overlap?: number;
  enable_feishu_welcome_card?: number;
  feishu_welcome_cooldown_hours?: number;
  langsmith_enabled: number;
  langsmith_project: string;
  langsmith_endpoint: string;
  has_langsmith_key: boolean;
  chroma_stats?: {
    ready: boolean;
    total_vectors: number;
    storage_path: string;
    collection: string;
    error?: string;
  };
}

export interface DocumentCreatePayload {
  category_id: number;
  doc_title: string;
  file_type: string;
  content: string;
  chunk_strategy: string;
  chunk_size?: number;
  chunk_overlap?: number;
  decision_mode?: string;
}

export interface ConnectivityData {
  ollama: {
    connected: boolean;
    models: string[];
    latency_ms: number;
    msg: string;
  };
  redis: {
    connected: boolean;
    latency_ms: number;
    msg: string;
  };
  neo4j: {
    connected: boolean;
    nodes: number;
    latency_ms: number;
    msg: string;
  };
  mimo: {
    configured: boolean;
    model: string;
    msg: string;
  };
  langsmith: {
    enabled: boolean;
    project: string;
    has_key: boolean;
  };
}

export interface AgentExecutePayload {
  agent_id: string;
  query: string;
  resume_action?: string;
  state_payload?: Record<string, any>;
  review_comment?: string;
  user_role?: string;
}

export interface RagInspectionResult {
  status: string;
  total_documents: number;
  indexed_documents: number;
  unindexed_count: number;
  health_score: number;
  abnormal_documents: Array<{
    doc_id: number;
    doc_code: string;
    doc_title: string;
    file_type: string;
    file_size_kb: number;
    recorded_chunks: number;
    actual_chunks: number;
    doc_status: string;
    recommended_strategy: string;
    strategy_reason: string;
  }>;
}

/**
 * 知识库切片健康度全库巡检 (Sub-Agent 6A)
 * @param 无
 * @returns {Promise<RagInspectionResult>} 巡检结果包含总文档数、已切片数与异常清单
 * @route GET /api/v1/rag-hub/maintenance/inspect
 * @throws 请求失败时抛出 HTTP 错误
 */
export async function getRagInspection(): Promise<RagInspectionResult> {
  return await httpGet<RagInspectionResult>('/rag-hub/maintenance/inspect');
}

/**
 * 针对未切片/异常文档执行自动/指定策略重新切片 (Sub-Agent 6A)
 * @param {Object} payload 重新切片请求参数
 * @param {number} payload.doc_id 目标文档主键 ID
 * @param {string} [payload.strategy] 可选指定切片策略 (为空则由 Agent 动态自主决策)
 * @returns {Promise<any>} 重新切片执行结果与生成的切片统计
 * @route POST /api/v1/rag-hub/maintenance/rechunk
 * @throws 重新切片执行异常时抛出
 */
export async function postRagRechunk(payload: { doc_id: number; strategy?: string }): Promise<any> {
  return await httpPost<any>('/rag-hub/maintenance/rechunk', payload);
}

/**
 * 获取知识库树状分类目录
 * @param 无
 * @returns {Promise<CategoryTreeNode[]>} 树状目录节点数组
 * @route GET /api/v1/rag-hub/category/tree
 * @throws 获取目录结构异常时抛出
 */
export async function getCategoryTree(): Promise<CategoryTreeNode[]> {
  return await httpGet<CategoryTreeNode[]>('/rag-hub/category/tree');
}

/**
 * 保存或更新知识库分类目录
 * @param {Partial<CategoryTreeNode>} payload 分类目录编辑载荷
 * @returns {Promise<any>} 保存结果实体
 * @route POST /api/v1/rag-hub/category/save
 * @throws 目录信息校验失败或后端持久化异常时抛出
 */
export async function saveCategory(payload: Partial<CategoryTreeNode>): Promise<any> {
  return await httpPost<any>('/rag-hub/category/save', payload);
}

/**
 * 删除知识库分类目录
 * @param {number} id 分类目录主键 ID
 * @returns {Promise<any>} 删除结果
 * @route DELETE /api/v1/rag-hub/category/{id}
 * @throws 目录下仍有文档或网络故障时抛出
 */
export async function deleteCategory(id: number): Promise<any> {
  return await httpDelete<any>(`/rag-hub/category/${id}`);
}

/**
 * 获取文档资产列表 (支持按目录筛选)
 * @param {number} [categoryId] 可选目录分类 ID 过滤
 * @returns {Promise<DocumentItem[]>} 医疗规范文档列表
 * @route GET /api/v1/rag-hub/document/list
 * @throws 文档查询异常时抛出
 */
export async function listDocuments(categoryId?: number): Promise<DocumentItem[]> {
  const url = categoryId ? `/rag-hub/document/list?category_id=${categoryId}` : '/rag-hub/document/list';
  return await httpGet<DocumentItem[]>(url);
}

/**
 * 创建文档并执行 7 大策略 Agentic 智能分块
 * @param {DocumentCreatePayload} payload 文档正文与切片策略配置
 * @returns {Promise<any>} 创建成功回执与生成切片数
 * @route POST /api/v1/rag-hub/document/create-and-chunk
 * @throws 文本切片或向量入库异常时抛出
 */
export async function createDocumentAndChunk(payload: DocumentCreatePayload): Promise<any> {
  return await httpPost<any>('/rag-hub/document/create-and-chunk', payload);
}

/**
 * 删除知识库文档并物理清理 MySQL 切片与 Chroma 向量
 * @param {number} docId 目标文档主键 ID
 * @returns {Promise<any>} 删除回执
 * @route DELETE /api/v1/rag-hub/document/${docId}
 * @throws 物理清理异常时抛出
 */
export async function deleteDocumentApi(docId: number): Promise<any> {
  return await httpDelete<any>(`/rag-hub/document/${docId}`);
}

/**
 * 获取指定文档切片详情
 * @param {number} docId 目标文档主键 ID
 * @returns {Promise<ChunkItem[]>} 文档切片列表
 * @route GET /api/v1/rag-hub/document/${docId}/chunks
 * @throws 切片获取失败时抛出
 */
export async function getDocumentChunks(docId: number): Promise<ChunkItem[]> {
  return await httpGet<ChunkItem[]>(`/rag-hub/document/${docId}/chunks`);
}

/**
 * 获取 Modular RAG 热插拔全局配置
 * @param 无
 * @returns {Promise<ModularRagConfig>} 各算子开关与大模型状态
 * @route GET /api/v1/rag-hub/config
 * @throws 配置加载失败时抛出
 */
export async function getModularRagConfig(): Promise<ModularRagConfig> {
  return await httpGet<ModularRagConfig>('/rag-hub/config');
}

/**
 * 更新 Modular RAG 热插拔配置
 * @param {Partial<ModularRagConfig>} payload 需更新的算子配置参数
 * @returns {Promise<any>} 更新回执
 * @route POST /api/v1/rag-hub/config/update
 * @throws 配置持久化异常时抛出
 */
export async function updateModularRagConfig(payload: Partial<ModularRagConfig>): Promise<any> {
  return await httpPost<any>('/rag-hub/config/update', payload);
}

/**
 * 探测四方连通性健康状况 (Ollama, Redis, Neo4j, MiMo, LangSmith)
 * @param 无
 * @returns {Promise<ConnectivityData>} 基础设施连接状态与时延
 * @route GET /api/v1/rag-hub/connectivity/check
 * @throws 探测服务不可用时抛出
 */
export async function checkConnectivity(): Promise<ConnectivityData> {
  return await httpGet<ConnectivityData>('/rag-hub/connectivity/check');
}

/**
 * 执行 6 大业务智能体常规调用
 * @param {AgentExecutePayload} payload 智能体标识与用户提问指令
 * @returns {Promise<any>} 智能体执行结果、思考链与工具调用记录
 * @route POST /api/v1/rag-hub/agent/execute
 * @throws 智能体执行超时或网络中断时抛出
 */
export async function executeAgentCall(payload: AgentExecutePayload): Promise<any> {
  return await httpPost<any>('/rag-hub/agent/execute', payload);
}

/**
 * 独立测试单项基础设施连通性与时延
 * @param {'ollama' | 'redis' | 'neo4j' | 'mimo' | 'langsmith'} target 测试目标
 * @returns {Promise<any>} 单项连通性测速结果
 * @route POST /api/v1/rag-hub/connectivity/test-single
 * @throws 目标连接失败时抛出
 */
export async function testSingleConnectivity(target: 'ollama' | 'redis' | 'neo4j' | 'mimo' | 'langsmith'): Promise<any> {
  return await httpPost<any>('/rag-hub/connectivity/test-single', { target });
}

/**
 * 真实上传 PDF/Word/MD/TXT 文件并由 Agent 执行特征雷达探测与分块
 * @param {FormData} formData 包含上传文件的表单数据
 * @returns {Promise<any>} 文件解析与切片入库详情
 * @route POST /api/v1/rag-hub/document/upload-file
 * @throws 文件格式不支持或解析失败时抛出
 */
export async function uploadDocumentFile(formData: FormData): Promise<any> {
  return await httpPost<any>('/rag-hub/document/upload-file', formData);
}

/**
 * 获取 6 大智能体独立大模型解耦配置
 * @param 无
 * @returns {Promise<any[]>} 智能体独立模型配置列表
 * @route GET /api/v1/rag-hub/agent-models
 * @throws 读取智能体配置异常时抛出
 */
export async function getAgentModels(): Promise<any[]> {
  return await httpGet<any[]>('/rag-hub/agent-models');
}

/**
 * 批量或单独保存 6 大智能体大模型解耦配置
 * @param {any[]} configs 智能体独立模型配置清单
 * @returns {Promise<any>} 保存完成回执
 * @route POST /api/v1/rag-hub/agent-models/batch-save
 * @throws 配置写入异常时抛出
 */
export async function saveAgentModels(configs: any[]): Promise<any> {
  return await httpPost<any>('/rag-hub/agent-models/batch-save', configs);
}

/**
 * 拉取指定智能体历史会话消息
 * @param {string} agentId 智能体编号
 * @param {string} [sessionId='default'] 会话会话 ID
 * @returns {Promise<any[]>} 历史对话记录列表
 * @route GET /api/v1/rag-hub/chat/history
 * @throws 获取历史会话异常时抛出
 */
export async function getAgentChatHistory(agentId: string, sessionId = 'default'): Promise<any[]> {
  return await httpGet<any[]>(`/rag-hub/chat/history?agent_id=${agentId}&session_id=${sessionId}`);
}

/**
 * 上传多模态实物图片或 UDI 二维码
 * @param {FormData} formData 包含图片的表单对象
 * @returns {Promise<any>} 图片识别结果与条码解析
 * @route POST /api/v1/rag-hub/chat/upload-image
 * @throws 图片解析异常时抛出
 */
export async function uploadChatImage(formData: FormData): Promise<any> {
  return await httpPost<any>('/rag-hub/chat/upload-image', formData);
}

/**
 * 测试发送原生飞书业务交互式卡片 (支持 Webhook 直连与 OpenAPI 双轨，支持精准 @成员)
 * @param {Object} payload 飞书卡片配置参数
 * @param {string} payload.card_type 卡片业务场景类型
 * @param {string} [payload.receive_id] 可选接收人或群标识
 * @param {string} [payload.webhook_url] 飞书群自定义机器人 Webhook 地址
 * @param {string} [payload.product_name] 物资名称
 * @param {string} [payload.at_open_id] 需强提醒并 @ 的成员 open_id
 * @returns {Promise<any>} 飞书消息发送结果回执
 * @route POST /api/v1/rag-hub/feishu/send-test
 * @throws 飞书鉴权失败或网络超时时抛出
 */
export async function testFeishuCard(payload: { card_type: string; receive_id?: string; webhook_url?: string; product_name?: string; at_open_id?: string }): Promise<any> {
  return await httpPost<any>('/rag-hub/feishu/send-test', payload);
}

/**
 * 与云端 Coze 小爱智能体协同问答 (基于 Coze V3 Chat 协议)
 * @param {Object} payload 提问参数
 * @param {string} payload.query 咨询问题正文
 * @param {string} [payload.user_id] 用户标识
 * @returns {Promise<any>} Coze 智能体返回回答实体
 * @route POST /api/v1/rag-hub/coze/chat
 * @throws Coze API 通信异常时抛出
 */
export async function chatWithCoze(payload: { query: string; user_id?: string }): Promise<any> {
  return await httpPost<any>('/rag-hub/coze/chat', payload);
}

/**
 * 获取飞书官方 SDK 长连接 (反向 WebSocket) 实时健康状态与监听指标
 * @returns {Promise<any>} 长连接在线状态、已处理消息数与连接 ID
 * @route GET /api/v1/rag-hub/feishu/ws-status
 * @throws 网络异常时抛出
 */
export async function getFeishuWsStatus(): Promise<any> {
  return await httpGet<any>('/rag-hub/feishu/ws-status');
}

/**
 * 手动重新启动飞书官方 SDK 长连接守护服务
 * @returns {Promise<any>} 重启回执与刷新后的连接状态
 * @route POST /api/v1/rag-hub/feishu/ws-restart
 * @throws 重启请求异常时抛出
 */
export async function restartFeishuWs(): Promise<any> {
  return await httpPost<any>('/rag-hub/feishu/ws-restart', {});
}

/**
 * 一键统一持久化 Modular RAG 全局配置、8 大业务智能体模型解耦配置与飞书 Webhook
 * @param {Object} payload 统一保存载荷
 * @param {any} [payload.global_config] Modular RAG 算子全局参数
 * @param {any[]} [payload.agent_configs] 8 大业务智能体独立模型配置列表
 * @param {string} [payload.feishu_webhook_url] 飞书群自定义机器人 Webhook 地址
 * @returns {Promise<any>} 统一落盘回执
 * @route POST /api/v1/rag-hub/config/save-all
 * @throws 数据库批量事务提交异常时抛出
 */
export async function saveAllUnifiedConfig(payload: { global_config?: any; agent_configs?: any[]; feishu_webhook_url?: string }): Promise<any> {
  return await httpPost<any>('/rag-hub/config/save-all', payload);
}

/**
 * 获取系统接入的外部解耦 MCP 协议扩展工具清单与监控指标
 * @param 无
 * @returns {Promise<any>} 外部 MCP 工具列表与配置状态
 * @route GET /api/v1/rag-hub/mcp-external/status
 * @throws 网络请求异常时抛出
 */
export async function getExternalMcpStatus(): Promise<any> {
  return await httpGet<any>('/rag-hub/mcp-external/status');
}

/**
 * 动态启用或停用指定的外部 MCP 协议工具
 * @param {string} toolName 工具标识
 * @param {boolean} enabled 启闭状态
 * @returns {Promise<any>} 切换回执
 * @route POST /api/v1/rag-hub/mcp-external/toggle
 * @throws 切换失败时抛出
 */
export async function toggleExternalMcpTool(toolName: string, enabled: boolean): Promise<any> {
  return await httpPost<any>('/rag-hub/mcp-external/toggle', { tool_name: toolName, enabled });
}

/**
 * 手动调试执行外部 MCP 工具 (用于控制台连通性与入参出参测试)
 * @param {string} toolName 工具标识
 * @param {Record<string, any>} args 入参字典
 * @returns {Promise<any>} 执行结果、耗时与标准出参
 * @route POST /api/v1/rag-hub/mcp-external/execute
 * @throws 执行异常时抛出
 */
export async function executeExternalMcpTool(toolName: string, args: Record<string, any>): Promise<any> {
  return await httpPost<any>('/rag-hub/mcp-external/execute', { tool_name: toolName, arguments: args });
}

/**
 * 智能体对话反馈请求载荷契约 (方案 C 落地)
 */
export interface AgentChatFeedbackPayload {
  agent_id: string;
  query: string;
  original_answer: string;
  feedback_type: 'THUMBS_UP' | 'CORRECTION';
  correction_text?: string;
  operator_name?: string;
}

/**
 * 提交智能体回答的临床医护采纳建议或人工纠偏知识（写入 Chroma 物理向量库 EXPERT_HUMAN_CORRECTION 分区）
 * @param {AgentChatFeedbackPayload} payload 包含智能体标识、原提问、原回答、纠偏类型及内容
 * @returns {Promise<any>} 持久化写入结果与自演化向量元数据
 * @route POST /api/v1/rag-hub/chat/feedback
 * @throws 提交失败时抛出异常
 */
export async function submitAgentChatFeedback(payload: AgentChatFeedbackPayload): Promise<any> {
  return await httpPost<any>('/rag-hub/chat/feedback', payload);
}




