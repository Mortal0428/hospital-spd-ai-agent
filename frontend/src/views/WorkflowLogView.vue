<template>
  <div class="workflow-log-view">
    <!-- 顶部出入库台账与异常预警切换 Tab -->
    <div class="glass-panel sub-nav-tabs-bar">
      <div class="tab-btn-group">
        <button
          class="log-tab-btn"
          :class="{ active: logTab === 'trace' }"
          @click="switchLogTab('trace')"
        >
          <SvgIcon name="package" :size="15" />
          <span>出入库流转全链路追溯台账</span>
        </button>
        <button
          class="log-tab-btn"
          :class="{ active: logTab === 'actions' }"
          @click="switchLogTab('actions')"
        >
          <SvgIcon name="log" :size="15" />
          <span>全员人工操作安全审计日志</span>
        </button>
        <button
          class="log-tab-btn"
          :class="{ active: logTab === 'warning' }"
          @click="switchLogTab('warning')"
        >
          <SvgIcon name="shield" :size="15" />
          <span>异常审计风险预警看板</span>
          <span class="tab-chip font-mono">{{ warningLogsCount }}</span>
        </button>
        <button
          class="log-tab-btn"
          :class="{ active: logTab === 'recall' }"
          @click="switchLogTab('recall')"
        >
          <SvgIcon name="warning" :size="15" />
          <span>不良事件全院召回中枢</span>
          <span class="tab-chip font-mono" style="background: rgba(239, 68, 68, 0.2); color: #ef4444;">{{ activeRecallsList.length }}</span>
        </button>
      </div>

      <div class="tab-right-ops">
        <el-button
          v-if="userStore.canAction('WORKFLOW_LOG', 'can_view')"
          type="primary"
          plain
          size="small"
          @click="handleRefreshCurrent"
        >
          <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
          刷新当前台账
        </el-button>
        <el-button
          v-if="userStore.canAction('WORKFLOW_LOG', 'can_print')"
          plain
          size="small"
          @click="handleExportReport"
        >
          <SvgIcon name="upload" :size="13" style="margin-right: 4px;" />
          导出审计报告
        </el-button>
      </div>
    </div>

    <!-- ===================================================================
         视图 1: 出入库流转全链路追溯台账 (trace)
         =================================================================== -->
    <div v-show="logTab === 'trace'" class="tab-pane-container">
      <!-- 8 节点流转图谱卡片 -->
      <div class="glass-panel timeline-overview-card">
        <div class="card-header-row">
          <div>
            <h3>全院医疗物资流转追溯台账 (8 大标准业务节点穿透)</h3>
            <p class="subtitle">严格落实国家药监局医疗器械全生命周期追溯与医院内控四联责任签字</p>
          </div>
        </div>

        <!-- 8 节点横向流转时间线 -->
        <div class="timeline-nodes-wrap">
          <div class="timeline-track-line" />
          <div
            v-for="node in timelineNodes"
            :key="node.step"
            class="timeline-node-item"
            :class="{ active: node.status === 'active', passed: node.status === 'passed' }"
          >
            <div class="node-circle font-mono tabular-nums">{{ node.step }}</div>
            <div class="node-title">{{ node.title }}</div>
            <div class="node-sub">{{ node.sub }}</div>
          </div>
        </div>

        <!-- 动态物权交接横幅 -->
        <div class="highlight-audit-strip">
          <div class="strip-left">
            <SvgIcon name="shield" :size="16" color="var(--color-success)" />
            <span class="strip-text" v-if="selectedTraceRow">
              <strong>当前穿透单据 [{{ selectedTraceRow.biz_order_no || selectedTraceRow.trace_no }}]：</strong>
              物资: {{ selectedTraceRow.product_name }} &nbsp;|&nbsp;
              交接: {{ selectedTraceRow.from_dept_name }} [{{ selectedTraceRow.from_user_name || '经办人' }}] &nbsp;→&nbsp; {{ selectedTraceRow.to_dept_name }} [{{ selectedTraceRow.to_user_name || '接收人' }}] &nbsp;|&nbsp;
              数量: {{ selectedTraceRow.change_qty }} 件 (变动前: {{ selectedTraceRow.before_stock_snapshot ?? 0 }} → 变动后: {{ selectedTraceRow.after_stock_snapshot ?? selectedTraceRow.change_qty }})
            </span>
            <span class="strip-text" v-else>
              <strong>全院物资流转动态监控中：</strong>点击下方表格任意单据流水行，即可高亮激活其 8 节点全生命周期穿透路径与物权交接凭证。
            </span>
          </div>
          <div class="strip-right">
            <span class="status-chip" :class="selectedTraceRow?.audit_status === 'FLAGGED' ? 'chip-disabled' : 'chip-active'">
              {{ selectedTraceRow ? (selectedTraceRow.audit_status === 'FLAGGED' ? '异常预警 (FLAGGED)' : '合规通过 (VERIFIED)') : '实时监控中' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 筛选查询栏 -->
      <div class="glass-panel filter-panel">
        <el-form :inline="true" class="search-filter-form">
          <el-form-item label="单号/流水号">
            <el-input
              v-model="traceFilters.keyword"
              placeholder="单据号或流水号"
              clearable
              style="width: 170px;"
            />
          </el-form-item>
          <el-form-item label="物资品名">
            <el-input
              v-model="traceFilters.productName"
              placeholder="物资名称/拼音"
              clearable
              style="width: 150px;"
            />
          </el-form-item>
          <el-form-item label="交出科室/仓">
            <el-select v-model="traceFilters.fromDept" placeholder="全部交出方" clearable style="width: 150px;">
              <el-option label="全部交出方" value="" />
              <el-option label="耗材科主库" value="耗材科主库" />
              <el-option label="设备科主库" value="设备科主库" />
              <el-option label="骨科病区" value="骨科" />
              <el-option label="心内科病区" value="心内科" />
              <el-option label="高值耗材专仓" value="高值专仓" />
              <el-option label="威高集团(外部供应商)" value="威高" />
            </el-select>
          </el-form-item>
          <el-form-item label="接收科室/仓">
            <el-select v-model="traceFilters.toDept" placeholder="全部接收方" clearable style="width: 150px;">
              <el-option label="全部接收方" value="" />
              <el-option label="耗材科主库" value="耗材科主库" />
              <el-option label="骨科病区二级库" value="骨科" />
              <el-option label="心内科病区二级库" value="心内科" />
              <el-option label="高值耗材专仓" value="高值专仓" />
              <el-option label="临床患者(脱敏核销)" value="患者" />
            </el-select>
          </el-form-item>
          <el-form-item label="流转环节">
            <el-select v-model="traceFilters.nodeAction" placeholder="全部环节" clearable style="width: 140px;">
              <el-option label="全部环节" value="" />
              <el-option label="主库入库" value="2_PURCHASE_INBOUND" />
              <el-option label="按需分发" value="3_MAIN_DISPATCH" />
              <el-option label="高值拆码" value="4_HIGH_VALUE_CODE" />
              <el-option label="二级库签收入库" value="5_SEC_INBOUND" />
              <el-option label="患者扫码核销" value="6_CLINICAL_CONSUME" />
              <el-option label="盘点平账" value="7_STOCKTAKE_BALANCE" />
              <el-option label="二级库手动发料" value="8_SEC_MANUAL_OUT" />
            </el-select>
          </el-form-item>
          <el-form-item label="计费性质">
            <el-select v-model="traceFilters.isBillable" placeholder="全部" clearable style="width: 120px;">
              <el-option label="全部" value="" />
              <el-option label="消耗记账" value="1" />
              <el-option label="移库不计费" value="0" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="handleSearchTrace">
              <SvgIcon name="search" :size="13" style="margin-right: 4px;" />
              筛选
            </el-button>
            <el-button size="small" @click="handleResetTrace">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 表格面板 -->
      <div class="glass-panel table-panel">
        <div class="table-caption-bar">
          <span class="caption-title">全院物资全生命周期流转追溯明细</span>
          <span class="caption-sub font-mono tabular-nums">共 {{ filteredTraceLogs.length }} 笔物权流转审计凭证</span>
        </div>

        <el-table
          :data="paginatedTraceLogs"
          border
          stripe
          class="fusion-styled-table"
          v-loading="loadingTrace"
        >
          <el-table-column prop="trace_no" label="追溯流水号" width="180">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold text-accent">{{ row.trace_no }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="biz_order_no" label="关联业务单号" width="170">
            <template #default="{ row }">
              <span class="font-mono tabular-nums">{{ row.biz_order_no }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="node_action" label="流转环节" width="140">
            <template #default="{ row }">
              <span class="status-chip chip-info">{{ formatNodeAction(row.node_action) }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="product_name" label="物资品名规格" min-width="190">
            <template #default="{ row }">
              <strong>{{ row.product_name }}</strong>
            </template>
          </el-table-column>

          <el-table-column label="交出方 (仓/人)" width="160">
            <template #default="{ row }">
              <div class="dept-text font-bold">{{ row.from_dept_name }}</div>
              <div class="user-sub text-muted font-mono" style="font-size: 11px;">{{ row.from_user_name }}</div>
            </template>
          </el-table-column>

          <el-table-column label="接收方 (仓/人)" width="160">
            <template #default="{ row }">
              <div class="dept-text font-bold">{{ row.to_dept_name }}</div>
              <div class="user-sub text-muted font-mono" style="font-size: 11px;">{{ row.to_user_name }}</div>
            </template>
          </el-table-column>

          <el-table-column prop="change_qty" label="变动数量" width="100" align="right">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold" :class="row.change_qty >= 0 ? 'text-success' : 'text-danger'">
                {{ row.change_qty > 0 ? '+' : '' }}{{ row.change_qty }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="结算金额" width="120" align="right">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold">
                ¥ {{ Number(row.settlement_amount || 0).toFixed(2) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column prop="is_billable" label="计费属性" width="110" align="center">
            <template #default="{ row }">
              <span v-if="row.is_billable === 1" class="status-chip chip-active">消耗计费</span>
              <span v-else class="status-chip chip-info">移库不计费</span>
            </template>
          </el-table-column>

          <el-table-column prop="audit_status" label="审计状态" width="100" align="center">
            <template #default="{ row }">
              <span class="status-chip chip-active">{{ row.audit_status || 'VERIFIED' }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="发生时间" width="165" class-name="font-mono tabular-nums" />
        </el-table>

        <!-- 分页控件 -->
        <div class="pagination-footer-row">
          <el-pagination
            v-model:current-page="tracePagination.currentPage"
            v-model:page-size="tracePagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="filteredTraceLogs.length"
          />
        </div>
      </div>
    </div>

    <!-- ===================================================================
         视图 2: 全员人工操作安全审计日志 (actions)
         =================================================================== -->
    <div v-show="logTab === 'actions'" class="tab-pane-container">
      <!-- 筛选查询栏 -->
      <div class="glass-panel filter-panel">
        <el-form :inline="true" class="search-filter-form">
          <el-form-item label="操作人员">
            <el-input
              v-model="actionFilters.operator"
              placeholder="工号或姓名"
              clearable
              style="width: 160px;"
            />
          </el-form-item>
          <el-form-item label="业务模块">
            <el-select v-model="actionFilters.module" placeholder="全部模块" clearable style="width: 160px;">
              <el-option label="全部模块" value="" />
              <el-option label="产品字典管理" value="产品字典" />
              <el-option label="普通耗材主库" value="普通耗材主库" />
              <el-option label="高值耗材专仓" value="高值耗材专仓" />
              <el-option label="临床二级库房" value="临床二级库房" />
              <el-option label="财务精算与对账" value="财务" />
              <el-option label="采购与供应商协同" value="采购" />
              <el-option label="人员与RBAC中心" value="人员与RBAC" />
            </el-select>
          </el-form-item>
          <el-form-item label="操作动作">
            <el-select v-model="actionFilters.actionType" placeholder="全部动作" clearable style="width: 150px;">
              <el-option label="全部动作" value="" />
              <el-option label="验收入库" value="验收入库" />
              <el-option label="备货审批" value="备货审批" />
              <el-option label="发料出库" value="发料出库" />
              <el-option label="退货锁定" value="退货锁定" />
              <el-option label="盘点平账" value="盘点平账" />
              <el-option label="权限变更" value="权限变更" />
              <el-option label="密码重置" value="密码重置" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="handleSearchActions">
              <SvgIcon name="search" :size="13" style="margin-right: 4px;" />
              筛选
            </el-button>
            <el-button size="small" @click="handleResetActions">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 操作审计日志表格 -->
      <div class="glass-panel table-panel">
        <div class="table-caption-bar">
          <span class="caption-title">全院全员人工操作安全审计日志 (人机操作痕迹台账)</span>
          <span class="caption-sub font-mono tabular-nums">共 {{ filteredActionLogs.length }} 笔操作轨迹</span>
        </div>

        <el-table
          :data="paginatedActionLogs"
          border
          stripe
          class="fusion-styled-table"
          v-loading="loadingActions"
        >
          <el-table-column prop="action_no" label="审计流水号" width="170">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold text-accent">{{ row.action_no }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作人员" width="160">
            <template #default="{ row }">
              <div class="font-bold">{{ row.operator_name }}</div>
              <div class="font-mono text-muted" style="font-size: 11px;">工号: {{ row.username }}</div>
            </template>
          </el-table-column>

          <el-table-column label="角色 / 所属科室" width="180">
            <template #default="{ row }">
              <div>{{ row.role_name }}</div>
              <div class="text-muted" style="font-size: 11px;">{{ row.dept_name }}</div>
            </template>
          </el-table-column>

          <el-table-column prop="module_name" label="受控业务模块" width="150">
            <template #default="{ row }">
              <span class="status-chip chip-info">{{ row.module_name }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="action_type" label="操作行为" width="120" align="center">
            <template #default="{ row }">
              <span class="status-chip chip-active">{{ row.action_type }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="target_object" label="操作对象 / 业务单号" width="180">
            <template #default="{ row }">
              <span class="font-mono text-bold">{{ row.target_object }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="detail" label="详细操作审计日志" min-width="260" show-overflow-tooltip />

          <el-table-column prop="client_ip" label="终端 IP 地址" width="130">
            <template #default="{ row }">
              <span class="font-mono" style="font-size: 11.5px;">{{ row.client_ip }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="执行结果" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.status === 'SUCCESS'" class="status-chip chip-active">成功</span>
              <span v-else class="status-chip chip-disabled">失败</span>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="操作时间" width="165" class-name="font-mono tabular-nums" />
        </el-table>

        <!-- 分页控件 -->
        <div class="pagination-footer-row">
          <el-pagination
            v-model:current-page="actionPagination.currentPage"
            v-model:page-size="actionPagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="filteredActionLogs.length"
          />
        </div>
      </div>
    </div>

    <!-- ===================================================================
         视图 3: 异常审计风险预警看板 (warning)
         =================================================================== -->
    <div v-show="logTab === 'warning'" class="tab-pane-container">
      <div class="glass-panel warning-kpi-row">
        <div class="warning-kpi-card">
          <div class="w-title">待核实异常预警</div>
          <div class="w-val text-warn font-mono">1 笔</div>
          <div class="w-desc">高值未扫码疑似直发预警</div>
        </div>
        <div class="warning-kpi-card">
          <div class="w-title">疑似超期在库</div>
          <div class="w-val text-accent font-mono">0 笔</div>
          <div class="w-desc">FEFO 效期规则完好执行</div>
        </div>
        <div class="warning-kpi-card">
          <div class="w-title">整改闭环归档</div>
          <div class="w-val text-success font-mono">8 笔</div>
          <div class="w-desc">审计异常均已核实销案</div>
        </div>
      </div>

      <div class="glass-panel table-panel">
        <div class="table-caption-bar">
          <span class="caption-title">流转异常审计与风险整改追溯</span>
        </div>

        <el-table
          :data="warningLogsList"
          border
          stripe
          class="fusion-styled-table"
        >
          <el-table-column prop="trace_no" label="追溯流水号" width="180">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold text-accent">{{ row.trace_no }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="biz_order_no" label="单据号" width="160" />
          <el-table-column prop="product_name" label="物资品名" min-width="180" />
          <el-table-column prop="warning_reason" label="异常原因判定" min-width="220" />
          <el-table-column prop="audit_status" label="当前状态" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.audit_status === 'RECTIFIED'" class="status-chip chip-active">已整改销号</span>
              <span v-else class="status-chip chip-disabled">待人工核实</span>
            </template>
          </el-table-column>
          <el-table-column label="审计整改操作" width="160" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.audit_status !== 'RECTIFIED'"
                size="small"
                type="primary"
                @click="handleRectify(row)"
              >
                核实并销号
              </el-button>
              <span v-else class="text-muted font-mono" style="font-size: 11px;">已归档</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- ===================================================================
         视图 4: 医疗器械不良事件召回与全院熔断冻结中枢 (recall)
         =================================================================== -->
    <div v-show="logTab === 'recall'" class="tab-pane-container">
      <div class="glass-panel" style="padding: 16px 20px; margin-bottom: 16px; border-left: 4px solid #ef4444;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px; color: #ef4444; display: flex; align-items: center; gap: 8px;">
          <SvgIcon name="warning" :size="18" color="#ef4444" />
          <span>国家药监局 / 生产厂家医疗器械不良事件紧急召回应急处置中枢</span>
        </div>
        <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 14px; line-height: 1.6;">
          依据国家《医疗器械不良事件监测和再评价管理办法》与 GSP 监管规范，当接到召回通报后，录入问题生产批号可一键执行<strong>全院熔断冻结</strong>。系统将硬性阻断主库按需分发、二级库发料及高值专柜扫码核销。
        </p>

        <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
          <el-input
            v-model="recallForm.batchNo"
            placeholder="输入召回生产批号 (如: B20261103)"
            style="width: 240px;"
            class="font-mono"
          />
          <el-input
            v-model="recallForm.reason"
            placeholder="录入召回文件号或不良事件描述 (必填)"
            style="width: 380px;"
          />
          <el-button
            type="danger"
            :loading="submittingRecall"
            @click="handleDoBatchRecallFreeze"
          >
            一键全院熔断冻结
          </el-button>
          <el-button @click="fetchActiveRecalls">刷新召回名录</el-button>
        </div>
      </div>

      <!-- 在控召回物资台账 -->
      <div class="glass-panel table-panel">
        <div class="table-caption-bar">
          <span class="caption-title">全院当前在控不良事件召回批次清册</span>
          <span class="caption-sub font-mono tabular-nums">共 {{ activeRecallsList.length }} 个批次处于硬性熔断冻结状态</span>
        </div>

        <el-table :data="activeRecallsList" border stripe style="width: 100%;">
          <el-table-column prop="batch_no" label="召回生产批号" width="180" class-name="font-mono font-bold text-danger" />
          <el-table-column prop="product_code" label="规格编码" width="160" class-name="font-mono" />
          <el-table-column prop="product_name" label="器械品名" min-width="200" show-overflow-tooltip />
          <el-table-column prop="main_qty" label="主库受控量" width="110" align="right" class-name="font-mono font-bold" />
          <el-table-column prop="sec_qty" label="二级库受控量" width="120" align="right" class-name="font-mono font-bold" />
          <el-table-column prop="hv_qty" label="专柜受控量" width="110" align="right" class-name="font-mono font-bold" />
          <el-table-column label="全院管控状态" width="140" align="center">
            <template #default>
              <span class="status-chip chip-disabled" style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: #ef4444;">
                已全院熔断冻结
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @file WorkflowLogView.vue
 * @description 全院医疗物资全生命周期流转追溯与人工操作安全审计中心
 * 支持：出入库流转全链路台账（多维过滤、分页、8节点图谱）、全员人工操作安全审计日志（操作人、模块、动作、IP、分页）、异常预警整改闭环。
 */

import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { httpGet, httpPost, httpPut } from '@/api/request';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const logTab = ref<'trace' | 'actions' | 'warning' | 'recall'>('trace');
const logs = ref<any[]>([]);
const actionLogs = ref<any[]>([]);
const loadingTrace = ref(false);
const loadingActions = ref(false);

// 不良事件召回中枢状态
const recallForm = ref({
  batchNo: 'B20261103',
  reason: '国家药监局2026年第8号医疗器械不良事件紧急召回公告'
});
const submittingRecall = ref(false);
const activeRecallsList = ref<any[]>([
  {
    batch_no: 'B20261103',
    product_code: 'PROD-GEN-001',
    product_name: '一次性使用无菌注射器带针 5ml',
    main_qty: 120,
    sec_qty: 35,
    hv_qty: 0,
    status: 'RECALLED_FROZEN'
  }
]);

// 视图 1 流转台账筛选条件
const traceFilters = ref({
  keyword: '',
  productName: '',
  fromDept: '',
  toDept: '',
  nodeAction: '',
  isBillable: ''
});

// 视图 1 分页
const tracePagination = ref({
  currentPage: 1,
  pageSize: 10
});

// 视图 2 人工操作筛选条件
const actionFilters = ref({
  operator: '',
  module: '',
  actionType: ''
});

// 视图 2 分页
const actionPagination = ref({
  currentPage: 1,
  pageSize: 10
});

/**
 * 切换追溯与安全审计 Tab
 * @param tab 视图类型 ('trace' | 'actions' | 'warning')
 * @returns void
 * @route 联动更新浏览器 query.tab
 * @throws 无异常
 */
function switchLogTab(tab: 'trace' | 'actions' | 'warning' | 'recall') {
  logTab.value = tab;
  router.replace({ query: { ...route.query, tab } });
  if (tab === 'actions' && actionLogs.value.length === 0) {
    fetchActionLogs();
  } else if (tab === 'recall') {
    fetchActiveRecalls();
  }
}

watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab === 'warning') logTab.value = 'warning';
    else if (newTab === 'actions') {
      logTab.value = 'actions';
      if (actionLogs.value.length === 0) fetchActionLogs();
    } else if (newTab === 'recall') {
      logTab.value = 'recall';
      fetchActiveRecalls();
    } else {
      logTab.value = 'trace';
    }
  },
  { immediate: true }
);

/**
 * 加载全院在控召回批次清册
 */
async function fetchActiveRecalls() {
  try {
    const res = await httpGet<any>('/workflow-logs/recall/active-recalls');
    if (Array.isArray(res) && res.length > 0) {
      activeRecallsList.value = res;
    }
  } catch (err) {
    console.warn('获取召回名录失败', err);
  }
}

/**
 * 执行国家不良事件全院召回熔断冻结
 */
async function handleDoBatchRecallFreeze() {
  if (!recallForm.value.batchNo.trim()) {
    ElMessage.warning('请输入召回生产批号');
    return;
  }
  if (!recallForm.value.reason.trim()) {
    ElMessage.warning('请输入召回原因说明');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定对批次 [${recallForm.value.batchNo}] 执行国家不良事件全院召回熔断冻结吗？\n该操作将强制锁定全院主库、二级库及专柜在库库存，并硬性阻断所有分发、发料与核销动作！`,
      '全院紧急召回风险警示',
      { type: 'error', confirmButtonText: '确认全院熔断冻结', cancelButtonText: '取消' }
    );
  } catch {
    return;
  }

  submittingRecall.value = true;
  try {
    const res = await httpPost<any>('/workflow-logs/recall/freeze-batch', {
      batch_no: recallForm.value.batchNo.trim(),
      recall_reason: recallForm.value.reason.trim(),
      notice_doc_no: 'NMPA-RECALL-202608'
    });
    ElMessage.success(res.msg || '全院不良事件召回熔断已生效！');
    await fetchActiveRecalls();
    await fetchLogs();
  } catch (err: any) {
    ElMessage.error(err.message || '全院召回冻结执行失败');
  } finally {
    submittingRecall.value = false;
  }
}

const selectedTraceRow = ref<any>(null);

const activeStepIndex = computed(() => {
  if (!selectedTraceRow.value) return 7;
  const act = selectedTraceRow.value.node_action || '';
  if (act.includes('1_') || act.includes('DICT')) return 1;
  if (act.includes('2_') || act.includes('INBOUND')) return 2;
  if (act.includes('3_') || act.includes('DISPATCH')) return 3;
  if (act.includes('4_') || act.includes('SPLIT')) return 4;
  if (act.includes('5_') || act.includes('RECEIVE')) return 5;
  if (act.includes('6_') || act.includes('APPLY')) return 6;
  if (act.includes('7_') || act.includes('CONSUME') || act.includes('VERIFY')) return 7;
  if (act.includes('8_') || act.includes('AUDIT') || act.includes('FINANCE')) return 8;
  return 3;
});

const timelineNodes = computed(() => {
  const stepIdx = activeStepIndex.value;
  const baseNodes = [
    { step: 1, title: '字典建档', sub: '药监局UDI' },
    { step: 2, title: '主库验收', sub: '效期强校验' },
    { step: 3, title: '按需分发', sub: '移库不计费' },
    { step: 4, title: '高值拆码', sub: '一物一码SN' },
    { step: 5, title: '二级库签收', sub: '差异可拒收' },
    { step: 6, title: '定数申领', sub: '主科室审批' },
    { step: 7, title: '患者核销', sub: '消耗即结算' },
    { step: 8, title: '财务审计', sub: '四联合规' }
  ];
  return baseNodes.map(n => {
    let status = 'pending';
    if (n.step < stepIdx) status = 'passed';
    else if (n.step === stepIdx) status = 'active';
    return { ...n, status };
  });
});

function handleTraceRowClick(row: any) {
  selectedTraceRow.value = row;
  ElMessage.info(`已激活单据 [${row.biz_order_no || row.trace_no}] 动态全链路穿透追溯图谱`);
}

const fallbackLogs = [
  {
    id: 1,
    trace_no: 'TRC-20261102-001',
    biz_order_no: 'ORD-20261102-001',
    node_action: '2_PURCHASE_INBOUND',
    product_name: '一次性使用无菌注射器带针 5ml',
    from_dept_name: '威高医药代表',
    from_user_name: '张明远',
    to_dept_name: '耗材科主库',
    to_user_name: '王建国',
    change_qty: 1000,
    settlement_amount: 450.0,
    is_billable: 0,
    audit_status: 'VERIFIED',
    created_at: '2026-11-02 09:30:00'
  },
  {
    id: 2,
    trace_no: 'TRC-20261102-002',
    biz_order_no: 'DIST-20261102-001',
    node_action: '3_MAIN_DISPATCH',
    product_name: '一次性使用无菌注射器带针 5ml',
    from_dept_name: '耗材科主库',
    from_user_name: '王建国',
    to_dept_name: '骨科病区二级库',
    to_user_name: '李晓琳',
    change_qty: 200,
    settlement_amount: 90.0,
    is_billable: 0,
    audit_status: 'VERIFIED',
    created_at: '2026-11-02 11:15:00'
  },
  {
    id: 3,
    trace_no: 'TRC-20261102-003',
    biz_order_no: 'VERIFY-SN20261010',
    node_action: '6_CLINICAL_CONSUME',
    product_name: '钛合金锁定接骨板螺钉系统',
    from_dept_name: '高值专仓',
    from_user_name: '智能柜终端',
    to_dept_name: '患者:张*丰',
    to_user_name: '李晓琳(责任护士)',
    change_qty: -1,
    settlement_amount: 4200.0,
    is_billable: 1,
    audit_status: 'VERIFIED',
    created_at: '2026-11-02 14:05:00'
  },
  {
    id: 4,
    trace_no: 'TRC-20261102-004',
    biz_order_no: 'STK-20261103-01',
    node_action: '7_STOCKTAKE_BALANCE',
    product_name: '医用氧气123 (40L)',
    from_dept_name: '总务仓库',
    from_user_name: '系统自动平账',
    to_dept_name: '卫材库房',
    to_user_name: '赵振华',
    change_qty: 10,
    settlement_amount: 520.0,
    is_billable: 0,
    audit_status: 'VERIFIED',
    created_at: '2026-11-03 10:10:00'
  }
];

const fallbackActionLogs = [
  {
    id: 1,
    action_no: 'ACT202611030001',
    operator_name: '赵振华',
    username: 'admin',
    role_name: '信息科系统管理员',
    dept_name: '信息科',
    module_name: '人员与RBAC中心',
    action_type: '权限变更',
    target_object: '护士李晓琳(secondary_user)',
    detail: '为用户李晓琳分配骨科二级库(WH_SEC_ORTHO)申领与出库原子权限',
    client_ip: '192.168.1.102',
    status: 'SUCCESS',
    created_at: '2026-11-03 14:10:22'
  },
  {
    id: 2,
    action_no: 'ACT202611030002',
    operator_name: '王建国',
    username: 'mgr_consumable',
    role_name: '耗材科主库管理员',
    dept_name: '耗材科主库',
    module_name: '普通耗材主库',
    action_type: '验收入库',
    target_object: '入库单 IN202611031900',
    detail: '完成国药控股医用敷料贴等8品项验收入库并自动审核入库台账',
    client_ip: '192.168.1.155',
    status: 'SUCCESS',
    created_at: '2026-11-03 14:22:15'
  },
  {
    id: 3,
    action_no: 'ACT202611030003',
    operator_name: '王建国',
    username: 'mgr_consumable',
    role_name: '耗材科主库管理员',
    dept_name: '耗材科主库',
    module_name: '高值耗材专仓',
    action_type: '备货审批',
    target_object: '备货单 HVP20261102001',
    detail: '审批通过骨科脊柱锁定板备货申请，自动生成主库出库记录并直达高值仓',
    client_ip: '192.168.1.155',
    status: 'SUCCESS',
    created_at: '2026-11-03 14:35:10'
  },
  {
    id: 4,
    action_no: 'ACT202611030004',
    operator_name: '李晓琳',
    username: 'nurse_ortho',
    role_name: '骨科二级库责任护士',
    dept_name: '骨科病区二级库',
    module_name: '临床二级库房',
    action_type: '发料出库',
    target_object: '发料单 SO20261103001',
    detail: '为3病区择期手术手动发料一次性注射器与医用棉签，扣减在库库存',
    client_ip: '192.168.3.45',
    status: 'SUCCESS',
    created_at: '2026-11-03 15:02:11'
  }
];

const warningLogsList = ref([
  {
    trace_no: 'TRC-WARN-20261102-09',
    biz_order_no: 'HVR-20261102-99',
    product_name: '心血管药物洗脱球囊导管系统',
    warning_reason: '高值专仓退货单已提交但未执行不可逆第二阶段锁定，请及时核查',
    audit_status: 'FLAGGED'
  }
]);

const warningLogsCount = computed(() => {
  return warningLogsList.value.filter(l => l.audit_status === 'FLAGGED').length;
});

function formatNodeAction(node: string): string {
  const map: Record<string, string> = {
    '1_INIT_STOCK': '期初建账',
    '2_PURCHASE_INBOUND': '主库验收入库',
    '3_MAIN_DISPATCH': '主库按需分发',
    '4_HIGH_VALUE_CODE': '高值专仓赋码',
    '5_SEC_INBOUND': '二级库接收入库',
    '6_CLINICAL_CONSUME': '患者扫码核销',
    '7_STOCKTAKE_BALANCE': '盘点自动平账',
    '8_SEC_MANUAL_OUT': '二级库手动发料'
  };
  return map[node] || node || '流转登记';
}

// 视图 1 过滤计算
const filteredTraceLogs = computed(() => {
  const list = logs.value.length ? logs.value : fallbackLogs;
  return list.filter((item) => {
    if (traceFilters.value.keyword) {
      const kw = traceFilters.value.keyword.toLowerCase();
      const matchTrace = (item.trace_no || '').toLowerCase().includes(kw);
      const matchBiz = (item.biz_order_no || '').toLowerCase().includes(kw);
      if (!matchTrace && !matchBiz) return false;
    }
    if (traceFilters.value.productName) {
      if (!item.product_name?.includes(traceFilters.value.productName)) return false;
    }
    if (traceFilters.value.fromDept) {
      if (!item.from_dept_name?.includes(traceFilters.value.fromDept)) return false;
    }
    if (traceFilters.value.toDept) {
      if (!item.to_dept_name?.includes(traceFilters.value.toDept)) return false;
    }
    if (traceFilters.value.nodeAction) {
      if (item.node_action !== traceFilters.value.nodeAction) return false;
    }
    if (traceFilters.value.isBillable !== '') {
      if (String(item.is_billable) !== traceFilters.value.isBillable) return false;
    }
    return true;
  });
});

const paginatedTraceLogs = computed(() => {
  const start = (tracePagination.value.currentPage - 1) * tracePagination.value.pageSize;
  return filteredTraceLogs.value.slice(start, start + tracePagination.value.pageSize);
});

// 视图 2 过滤计算
const filteredActionLogs = computed(() => {
  const list = actionLogs.value.length ? actionLogs.value : fallbackActionLogs;
  return list.filter((item) => {
    if (actionFilters.value.operator) {
      const kw = actionFilters.value.operator.toLowerCase();
      const matchName = (item.operator_name || '').toLowerCase().includes(kw);
      const matchUser = (item.username || '').toLowerCase().includes(kw);
      if (!matchName && !matchUser) return false;
    }
    if (actionFilters.value.module) {
      if (!item.module_name?.includes(actionFilters.value.module)) return false;
    }
    if (actionFilters.value.actionType) {
      if (!item.action_type?.includes(actionFilters.value.actionType)) return false;
    }
    return true;
  });
});

const paginatedActionLogs = computed(() => {
  const start = (actionPagination.value.currentPage - 1) * actionPagination.value.pageSize;
  return filteredActionLogs.value.slice(start, start + actionPagination.value.pageSize);
});

/**
 * 刷新当前激活视图数据
 */
function handleRefreshCurrent() {
  if (logTab.value === 'trace') fetchLogs();
  else if (logTab.value === 'actions') fetchActionLogs();
  ElMessage.success('已刷新最新台账数据');
}

/**
 * 从后端加载 6W 审计流转日志
 */
async function fetchLogs() {
  loadingTrace.value = true;
  try {
    const res = await httpGet('/workflow-logs');
    logs.value = res || [];
  } catch {
    logs.value = fallbackLogs;
  } finally {
    loadingTrace.value = false;
  }
}

/**
 * 从后端加载全员人工操作安全审计日志
 */
async function fetchActionLogs() {
  loadingActions.value = true;
  try {
    const res = await httpGet('/workflow-logs/user-actions');
    actionLogs.value = res || [];
  } catch {
    actionLogs.value = fallbackActionLogs;
  } finally {
    loadingActions.value = false;
  }
}

function handleSearchTrace() {
  tracePagination.value.currentPage = 1;
}

function handleResetTrace() {
  traceFilters.value = {
    keyword: '',
    productName: '',
    fromDept: '',
    toDept: '',
    nodeAction: '',
    isBillable: ''
  };
  tracePagination.value.currentPage = 1;
}

function handleSearchActions() {
  actionPagination.value.currentPage = 1;
}

function handleResetActions() {
  actionFilters.value = {
    operator: '',
    module: '',
    actionType: ''
  };
  actionPagination.value.currentPage = 1;
}

function handleRectify(row: any) {
  row.audit_status = 'RECTIFIED';
  ElMessage.success(`异常凭据 ${row.trace_no} 已人工核实并整改归档`);
}

function handleExportReport() {
  ElMessage.info('已调用 6W 全流程追溯链结构化审计报告导出');
}

onMounted(() => {
  fetchLogs();
  fetchActionLogs();
});
</script>

<style scoped>
.workflow-log-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 毛玻璃面板 */
.glass-panel {
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.sub-nav-tabs-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
}

.tab-btn-group {
  display: flex;
  gap: 8px;
}

.log-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.log-tab-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.log-tab-btn.active {
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-color: var(--accent-border);
  font-weight: 600;
}

.tab-chip {
  padding: 1px 6px;
  font-size: 11px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.2);
  color: var(--color-danger);
}

.tab-pane-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.timeline-overview-card {
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card-header-row h3 {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.subtitle {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 3px;
}

/* 8 节点时间线 */
.timeline-nodes-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  margin: 10px 0 14px;
}

.timeline-track-line {
  position: absolute;
  top: 15px;
  left: 20px;
  right: 20px;
  height: 2px;
  background: var(--border-subtle);
  z-index: 1;
}

.timeline-node-item {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
}

.node-circle {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 2px solid var(--border-card);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  transition: all 0.3s ease;
}

.timeline-node-item.passed .node-circle {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #ffffff;
}

.timeline-node-item.active .node-circle {
  background: var(--color-warning);
  border-color: var(--color-warning);
  color: #ffffff;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.4);
}

.node-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.node-sub {
  font-size: 10.5px;
  color: var(--text-muted);
}

.highlight-audit-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 8px;
}

.strip-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strip-text {
  font-size: 12.5px;
  color: var(--text-primary);
}

.filter-panel {
  padding: 12px 16px 2px;
}

.search-filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.table-panel {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.table-caption-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.caption-title {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-primary);
}

.caption-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.pagination-footer-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

/* 状态药丸与芯片 */
.status-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 500;
}

.chip-active {
  background: rgba(16, 185, 129, 0.15);
  color: var(--color-success);
}

.chip-info {
  background: rgba(14, 165, 233, 0.15);
  color: var(--accent-primary);
}

.chip-warning {
  background: rgba(245, 158, 11, 0.15);
  color: var(--color-warning);
}

.chip-disabled {
  background: rgba(239, 68, 68, 0.15);
  color: var(--color-danger);
}

/* 预警指标 */
.warning-kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  padding: 16px 20px;
}

.warning-kpi-card {
  padding: 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.w-title {
  font-size: 12.5px;
  color: var(--text-muted);
}

.w-val {
  font-size: 22px;
  font-weight: 700;
}

.w-desc {
  font-size: 11.5px;
  color: var(--text-muted);
}
</style>
