<template>
  <!-- 浮动悬浮模式 (嵌入在业务视图中) -->
  <div v-if="floating" class="floating-agent-wrapper">
    <!-- 悬浮触发球 -->
    <div
      v-if="!isFloatingOpen"
      class="floating-agent-trigger glass-panel"
      :title="`唤起【${agentTitle}】(${architectureTag})`"
      @click="isFloatingOpen = true"
    >
      <div class="trigger-core">
        <svg class="trigger-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
        </svg>
        <span class="trigger-label font-bold">{{ agentTitle }}</span>
      </div>
      <span class="floating-pulse-ring" />
    </div>

    <!-- 浮动对话卡片窗口 -->
    <div v-else class="floating-agent-window glass-panel">
      <!-- 智能体顶部标题与架构标识栏（浮动窗口高质感双层结构，彻底消灭文字推挤与断行） -->
      <div class="widget-header floating-header-dual">
        <!-- 第一层：主要标识、状态指示与窗口操作 -->
        <div class="floating-header-primary">
          <div class="floating-header-title-box">
            <span class="agent-avatar-badge font-mono font-bold">{{ agentId.toUpperCase() }}</span>
            <span class="agent-name font-bold">{{ agentTitle }}</span>
          </div>
          <div class="floating-header-actions">
            <span class="status-chip chip-active">AI 守护中</span>
            <button class="btn-widget-icon" title="收起助手" @click="isFloatingOpen = false">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 第二层：架构特征微标签与能力控制开关栏 -->
        <div class="floating-header-secondary">
          <div class="floating-arch-badge font-mono" :title="`架构模式: ${architectureTag}`">
            <span class="arch-dot" />
            <span class="arch-text">{{ architectureTag }}</span>
          </div>
          <div class="floating-switches-bar">
            <div class="switch-capsule">
              <span class="switch-title">流式</span>
              <el-switch v-model="enableStream" size="small" />
            </div>
            <div class="switch-capsule">
              <span class="switch-title">深度思考</span>
              <el-switch v-model="enableDeepThinking" size="small" />
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷业务问题提问建议药丸 -->
      <div v-if="presetQuestions && presetQuestions.length > 0" class="preset-pill-group">
        <span
          v-for="(pq, idx) in presetQuestions"
          :key="idx"
          class="preset-pill"
          @click="sendQuery(pq)"
        >
          {{ pq }}
        </span>
      </div>

      <!-- 消息对话与架构特征可视化滚动区 -->
      <div ref="chatScrollWrap" class="chat-message-list">
        <div
          v-for="(msg, mIdx) in messages"
          :key="mIdx"
          class="message-row"
          :class="{ 'is-user': msg.role === 'user', 'is-agent': msg.role === 'agent' }"
        >
          <div class="message-bubble" :class="{ 'user-bubble': msg.role === 'user', 'agent-bubble': msg.role === 'agent' }">
            <!-- 子智能体协作徽章 -->
            <div v-if="msg.sub_agent_name" class="sub-agent-badge font-mono" style="font-size: 10.5px; color: var(--accent-primary); margin-bottom: 4px; font-weight: 700;">
              [协作子智能体: {{ msg.sub_agent_name }}]
            </div>

            <!-- 多模态图片预览 -->
            <div v-if="msg.image_url" class="msg-img-preview" style="margin: 4px 0;">
              <img :src="msg.image_url" style="max-height: 120px; border-radius: 6px; border: 1px solid var(--border-divider);" alt="多模态识图" />
            </div>

            <!-- DeepSeek 思考过程 -->
            <div v-if="msg.thought" class="think-card glass-panel" style="margin: 6px 0; border-radius: 6px; overflow: hidden; border: 1px solid rgba(56, 189, 248, 0.25); background: rgba(56, 189, 248, 0.04);">
              <div class="think-header" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; cursor: pointer; user-select: none;" @click="msg.showThink = !msg.showThink">
                <span class="font-mono text-accent" style="font-size: 11px; font-weight: 700;">DeepSeek 思考链</span>
                <span class="font-mono text-muted" style="font-size: 11px;">{{ msg.showThink ? '收起 ▴' : '展开 ▾' }}</span>
              </div>
              <div v-if="msg.showThink" class="think-body font-mono" style="padding: 8px 10px; font-size: 11.5px; line-height: 1.5; color: var(--text-muted); border-top: 1px dashed rgba(56, 189, 248, 0.2); white-space: pre-wrap;">{{ msg.thought }}</div>
            </div>

            <!-- OpenClaw 工具展开器 -->
            <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="tool-calls-container" style="margin: 8px 0;">
              <div v-for="(tc, tcIdx) in msg.toolCalls" :key="tcIdx" class="tool-call-card glass-panel" style="margin-bottom: 6px; border-radius: 6px; border: 1px solid var(--border-divider); background: var(--bg-card); overflow: hidden;">
                <div class="tool-call-header" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; cursor: pointer; user-select: none; background: rgba(14, 165, 233, 0.06);" @click="tc.isExpanded = !tc.isExpanded">
                  <div style="display: flex; gap: 6px; align-items: center;">
                    <span class="tool-badge font-mono text-accent" style="font-size: 11px; font-weight: 700;">TOOL: {{ tc.tool_name || tc.name || 'mcp_tool' }}</span>
                    <span v-if="tc.is_external_mcp || (tc.tool_name && (tc.tool_name.startsWith('mcp_external_') || tc.tool_name.startsWith('mcp_datetime_')))" class="status-chip chip-success" style="font-size: 10px; padding: 1px 5px; background: rgba(16, 185, 129, 0.15); color: #059669; font-weight: 700;">MCP EXTERNAL</span>
                    <span v-else class="status-chip chip-success" style="font-size: 10px; padding: 0 4px;">SUCCESS</span>
                    <span v-if="tc.latency_ms" class="text-muted font-mono" style="font-size: 10px;">{{ tc.latency_ms }}ms</span>
                  </div>
                  <span class="font-mono text-muted" style="font-size: 11px;">{{ tc.isExpanded ? '折叠 ▴' : '展开入参/出参 (JSON) ▾' }}</span>
                </div>
                <div v-if="tc.isExpanded" class="tool-call-payload font-mono" style="padding: 8px 10px; font-size: 11px; background: rgba(0, 0, 0, 0.02); border-top: 1px solid var(--border-divider);">
                  <div style="margin-bottom: 4px;"><strong>详细入参 (Arguments):</strong> <pre style="margin: 2px 0; background: var(--bg-hover); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider); overflow-x: auto;">{{ JSON.stringify(tc.args || tc.input || tc.parameters || tc.arguments || {}, null, 2) }}</pre></div>
                  <div><strong>响应回传 (Output):</strong> <pre style="margin: 2px 0; background: var(--bg-hover); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider); overflow-x: auto;">{{ JSON.stringify(tc.output || tc.result || tc.response || '执行成功', null, 2) }}</pre></div>
                </div>
              </div>
            </div>

            <!-- 多子智能体微信/Ins 群聊协同工作流气泡流 (Multi-Agent Bubble Stream) -->
            <div v-if="msg.subagentBubbles && msg.subagentBubbles.length > 0" class="subagent-chat-group" style="margin: 10px 0; display: flex; flex-direction: column; gap: 8px;">
              <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: var(--text-muted); padding-bottom: 4px; border-bottom: 1px dashed var(--border-divider);">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span class="font-bold font-mono">多子智能体协同推导网络 (Multi-Agent Collaboration):</span>
                  <span class="status-chip chip-active">{{ msg.subagentBubbles.length }} 位专家已协同</span>
                </div>
                <span class="font-mono text-xs text-muted">微信群聊流式制</span>
              </div>
              <div
                v-for="(sb, sbIdx) in msg.subagentBubbles"
                :key="sbIdx"
                class="subagent-bubble-card"
                style="display: flex; gap: 10px; padding: 10px 12px; border-radius: 8px; background: var(--bg-hover); border: 1px solid var(--border-divider); transition: all 0.2s ease;"
              >
                <!-- 子智能体专属头像 -->
                <div class="subagent-avatar" style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--color-primary, #3b82f6), #1d4ed8); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #fff; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                  {{ (sb.subagent_name || 'Agent').slice(0, 1) }}
                </div>
                <!-- 气泡内容 -->
                <div style="flex: 1; min-width: 0;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                      <span class="font-bold" style="font-size: 12px; color: var(--text-primary);">{{ sb.subagent_name }}</span>
                      <span class="role-badge" style="font-size: 10px; padding: 1px 6px; border-radius: 4px; background: rgba(59, 130, 246, 0.12); color: #3b82f6; font-family: monospace;">{{ sb.badge || sb.role }}</span>
                    </div>
                    <span class="status-chip chip-success" style="font-size: 9px; padding: 0 4px;">{{ sb.status || 'COMPLETED' }}</span>
                  </div>
                  <div style="font-size: 11.5px; line-height: 1.5; color: var(--text-secondary); white-space: pre-wrap;">{{ sb.content }}</div>

                  <!-- 若该子智能体调用了 MCP 工具，内联展示工具胶囊 -->
                  <div v-if="sb.tools && sb.tools.length > 0" style="margin-top: 6px;">
                    <div v-for="(t, tIdx) in sb.tools" :key="tIdx" style="font-size: 10.5px; font-family: monospace; background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.2); border-radius: 4px; padding: 4px 8px; margin-top: 4px;">
                      <div style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" @click="t.isExpanded = !t.isExpanded">
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <span style="color: var(--color-primary, #0284c7); font-weight: 600;">调用 MCP 工具: {{ t.tool_name || t.name }}</span>
                          <span v-if="t.is_external_mcp || (t.tool_name && (t.tool_name.startsWith('mcp_external_') || t.tool_name.startsWith('mcp_datetime_')))" style="font-size: 9.5px; padding: 1px 5px; border-radius: 3px; background: rgba(16, 185, 129, 0.15); color: #059669; font-weight: 700;">MCP EXTERNAL</span>
                          <span v-if="t.latency_ms" style="color: var(--text-muted); font-size: 10px; font-family: monospace;">{{ t.latency_ms }}ms</span>
                        </div>
                        <span style="color: var(--text-muted);">{{ t.isExpanded ? '收起 ▴' : '展开入参/出参 (JSON) ▾' }}</span>
                      </div>
                      <div v-if="t.isExpanded" style="margin-top: 4px; padding-top: 4px; border-top: 1px dashed var(--border-divider);">
                        <div><strong>详细入参 (Arguments / Parameters):</strong> <pre style="margin: 2px 0; max-height: 140px; overflow-y: auto; background: var(--bg-card); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider);">{{ JSON.stringify(t.args || t.input || t.parameters || t.arguments || {}, null, 2) }}</pre></div>
                        <div style="margin-top: 4px;"><strong>详细出参 (Output / Response):</strong> <pre style="margin: 2px 0; max-height: 140px; overflow-y: auto; background: var(--bg-card); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider);">{{ JSON.stringify(t.output || t.result || t.response || '执行成功', null, 2) }}</pre></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="message-content" style="white-space: pre-wrap;">{{ msg.content }}</div>

            <!-- 架构专属可视化 1: Agent 1 (Plan & Execute 3 步执行进度) -->
            <div v-if="msg.planSteps && msg.planSteps.length > 0" class="arch-visual-card plan-card">
              <div class="visual-card-title">Plan & Execute 规划分步执行跟踪</div>
              <div class="plan-steps-timeline">
                <div
                  v-for="st in msg.planSteps"
                  :key="st.step_id"
                  class="plan-step-item"
                >
                  <div class="step-num font-mono">{{ st.step_id }}</div>
                  <div class="step-info">
                    <div class="step-name font-bold">{{ st.step_title }} <span class="step-tool font-mono">[{{ st.tool_name }}]</span></div>
                    <div class="step-content">{{ st.content }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 架构专属可视化 2: Agent 2 (Router + Skill 0~100 置信度排行榜) -->
            <div v-if="msg.confidenceRankings && msg.confidenceRankings.length > 0" class="arch-visual-card router-card">
              <div class="visual-card-title">Router 技能意图分诊 0~100 置信度打分排行榜</div>
              <div class="ranking-list">
                <div
                  v-for="(rk, rIdx) in msg.confidenceRankings"
                  :key="rIdx"
                  class="ranking-item"
                  :class="{ 'is-top': rIdx === 0 }"
                >
                  <div class="rank-name font-mono">{{ rk.skill }}</div>
                  <div class="rank-bar-wrap">
                    <div class="rank-bar-fill" :style="{ width: rk.score + '%' }"></div>
                  </div>
                  <div class="rank-score font-mono font-bold">{{ rk.score }} 分</div>
                </div>
              </div>
            </div>

            <!-- 架构专属可视化 3: Agent 3 (LangGraph Human-in-the-loop 人机协同回环) -->
            <div
              v-if="msg.hitlStatus === 'PENDING_CONFIRMATION' || msg.hitlStatus === 'WAITING_HUMAN' || msg.hitlStatus === 'APPROVED' || msg.hitlStatus === 'REJECTED' || (msg.workflowSteps && msg.workflowSteps.length > 0)"
              class="arch-visual-card hitl-card"
            >
              <div class="visual-card-title" style="display: flex; justify-content: space-between; align-items: center;">
                <span>LangGraph 状态图与人机回环 (HITL) 流程节点</span>
                <span
                  class="font-mono text-xs px-2 py-0.5 rounded"
                  :style="{
                    background: msg.hitlStatus === 'APPROVED' ? 'rgba(34, 197, 94, 0.15)' : (msg.hitlStatus === 'REJECTED' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)'),
                    color: msg.hitlStatus === 'APPROVED' ? 'var(--color-success, #22c55e)' : (msg.hitlStatus === 'REJECTED' ? '#ef4444' : '#f59e0b')
                  }"
                >
                  {{ msg.hitlStatus === 'APPROVED' ? '审批通过 / 物理单据已落盘' : (msg.hitlStatus === 'REJECTED' ? '人工已驳回' : '中断挂起中 (PAUSED)') }}
                </span>
              </div>

              <!-- 4 节点流程步骤条 -->
              <div class="langgraph-stepper-wrap" style="margin: 10px 0 12px 0;">
                <el-steps :active="(msg.currentStepIndex ?? 2) + 1" finish-status="success" size="small" align-center>
                  <el-step title="临床意图解析" description="提取品名与数量" />
                  <el-step title="主库库存查验" description="核对可用余量" />
                  <el-step
                    title="人机协同审批"
                    :status="msg.hitlStatus === 'APPROVED' ? 'success' : (msg.hitlStatus === 'REJECTED' ? 'error' : 'process')"
                    description="护士长人工批示"
                  />
                  <el-step
                    title="单据物理落盘"
                    :status="msg.hitlStatus === 'APPROVED' ? 'success' : (msg.hitlStatus === 'REJECTED' ? 'wait' : 'wait')"
                    description="向主库排队出库"
                  />
                </el-steps>
              </div>

              <!-- 中断挂起状态: 展示拟申领明细与批示输入框 -->
              <div v-if="msg.hitlStatus === 'PENDING_CONFIRMATION' || msg.hitlStatus === 'WAITING_HUMAN'" class="hitl-action-box" style="background: var(--bg-hover); padding: 10px 12px; border-radius: 6px; border: 1px solid var(--border-divider);">
                <div v-if="msg.requisitionDraft" class="draft-info font-mono" style="font-size: 11.5px; margin-bottom: 8px; line-height: 1.6;">
                  <div>• 申领科室: <strong>{{ msg.requisitionDraft.dept_name || '临床二级库' }}</strong></div>
                  <div>• 拟申领品规: <strong>{{ msg.requisitionDraft.product_name }}</strong> (申请数量: <strong>{{ msg.requisitionDraft.apply_qty }}</strong>)</div>
                  <div>• 审批约束: 按照三甲医院内控规范，需人工填写审批批示意见后继续执行状态图。</div>
                </div>

                <div style="display: flex; gap: 8px; align-items: center; margin-top: 6px;">
                  <el-input
                    v-model="hitlReviewComment"
                    size="small"
                    placeholder="输入审核批示意见 (例如: 同意申领并下发排队出库)"
                    style="flex: 1;"
                  />
                  <el-button type="success" size="small" @click="handleHitlAction('CONFIRM', msg)">
                    同意下发 (CONFIRM)
                  </el-button>
                  <el-button type="danger" size="small" plain @click="handleHitlAction('REJECT', msg)">
                    驳回 (REJECT)
                  </el-button>
                </div>
              </div>

              <!-- 已审批通过或驳回的批示结果回显 -->
              <div v-else-if="msg.reviewComment" class="hitl-reviewed-note" style="margin-top: 6px; font-size: 11.5px; color: var(--text-muted);">
                <strong>历史审批意见:</strong> {{ msg.reviewComment }}
              </div>
            </div>

            <!-- 架构专属可视化 4: Agent 4 (ReAct 推理行动链 Thought/Action/Observation) -->
            <div v-if="msg.reactSteps && msg.reactSteps.length > 0" class="arch-visual-card react-card">
              <div class="visual-card-title">ReAct 循环推理过程 (Thought -> Action -> Observation)</div>
              <div class="react-step-loop">
                <div v-for="rst in msg.reactSteps" :key="rst.step" class="react-cycle-box">
                  <div class="react-line thought-line">
                    <span class="react-tag font-mono">Thought {{ rst.step }}</span>
                    <span>{{ rst.thought }}</span>
                  </div>
                  <div class="react-line action-line">
                    <span class="react-tag font-mono text-accent">Action</span>
                    <span class="font-mono text-accent">{{ rst.action }}</span>
                  </div>
                  <div class="react-line observation-line">
                    <span class="react-tag font-mono text-success">Observation</span>
                    <span>{{ rst.observation }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 架构专属可视化 5: Agent 5 (Blackboard 黑板 4 大专家协同面板) -->
            <div v-if="msg.blackboardData" class="arch-visual-card blackboard-card">
              <div class="visual-card-title">中央公共黑板多专家协同数据</div>
              <div class="bb-grid">
                <div class="bb-col">
                  <div class="bb-col-title font-bold">各科室消耗精算</div>
                  <div v-for="(v, k) in msg.blackboardData.dept_costs" :key="k" class="font-mono" style="font-size: 11px;">
                    {{ k }}: ¥{{ v }}
                  </div>
                </div>
                <div class="bb-col">
                  <div class="bb-col-title font-bold">盘点损耗核算</div>
                  <div v-for="(v, k) in msg.blackboardData.loss_data" :key="k" class="font-mono" style="font-size: 11px;">
                    {{ k }}: {{ v }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 架构专属可视化 6: Agent 6 (自省重写历程与引用溯源) -->
            <div v-if="msg.rewriteSteps && msg.rewriteSteps.length > 0" class="arch-visual-card rewrite-card">
              <div class="visual-card-title">Agentic RAG 查询自省重写历程 (上限3次选最优)</div>
              <div v-for="rw in msg.rewriteSteps" :key="rw.loop" class="rewrite-step-line font-mono" style="font-size: 11px;">
                轮次 {{ rw.loop }} [评分: {{ rw.score }}]: {{ rw.rewritten_query }} ({{ rw.feedback }})
              </div>
            </div>

            <div v-if="msg.citations && msg.citations.length > 0" class="citations-box">
              <div class="citations-title font-bold">知识库引用溯源 (精确至切片):</div>
              <div v-for="c in msg.citations" :key="c.citation_id" class="citation-tag font-mono">
                [{{ c.citation_id }}] {{ c.doc_code }} · {{ c.chunk_uid }} (相似度: {{ (c.score * 100).toFixed(1) }}%)
              </div>
            </div>

            <!-- 架构专属可视化 7: Modular RAG 热插拔算子生效凭证卡片 (图三算子真实落地凭证) -->
            <div v-if="msg.operatorProofs" class="arch-visual-card proof-card" style="margin-top: 10px; background: rgba(14, 165, 233, 0.04); border: 1px solid rgba(14, 165, 233, 0.2); border-radius: 8px; padding: 10px 12px;">
              <div class="visual-card-title" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-weight: 700; font-size: 12px; color: var(--color-primary, #0284c7);">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span class="font-mono">[Modular RAG 算子生效物理凭证]</span>
                  <span class="status-chip chip-success" style="font-size: 10px; padding: 0 4px;">100% 真实执行</span>
                </div>
                <span class="font-mono text-muted" style="font-size: 10.5px;">Self-RAG 幻觉防护网</span>
              </div>

              <!-- 算子 1: 查询消歧与领域重写 -->
              <div v-if="msg.operatorProofs.query_rewrite" style="margin-bottom: 8px; font-size: 11px; padding: 6px 8px; background: var(--bg-hover); border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                  <span class="font-bold text-accent">1. 查询重写与意图消歧 (Query Rewriter)</span>
                  <span class="font-mono text-xs" :style="{ color: msg.operatorProofs.query_rewrite.enabled ? 'var(--color-success, #22c55e)' : 'var(--text-muted)' }">
                    {{ msg.operatorProofs.query_rewrite.enabled ? '算子已启用 / 达标' : '算子已旁路透传' }}
                  </span>
                </div>
                <div v-if="msg.operatorProofs.query_rewrite.enabled" class="font-mono text-muted" style="line-height: 1.5;">
                  <div>• 原始口语输入: <span style="color: var(--text-primary);">"{{ msg.operatorProofs.query_rewrite.original_query }}"</span></div>
                  <div>• 实体消歧改写: <span style="color: var(--color-primary, #0284c7); font-weight: 600;">"{{ msg.operatorProofs.query_rewrite.rewritten_query }}"</span></div>
                  <div>• 改写质量评分: <strong class="text-success">{{ (msg.operatorProofs.query_rewrite.quality_score * 100).toFixed(0) }} 分</strong> ({{ msg.operatorProofs.query_rewrite.diff_summary }})</div>
                </div>
                <div v-else class="font-mono text-muted">
                  • 管理员在控制台关闭了重写算子，系统直接采用原始提问透传检索。
                </div>
              </div>

              <!-- 算子 2: Cross-Encoder 交叉重排与 ISREL 过滤拦截 -->
              <div v-if="msg.operatorProofs.isrel_rerank" style="margin-bottom: 8px; font-size: 11px; padding: 6px 8px; background: var(--bg-hover); border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                  <span class="font-bold text-accent">2. 交叉重排与最低相关性过滤 (ISREL Guard)</span>
                  <span class="font-mono text-xs" :style="{ color: msg.operatorProofs.isrel_rerank.status === 'BLOCKED' ? '#ef4444' : 'var(--color-success, #22c55e)' }">
                    {{ msg.operatorProofs.isrel_rerank.status === 'BLOCKED' ? '触发硬拦截 (BLOCKED)' : '重排通过 (PASSED)' }}
                  </span>
                </div>
                <div class="font-mono text-muted" style="line-height: 1.5;">
                  <div>• 候选池扫描: <strong>{{ msg.operatorProofs.isrel_rerank.candidates_scanned || 0 }} 篇</strong> | 存活保留: <strong class="text-success">{{ msg.operatorProofs.isrel_rerank.survived_count || 0 }} 篇</strong> | 过滤淘汰: <strong style="color: #ef4444;">{{ msg.operatorProofs.isrel_rerank.filtered_count || 0 }} 篇</strong></div>
                  <div>• 最高切片相关度: <strong :style="{ color: msg.operatorProofs.isrel_rerank.max_similarity >= (msg.operatorProofs.isrel_rerank.threshold || 0.35) ? 'var(--color-success, #22c55e)' : '#ef4444' }">{{ (msg.operatorProofs.isrel_rerank.max_similarity * 100).toFixed(1) }}%</strong> (设定最低阈值: {{ ((msg.operatorProofs.isrel_rerank.threshold || 0.35) * 100).toFixed(0) }}%)</div>
                  <div v-if="msg.operatorProofs.isrel_rerank.status === 'BLOCKED'" style="color: #ef4444; margin-top: 2px;">
                    [合规告警] 召回切片置信度未达标，系统已坚决熔断阻断大模型虚构事实！
                  </div>
                </div>
              </div>

              <!-- 算子 3: 答案事实忠实度自检 (Faithfulness Check) -->
              <div v-if="msg.operatorProofs.faithfulness" style="font-size: 11px; padding: 6px 8px; background: var(--bg-hover); border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                  <span class="font-bold text-accent">3. 答案事实忠实度反向交叉自检 (Faithfulness)</span>
                  <span class="font-mono text-xs" :style="{ color: msg.operatorProofs.faithfulness.passed ? 'var(--color-success, #22c55e)' : '#ef4444' }">
                    {{ msg.operatorProofs.faithfulness.passed ? '忠实度达标' : '待复核' }}
                  </span>
                </div>
                <div class="font-mono text-muted" style="line-height: 1.5;">
                  <div>• 事实忠实度评分: <strong class="text-success">{{ (msg.operatorProofs.faithfulness.score * 100).toFixed(0) }} 分</strong> (合规达标线: 80 分)</div>
                  <div>• 证据链实测: {{ msg.operatorProofs.faithfulness.overlap_metrics || '答案核心词与真实切片依据 100% 对应' }}</div>
                </div>
              </div>
            </div>

            <!-- 方案 C 落地: 智能体回答医护采纳建议与人工纠偏自演化操作卡片 -->
            <div v-if="msg.role === 'agent' && !msg.isStreaming" class="feedback-action-bar" style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-divider); display: flex; flex-direction: column; gap: 6px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="text-muted font-mono" style="font-size: 11px;">智能体知识自演化引擎</span>
                <div style="display: flex; gap: 6px;">
                  <el-button
                    size="small"
                    :type="msg.feedbackStatus === 'ACCEPTED' ? 'success' : 'default'"
                    :plain="msg.feedbackStatus !== 'ACCEPTED'"
                    style="font-size: 11px; padding: 3px 8px; height: 24px;"
                    @click="handleAcceptAdvice(msg)"
                  >
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 3px;">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                    {{ msg.feedbackStatus === 'ACCEPTED' ? '已采纳建议' : '采纳建议' }}
                  </el-button>
                  <el-button
                    size="small"
                    :type="msg.showCorrectionCard ? 'warning' : 'default'"
                    :plain="!msg.showCorrectionCard"
                    style="font-size: 11px; padding: 3px 8px; height: 24px;"
                    @click="msg.showCorrectionCard = !msg.showCorrectionCard"
                  >
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 3px;">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
                    </svg>
                    {{ msg.feedbackStatus === 'CORRECTED' ? '已人工纠偏' : '人工纠偏 / 院内规则' }}
                  </el-button>
                </div>
              </div>

              <!-- 展开的人工纠偏输入卡片 -->
              <div v-if="msg.showCorrectionCard" class="correction-card" style="background: rgba(var(--accent-primary-rgb), 0.04); border: 1px solid var(--border-divider); border-radius: 6px; padding: 8px 10px; margin-top: 4px;">
                <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 6px; font-weight: 600;">
                  临床专家补充规范 (将即时写入 Chroma 向量库 EXPERT_HUMAN_CORRECTION 分区):
                </div>
                <el-input
                  v-model="msg.correctionInput"
                  type="textarea"
                  :rows="2"
                  placeholder="例如: 院内规定高值介入支架若遇患者急诊过敏，需优先执行二级库就近退换并通知医务处备案..."
                  size="small"
                  style="font-size: 11px;"
                />
                <div style="display: flex; justify-content: flex-end; gap: 6px; margin-top: 6px;">
                  <el-button size="small" style="height: 22px; font-size: 11px;" @click="msg.showCorrectionCard = false">取消</el-button>
                  <el-button
                    type="primary"
                    size="small"
                    style="height: 22px; font-size: 11px;"
                    :loading="msg.submittingCorrection"
                    @click="handleSubmitCorrection(msg)"
                  >
                    提交记忆沉淀
                  </el-button>
                </div>
              </div>

              <!-- 纠偏成功提示 -->
              <div v-if="msg.feedbackStatus === 'CORRECTED'" style="font-size: 11px; color: var(--color-success); display: flex; align-items: center; gap: 4px;">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>专家纠偏规则已成功沉淀至 Chroma 物理向量库，下次对话将优先遵从！</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="loading" class="loading-indicator font-mono">
          智能体深度推理中 (LangSmith Trace 追踪中)...
        </div>
      </div>

      <!-- 底部输入框与操作栏 -->
      <div class="widget-footer">
        <el-input
          v-model="inputQuery"
          placeholder="输入业务指令或自然语言咨询..."
          size="small"
          @keyup.enter="handleSend"
        />
        <el-button type="primary" size="small" :loading="loading" @click="handleSend">
          执行
        </el-button>
      </div>
    </div>
  </div>

  <!-- 非 floating 模式：标准内嵌容器 -->
  <div v-else class="agent-chat-widget glass-panel">
    <!-- 智能体顶部标题与架构标识栏 -->
    <div class="widget-header">
      <div class="header-left">
        <span class="agent-avatar-badge font-mono font-bold">{{ agentId.toUpperCase() }}</span>
        <div class="agent-title-wrap">
          <div class="agent-name font-bold">{{ agentTitle }}</div>
          <div class="agent-arch font-mono">架构模式: {{ architectureTag }}</div>
        </div>
      </div>
      <div class="header-right" style="display: flex; align-items: center; gap: 10px;">
        <div style="display: flex; align-items: center; gap: 4px; font-size: 11px;">
          <span style="color: var(--text-muted);">流式</span>
          <el-switch v-model="enableStream" size="small" />
        </div>
        <div style="display: flex; align-items: center; gap: 4px; font-size: 11px;">
          <span style="color: var(--text-muted);">深度思考</span>
          <el-switch v-model="enableDeepThinking" size="small" />
        </div>
        <span class="status-chip chip-active">AI Agent 就绪</span>
      </div>
    </div>

    <!-- 快捷业务问题提问建议药丸 -->
    <div v-if="presetQuestions && presetQuestions.length > 0" class="preset-pill-group">
      <span
        v-for="(pq, idx) in presetQuestions"
        :key="idx"
        class="preset-pill"
        @click="sendQuery(pq)"
      >
        {{ pq }}
      </span>
    </div>

    <!-- 消息对话与架构特征可视化滚动区 -->
    <div ref="chatScrollWrap" class="chat-message-list">
      <div
        v-for="(msg, mIdx) in messages"
        :key="mIdx"
        class="message-row"
        :class="{ 'is-user': msg.role === 'user', 'is-agent': msg.role === 'agent' }"
      >
        <div class="message-bubble" :class="{ 'user-bubble': msg.role === 'user', 'agent-bubble': msg.role === 'agent' }">
          <!-- 子智能体协作徽章 -->
          <div v-if="msg.sub_agent_name" class="sub-agent-badge font-mono" style="font-size: 10.5px; color: var(--accent-primary); margin-bottom: 4px; font-weight: 700;">
            [协作子智能体: {{ msg.sub_agent_name }}]
          </div>

          <!-- 多模态实物与条码图片回显 -->
          <div v-if="msg.image_url" class="msg-img-preview" style="margin: 4px 0;">
            <img :src="msg.image_url" style="max-height: 120px; border-radius: 6px; border: 1px solid var(--border-divider);" alt="多模态识图" />
          </div>

          <!-- DeepSeek 风格思维推理思考过程 (<think>) -->
          <div v-if="msg.thought" class="think-card glass-panel" style="margin: 6px 0; border-radius: 6px; overflow: hidden; border: 1px solid rgba(56, 189, 248, 0.25); background: rgba(56, 189, 248, 0.04);">
            <div class="think-header" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; cursor: pointer; user-select: none;" @click="msg.showThink = !msg.showThink">
              <span class="font-mono text-accent" style="font-size: 11px; font-weight: 700;">DeepSeek 思考链 (Thinking Process)</span>
              <span class="font-mono text-muted" style="font-size: 11px;">{{ msg.showThink ? '收起 ▴' : '展开 ▾' }}</span>
            </div>
            <div v-if="msg.showThink" class="think-body font-mono" style="padding: 8px 10px; font-size: 11.5px; line-height: 1.5; color: var(--text-muted); border-top: 1px dashed rgba(56, 189, 248, 0.2); white-space: pre-wrap;">{{ msg.thought }}</div>
          </div>

          <!-- OpenClaw 风格工具调用展开器 (Tool Calls) -->
          <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="tool-calls-container" style="margin: 8px 0;">
            <div v-for="(tc, tcIdx) in msg.toolCalls" :key="tcIdx" class="tool-call-card glass-panel" style="margin-bottom: 6px; border-radius: 6px; border: 1px solid var(--border-divider); background: var(--bg-card); overflow: hidden;">
              <div class="tool-call-header" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; cursor: pointer; user-select: none; background: rgba(14, 165, 233, 0.06);" @click="tc.isExpanded = !tc.isExpanded">
                <div style="display: flex; gap: 6px; align-items: center;">
                  <span class="tool-badge font-mono text-accent" style="font-size: 11px; font-weight: 700;">TOOL: {{ tc.tool_name || tc.name || 'mcp_tool' }}</span>
                  <span v-if="tc.is_external_mcp || (tc.tool_name && (tc.tool_name.startsWith('mcp_external_') || tc.tool_name.startsWith('mcp_datetime_')))" class="status-chip chip-success" style="font-size: 10px; padding: 1px 5px; background: rgba(16, 185, 129, 0.15); color: #059669; font-weight: 700;">MCP EXTERNAL</span>
                  <span v-else class="status-chip chip-success" style="font-size: 10px; padding: 0 4px;">SUCCESS</span>
                  <span v-if="tc.latency_ms" class="text-muted font-mono" style="font-size: 10px;">{{ tc.latency_ms }}ms</span>
                </div>
                <span class="font-mono text-muted" style="font-size: 11px;">{{ tc.isExpanded ? '折叠入参/出参 ▴' : '展开入参/出参 (JSON) ▾' }}</span>
              </div>
              <div v-if="tc.isExpanded" class="tool-call-payload font-mono" style="padding: 8px 10px; font-size: 11px; background: rgba(0, 0, 0, 0.02); border-top: 1px solid var(--border-divider);">
                <div style="margin-bottom: 4px;"><strong>详细入参 (Arguments):</strong> <pre style="margin: 2px 0; background: var(--bg-hover); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider); overflow-x: auto;">{{ JSON.stringify(tc.args || tc.input || tc.parameters || tc.arguments || {}, null, 2) }}</pre></div>
                <div><strong>响应回传 (Output):</strong> <pre style="margin: 2px 0; background: var(--bg-hover); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider); overflow-x: auto;">{{ JSON.stringify(tc.output || tc.result || tc.response || '执行成功', null, 2) }}</pre></div>
              </div>
            </div>
          </div>

          <!-- 多子智能体微信/Ins 群聊协同工作流气泡流 (Multi-Agent Bubble Stream) -->
          <div v-if="msg.subagentBubbles && msg.subagentBubbles.length > 0" class="subagent-chat-group" style="margin: 10px 0; display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: var(--text-muted); padding-bottom: 4px; border-bottom: 1px dashed var(--border-divider);">
              <div style="display: flex; align-items: center; gap: 6px;">
                <span class="font-bold font-mono">多子智能体协同推导网络 (Multi-Agent Collaboration):</span>
                <span class="status-chip chip-active">{{ msg.subagentBubbles.length }} 个专家已入组响应</span>
              </div>
              <span class="font-mono text-xs text-muted">群聊制流式会话</span>
            </div>
            <div
              v-for="(sb, sbIdx) in msg.subagentBubbles"
              :key="sbIdx"
              class="subagent-bubble-card"
              style="display: flex; gap: 10px; padding: 10px 12px; border-radius: 8px; background: var(--bg-hover); border: 1px solid var(--border-divider); transition: all 0.2s ease;"
            >
              <!-- 子智能体专属头像 -->
              <div class="subagent-avatar" style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--color-primary, #3b82f6), #1d4ed8); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #fff; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                {{ (sb.subagent_name || 'Agent').slice(0, 1) }}
              </div>
              <!-- 气泡内容 -->
              <div style="flex: 1; min-width: 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span class="font-bold" style="font-size: 12px; color: var(--text-primary);">{{ sb.subagent_name }}</span>
                    <span class="role-badge" style="font-size: 10px; padding: 1px 6px; border-radius: 4px; background: rgba(59, 130, 246, 0.12); color: #3b82f6; font-family: monospace;">{{ sb.badge || sb.role }}</span>
                  </div>
                  <span class="status-chip chip-success" style="font-size: 9px; padding: 0 4px;">{{ sb.status || 'COMPLETED' }}</span>
                </div>
                <div style="font-size: 11.5px; line-height: 1.5; color: var(--text-secondary); white-space: pre-wrap;">{{ sb.content }}</div>

                <!-- 若该子智能体调用了 MCP 工具，内联展示工具胶囊 -->
                <div v-if="sb.tools && sb.tools.length > 0" style="margin-top: 6px;">
                  <div v-for="(t, tIdx) in sb.tools" :key="tIdx" style="font-size: 10.5px; font-family: monospace; background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.2); border-radius: 4px; padding: 4px 8px; margin-top: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" @click="t.isExpanded = !t.isExpanded">
                      <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="color: var(--color-primary, #0284c7); font-weight: 600;">调用 MCP 工具: {{ t.tool_name || t.name }}</span>
                        <span v-if="t.is_external_mcp || (t.tool_name && (t.tool_name.startsWith('mcp_external_') || t.tool_name.startsWith('mcp_datetime_')))" style="font-size: 9.5px; padding: 1px 5px; border-radius: 3px; background: rgba(16, 185, 129, 0.15); color: #059669; font-weight: 700;">MCP EXTERNAL</span>
                        <span v-if="t.latency_ms" style="color: var(--text-muted); font-size: 10px; font-family: monospace;">{{ t.latency_ms }}ms</span>
                      </div>
                      <span style="color: var(--text-muted);">{{ t.isExpanded ? '收起 ▴' : '展开入参/出参 (JSON) ▾' }}</span>
                    </div>
                    <div v-if="t.isExpanded" style="margin-top: 4px; padding-top: 4px; border-top: 1px dashed var(--border-divider);">
                      <div><strong>详细入参 (Arguments / Parameters):</strong> <pre style="margin: 2px 0; max-height: 140px; overflow-y: auto; background: var(--bg-card); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider);">{{ JSON.stringify(t.args || t.input || t.parameters || t.arguments || {}, null, 2) }}</pre></div>
                      <div style="margin-top: 4px;"><strong>详细出参 (Output / Response):</strong> <pre style="margin: 2px 0; max-height: 140px; overflow-y: auto; background: var(--bg-card); padding: 6px; border-radius: 4px; border: 1px solid var(--border-divider);">{{ JSON.stringify(t.output || t.result || t.response || '执行成功', null, 2) }}</pre></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 消息文本 -->
          <div class="message-content" style="white-space: pre-wrap;">{{ msg.content }}</div>

          <!-- 架构专属可视化 1: Agent 1 (Plan & Execute 3 步执行进度) -->
          <div v-if="msg.planSteps && msg.planSteps.length > 0" class="arch-visual-card plan-card">
            <div class="visual-card-title">Plan & Execute 规划分步执行跟踪</div>
            <div class="plan-steps-timeline">
              <div
                v-for="st in msg.planSteps"
                :key="st.step_id"
                class="plan-step-item"
              >
                <div class="step-num font-mono">{{ st.step_id }}</div>
                <div class="step-info">
                  <div class="step-name font-bold">{{ st.step_title }} <span class="step-tool font-mono">[{{ st.tool_name }}]</span></div>
                  <div class="step-content">{{ st.content }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 架构专属可视化 2: Agent 2 (Router + Skill 0~100 置信度排行榜) -->
          <div v-if="msg.confidenceRankings && msg.confidenceRankings.length > 0" class="arch-visual-card router-card">
            <div class="visual-card-title">Router 技能意图分诊 0~100 置信度打分排行榜</div>
            <div class="ranking-list">
              <div
                v-for="(rk, rIdx) in msg.confidenceRankings"
                :key="rIdx"
                class="ranking-item"
                :class="{ 'is-top': rIdx === 0 }"
              >
                <div class="rank-name font-mono">{{ rk.skill }}</div>
                <div class="rank-bar-wrap">
                  <div class="rank-bar-fill" :style="{ width: rk.score + '%' }"></div>
                </div>
                <div class="rank-score font-mono font-bold">{{ rk.score }} 分</div>
              </div>
            </div>
          </div>

          <!-- 架构专属可视化 3: Agent 3 (LangGraph Human-in-the-loop 人机协同回环) -->
          <div
            v-if="msg.hitlStatus === 'PENDING_CONFIRMATION' || msg.hitlStatus === 'WAITING_HUMAN' || msg.hitlStatus === 'APPROVED' || msg.hitlStatus === 'REJECTED' || (msg.workflowSteps && msg.workflowSteps.length > 0)"
            class="arch-visual-card hitl-card"
          >
            <div class="visual-card-title" style="display: flex; justify-content: space-between; align-items: center;">
              <span>LangGraph 状态图与人机回环 (HITL) 流程节点</span>
              <span
                class="font-mono text-xs px-2 py-0.5 rounded"
                :style="{
                  background: msg.hitlStatus === 'APPROVED' ? 'rgba(34, 197, 94, 0.15)' : (msg.hitlStatus === 'REJECTED' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)'),
                  color: msg.hitlStatus === 'APPROVED' ? 'var(--color-success, #22c55e)' : (msg.hitlStatus === 'REJECTED' ? '#ef4444' : '#f59e0b')
                }"
              >
                {{ msg.hitlStatus === 'APPROVED' ? '审批通过 / 物理单据已落盘' : (msg.hitlStatus === 'REJECTED' ? '人工已驳回' : '中断挂起中 (PAUSED)') }}
              </span>
            </div>

            <!-- 4 节点流程步骤条 -->
            <div class="langgraph-stepper-wrap" style="margin: 10px 0 12px 0;">
              <el-steps :active="(msg.currentStepIndex ?? 2) + 1" finish-status="success" size="small" align-center>
                <el-step title="临床意图解析" description="提取品名与数量" />
                <el-step title="主库库存查验" description="核对可用余量" />
                <el-step
                  title="人机协同审批"
                  :status="msg.hitlStatus === 'APPROVED' ? 'success' : (msg.hitlStatus === 'REJECTED' ? 'error' : 'process')"
                  description="护士长人工批示"
                />
                <el-step
                  title="单据物理落盘"
                  :status="msg.hitlStatus === 'APPROVED' ? 'success' : (msg.hitlStatus === 'REJECTED' ? 'wait' : 'wait')"
                  description="向主库排队出库"
                />
              </el-steps>
            </div>

            <!-- 中断挂起状态: 展示拟申领明细与批示输入框 -->
            <div v-if="msg.hitlStatus === 'PENDING_CONFIRMATION' || msg.hitlStatus === 'WAITING_HUMAN'" class="hitl-action-box" style="background: var(--bg-hover); padding: 10px 12px; border-radius: 6px; border: 1px solid var(--border-divider);">
              <div v-if="msg.requisitionDraft" class="draft-info font-mono" style="font-size: 11.5px; margin-bottom: 8px; line-height: 1.6;">
                <div>• 申领科室: <strong>{{ msg.requisitionDraft.dept_name || '临床二级库' }}</strong></div>
                <div>• 拟申领品规: <strong>{{ msg.requisitionDraft.product_name }}</strong> (申请数量: <strong>{{ msg.requisitionDraft.apply_qty }}</strong>)</div>
                <div>• 审批约束: 按照三甲医院内控规范，需人工填写审批批示意见后继续执行状态图。</div>
              </div>

              <div style="display: flex; gap: 8px; align-items: center; margin-top: 6px;">
                <el-input
                  v-model="hitlReviewComment"
                  size="small"
                  placeholder="输入审核批示意见 (例如: 同意申领并下发排队出库)"
                  style="flex: 1;"
                />
                <el-button type="success" size="small" @click="handleHitlAction('CONFIRM', msg)">
                  同意下发 (CONFIRM)
                </el-button>
                <el-button type="danger" size="small" plain @click="handleHitlAction('REJECT', msg)">
                  驳回 (REJECT)
                </el-button>
              </div>
            </div>

            <!-- 已审批通过或驳回的批示结果回显 -->
            <div v-else-if="msg.reviewComment" class="hitl-reviewed-note" style="margin-top: 6px; font-size: 11.5px; color: var(--text-muted);">
              <strong>历史审批意见:</strong> {{ msg.reviewComment }}
            </div>
          </div>

          <!-- 架构专属可视化 4: Agent 4 (ReAct 推理行动链 Thought/Action/Observation) -->
          <div v-if="msg.reactSteps && msg.reactSteps.length > 0" class="arch-visual-card react-card">
            <div class="visual-card-title">ReAct 循环推理过程 (Thought -> Action -> Observation)</div>
            <div class="react-step-loop">
              <div v-for="rst in msg.reactSteps" :key="rst.step" class="react-cycle-box">
                <div class="react-line thought-line">
                  <span class="react-tag font-mono">Thought {{ rst.step }}</span>
                  <span>{{ rst.thought }}</span>
                </div>
                <div class="react-line action-line">
                  <span class="react-tag font-mono text-accent">Action</span>
                  <span class="font-mono text-accent">{{ rst.action }}</span>
                </div>
                <div class="react-line observation-line">
                  <span class="react-tag font-mono text-success">Observation</span>
                  <span>{{ rst.observation }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 架构专属可视化 5: Agent 5 (Blackboard 黑板 4 大专家协同面板) -->
          <div v-if="msg.blackboardData" class="arch-visual-card blackboard-card">
            <div class="visual-card-title">中央公共黑板多专家协同数据</div>
            <div class="bb-grid">
              <div class="bb-col">
                <div class="bb-col-title font-bold">各科室消耗精算</div>
                <div v-for="(v, k) in msg.blackboardData.dept_costs" :key="k" class="font-mono" style="font-size: 11px;">
                  {{ k }}: ¥{{ v }}
                </div>
              </div>
              <div class="bb-col">
                <div class="bb-col-title font-bold">盘点损耗核算</div>
                <div v-for="(v, k) in msg.blackboardData.loss_data" :key="k" class="font-mono" style="font-size: 11px;">
                  {{ k }}: {{ v }}
                </div>
              </div>
            </div>
          </div>

          <!-- 架构专属可视化 6: Agent 6 (自省重写历程与引用溯源) -->
          <div v-if="msg.rewriteSteps && msg.rewriteSteps.length > 0" class="arch-visual-card rewrite-card">
            <div class="visual-card-title">Agentic RAG 查询自省重写历程 (上限3次选最优)</div>
            <div v-for="rw in msg.rewriteSteps" :key="rw.loop" class="rewrite-step-line font-mono" style="font-size: 11px;">
              轮次 {{ rw.loop }} [评分: {{ rw.score }}]: {{ rw.rewritten_query }} ({{ rw.feedback }})
            </div>
          </div>

          <div v-if="msg.citations && msg.citations.length > 0" class="citations-box">
            <div class="citations-title font-bold">知识库引用溯源 (精确至切片):</div>
            <div v-for="c in msg.citations" :key="c.citation_id" class="citation-tag font-mono">
              [{{ c.citation_id }}] {{ c.doc_code }} · {{ c.chunk_uid }} (相似度: {{ (c.score * 100).toFixed(1) }}%)
            </div>
          </div>

          <!-- 架构专属可视化 7: Modular RAG 热插拔算子生效凭证卡片 (图三算子真实落地凭证) -->
          <div v-if="msg.operatorProofs" class="arch-visual-card proof-card" style="margin-top: 10px; background: rgba(14, 165, 233, 0.04); border: 1px solid rgba(14, 165, 233, 0.2); border-radius: 8px; padding: 10px 12px;">
            <div class="visual-card-title" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-weight: 700; font-size: 12px; color: var(--color-primary, #0284c7);">
              <div style="display: flex; align-items: center; gap: 6px;">
                <span class="font-mono">[Modular RAG 算子生效物理凭证]</span>
                <span class="status-chip chip-success" style="font-size: 10px; padding: 0 4px;">100% 真实执行</span>
              </div>
              <span class="font-mono text-muted" style="font-size: 10.5px;">Self-RAG 幻觉防护网</span>
            </div>

            <!-- 算子 1: 查询消歧与领域重写 -->
            <div v-if="msg.operatorProofs.query_rewrite" style="margin-bottom: 8px; font-size: 11px; padding: 6px 8px; background: var(--bg-hover); border-radius: 6px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                <span class="font-bold text-accent">1. 查询重写与意图消歧 (Query Rewriter)</span>
                <span class="font-mono text-xs" :style="{ color: msg.operatorProofs.query_rewrite.enabled ? 'var(--color-success, #22c55e)' : 'var(--text-muted)' }">
                  {{ msg.operatorProofs.query_rewrite.enabled ? '算子已启用 / 达标' : '算子已旁路透传' }}
                </span>
              </div>
              <div v-if="msg.operatorProofs.query_rewrite.enabled" class="font-mono text-muted" style="line-height: 1.5;">
                <div>• 原始口语输入: <span style="color: var(--text-primary);">"{{ msg.operatorProofs.query_rewrite.original_query }}"</span></div>
                <div>• 实体消歧改写: <span style="color: var(--color-primary, #0284c7); font-weight: 600;">"{{ msg.operatorProofs.query_rewrite.rewritten_query }}"</span></div>
                <div>• 改写质量评分: <strong class="text-success">{{ (msg.operatorProofs.query_rewrite.quality_score * 100).toFixed(0) }} 分</strong> ({{ msg.operatorProofs.query_rewrite.diff_summary }})</div>
              </div>
              <div v-else class="font-mono text-muted">
                • 管理员在控制台关闭了重写算子，系统直接采用原始提问透传检索。
              </div>
            </div>

            <!-- 算子 2: Cross-Encoder 交叉重排与 ISREL 过滤拦截 -->
            <div v-if="msg.operatorProofs.isrel_rerank" style="margin-bottom: 8px; font-size: 11px; padding: 6px 8px; background: var(--bg-hover); border-radius: 6px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                <span class="font-bold text-accent">2. 交叉重排与最低相关性过滤 (ISREL Guard)</span>
                <span class="font-mono text-xs" :style="{ color: msg.operatorProofs.isrel_rerank.status === 'BLOCKED' ? '#ef4444' : 'var(--color-success, #22c55e)' }">
                  {{ msg.operatorProofs.isrel_rerank.status === 'BLOCKED' ? '触发硬拦截 (BLOCKED)' : '重排通过 (PASSED)' }}
                </span>
              </div>
              <div class="font-mono text-muted" style="line-height: 1.5;">
                <div>• 候选池扫描: <strong>{{ msg.operatorProofs.isrel_rerank.candidates_scanned || 0 }} 篇</strong> | 存活保留: <strong class="text-success">{{ msg.operatorProofs.isrel_rerank.survived_count || 0 }} 篇</strong> | 过滤淘汰: <strong style="color: #ef4444;">{{ msg.operatorProofs.isrel_rerank.filtered_count || 0 }} 篇</strong></div>
                <div>• 最高切片相关度: <strong :style="{ color: msg.operatorProofs.isrel_rerank.max_similarity >= (msg.operatorProofs.isrel_rerank.threshold || 0.35) ? 'var(--color-success, #22c55e)' : '#ef4444' }">{{ (msg.operatorProofs.isrel_rerank.max_similarity * 100).toFixed(1) }}%</strong> (设定最低阈值: {{ ((msg.operatorProofs.isrel_rerank.threshold || 0.35) * 100).toFixed(0) }}%)</div>
                <div v-if="msg.operatorProofs.isrel_rerank.status === 'BLOCKED'" style="color: #ef4444; margin-top: 2px;">
                  [合规告警] 召回切片置信度未达标，系统已坚决熔断阻断大模型虚构事实！
                </div>
              </div>
            </div>

            <!-- 算子 3: 答案事实忠实度自检 (Faithfulness Check) -->
            <div v-if="msg.operatorProofs.faithfulness" style="font-size: 11px; padding: 6px 8px; background: var(--bg-hover); border-radius: 6px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                <span class="font-bold text-accent">3. 答案事实忠实度反向交叉自检 (Faithfulness)</span>
                <span class="font-mono text-xs" :style="{ color: msg.operatorProofs.faithfulness.passed ? 'var(--color-success, #22c55e)' : '#ef4444' }">
                  {{ msg.operatorProofs.faithfulness.passed ? '忠实度达标' : '待复核' }}
                </span>
              </div>
              <div class="font-mono text-muted" style="line-height: 1.5;">
                <div>• 事实忠实度评分: <strong class="text-success">{{ (msg.operatorProofs.faithfulness.score * 100).toFixed(0) }} 分</strong> (合规达标线: 80 分)</div>
                <div>• 证据链实测: {{ msg.operatorProofs.faithfulness.overlap_metrics || '答案核心词与真实切片依据 100% 对应' }}</div>
              </div>
            </div>
          </div>

          <!-- 方案 C 落地: 智能体回答医护采纳建议与人工纠偏自演化操作卡片 -->
          <div v-if="msg.role === 'agent' && !msg.isStreaming" class="feedback-action-bar" style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-divider); display: flex; flex-direction: column; gap: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span class="text-muted font-mono" style="font-size: 11px;">智能体知识自演化引擎</span>
              <div style="display: flex; gap: 6px;">
                <el-button
                  size="small"
                  :type="msg.feedbackStatus === 'ACCEPTED' ? 'success' : 'default'"
                  :plain="msg.feedbackStatus !== 'ACCEPTED'"
                  style="font-size: 11px; padding: 3px 8px; height: 24px;"
                  @click="handleAcceptAdvice(msg)"
                >
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 3px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  {{ msg.feedbackStatus === 'ACCEPTED' ? '已采纳建议' : '采纳建议' }}
                </el-button>
                <el-button
                  size="small"
                  :type="msg.showCorrectionCard ? 'warning' : 'default'"
                  :plain="!msg.showCorrectionCard"
                  style="font-size: 11px; padding: 3px 8px; height: 24px;"
                  @click="msg.showCorrectionCard = !msg.showCorrectionCard"
                >
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 3px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
                  </svg>
                  {{ msg.feedbackStatus === 'CORRECTED' ? '已人工纠偏' : '人工纠偏 / 院内规则' }}
                </el-button>
              </div>
            </div>

            <!-- 展开的人工纠偏输入卡片 -->
            <div v-if="msg.showCorrectionCard" class="correction-card" style="background: rgba(var(--accent-primary-rgb), 0.04); border: 1px solid var(--border-divider); border-radius: 6px; padding: 8px 10px; margin-top: 4px;">
              <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 6px; font-weight: 600;">
                临床专家补充规范 (将即时写入 Chroma 向量库 EXPERT_HUMAN_CORRECTION 分区):
              </div>
              <el-input
                v-model="msg.correctionInput"
                type="textarea"
                :rows="2"
                placeholder="例如: 院内规定高值介入支架若遇患者急诊过敏，需优先执行二级库就近退换并通知医务处备案..."
                size="small"
                style="font-size: 11px;"
              />
              <div style="display: flex; justify-content: flex-end; gap: 6px; margin-top: 6px;">
                <el-button size="small" style="height: 22px; font-size: 11px;" @click="msg.showCorrectionCard = false">取消</el-button>
                <el-button
                  type="primary"
                  size="small"
                  style="height: 22px; font-size: 11px;"
                  :loading="msg.submittingCorrection"
                  @click="handleSubmitCorrection(msg)"
                >
                  提交记忆沉淀
                </el-button>
              </div>
            </div>

            <!-- 纠偏成功提示 -->
            <div v-if="msg.feedbackStatus === 'CORRECTED'" style="font-size: 11px; color: var(--color-success); display: flex; align-items: center; gap: 4px;">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>专家纠偏规则已成功沉淀至 Chroma 物理向量库，下次对话将优先遵从！</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-indicator font-mono">
        智能体深度推理中 (LangSmith Trace 追踪中)...
      </div>
    </div>

    <!-- 底部输入框与操作栏 -->
    <div class="widget-footer" style="display: flex; align-items: center; gap: 8px;">
      <input ref="imgInputRef" type="file" accept="image/*" style="display: none;" @change="handleImageSelected" />
      <button
        type="button"
        class="spd-btn-icon"
        title="上传多模态实物照片或高值 UDI 二维码"
        style="padding: 6px 8px; border-radius: 6px; border: 1px solid var(--border-divider); background: var(--bg-card); cursor: pointer; display: flex; align-items: center; justify-content: center;"
        @click="triggerImageUpload"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
        </svg>
      </button>

      <div v-if="stagedImage" class="staged-img-tag font-mono" style="display: flex; align-items: center; gap: 4px; padding: 2px 6px; border-radius: 4px; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.3); font-size: 11px; white-space: nowrap;">
        <span>{{ stagedImage.filename }}</span>
        <span v-if="stagedImage.detected_barcode" class="status-chip chip-success" style="font-size: 10px;">UDI已识</span>
        <button style="border: none; background: transparent; cursor: pointer; color: var(--text-muted);" @click="stagedImage = null">×</button>
      </div>

      <el-input
        v-model="inputQuery"
        placeholder="输入业务指令或自然语言咨询 (支持图片识图与UDI溯源)..."
        size="small"
        style="flex: 1;"
        @keyup.enter="handleSend"
      />
      <el-button type="primary" size="small" :loading="loading" @click="handleSend">
        执行
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { executeAgentCall, getAgentChatHistory, uploadChatImage, getModularRagConfig, submitAgentChatFeedback } from '@/api/ragAgentHubApi';

const props = withDefaults(
  defineProps<{
    agentId: string;
    agentTitle: string;
    architectureTag: string;
    presetQuestions?: string[];
    floating?: boolean;
  }>(),
  {
    presetQuestions: () => [],
    floating: false
  }
);

const isFloatingOpen = ref(false);
const enableStream = ref(true);
const enableDeepThinking = ref(true);

onMounted(async () => {
  try {
    const cfg = await getModularRagConfig();
    if (cfg) {
      if (typeof cfg.enable_streaming !== 'undefined') {
        enableStream.value = Boolean(cfg.enable_streaming);
      }
      if (typeof cfg.enable_deep_thinking !== 'undefined') {
        enableDeepThinking.value = Boolean(cfg.enable_deep_thinking);
      }
    }
  } catch (e) {
    // 保持默认 true
  }
});

interface ChatMessage {
  role: 'user' | 'agent' | 'sub_agent';
  content: string;
  thought?: string;
  showThink?: boolean;
  toolCalls?: any[];
  image_url?: string;
  sub_agent_name?: string;
  subagentBubbles?: any[];
  planSteps?: any[];
  confidenceRankings?: any[];
  hitlStatus?: string;
  workflowSteps?: any[];
  currentStepIndex?: number;
  requisitionDraft?: any;
  reviewComment?: string;
  statePayload?: any;
  reactSteps?: any[];
  blackboardData?: any;
  rewriteSteps?: any[];
  citations?: any[];
  operatorProofs?: any;
  isStreaming?: boolean;
  userQuery?: string;
  feedbackStatus?: 'NONE' | 'ACCEPTED' | 'CORRECTED';
  showCorrectionCard?: boolean;
  correctionInput?: string;
  submittingCorrection?: boolean;
}

const hitlReviewComment = ref('同意申领并下发排队出库');

const inputQuery = ref('');
const loading = ref(false);

const handleAcceptAdvice = async (msg: ChatMessage) => {
  if (msg.feedbackStatus === 'ACCEPTED') return;
  try {
    await submitAgentChatFeedback({
      agent_id: props.agentId,
      query: msg.userQuery || '用户业务指令',
      original_answer: msg.content,
      feedback_type: 'THUMBS_UP',
      operator_name: '临床医护专家'
    });
    msg.feedbackStatus = 'ACCEPTED';
    ElMessage.success('已采纳智能体建议，感谢您的专业反馈！');
  } catch (err: any) {
    ElMessage.error(err.message || '提交采纳反馈失败');
  }
};

const handleSubmitCorrection = async (msg: ChatMessage) => {
  if (!msg.correctionInput || !msg.correctionInput.trim()) {
    ElMessage.warning('请填写人工纠偏内容或标准化院内规则');
    return;
  }
  msg.submittingCorrection = true;
  try {
    await submitAgentChatFeedback({
      agent_id: props.agentId,
      query: msg.userQuery || '用户业务指令',
      original_answer: msg.content,
      feedback_type: 'CORRECTION',
      correction_text: msg.correctionInput.trim(),
      operator_name: '临床医护专家'
    });
    msg.feedbackStatus = 'CORRECTED';
    msg.showCorrectionCard = false;
    ElMessage.success('已成功将专家纠偏规则沉淀至 Chroma 物理向量库！');
  } catch (err: any) {
    ElMessage.error(err.message || '提交纠偏失败');
  } finally {
    msg.submittingCorrection = false;
  }
};

const chatScrollWrap = ref<HTMLElement | null>(null);

// 多模态图片上传
const imgInputRef = ref<HTMLInputElement | null>(null);
const stagedImage = ref<any>(null);

/**
 * 触发多模态图片文件选择器
 * @param 无
 * @returns {void}
 * @route 纯前端文件输入触发
 * @throws 无
 */
function triggerImageUpload() {
  imgInputRef.value?.click();
}

/**
 * 处理用户选择的多模态图片或高值 UDI 条码
 * @param {Event} e 表单变更事件
 * @returns {Promise<void>} 异步上传与识别处理承诺
 * @route POST /api/v1/rag-hub/chat/upload-image
 * @throws 图片解析失败或网络异常时提示错误
 */
async function handleImageSelected(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await uploadChatImage(fd);
      stagedImage.value = res;
      if (res.detected_barcode) {
        ElMessage.success(`成功识别高值 UDI 码: ${res.detected_barcode}`);
        inputQuery.value = `请对该高值耗材执行一物一码全链路追溯: ${res.detected_barcode}`;
      } else {
        ElMessage.success(`多模态图片 [${res.filename}] 上传解析完成`);
      }
    } catch (err: any) {
      ElMessage.error(err.message || '图片上传解析失败');
    }
  }
}

const messages = ref<ChatMessage[]>([]);

/**
 * 加载指定智能体与会话的历史聊天记录
 * @param {string} aid 智能体编号标识
 * @returns {Promise<void>} 异步加载承诺
 * @route GET /api/v1/rag-hub/chat/history
 * @throws 加载异常时回退至默认引导消息
 */
async function loadHistory(aid: string) {
  try {
    const list = await getAgentChatHistory(aid);
    if (list && list.length > 0) {
      messages.value = list.map((m: any) => ({
        role: m.role || 'agent',
        content: m.content || '',
        thought: m.thought || '',
        showThink: true,
        toolCalls: (m.tool_calls || []).map((tc: any) => ({
          tool_name: tc.tool_name || tc.name || 'mcp_tool',
          args: tc.args || tc.input || tc.parameters || tc.arguments || {},
          output: tc.output || tc.result || tc.response || '执行成功',
          status: tc.status || 'SUCCESS',
          isExpanded: false
        })),
        image_url: m.image_url,
        sub_agent_name: m.sub_agent_name
      }));
    } else {
      messages.value = [
        {
          role: 'agent',
          content: `您好！我是【${props.agentTitle}】，采用【${props.architectureTag}】模式，已准备好执行您的业务指令。`
        }
      ];
    }
  } catch {
    messages.value = [
      {
        role: 'agent',
        content: `您好！我是【${props.agentTitle}】，采用【${props.architectureTag}】模式，已准备好执行您的业务指令。`
      }
    ];
  }
}

watch(
  () => props.agentId,
  (newId) => {
    loadHistory(newId);
  },
  { immediate: true }
);

/**
 * 滚动消息列表容器至最底部
 * @param 无
 * @returns {void}
 * @route 纯前端 DOM 视口操作
 * @throws 无
 */
function scrollToBottom() {
  nextTick(() => {
    if (chatScrollWrap.value) {
      chatScrollWrap.value.scrollTop = chatScrollWrap.value.scrollHeight;
    }
  });
}

/**
 * 发送业务预设快捷提问或输入指令
 * @param {string} q 快捷提问指令文本
 * @returns {void}
 * @route 纯前端触发提交流程
 * @throws 无
 */
function sendQuery(q: string) {
  inputQuery.value = q;
  handleSend();
}

/**
 * 执行消息发送与全员 SSE 逐字打字机流式/同步调用流转
 * @param 无
 * @returns {Promise<void>} 异步流式调度执行承诺
 * @route POST /api/v1/rag-hub/agent/execute-stream 或 /agent/execute
 * @throws 流式通信异常或网络故障时自动降级回退
 */
async function handleSend() {
  const q = inputQuery.value.trim();
  if (!q && !stagedImage.value) return;

  const currentImg = stagedImage.value;
  stagedImage.value = null;

  messages.value.push({
    role: 'user',
    content: q || '请识别并分析该图片',
    image_url: currentImg?.image_url || ''
  });
  inputQuery.value = '';
  loading.value = true;
  scrollToBottom();

  // 1. 全员流式输出模式 (全员 1~6 号智能体解封 SSE 逐字打字机与多子智能体群聊气泡)
  if (enableStream.value) {
    const agentMsg: ChatMessage = {
      role: 'agent',
      content: '',
      thought: '',
      showThink: true,
      subagentBubbles: [],
      toolCalls: [],
      isStreaming: true,
      userQuery: q || `多模态图像识别: ${currentImg?.filename}`,
      feedbackStatus: 'NONE',
      showCorrectionCard: false,
      correctionInput: '',
      submittingCorrection: false
    };
    messages.value.push(agentMsg);
    scrollToBottom();

    try {
      const resp = await fetch('/api/v1/rag-hub/agent/execute-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          agent_id: props.agentId,
          query: q || `多模态图像识别: ${currentImg?.filename}`,
          enable_deep_thinking: enableDeepThinking.value ? 1 : 0
        })
      });

      if (!resp.ok) {
        throw new Error(`流式响应状态异常: ${resp.status}`);
      }

      const reader = resp.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data:')) {
              const dataStr = trimmed.slice(5).trim();
              if (!dataStr) continue;
              try {
                const parsed = JSON.parse(dataStr);
                // 多子智能体微信群聊气泡事件 (双向兼容 subagent_bubble 与 subagent_message)
                if (parsed.type === 'subagent_bubble' || parsed.type === 'subagent_message') {
                  if (!agentMsg.subagentBubbles) agentMsg.subagentBubbles = [];
                  const b = parsed.bubble || {};
                  const sid = parsed.subagent_id || b.subagent_id || (`subagent_${agentMsg.subagentBubbles.length + 1}`);
                  const sname = parsed.subagent_name || b.subagent_name || '协同专家智能体';
                  const sbadge = parsed.role_badge || parsed.badge || b.badge || b.role || 'Expert';
                  const savatar = parsed.avatar || b.avatar || 'expert';
                  const scontent = parsed.delta || parsed.content || b.content || '';
                  const sstatus = parsed.status || b.status || (parsed.done ? 'COMPLETED' : 'RUNNING');

                  // 提取子智能体调用的 MCP 工具并格式化真实入参出参
                  let rawTools: any[] = [];
                  if (Array.isArray(b.tools) && b.tools.length > 0) {
                    rawTools = b.tools;
                  } else if (Array.isArray(parsed.tools) && parsed.tools.length > 0) {
                    rawTools = parsed.tools;
                  } else if (parsed.mcp_tool_call) {
                    rawTools = [parsed.mcp_tool_call];
                  }

                  const formattedTools = rawTools.map((t: any) => {
                    if (typeof t === 'string') {
                      return { tool_name: t, isExpanded: false, args: {}, output: '执行成功', status: 'SUCCESS' };
                    }
                    return {
                      tool_name: t.tool_name || t.name || 'mcp_tool',
                      tool_title: t.tool_title || '',
                      args: t.args || t.input || t.parameters || t.arguments || {},
                      output: t.output || t.result || t.response || '执行成功',
                      status: t.status || 'SUCCESS',
                      is_external_mcp: t.is_external_mcp || (t.tool_name && (t.tool_name.startsWith('mcp_external_') || t.tool_name.startsWith('mcp_datetime_'))),
                      latency_ms: t.latency_ms,
                      isExpanded: Boolean(t.isExpanded)
                    };
                  });

                  // 依据 subagent_id 去重并实现流式增量追加与状态刷新
                  const existingIdx = agentMsg.subagentBubbles.findIndex((item: any) => item.subagent_id === sid);
                  if (existingIdx >= 0) {
                    const existing = agentMsg.subagentBubbles[existingIdx];
                    existing.subagent_name = sname;
                    existing.badge = sbadge;
                    existing.role = sbadge;
                    existing.avatar = savatar;
                    existing.status = sstatus;
                    if (scontent) {
                      existing.content = scontent;
                    }
                    if (formattedTools.length > 0) {
                      existing.tools = formattedTools;
                    }
                  } else {
                    agentMsg.subagentBubbles.push({
                      subagent_id: sid,
                      subagent_name: sname,
                      badge: sbadge,
                      role: sbadge,
                      avatar: savatar,
                      content: scontent,
                      status: sstatus,
                      tools: formattedTools
                    });
                  }
                } else if (parsed.type === 'reasoning') {
                  agentMsg.thought = (agentMsg.thought || '') + (parsed.delta || '');
                } else if (parsed.type === 'content') {
                  agentMsg.content += (parsed.delta || '');
                } else if (parsed.type === 'tool') {
                  if (!agentMsg.toolCalls) agentMsg.toolCalls = [];
                  const toolItem = typeof parsed.name === 'string'
                    ? {
                        tool_name: parsed.name,
                        isExpanded: false,
                        status: parsed.status || 'SUCCESS',
                        args: parsed.args || parsed.input || parsed.parameters || {},
                        output: parsed.output || parsed.result || '执行成功'
                      }
                    : {
                        tool_name: parsed.tool_name || parsed.name || 'mcp_tool',
                        isExpanded: false,
                        status: parsed.status || 'SUCCESS',
                        args: parsed.args || parsed.input || parsed.parameters || {},
                        output: parsed.output || parsed.result || '执行成功'
                      };
                  agentMsg.toolCalls.push(toolItem);
                } else if (parsed.type === 'done') {
                  agentMsg.isStreaming = false;
                  const d = parsed.data || {};
                  agentMsg.toolCalls = (d.tools_called || []).map((t: any) =>
                    typeof t === 'string'
                      ? { tool_name: t, isExpanded: false, args: {}, output: '执行成功', status: 'SUCCESS' }
                      : {
                          tool_name: t.tool_name || t.name || 'mcp_tool',
                          tool_title: t.tool_title || '',
                          args: t.args || t.input || t.parameters || t.arguments || {},
                          output: t.output || t.result || t.response || '执行成功',
                          status: t.status || 'SUCCESS',
                          is_external_mcp: t.is_external_mcp || (t.tool_name && (t.tool_name.startsWith('mcp_external_') || t.tool_name.startsWith('mcp_datetime_'))),
                          latency_ms: t.latency_ms,
                          isExpanded: false
                        }
                  );
                  agentMsg.planSteps = d.plan_steps;
                  agentMsg.confidenceRankings = d.confidence_rankings;
                  agentMsg.hitlStatus = d.state?.human_in_the_loop_status;
                  agentMsg.workflowSteps = d.state?.workflow_steps;
                  agentMsg.currentStepIndex = d.state?.current_step_index;
                  agentMsg.requisitionDraft = d.state?.requisition_draft;
                  agentMsg.statePayload = d.state;
                  agentMsg.reactSteps = d.react_steps;
                  agentMsg.blackboardData = d.blackboard_data;
                  agentMsg.citations = d.citations;
                  agentMsg.operatorProofs = d.operator_proofs;
                  if (!agentMsg.content) {
                    agentMsg.content = d.final_summary || d.final_answer || '';
                  }
                } else if (parsed.type === 'error') {
                  agentMsg.content += `\n[流式错误提示] ${parsed.message || ''}`;
                }
                scrollToBottom();
              } catch (e) {
                // 忽略未闭合碎片
              }
            }
          }
        }
      }

      if (!agentMsg.content && !agentMsg.thought) {
        agentMsg.content = '指令已响应完成。';
      }
    } catch (err: any) {
      console.warn('流式异常，回退常规调用:', err);
      try {
        const res = await executeAgentCall({
          agent_id: props.agentId,
          query: q || `多模态图像识别: ${currentImg?.filename}`
        });
        agentMsg.content = res.final_summary || res.final_answer || '任务执行完毕。';
        agentMsg.thought = res.thought || res.thought_process || '';
        agentMsg.toolCalls = (res.tools_called || []).map((t: any) =>
          typeof t === 'string'
            ? { tool_name: t, isExpanded: false, args: {}, output: '执行成功', status: 'SUCCESS' }
            : {
                tool_name: t.tool_name || t.name || 'mcp_tool',
                tool_title: t.tool_title || '',
                args: t.args || t.input || t.parameters || t.arguments || {},
                output: t.output || t.result || t.response || '执行成功',
                status: t.status || 'SUCCESS',
                is_external_mcp: t.is_external_mcp || (t.tool_name && (t.tool_name.startsWith('mcp_external_') || t.tool_name.startsWith('mcp_datetime_'))),
                latency_ms: t.latency_ms,
                isExpanded: false
              }
        );
        agentMsg.planSteps = res.plan_steps;
        agentMsg.confidenceRankings = res.confidence_rankings;
        agentMsg.hitlStatus = res.state?.human_in_the_loop_status;
        agentMsg.workflowSteps = res.state?.workflow_steps;
        agentMsg.currentStepIndex = res.state?.current_step_index;
        agentMsg.requisitionDraft = res.state?.requisition_draft;
        agentMsg.statePayload = res.state;
        agentMsg.reactSteps = res.react_steps;
        agentMsg.blackboardData = res.blackboard_data;
        agentMsg.citations = res.citations;
        agentMsg.operatorProofs = res.operator_proofs;
        if (res.subagent_bubbles && Array.isArray(res.subagent_bubbles)) {
          agentMsg.subagentBubbles = res.subagent_bubbles.map((b: any) => ({
            ...b,
            tools: (b.tools || []).map((t: any) =>
              typeof t === 'string'
                ? { tool_name: t, isExpanded: false, args: {}, output: '执行成功' }
                : {
                    tool_name: t.tool_name || t.name || 'mcp_tool',
                    tool_title: t.tool_title || '',
                    args: t.args || t.input || t.parameters || t.arguments || {},
                    output: t.output || t.result || t.response || '执行成功',
                    is_external_mcp: t.is_external_mcp || (t.tool_name && (t.tool_name.startsWith('mcp_external_') || t.tool_name.startsWith('mcp_datetime_'))),
                    latency_ms: t.latency_ms,
                    isExpanded: false
                  }
            )
          }));
        }
      } catch (fallbackErr: any) {
        agentMsg.content = `[智能体调用异常] ${fallbackErr.message || '请检查模型网络连通性'}`;
      }
    } finally {
      loading.value = false;
      scrollToBottom();
    }
    return;
  }

  // 2. 常规同步非流式模式
  try {
    const res = await executeAgentCall({
      agent_id: props.agentId,
      query: q || `多模态图像识别: ${currentImg?.filename}`
    });

    const thoughtText = res.thought || res.thought_process || '';
    const tools = (res.tools_called || []).map((t: any) =>
      typeof t === 'string'
        ? { tool_name: t, isExpanded: false, args: {}, output: '执行成功', status: 'SUCCESS' }
        : {
            tool_name: t.tool_name || t.name || 'mcp_tool',
            args: t.args || t.input || t.parameters || t.arguments || {},
            output: t.output || t.result || t.response || '执行成功',
            status: t.status || 'SUCCESS',
            isExpanded: false
          }
    );

    const subBubbles = (res.subagent_bubbles || []).map((b: any) => ({
      ...b,
      tools: (b.tools || []).map((t: any) =>
        typeof t === 'string'
          ? { tool_name: t, isExpanded: false, args: {}, output: '执行成功' }
          : {
              tool_name: t.tool_name || t.name || 'mcp_tool',
              args: t.args || t.input || t.parameters || t.arguments || {},
              output: t.output || t.result || t.response || '执行成功',
              isExpanded: false
            }
      )
    }));

    const agentMsg: ChatMessage = {
      role: 'agent',
      content: res.final_summary || res.final_answer || '任务执行完毕。',
      thought: thoughtText,
      showThink: true,
      toolCalls: tools,
      subagentBubbles: subBubbles,
      planSteps: res.plan_steps,
      confidenceRankings: res.confidence_rankings,
      hitlStatus: res.state?.human_in_the_loop_status,
      workflowSteps: res.state?.workflow_steps,
      currentStepIndex: res.state?.current_step_index,
      requisitionDraft: res.state?.requisition_draft,
      statePayload: res.state,
      reactSteps: res.react_steps,
      blackboardData: res.blackboard_data,
      rewriteSteps: res.rewrite_steps,
      citations: res.citations,
      operatorProofs: res.operator_proofs,
      isStreaming: false,
      userQuery: q || `多模态图像识别: ${currentImg?.filename}`,
      feedbackStatus: 'NONE',
      showCorrectionCard: false,
      correctionInput: ''
    };

    messages.value.push(agentMsg);
  } catch (err: any) {
    ElMessage.error(err.message || '智能体执行失败');
    messages.value.push({
      role: 'agent',
      content: `[智能体异常熔断] ${err.message || '系统服务调用异常，已触发安全降级保护。'}`
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
}

/**
 * 处理 LangGraph 人机回环 (HITL) 签批或驳回确认
 * @param {'CONFIRM' | 'REJECT'} action 人机审批决策动作
 * @param {ChatMessage} msg 当前被操作的对话消息实体
 * @returns {Promise<void>} 异步状态机恢复执行承诺
 * @route POST /api/v1/rag-hub/agent/execute
 * @throws 审批恢复异常时提示错误
 */
async function handleHitlAction(action: 'CONFIRM' | 'REJECT', msg: ChatMessage) {
  loading.value = true;
  try {
    const res = await executeAgentCall({
      agent_id: props.agentId,
      query: action === 'CONFIRM' ? '确认提交申领单' : '驳回申领单',
      resume_action: action,
      state_payload: msg.statePayload,
      review_comment: hitlReviewComment.value
    });

    msg.hitlStatus = res.state?.human_in_the_loop_status || (action === 'CONFIRM' ? 'APPROVED' : 'REJECTED');
    msg.currentStepIndex = res.state?.current_step_index ?? 3;
    msg.reviewComment = hitlReviewComment.value;

    messages.value.push({
      role: 'agent',
      content: res.final_answer || res.state?.final_response || '人机回环流程已执行完毕。',
      thought: res.thought || '人机回环审批处理完毕。',
      workflowSteps: res.state?.workflow_steps || msg.workflowSteps,
      currentStepIndex: res.state?.current_step_index ?? 3,
      hitlStatus: msg.hitlStatus,
      reviewComment: hitlReviewComment.value
    });
    ElMessage.success(action === 'CONFIRM' ? '人机审批已通过，请领单已物理落盘！' : '申领单已成功驳回');
  } catch (err: any) {
    ElMessage.error(err.message || '审批处理失败');
  } finally {
    loading.value = false;
    scrollToBottom();
  }
}
</script>

<style scoped>
.agent-chat-widget {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-divider);
  background: var(--bg-card);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-divider);
  background: var(--bg-card);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-avatar-badge {
  padding: 4px 8px;
  background: var(--accent-gradient);
  color: #fff;
  border-radius: 6px;
  font-size: 11px;
}

.agent-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-name {
  font-size: 13px;
  color: var(--text-primary);
}

.agent-arch {
  font-size: 11px;
  color: var(--text-muted);
}

.preset-pill-group {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-card-hover);
  overflow-x: auto;
  border-bottom: 1px solid var(--border-divider);
  flex-shrink: 0;
}

.preset-pill {
  padding: 2px 10px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-divider);
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.preset-pill:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.chat-message-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-row {
  display: flex;
}

.message-row.is-user {
  justify-content: flex-end;
}

.message-row.is-agent {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.5;
}

.user-bubble {
  background: var(--accent-primary);
  color: #fff;
}

.agent-bubble {
  background: var(--bg-card);
  border: 1px solid var(--border-divider);
  color: var(--text-primary);
}

.arch-visual-card {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--bg-card-hover);
  border: 1px solid var(--border-divider);
}

.visual-card-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent-primary);
  margin-bottom: 6px;
}

.plan-steps-timeline {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.plan-step-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 11px;
}

.step-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.step-tool {
  color: var(--accent-primary);
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.ranking-item.is-top {
  font-weight: 700;
  color: var(--accent-primary);
}

.rank-bar-wrap {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--border-divider);
  overflow: hidden;
}

.rank-bar-fill {
  height: 100%;
  background: var(--accent-primary);
}

.react-cycle-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--border-divider);
}

.react-line {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 11px;
}

.react-tag {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 3px;
  background: var(--bg-card);
  border: 1px solid var(--border-divider);
}

.bb-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.bb-col-title {
  font-size: 11px;
  color: var(--accent-primary);
  margin-bottom: 4px;
}

.citations-box {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border-divider);
}

.citation-tag {
  font-size: 10px;
  color: var(--accent-primary);
  margin-top: 2px;
}

.widget-footer {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid var(--border-divider);
  background: var(--bg-card);
  flex-shrink: 0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.02);
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
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.loading-indicator {
  font-size: 11px;
  color: var(--accent-primary);
  text-align: center;
  padding: 6px 0;
}

/* 浮动助手悬浮球与窗口 */
.floating-agent-wrapper {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 2100;
}

.floating-agent-trigger {
  position: relative;
  display: flex;
  align-items: center;
  padding: 10px 18px;
  border-radius: 30px;
  background: var(--bg-card);
  border: 1px solid var(--accent-primary);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  cursor: pointer;
  user-select: none;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.floating-agent-trigger:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
}

.trigger-core {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--accent-primary);
}

.trigger-label {
  font-size: 13px;
  color: var(--text-primary);
}

.floating-agent-window {
  width: 470px;
  height: 580px;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border-divider);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.28);
  background: var(--bg-card);
}

/* 浮动助手高质感双层头部 */
.floating-header-dual {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 16px 10px 16px;
  border-bottom: 1px solid var(--border-divider);
  background: var(--bg-card);
  flex-shrink: 0;
}

.floating-header-primary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 10px;
}

.floating-header-title-box {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.floating-header-title-box .agent-name {
  font-size: 13.5px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.floating-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.floating-header-secondary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding-top: 6px;
  border-top: 1px dashed var(--border-divider);
}

.floating-arch-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-card-hover);
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid var(--border-divider);
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.floating-arch-badge .arch-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-primary);
  flex-shrink: 0;
}

.floating-switches-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.switch-capsule {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  white-space: nowrap;
  user-select: none;
}

.switch-title {
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.btn-widget-icon {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, color 0.2s ease;
}

.btn-widget-icon:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
</style>
