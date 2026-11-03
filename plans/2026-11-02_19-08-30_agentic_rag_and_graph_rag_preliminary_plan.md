# Agentic RAG + Graph-RAG 双阶段智能检索与管理员调优评估中心初步规划书

> 归档时间戳：2026-11-02 19:08:30  
> 任务标识符：`agentic_rag_and_graph_rag_preliminary_plan`  
> 实施排期定位：**第二阶段专项计划（待全套 SPD 业务模块完成后立即实施）**

---

## 一、 整体架构定位

本计划书旨在将医院医疗物资管理系统中的 5 大业务智能体知识底座升级为工业级 **Agentic RAG + Graph-RAG 双引擎架构**，划分为**离线知识工程阶段（Offline Pipeline）**、**在线自适应推理阶段（Online Pipeline）**以及**信息科管理员 CRAG 调参及多维评估控制台（Admin Evaluation Console）**。

---

## 二、 离线阶段（Offline Pipeline）：数据清洗 Agent + 递归分块 + Graph-RAG 实体联系文档

### 1. 原始多模态医疗文档上传
- 支持信息科/耗材科/设备科上传：
  - 《国家医疗器械分类目录与编码规范》
  - 《临床手术定数包标准配置与耗材使用说明书》
  - 《医院耗占比内控审计制度与不良事件召回办法》
  - 《供应商准入资质审查规范与冷链验收规程》

### 2. 专职数据清洗智能体（`data_cleaning_agent`）
- 在分块前引入专门的清洗 Agent 节点，执行 4 项标准化清洗：
  1. **噪点剥离**：自动剔除 PDF/Word 页眉页脚、水印、乱码字符与冗余空行；
  2. **医疗表格结构化**：将跨页耗材规格参数表转换为高可读性的标准 Markdown 表格；
  3. **术语归一化**：将俗称（如“骨水泥”、“留置针”）关联至国械注准标准通用名；
  4. **隐私脱敏**：自动遵循 Skill 04 脱敏历史案例中的患者姓名、住院号与手机号。

### 3. 可配置递归分块与双库向量化（Chroma）
- 默认采用**递归字符分块器（`RecursiveCharacterTextSplitter`）**，默认 `chunk_size=500`、`chunk_overlap=80`（支持在管理员端动态调整并触发重建索引）；
- 通过 Embedding 模型向量化后持久化存入本地 Chroma 向量库。

### 4. Graph-RAG 医疗实体联系文档与知识图谱构建
- 自动生成并维护结构化的 **《医疗物资 Graph-RAG 实体联系文档》** 与 MySQL 知识图谱三元组表（`spd_knowledge_graph_triple`）：
  - **核心实体类型（Nodes）**：`[产品字典/规格]`、`[耗材分类]`、`[所属仓库/科室]`、`[供应商]`、`[医疗器械注册证]`、`[临床术式/定数包]`；
  - **核心关系类型（Edges）**：`BELONGS_TO_CATEGORY（属于分类）`、`STORED_IN_WAREHOUSE（存放于仓库）`、`SUPPLIED_BY（由供应商供货）`、`USED_IN_SURGERY（适用于手术/科室）`、`GOVERNED_BY_CERT（受注册证监管）`。

---

## 三、 在线阶段（Online Pipeline）：意图判别 + 混合检索重排 + Self-RAG 四部曲 + CRAG

### 1. 用户提问与前置语义路由
- **意图判别（Intent Classification）**：自动识别用户问题是属于“业务数据库实时查询（走 MCP SQL 工具）”、“医疗法规/说明书问答（走 RAG）”还是“复合型业务审查（MCP + RAG 联合调用）”；
- **查询重写（Query Rewriting）**：将口语化提问重写为包含医疗专业术语、耗材编码或扩充子查询的多路检索词。

### 2. 三路混合检索 + 重排序（Rerank）+ 精排序
1. **混合检索（Hybrid Retrieval）**：
   - 第 1 路：Chroma 稠密向量语义检索（Dense Retrieval）；
   - 第 2 路：BM25 稀疏关键词精准匹配（针对国械注准号、UDI 码、产品代码、批号）；
   - 第 3 路：Graph-RAG 实体一度/二度邻居子图关联检索；
2. **重排序（Cross-Encoder Rerank）与精排序**：
   - 对三路召回的 Top-K 候选文档块进行交叉注意力打分重排，过滤低分冗余块，按相关性精排后注入上下文窗口。

### 3. Self-RAG 四部曲自省闭环与 CRAG 纠偏
- **Step 1 - 检索必要性判定（Retrieve）**：评估当前问题是否需要外部医疗知识证据；
- **Step 2 - 检索片段相关性评估（ISREL）+ CRAG 纠偏**：
  - 对召回文档进行相关性打分（`Correct` / `Ambiguous` / `Incorrect`）；
  - 若触发 `Incorrect` 或低于管理员设定的 CRAG 阈值，自动启动 **CRAG（Corrective RAG）** 机制：触发二次查询重写或扩大知识图谱跳跃半径重新检索；
- **Step 3 - 生成事实支撑度自检（ISSUP）**：校验大模型生成的每一句结论是否完全由检索到的医疗规范或数据库快照支撑（严防幻觉）；
- **Step 4 - 答案实用性评估（ISUSE）**：检验最终输出是否完整解答了医护或管理人员的业务诉求。

---

## 四、 信息科管理员端：CRAG 参数调优与多维量化评估大盘

在信息科系统管理员（`sys_admin`）工作台中，设立独立的 **“Agentic RAG 调优与质量评估中心”**：

### 1. 管理员在线可调参数（CRAG & Pipeline Config）
- 分块策略参数：`chunk_size`、`chunk_overlap`、分块器类型切换；
- 混合检索权重：`Vector 权重` vs `BM25 权重` vs `Graph-RAG 图谱权重`、`Top-K 召回数`；
- CRAG 与 Self-RAG 阈值：相关性拦截阈值（`isrel_threshold`）、最大自动重写纠偏次数、幻觉重生成开关。

### 2. 六大核心量化评估指标（RAG Evaluation Metrics）
每次问答及批量基准测试后，系统自动计算并持久化以下 6 项核心指标：
1. **召回率（Recall@K）**：标准答案所需的核心医疗知识片段在 Top-K 检索结果中被成功召回的比例；
2. **上下文精确率（Context Precision / MRR）**：高相关文档块排在检索结果前列的排序质量；
3. **忠诚度（Faithfulness / Loyalty）**：生成答案与检索到的医疗规范/数据库事实的一致程度（反幻觉指标，0~100%）；
4. **可信度（Credibility / Confidence）**：引用证据链的权威等级（国械注准官方目录 > 院内制度 > 一般说明）与多源交叉印证得分；
5. **准确性（Answer Accuracy / Relevance）**：最终回答与用户问题意图及标准医疗业务逻辑的吻合度；
6. **端到端响应耗时与纠偏率（Latency & CRAG Trigger Rate）**：检索耗时、重排耗时、生成耗时及 CRAG 触发回退比例。
