"""
@file rag_agent_models.py
@description 医疗物资全链路 SPD 知识工程与 6 大异构智能体 ORM 数据模型
严格遵循 SQLAlchemy 2.0 声明式映射，所有表与所有字段 100% 携带详细中文注释 (comment)。
承载知识库树状目录分类、文档六阶状态机、7 大策略切片明细、Modular RAG 热插拔配置与智能体执行追踪。

@param 无 (ORM 模型定义)
@returns SQLAlchemy Declarative Models
@route internal://backend/app/models/rag_agent_models.py
@throws 无
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer,
    SmallInteger,
    String,
    Text,
    DateTime,
    Numeric,
    func
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SpdRagCategoryTree(Base):
    """知识库树状目录分类表：支持无限级树形层级管理与增删改查"""
    __tablename__ = "spd_rag_category_tree"
    __table_args__ = {"comment": "知识库树状目录分类表：承载国家医疗器械法规/手术定数包/耗材目录等树状多级归集"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分类节点主键ID")
    parent_id: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True, comment="父级节点ID(0表示顶级分类根目录)")
    category_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="分类编码(如: CAT_REGULATION, CAT_SURGERY_PACK)")
    category_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="分类显示名称(如: 国家医疗器械法规与药监准入标准)")
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="同级目录排序权重")
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="分类业务职能描述")
    icon_name: Mapped[str] = mapped_column(String(64), default="folder", nullable=False, comment="前端渲染的矢量图标标识")
    doc_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="当前目录下归集的文档总篇数")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")


class SpdRagDocument(Base):
    """离线知识文档资产表：严格记录六阶状态机生命周期与 7 大策略执行结果"""
    __tablename__ = "spd_rag_document"
    __table_args__ = {"comment": "离线知识文档资产表：跟踪文档解析清洗、Agent决策分块、向量化与图谱构建六阶状态机"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="文档主键ID")
    category_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="所属树状目录节点ID")
    doc_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="文档统一编号(如: DOC-202611-001)")
    doc_title: Mapped[str] = mapped_column(String(255), nullable=False, comment="文档名称标题")
    file_type: Mapped[str] = mapped_column(String(32), default="markdown", nullable=False, comment="文件类型(pdf, docx, xlsx, markdown, txt)")
    file_size_kb: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="文件大小(KB)")
    doc_status: Mapped[str] = mapped_column(
        String(32),
        default="STAGE_1_UPLOADED",
        nullable=False,
        index=True,
        comment="六阶状态机: STAGE_1_UPLOADED(已上传) | STAGE_2_CLEANED(已解析清洗) | STAGE_3_STRATEGY_SELECTED(已选分块策略) | STAGE_4_CHUNKED(切分完成) | STAGE_5_EMBEDDED(向量入库) | STAGE_6_GRAPH_READY(图谱就绪可用)"
    )
    selected_chunk_strategy: Mapped[str] = mapped_column(
        String(64),
        default="RECURSIVE_CHAR",
        nullable=False,
        comment="采用的切分策略: RECURSIVE_CHAR, PARENT_CHILD, MARKDOWN_HEADER, TABLE_AWARE, SEMANTIC_CLUSTER, SENTENCE_WINDOW, FIXED_OVERLAP"
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="分块生成的切片总数量")
    vector_id_prefix: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="Chroma 向量存储中的集合或命名空间前缀")
    graph_entity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="抽取并写入 Neo4j 的实体节点与三元组关系总数")
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始文档解析清洗后的完整正文内容")
    agent_decision_reason: Mapped[str] = mapped_column(String(500), default="", nullable=False, comment="智能体6A分块决策子智能体选定该切分策略的自主判定理由")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建上传时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="最新推进时间")


class SpdRagChunk(Base):
    """文档切片分块明细表：承载父子块关联与 7 大策略切分数据"""
    __tablename__ = "spd_rag_chunk"
    __table_args__ = {"comment": "文档切片明细表：记录各分块的文本、字符数、策略类型及父子映射关系"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="切片主键ID")
    doc_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="关联的文档主键ID")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="切片在本文档内的顺序索引(从0开始)")
    chunk_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="切片全局唯一标识符(用于Chroma与溯源)")
    parent_chunk_uid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="父块UID(用于父子分块检索Small-to-Big扩展)")
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False, comment="当前切片实际纯文本内容")
    chunk_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="切片字符长度")
    strategy_applied: Mapped[str] = mapped_column(String(64), default="RECURSIVE_CHAR", nullable=False, comment="切分时实际应用的策略算子")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False, comment="切片元数据JSON(章节路径/页码/表格字段/关键词)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="切分生成时间")


class SpdModularRagConfig(Base):
    """Modular RAG 全链路热插拔配置持久化表：实时调控各环节算子开关与参数"""
    __tablename__ = "spd_modular_rag_config"
    __table_args__ = {"comment": "Modular RAG 热插拔全局配置表：支持前台无缝热切换检索前/中/后算子与大模型"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="配置主键ID")
    config_key: Mapped[str] = mapped_column(String(64), unique=True, default="GLOBAL_CONFIG", nullable=False, comment="配置唯一标识")
    # 检索前算子
    enable_intent_classify: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用意图分类分诊: 1-开启, 0-关闭")
    enable_query_rewrite: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用查询重写: 1-开启, 0-关闭")
    max_rewrite_loops: Mapped[int] = mapped_column(Integer, default=3, nullable=False, comment="查询重写最大自省循环轮次上限")
    rewrite_threshold: Mapped[float] = mapped_column(Numeric(4, 2), default=0.85, nullable=False, comment="重写质量达标置信度阈值")
    enable_subquery_decompose: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用复杂多跳子问题拆解: 1-开启, 0-关闭")
    enable_hyde: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否启用HyDE假设文档生成: 1-开启, 0-关闭")
    # 检索中算子
    enable_dense_vector: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用Chroma稠密向量检索: 1-开启, 0-关闭")
    enable_bm25_sparse: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用BM25稀疏关键词检索: 1-开启, 0-关闭")
    enable_graph_rag: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用Neo4j医疗实体关系图谱检索: 1-开启, 0-关闭")
    top_k_retrieval: Mapped[int] = mapped_column(Integer, default=15, nullable=False, comment="多路召回候选段落数量")
    # 检索后算子
    enable_reranker: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用Cross-Encoder交叉重排序: 1-开启, 0-关闭")
    rerank_threshold: Mapped[float] = mapped_column(Numeric(4, 2), default=0.60, nullable=False, comment="重排序最低相关性过滤阈值")
    enable_context_compression: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用上下文冗余压缩: 1-开启, 0-关闭")
    enable_citation_source: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用精准文档引用溯源增强: 1-开启, 0-关闭")
    enable_faithfulness_check: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用真实答案忠实度与幻觉自检: 1-开启, 0-关闭")
    enable_system_grounding: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用系统事实(数据库+知识库)查验优先: 1-开启, 0-关闭")
    default_chunking_mode: Mapped[str] = mapped_column(String(32), default="AGENT_AUTO", nullable=False, comment="默认分块决策引擎模式(AGENT_AUTO / SYSTEM_BUILTIN)")
    # 核心引擎与模型挂载
    active_embedding_model: Mapped[str] = mapped_column(String(64), default="bge-m3:latest", nullable=False, comment="当前启用的向量化嵌入模型(bge-m3:latest / qwen3-embedding:0.6b)")
    active_llm_provider: Mapped[str] = mapped_column(String(32), default="mimo", nullable=False, comment="当前主力大模型供应商(ollama / mimo)")
    active_chat_model: Mapped[str] = mapped_column(String(64), default="qwen3.5:2b", nullable=False, comment="本地主力对话推理模型")
    mimo_base_url: Mapped[str] = mapped_column(String(255), default="https://api.xiaomimimo.com/v1", nullable=False, comment="云端小米MiMo自定义Base URL")
    mimo_model_name: Mapped[str] = mapped_column(String(64), default="mimo-v2.6-flash", nullable=False, comment="云端小米MiMo模型标识")
    mimo_api_key_override: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="云端小米MiMo自定义覆盖API Key(空表示读取环境变量)")
    # 流式传输、深度思考与切分动态调控
    enable_streaming: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用SSE流式输出打字机模式: 1-开启, 0-关闭")
    enable_deep_thinking: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用长思考推理链路: 1-开启, 0-关闭")
    llm_timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False, comment="大模型调用兜底超时上限(秒)")
    default_chunk_size: Mapped[int] = mapped_column(Integer, default=500, nullable=False, comment="知识库文档默认切片字符数")
    default_chunk_overlap: Mapped[int] = mapped_column(Integer, default=80, nullable=False, comment="知识库文档默认重叠字符数")
    # 飞书单聊欢迎卡片频控与开关
    enable_feishu_welcome_card: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用进入单聊自动弹出引导卡片: 1-开启, 0-关闭")
    feishu_welcome_cooldown_hours: Mapped[float] = mapped_column(Numeric(6, 2), default=24.0, nullable=False, comment="飞书引导卡片用户频控冷却时间(小时，如24表示每天仅弹窗1次)")
    # LangSmith 全链路监控配置
    langsmith_enabled: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用LangSmith全流程可观测追踪: 1-开启, 0-关闭")
    langsmith_project: Mapped[str] = mapped_column(String(64), default="Personal", nullable=False, comment="LangSmith 项目名称")
    langsmith_endpoint: Mapped[str] = mapped_column(String(255), default="https://api.smith.langchain.com", nullable=False, comment="LangSmith API 端点")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="配置最新更新时间")


class SpdAgentExecutionTrace(Base):
    """6 大智能体执行轨迹与熔断审计表：全量记录架构行为与 LangSmith 关联 Trace"""
    __tablename__ = "spd_agent_execution_trace"
    __table_args__ = {"comment": "6大智能体执行轨迹表：记录Plan&Execute步骤/Router置信度/ReAct思考链/HITL状态与执行耗时"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="轨迹记录主键ID")
    agent_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="智能体标识(agent_1 到 agent_6)")
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="智能体中文全称")
    architecture_pattern: Mapped[str] = mapped_column(String(64), nullable=False, comment="架构模式(Plan & Execute / Router+Skill / Graph / ReAct / Blackboard / Multi-Agent)")
    operator_account: Mapped[str] = mapped_column(String(64), nullable=False, comment="触发操作的用户账号")
    user_query: Mapped[str] = mapped_column(Text, nullable=False, comment="用户原始提问或业务触发指令")
    structured_output_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False, comment="架构结构化产出JSON(如Plan步骤/Router打分排行/ReAct推理链/HITL确认单)")
    tools_called_summary: Mapped[str] = mapped_column(String(500), default="", nullable=False, comment="本次执行调用的真实工具名称列表摘要")
    final_answer: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="智能体返回给用户的最终结构化或自然语言答案")
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="本次执行总耗时(毫秒)")
    langsmith_run_id: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True, comment="关联的 LangSmith 云端 Run ID (支持点击直跳)")
    is_fallback_triggered: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="是否触发了多级兜底熔断降级: 1-是, 0-否")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="执行记录创建时间")


class SpdAgentModelConfig(Base):
    """6 大智能体独立大模型配置表：支持每个智能体单独解耦或批量配置模型"""
    __tablename__ = "spd_agent_model_config"
    __table_args__ = {"comment": "6大智能体独立大模型解耦配置表：支持单独绑定模型、温度与端点"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="配置主键ID")
    agent_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True, comment="智能体唯一标识(agent_1 到 agent_6)")
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="智能体中文全称")
    model_provider: Mapped[str] = mapped_column(String(32), default="ollama", nullable=False, comment="模型提供商(ollama / mimo)")
    model_name: Mapped[str] = mapped_column(String(64), default="qwen3.5:2b", nullable=False, comment="模型标识名称")
    temperature: Mapped[float] = mapped_column(Numeric(3, 2), default=0.20, nullable=False, comment="模型推理温度(0.0~1.0)")
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False, comment="最大生成 Token 数量上限")
    custom_base_url: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="自定义 API Base URL(空表示默认)")
    custom_api_key_masked: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="脱敏 API Key 显示(如 mimo_****)")
    custom_api_key_encrypted: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="受保护的 API Key 密文存储")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")


class SpdAgentChatMessage(Base):
    """智能体多轮对话持久化记忆表：记录主从智能体会话历史、多模态图片、思考链与工具调用"""
    __tablename__ = "spd_agent_chat_message"
    __table_args__ = {"comment": "智能体多轮对话持久化记录表：支持独立会话历史、OpenClaw工具卡片与思考链回溯"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="消息自增主键ID")
    agent_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="关联智能体标识(agent_1 到 agent_6)")
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="会话唯一SessionID")
    role: Mapped[str] = mapped_column(String(32), nullable=False, comment="发送方角色(user / agent / sub_agent)")
    sub_agent_name: Mapped[str] = mapped_column(String(64), default="", nullable=False, comment="子智能体名称(如: query_rewriter / data_chunker)")
    content: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="自然语言正文内容")
    thought_process: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="DeepSeek风格think思考链内容")
    tool_calls_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False, comment="OpenClaw风格工具调用入参出参JSON")
    image_url: Mapped[str] = mapped_column(String(500), default="", nullable=False, comment="多模态识图上传图片相对或绝对路径")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="消息产生时间")

