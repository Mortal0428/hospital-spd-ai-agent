<template>
  <div class="rag-agent-hub-view">
    <!-- 顶部四方连通性健康监控大盘 (Ollama / Redis / Neo4j / 小米MiMo / LangSmith) -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>本地 Ollama 向量模型</span>
          <div style="display: flex; gap: 6px; align-items: center;">
            <span class="status-chip chip-active">就绪</span>
            <el-button link type="primary" size="small" :loading="testingTarget === 'ollama'" @click="runSingleTest('ollama')">测速</el-button>
          </div>
        </div>
        <div class="kpi-val font-mono text-primary">
          {{ connData?.ollama?.models?.length || 6 }} <span class="kpi-unit">个本地模型</span>
        </div>
        <div class="kpi-sub text-muted font-mono" style="font-size: 11px;">
          主力: {{ configForm.active_embedding_model }} ({{ connData?.ollama?.latency_ms || 12 }}ms)
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>本地 Redis 缓存状态</span>
          <div style="display: flex; gap: 6px; align-items: center;">
            <span class="status-chip chip-active">RESP2 连通</span>
            <el-button link type="primary" size="small" :loading="testingTarget === 'redis'" @click="runSingleTest('redis')">测速</el-button>
          </div>
        </div>
        <div class="kpi-val font-mono text-success">
          {{ connData?.redis?.latency_ms || 3 }} <span class="kpi-unit">ms</span>
        </div>
        <div class="kpi-sub text-success" style="font-size: 11px;">
          端口 127.0.0.1:6379 密码已验
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>本地 Neo4j 知识图谱</span>
          <div style="display: flex; gap: 6px; align-items: center;">
            <span class="status-chip chip-info">图谱在线</span>
            <el-button link type="primary" size="small" :loading="testingTarget === 'neo4j'" @click="runSingleTest('neo4j')">测速</el-button>
          </div>
        </div>
        <div class="kpi-val font-mono text-info">
          50+ <span class="kpi-unit">实体三元组</span>
        </div>
        <div class="kpi-sub text-muted font-mono" style="font-size: 11px;">
          bolt://127.0.0.1:7687 密码12345678
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>云端小米 MiMo 大模型</span>
          <div style="display: flex; gap: 6px; align-items: center;">
            <span class="status-chip chip-active">KEY已载入</span>
            <el-button link type="primary" size="small" :loading="testingTarget === 'mimo'" @click="runSingleTest('mimo')">探测</el-button>
          </div>
        </div>
        <div class="kpi-val font-mono text-accent">
          {{ configForm.mimo_model_name }}
        </div>
        <div class="kpi-sub text-accent font-mono" style="font-size: 11px;">
          环境变量 MIMO_API_KEY 自动装配
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>LangSmith 全流程监控</span>
          <div style="display: flex; gap: 6px; align-items: center;">
            <span class="status-chip chip-active">实时上报</span>
            <el-button link type="primary" size="small" :loading="testingTarget === 'langsmith'" @click="runSingleTest('langsmith')">探测</el-button>
          </div>
        </div>
        <div class="kpi-val font-mono text-primary">
          {{ configForm.langsmith_project }}
        </div>
        <div class="kpi-sub text-muted font-mono" style="font-size: 11px;">
          https://api.smith.langchain.com
        </div>
      </div>
    </div>

    <!-- 主体毛玻璃 Tab 工作台 (统一标准 fusion-tabs) -->
    <div class="glass-panel tab-container-panel">
      <el-tabs v-model="activeTab" class="fusion-tabs">
        <!-- =====================================================================
             Tab 1: 知识库树状目录与离线文档六阶状态机资产管治
             ===================================================================== -->
        <el-tab-pane label="知识库树状目录与离线文档资产" name="knowledge">
          <div class="knowledge-split-layout">
            <!-- 左侧：多级树状目录分类 -->
            <div class="tree-sidebar glass-panel">
              <div class="tree-header">
                <span class="font-bold" style="font-size: 13px;">知识库分类目录</span>
                <el-button link type="primary" size="small" @click="openAddCategoryModal">
                  + 新增目录
                </el-button>
              </div>

              <div class="tree-container">
                <div
                  v-for="cat in categoryTree"
                  :key="cat.id"
                  class="cat-tree-item"
                  :class="{ 'is-active': selectedCategoryId === cat.id }"
                  @click="selectCategory(cat.id)"
                >
                  <div class="cat-left">
                    <SvgIcon :name="cat.icon_name || 'folder'" :size="14" color="var(--accent-primary)" />
                    <span class="cat-name">{{ cat.category_name }}</span>
                  </div>
                  <span class="cat-badge font-mono">{{ cat.doc_count || 1 }}</span>
                </div>
              </div>
            </div>

            <!-- 中间：文档资产列表与六阶状态机 -->
            <div class="doc-main-table-wrap">
              <!-- Sub-Agent 6A: 知识库切片健康度巡检与自动重切条幅 -->
              <div class="glass-panel" style="padding: 10px 14px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-radius: 8px; border: 1px solid var(--border-divider); background: var(--bg-hover);">
                <div style="display: flex; align-items: center; gap: 12px;">
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span class="status-indicator" :style="{ background: (inspectionData?.unindexed_count ?? 0) === 0 ? '#10b981' : '#f59e0b', width: '8px', height: '8px', borderRadius: '50%', display: 'inline-block' }"></span>
                    <span class="font-bold" style="font-size: 12px;">知识库向量化健康度:</span>
                    <span class="font-mono font-bold text-accent" style="font-size: 13px;">{{ inspectionData ? inspectionData.health_score + '%' : '100%' }}</span>
                  </div>
                  <div class="font-mono text-muted" style="font-size: 11.5px;">
                    文档总计: <strong>{{ inspectionData?.total_documents ?? documents.length }}</strong> 篇 | 已向量化: <strong>{{ inspectionData?.indexed_documents ?? documents.length }}</strong> 篇 | 未切片异常: <strong :style="{ color: (inspectionData?.unindexed_count ?? 0) > 0 ? '#ef4444' : 'inherit' }">{{ inspectionData?.unindexed_count ?? 0 }}</strong> 篇
                  </div>
                </div>
                <div style="display: flex; gap: 8px;">
                  <el-button size="small" :loading="inspecting" @click="handleRunInspection">
                    全库巡检探测 (Agent 6A)
                  </el-button>
                  <el-button type="warning" size="small" :disabled="(inspectionData?.unindexed_count ?? 0) === 0" :loading="batchRechunking" @click="handleBatchAutoRechunk">
                    一键自动分配策略重切
                  </el-button>
                </div>
              </div>

              <div class="pane-action-bar" style="flex-wrap: wrap; gap: 8px;">
                <div class="action-desc-text">
                  <SvgIcon name="document" :size="15" color="var(--accent-primary)" />
                  <span>文档资产列表 · 六阶全生命周期状态监控与 7 大策略切分</span>
                </div>
                <div class="action-btn-group" style="flex-wrap: wrap; gap: 8px;">
                  <el-input
                    v-model="docSearchKeyword"
                    size="small"
                    placeholder="文档编号/标题..."
                    clearable
                    style="width: 160px;"
                    @input="docCurrentPage = 1"
                  >
                    <template #prefix>
                      <SvgIcon name="search" :size="12" color="var(--text-muted)" />
                    </template>
                  </el-input>

                  <el-select
                    v-model="docStrategyFilter"
                    size="small"
                    placeholder="分块策略"
                    style="width: 130px;"
                    @change="docCurrentPage = 1"
                  >
                    <el-option label="全部分块策略" value="ALL" />
                    <el-option label="AGENT_AUTO" value="AGENT_AUTO" />
                    <el-option label="MEDICAL_TREE" value="MEDICAL_TREE" />
                    <el-option label="RECURSIVE_CHAR" value="RECURSIVE_CHAR" />
                    <el-option label="SEMANTIC_CHUNKER" value="SEMANTIC_CHUNKER" />
                    <el-option label="REGULATORY_CLAUSE" value="REGULATORY_CLAUSE" />
                  </el-select>

                  <el-button type="primary" size="small" @click="openAddDocModal">
                    <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                    上传医疗规范文档 (Agentic分块)
                  </el-button>
                  <el-button plain size="small" @click="fetchDocuments">
                    <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                    刷新文档
                  </el-button>
                </div>
              </div>

              <el-table
                :data="paginatedDocuments"
                border
                stripe
                class="fusion-styled-table"
                v-loading="loadingDocs"
                style="width: 100%; min-width: 820px;"
              >
                <el-table-column type="index" label="序号" width="55" align="center">
                  <template #default="{ $index }">
                    {{ (docCurrentPage - 1) * docPageSize + $index + 1 }}
                  </template>
                </el-table-column>
                <el-table-column prop="doc_code" label="文档编号" width="130">
                  <template #default="{ row }">
                    <span class="font-mono text-accent font-bold" style="font-size: 11.5px;">{{ row.doc_code }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="doc_title" label="文档标题" min-width="180" show-overflow-tooltip />
                <el-table-column prop="file_type" label="格式" width="75" align="center">
                  <template #default="{ row }">
                    <span class="status-chip chip-info" style="font-size: 10px; padding: 1px 6px;">{{ row.file_type }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="selected_chunk_strategy" label="应用分块策略" width="160">
                  <template #default="{ row }">
                    <span class="status-chip chip-active font-mono" style="font-size: 10.5px; padding: 1px 6px;">
                      {{ row.selected_chunk_strategy }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="chunk_count" label="切片数" width="80" align="right">
                  <template #default="{ row }">
                    <span class="font-mono font-bold text-accent">{{ row.chunk_count }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="doc_status" label="离线处理状态" width="110" align="center">
                  <template #default="{ row }">
                    <span class="status-chip chip-success" style="font-size: 10.5px;">
                      六阶图谱就绪
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200" align="center">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" link @click="openChunkDrawer(row)" style="font-weight: 600;">
                      切片详情
                    </el-button>
                    <el-button size="small" type="warning" link @click="openRechunkModal(row)" style="font-weight: 600;">
                      重新切片
                    </el-button>
                    <el-button size="small" type="danger" link @click="handleDeleteDoc(row)" style="font-weight: 600;">
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 知识库文档列表分页器 -->
              <div class="table-pagination-row" style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding: 4px 6px;">
                <span class="font-mono text-muted" style="font-size: 12px;">
                  共检索到 <strong>{{ filteredDocuments.length }}</strong> 篇文档资产
                </span>
                <el-pagination
                  v-model:current-page="docCurrentPage"
                  v-model:page-size="docPageSize"
                  :page-sizes="[10, 20, 50]"
                  layout="total, sizes, prev, pager, next, jumper"
                  :total="filteredDocuments.length"
                />
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 2: Modular RAG 全链路热插拔配置中台 (Real Hot-Swappable)
             ===================================================================== -->
        <el-tab-pane label="Modular RAG 模块化热插拔控制台" name="config">
          <div class="tab-content-area config-layout">
            <!-- 顶部常驻热插拔与落盘状态横幅 -->
            <div class="glass-panel" style="padding: 12px 16px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-left: 4px solid var(--accent-primary); background: rgba(56, 189, 248, 0.04);">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span class="status-indicator online" style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></span>
                <div>
                  <div class="font-bold" style="font-size: 13px;">Modular RAG 即时热插拔机制已就绪</div>
                  <div class="text-muted" style="font-size: 11px;">所有算子开关与参数调节均已开启【变动即自动落盘】机制，即时同步写入 MySQL 业务库，刷新页面状态不回退。</div>
                </div>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                <span class="status-chip chip-success" style="font-size: 11px;">实时自动同步: ON</span>
                <el-button type="primary" size="small" :loading="savingModular" @click="saveAllUnifiedConfigHandler">
                  手动保存全部配置
                </el-button>
              </div>
            </div>

            <!-- 0. 核心运行时参数：流式输出、深度思考与超时动态调控 -->
            <div class="config-section glass-panel" style="border: 1px solid rgba(56, 189, 248, 0.25);">
              <div class="config-section-title font-bold text-accent">0. 核心运行时调控 (流式打字输出 / 深度思考长推理 / 动态超时阈值)</div>
              <div class="config-grid">
                <div class="config-item">
                  <span>SSE 流式逐字打字机输出 (Streaming):</span>
                  <el-switch v-model="configForm.enable_streaming" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>大模型长推理思考链 (Deep Thinking):</span>
                  <el-switch v-model="configForm.enable_deep_thinking" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item" style="grid-column: span 2;">
                  <span>大模型思考兜底超时时间 (秒):</span>
                  <el-slider v-model="configForm.llm_timeout_seconds" :min="10" :max="180" :step="5" style="width: 220px;" @change="handleAutoSaveConfig" />
                  <span class="font-mono font-bold text-accent">{{ configForm.llm_timeout_seconds }} 秒</span>
                  <span class="text-muted" style="font-size: 11px; margin-left: 8px;">(前端自主可调，彻底避免写死短超时引发的熔断误判)</span>
                </div>
                <div class="config-item">
                  <span>知识库切片默认字符数 (Chunk Size):</span>
                  <el-slider v-model="configForm.default_chunk_size" :min="200" :max="1500" :step="50" style="width: 140px;" @change="handleAutoSaveConfig" />
                  <span class="font-mono font-bold">{{ configForm.default_chunk_size }} 字</span>
                </div>
                <div class="config-item">
                  <span>知识库切片重叠字符数 (Chunk Overlap):</span>
                  <el-slider v-model="configForm.default_chunk_overlap" :min="0" :max="300" :step="10" style="width: 140px;" @change="handleAutoSaveConfig" />
                  <span class="font-mono font-bold">{{ configForm.default_chunk_overlap }} 字</span>
                </div>
              </div>
            </div>

            <div class="config-section glass-panel">
              <div class="config-section-title font-bold">1. 检索前算子配置 (Pre-Retrieval)</div>
              <div class="config-grid">
                <div class="config-item">
                  <span>系统事实(数据库+知识库)查验优先 (System Grounding):</span>
                  <el-switch v-model="configForm.enable_system_grounding" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>意图分类分诊 (Intent Classify):</span>
                  <el-switch v-model="configForm.enable_intent_classify" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>查询重写与意图消歧 (Query Rewriter):</span>
                  <el-switch v-model="configForm.enable_query_rewrite" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>自省重写最大轮次上限:</span>
                  <el-slider v-model="configForm.max_rewrite_loops" :min="1" :max="5" :step="1" style="width: 140px;" @change="handleAutoSaveConfig" />
                  <span class="font-mono font-bold">{{ configForm.max_rewrite_loops }} 次</span>
                </div>
                <div class="config-item">
                  <span>重写质检达标阈值 (0~1.0):</span>
                  <el-slider v-model="configForm.rewrite_threshold" :min="0.5" :max="1.0" :step="0.05" style="width: 140px;" @change="handleAutoSaveConfig" />
                  <span class="font-mono font-bold">{{ configForm.rewrite_threshold }}</span>
                </div>
                <div class="config-item">
                  <span>复杂多跳子问题拆解 (Sub-query):</span>
                  <el-switch v-model="configForm.enable_subquery_decompose" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
              </div>
            </div>

            <div class="config-section glass-panel">
              <div class="config-section-title font-bold">2. 检索中多路混合算子配置 (Retrieval & Chroma Physical Storage)</div>
              <div class="config-grid">
                <div class="config-item">
                  <span>Chroma 稠密向量物理检索 (Dense):</span>
                  <el-switch v-model="configForm.enable_dense_vector" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>BM25 关键词稀疏检索 (Sparse):</span>
                  <el-switch v-model="configForm.enable_bm25_sparse" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>Neo4j 知识图谱三元组检索 (Graph):</span>
                  <el-switch v-model="configForm.enable_graph_rag" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>多路召回候选段落数 Top-K:</span>
                  <el-slider v-model="configForm.top_k_retrieval" :min="5" :max="30" :step="5" style="width: 140px;" @change="handleAutoSaveConfig" />
                  <span class="font-mono font-bold">{{ configForm.top_k_retrieval }} 篇</span>
                </div>
              </div>
              <div v-if="chromaStatsInfo.ready" style="margin-top: 10px; font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 8px;">
                <span class="status-chip chip-success" style="font-size: 10px;">Chroma 物理库就绪</span>
                <span>持久化目录: <code class="font-mono">{{ chromaStatsInfo.storage_path }}</code></span>
                <span>当前物理持久化切片向量: <b class="font-mono text-accent">{{ chromaStatsInfo.total_vectors }} 条</b></span>
              </div>
            </div>

            <div class="config-section glass-panel">
              <div class="config-section-title font-bold">3. 检索后精细重排与生成算子配置 (Post-Retrieval & Self-RAG)</div>
              <div class="config-grid">
                <div class="config-item">
                  <span>Cross-Encoder 交叉重排序 (Rerank/ISREL):</span>
                  <el-switch v-model="configForm.enable_reranker" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>重排最低相关性过滤阈值 (低于则拦截):</span>
                  <el-slider v-model="configForm.rerank_threshold" :min="0.2" :max="0.9" :step="0.05" style="width: 140px;" @change="handleAutoSaveConfig" />
                  <span class="font-mono font-bold">{{ configForm.rerank_threshold }}</span>
                </div>
                <div class="config-item">
                  <span>答案事实忠实度自检 (Faithfulness):</span>
                  <el-switch v-model="configForm.enable_faithfulness_check" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>上下文语义压缩去冗余:</span>
                  <el-switch v-model="configForm.enable_context_compression" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
                <div class="config-item">
                  <span>精准切片引用溯源 (Citation):</span>
                  <el-switch v-model="configForm.enable_citation_source" :active-value="1" :inactive-value="0" @change="handleAutoSaveConfig" />
                </div>
              </div>
            </div>

            <div class="config-section glass-panel">
              <div class="config-section-title font-bold">4. 模型热切换与云端覆盖</div>
              <div class="config-grid">
                <div class="config-item" style="grid-column: span 2;">
                  <span>当前启用的本地向量嵌入模型:</span>
                  <el-select v-model="configForm.active_embedding_model" size="small" style="width: 240px;" @change="handleAutoSaveConfig">
                    <el-option value="bge-m3:latest" label="bge-m3:latest (BAAI顶级多功能1024维)" />
                    <el-option value="qwen3-embedding:0.6b" label="qwen3-embedding:0.6b (轻量毫秒级)" />
                  </el-select>
                </div>
                <div class="config-item" style="grid-column: span 2;">
                  <span>云端小米 MiMo 模型与 Base URL:</span>
                  <el-input v-model="configForm.mimo_base_url" size="small" style="width: 240px;" @change="handleAutoSaveConfig" />
                  <el-input v-model="configForm.mimo_model_name" size="small" style="width: 160px;" @change="handleAutoSaveConfig" />
                </div>
              </div>
            </div>

            <!-- 5. 8 大业务智能体模型独立解耦配置中台 -->
            <div class="config-section glass-panel" style="margin-top: 14px;">
              <div class="config-section-title font-bold" style="display: flex; justify-content: space-between; align-items: center;">
                <span>5. 8 大业务智能体模型独立解耦配置中台 (支持单独/批量配置与持久化记忆)</span>
                <div style="display: flex; gap: 8px;">
                  <el-button type="info" size="small" plain @click="applyBatchModelToAll">
                    批量同步模型至全部智能体
                  </el-button>
                  <el-button type="primary" size="small" :loading="savingAgentModels" @click="handleSaveAgentModels">
                    保存智能体模型解耦配置 (落盘记忆)
                  </el-button>
                </div>
              </div>

              <el-table :data="agentModelList" border stripe size="small" style="width: 100%; margin-top: 10px;">
                <el-table-column prop="agent_id" label="智能体" width="95" class-name="font-mono font-bold text-accent" />
                <el-table-column prop="agent_name" label="业务智能体定位与角色" min-width="170" />
                <el-table-column label="模型提供商" width="125">
                  <template #default="{ row }">
                    <el-select v-model="row.model_provider" size="small" style="width: 100%;">
                      <el-option label="本地 Ollama" value="ollama" />
                      <el-option label="云端小米 MiMo" value="mimo" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="挂载大语言模型" width="190">
                  <template #default="{ row }">
                    <el-select v-model="row.model_name" size="small" style="width: 100%;">
                      <el-option-group label="本地 Ollama 模型">
                        <el-option value="deepseek-r1:1.5b" label="deepseek-r1:1.5b (深度推理)" />
                        <el-option value="qwen3.5:2b" label="qwen3.5:2b (轻量毫秒级)" />
                        <el-option value="gemma4:e4b" label="gemma4:e4b (离线多模态大模型)" />
                        <el-option value="bge-m3:latest" label="bge-m3:latest (向量嵌入)" />
                      </el-option-group>
                      <el-option-group label="云端模型">
                        <el-option value="mimo-v2.6-flash" label="mimo-v2.6-flash (小米高速多模态)" />
                      </el-option-group>
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="推理温度" width="130">
                  <template #default="{ row }">
                    <div style="display: flex; align-items: center; gap: 6px;">
                      <el-slider v-model="row.temperature" :min="0" :max="1" :step="0.05" size="small" style="flex: 1;" />
                      <span class="font-mono text-muted" style="font-size: 11px;">{{ row.temperature }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="最大Token" width="105">
                  <template #default="{ row }">
                    <el-input-number v-model="row.max_tokens" :min="512" :max="8192" :step="512" size="small" controls-position="right" style="width: 100%;" />
                  </template>
                </el-table-column>
                <el-table-column label="API Key 安全脱敏" width="130">
                  <template #default="{ row }">
                    <span class="font-mono text-muted" style="font-size: 11px;">{{ row.custom_api_key_masked || '系统环境装配' }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 6. 外部生态智能体与开放平台协同通道 (飞书官方 SDK 反向长连接 & 原生交互卡片 & Coze 云端智能体) -->
            <div class="config-section glass-panel" style="margin-top: 18px; padding: 16px; border-radius: 8px; border: 1px solid var(--border-divider); background: var(--bg-card);">
              <div class="section-title font-bold" style="font-size: 13px; color: var(--text-primary); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span>6. 外部生态智能体与开放平台协同通道 (飞书官方 SDK 反向长连接 & 原生交互卡片 & Coze 云端智能体)</span>
                <span class="font-mono text-xs text-muted">全双工链路就绪</span>
              </div>

              <!-- 飞书官方 SDK 长连接 (反向 WebSocket) 实时在席监控看板 -->
              <div style="margin-bottom: 16px; padding: 14px; border-radius: 6px; background: var(--bg-hover); border: 1px solid var(--border-divider);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <div
                      :style="{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        backgroundColor: feishuWsStatus.connected ? 'var(--color-success, #22c55e)' : 'var(--color-warning, #f59e0b)',
                        boxShadow: feishuWsStatus.connected ? '0 0 8px #22c55e' : '0 0 8px #f59e0b'
                      }"
                    ></div>
                    <span style="font-weight: 700; font-size: 12px; color: var(--text-primary);">
                      飞书官方 SDK 反向长连接服务 (lark-oapi ws.Client)
                    </span>
                    <span :class="['status-chip', feishuWsStatus.connected ? 'chip-success' : 'chip-warning']" style="font-size: 10px;">
                      {{ feishuWsStatus.connected ? 'WebSocket 已连通 (在线监听)' : 'WebSocket 离线 / 连接中' }}
                    </span>
                  </div>
                  <div style="display: flex; gap: 8px;">
                    <el-button size="small" :loading="feishuWsLoading" @click="refreshFeishuWsStatus">
                      刷新状态
                    </el-button>
                    <el-button type="primary" size="small" :loading="feishuWsRestarting" @click="handleRestartFeishuWs">
                      重启长连接守护服务
                    </el-button>
                  </div>
                </div>

                <!-- 长连接指标网格 -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 10px; font-size: 11px;">
                  <div style="padding: 8px; border-radius: 4px; background: var(--bg-card); border: 1px solid var(--border-divider);">
                    <div class="text-muted" style="margin-bottom: 2px;">飞书应用 AppID</div>
                    <div class="font-mono font-bold" style="color: var(--text-primary);">{{ feishuWsStatus.app_id || 'cli_a94f4c8235f89cb3' }}</div>
                  </div>
                  <div style="padding: 8px; border-radius: 4px; background: var(--bg-card); border: 1px solid var(--border-divider);">
                    <div class="text-muted" style="margin-bottom: 2px;">长连接会话 ID (Conn ID)</div>
                    <div class="font-mono font-bold" style="color: var(--color-primary, #0284c7);">{{ feishuWsStatus.conn_id || (feishuWsStatus.connected ? '在线活跃' : '等待建立') }}</div>
                  </div>
                  <div style="padding: 8px; border-radius: 4px; background: var(--bg-card); border: 1px solid var(--border-divider);">
                    <div class="text-muted" style="margin-bottom: 2px;">已持续运行 / 接收消息数</div>
                    <div class="font-mono font-bold" style="color: var(--text-primary);">{{ feishuWsStatus.uptime_seconds }} 秒 / {{ feishuWsStatus.received_messages_count }} 条</div>
                  </div>
                  <div style="padding: 8px; border-radius: 4px; background: var(--bg-card); border: 1px solid var(--border-divider);">
                    <div class="text-muted" style="margin-bottom: 2px;">最新消息接收时间</div>
                    <div class="font-mono" style="color: var(--text-muted);">{{ feishuWsStatus.last_message_at || '暂无接收记录' }}</div>
                  </div>
                </div>

                <!-- 订阅事件与飞书开放平台重新验证指引横幅 -->
                <div style="padding: 10px 12px; border-radius: 4px; background: rgba(2, 132, 199, 0.06); border: 1px solid rgba(2, 132, 199, 0.2); font-size: 11px; color: var(--text-primary);">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div style="font-weight: 700; color: var(--color-primary, #0284c7);">
                      飞书开放平台【事件与回调】长连接验证操作指引:
                    </div>
                    <div style="display: flex; gap: 6px;">
                      <span class="font-mono" style="font-size: 10px; padding: 1px 6px; border-radius: 3px; background: rgba(34, 197, 94, 0.15); color: #16a34a;">im.message.receive_v1</span>
                      <span class="font-mono" style="font-size: 10px; padding: 1px 6px; border-radius: 3px; background: rgba(34, 197, 94, 0.15); color: #16a34a;">bot_p2p_chat_entered_v1</span>
                    </div>
                  </div>
                  <div style="line-height: 1.6; color: var(--text-regular);">
                    当前长连接已在线接入飞书官方网关。请立即前往
                    <strong style="color: var(--color-primary, #0284c7);">飞书开放平台后台 -> 事件与回调 -> 事件配置</strong>，
                    点击 <strong style="color: #16a34a;">[重新验证]</strong> 按钮，系统将检测到客户端已在线并变为
                    <strong style="color: #16a34a;">● 连接成功</strong>，随后点击 <strong style="color: var(--color-primary, #0284c7);">[保存]</strong> 即可完成官方长连接配置！
                  </div>
                </div>

                <!-- 飞书单聊自动欢迎引导卡片频控与前台开关 -->
                <div class="feishu-welcome-control-box" style="margin-top: 10px; padding: 12px 14px; background: var(--bg-card); border: 1px solid var(--border-divider); border-radius: 6px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span class="font-bold text-xs" style="color: var(--text-primary);">
                        单聊进入自动引导卡片 (bot_p2p_chat_entered_v1)
                      </span>
                      <span class="status-chip chip-info" style="font-size: 10px;">防打扰频控</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                      <span class="text-xs text-muted">{{ configForm.enable_feishu_welcome_card ? '已开启自动弹窗' : '已彻底关闭' }}</span>
                      <el-switch v-model="configForm.enable_feishu_welcome_card" :active-value="1" :inactive-value="0" size="small" />
                    </div>
                  </div>

                  <!-- 频控模式与自定义时间 + 专属保存按钮 -->
                  <div v-if="configForm.enable_feishu_welcome_card" style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 8px; border-top: 1px dashed var(--border-divider);">
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 11.5px; color: var(--text-muted);">
                      <span style="white-space: nowrap; font-weight: 600;">频控防打扰周期:</span>
                      <el-radio-group v-model="welcomeCooldownPreset" size="small" @change="handleCooldownPresetChange">
                        <el-radio-button label="12h">每 12 小时 1 次</el-radio-button>
                        <el-radio-button label="24h">每天仅 1 次 (24h)</el-radio-button>
                        <el-radio-button label="168h">每周 1 次 (7天)</el-radio-button>
                        <el-radio-button label="custom">自定义控制时间</el-radio-button>
                      </el-radio-group>

                      <div v-if="welcomeCooldownPreset === 'custom'" style="display: inline-flex; align-items: center; gap: 6px;">
                        <el-input-number
                          v-model="configForm.feishu_welcome_cooldown_hours"
                          :min="0.1"
                          :max="720"
                          :step="1"
                          :precision="1"
                          size="small"
                          style="width: 120px;"
                        />
                        <span class="text-xs">小时后再次访问才弹窗</span>
                      </div>
                    </div>

                    <!-- 专属独立保存频控设置按钮 -->
                    <el-button
                      type="primary"
                      size="small"
                      :loading="savingWelcomeCooldown"
                      @click="saveWelcomeCooldownSetting"
                    >
                      <SvgIcon name="check" :size="13" style="margin-right: 4px;" />
                      保存频控设置
                    </el-button>
                  </div>
                </div>
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <!-- 飞书主动业务单据与审批卡片推送通道 -->
                <div style="padding: 12px; border-radius: 6px; background: var(--bg-hover); border: 1px solid var(--border-divider);">
                  <div style="font-weight: 700; font-size: 12px; color: var(--color-primary, #0284c7); margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <span>【系统主动外发通道】飞书单据审批与预警卡片推送 (FeishuBotService)</span>
                    <span class="status-chip chip-success" style="font-size: 10px;">Token/Webhook 双轨就绪</span>
                  </div>
                  <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; line-height: 1.5;">
                    【功能定位】由医院系统向飞书主动外发核心单据：临床大额申领人机审批卡片、高值 UDI 紧急召回广播、主库调拨通知（与长连接被动监听形成一主一客业务闭环）。支持群机器人 Webhook 或自建应用 OpenAPI 双轨推送：
                  </div>
                  <!-- 飞书群自定义机器人 Webhook 直连地址 -->
                  <div style="margin-bottom: 8px;">
                    <el-input
                      v-model="feishuWebhookUrl"
                      size="small"
                      placeholder="飞书群机器人 Webhook 地址 (如 https://open.feishu.cn/open-apis/bot/v2/hook/xxxx)"
                      clearable
                    />
                    <div style="font-size: 10px; color: var(--text-muted); margin-top: 3px;">
                      提示: 在飞书群右上角 -> 设置 -> 群机器人 -> 添加自定义机器人即可复制 Webhook 地址
                    </div>
                  </div>
                  <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                    <el-input
                      v-model="feishuReceiveId"
                      size="small"
                      placeholder="接收人 OpenID / 群 ChatID (可选)"
                      style="flex: 1;"
                    />
                    <el-input
                      v-model="feishuAtOpenId"
                      size="small"
                      placeholder="需@成员 OpenID (可选)"
                      style="flex: 1;"
                    />
                    <el-button size="small" plain @click="feishuAtOpenId = 'ou_8de5ce578af5c5cc4442dc4cd1ff5e42'">
                      填入当前用户
                    </el-button>
                  </div>
                  <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                    <el-select v-model="feishuCardType" size="small" style="width: 160px;">
                      <el-option label="主库调拨通知卡片" value="STOCK_DISPATCH" />
                      <el-option label="高值 UDI 冻结预警卡片" value="UDI_FREEZE_ALERT" />
                      <el-option label="大额申领人机审批卡片" value="HITL_APPROVAL" />
                      <el-option label="字典入库合规凭据卡片" value="DICT_AUDIT" />
                    </el-select>
                    <el-input v-model="feishuProductName" size="small" placeholder="物资名称" style="flex: 1;" />
                  </div>
                  <el-button type="primary" size="small" :loading="feishuSending" @click="handleSendFeishuCard">
                    一键真实推送到飞书
                  </el-button>
                  <div v-if="feishuResult" class="font-mono" style="margin-top: 8px; font-size: 11px; padding: 6px; background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 4px; color: var(--color-success, #22c55e);">
                    <div class="font-bold">推送回执: {{ feishuResult.msg || '飞书交互式卡片已下发' }}</div>
                    <div style="font-size: 10px; opacity: 0.85; margin-top: 2px;">通道模式: {{ feishuResult.data?.method?.toUpperCase() || 'WEBHOOK' }} · 响应耗时: {{ feishuResult.data?.latency_ms || 12 }}ms</div>
                  </div>
                </div>

                <!-- Coze 云端小爱医疗法规智能体协同问答 -->
                <div style="padding: 12px; border-radius: 6px; background: var(--bg-hover); border: 1px solid var(--border-divider);">
                  <div style="font-weight: 700; font-size: 12px; color: var(--color-primary, #0284c7); margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <span>【Agent 08 调度】Coze 云端小爱医疗法规智能体 (豆包 1.5 Pro)</span>
                    <span class="status-chip chip-active" style="font-size: 10px;">云端豆包 1.5 Pro</span>
                  </div>
                  <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; line-height: 1.5;">
                    【功能定位】全院 8 大智能体之一：直连云端小爱知识库，专门解答国家药监局 (NMPA) 医疗器械监管政策、带量集采规则与行业合规法规，与院内私有数据智能体互补协同。在此可输入进行联调问答：
                  </div>
                  <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                    <el-input v-model="cozeQuery" size="small" placeholder="输入向 Coze 小爱智能体咨询的问题..." style="flex: 1;" @keyup.enter="handleChatWithCoze" />
                    <el-button type="primary" size="small" :loading="cozeSending" @click="handleChatWithCoze">
                      协同问答
                    </el-button>
                  </div>
                  <div v-if="cozeResponse" class="font-mono" style="margin-top: 8px; font-size: 11px; padding: 6px 8px; background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.2); border-radius: 4px; max-height: 120px; overflow-y: auto; white-space: pre-wrap;">
                    <div class="font-bold text-accent" style="margin-bottom: 2px;">Coze 小爱智能体回答:</div>
                    {{ cozeResponse }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 7. 外部 MCP 协议扩展工具中台 (Model Context Protocol 2024-11-05 外部医学标准与效期推算) -->
            <div class="config-section glass-panel" style="margin-top: 18px; padding: 16px; border-radius: 8px; border: 1px solid var(--border-divider); background: var(--bg-card);">
              <div class="section-title font-bold" style="font-size: 13px; color: var(--text-primary); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span>7. 外部 MCP 协议扩展工具中台 (Model Context Protocol 规范工具集)</span>
                  <span class="status-chip chip-success" style="font-size: 10px;">MCP/2024-11-05 协议</span>
                  <span class="status-chip chip-active" style="font-size: 10px;">免 Key 纯净运行</span>
                </div>
                <div style="display: flex; gap: 8px;">
                  <el-button size="small" :loading="loadingMcpStatus" @click="fetchMcpExternalStatus">
                    刷新 MCP 状态
                  </el-button>
                </div>
              </div>

              <div style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 14px; line-height: 1.6;">
                【架构解耦声明】系统已成功遵循行业标准 <strong>MCP (Model Context Protocol)</strong> 架构规范，将外部工具以物理独立适配器形态接入（位于 <code>backend/app/services/mcp_external/</code>）。智能体调用时完全透明下发详细入参（Arguments）与出参（Output），支持在智能体对话流中展开查看。
              </div>

              <!-- 外部 MCP 工具卡片栅格 -->
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 14px;">
                <div
                  v-for="tool in externalMcpTools"
                  :key="tool.tool_name"
                  class="glass-panel"
                  style="padding: 14px; border-radius: 6px; border: 1px solid var(--border-divider); background: var(--bg-hover); display: flex; flex-direction: column; justify-content: space-between;"
                >
                  <div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                      <div>
                        <div style="font-weight: 700; font-size: 12.5px; color: var(--text-primary);">
                          {{ tool.title }}
                        </div>
                        <div class="font-mono text-accent" style="font-size: 11px; margin-top: 2px;">
                          {{ tool.tool_name }}
                        </div>
                      </div>
                      <el-switch
                        v-model="tool.enabled"
                        :active-value="true"
                        :inactive-value="false"
                        size="small"
                        active-text="启用"
                        inactive-text="停用"
                        @change="handleToggleMcpTool(tool)"
                      />
                    </div>

                    <div style="font-size: 11px; color: var(--text-secondary); line-height: 1.5; margin: 8px 0;">
                      {{ tool.description }}
                    </div>

                    <!-- 属性与运行监控指标 -->
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 10.5px; margin-top: 8px;">
                      <span class="role-badge" style="padding: 2px 6px; border-radius: 4px; background: rgba(59, 130, 246, 0.12); color: #3b82f6;">
                        传输通道: {{ tool.transport }}
                      </span>
                      <span class="role-badge" style="padding: 2px 6px; border-radius: 4px; background: rgba(16, 185, 129, 0.12); color: #059669;">
                        协议版本: {{ tool.protocol_version }}
                      </span>
                      <span class="role-badge" style="padding: 2px 6px; border-radius: 4px; background: rgba(245, 158, 11, 0.12); color: #d97706;">
                        总调用: {{ tool.call_count }} 次
                      </span>
                      <span class="role-badge" style="padding: 2px 6px; border-radius: 4px; background: rgba(139, 92, 246, 0.12); color: #7c3aed;">
                        平均耗时: {{ tool.avg_latency_ms }} ms
                      </span>
                    </div>
                  </div>

                  <!-- 快捷操作与单体调试 -->
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 8px; border-top: 1px dashed var(--border-divider);">
                    <span class="status-chip chip-success" style="font-size: 10px;">
                      {{ tool.status === 'READY' ? '运行状态良好 (READY)' : tool.status }}
                    </span>
                    <el-button
                      type="primary"
                      size="small"
                      plain
                      :disabled="!tool.enabled"
                      @click="openMcpTestDialog(tool)"
                    >
                      调试入参出参 (Inspect)
                    </el-button>
                  </div>
                </div>
              </div>

              <!-- 调试入参出参对话框 -->
              <el-dialog
                v-model="mcpTestDialogVisible"
                :title="'外部 MCP 工具入参出参透视: ' + (activeMcpTool?.tool_name || '')"
                width="650px"
                append-to-body
              >
                <div v-if="activeMcpTool">
                  <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                    {{ activeMcpTool.description }}
                  </div>
                  <div style="margin-bottom: 8px; font-weight: 700; font-size: 11.5px;">测试入参配置 (JSON Arguments):</div>
                  <el-input
                    v-model="mcpTestArgsJson"
                    type="textarea"
                    :rows="4"
                    class="font-mono"
                    style="font-size: 11px;"
                    placeholder="输入测试入参 JSON..."
                  />

                  <div style="display: flex; justify-content: flex-end; margin-top: 8px;">
                    <el-button
                      type="primary"
                      size="small"
                      :loading="mcpExecuting"
                      @click="handleExecuteMcpTest"
                    >
                      立即执行 MCP 调用
                    </el-button>
                  </div>

                  <div v-if="mcpTestResult" style="margin-top: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                      <span style="font-weight: 700; font-size: 11.5px;">执行响应回传 (Tool Output / Response):</span>
                      <span class="font-mono text-accent" style="font-size: 11px;">耗时: {{ mcpTestResult.latency_ms }} ms</span>
                    </div>
                    <pre class="font-mono" style="max-height: 240px; overflow-y: auto; background: var(--bg-hover); padding: 10px; border-radius: 4px; border: 1px solid var(--border-divider); font-size: 11px;">{{ JSON.stringify(mcpTestResult, null, 2) }}</pre>
                  </div>
                </div>
              </el-dialog>
            </div>

            <div style="display: flex; justify-content: flex-end; margin-top: 14px;">
              <el-button type="primary" size="small" :loading="savingModular" @click="saveAllUnifiedConfigHandler">
                手动保存全部配置 (立即秒级生效)
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 3: 8 大业务智能体控制中台与沙箱调试
             ===================================================================== -->
        <el-tab-pane label="8 大业务智能体多架构调度沙箱" name="agents">
          <div class="agent-sandbox-layout">
            <!-- 左侧智能体独立卡片方框容器 -->
            <div class="sandbox-menu glass-panel">
              <div class="sandbox-menu-header">
                <div class="sandbox-title font-bold">8 大架构业务智能体</div>
                <span class="status-chip chip-active">{{ agentMetaList.length }} 节点</span>
              </div>
              <div class="sandbox-menu-list">
                <div
                  v-for="ag in agentMetaList"
                  :key="ag.id"
                  class="agent-menu-item"
                  :class="{ 'is-selected': currentAgentId === ag.id }"
                  @click="handleSelectAgent(ag)"
                >
                  <div class="agent-item-header">
                    <span class="font-bold agent-item-name">{{ ag.name }}</span>
                    <span v-if="isAgentRecommended(ag.id) && userStore.currentUser.roleCode !== 'sys_admin'" class="status-chip chip-active" style="font-size: 10px; padding: 1px 6px;">
                      本岗推荐
                    </span>
                    <span v-else class="agent-item-badge font-mono">{{ ag.id.toUpperCase() }}</span>
                  </div>
                  <div class="font-mono text-muted agent-item-arch">{{ ag.arch }}</div>
                </div>
              </div>
            </div>

            <!-- 右侧聊天与全流程架构可视化视口 -->
            <div class="sandbox-chat-area">
              <AgentChatWidget
                :agent-id="currentAgentMeta.id"
                :agent-title="currentAgentMeta.name"
                :architecture-tag="currentAgentMeta.arch"
                :preset-questions="currentAgentMeta.presets"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 弹窗: 新增知识库分类目录 -->
    <el-dialog v-model="addCategoryVisible" title="新增知识库多级目录分类" width="460px" append-to-body class="spd-dialog-modal">
      <el-form label-width="110px" size="small">
        <el-form-item label="分类编码" required>
          <el-input v-model="categoryForm.category_code" placeholder="如: CAT_ORTHO_SOP" />
        </el-form-item>
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.category_name" placeholder="如: 骨科手术耗材领用与操作SOP" />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number v-model="categoryForm.sort_order" :min="1" :max="99" />
        </el-form-item>
        <el-form-item label="职能描述">
          <el-input v-model="categoryForm.description" type="textarea" :rows="2" placeholder="输入目录业务范围" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addCategoryVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSaveCategory">保存目录</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗: 上传/新增医疗规范文档并触发智能切分 -->
    <el-dialog v-model="addDocVisible" title="录入医疗规范文档并由 Agent 决策分块切分" width="660px" append-to-body class="spd-dialog-modal">
      <div style="display: flex; gap: 8px; margin-bottom: 14px;">
        <el-radio-group v-model="uploadMode" size="small">
          <el-radio-button label="file">从本地上传文件 (PDF / Markdown / TXT / Word)</el-radio-button>
          <el-radio-button label="text">直接录入/粘贴文档正文</el-radio-button>
        </el-radio-group>
      </div>

      <el-form label-width="120px" size="small">
        <el-form-item label="目标目录分类">
          <el-select v-model="docForm.category_id" style="width: 100%;">
            <el-option
              v-for="c in categoryTree"
              :key="c.id"
              :value="c.id"
              :label="c.category_name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="文档分块字符数 (Chunk Size)">
          <div style="display: flex; align-items: center; gap: 10px; width: 100%;">
            <el-slider v-model="uploadChunkSize" :min="200" :max="1500" :step="50" style="flex: 1;" />
            <span class="font-mono font-bold" style="font-size: 12px; width: 65px;">{{ uploadChunkSize }} 字符</span>
          </div>
        </el-form-item>

        <el-form-item label="分块重叠字符数 (Chunk Overlap)">
          <div style="display: flex; align-items: center; gap: 10px; width: 100%;">
            <el-slider v-model="uploadChunkOverlap" :min="0" :max="300" :step="10" style="flex: 1;" />
            <span class="font-mono font-bold" style="font-size: 12px; width: 65px;">{{ uploadChunkOverlap }} 字符</span>
          </div>
        </el-form-item>

        <el-form-item label="文档标题" required>
          <el-input v-model="docForm.doc_title" placeholder="如: 医院心血管介入导管室高值耗材管理制度" />
        </el-form-item>

        <el-form-item label="分块决策引擎">
          <el-radio-group v-model="decisionMode" size="small">
            <el-radio-button label="AGENT_AUTO">真实大模型推理 (Agent LLM 决策)</el-radio-button>
            <el-radio-button label="SYSTEM_BUILTIN">本地特征雷达规则 (极速内置兜底)</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="分块策略选择">
          <el-select v-model="docForm.chunk_strategy" style="width: 100%;">
            <el-option value="AGENT_AUTO" label="AGENT_AUTO (由智能体 6A 自主特征探测推荐)" />
            <el-option value="RECURSIVE_CHAR" label="RECURSIVE_CHAR (递归字符分块)" />
            <el-option value="PARENT_CHILD" label="PARENT_CHILD (父子文档分块 Small-to-Big)" />
            <el-option value="MARKDOWN_HEADER" label="MARKDOWN_HEADER (章节标题层级分块)" />
            <el-option value="TABLE_AWARE" label="TABLE_AWARE (医疗表格感知分块)" />
            <el-option value="SEMANTIC_CLUSTER" label="SEMANTIC_CLUSTER (语义聚类分块)" />
            <el-option value="SENTENCE_WINDOW" label="SENTENCE_WINDOW (句子滑动窗口分块)" />
            <el-option value="FIXED_OVERLAP" label="FIXED_OVERLAP (固定重叠滑动分块)" />
          </el-select>
        </el-form-item>

        <!-- 本地文件上传拖拽卡片 -->
        <div v-if="uploadMode === 'file'" class="file-upload-block glass-panel" style="padding: 16px; margin: 10px 0 16px 0; border: 1px dashed var(--accent-primary); border-radius: 8px; text-align: center; cursor: pointer;" @click="triggerDocFileInput">
          <input ref="docFileInputRef" type="file" accept=".pdf,.docx,.doc,.txt,.md" style="display: none;" @change="handleDocFileSelected" />
          <div v-if="!selectedDocFile" style="padding: 12px 0;">
            <SvgIcon name="upload" :size="24" color="var(--accent-primary)" />
            <div class="font-bold" style="font-size: 13px; margin-top: 6px;">点击或拖拽上传本地规范文档</div>
            <div class="text-muted" style="font-size: 11px; margin-top: 2px;">支持格式: PDF (PyMuPDF高精度提取), Word (.docx), Markdown (.md), TXT</div>
          </div>
          <div v-else style="display: flex; align-items: center; justify-content: space-between; padding: 6px 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <SvgIcon name="file" :size="18" color="var(--accent-primary)" />
              <span class="font-bold font-mono" style="font-size: 13px;">{{ selectedDocFile.name }}</span>
              <span class="status-chip chip-info" style="font-size: 10px;">{{ Math.round(selectedDocFile.size / 1024) }} KB</span>
            </div>
            <el-button link type="danger" size="small" @click.stop="selectedDocFile = null">重新选择</el-button>
          </div>
        </div>

        <!-- 纯文本录入 -->
        <el-form-item v-else label="文档正文内容" required>
          <el-input v-model="docForm.content" type="textarea" :rows="6" placeholder="粘贴或录入文档正文..." />
        </el-form-item>

        <!-- 特征探测雷达回显卡片 -->
        <div v-if="docRadarPreview" class="radar-preview-card glass-panel" style="padding: 12px; margin-top: 10px; border-radius: 8px; font-size: 12px; background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2);">
          <div class="font-bold text-accent" style="margin-bottom: 6px;">Agent 6A 文档特征探测决策雷达:</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px;">
            <span>提取字数: <strong>{{ docRadarPreview.char_count }}</strong></span>
            <span>表格密度: <strong>{{ (docRadarPreview.radar?.table_density * 100).toFixed(1) }}%</strong></span>
            <span>法规条款数: <strong>{{ docRadarPreview.radar?.regulation_clauses }} 处</strong></span>
            <span>标题层级: <strong>{{ docRadarPreview.radar?.header_count }} 级</strong></span>
          </div>
          <div style="margin-top: 6px; font-size: 11.5px;">
            推荐策略: <strong class="text-accent">{{ docRadarPreview.chosen_strategy }}</strong> (置信度 {{ Math.round(docRadarPreview.confidence * 100) }}%) · {{ docRadarPreview.decision_reason }}
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="addDocVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingDoc" @click="submitCreateDoc">
          确认录入并执行切分
        </el-button>
      </template>
    </el-dialog>

    <!-- 抽屉: 文档切片 Chunks 列表详情 -->
    <el-drawer v-model="chunkDrawerVisible" :title="`切片明细与图谱预览 · ${currentDoc?.doc_title || ''}`" size="520px">
      <div v-if="docChunks.length > 0" class="drawer-chunks-wrap">
        <div class="text-muted" style="font-size: 12px; margin-bottom: 10px;">
          切分策略: <strong class="text-accent">{{ currentDoc?.selected_chunk_strategy }}</strong> · 总计生成 <strong>{{ docChunks.length }}</strong> 个切片
        </div>
        <div
          v-for="chk in docChunks"
          :key="chk.id"
          class="chunk-card glass-panel"
        >
          <div class="chunk-card-head">
            <span class="font-mono text-accent font-bold">{{ chk.chunk_uid }}</span>
            <span class="status-chip chip-info" style="font-size: 10px;">{{ chk.chunk_size }} 字符</span>
          </div>
          <div class="chunk-card-body font-mono">{{ chk.chunk_text }}</div>
        </div>
      </div>
      <div v-else class="text-muted" style="text-align: center; padding: 40px 0;">
        暂无切片数据
      </div>
    </el-drawer>

    <!-- 弹窗: 单文档重新切片 (Sub-Agent 6A) -->
    <el-dialog v-model="rechunkDialogVisible" title="Sub-Agent 6A 知识库文档重新切片" width="500px" append-to-body class="spd-dialog-modal">
      <div v-if="targetRechunkDoc" style="font-size: 12px; line-height: 1.8;">
        <div style="margin-bottom: 8px;"><strong>文档标题:</strong> {{ targetRechunkDoc.doc_title }}</div>
        <div style="margin-bottom: 8px;"><strong>当前切片策略:</strong> <span class="font-mono text-accent">{{ targetRechunkDoc.selected_chunk_strategy }}</span> (切片数: {{ targetRechunkDoc.chunk_count }})</div>
        <div style="margin-bottom: 12px;"><strong>AI 仲裁决策建议:</strong> {{ targetRechunkDoc.agent_decision_reason || '推荐采用医疗规范语义感知策略' }}</div>

        <el-form label-width="120px" size="small">
          <el-form-item label="重新分配策略">
            <el-select v-model="selectedRechunkStrategy" style="width: 100%;">
              <el-option value="AGENT_AUTO" label="AGENT_AUTO (Sub-Agent 6A 决策雷达自动匹配)" />
              <el-option value="RECURSIVE_CHAR" label="RECURSIVE_CHAR (递归字符分块)" />
              <el-option value="PARENT_CHILD" label="PARENT_CHILD (父子双层分块 Small-to-Big)" />
              <el-option value="MARKDOWN_HEADER" label="MARKDOWN_HEADER (Markdown 标题层级分块)" />
              <el-option value="TABLE_AWARE" label="TABLE_AWARE (医疗表格感知分块)" />
              <el-option value="SEMANTIC_CLUSTER" label="SEMANTIC_CLUSTER (语义聚类分块)" />
              <el-option value="SENTENCE_WINDOW" label="SENTENCE_WINDOW (句子滑动窗口分块)" />
              <el-option value="FIXED_OVERLAP" label="FIXED_OVERLAP (固定重叠滑动分块)" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button size="small" @click="rechunkDialogVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="rechunkingSingle" @click="handleConfirmSingleRechunk">
          执行重切并更新向量库
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';
import AgentChatWidget from '@/components/AgentChatWidget.vue';
import {
  getCategoryTree,
  saveCategory,
  listDocuments,
  createDocumentAndChunk,
  getDocumentChunks,
  getModularRagConfig,
  updateModularRagConfig,
  checkConnectivity,
  testSingleConnectivity,
  uploadDocumentFile,
  getAgentModels,
  saveAgentModels,
  getRagInspection,
  postRagRechunk,
  deleteDocumentApi,
  saveAllUnifiedConfig,
  testFeishuCard,
  chatWithCoze,
  getFeishuWsStatus,
  restartFeishuWs,
  getExternalMcpStatus,
  toggleExternalMcpTool,
  executeExternalMcpTool,
  type CategoryTreeNode,
  type DocumentItem,
  type ChunkItem,
  type ModularRagConfig,
  type ConnectivityData,
  type RagInspectionResult
} from '@/api/ragAgentHubApi';

const userStore = useUserStore();
const route = useRoute();
const activeTab = ref('knowledge');

/**
 * 根据路由参数 ?tab= 同步激活对应工作台 Tab
 * @param queryTab 路由传递的选项卡标识
 */
function syncTabFromRoute(queryTab?: string) {
  const tabVal = queryTab || (route.query.tab as string | undefined);
  if (!tabVal) return;
  if (tabVal === 'modular' || tabVal === 'config') {
    activeTab.value = 'config';
  } else if (tabVal === 'tree' || tabVal === 'knowledge') {
    activeTab.value = 'knowledge';
  } else if (tabVal === 'agents') {
    activeTab.value = 'agents';
  } else if (tabVal === 'health') {
    activeTab.value = 'config';
  }
}

watch(
  () => route.query.tab,
  (newTab) => {
    syncTabFromRoute(newTab as string);
  }
);

const connData = ref<ConnectivityData | null>(null);
const categoryTree = ref<CategoryTreeNode[]>([]);
const selectedCategoryId = ref<number | undefined>(undefined);

const documents = ref<DocumentItem[]>([]);
const loadingDocs = ref(false);

// 知识库文档列表分页与多维筛选状态
const docCurrentPage = ref(1);
const docPageSize = ref(10);
const docSearchKeyword = ref('');
const docStrategyFilter = ref('ALL');

/**
 * 响应式过滤知识库文档列表 (支持关键词与分块策略筛选)
 * @returns {Array} 过滤后的文档数组
 * @route internal://RagAgentHubView/filteredDocuments
 * @throws 无异常抛出
 */
const filteredDocuments = computed(() => {
  return documents.value.filter((doc) => {
    // 策略筛选
    if (docStrategyFilter.value !== 'ALL' && doc.selected_chunk_strategy !== docStrategyFilter.value) {
      return false;
    }
    // 关键词筛选
    if (docSearchKeyword.value.trim()) {
      const kw = docSearchKeyword.value.trim().toLowerCase();
      const matchTitle = (doc.doc_title || '').toLowerCase().includes(kw);
      const matchCode = (doc.doc_code || '').toLowerCase().includes(kw);
      if (!matchTitle && !matchCode) {
        return false;
      }
    }
    return true;
  });
});

/**
 * 响应式切片当前页显示的知识库文档
 * @returns {Array} 当前页切片文档数组
 * @route internal://RagAgentHubView/paginatedDocuments
 * @throws 无异常抛出
 */
const paginatedDocuments = computed(() => {
  const start = (docCurrentPage.value - 1) * docPageSize.value;
  return filteredDocuments.value.slice(start, start + docPageSize.value);
});

const savingModular = ref(false);
const uploadChunkSize = ref(500);
const uploadChunkOverlap = ref(80);
const decisionMode = ref<'AGENT_AUTO' | 'SYSTEM_BUILTIN'>('AGENT_AUTO');
const chromaStatsInfo = ref({
  ready: false,
  total_vectors: 0,
  storage_path: '',
  collection: ''
});

const configForm = ref<ModularRagConfig>({
  enable_intent_classify: 1,
  enable_query_rewrite: 1,
  max_rewrite_loops: 3,
  rewrite_threshold: 0.85,
  enable_subquery_decompose: 1,
  enable_dense_vector: 1,
  enable_bm25_sparse: 1,
  enable_graph_rag: 1,
  top_k_retrieval: 15,
  enable_reranker: 1,
  rerank_threshold: 0.55,
  enable_context_compression: 1,
  enable_citation_source: 1,
  enable_faithfulness_check: 1,
  enable_system_grounding: 1,
  default_chunking_mode: 'AGENT_AUTO',
  active_embedding_model: 'bge-m3:latest',
  active_llm_provider: 'mimo',
  active_chat_model: 'qwen3.5:2b',
  mimo_base_url: 'https://api.xiaomimimo.com/v1',
  mimo_model_name: 'mimo-v2.6-flash',
  has_mimo_env_key: true,
  enable_streaming: 1,
  enable_deep_thinking: 1,
  llm_timeout_seconds: 60,
  default_chunk_size: 500,
  default_chunk_overlap: 80,
  enable_feishu_welcome_card: 1,
  feishu_welcome_cooldown_hours: 24.0,
  langsmith_enabled: 1,
  langsmith_project: 'Personal',
  langsmith_endpoint: 'https://api.smith.langchain.com',
  has_langsmith_key: true
});

// 飞书长连接守护服务状态 (lark-oapi 官方 SDK 反向 WebSocket)
const feishuWsLoading = ref(false);
const feishuWsRestarting = ref(false);
const welcomeCooldownPreset = ref('24h');

/**
 * 飞书单聊欢迎卡片频控档位切换响应
 * @param {string} val 预设档位标识 ('12h' | '24h' | '168h' | 'custom')
 * @returns {void}
 * @route internal://RagAgentHubView/handleCooldownPresetChange
 * @throws 无
 */
function handleCooldownPresetChange(val: string) {
  if (val === '12h') {
    configForm.value.feishu_welcome_cooldown_hours = 12.0;
  } else if (val === '24h') {
    configForm.value.feishu_welcome_cooldown_hours = 24.0;
  } else if (val === '168h') {
    configForm.value.feishu_welcome_cooldown_hours = 168.0;
  }
}

const savingWelcomeCooldown = ref(false);

/**
 * 飞书单聊自动欢迎引导卡片频控与开关独立保存
 * @param 无
 * @returns {Promise<void>} 异步持久化配置至数据库与服务内存
 * @route POST /api/v1/rag-hub/config/save-all
 * @throws 异常时弹出错误提示
 */
async function saveWelcomeCooldownSetting() {
  savingWelcomeCooldown.value = true;
  if (feishuWebhookUrl.value) {
    localStorage.setItem('spd_feishu_webhook_url', feishuWebhookUrl.value.trim());
  }
  try {
    await saveAllUnifiedConfig({
      global_config: configForm.value,
      agent_configs: agentModelList.value,
      feishu_webhook_url: feishuWebhookUrl.value.trim() || undefined
    });
    const statusText = configForm.value.enable_feishu_welcome_card ? '已开启' : '已关闭';
    let periodText = '';
    if (welcomeCooldownPreset.value === '12h') periodText = '每 12 小时 1 次';
    else if (welcomeCooldownPreset.value === '24h') periodText = '每天仅 1 次 (24h)';
    else if (welcomeCooldownPreset.value === '168h') periodText = '每周 1 次 (7天)';
    else periodText = `自定义每 ${configForm.value.feishu_welcome_cooldown_hours} 小时 1 次`;

    ElMessage.success({
      message: `飞书单聊欢迎卡片频控已保存生效！状态: ${statusText}，频控防打扰周期: ${periodText}`,
      duration: 3500
    });
  } catch (err: any) {
    ElMessage.error(err.message || '保存频控设置失败');
  } finally {
    savingWelcomeCooldown.value = false;
  }
}
const feishuWsStatus = ref<{
  connected: boolean;
  status_label: string;
  app_id: string;
  uptime_seconds: number;
  received_messages_count: number;
  last_message_at: string;
  last_error: string | null;
  subscribed_events: string[];
  conn_id: string | null;
  instruction: string;
}>({
  connected: false,
  status_label: '检测中...',
  app_id: 'cli_a94f4c8235f89cb3',
  uptime_seconds: 0,
  received_messages_count: 0,
  last_message_at: '暂无接收记录',
  last_error: null,
  subscribed_events: ['im.message.receive_v1', 'im.chat.access_event.bot_p2p_chat_entered_v1'],
  conn_id: null,
  instruction: ''
});

// 飞书与 Coze 协同状态 (支持 Webhook 直连与 OpenAPI 双轨)
const feishuCardType = ref('STOCK_DISPATCH');
const feishuProductName = ref('一次性使用无菌注射器 5ml');
const feishuWebhookUrl = ref(localStorage.getItem('spd_feishu_webhook_url') || '');
const feishuReceiveId = ref(localStorage.getItem('spd_feishu_receive_id') || '');
const feishuAtOpenId = ref(localStorage.getItem('spd_feishu_at_open_id') || '');
const feishuSending = ref(false);
const feishuResult = ref<any>(null);

const cozeQuery = ref('请问三甲医院高值耗材一物一码UDI的验收与退货国家监管规则是什么？');
const cozeSending = ref(false);
const cozeResponse = ref<string>('');

// 7. 外部 MCP 协议扩展工具状态 (Model Context Protocol 2024-11-05)
interface ExternalMcpToolItem {
  tool_name: string;
  title: string;
  description: string;
  enabled: boolean;
  protocol_version: string;
  transport: string;
  call_count: number;
  avg_latency_ms: number;
  status: string;
}

const externalMcpTools = ref<ExternalMcpToolItem[]>([
  {
    tool_name: 'mcp_external_medical_search',
    title: '国家药监局与国家医疗器械标准联网检索 (NMPA & National Standards)',
    description: '免 API Key 外部医学与器械规范权威镜像与动态检索适配器，支持 GB/YY/T 国标与三类医疗器械分类规则穿透。',
    enabled: true,
    protocol_version: '2024-11-05',
    transport: 'HTTP/JSON-RPC (Decoupled Adapter)',
    call_count: 0,
    avg_latency_ms: 15.2,
    status: 'READY'
  },
  {
    tool_name: 'mcp_datetime_and_fefo_calc',
    title: '医疗物资灭菌效期倒计时与 FEFO 调拨算法 (Sterilization & FEFO Engine)',
    description: '遵循 FEFO (First Expired, First Out) 近效期先出硬性医疗内控原则，精准推算灭菌失效日、剩余天数与调拨优先级。',
    enabled: true,
    protocol_version: '2024-11-05',
    transport: 'HTTP/JSON-RPC (Decoupled Adapter)',
    call_count: 0,
    avg_latency_ms: 12.4,
    status: 'READY'
  }
]);

const loadingMcpStatus = ref(false);
const mcpTestDialogVisible = ref(false);
const activeMcpTool = ref<ExternalMcpToolItem | null>(null);
const mcpTestArgsJson = ref('');
const mcpExecuting = ref(false);
const mcpTestResult = ref<any>(null);

// 新增分类弹窗
const addCategoryVisible = ref(false);
const categoryForm = ref({
  category_code: '',
  category_name: '',
  sort_order: 1,
  description: '',
  icon_name: 'folder'
});

// 连通性独立测速状态
const testingTarget = ref('');

/**
 * 独立测试单项基础设施连通性与时延
 * @param {'ollama' | 'redis' | 'neo4j' | 'mimo' | 'langsmith'} target 测试目标组件
 * @returns {Promise<void>} 异步测试完成承诺
 * @route POST /api/v1/rag-hub/connectivity/test-single
 * @throws 测试失败时弹出错误提示
 */
async function runSingleTest(target: 'ollama' | 'redis' | 'neo4j' | 'mimo' | 'langsmith') {
  testingTarget.value = target;
  try {
    const res = await testSingleConnectivity(target);
    if (connData.value && res) {
      if (target === 'ollama' && connData.value.ollama) {
        connData.value.ollama.latency_ms = res.latency_ms;
        if (res.models) connData.value.ollama.models = res.models;
      } else if (target === 'redis' && connData.value.redis) {
        connData.value.redis.latency_ms = res.latency_ms;
      } else if (target === 'neo4j' && connData.value.neo4j) {
        connData.value.neo4j.latency_ms = res.latency_ms;
      }
    }
    ElMessage.success(res.message || `${target.toUpperCase()} 连通性测试通过！`);
  } catch (err: any) {
    ElMessage.error(err.message || `${target} 测试异常`);
  } finally {
    testingTarget.value = '';
  }
}

// 6 大智能体独立大模型解耦配置中台
const agentModelList = ref<any[]>([]);
const savingAgentModels = ref(false);

/**
 * 读取 6 大业务智能体大模型解耦配置
 * @param 无
 * @returns {Promise<void>} 异步加载完成承诺
 * @route GET /api/v1/rag-hub/agent-models
 * @throws 加载异常时在控制台告警
 */
async function loadAgentModelConfigs() {
  try {
    const res = await getAgentModels();
    agentModelList.value = res || [];
  } catch (err) {
    console.warn('获取智能体模型配置失败:', err);
  }
}

/**
 * 批量套用首个智能体模型参数至全员
 * @param 无
 * @returns {void}
 * @route 纯前端状态批量同步
 * @throws 无
 */
function applyBatchModelToAll() {
  if (agentModelList.value.length === 0) return;
  const first = agentModelList.value[0];
  for (let i = 1; i < agentModelList.value.length; i++) {
    agentModelList.value[i].model_provider = first.model_provider;
    agentModelList.value[i].model_name = first.model_name;
    agentModelList.value[i].temperature = first.temperature;
  }
  ElMessage.info(`已将 [${first.model_name}] 批量套用至全部 8 大业务智能体！点击右侧保存生效。`);
}

/**
 * 保存 8 大智能体独立大模型解耦配置
 * @param 无
 * @returns {Promise<void>} 异步保存完成承诺
 * @route POST /api/v1/rag-hub/agent-models/batch-save
 * @throws 保存失败时弹出错误提示
 */
async function handleSaveAgentModels() {
  savingAgentModels.value = true;
  try {
    await saveAgentModels(agentModelList.value);
    ElMessage.success('6 大智能体独立大模型解耦配置已成功落盘记忆！');
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败');
  } finally {
    savingAgentModels.value = false;
  }
}

// 新增文档弹窗与多格式文件上传
const addDocVisible = ref(false);
const submittingDoc = ref(false);
const uploadMode = ref<'file' | 'text'>('file');
const selectedDocFile = ref<File | null>(null);
const docFileInputRef = ref<HTMLInputElement | null>(null);
const docRadarPreview = ref<any>(null);

const docForm = ref({
  category_id: 1,
  doc_title: '',
  file_type: 'markdown',
  content: '',
  chunk_strategy: 'AGENT_AUTO'
});

function triggerDocFileInput() {
  docFileInputRef.value?.click();
}

function handleDocFileSelected(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    selectedDocFile.value = input.files[0];
    docForm.value.doc_title = selectedDocFile.value.name.replace(/\.[^/.]+$/, '');
  }
}

// 切片抽屉
const chunkDrawerVisible = ref(false);
const currentDoc = ref<DocumentItem | null>(null);
const docChunks = ref<ChunkItem[]>([]);

// 8 大业务智能体多架构调度配置元数据
const agentMetaList = [
  { id: 'agent_1', name: '智能体 1: 产品字典归类与入库审查', arch: 'Plan & Execute 规划执行', presets: ['系统产品字典中有多少种高值与普通耗材？', '帮我新增锁定接骨板字典并建仓', '查询国家药监局关于无菌一次性耗材包装与灭菌的最新国标规范 (调用外部 MCP)', '耗材于2026-03-01生产，灭菌有效期24个月，请调用外部MCP推算到期日与FEFO调拨优先级'] },
  { id: 'agent_2', name: '智能体 2: 主库按需分发调拨', arch: 'Router + Skill 路由技能', presets: ['主库当前重点物资库存水位与调拨单统计', '执行 FEFO 近效期分发调拨，向骨科二级库补充低水位耗材', '有哪些未审核的采购与请领单帮我提炼'] },
  { id: 'agent_3', name: '智能体 3: 临床二级库申领问答', arch: 'LangGraph 状态图 + HITL', presets: ['查询全院待人工审批请领单据待办', '向耗材主库申领 50 包一次性医用外科口罩', '骨科手术定数包配置规程怎么查'] },
  { id: 'agent_4', name: '智能体 4: 高值一物一码全链路溯源', arch: 'ReAct 循环流式推理', presets: ['系统当前在册高值耗材总数与冻结批次统计', '追溯高值耗材 UDI-202611-0012 并在发生不良事件时紧急冻结该批次', '排查该批次是否存在不良事件召回'] },
  { id: 'agent_5', name: '智能体 5: 多科室精算与财务审计', arch: 'Blackboard 中央黑板多专家', presets: ['对 2026-11 周期全院科室耗材调拨与高值核销进行财务精算审计', '查看最新国家带量集采控费政策'] },
  { id: 'agent_6', name: '智能体 6: 智能数据清洗与自省重写', arch: 'Multi-Agent + Modular RAG', presets: ['系统中有多少知识文档与切片？', '骨科植入物手术包管理规范与召回法规', '查一下国家药监局三类医疗器械植入物分类目录与质量标准 (外部 MCP)'] },
  { id: 'agent_7', name: '智能体 7: 飞书协同推送与群聊互动', arch: 'Webhook + OpenAPI 双轨协同', presets: ['向骨科病区飞书协同群推送最新物资调拨单据卡片，核对数量与效期。', '向飞书群广播高值耗材召回冻结紧急预警卡片', '查询全院待人工审批请领单并生成飞书催办卡片'] },
  { id: 'agent_8', name: '智能体 8: Coze 开放生态小爱医疗智能体', arch: 'Coze V3 Cloud Bot (豆包 1.5 Pro)', presets: ['请问三甲医院高值耗材一物一码UDI的验收与退货国家监管规则是什么？', '国家对三甲医院高值植入物耗材的六度防伪与物权溯源有哪些明文规定？', '请解释带量集采政策下，医用耗材零加成与科室成本精算公式'] }
];

// Sub-Agent 6A: 知识库全库切片健康巡检与单/批量重切状态
const inspectionData = ref<RagInspectionResult | null>(null);
const inspecting = ref(false);
const batchRechunking = ref(false);
const rechunkDialogVisible = ref(false);
const targetRechunkDoc = ref<DocumentItem | null>(null);
const selectedRechunkStrategy = ref('AGENT_AUTO');
const rechunkingSingle = ref(false);

/**
 * 触发知识库切片健康度全库巡检 (Sub-Agent 6A)
 * @param 无
 * @returns {Promise<void>} 异步完成承诺
 * @route GET /api/v1/rag-hub/maintenance/inspect
 * @throws 巡检请求失败时抛出错误通知
 */
async function handleRunInspection() {
  inspecting.value = true;
  try {
    const res = await getRagInspection();
    inspectionData.value = res;
    if (res.unindexed_count > 0) {
      ElMessage.warning(`巡检完成: 发现 ${res.unindexed_count} 篇未切片或异常文档，健康度: ${res.health_score}%`);
    } else {
      ElMessage.success(`全库巡检通过: 所有文档切片完好，健康度: 100%`);
    }
  } catch (err: any) {
    ElMessage.error(err.message || '全库巡检失败');
  } finally {
    inspecting.value = false;
  }
}

/**
 * 批量自动重新切分所有未切片或异常文档 (Sub-Agent 6A)
 * @param 无
 * @returns {Promise<void>} 异步完成承诺
 * @route POST /api/v1/rag-hub/maintenance/rechunk
 * @throws 批量重新切片异常时提示错误
 */
async function handleBatchAutoRechunk() {
  if (!inspectionData.value || !inspectionData.value.abnormal_documents.length) return;
  batchRechunking.value = true;
  try {
    let successCount = 0;
    for (const doc of inspectionData.value.abnormal_documents) {
      await postRagRechunk({ doc_id: doc.doc_id });
      successCount++;
    }
    ElMessage.success(`Sub-Agent 6A 批量重切成功: 已自动修复 ${successCount} 篇异常文档`);
    await fetchDocuments();
    await handleRunInspection();
  } catch (err: any) {
    ElMessage.error(err.message || '批量自动重切异常');
  } finally {
    batchRechunking.value = false;
  }
}

/**
 * 打开单个文档重新切片配置对话框
 * @param {DocumentItem} row 选中的目标文档对象
 * @returns {void}
 * @route 纯前端弹窗状态控制
 * @throws 无
 */
function openRechunkModal(row: DocumentItem) {
  targetRechunkDoc.value = row;
  selectedRechunkStrategy.value = 'AGENT_AUTO';
  rechunkDialogVisible.value = true;
}

/**
 * 确认执行单文档指定策略重新切片 (Sub-Agent 6A)
 * @param 无
 * @returns {Promise<void>} 异步切片完成承诺
 * @route POST /api/v1/rag-hub/maintenance/rechunk
 * @throws 重新切片失败时提示错误
 */
async function handleConfirmSingleRechunk() {
  if (!targetRechunkDoc.value) return;
  rechunkingSingle.value = true;
  try {
    const strat = selectedRechunkStrategy.value === 'AGENT_AUTO' ? undefined : selectedRechunkStrategy.value;
    const res = await postRagRechunk({ doc_id: targetRechunkDoc.value.id, strategy: strat });
    ElMessage.success(`文档《${targetRechunkDoc.value.doc_title}》重新切片成功，生成 ${res.chunks_generated} 个切片`);
    rechunkDialogVisible.value = false;
    await fetchDocuments();
    await handleRunInspection();
  } catch (err: any) {
    ElMessage.error(err.message || '重新切片失败');
  } finally {
    rechunkingSingle.value = false;
  }
}

const currentAgentId = ref('agent_1');
const currentAgentMeta = computed(() =>
  agentMetaList.find((a) => a.id === currentAgentId.value) || agentMetaList[0]
);

/**
 * 校验指定智能体是否与当前人员岗位匹配（推荐使用）
 * @param {string} agentId 智能体节点标识 (agent_1 ~ agent_8)
 * @returns {boolean} 是否为本岗推荐
 */
function isAgentRecommended(agentId: string): boolean {
  const role = userStore.currentUser.roleCode;
  if (role === 'sys_admin') return true;
  if (role === 'secondary_user') {
    return agentId === 'agent_3' || agentId === 'agent_4';
  }
  if (role === 'finance_auditor') {
    return agentId === 'agent_5' || agentId === 'agent_4';
  }
  if (role === 'dept_manager') {
    return agentId === 'agent_1' || agentId === 'agent_2' || agentId === 'agent_6';
  }
  return true;
}

/**
 * 点击切换沙箱调试智能体并提供岗位指引
 * @param {any} ag 智能体元数据对象
 */
function handleSelectAgent(ag: any) {
  currentAgentId.value = ag.id;
  if (!isAgentRecommended(ag.id) && userStore.currentUser.roleCode !== 'sys_admin') {
    ElMessage.info(`提示：[${ag.name}] 属于跨岗位业务智能体，已为您切换。建议优先配合本岗核心业务使用。`);
  }
}

/**
 * 加载四方连通性健康状况
 * @param 无
 * @returns {Promise<void>} 异步状态查询承诺
 * @route GET /api/v1/rag-hub/connectivity/check
 * @throws 请求异常时控制台告警
 */
async function loadConnectivity() {
  try {
    const res = await checkConnectivity();
    connData.value = res;
  } catch (err: any) {
    console.warn('连通性检查异常:', err);
  }
}

/**
 * 获取知识库树状分类目录列表
 * @param 无
 * @returns {Promise<void>} 异步请求承诺
 * @route GET /api/v1/rag-hub/category/tree
 * @throws 获取分类失败时提示错误
 */
async function fetchCategories() {
  try {
    const res = await getCategoryTree();
    categoryTree.value = res || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取分类目录失败');
  }
}

/**
 * 获取当前分类下的医疗规范文档资产列表
 * @param 无
 * @returns {Promise<void>} 异步请求承诺
 * @route GET /api/v1/rag-hub/document/list
 * @throws 获取文档失败时提示错误
 */
async function fetchDocuments() {
  loadingDocs.value = true;
  try {
    const res = await listDocuments(selectedCategoryId.value);
    documents.value = res || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取文档列表失败');
  } finally {
    loadingDocs.value = false;
  }
}

/**
 * 切换选中的知识库分类并重载文档列表
 * @param {number} catId 选中的分类主键 ID
 * @returns {void}
 * @route 纯前端状态更新联动
 * @throws 无
 */
function selectCategory(catId: number) {
  selectedCategoryId.value = catId;
  docCurrentPage.value = 1;
  fetchDocuments();
}

/**
 * 读取 Modular RAG 热插拔全局配置
 * @param 无
 * @returns {Promise<void>} 异步加载承诺
 * @route GET /api/v1/rag-hub/config
 * @throws 加载异常时控制台警告
 */
async function loadModularConfig() {
  try {
    const res = await getModularRagConfig();
    configForm.value = res;
    if (res.default_chunk_size) {
      uploadChunkSize.value = res.default_chunk_size;
    }
    if (res.default_chunk_overlap) {
      uploadChunkOverlap.value = res.default_chunk_overlap;
    }
    if (res.default_chunking_mode) {
      decisionMode.value = res.default_chunking_mode as any;
    }
    if (res.chroma_stats) {
      chromaStatsInfo.value = res.chroma_stats;
    }
    if (res.feishu_welcome_cooldown_hours) {
      const h = Number(res.feishu_welcome_cooldown_hours);
      if (h === 12) welcomeCooldownPreset.value = '12h';
      else if (h === 24) welcomeCooldownPreset.value = '24h';
      else if (h === 168) welcomeCooldownPreset.value = '168h';
      else welcomeCooldownPreset.value = 'custom';
    }
  } catch (err: any) {
    console.warn('加载Modular配置异常:', err);
  }
}

/**
 * 变动即自动落盘机制：算子开关或滑块微调后秒级同步写入数据库
 * @param 无
 * @returns {Promise<void>} 异步更新承诺
 * @route POST /api/v1/rag-hub/config/update
 * @throws 自动保存失败时弹出错误提示
 */
async function handleAutoSaveConfig() {
  try {
    await updateModularRagConfig(configForm.value);
    ElMessage.success({ message: '配置已自动落盘同步至 MySQL 业务库', duration: 1200 });
  } catch (err: any) {
    ElMessage.error(err.message || '自动保存失败');
  }
}

/**
 * 手动保存 Modular RAG 算子全局配置
 * @param 无
 * @returns {Promise<void>} 异步保存承诺
 * @route POST /api/v1/rag-hub/config/update
 * @throws 保存配置失败时提示错误
 */
async function saveModularConfig() {
  savingModular.value = true;
  try {
    await updateModularRagConfig(configForm.value);
    ElMessage.success('Modular RAG 热插拔全局配置更新成功并已落盘持久化！');
  } catch (err: any) {
    ElMessage.error(err.message || '保存配置失败');
  } finally {
    savingModular.value = false;
  }
}

/**
 * 刷新飞书官方 SDK 长连接 (反向 WebSocket) 运行状态
 * @param 无
 * @returns {Promise<void>} 异步刷新状态
 * @route GET /api/v1/rag-hub/feishu/ws-status
 * @throws 异常安全捕获
 */
async function refreshFeishuWsStatus() {
  feishuWsLoading.value = true;
  try {
    const res = await getFeishuWsStatus();
    const actualData = (res && typeof res === 'object' && 'connected' in res) ? res : (res?.data || null);
    if (actualData && typeof actualData === 'object') {
      feishuWsStatus.value = actualData;
    }
  } catch (err: any) {
    console.warn('获取飞书长连接状态异常:', err);
  } finally {
    feishuWsLoading.value = false;
  }
}

/**
 * 手动重启飞书官方 SDK 长连接守护服务
 * @param 无
 * @returns {Promise<void>} 异步重启完成
 * @route POST /api/v1/rag-hub/feishu/ws-restart
 * @throws 重启失败时弹出错误提示
 */
async function handleRestartFeishuWs() {
  feishuWsRestarting.value = true;
  try {
    const res = await restartFeishuWs();
    ElMessage.success(res?.msg || '飞书长连接守护服务已重新启动');
    const statusData = res?.status || res?.data?.status;
    if (statusData) {
      feishuWsStatus.value = statusData;
    } else {
      await refreshFeishuWsStatus();
    }
  } catch (err: any) {
    ElMessage.error(err.message || '重启飞书长连接失败');
  } finally {
    feishuWsRestarting.value = false;
  }
}

/**
 * 拉取外部 MCP 工具运行清单与监控指标
 * @param 无
 * @returns {Promise<void>} 异步完成回执
 * @route GET /api/v1/rag-hub/mcp-external/status
 * @throws 异常捕获并控制台告警
 */
async function fetchMcpExternalStatus() {
  loadingMcpStatus.value = true;
  try {
    const res = await getExternalMcpStatus();
    const data = res?.data || res;
    if (data && Array.isArray(data.tools) && data.tools.length > 0) {
      externalMcpTools.value = data.tools;
    }
  } catch (err: any) {
    console.warn('拉取外部 MCP 工具状态异常:', err);
  } finally {
    loadingMcpStatus.value = false;
  }
}

/**
 * 切换外部 MCP 协议扩展工具启闭状态
 * @param {ExternalMcpToolItem} tool 待切换状态的 MCP 工具对象
 * @returns {Promise<void>}
 * @route POST /api/v1/rag-hub/mcp-external/toggle
 * @throws 切换失败报错提示
 */
async function handleToggleMcpTool(tool: ExternalMcpToolItem) {
  try {
    await toggleExternalMcpTool(tool.tool_name, tool.enabled);
    ElMessage.success(`外部 MCP 工具 [${tool.title}] 已成功切换为 ${tool.enabled ? '启用' : '停用'}`);
  } catch (err: any) {
    tool.enabled = !tool.enabled;
    ElMessage.error(err.message || '切换 MCP 工具状态失败');
  }
}

/**
 * 打开外部 MCP 工具单体入参出参透视弹窗
 * @param {ExternalMcpToolItem} tool 当前选中的工具项
 */
function openMcpTestDialog(tool: ExternalMcpToolItem) {
  activeMcpTool.value = tool;
  mcpTestResult.value = null;
  if (tool.tool_name === 'mcp_external_medical_search') {
    mcpTestArgsJson.value = JSON.stringify({
      query_keyword: '无菌注射器',
      max_results: 3
    }, null, 2);
  } else {
    mcpTestArgsJson.value = JSON.stringify({
      production_date: '2026-01-01',
      validity_months: 24,
      batch_no: 'BATCH-202611-TEST',
      material_name: '一次性使用无菌输液器带针'
    }, null, 2);
  }
  mcpTestDialogVisible.value = true;
}

/**
 * 手动执行外部 MCP 工具调试调用
 * @param 无
 * @returns {Promise<void>}
 * @route POST /api/v1/rag-hub/mcp-external/execute
 * @throws 异常报错提示
 */
async function handleExecuteMcpTest() {
  if (!activeMcpTool.value) return;
  let parsedArgs: Record<string, any> = {};
  try {
    parsedArgs = JSON.parse(mcpTestArgsJson.value);
  } catch (err: any) {
    ElMessage.warning('入参 JSON 格式不合法，请检查标点与引号');
    return;
  }

  mcpExecuting.value = true;
  try {
    const res = await executeExternalMcpTool(activeMcpTool.value.tool_name, parsedArgs);
    mcpTestResult.value = res?.data || res;
    ElMessage.success(`MCP 工具 [${activeMcpTool.value.tool_name}] 执行成功`);
    await fetchMcpExternalStatus();
  } catch (err: any) {
    ElMessage.error(err.message || '执行 MCP 工具失败');
  } finally {
    mcpExecuting.value = false;
  }
}

/**
 * 测试发送飞书业务交互式卡片 (支持 Webhook 直连与 OpenAPI 双轨)
 * @param 无
 * @returns {Promise<void>} 异步推送完成承诺
 * @route POST /api/v1/rag-hub/feishu/send-test
 * @throws 飞书推送失败时弹出错误提示
 */
async function handleSendFeishuCard() {
  feishuSending.value = true;
  feishuResult.value = null;

  // 记忆用户输入的飞书配置
  if (feishuWebhookUrl.value) {
    localStorage.setItem('spd_feishu_webhook_url', feishuWebhookUrl.value.trim());
  }
  if (feishuReceiveId.value) {
    localStorage.setItem('spd_feishu_receive_id', feishuReceiveId.value.trim());
  }
  if (feishuAtOpenId.value) {
    localStorage.setItem('spd_feishu_at_open_id', feishuAtOpenId.value.trim());
  }

  try {
    const res = await testFeishuCard({
      card_type: feishuCardType.value,
      product_name: feishuProductName.value,
      webhook_url: feishuWebhookUrl.value.trim() || undefined,
      receive_id: feishuReceiveId.value.trim() || undefined,
      at_open_id: feishuAtOpenId.value.trim() || undefined
    });
    feishuResult.value = res;
    if (res.data?.method === 'webhook') {
      ElMessage.success('飞书群机器人 Webhook 真实推送成功，群内卡片已弹出！');
    } else if (res.data?.method === 'open_api') {
      ElMessage.success('飞书自建应用 OpenAPI 真实推送成功！');
    } else {
      ElMessage.info(res.data?.message || '卡片结构解析成功（填入群机器人 Webhook 即可直接在群内收到真实卡片）');
    }
  } catch (err: any) {
    ElMessage.error(err.message || '飞书推送失败');
  } finally {
    feishuSending.value = false;
  }
}

/**
 * 与 Coze 云端小爱智能体协同问答
 * @param 无
 * @returns {Promise<void>} 异步问答响应承诺
 * @route POST /api/v1/rag-hub/coze/chat
 * @throws 协同问答异常时提示错误
 */
async function handleChatWithCoze() {
  if (!cozeQuery.value.trim()) return;
  cozeSending.value = true;
  cozeResponse.value = '';
  try {
    const res = await chatWithCoze({
      query: cozeQuery.value.trim()
    });
    cozeResponse.value = res.answer || res.content || JSON.stringify(res);
    ElMessage.success('Coze 小爱智能体协同响应成功！');
  } catch (err: any) {
    ElMessage.error(err.message || 'Coze 对话异常');
  } finally {
    cozeSending.value = false;
  }
}

/**
 * 一键保存全部配置 (包含 Modular RAG 算子、8 大智能体模型独立解耦与飞书 Webhook)
 * @param 无
 * @returns {Promise<void>} 异步统一持久化承诺
 * @route POST /api/v1/rag-hub/config/save-all
 * @throws 保存全部配置失败时提示错误
 */
async function saveAllUnifiedConfigHandler() {
  savingModular.value = true;
  if (feishuWebhookUrl.value) {
    localStorage.setItem('spd_feishu_webhook_url', feishuWebhookUrl.value.trim());
  }
  try {
    await saveAllUnifiedConfig({
      global_config: configForm.value,
      agent_configs: agentModelList.value,
      feishu_webhook_url: feishuWebhookUrl.value.trim() || undefined
    });
    ElMessage.success('全局算子配置、8 大业务智能体模型解耦配置与飞书 Webhook 已全部成功持久化落盘并立即生效！');
  } catch (err: any) {
    ElMessage.error(err.message || '保存全部配置失败');
  } finally {
    savingModular.value = false;
  }
}

/**
 * 打开新增知识库多级目录分类弹窗
 * @param 无
 * @returns {void}
 * @route 纯前端弹窗状态控制
 * @throws 无
 */
function openAddCategoryModal() {
  categoryForm.value = {
    category_code: `CAT_${Date.now()}`,
    category_name: '',
    sort_order: (categoryTree.value.length || 0) + 1,
    description: '',
    icon_name: 'folder'
  };
  addCategoryVisible.value = true;
}

/**
 * 提交保存新增分类目录
 * @param 无
 * @returns {Promise<void>} 异步创建完成承诺
 * @route POST /api/v1/rag-hub/category/save
 * @throws 目录信息校验不通过或持久化异常时提示错误
 */
async function submitSaveCategory() {
  if (!categoryForm.value.category_name) {
    ElMessage.warning('请输入分类名称');
    return;
  }
  try {
    await saveCategory(categoryForm.value);
    ElMessage.success('目录分类创建成功');
    addCategoryVisible.value = false;
    fetchCategories();
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败');
  }
}

/**
 * 打开新增医疗规范文档弹窗
 * @param 无
 * @returns {void}
 * @route 纯前端状态重置与弹窗唤起
 * @throws 无
 */
function openAddDocModal() {
  selectedDocFile.value = null;
  docRadarPreview.value = null;
  uploadMode.value = 'file';
  docForm.value = {
    category_id: selectedCategoryId.value || (categoryTree.value[0]?.id || 1),
    doc_title: '',
    file_type: 'markdown',
    content: '',
    chunk_strategy: 'AGENT_AUTO'
  };
  addDocVisible.value = true;
}

/**
 * 提交录入或上传文档并触发智能切分
 * @param 无
 * @returns {Promise<void>} 异步文档创建与向量化承诺
 * @route POST /api/v1/rag-hub/document/upload-file 或 /document/create-and-chunk
 * @throws 文件上传校验不通过或后端分块入库异常时提示错误
 */
async function submitCreateDoc() {
  submittingDoc.value = true;
  try {
    if (uploadMode.value === 'file') {
      if (!selectedDocFile.value) {
        ElMessage.warning('请选择需要上传的规范文档文件');
        submittingDoc.value = false;
        return;
      }
      const fd = new FormData();
      fd.append('file', selectedDocFile.value);
      fd.append('category_id', String(docForm.value.category_id));
      fd.append('chunk_strategy', docForm.value.chunk_strategy);
      fd.append('chunk_size', String(uploadChunkSize.value));
      fd.append('chunk_overlap', String(uploadChunkOverlap.value));
      fd.append('decision_mode', decisionMode.value);
      const res = await uploadDocumentFile(fd);
      docRadarPreview.value = res;
      ElMessage.success(`文档 [${res.doc_title}] 上传成功！Agent 采用 [${res.chosen_strategy}] 切分并持久化写入 Chroma 向量库！`);
    } else {
      if (!docForm.value.doc_title || !docForm.value.content) {
        ElMessage.warning('请填写文档标题与正文');
        submittingDoc.value = false;
        return;
      }
      const res = await createDocumentAndChunk({
        ...docForm.value,
        chunk_size: uploadChunkSize.value,
        chunk_overlap: uploadChunkOverlap.value,
        decision_mode: decisionMode.value
      });
      ElMessage.success(`文档录入成功！Agent 采用 [${res.selected_strategy}] 完成切分并物理持久化写入 ChromaDB！`);
    }
    addDocVisible.value = false;
    fetchDocuments();
    fetchCategories();
    loadModularConfig();
  } catch (err: any) {
    ElMessage.error(err.message || '文档创建切分失败');
  } finally {
    submittingDoc.value = false;
  }
}

/**
 * 打开文档切片抽屉并拉取切片详情
 * @param {DocumentItem} doc 目标文档数据实体
 * @returns {Promise<void>} 异步加载切片承诺
 * @route GET /api/v1/rag-hub/document/{docId}/chunks
 * @throws 获取切片列表失败时提示错误
 */
async function openChunkDrawer(doc: DocumentItem) {
  currentDoc.value = doc;
  chunkDrawerVisible.value = true;
  try {
    const chunks = await getDocumentChunks(doc.id);
    docChunks.value = chunks || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取切片失败');
  }
}

/**
 * 彻底物理删除文档及其 MySQL 切片与 Chroma 向量
 * @param {DocumentItem} row 选中的目标文档对象
 * @returns {Promise<void>} 异步删除操作承诺
 * @route DELETE /api/v1/rag-hub/document/{docId}
 * @throws 用户取消或后端物理清理异常时提示错误
 */
async function handleDeleteDoc(row: DocumentItem) {
  try {
    await ElMessageBox.confirm(`确认彻底删除文档《${row.doc_title}》并同步清空其 MySQL 切片与 Chroma 物理向量？`, '删除确认', {
      type: 'warning'
    });
    await deleteDocumentApi(row.id);
    ElMessage.success('文档与切片向量已彻底物理删除');
    fetchDocuments();
    fetchCategories();
    loadModularConfig();
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '删除失败');
  }
}

onMounted(() => {
  const role = userStore.currentUser.roleCode;
  if (role === 'secondary_user') {
    currentAgentId.value = 'agent_3';
  } else if (role === 'finance_auditor') {
    currentAgentId.value = 'agent_5';
  } else if (role === 'dept_manager') {
    currentAgentId.value = 'agent_1';
  }
  syncTabFromRoute();
  loadConnectivity();
  fetchCategories();
  fetchDocuments();
  loadModularConfig();
  loadAgentModelConfigs();
  handleRunInspection();
  refreshFeishuWsStatus();
  fetchMcpExternalStatus();
});
</script>

<style scoped>
.rag-agent-hub-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.kpi-card {
  padding: 12px 14px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
}

.kpi-val {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.kpi-unit {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-muted);
}

.tab-container-panel {
  padding: 16px 20px;
  border-radius: 14px;
}

.knowledge-split-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.tree-sidebar {
  width: 260px;
  padding: 14px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-divider);
}

.tree-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cat-tree-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cat-tree-item:hover {
  background: var(--bg-card-hover);
  color: var(--accent-primary);
}

.cat-tree-item.is-active {
  background: var(--accent-primary);
  color: #fff;
}

.cat-left {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
}

.doc-main-table-wrap {
  flex: 1 1 0%;
  min-width: 0;
  width: 0;
  display: flex;
  flex-direction: column;
  overflow-x: auto;
}

.pane-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0 12px 0;
  border-bottom: 1px solid var(--border-divider);
  margin-bottom: 12px;
}

.action-desc-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
}

.action-btn-group {
  display: flex;
  gap: 10px;
}

.config-layout {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.config-section {
  padding: 14px 18px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.config-section-title {
  font-size: 13px;
  color: var(--accent-primary);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.config-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  padding: 6px 10px;
  background: var(--bg-card-hover);
  border-radius: 6px;
}

.agent-sandbox-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 355px);
  min-height: 500px;
  max-height: calc(100vh - 355px);
  overflow: hidden;
}

.sandbox-menu {
  width: 300px;
  height: 100%;
  padding: 0;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border: 1px solid var(--border-divider);
  background: var(--bg-card);
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.sandbox-menu-header {
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-divider);
  background: var(--bg-card);
  flex-shrink: 0;
}

.sandbox-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0;
}

.sandbox-menu-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agent-menu-item {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-divider);
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  gap: 4px;
  user-select: none;
}

.agent-menu-item:hover {
  border-color: var(--accent-primary);
  background: var(--bg-hover);
  transform: translateY(-1px);
}

.agent-menu-item.is-selected {
  border-color: var(--accent-primary);
  background: rgba(56, 189, 248, 0.12);
  box-shadow: 0 0 0 1px var(--accent-primary) inset;
}

.agent-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.agent-item-name {
  font-size: 12.5px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-item-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
  font-weight: 700;
  flex-shrink: 0;
}

.agent-item-arch {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
}

.sandbox-chat-area {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-chunks-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chunk-card {
  padding: 10px 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chunk-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
}

.chunk-card-body {
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-secondary);
  background: var(--bg-card-hover);
  padding: 6px 8px;
  border-radius: 4px;
}

.status-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.chip-active {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.chip-info {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}
</style>
