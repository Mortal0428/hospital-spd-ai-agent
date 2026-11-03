<template>
  <div class="secondary-warehouse-view">
    <!-- 顶部 4 宫格高质感毛玻璃 KPI 指标大盘 -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>临床二级库在库品规数</span>
          <SvgIcon name="room" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          128 <span class="kpi-unit">种品规</span>
        </div>
        <div class="kpi-sub">
          <SvgIcon name="check" :size="13" color="var(--color-success)" />
          <span>{{ currentWarehouseName }} 实物储备与独立财产建账就绪</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>待主库审批申领单</span>
          <SvgIcon name="clock" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-warn">
          {{ pendingRequisitionCount }} <span class="kpi-unit">笔审核中</span>
        </div>
        <div class="kpi-sub text-warn">
          <SvgIcon name="info" :size="13" color="var(--color-warning)" />
          <span>主库未审核前护士可自主撤回与删除</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>本日手动发料出库额</span>
          <SvgIcon name="package" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-accent">
          ¥ {{ todayManualOutAmount.toFixed(2) }}
        </div>
        <div class="kpi-sub">
          <SvgIcon name="arrow-right" :size="13" color="var(--accent-primary)" />
          <span>替代前端 HIS 手动发料核减库存</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>本科室物资资产累计总额</span>
          <SvgIcon name="stats" :size="16" color="var(--color-success)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-success">
          ¥ 158,240.00
        </div>
        <div class="kpi-sub text-success">
          <SvgIcon name="scale" :size="13" color="var(--color-success)" />
          <span>主库转入计入二级库资产 · 发料核算科室成本</span>
        </div>
      </div>
    </div>

    <!-- 病区切换与经办科室选择栏 -->
    <div class="glass-panel dept-switcher-bar">
      <div class="dept-pills-wrap">
        <span class="dept-label">当前经办临床二级库：</span>
        <button
          class="dept-pill"
          :class="{ active: currentDeptCode === 'WH_SEC_ORTHO' }"
          @click="switchDept('WH_SEC_ORTHO')"
        >
          <SvgIcon name="room" :size="14" />
          <span>骨科病区二级库 (WH_SEC_ORTHO)</span>
        </button>
        <button
          class="dept-pill"
          :class="{ active: currentDeptCode === 'WH_SEC_CARDIO' }"
          @click="switchDept('WH_SEC_CARDIO')"
        >
          <SvgIcon name="pulse" :size="14" />
          <span>心内科病区二级库 (WH_SEC_CARDIO)</span>
        </button>
      </div>

      <div class="dept-action-btns">
        <button class="spd-btn btn-primary" @click="openCreateRequisitionModal">
          <SvgIcon name="plus" :size="13" />
          <span>+ 填报物资申请单</span>
        </button>
        <button class="spd-btn btn-warn" @click="openManualOutboundModal">
          <SvgIcon name="package" :size="13" />
          <span>开具科室发料单 (核销库存)</span>
        </button>
      </div>
    </div>

    <!-- 主体毛玻璃 Tab 工作台 -->
    <div class="glass-panel tab-container-panel">
      <el-tabs v-model="activeTab" class="fusion-tabs" @tab-change="handleTabChange">
        <!-- =====================================================================
             Tab 1: 临床科室物资申领 (对标图 4 申请单)
             ===================================================================== -->
        <el-tab-pane label="科室物资申请与记录" name="requisition">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>临床科室物资申请台账 · 支持多耗材批量申请 · 待主库审批前可自主撤回与删除 · 双击查看明细</span>
              </div>
              <div class="action-btn-group">
                <el-button type="primary" size="small" @click="openCreateRequisitionModal">
                  <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                  新建申请单
                </el-button>
                <el-button
                  type="warning"
                  plain
                  size="small"
                  :disabled="!selectedRequisition || selectedRequisition.req_status !== 'PENDING_APPROVAL'"
                  @click="handleWithdrawSelected"
                >
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  自主撤回
                </el-button>
                <el-button
                  type="danger"
                  plain
                  size="small"
                  :disabled="!selectedRequisition || selectedRequisition.req_status !== 'PENDING_APPROVAL'"
                  @click="handleDeleteSelected"
                >
                  <SvgIcon name="close" :size="13" style="margin-right: 4px;" />
                  删除申请
                </el-button>
                <el-button plain size="small" @click="fetchRequisitions">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新记录
                </el-button>
              </div>
            </div>

            <!-- 申领记录表格 -->
            <el-table
              :data="paginatedRequisitions"
              border
              stripe
              highlight-current-row
              class="fusion-styled-table spd-clickable-table"
              :row-class-name="requisitionRowClassName"
              v-loading="loadingReq"
              @current-change="handleRequisitionRowClick"
              @row-dblclick="handleRequisitionRowDblClick"
            >
              <el-table-column type="index" label="序号" width="55" align="center" />

              <el-table-column prop="req_order_no" label="申请单号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.req_order_no }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="created_at" label="申请时间" width="160">
                <template #default="{ row }">
                  <span class="font-mono text-muted" style="font-size: 11.5px;">{{ row.created_at }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="target_main_warehouse_code" label="出库主库" width="150">
                <template #default="{ row }">
                  <span class="font-mono">{{ row.target_main_warehouse_code || '卫材库房 (WH_WEICAI)' }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="product_name" label="申请内容" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="font-bold">{{ row.product_name }}</span>
                  <span v-if="row.spec_name" class="font-mono text-muted" style="font-size: 11px;"> ({{ row.spec_name }})</span>
                </template>
              </el-table-column>

              <el-table-column prop="apply_qty" label="申请数量" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold">{{ row.apply_qty }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="total_amount" label="申请金额" width="120" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold">¥ {{ (row.total_amount || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="applicant_name" label="申请人" width="100" align="center" />

              <el-table-column prop="apply_reason" label="申请备注" min-width="150" show-overflow-tooltip />

              <el-table-column prop="req_status" label="审核状态" width="130" align="center" fixed="right">
                <template #default="{ row }">
                  <span v-if="row.req_status === 'APPROVED_DISPATCHED'" class="status-chip chip-active">主库已出库</span>
                  <span v-else-if="row.req_status === 'REJECTED'" class="status-chip chip-disabled">已退回</span>
                  <span v-else-if="row.req_status === 'WITHDRAWN'" class="status-chip chip-locked">已撤回</span>
                  <span v-else class="status-chip chip-warning">待主库审批</span>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="160" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 4px; justify-content: center;">
                    <button
                      v-if="row.req_status === 'PENDING_APPROVAL'"
                      class="mini-op-btn btn-warn"
                      title="撤回申请"
                      @click="handleWithdrawReq(row)"
                    >
                      撤回
                    </button>
                    <button
                      v-if="row.req_status === 'PENDING_APPROVAL'"
                      class="mini-op-btn btn-danger"
                      title="删除申请"
                      @click="handleDeleteReq(row)"
                    >
                      删除
                    </button>
                    <button
                      class="mini-op-btn"
                      title="查看申请单明细"
                      @click="openRequisitionDetail(row)"
                    >
                      查看明细
                    </button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 申领记录分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="reqPage"
                v-model:page-size="reqPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="requisitions.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 2: 二级库接收入库 (确认主库分发调拨)
             ===================================================================== -->
        <el-tab-pane label="二级库接收入库" name="receive">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="package" :size="15" color="var(--accent-primary)" />
                <span>主库按需分发待临床二级库签收入库台账 · 移库不计费 · 确认签收即计入科室在库资产，若有破损支持差异拒收逆向退库</span>
              </div>
              <div class="action-btn-group">
                <el-button plain size="small" @click="fetchPendingReceives">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新待入库分发单
                </el-button>
              </div>
            </div>

            <el-table
              :data="paginatedReceives"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingReceives"
            >
              <el-table-column type="index" label="序号" width="55" align="center" />
              <el-table-column prop="dist_order_no" label="分发调拨单号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.dist_order_no }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="source_main_dept" label="出库主库" width="140">
                <template #default="{ row }">
                  <span>{{ row.source_main_dept === 'EQUIP_DEPT' ? '设备科主库' : '耗材科主库' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="target_dept_name" label="接收科室" width="150" />
              <el-table-column prop="product_name" label="耗材品名" min-width="190" />
              <el-table-column prop="batch_no" label="生产批号" width="130" class-name="font-mono" />
              <el-table-column prop="expiry_date" label="有效期至" width="120" class-name="font-mono" />
              <el-table-column prop="dist_qty" label="分发数量" width="100" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold">{{ row.dist_qty }}</span>
                </template>
              </el-table-column>
              <el-table-column label="单价" width="100" align="right">
                <template #default="{ row }">
                  <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="dispatcher_name" label="主库发料人" width="110" align="center" />
              <el-table-column prop="created_at" label="分发时间" width="165" class-name="font-mono tabular-nums" />
              <el-table-column label="入库签收操作" width="180" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 6px; justify-content: center;">
                    <el-button
                      size="small"
                      type="success"
                      @click="handleAcceptReceive(row)"
                    >
                      确认接收入库
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      plain
                      @click="handleRejectReceive(row)"
                    >
                      差异拒收
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 待接收入库分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="receivePage"
                v-model:page-size="receivePageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="pendingReceives.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 3: 科室在库台账 (stock)
             ===================================================================== -->
        <el-tab-pane label="科室在库台账" name="stock">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="room" :size="15" color="var(--accent-primary)" />
                <span>{{ currentWarehouseName }} 实物在库实时批次台账 · 现存数量 · 累计消耗量 · 安全基准水位监控</span>
              </div>
              <div class="action-btn-group">
                <el-button plain size="small" @click="fetchSecondaryInventory">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新在库台账
                </el-button>
              </div>
            </div>

            <el-table
              :data="paginatedInventory"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingInventory"
            >
              <el-table-column type="index" label="序号" width="55" align="center" />
              <el-table-column prop="product_code" label="物料代码" width="165">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.product_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="耗材品名" min-width="190" />
              <el-table-column prop="batch_no" label="生产批号" width="130" class-name="font-mono" />
              <el-table-column prop="expiry_date" label="有效期至" width="120" class-name="font-mono" />
              <el-table-column prop="current_qty" label="在库实数" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold" :class="row.current_qty <= row.dept_safe_min ? 'text-danger' : 'text-success'">
                    {{ row.current_qty }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="consumed_qty" label="累计消耗" width="100" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums text-muted">{{ row.consumed_qty || 0 }}</span>
                </template>
              </el-table-column>
              <el-table-column label="单价" width="100" align="right">
                <template #default="{ row }">
                  <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="sec_shelf_code" label="货位代码" width="160" show-overflow-tooltip />
              <el-table-column label="库存预警" width="130" align="center">
                <template #default="{ row }">
                  <span v-if="row.current_qty <= (row.dept_safe_min || 10)" class="status-chip chip-disabled">
                    低于安全水位
                  </span>
                  <span v-else class="status-chip chip-active">库存充盈正常</span>
                </template>
              </el-table-column>
            </el-table>

            <!-- 科室在库台账分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="invPage"
                v-model:page-size="invPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="secondaryInventoryList.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 4: 二级库手动发料出库 (消除在库库存，替代 HIS)
             ===================================================================== -->
        <el-tab-pane label="科室手动发料出库 (核减库存)" name="manual-out">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="safe" :size="15" color="var(--accent-primary)" />
                <span>病区二级库发料台账 · 系统当前未对接前端 HIS，护士通过手动发料出库消除库存并结转科室消耗成本</span>
              </div>
              <div class="action-btn-group">
                <el-button type="primary" size="small" @click="openManualOutboundModal">
                  <SvgIcon name="package" :size="13" style="margin-right: 4px;" />
                  开具发料出库单
                </el-button>
                <el-button plain size="small" @click="fetchManualOutbounds">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新发料台账
                </el-button>
              </div>
            </div>

            <!-- 手动发料台账列表 -->
            <el-table
              :data="paginatedManualOutbounds"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingManualOut"
            >
              <el-table-column type="index" label="序号" width="55" align="center" />

              <el-table-column prop="order_no" label="发料出库单号" width="185">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="created_at" label="发料时间" width="160">
                <template #default="{ row }">
                  <span class="font-mono text-muted" style="font-size: 11.5px;">{{ row.created_at }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="product_name" label="出库耗材品名" min-width="190" show-overflow-tooltip />

              <el-table-column prop="batch_no" label="出库批次" width="130" class-name="font-mono" />

              <el-table-column prop="quantity" label="发料数量" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-danger">-{{ row.quantity }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="target_dept_or_supplier" label="领用人 / 领用科室" width="160" />

              <el-table-column prop="created_by" label="经办护士" width="100" align="center" />

              <el-table-column prop="remark" label="用途说明" min-width="160" show-overflow-tooltip />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 3: 二级库独立盘点与对账 (对标图 2 两级盘点工作台)
             ===================================================================== -->
        <el-tab-pane label="病区独立盘点" name="stocktake">
          <div class="tab-content-area" style="padding-top: 4px;">
            <StocktakePlanWorkbench
              scope="SECONDARY"
              :default-warehouse-code="currentDeptCode"
            />
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 4: 库存调拨与安全水位监控
             ===================================================================== -->
        <el-tab-pane label="库存调拨与安全水位" name="transfer">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="warning" :size="15" color="var(--color-warning)" />
                <span>各临床病区二级库之间应急调剂与常备耗材安全库存预警</span>
              </div>
              <div class="action-btn-group">
                <el-button type="primary" size="small" @click="transferModalVisible = true">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  发起跨病区应急调拨
                </el-button>
              </div>
            </div>

            <el-table :data="safetyStockList" border stripe class="fusion-styled-table">
              <el-table-column prop="product_code" label="耗材编码" width="140" class-name="font-mono text-accent" />
              <el-table-column prop="product_name" label="物资品名" min-width="190" />
              <el-table-column prop="safe_qty" label="安全基准水位" width="130" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums">{{ row.safe_qty }} {{ row.unit }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="current_qty" label="当前在库实数" width="130" align="right">
                <template #default="{ row }">
                  <span
                    class="font-mono tabular-nums font-bold"
                    :class="row.current_qty < row.safe_qty ? 'text-danger' : 'text-success'"
                  >
                    {{ row.current_qty }} {{ row.unit }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="库存预警状态" width="150" align="center">
                <template #default="{ row }">
                  <span v-if="row.current_qty < row.safe_qty" class="status-chip chip-disabled">
                    低于安全水位 (缺货)
                  </span>
                  <span v-else class="status-chip chip-active">库存充盈正常</span>
                </template>
              </el-table-column>
            </el-table>

            <!-- 手动发料台账分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="manualOutPage"
                v-model:page-size="manualOutPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="manualOutbounds.length"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- =========================================================================
         弹窗 1：对标图 4 《申请单》 填报模态框 (支持多行物资从字典选品)
         ========================================================================= -->
    <el-dialog
      v-model="showCreateReqModal"
      title="科室物资申请单"
      width="1000px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="hospital-bill-container">
        <!-- 自动防丢草稿箱提示栏 -->
        <div v-if="hasReqDraft" class="draft-tip-banner" style="display:flex; justify-content:space-between; align-items:center; background: rgba(56, 189, 248, 0.1); border: 1px dashed #38bdf8; border-radius: 6px; padding: 6px 12px; margin-bottom: 12px; font-size: 13px;">
          <span>检测到未提交的科室申领单草稿 (自动暂存时间: {{ reqDraftTime }})</span>
          <div style="display:flex; gap: 8px;">
            <el-button size="small" type="primary" link @click="restoreReqDraft">一键恢复草稿</el-button>
            <el-button size="small" type="danger" link @click="clearReqDraft">丢弃</el-button>
          </div>
        </div>

        <!-- 头部印章与标题 -->
        <div class="bill-header-row">
          <div class="bill-title-center">申 请 单</div>
          <div class="bill-stamp stamp-pending">未审核</div>
        </div>

        <!-- 单头元数据网格 (对标图 4) -->
        <div class="bill-meta-grid">
          <div class="meta-item">
            <span class="meta-label">申请单号:</span>
            <span class="meta-val font-mono font-bold">{{ newReqOrderNo }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请时间:</span>
            <span class="meta-val font-mono">{{ newReqDate }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请人:</span>
            <span class="meta-val font-bold">{{ userStore.currentUser.realName }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请部门:</span>
            <span class="meta-val">{{ currentDeptName }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请仓库:</span>
            <span class="meta-val font-mono">{{ currentDeptCode }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">出库仓库:</span>
            <select v-model="createReqTargetMainWh" class="spd-select font-mono">
              <option value="WH_WEICAI">卫材库房 (WH_WEICAI)</option>
              <option value="WH_EQUIP">设备库房 (WH_EQUIP)</option>
              <option value="WH_ZONGWU">总务仓库 (WH_ZONGWU)</option>
            </select>
          </div>
          <div class="meta-item" style="grid-column: span 3;">
            <span class="meta-label">申请备注:</span>
            <input v-model="createReqReason" placeholder="如: 骨科病房换药周常定额补货申领" class="spd-input" style="flex: 1;" />
          </div>
        </div>

        <!-- 单身操作条 -->
        <div class="bill-body-toolbar">
          <div class="title">申领物资清单 (共 {{ createReqItems.length }} 行)</div>
          <div class="btns">
            <button class="spd-btn btn-primary btn-sm" @click="openDictSpecPicker">
              <SvgIcon name="dict" :size="13" />
              <span>+ 从产品字典选品</span>
            </button>
            <button class="spd-btn btn-sm" @click="addEmptyReqRow">
              <SvgIcon name="plus" :size="13" />
              <span>新增空行</span>
            </button>
            <button class="spd-btn btn-danger btn-sm" :disabled="selectedReqRowIndex === -1" @click="removeSelectedReqRow">
              <SvgIcon name="close" :size="13" />
              <span>删除行</span>
            </button>
          </div>
        </div>

        <!-- 单身物资表格 (1:1 对标图 4) -->
        <div class="table-scroll-wrap">
          <table class="bill-detail-table edit-table">
            <thead>
              <tr>
                <th width="45" align="center">行号</th>
                <th width="150">代码</th>
                <th width="160">品名</th>
                <th width="120">规格</th>
                <th width="100">型号</th>
                <th width="70" align="center">计量单位</th>
                <th width="160">生产厂家</th>
                <th width="90" align="right">数量</th>
                <th width="90" align="right">单价</th>
                <th width="100" align="right">金额</th>
                <th>备注</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in createReqItems"
                :key="idx"
                :class="{ 'row-active': selectedReqRowIndex === idx }"
                @click="selectedReqRowIndex = idx"
              >
                <td align="center">{{ idx + 1 }}</td>
                <td>
                  <input v-model="item.spec_code" placeholder="输入或选品" class="table-inline-input font-mono" />
                </td>
                <td>
                  <input v-model="item.product_name" placeholder="耗材品名" class="table-inline-input font-bold" />
                </td>
                <td>
                  <input v-model="item.spec_name" placeholder="规格" class="table-inline-input" />
                </td>
                <td>
                  <input v-model="item.model_name" placeholder="型号" class="table-inline-input" />
                </td>
                <td align="center">
                  <input v-model="item.unit_name" style="text-align: center;" class="table-inline-input" />
                </td>
                <td>
                  <input v-model="item.manufacturer" placeholder="生产厂家" class="table-inline-input" />
                </td>
                <td align="right">
                  <input
                    v-model.number="item.apply_qty"
                    type="number"
                    min="1"
                    class="table-inline-input font-mono font-bold"
                    style="text-align: right;"
                    @input="recalcReqRow(item)"
                  />
                </td>
                <td align="right">
                  <input
                    v-model.number="item.unit_price"
                    type="number"
                    step="0.01"
                    min="0"
                    class="table-inline-input font-mono"
                    style="text-align: right;"
                    @input="recalcReqRow(item)"
                  />
                </td>
                <td align="right" class="font-mono font-bold">
                  ¥ {{ ((item.apply_qty || 0) * (item.unit_price || 0)).toFixed(2) }}
                </td>
                <td>
                  <input v-model="item.remark" placeholder="备注" class="table-inline-input" />
                </td>
              </tr>
              <tr class="bill-total-row">
                <td colspan="7" align="center" class="font-bold">合 计</td>
                <td align="right" class="font-mono font-bold">{{ reqTotalQty }}</td>
                <td />
                <td align="right" class="font-mono font-bold">¥ {{ reqTotalAmount.toFixed(2) }}</td>
                <td />
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="showCreateReqModal = false">取消</el-button>
          <el-button type="primary" :loading="submittingReq" @click="handleSaveRequisitionBatch">
            提交申请单 (向主库提报)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 2：图 4 详情穿透查看弹窗
         ========================================================================= -->
    <el-dialog
      v-model="showReqDetailModal"
      title="申请单明细"
      width="900px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div v-if="activeReqDetail" class="hospital-bill-container">
        <div class="bill-header-row">
          <div class="bill-title-center">申 请 单</div>
          <div class="bill-stamp" :class="activeReqDetail.req_status === 'APPROVED_DISPATCHED' ? 'stamp-approved' : 'stamp-pending'">
            {{ activeReqDetail.req_status === 'APPROVED_DISPATCHED' ? '已审核' : '未审核' }}
          </div>
        </div>

        <div class="bill-meta-grid">
          <div class="meta-item">
            <span class="meta-label">申请单号:</span>
            <span class="meta-val font-mono font-bold">{{ activeReqDetail.req_order_no }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请时间:</span>
            <span class="meta-val font-mono">{{ activeReqDetail.created_at }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请人:</span>
            <span class="meta-val font-bold">{{ activeReqDetail.applicant_name }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请部门:</span>
            <span class="meta-val">{{ activeReqDetail.apply_dept_name }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请仓库:</span>
            <span class="meta-val font-mono">{{ activeReqDetail.apply_warehouse_code }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">出库仓库:</span>
            <span class="meta-val font-mono">{{ activeReqDetail.target_main_warehouse_code || '卫材库房 (WH_WEICAI)' }}</span>
          </div>
        </div>

        <table class="bill-detail-table">
          <thead>
            <tr>
              <th width="45" align="center">行号</th>
              <th width="150">代码</th>
              <th>品名</th>
              <th>规格</th>
              <th>型号</th>
              <th width="70" align="center">计量单位</th>
              <th>生产厂家</th>
              <th width="90" align="right">数量</th>
              <th width="90" align="right">单价</th>
              <th width="100" align="right">金额</th>
              <th>备注</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td align="center">1</td>
              <td class="font-mono text-accent">{{ activeReqDetail.spec_code || '936010900135' }}</td>
              <td class="font-bold">{{ activeReqDetail.product_name }}</td>
              <td>{{ activeReqDetail.spec_name || '10cm*11.5cm' }}</td>
              <td>{{ activeReqDetail.model_name || '9546HP' }}</td>
              <td align="center">{{ activeReqDetail.unit_name || '片' }}</td>
              <td>{{ activeReqDetail.manufacturer || '广州明州康普医疗产品有限公司' }}</td>
              <td align="right" class="font-mono font-bold">{{ activeReqDetail.apply_qty }}</td>
              <td align="right" class="font-mono">¥ {{ (activeReqDetail.unit_price || 8.76).toFixed(2) }}</td>
              <td align="right" class="font-mono font-bold">¥ {{ (activeReqDetail.total_amount || activeReqDetail.apply_qty * 8.76).toFixed(2) }}</td>
              <td>{{ activeReqDetail.apply_reason || '' }}</td>
            </tr>
            <tr class="bill-total-row">
              <td colspan="7" align="center" class="font-bold">合 计</td>
              <td align="right" class="font-mono font-bold">{{ activeReqDetail.apply_qty }}</td>
              <td />
              <td align="right" class="font-mono font-bold">¥ {{ (activeReqDetail.total_amount || activeReqDetail.apply_qty * 8.76).toFixed(2) }}</td>
              <td />
            </tr>
          </tbody>
        </table>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="showReqDetailModal = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 3：科室手动发料出库凭证式单据 (对标图 1 / 图 5 规范)
         ========================================================================= -->
    <el-dialog
      v-model="showManualOutModal"
      title="开具科室发料出库单 (核减在库库存)"
      width="920px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal voucher-dialog"
    >
      <div class="hospital-bill-container">
        <div class="dialog-warning-banner" style="background: rgba(2, 132, 199, 0.1); border-left: 4px solid var(--accent-primary); padding: 8px 12px; border-radius: 4px; font-size: 12px; margin-bottom: 12px;">
          业务提醒：因当前系统未直连 HIS 前端，科室通过本出库单据批量核减库存实物，直接结转为本科室当期耗材支出并留存 6W 流水日志！
        </div>

        <div class="voucher-header-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">发料出库单号</label>
            <input v-model="manualOutVoucherNo" readonly class="spd-input font-mono readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">发料所属病区/仓库</label>
            <input :value="currentDeptName" readonly class="spd-input font-bold readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">出库类别</label>
            <input value="科室发料出库 (病房定数消耗)" readonly class="spd-input readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label required font-bold" style="font-size: 11px;">领用责任人 / 医生</label>
            <input v-model="manualOutForm.receiver_name" placeholder="例如: 张主治医生 / 李护士长" class="spd-input" />
          </div>
          <div class="form-group">
            <label class="form-label required font-bold" style="font-size: 11px;">领用用途说明</label>
            <input v-model="manualOutForm.use_purpose" placeholder="例如: 病房换药日常消耗核减" class="spd-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">经办护士</label>
            <input :value="userStore.currentUser.realName" readonly class="spd-input readonly-input" />
          </div>
        </div>

        <!-- 凭证明细表格 -->
        <div class="voucher-items-section">
          <div class="table-action-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="font-bold" style="font-size: 13px;">发料耗材明细清单 (共 {{ manualOutItems.length }} 行)</span>
            <el-button type="primary" size="small" @click="showSecSelectModalForOut = true">
              <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
              + 从本科室在库台账选品
            </el-button>
          </div>

          <el-table :data="manualOutItems" border stripe size="small" class="fusion-styled-table">
            <el-table-column type="index" label="序号" width="50" align="center" />
            <el-table-column prop="product_code" label="物料代码" width="140" class-name="font-mono" />
            <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
            <el-table-column prop="spec_model" label="规格型号" width="120" show-overflow-tooltip />
            <el-table-column prop="batch_no" label="批次号" width="110" class-name="font-mono" />
            <el-table-column prop="current_qty" label="在库可用" width="90" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold text-success">{{ row.current_qty || row.available_qty || 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="发料数量" width="120" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.out_qty"
                  :min="1"
                  :max="row.current_qty || row.available_qty || 999"
                  size="small"
                  style="width: 100px;"
                />
              </template>
            </el-table-column>
            <el-table-column label="单价" width="85" align="right">
              <template #default="{ row }">
                <span class="font-mono">¥{{ Number(row.unit_price || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="95" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold">¥{{ ((row.out_qty || 1) * Number(row.unit_price || 0)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="65" align="center">
              <template #default="{ $index }">
                <el-button type="danger" text size="small" @click="manualOutItems.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="voucher-total-bar" style="display: flex; justify-content: flex-end; gap: 24px; padding: 10px 14px; background: var(--spd-bg-subtle); border-radius: 4px; margin-top: 8px; font-size: 13px;">
            <span>合计件数: <strong class="font-mono text-primary">{{ manualOutTotalQty }}</strong> 件</span>
            <span>合计金额: <strong class="font-mono text-danger">¥ {{ manualOutTotalAmount.toFixed(2) }}</strong></span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="showManualOutModal = false">取消</el-button>
          <el-button type="primary" :loading="submittingManualOut" :disabled="manualOutItems.length === 0" @click="handleSaveManualOutboundVoucher">
            确认发料并扣减库存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         选品模态框
         ========================================================================= -->
    <el-dialog
      v-model="showDictSpecModal"
      title="从产品字典选品加入申请单"
      width="850px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="spec-select-container">
        <div class="spec-search-bar" style="margin-bottom: 12px;">
          <input
            v-model="dictSearchKeyword"
            placeholder="搜索物料编码、品名或拼音码..."
            class="spd-input font-mono"
            style="width: 100%;"
          />
        </div>
        <el-table
          :data="filteredDictSpecs"
          border
          stripe
          height="380"
          @selection-change="handleDictSpecSelection"
        >
          <el-table-column type="selection" width="46" align="center" />
          <el-table-column prop="spec_code" label="物料代码" width="165" class-name="font-mono text-accent" />
          <el-table-column prop="product_name" label="品名" min-width="150" />
          <el-table-column prop="spec_name" label="规格" width="120" />
          <el-table-column prop="pricing_unit" label="单位" width="65" align="center" />
          <el-table-column prop="unit_price" label="基准单价" width="100" align="right">
            <template #default="{ row }">
              <span class="font-mono">¥ {{ Number(row.unit_price).toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="showDictSpecModal = false">取消</el-button>
          <el-button type="primary" :disabled="selectedDictSpecs.length === 0" @click="confirmSelectDictSpecs">
            导入选中耗材 ({{ selectedDictSpecs.length }})
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 盘点漏账增补模态框 (全面采用图 3 / 图 5 表格多选规范，彻底替代原生下拉框) -->
    <SelectProductDictDialog
      v-model="showDictSelectDialog"
      @confirm="handleDictSelected"
    />

    <!-- =========================================================================
         弹窗 4：跨病区科室调拨凭证式单据 (对标图 1 / 图 5 规范)
         ========================================================================= -->
    <el-dialog
      v-model="transferModalVisible"
      title="开具跨病区科室调拨出库单 (双方库房留存双向台账)"
      width="920px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal voucher-dialog"
    >
      <div class="hospital-bill-container">
        <div class="dialog-warning-banner" style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid var(--spd-success); padding: 8px 12px; border-radius: 4px; font-size: 12px; margin-bottom: 12px;">
          业务规则：调拨出库将直接核减调出病区在库库存，并在调入病区生成待接收记录，双方病区调拨单号同步双向留痕追溯！
        </div>

        <div class="voucher-header-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">调拨单号</label>
            <input v-model="transferVoucherNo" readonly class="spd-input font-mono readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">调出病区 (本仓)</label>
            <input :value="currentDeptName" readonly class="spd-input font-bold readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label required font-bold" style="font-size: 11px;">调入目标病区</label>
            <select v-model="transferForm.to_warehouse_code" class="spd-select font-bold">
              <option value="WH_SEC_CARDIO">心内科病区二级库 (WH_SEC_CARDIO)</option>
              <option value="WH_SEC_ORTHO">骨科病区二级库 (WH_SEC_ORTHO)</option>
            </select>
          </div>
          <div class="form-group" style="grid-column: span 2;">
            <label class="form-label required font-bold" style="font-size: 11px;">调拨事由 / 临床急用说明</label>
            <input v-model="transferForm.reason_note" placeholder="例如: 抢救急用跨病区应急调剂无菌敷料" class="spd-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">经办护士</label>
            <input :value="userStore.currentUser.realName" readonly class="spd-input readonly-input" />
          </div>
        </div>

        <!-- 调拨明细表格 -->
        <div class="voucher-items-section">
          <div class="table-action-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="font-bold" style="font-size: 13px;">调拨物资明细清单 (共 {{ transferItems.length }} 行)</span>
            <el-button type="success" size="small" @click="showSecSelectModalForTransfer = true">
              <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
              + 从本科室在库台账选品
            </el-button>
          </div>

          <el-table :data="transferItems" border stripe size="small" class="fusion-styled-table">
            <el-table-column type="index" label="序号" width="50" align="center" />
            <el-table-column prop="product_code" label="物料代码" width="140" class-name="font-mono" />
            <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
            <el-table-column prop="spec_model" label="规格型号" width="120" show-overflow-tooltip />
            <el-table-column prop="batch_no" label="批次号" width="110" class-name="font-mono" />
            <el-table-column prop="current_qty" label="当前库存" width="90" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold text-success">{{ row.current_qty || row.available_qty || 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="调拨数量" width="120" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.transfer_qty"
                  :min="1"
                  :max="row.current_qty || row.available_qty || 999"
                  size="small"
                  style="width: 100px;"
                />
              </template>
            </el-table-column>
            <el-table-column label="单价" width="85" align="right">
              <template #default="{ row }">
                <span class="font-mono">¥{{ Number(row.unit_price || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="95" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold">¥{{ ((row.transfer_qty || 1) * Number(row.unit_price || 0)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="65" align="center">
              <template #default="{ $index }">
                <el-button type="danger" text size="small" @click="transferItems.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="voucher-total-bar" style="display: flex; justify-content: flex-end; gap: 24px; padding: 10px 14px; background: var(--spd-bg-subtle); border-radius: 4px; margin-top: 8px; font-size: 13px;">
            <span>调拨总件数: <strong class="font-mono text-primary">{{ transferTotalQty }}</strong> 件</span>
            <span>调拨总金额: <strong class="font-mono text-danger">¥ {{ transferTotalAmount.toFixed(2) }}</strong></span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="transferModalVisible = false">取消</el-button>
          <el-button type="success" :disabled="transferItems.length === 0" @click="handleSaveTransferVoucher">
            提交调拨单 (双方留存记录)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 5: 从本科室在库台账选品组件 -->
    <SelectSecInventoryDialog
      v-model="showSecSelectModalForOut"
      :inventory-list="secondaryInventoryList"
      title="从本科室在库台账选品开具备料发料出库单"
      @confirm="handleConfirmSecSelectForOut"
    />

    <SelectSecInventoryDialog
      v-model="showSecSelectModalForTransfer"
      :inventory-list="secondaryInventoryList"
      title="从本科室在库台账选品开具跨病区调拨单"
      @confirm="handleConfirmSecSelectForTransfer"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StocktakePlanWorkbench from '@/components/StocktakePlanWorkbench.vue';
import SelectSecInventoryDialog from '@/components/SelectSecInventoryDialog.vue';
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus';
import { httpGet, httpPost } from '@/api/request';
import { useFormDraft } from '@/composables/useFormDraft';
import { useBarcodeScanner } from '@/composables/useBarcodeScanner';
import {
  createRequisitionBatch,
  withdrawRequisition,
  deleteRequisition,
  createManualOutbound,
  getSecondaryStocktakeInventory,
  submitSecondaryStocktake,
  listMainRequisitions,
  type RequisitionBatchItemDTO,
  type StocktakeItemDTO
} from '@/api/stockApi';
import { listSpecs, type SpecItem } from '@/api/dictApi';
import { listInboundOutboundOrders, type InboundOutboundOrder } from '@/api/orderApi';
import {
  listStocktakeTransferOrders,
  createStocktakeOrTransferOrder,
  type StocktakeTransferOrder
} from '@/api/stocktakeTransferApi';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';
import SelectProductDictDialog from '@/components/SelectProductDictDialog.vue';

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const activeTab = ref('requisition');
const currentDeptCode = ref('WH_SEC_ORTHO');

// 全局产品字典选品组件控制 (图 3 / 图 5 规范)
const showDictSelectDialog = ref(false);

// 二级库待接收入库列表
const pendingReceives = ref<any[]>([]);
const loadingReceives = ref(false);

// 二级库在库台账列表
const secondaryInventoryList = ref<any[]>([]);
const loadingInventory = ref(false);

// 监听路由 Query 切换活动 Tab (全面覆盖 6 大子视图)
watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab && typeof newTab === 'string') {
      let target = newTab;
      if (newTab === 'apply') target = 'requisition';
      if (newTab === 'manual-outbound') target = 'manual-out';
      if (['requisition', 'receive', 'stock', 'manual-out', 'transfer', 'stocktake'].includes(target)) {
        activeTab.value = target;
      }
    }
  },
  { immediate: true }
);

// 列表与状态
const requisitions = ref<any[]>([]);
const manualOutbounds = ref<InboundOutboundOrder[]>([]);
const stocktakeItems = ref<StocktakeItemDTO[]>([]);
const allSpecs = ref<SpecItem[]>([]);
const transferList = ref<StocktakeTransferOrder[]>([]);

// 4 大业务台账分页控制
const reqPage = ref(1);
const reqPageSize = ref(10);
const paginatedRequisitions = computed(() => {
  const start = (reqPage.value - 1) * reqPageSize.value;
  return requisitions.value.slice(start, start + reqPageSize.value);
});

const receivePage = ref(1);
const receivePageSize = ref(10);
const paginatedReceives = computed(() => {
  const start = (receivePage.value - 1) * receivePageSize.value;
  return pendingReceives.value.slice(start, start + receivePageSize.value);
});

const invPage = ref(1);
const invPageSize = ref(10);
const paginatedInventory = computed(() => {
  const start = (invPage.value - 1) * invPageSize.value;
  return secondaryInventoryList.value.slice(start, start + invPageSize.value);
});

const manualOutPage = ref(1);
const manualOutPageSize = ref(10);
const paginatedManualOutbounds = computed(() => {
  const start = (manualOutPage.value - 1) * manualOutPageSize.value;
  return manualOutbounds.value.slice(start, start + manualOutPageSize.value);
});

const loadingReq = ref(false);
const loadingManualOut = ref(false);
const loadingStocktake = ref(false);
const submittingReq = ref(false);
const submittingManualOut = ref(false);
const submittingStocktake = ref(false);

// 选中行状态 (用于高对比度高亮)
const selectedRequisition = ref<any | null>(null);

// 申请单明细查看弹窗
const showReqDetailModal = ref(false);
const activeReqDetail = ref<any | null>(null);

// 新建申请单弹窗 (图 4 样式)
const showCreateReqModal = ref(false);
const newReqOrderNo = ref('');
const newReqDate = ref(new Date().toISOString().slice(0, 10));
const createReqTargetMainWh = ref('WH_WEICAI');
const createReqReason = ref('骨科病区周常耗材定额补货');
const createReqItems = ref<RequisitionBatchItemDTO[]>([]);
const selectedReqRowIndex = ref<number>(-1);

const reqFormData = ref({
  reason: createReqReason.value,
  targetMainWh: createReqTargetMainWh.value,
  items: createReqItems.value
});

watch([createReqReason, createReqTargetMainWh, createReqItems], () => {
  reqFormData.value = {
    reason: createReqReason.value,
    targetMainWh: createReqTargetMainWh.value,
    items: createReqItems.value
  };
}, { deep: true });

const {
  hasDraft: hasReqDraft,
  draftTime: reqDraftTime,
  restoreDraft: restoreRawDraft,
  clearDraft: clearReqDraft
} = useFormDraft({
  formKey: 'sec_create_requisition',
  formData: reqFormData
});

function restoreReqDraft() {
  const ok = restoreRawDraft();
  if (ok && reqFormData.value) {
    if (reqFormData.value.reason) createReqReason.value = reqFormData.value.reason;
    if (reqFormData.value.targetMainWh) createReqTargetMainWh.value = reqFormData.value.targetMainWh;
    if (reqFormData.value.items && reqFormData.value.items.length) {
      createReqItems.value = reqFormData.value.items;
    }
    ElMessage.success('已恢复上次编辑的申领单草稿');
  }
}

useBarcodeScanner({
  onScan: (res) => {
    ElNotification({
      title: '临床二级库扫码枪识别',
      message: `已自动校验物料/UDI条码: ${res.rawCode} ${res.piBatch ? '(批号:' + res.piBatch + ')' : ''}`,
      type: 'success',
      duration: 3500
    });
  }
});

// 选品弹窗
const showDictSpecModal = ref(false);
const dictSearchKeyword = ref('');
const selectedDictSpecs = ref<SpecItem[]>([]);

// 手动发料出库弹窗
const showManualOutModal = ref(false);
const selectedStockItemSpecCode = ref('');
const manualOutForm = ref({
  quantity: 10,
  receiver_name: '张主治医生',
  use_purpose: '病房换药日常消耗核减'
});

// 盘点漏账增补
const showSupplementModal = ref(false);
const supplementSelectedSpecId = ref<number>(1);
const supplementForm = ref({
  actual_qty: 5,
  batch_no: 'B20261103'
});

// 应急调拨
const transferModalVisible = ref(false);
const transferForm = ref({
  from_warehouse_code: 'WH_SEC_ORTHO',
  to_warehouse_code: 'WH_SEC_CARDIO',
  qty: 20,
  reason_note: '二级库跨病区应急调拨20片无菌敷贴'
});

// 模拟科室当前在库批次清单 (出库必须基于实际在库选品)
const currentDeptStockList = ref<StocktakeItemDTO[]>([
  {
    spec_code: '936010900135',
    product_name: '医用敷料贴 (透明敷料)',
    spec_name: '10cm*11.5cm',
    model_name: '9546HP',
    unit_name: '片',
    manufacturer: '普昂(杭州)医疗科技有限公司',
    batch_no: 'B2026102801',
    book_qty: 120,
    actual_qty: 120,
    diff_qty: 0,
    unit_price: 8.7654
  },
  {
    spec_code: '93601100000100001',
    product_name: '一次性使用无菌注射器带针',
    spec_name: '5ml 平头',
    model_name: '0.7*30mm',
    unit_name: '支',
    manufacturer: '山东威高集团医用高分子',
    batch_no: 'B20261001',
    book_qty: 85,
    actual_qty: 85,
    diff_qty: 0,
    unit_price: 1.25
  }
]);

const safetyStockList = ref([
  {
    product_code: 'PROD-GEN-001',
    product_name: '一次性使用无菌注射器带针 5ml',
    safe_qty: 200,
    current_qty: 85,
    unit: '支'
  },
  {
    product_code: 'PROD-GEN-002',
    product_name: '医用无菌敷料贴 10cm*15cm',
    safe_qty: 100,
    current_qty: 40,
    unit: '片'
  }
]);

// 计算属性
const currentWarehouseName = computed(() =>
  currentDeptCode.value === 'WH_SEC_ORTHO' ? '骨科病区二级库' : '心内科病区二级库'
);

const currentDeptName = computed(() =>
  currentDeptCode.value === 'WH_SEC_ORTHO' ? '010101 内一科(骨科病区)' : '010201 心血管内科'
);

const pendingRequisitionCount = computed(() =>
  requisitions.value.filter((r) => r.req_status === 'PENDING_APPROVAL').length
);

const todayManualOutAmount = computed(() =>
  manualOutbounds.value.reduce((acc, cur) => acc + (cur.quantity || 0) * 8.5, 0) || 640.0
);

const filteredDictSpecs = computed(() => {
  if (!dictSearchKeyword.value.trim()) return allSpecs.value;
  const kw = dictSearchKeyword.value.toLowerCase().trim();
  return allSpecs.value.filter(
    (s) =>
      s.spec_code.toLowerCase().includes(kw) ||
      s.product_name.toLowerCase().includes(kw) ||
      (s.pinyin_code && s.pinyin_code.toLowerCase().includes(kw))
  );
});

const reqTotalQty = computed(() =>
  createReqItems.value.reduce((acc, cur) => acc + (Number(cur.apply_qty) || 0), 0)
);

const reqTotalAmount = computed(() =>
  createReqItems.value.reduce((acc, cur) => acc + (Number(cur.apply_qty) || 0) * (Number(cur.unit_price) || 0), 0)
);

function requisitionRowClassName({ row }: { row: any }) {
  if (selectedRequisition.value && selectedRequisition.value.id === row.id) {
    return 'is-row-selected-highlight';
  }
  return '';
}

function handleRequisitionRowClick(row: any | null) {
  selectedRequisition.value = row;
}

function handleRequisitionRowDblClick(row: any) {
  selectedRequisition.value = row;
  openRequisitionDetail(row);
}

function switchDept(deptCode: string) {
  currentDeptCode.value = deptCode;
  ElMessage.info(`已切换查看病区：${deptCode === 'WH_SEC_ORTHO' ? '骨科病区二级库' : '心内科病区二级库'}`);
  fetchRequisitions();
  fetchManualOutbounds();
}

/**
 * 获取科室请领记录
 */
async function fetchRequisitions() {
  loadingReq.value = true;
  try {
    const list = await listMainRequisitions({
      warehouse_code: currentDeptCode.value
    });
    requisitions.value = (list || []).map((r: any) => ({
      id: r.id,
      req_order_no: r.req_order_no,
      created_at: r.created_at,
      apply_dept_name: r.apply_dept_name,
      apply_warehouse_code: r.apply_warehouse || r.apply_warehouse_code || currentDeptCode.value,
      applicant_name: r.applicant_name,
      product_name: r.product_name || r.content_summary || '医用敷料贴 (透明敷料)',
      spec_name: r.spec_name || '10cm*11.5cm',
      model_name: r.model_name || '9546HP',
      unit_name: r.unit_name || '片',
      manufacturer: r.manufacturer || '广州明州康普医疗产品有限公司',
      apply_qty: r.apply_qty || 2,
      unit_price: r.unit_price || 8.7654,
      total_amount: r.total_amount || r.apply_amount || 17.53,
      apply_reason: r.apply_reason || r.remark || '病房日常补库申领',
      req_status: r.req_status || r.status || 'PENDING_APPROVAL'
    }));
    if (requisitions.value.length > 0 && !selectedRequisition.value) {
      selectedRequisition.value = requisitions.value[0];
    }
  } catch (err: any) {
    ElMessage.error(err.message || '获取申请记录失败');
  } finally {
    loadingReq.value = false;
  }
}

/**
 * 获取科室手动发料出库记录
 */
async function fetchManualOutbounds() {
  loadingManualOut.value = true;
  try {
    const list = await listInboundOutboundOrders();
    manualOutbounds.value = (list || []).filter(
      (o) => o.order_type === 'GEN_MANUAL_OUT' || o.warehouse_code === currentDeptCode.value
    );
  } catch (err: any) {
    ElMessage.error(err.message || '获取手动发料记录失败');
  } finally {
    loadingManualOut.value = false;
  }
}

/**
 * 获取二级库独立盘点底表
 */
async function fetchSecondaryStocktake() {
  loadingStocktake.value = true;
  try {
    const list = await getSecondaryStocktakeInventory(1);
    stocktakeItems.value = list || [];
    ElMessage.success(`已加载本科室 ${stocktakeItems.value.length} 项在库盘点底表`);
  } catch (err: any) {
    ElMessage.error(err.message || '获取盘点底表失败');
  } finally {
    loadingStocktake.value = false;
  }
}

function calculateStocktakeDiff(row: StocktakeItemDTO) {
  row.diff_qty = Number(row.actual_qty) - Number(row.book_qty);
}

/**
 * 提交二级库盘点平账
 */
async function handleSubmitSecondaryStocktake() {
  if (stocktakeItems.value.length === 0) {
    ElMessage.warning('请先加载本科室盘点底表');
    return;
  }
  submittingStocktake.value = true;
  try {
    await submitSecondaryStocktake({
      warehouse_code: currentDeptCode.value,
      operator_name: userStore.currentUser.realName,
      reason_note: `${currentWarehouseName.value}实物月度盘点与对账`,
      items: stocktakeItems.value
    });
    ElMessage.success('病区盘点已成功平账，对账入出库流水已自动更新！');
    await fetchManualOutbounds();
  } catch (err: any) {
    ElMessage.error(err.message || '提交盘点平账失败');
  } finally {
    submittingStocktake.value = false;
  }
}

/**
 * 打开申请单详情 (图 4)
 */
function openRequisitionDetail(row: any) {
  activeReqDetail.value = row;
  showReqDetailModal.value = true;
}

/**
 * 自主撤回申请单
 */
async function handleWithdrawSelected() {
  if (!selectedRequisition.value) return;
  await handleWithdrawReq(selectedRequisition.value);
}

async function handleWithdrawReq(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定撤回申请单 [${row.req_order_no}] 吗？撤回后主库将停止审批。`,
      '撤回确认',
      { confirmButtonText: '确定撤回', cancelButtonText: '取消', type: 'warning' }
    );
    await withdrawRequisition(row.id);
    ElMessage.success('申请单已成功自主撤回');
    row.req_status = 'WITHDRAWN';
    await fetchRequisitions();
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '撤回失败');
    }
  }
}

/**
 * 删除申请单 (未审核前)
 */
async function handleDeleteSelected() {
  if (!selectedRequisition.value) return;
  await handleDeleteReq(selectedRequisition.value);
}

async function handleDeleteReq(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除申请单 [${row.req_order_no}] 吗？删除后不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    );
    await deleteRequisition(row.id);
    ElMessage.success('申请单已删除');
    selectedRequisition.value = null;
    await fetchRequisitions();
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败');
    }
  }
}

/**
 * 打开新建申请单弹窗 (图 4)
 */
function openCreateRequisitionModal() {
  const dateStr = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 8);
  newReqOrderNo.value = `SQ${dateStr}${Math.floor(1000 + Math.random() * 9000)}`;
  newReqDate.value = new Date().toISOString().slice(0, 10);
  createReqItems.value = [
    {
      spec_code: '936010900135',
      product_name: '医用敷料贴 (透明敷料)',
      spec_name: '10cm*11.5cm',
      model_name: '9546HP',
      unit_name: '片',
      manufacturer: '普昂(杭州)医疗科技有限公司',
      unit_price: 8.7654,
      apply_qty: 2,
      remark: '病房换药周常备货'
    }
  ];
  selectedReqRowIndex.value = 0;
  showCreateReqModal.value = true;
}

function addEmptyReqRow() {
  createReqItems.value.push({
    spec_code: '',
    product_name: '',
    spec_name: '',
    model_name: '',
    unit_name: '件',
    manufacturer: '',
    unit_price: 10.0,
    apply_qty: 1,
    remark: ''
  });
  selectedReqRowIndex.value = createReqItems.value.length - 1;
}

function removeSelectedReqRow() {
  if (selectedReqRowIndex.value >= 0 && selectedReqRowIndex.value < createReqItems.value.length) {
    createReqItems.value.splice(selectedReqRowIndex.value, 1);
    selectedReqRowIndex.value = Math.max(0, createReqItems.value.length - 1);
  }
}

function recalcReqRow(item: RequisitionBatchItemDTO) {
  // 自动重新计算
}

function openDictSpecPicker() {
  selectedDictSpecs.value = [];
  dictSearchKeyword.value = '';
  showDictSpecModal.value = true;
}

function handleDictSpecSelection(rows: SpecItem[]) {
  selectedDictSpecs.value = rows;
}

function confirmSelectDictSpecs() {
  selectedDictSpecs.value.forEach((spec) => {
    createReqItems.value.push({
      spec_code: spec.spec_code,
      product_name: spec.product_name,
      spec_name: spec.spec_name,
      model_name: spec.model_name,
      unit_name: spec.pricing_unit || '件',
      manufacturer: spec.manufacturer,
      unit_price: Number(spec.unit_price) || 10.0,
      apply_qty: 10,
      remark: '临床日常领用'
    });
  });
  showDictSpecModal.value = false;
  ElMessage.success(`已导入 ${selectedDictSpecs.value.length} 项耗材到申请单`);
}

/**
 * 提交申请单
 */
async function handleSaveRequisitionBatch() {
  if (createReqItems.value.length === 0) {
    ElMessage.warning('申请明细不能为空，请至少添加一行耗材');
    return;
  }
  submittingReq.value = true;
  try {
    const res = await createRequisitionBatch({
      apply_dept_code: currentDeptCode.value === 'WH_SEC_ORTHO' ? '010101' : '010201',
      apply_dept_name: currentDeptName.value,
      apply_warehouse_code: currentDeptCode.value,
      target_main_warehouse_code: createReqTargetMainWh.value,
      applicant_id: userStore.currentUser.id || 4,
      applicant_name: userStore.currentUser.realName,
      urgency_level: 'ROUTINE',
      apply_reason: createReqReason.value,
      items: createReqItems.value
    });
    ElMessage.success(`申请单 [${res.req_order_no}] 已成功提报主库！共包含 ${res.total_items} 种物资。`);
    clearReqDraft();
    showCreateReqModal.value = false;
    await fetchRequisitions();
  } catch (err: any) {
    ElMessage.error(err.message || '提报申请单失败');
  } finally {
    submittingReq.value = false;
  }
}

/**
 * 打开手动发料出库弹窗
 */
const manualOutVoucherNo = ref('');
const manualOutItems = ref<any[]>([]);
const showSecSelectModalForOut = ref(false);

const manualOutTotalQty = computed(() =>
  manualOutItems.value.reduce((acc, cur) => acc + (Number(cur.out_qty) || 0), 0)
);

const manualOutTotalAmount = computed(() =>
  manualOutItems.value.reduce((acc, cur) => acc + (Number(cur.out_qty) || 0) * (Number(cur.unit_price) || 0), 0)
);

/**
 * 打开凭证式手动发料出库制单窗口 (对标图 1 / 图 5 规范)
 */
function openManualOutboundModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  manualOutVoucherNo.value = `CK936${ts}`;
  manualOutItems.value = [];
  manualOutForm.value.receiver_name = '张主治医生';
  manualOutForm.value.use_purpose = '病房换药日常消耗核减';
  showManualOutModal.value = true;
}

function handleConfirmSecSelectForOut(selectedItems: any[]) {
  for (const item of selectedItems) {
    const code = item.product_code || item.spec_code;
    const exists = manualOutItems.value.find(i => (i.product_code || i.spec_code) === code && i.batch_no === item.batch_no);
    if (!exists) {
      manualOutItems.value.push({
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_model: item.spec_name || item.spec_model || '标准规格',
        batch_no: item.batch_no,
        current_qty: item.current_qty || item.available_qty || 10,
        out_qty: 1,
        unit_price: Number(item.unit_price) || 8.5
      });
    }
  }
  ElMessage.success(`已选入 ${selectedItems.length} 项在库耗材`);
}

/**
 * 提交科室发料出库凭证并扣减在库库存
 */
async function handleSaveManualOutboundVoucher() {
  if (manualOutItems.value.length === 0) {
    ElMessage.warning('发料明细不能为空，请从在库台账中选品');
    return;
  }

  // 医疗顾问三甲内控风控：二级库临期强控熔断 (<= 30天或已失效)
  for (const it of manualOutItems.value) {
    if (it.expiry_date) {
      const expTime = new Date(it.expiry_date).getTime();
      const nowTime = new Date().getTime();
      const diffDays = Math.ceil((expTime - nowTime) / (1000 * 3600 * 24));
      if (diffDays <= 30) {
        ElMessageBox.alert(
          `规格 [${it.product_name || it.spec_name || it.spec_code}] (批号:${it.batch_no || '在库批次'}) 距离失效仅剩 ${diffDays} 天 (<= 30天强控阈值)，已触发三甲临床二级库 FEFO 强控熔断机制！\n\n系统严禁向病区或病房发放临期/已过期物资，请联系主库退库或发起报废审批。`,
          '二级库临期强控熔断拦截',
          { type: 'error', confirmButtonText: '已知晓并阻断发料' }
        );
        return;
      }
    }
  }

  submittingManualOut.value = true;
  try {
    const res = await createManualOutbound({
      warehouse_code: currentDeptCode.value,
      dept_code: currentDeptCode.value === 'WH_SEC_ORTHO' ? '010101' : '010201',
      receiver_name: manualOutForm.value.receiver_name || '临床医生',
      operator_name: userStore.currentUser.realName,
      use_purpose: manualOutForm.value.use_purpose || '科室发料消耗',
      items: manualOutItems.value.map(item => ({
        spec_code: item.spec_code || item.product_code,
        batch_no: item.batch_no,
        quantity: item.out_qty || 1,
        unit_price: item.unit_price || 8.5,
        remark: manualOutForm.value.use_purpose || '病房换药日常消耗核减'
      }))
    });
    ElMessage.success(`科室发料单 [${res.outbound_order_no}] 出库成功！共核减 ${res.total_qty} 件，结转支出 ¥${res.total_amount.toFixed(2)}`);
    showManualOutModal.value = false;
    await fetchSecondaryInventory();
    await fetchManualOutbounds();
  } catch (err: any) {
    ElMessage.error(err.message || '手动发料出库失败');
  } finally {
    submittingManualOut.value = false;
  }
}

// 跨病区调拨单状态与处理
const transferVoucherNo = ref('');
const transferItems = ref<any[]>([]);
const showSecSelectModalForTransfer = ref(false);

const transferTotalQty = computed(() =>
  transferItems.value.reduce((acc, cur) => acc + (Number(cur.transfer_qty) || 0), 0)
);

const transferTotalAmount = computed(() =>
  transferItems.value.reduce((acc, cur) => acc + (Number(cur.transfer_qty) || 0) * (Number(cur.unit_price) || 0), 0)
);

function openTransferModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  transferVoucherNo.value = `TR936${ts}`;
  transferItems.value = [];
  transferForm.value.to_warehouse_code = currentDeptCode.value === 'WH_SEC_ORTHO' ? 'WH_SEC_CARDIO' : 'WH_SEC_ORTHO';
  transferForm.value.reason_note = '抢救急用跨病区应急调剂无菌敷料';
  transferModalVisible.value = true;
}

function handleConfirmSecSelectForTransfer(selectedItems: any[]) {
  for (const item of selectedItems) {
    const code = item.product_code || item.spec_code;
    const exists = transferItems.value.find(i => (i.product_code || i.spec_code) === code && i.batch_no === item.batch_no);
    if (!exists) {
      transferItems.value.push({
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_model: item.spec_name || item.spec_model || '标准规格',
        batch_no: item.batch_no,
        current_qty: item.current_qty || item.available_qty || 10,
        transfer_qty: 1,
        unit_price: Number(item.unit_price) || 8.5
      });
    }
  }
  ElMessage.success(`已选入 ${selectedItems.length} 项调拨耗材`);
}

async function handleSaveTransferVoucher() {
  if (transferItems.value.length === 0) {
    ElMessage.warning('调拨物资明细不能为空，请从在库台账中选品');
    return;
  }
  try {
    const targetName = transferForm.value.to_warehouse_code === 'WH_SEC_CARDIO' ? '心内科病区二级库' : '骨科病区二级库';
    await httpPost('/ext/orders/ward-transfer', {
      from_warehouse_code: currentDeptCode.value,
      from_dept_name: currentDeptName.value,
      to_warehouse_code: transferForm.value.to_warehouse_code,
      to_dept_name: targetName,
      operator_name: userStore.currentUser.realName,
      reason_note: transferForm.value.reason_note || '跨病区应急调剂',
      items: transferItems.value.map(item => ({
        spec_code: item.spec_code || item.product_code,
        product_name: item.product_name,
        batch_no: item.batch_no,
        quantity: item.transfer_qty || 1,
        unit_price: item.unit_price || 8.5
      }))
    });
    ElMessage.success('跨病区科室调拨单已生成并生效！双方库房已留存调拨流水记录并增减库存。');
    transferModalVisible.value = false;
    await fetchSecondaryInventory();
    await fetchManualOutbounds();
  } catch (err: any) {
    ElMessage.error(err.message || '调拨出库失败');
  }
}

// 增补漏账耗材 (触发全院表格选品弹窗，对齐图 3 / 图 5 规范)
function openAddSupplementDialog() {
  showDictSelectDialog.value = true;
}

/**
 * 接收从全局产品字典选品组件导入的耗材 (图 3 表格多选导入)
 */
function handleDictSelected(selectedRows: any[]) {
  for (const item of selectedRows) {
    const exists = stocktakeItems.value.find(s => s.spec_code === item.product_code);
    if (!exists) {
      stocktakeItems.value.push({
        spec_code: item.product_code,
        product_name: item.product_name,
        spec_name: item.spec_name,
        model_name: item.spec_name,
        unit_name: item.pricing_unit || '件',
        manufacturer: item.manufacturer,
        batch_no: `B${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
        book_qty: 0,
        actual_qty: 5,
        diff_qty: 5,
        unit_price: Number(item.unit_price || 10),
        is_new_supplement: 1
      });
    }
  }
  ElMessage.success(`已从全院产品字典增补 ${selectedRows.length} 项耗材到本科室盘点表！`);
}

/**
 * 获取主库待接收入库分发调拨单
 */
async function fetchPendingReceives() {
  loadingReceives.value = true;
  try {
    const res = await httpGet('/secondary-warehouse/pending-receives', {
      warehouse_code: currentDeptCode.value
    });
    pendingReceives.value = res || [];
  } catch {
    pendingReceives.value = [];
  } finally {
    loadingReceives.value = false;
  }
}

/**
 * 确认签收接收入库
 */
async function handleAcceptReceive(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定签收并接收入库分发单 [${row.dist_order_no}] 吗？\n物资数量: ${row.dist_qty} 件，将立即计入 ${row.target_dept_name} 在库资产。`,
      '二级库接收入库确认',
      { confirmButtonText: '确认接收入库', cancelButtonText: '取消', type: 'success' }
    );
    await httpPost(`/secondary-warehouse/receive/${row.id}`, { is_accept: true });
    ElMessage.success(`分发单 [${row.dist_order_no}] 已成功验收入库！`);
    await fetchPendingReceives();
    await fetchSecondaryInventory();
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '接收入库失败');
  }
}

/**
 * 差异拒收退料回主库
 */
async function handleRejectReceive(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定差异拒收分发单 [${row.dist_order_no}] 吗？物资将逆向退回主库并回滚主库可用量。`,
      '差异拒收退库确认',
      { confirmButtonText: '确定拒收退回', cancelButtonText: '取消', type: 'error' }
    );
    await httpPost(`/secondary-warehouse/receive/${row.id}`, {
      is_accept: false,
      reject_reason: '实物包装破损或规格型号不符'
    });
    ElMessage.success(`分发单 [${row.dist_order_no}] 已拒收并退回主库`);
    await fetchPendingReceives();
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '拒收操作失败');
  }
}

/**
 * 获取科室实物在库实时台账
 */
async function fetchSecondaryInventory() {
  loadingInventory.value = true;
  try {
    const res = await httpGet('/secondary-warehouse/inventory', {
      warehouse_code: currentDeptCode.value
    });
    secondaryInventoryList.value = res || [];
    if (secondaryInventoryList.value.length === 0) {
      secondaryInventoryList.value = [
        {
          id: 1,
          product_code: '936010900135',
          product_name: '医用敷料贴 (透明敷料)',
          batch_no: 'B2026102801',
          expiry_date: '2029-10-31',
          current_qty: 120,
          consumed_qty: 35,
          unit_price: 8.7654,
          sec_shelf_code: '骨科二级库-货架01-层02',
          dept_safe_min: 20,
          batch_status: 'NORMAL'
        },
        {
          id: 2,
          product_code: '93601100000100001',
          product_name: '一次性使用无菌注射器带针 5ml',
          batch_no: 'B20261001',
          expiry_date: '2028-09-30',
          current_qty: 85,
          consumed_qty: 215,
          unit_price: 1.25,
          sec_shelf_code: '骨科二级库-货架02-层01',
          dept_safe_min: 50,
          batch_status: 'NORMAL'
        }
      ];
    }
  } catch {
    secondaryInventoryList.value = [];
  } finally {
    loadingInventory.value = false;
  }
}

// 应急调拨
async function handleTransferSubmit() {
  try {
    await createStocktakeOrTransferOrder({
      biz_category: 'CROSS_HOSP_TRANSFER',
      from_warehouse_code: transferForm.value.from_warehouse_code,
      to_warehouse_code: transferForm.value.to_warehouse_code,
      product_id: 2,
      book_qty: 100,
      actual_or_transfer_qty: transferForm.value.qty,
      operator_name: userStore.currentUser.realName,
      reason_note: transferForm.value.reason_note
    });
    ElMessage.success('跨病区调拨单已生成并生效');
    transferModalVisible.value = false;
  } catch (err: any) {
    ElMessage.error(err.message || '调拨失败');
  }
}

/**
 * 标签页切换响应
 * @param tabName 目标标签页名称
 * @returns void
 * @route 切换视图并同步更新浏览器 query.tab
 * @throws 无异常
 */
function handleTabChange(tabName: any) {
  router.replace({ query: { ...route.query, tab: tabName } });
  if (tabName === 'requisition') fetchRequisitions();
  else if (tabName === 'receive') fetchPendingReceives();
  else if (tabName === 'stock') fetchSecondaryInventory();
  else if (tabName === 'manual-out') fetchManualOutbounds();
  else if (tabName === 'stocktake') fetchSecondaryStocktake();
  else if (tabName === 'transfer') fetchManualOutbounds();
}

onMounted(async () => {
  fetchRequisitions();
  fetchPendingReceives();
  fetchSecondaryInventory();
  fetchManualOutbounds();
  try {
    const spRes = await listSpecs();
    allSpecs.value = spRes || [];
  } catch {
    // 静默降级
  }
});
</script>

<style scoped>
.secondary-warehouse-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 4 宫格 KPI 大盘 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-card {
  padding: 18px 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.kpi-title {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kpi-val {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin: 8px 0;
}

.kpi-unit {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

.kpi-sub {
  font-size: 11.5px;
  color: var(--color-success);
  display: flex;
  align-items: center;
  gap: 4px;
}

.text-warn { color: var(--color-warning) !important; }
.text-danger { color: var(--color-danger) !important; }
.text-success { color: var(--color-success) !important; }
.text-accent { color: var(--accent-primary) !important; }
.text-muted { color: var(--text-muted) !important; }

/* 毛玻璃容器 */
.glass-panel {
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

/* 病区切换栏 */
.dept-switcher-bar {
  padding: 10px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.dept-pills-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dept-label {
  font-size: 12.5px;
  color: var(--text-muted);
  font-weight: 600;
}

.dept-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid var(--border-card);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.dept-pill:hover {
  background: rgba(56, 189, 248, 0.1);
  color: var(--text-primary);
  border-color: rgba(56, 189, 248, 0.3);
}

.dept-pill.active {
  background: rgba(56, 189, 248, 0.18);
  color: var(--accent-primary);
  border-color: rgba(56, 189, 248, 0.4);
  box-shadow: 0 2px 8px rgba(56, 189, 248, 0.2);
}

.dept-action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-container-panel {
  padding: 16px 20px;
}

.tab-content-area {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 8px;
}

.pane-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-card);
  border-radius: 8px;
  padding: 10px 14px;
}

.action-desc-text {
  font-size: 12.5px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 状态药丸标签 */
.status-chip {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.chip-active {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.chip-disabled {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.chip-locked {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.chip-warning {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.chip-info {
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
  border: 1px solid rgba(56, 189, 248, 0.25);
}

/* 高对比度选中行高亮 */
:deep(.is-row-selected-highlight) {
  background: rgba(14, 165, 233, 0.16) !important;
  border-left: 3px solid #0284c7 !important;
}

:deep(.spd-clickable-table .el-table__row) {
  cursor: pointer;
  transition: background-color 0.12s ease;
}

:deep(.spd-clickable-table .el-table__row:hover) {
  background: rgba(255, 255, 255, 0.05) !important;
}

/* 医院标准单据容器与印章 (图 4) */
.hospital-bill-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bill-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2px solid var(--accent-primary);
  padding-bottom: 8px;
  position: relative;
}

.bill-title-center {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 2px;
  color: var(--text-primary);
}

.bill-stamp {
  font-size: 13px;
  font-weight: 800;
  padding: 4px 12px;
  border-radius: 4px;
  letter-spacing: 1px;
}

.stamp-pending {
  border: 2px solid #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

.stamp-approved {
  border: 2px solid #10b981;
  color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}

.bill-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 18px;
  background: rgba(255, 255, 255, 0.02);
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-card);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
}

.meta-label {
  color: var(--text-muted);
  font-weight: 600;
}

.meta-val {
  color: var(--text-primary);
}

.bill-body-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
}

.bill-body-toolbar .title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.bill-body-toolbar .btns {
  display: flex;
  gap: 8px;
}

.table-scroll-wrap {
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid var(--border-card);
  border-radius: 6px;
}

.bill-detail-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.bill-detail-table th {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  padding: 8px 10px;
  border: 1px solid var(--border-card);
  font-weight: 600;
  white-space: nowrap;
}

.bill-detail-table td {
  padding: 6px 10px;
  border: 1px solid var(--border-card);
  color: var(--text-primary);
}

.bill-detail-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

.bill-detail-table tbody tr.row-active {
  background: rgba(14, 165, 233, 0.15);
}

.bill-total-row {
  background: rgba(255, 255, 255, 0.05);
  font-weight: 700;
}

.table-inline-input {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 4px;
}

.table-inline-input:focus {
  background: var(--bg-card);
  box-shadow: 0 0 0 1px var(--accent-primary);
  outline: none;
}

.spd-input, .spd-select {
  height: 30px;
  padding: 0 8px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
  outline: none;
}

.spd-input:focus, .spd-select:focus {
  border-color: var(--accent-primary);
}

.dialog-warning-banner {
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.3);
  color: var(--color-warning);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  margin-bottom: 12px;
}

.spd-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
  transition: all 0.15s ease;
}

.spd-btn:hover {
  border-color: var(--accent-primary);
}

.spd-btn.btn-primary {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #ffffff;
}

.spd-btn.btn-warn {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.4);
  color: #f59e0b;
}

.spd-btn.btn-danger {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.spd-btn.btn-sm {
  padding: 3px 8px;
  font-size: 11.5px;
}

.mini-op-btn {
  border: 1px solid var(--border-card);
  background: transparent;
  color: var(--accent-primary);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  cursor: pointer;
}

.mini-op-btn:hover {
  background: rgba(56, 189, 248, 0.1);
}

.mini-op-btn.btn-warn {
  color: #f59e0b;
}

.mini-op-btn.btn-danger {
  color: #ef4444;
}
</style>
