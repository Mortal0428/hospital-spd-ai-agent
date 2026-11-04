<template>
  <div class="general-material-view">
    <!-- 顶部 4 宫格高质感毛玻璃 KPI 指标大盘 -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>主库总仓在库数量</span>
          <SvgIcon name="package" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          {{ totalStockQty }} <span class="kpi-unit">件</span>
        </div>
        <div class="kpi-sub">
          <SvgIcon name="check" :size="13" color="var(--color-success)" />
          <span>FEFO 近效期先出批次就绪</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>待审核临床请领单</span>
          <SvgIcon name="clock" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-warn">
          {{ pendingRequisitionCount }} <span class="kpi-unit">笔待办</span>
        </div>
        <div class="kpi-sub text-warn">
          <SvgIcon name="arrow-right" :size="13" color="var(--color-warning)" />
          <span>审核通过后自动生成出库联动</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>近效期 FEFO 预警批次</span>
          <SvgIcon name="warning" :size="16" color="var(--color-warning)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-warn">
          2 <span class="kpi-unit">批 (优先出库)</span>
        </div>
        <div class="kpi-sub text-warn">
          <SvgIcon name="clock" :size="13" color="var(--color-warning)" />
          <span>B20261001 批次 2029-09-30 临期监控</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>今日按需分发出库额</span>
          <SvgIcon name="stats" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          ¥ {{ todayDispatchAmount.toFixed(2) }}
        </div>
        <div class="kpi-sub">
          <SvgIcon name="safe" :size="13" color="var(--color-success)" />
          <span>院内调拨严格遵守移库不计费</span>
        </div>
      </div>
    </div>

    <!-- 主体毛玻璃 Tab 工作台 -->
    <div class="glass-panel tab-container-panel">
      <el-tabs v-model="activeTab" class="fusion-tabs" @tab-change="handleTabChange">
        <!-- =====================================================================
             Tab 1: 临床请领受理 (对标图 3)
             ===================================================================== -->
        <el-tab-pane label="临床请领受理" name="requisition">
          <div class="tab-content-area">
            <!-- 图 3 顶栏操作条 -->
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>临床科室申领受理看板 · 双击单据行可穿透查看申请单明细 · 单击单据行高亮选中</span>
              </div>
              <div class="action-btn-group">
                <!-- 审核通过并出库 -->
                <el-button
                  type="success"
                  size="small"
                  :disabled="!selectedRequisition || selectedRequisition.req_status !== 'PENDING_APPROVAL'"
                  @click="handleApproveSelectedRequisition"
                >
                  <SvgIcon name="check" :size="13" style="margin-right: 4px;" />
                  审核通过并出库
                </el-button>

                <!-- 退回申请 -->
                <el-button
                  type="danger"
                  plain
                  size="small"
                  :disabled="!selectedRequisition || selectedRequisition.req_status !== 'PENDING_APPROVAL'"
                  @click="handleRejectSelectedRequisition"
                >
                  <SvgIcon name="close" :size="13" style="margin-right: 4px;" />
                  退回
                </el-button>

                <!-- 查看申请单明细 (图 4) -->
                <el-button
                  type="primary"
                  plain
                  size="small"
                  :disabled="!selectedRequisition"
                  @click="openRequisitionDetail(selectedRequisition)"
                >
                  <SvgIcon name="dict" :size="13" style="margin-right: 4px;" />
                  查看申请单明细
                </el-button>

                <el-button plain size="small" @click="fetchRequisitions">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新
                </el-button>
              </div>
            </div>

            <!-- 图 3 请领受理单据表格 -->
            <el-table
              :data="paginatedRequisitions"
              border
              stripe
              highlight-current-row
              class="fusion-styled-table spd-clickable-table"
              :row-class-name="requisitionTableRowClassName"
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

              <el-table-column prop="apply_dept_name" label="申请部门" width="150" />

              <el-table-column prop="apply_warehouse_code" label="申请仓库" width="150">
                <template #default="{ row }">
                  <span class="font-mono text-muted">{{ row.apply_warehouse_code }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="applicant_name" label="申请人" width="100" align="center" />

              <el-table-column prop="product_name" label="申请内容" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span>{{ row.product_name }} {{ row.spec_name ? `(${row.spec_name})` : '' }}</span>
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

              <el-table-column prop="apply_reason" label="备注说明" min-width="150" show-overflow-tooltip />

              <el-table-column prop="req_status" label="状态" width="130" align="center" fixed="right">
                <template #default="{ row }">
                  <span v-if="row.req_status === 'APPROVED_DISPATCHED'" class="status-chip chip-active">已审核出库</span>
                  <span v-else-if="row.req_status === 'REJECTED'" class="status-chip chip-disabled">已退回</span>
                  <span v-else class="status-chip chip-locked">待审批</span>
                </template>
              </el-table-column>
            </el-table>

            <!-- 申领受理分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="reqCurrentPage"
                v-model:page-size="reqPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="requisitions.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 2: 耗材验收入库 (对标图 5 采购入库单)
             ===================================================================== -->
        <el-tab-pane label="耗材验收入库与退货" name="inbound">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>采购入库全流程台账 · 双击单据行可穿透查看入库单多耗材明细 · 单击单据行高亮选中</span>
              </div>
              <div class="action-btn-group">
                <!-- 填写采购入库单 (图 5) -->
                <el-button
                  v-if="userStore.canAction('GEN_INBOUND', 'can_create')"
                  type="primary"
                  size="small"
                  @click="openPurchaseInboundModal"
                >
                  <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                  填写采购入库单
                </el-button>

                <!-- 开具退给供应商红字单 -->
                <el-button
                  v-if="userStore.canAction('GEN_INBOUND', 'can_create')"
                  type="danger"
                  plain
                  size="small"
                  @click="openReturnSupplierModal"
                >
                  <SvgIcon name="close" :size="13" style="margin-right: 4px;" />
                  开具退给供应商红字单
                </el-button>

                <el-button plain size="small" @click="fetchOrders">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新台账
                </el-button>
              </div>
            </div>

            <!-- 入库单据主列表 -->
            <el-table
              :data="paginatedInboundOrders"
              border
              stripe
              highlight-current-row
              class="fusion-styled-table spd-clickable-table"
              :row-class-name="orderTableRowClassName"
              v-loading="loadingOrders"
              @current-change="handleOrderRowClick"
              @row-dblclick="handleOrderRowDblClick"
            >
              <el-table-column type="index" label="序号" width="55" align="center" />

              <el-table-column prop="order_no" label="入库单号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="order_type" label="单据性质" width="150" align="center">
                <template #default="{ row }">
                  <span v-if="row.order_type === 'RETURN_TO_SUPPLIER'" class="status-chip chip-disabled">退给供应商红字</span>
                  <span v-else-if="row.order_type === 'PURCHASE_INBOUND'" class="status-chip chip-active">采购验收入库</span>
                  <span v-else class="status-chip chip-info">普通入库单</span>
                </template>
              </el-table-column>

              <el-table-column prop="target_dept_or_supplier" label="供应商 / 发货单位" min-width="180" show-overflow-tooltip />

              <el-table-column prop="product_name" label="物资品名" min-width="180" show-overflow-tooltip />

              <el-table-column prop="quantity" label="入库数量" width="120" align="right">
                <template #default="{ row }">
                  <strong class="font-mono tabular-nums" :class="row.quantity < 0 ? 'text-danger' : 'text-primary'">
                    {{ row.quantity }}
                  </strong>
                </template>
              </el-table-column>

              <el-table-column prop="created_by" label="经办人" width="100" align="center" />

              <el-table-column prop="created_at" label="入库时间" width="160">
                <template #default="{ row }">
                  <span class="font-mono text-muted" style="font-size: 11.5px;">{{ row.created_at }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="confirm_stage" label="审核状态" width="130" align="center">
                <template #default="{ row }">
                  <span v-if="row.confirm_stage === 'SUBMITTED'" class="status-chip chip-active">已审核入库</span>
                  <span v-else class="status-chip chip-locked">待二次确认</span>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="200" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 6px; justify-content: center;">
                    <el-button
                      v-if="row.confirm_stage === 'PENDING_CONFIRM' && userStore.canAction('GEN_INBOUND', 'can_second_confirm')"
                      size="small"
                      type="primary"
                      @click="openTwoStep(row, 'SECOND_CONFIRM')"
                    >
                      二次确认
                    </el-button>
                    <el-button
                      v-if="row.confirm_stage === 'SUBMITTED' && userStore.canAction('GEN_INBOUND', 'can_cancel_submit')"
                      size="small"
                      type="warning"
                      plain
                      @click="openTwoStep(row, 'CANCEL_SUBMIT')"
                    >
                      取消提交
                    </el-button>
                    <el-button
                      v-if="userStore.canAction('GEN_INBOUND', 'can_print')"
                      size="small"
                      plain
                      @click="openPrint(row)"
                    >
                      四联打印
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 耗材验收入库分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="inboundCurrentPage"
                v-model:page-size="inboundPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="inboundOrders.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 3: 主库耗材按需分发出库
             ===================================================================== -->
        <el-tab-pane label="主库耗材按需分发出库" name="outbound">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>主库向临床二级库按需分发出库单 · 遵循 FEFO 近效期先出与移库不计费准则 · 双击单据行查看出库明细</span>
              </div>
              <div class="action-btn-group">
                <el-button
                  type="primary"
                  size="small"
                  @click="openCreateOutboundVoucherModal"
                >
                  <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                  + 填写出库单
                </el-button>
                <el-button plain size="small" @click="fetchOrders">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新出库台账
                </el-button>
              </div>
            </div>

            <el-table
              :data="paginatedOutboundOrders"
              border
              stripe
              highlight-current-row
              class="fusion-styled-table spd-clickable-table"
              :row-class-name="orderTableRowClassName"
              v-loading="loadingOrders"
              @current-change="handleOrderRowClick"
              @row-dblclick="handleOrderRowDblClick"
            >
              <el-table-column type="index" label="序号" width="55" align="center" />

              <el-table-column prop="order_no" label="出库单号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="order_type" label="出库类型" width="160" align="center">
                <template #default="{ row }">
                  <span v-if="row.order_type === 'REQ_AUTO_OUT'" class="status-chip chip-active">请领联动出库</span>
                  <span v-else class="status-chip chip-info">主库按需分发</span>
                </template>
              </el-table-column>

              <el-table-column prop="product_name" label="物资品名" min-width="180" show-overflow-tooltip />

              <el-table-column prop="target_dept_or_supplier" label="目标临床科室" width="160" />

              <el-table-column prop="quantity" label="出库数量" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold">{{ row.quantity }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="created_by" label="发料经办人" width="110" align="center" />

              <el-table-column prop="created_at" label="出库时间" width="160">
                <template #default="{ row }">
                  <span class="font-mono text-muted" style="font-size: 11.5px;">{{ row.created_at }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="confirm_stage" label="审核状态" width="130" align="center">
                <template #default="{ row }">
                  <span v-if="row.confirm_stage === 'SUBMITTED'" class="status-chip chip-active">已审核出库</span>
                  <span v-else class="status-chip chip-locked">待二次确认</span>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="200" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 6px; justify-content: center;">
                    <el-button
                      v-if="row.confirm_stage === 'PENDING_CONFIRM' && userStore.canAction('GEN_OUTBOUND', 'can_second_confirm')"
                      size="small"
                      type="primary"
                      @click="openTwoStep(row, 'SECOND_CONFIRM')"
                    >
                      确认出库
                    </el-button>
                    <el-button
                      v-if="userStore.canAction('GEN_OUTBOUND', 'can_print')"
                      size="small"
                      plain
                      @click="openPrint(row)"
                    >
                      调拨单打印
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 主库按需分发出库分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="outboundCurrentPage"
                v-model:page-size="outboundPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="outboundOrders.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 4: 主库独立盘点与漏账耗材增补对账
             ===================================================================== -->
        <el-tab-pane label="主库独立盘点" name="stocktake">
          <div class="tab-content-area">
            <StocktakePlanWorkbench scope="MAIN" default-warehouse-code="WH_WEICAI" />
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 5: 全院与分仓实时库存总览 (按授权仓库动态过滤)
             ===================================================================== -->
        <el-tab-pane label="全院/分仓实时库存" name="inventory">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="package" :size="15" color="var(--accent-primary)" />
                <span>全院与多仓库实时在库批次台账 · 按人员授权仓库动态展示 · FEFO 近效期先出监控</span>
              </div>
              <div class="action-btn-group">
                <el-select v-model="realtimeWhFilter" size="small" placeholder="按仓库筛选" style="width: 170px;" @change="fetchRealtimeStock">
                  <el-option label="全部授权仓库汇总" value="ALL" />
                  <el-option v-for="wh in accessibleWarehouses" :key="wh.warehouse_code" :label="wh.warehouse_name" :value="wh.warehouse_code" />
                </el-select>
                <el-input v-model="realtimeKeyword" placeholder="编码/品名/批号..." size="small" style="width: 180px;" clearable @keyup.enter="fetchRealtimeStock" />
                <el-button plain size="small" @click="fetchRealtimeStock">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新实时库存
                </el-button>
              </div>
            </div>

            <el-table :data="realtimeStockList" border stripe class="fusion-styled-table" v-loading="loadingRealtimeStock">
              <el-table-column type="index" label="序号" width="55" align="center" />
              <el-table-column prop="warehouse_name" label="所属仓库" width="150">
                <template #default="{ row }">
                  <span class="status-chip chip-info">{{ row.warehouse_name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_code" label="物料代码" width="165" class-name="font-mono text-accent">
                <template #default="{ row }">
                  <span class="font-bold">{{ row.product_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="耗材品名" min-width="190" show-overflow-tooltip />
              <el-table-column prop="batch_no" label="生产批号" width="130" class-name="font-mono" />
              <el-table-column prop="expiry_date" label="有效期至" width="120" class-name="font-mono">
                <template #default="{ row }">
                  <span :class="{ 'text-danger font-bold': row.is_near_expiry === 1 }">{{ row.expiry_date }}</span>
                  <span v-if="row.is_near_expiry === 1" class="status-chip chip-danger" style="margin-left: 4px; font-size: 10px; padding: 0 4px;">近效期</span>
                </template>
              </el-table-column>
              <el-table-column prop="current_qty" label="在库实数" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold">{{ row.current_qty }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="available_qty" label="可用库存" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-success">{{ row.available_qty }}</span>
                </template>
              </el-table-column>
              <el-table-column label="基准单价" width="105" align="right">
                <template #default="{ row }">
                  <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="库存估值" width="125" align="right">
                <template #default="{ row }">
                  <span class="font-mono font-bold">¥ {{ Number(row.total_amount || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="shelf_location" label="货位号" width="130" class-name="font-mono" />
            </el-table>

            <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
              <el-pagination
                v-model:current-page="realtimePage"
                v-model:page-size="realtimePageSize"
                :total="realtimeTotal"
                :page-sizes="[15, 30, 50]"
                layout="total, sizes, prev, pager, next"
                @current-change="fetchRealtimeStock"
                @size-change="fetchRealtimeStock"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 5: 科室期初数据建账 (不可逆锁)
             ===================================================================== -->
        <el-tab-pane label="科室期初建账 (不可逆锁)" name="init-stock">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="lock" :size="15" color="var(--color-warning)" />
                <span>各科室仓库期初数据一次性建账 · 录入提交后需二次确认，二次确认后永久锁死只读</span>
              </div>
              <div class="action-btn-group">
                <el-button
                  v-if="userStore.canAction('GEN_INIT_STOCK', 'can_create')"
                  type="primary"
                  size="small"
                  @click="openInitStockModal"
                >
                  <SvgIcon name="package" :size="13" style="margin-right: 4px;" />
                  录入科室期初建账单
                </el-button>
              </div>
            </div>

            <el-table
              :data="initStockOrders"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingOrders"
            >
              <el-table-column prop="order_no" label="建账单号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="warehouse_code" label="仓库编码" width="140" class-name="font-mono" />
              <el-table-column prop="target_dept_or_supplier" label="说明" width="160" />
              <el-table-column prop="quantity" label="期初在库量" width="120" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold">{{ row.quantity }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="is_irreversible_locked" label="不可逆锁定" width="130" align="center">
                <template #default="{ row }">
                  <span v-if="row.is_irreversible_locked" class="status-chip chip-disabled">已永久锁死</span>
                  <span v-else class="status-chip chip-locked">待二次确认锁定</span>
                </template>
              </el-table-column>
              <el-table-column label="两阶段确认操作" width="200" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    v-if="!row.is_irreversible_locked && userStore.canAction('GEN_INIT_STOCK', 'can_second_confirm')"
                    size="small"
                    type="danger"
                    @click="openTwoStep(row, 'SECOND_CONFIRM', true)"
                  >
                    第2次确认(永久锁死)
                  </el-button>
                  <span v-else class="text-muted font-mono" style="font-size: 11.5px;">数据已永久封账</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- =========================================================================
         弹窗 1：图 4 样式 《申请单明细》 对话框 (双击请领单穿透查看)
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
        <!-- 头部印章与标题 -->
        <div class="bill-header-row">
          <div class="bill-title-center">申 请 单</div>
          <div class="bill-stamp" :class="activeReqDetail.req_status === 'APPROVED_DISPATCHED' ? 'stamp-approved' : 'stamp-pending'">
            {{ activeReqDetail.req_status === 'APPROVED_DISPATCHED' ? '已审核' : '未审核' }}
          </div>
        </div>

        <!-- 单头元数据网格 (对标图 4) -->
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
          <div class="meta-item" style="grid-column: span 3;">
            <span class="meta-label">申请备注:</span>
            <span class="meta-val">{{ activeReqDetail.apply_reason || '临床科室日常补库申领' }}</span>
          </div>
        </div>

        <!-- 单身物资列表明细 -->
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
          <el-button
            v-if="activeReqDetail && activeReqDetail.req_status === 'PENDING_APPROVAL'"
            type="danger"
            plain
            @click="handleRejectSelectedRequisition"
          >
            退回申请
          </el-button>
          <el-button
            v-if="activeReqDetail && activeReqDetail.req_status === 'PENDING_APPROVAL'"
            type="success"
            @click="handleApproveSelectedRequisition"
          >
            审核通过并生成出库单
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 2：图 5 样式 《采购入库单》 填单模态框 (支持多耗材录入与字典选品)
         ========================================================================= -->
    <el-dialog
      v-model="showPurchaseInboundModal"
      title="填写入库单 - 采购入库"
      width="1050px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal purchase-inbound-dialog"
    >
      <div class="hospital-bill-container">
        <!-- 自动防丢草稿箱提示栏 -->
        <div v-if="hasInboundDraft" class="draft-tip-banner" style="display:flex; justify-content:space-between; align-items:center; background: rgba(56, 189, 248, 0.1); border: 1px dashed #38bdf8; border-radius: 6px; padding: 6px 12px; margin-bottom: 12px; font-size: 13px;">
          <span>检测到未保存的入库单草稿 (自动暂存时间: {{ inboundDraftTime }})</span>
          <div style="display:flex; gap: 8px;">
            <el-button size="small" type="primary" link @click="restoreInboundDraft">一键恢复草稿</el-button>
            <el-button size="small" type="danger" link @click="clearInboundDraft">丢弃</el-button>
          </div>
        </div>

        <!-- 标题 -->
        <div class="bill-header-row">
          <div class="bill-title-center">采 购 入 库 单</div>
          <div class="bill-top-options">
            <el-checkbox v-model="purchaseForm.auto_approve">入库单保存后自动审核</el-checkbox>
            <el-checkbox v-model="purchaseFormAutoPrint">入库单保存时自动打印</el-checkbox>
          </div>
        </div>

        <!-- 单头录入表单网格 (1:1 对标图 5) -->
        <div class="purchase-header-grid">
          <div class="form-item-inline">
            <label>配送单号:</label>
            <input v-model="purchaseForm.delivery_order_no" placeholder="如: PS-20261103-01" class="spd-input font-mono" />
          </div>
          <div class="form-item-inline">
            <label>入库单号:</label>
            <input v-model="purchaseFormOrderNo" disabled class="spd-input font-mono font-bold" />
          </div>
          <div class="form-item-inline">
            <label>入库日期:</label>
            <input v-model="purchaseFormDate" type="date" class="spd-input font-mono" />
          </div>
          <div class="form-item-inline">
            <label>入库类别:</label>
            <select v-model="purchaseForm.inbound_type" class="spd-select">
              <option value="PURCHASE_INBOUND">采购入库</option>
              <option value="DONATION_INBOUND">捐赠入库</option>
              <option value="TRANSFER_INBOUND">调拨入库</option>
            </select>
          </div>

          <div class="form-item-inline">
            <label class="required">发票号:</label>
            <input v-model="purchaseForm.invoice_no" placeholder="如: FP-20261103001" class="spd-input font-mono" />
          </div>
          <div class="form-item-inline">
            <label>发票日期:</label>
            <input v-model="purchaseForm.invoice_date" type="date" class="spd-input font-mono" />
          </div>
          <div class="form-item-inline">
            <label class="required">入库仓库:</label>
            <select v-model="purchaseForm.warehouse_code" class="spd-select">
              <option value="WH_WEICAI">卫材库房 (WH_WEICAI)</option>
              <option value="WH_ZONGWU">总务仓库 (WH_ZONGWU)</option>
              <option value="WH_ZHUANXIANG">专项库房 (高值专仓)</option>
              <option value="WH_EQUIP">设备库房 (WH_EQUIP)</option>
            </select>
          </div>
          <div class="form-item-inline">
            <label>采购人:</label>
            <input v-model="purchaseForm.purchaser_name" placeholder="如: 王建国" class="spd-input" />
          </div>

          <div class="form-item-inline" style="grid-column: span 2;">
            <label class="required">供应商:</label>
            <select v-model="purchaseForm.supplier_id" class="spd-select" @change="handlePurchaseSupplierChange">
              <option v-for="s in availableSuppliers" :key="s.id" :value="s.id">{{ s.supplier_name }} ({{ s.supplier_code }})</option>
            </select>
          </div>
          <div class="form-item-inline">
            <label>配送人:</label>
            <input v-model="purchaseForm.delivery_person" placeholder="送货司机/代表姓名" class="spd-input" />
          </div>
          <div class="form-item-inline">
            <label>联系方式:</label>
            <input v-model="purchaseForm.delivery_phone" placeholder="配送人手机号" class="spd-input font-mono" />
          </div>

          <div class="form-item-inline" style="grid-column: span 3;">
            <label>备注说明:</label>
            <input v-model="purchaseForm.remark" placeholder="采购入库备忘，如: 浙药械采购平台当期配送批次" class="spd-input" />
          </div>
          <div class="form-item-inline">
            <label>经办人:</label>
            <input :value="userStore.currentUser.realName" disabled class="spd-input font-bold" />
          </div>
        </div>

        <!-- 单身多行耗材录入工具条 (对标图 5) -->
        <div class="bill-body-toolbar">
          <div class="title">入库耗材明细清单 (共 {{ purchaseItems.length }} 行)</div>
          <div class="btns">
            <button class="spd-btn btn-primary btn-sm" @click="openSpecSelectModal">
              <SvgIcon name="dict" :size="13" />
              <span>+ 从产品字典选品</span>
            </button>
            <button class="spd-btn btn-sm" @click="addEmptyPurchaseRow">
              <SvgIcon name="plus" :size="13" />
              <span>新增空行</span>
            </button>
            <button class="spd-btn btn-danger btn-sm" :disabled="selectedPurchaseRowIndex === -1" @click="removeSelectedPurchaseRow">
              <SvgIcon name="close" :size="13" />
              <span>删除选中行</span>
            </button>
          </div>
        </div>

        <!-- 单身多行耗材表格 (对标图 5) -->
        <div class="table-scroll-wrap">
          <table class="bill-detail-table edit-table">
            <thead>
              <tr>
                <th width="40" align="center">序号</th>
                <th width="150">代码</th>
                <th width="160">品名</th>
                <th width="120">规格</th>
                <th width="100">型号</th>
                <th width="65" align="center">单位</th>
                <th width="160">生产厂家</th>
                <th width="90" align="right">数量</th>
                <th width="90" align="right">单价</th>
                <th width="100" align="right">金额</th>
                <th width="120">批次号</th>
                <th width="120">有效期</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in purchaseItems"
                :key="idx"
                :class="{ 'row-active': selectedPurchaseRowIndex === idx }"
                @click="selectedPurchaseRowIndex = idx"
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
                    v-model.number="item.quantity"
                    type="number"
                    min="1"
                    class="table-inline-input font-mono font-bold"
                    style="text-align: right;"
                    @input="recalcPurchaseRow(item)"
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
                    @input="recalcPurchaseRow(item)"
                  />
                </td>
                <td align="right" class="font-mono font-bold">
                  ¥ {{ (item.total_amount || 0).toFixed(2) }}
                </td>
                <td>
                  <input v-model="item.batch_no" placeholder="批次号" class="table-inline-input font-mono" />
                </td>
                <td>
                  <input v-model="item.expiry_date" type="date" class="table-inline-input font-mono" />
                </td>
              </tr>

              <!-- 合计行 (对标图 5 底部合计) -->
              <tr class="bill-total-row">
                <td colspan="7" align="center" class="font-bold">合 计</td>
                <td align="right" class="font-mono font-bold">{{ purchaseTotalQty }}</td>
                <td />
                <td align="right" class="font-mono font-bold">¥ {{ purchaseTotalAmount.toFixed(2) }}</td>
                <td colspan="2" />
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="showPurchaseInboundModal = false">取消</el-button>
          <el-button type="primary" :loading="submittingPurchase" @click="handleSavePurchaseInbound">
            保存入库单
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         全院统一选品弹窗 1：从产品字典选品导入入库单 (图 3 / 图 5 规范)
         ========================================================================= -->
    <SelectProductDictDialog
      v-model="showSpecSelectModal"
      title="从全院产品字典选品导入入库单"
      @confirm="handleInboundDictConfirm"
    />

    <!-- =========================================================================
         全院统一选品弹窗 2：从产品字典增补账外漏账耗材 (图 3 / 图 5 规范，彻底移除下拉框)
         ========================================================================= -->
    <SelectProductDictDialog
      v-model="showStocktakeDictModal"
      title="从全院产品字典增补账外漏账耗材 (盘盈入库对账)"
      @confirm="handleStocktakeDictConfirm"
    />

    
    <!-- =========================================================================
         主库按需分发出库单 (医院标准单据样式，对齐采购入库单规范，反向业务流)
         ========================================================================= -->
    <el-dialog
      v-model="showOutboundVoucherModal"
      title="填写出库单 - 主库按需分发"
      width="1050px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal outbound-voucher-dialog"
    >
      <div class="hospital-bill-container">
        <!-- 标题 -->
        <div class="bill-header-row">
          <div class="bill-title-center">主 库 耗 材 按 需 分 发 出 库 单</div>
          <div class="bill-top-options">
            <el-checkbox v-model="outboundForm.auto_approve">出库单保存后自动审核下发并通知二级库</el-checkbox>
          </div>
        </div>

        <!-- 单头录入表单网格 (对齐采购入库单标准 4 列卡片规范) -->
        <div class="purchase-header-grid">
          <div class="form-item-inline">
            <label>出库单号:</label>
            <input v-model="outboundForm.order_no" disabled class="spd-input font-mono font-bold" />
          </div>
          <div class="form-item-inline">
            <label>出库日期:</label>
            <input v-model="outboundForm.outbound_date" type="date" class="spd-input font-mono" />
          </div>
          <div class="form-item-inline">
            <label>出库类别:</label>
            <input v-model="outboundForm.outbound_type" disabled class="spd-input" />
          </div>
          <div class="form-item-inline">
            <label>出库经办人:</label>
            <input :value="outboundForm.handler_name || userStore.currentUser.realName" disabled class="spd-input font-bold" />
          </div>

          <div class="form-item-inline">
            <label class="required">出库仓库:</label>
            <select v-model="outboundForm.source_warehouse_code" class="spd-select">
              <option value="WH_WEICAI">卫材库房 (WH_WEICAI)</option>
              <option value="WH_EQUIP">设备库房 (WH_EQUIP)</option>
            </select>
          </div>
          <div class="form-item-inline">
            <label class="required">接收科室:</label>
            <select v-model="outboundForm.target_dept_code" class="spd-select" @change="handleTargetDeptChange">
              <option value="WH_SEC_ORTHO">010101 内一科 (骨科二级库)</option>
              <option value="WH_SEC_CARDIO">010201 心内科 (心内科二级库)</option>
              <option value="WH_HIGH_VALUE">高值耗材专仓</option>
            </select>
          </div>
          <div class="form-item-inline">
            <label>领用负责人:</label>
            <input v-model="outboundForm.receiver_name" placeholder="科室护士长/医生" class="spd-input" />
          </div>
          <div class="form-item-inline">
            <label>下发状态:</label>
            <input :value="outboundForm.auto_approve ? '保存即审核' : '待二级审核'" disabled class="spd-input text-accent font-bold" />
          </div>

          <div class="form-item-inline" style="grid-column: span 4;">
            <label>出库说明:</label>
            <input v-model="outboundForm.remark" placeholder="出库备忘，例如: 临床病区周常耗材定额按需分发出库" class="spd-input" />
          </div>
        </div>

        <!-- 单身多行耗材录入工具条 (对标图 5 规范) -->
        <div class="bill-body-toolbar">
          <div class="title">出库耗材明细清单 (共 {{ outboundItems.length }} 行)</div>
          <div class="btns">
            <button class="spd-btn btn-primary btn-sm" @click="showOutboundDictModal = true">
              <SvgIcon name="dict" :size="13" />
              <span>+ 从全院产品字典选品</span>
            </button>
            <button
              class="spd-btn btn-danger btn-sm"
              :disabled="selectedOutboundRowIndex === null || selectedOutboundRowIndex < 0"
              @click="removeSelectedOutboundRow"
            >
              <SvgIcon name="close" :size="13" />
              <span>删除选中行</span>
            </button>
          </div>
        </div>

        <!-- 单身明细表格 (统一现代卡片编辑表格) -->
        <div class="table-scroll-wrap">
          <table class="bill-detail-table edit-table">
            <thead>
              <tr>
                <th width="45" align="center">序号</th>
                <th width="150">物料代码</th>
                <th min-width="160">品名规格</th>
                <th width="100">型号</th>
                <th width="55" align="center">单位</th>
                <th width="140">生产厂家</th>
                <th width="85" align="right">出库数</th>
                <th width="85" align="right">单价(元)</th>
                <th width="95" align="right">金额(元)</th>
                <th width="120">出库批号</th>
                <th width="120">有效期至</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in outboundItems"
                :key="idx"
                :class="{ 'is-selected-row': selectedOutboundRowIndex === idx }"
                @click="selectedOutboundRowIndex = idx"
              >
                <td align="center">{{ idx + 1 }}</td>
                <td class="font-mono text-accent font-bold">{{ item.spec_code }}</td>
                <td>
                  <div class="font-bold">{{ item.product_name }}</div>
                  <div class="text-muted font-mono" style="font-size: 11px;">{{ item.spec_name }}</div>
                </td>
                <td>{{ item.model_name || '-' }}</td>
                <td align="center">{{ item.pricing_unit || '件' }}</td>
                <td class="text-ellipsis">{{ item.manufacturer || '-' }}</td>
                <td align="right">
                  <input
                    v-model.number="item.quantity"
                    type="number"
                    min="1"
                    class="table-inline-input font-mono font-bold"
                    style="text-align: right;"
                    @input="recalcOutboundRow(item)"
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
                    @input="recalcOutboundRow(item)"
                  />
                </td>
                <td align="right" class="font-mono font-bold">
                  ¥ {{ (item.total_amount || 0).toFixed(2) }}
                </td>
                <td>
                  <input v-model="item.batch_no" placeholder="批次号" class="table-inline-input font-mono" />
                </td>
                <td>
                  <input v-model="item.expiry_date" type="date" class="table-inline-input font-mono" />
                </td>
              </tr>
              <!-- 空状态 -->
              <tr v-if="outboundItems.length === 0">
                <td colspan="11" align="center" style="padding: 24px; color: var(--text-secondary);">
                  暂无出库耗材明细，请点击上方“+ 从全院产品字典选品”导入
                </td>
              </tr>
              <!-- 合计行 -->
              <tr class="bill-total-row">
                <td colspan="6" align="center" class="font-bold">合 计</td>
                <td align="right" class="font-mono font-bold">{{ outboundTotalQty }}</td>
                <td />
                <td align="right" class="font-mono font-bold">¥ {{ outboundTotalAmount.toFixed(2) }}</td>
                <td colspan="2" />
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="showOutboundVoucherModal = false">取消</el-button>
          <el-button type="primary" :loading="submittingOutbound" @click="handleSaveOutboundVoucher">
            保存出库单 (待二次确认/自动审核)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 4: 出库选品弹窗 -->
    <SelectProductDictDialog
      v-model="showOutboundDictModal"
      title="从全院产品字典选品导入主库出库单"
      @confirm="handleOutboundDictConfirm"
    />

    <!-- 退给供应商红字单录入对话框 -->
    <el-dialog
      v-model="returnSupplierVisible"
      title="在耗材入库模块开具退给供应商红字退货单"
      width="500px"
      append-to-body
      class="fusion-dialog"
    >
      <el-form label-position="top">
        <el-form-item label="所属仓库" required>
          <el-select v-model="returnForm.warehouse_code" style="width: 100%;">
            <el-option label="卫材库 (WH_WEICAI)" value="WH_WEICAI" />
            <el-option label="设备库 (WH_EQUIP)" value="WH_EQUIP" />
          </el-select>
        </el-form-item>
        <el-form-item label="退回供应商" required>
          <el-input v-model="returnForm.target_dept_or_supplier" placeholder="例如: 普昂(杭州)医疗科技有限公司" />
        </el-form-item>
        <el-form-item label="退货数量 (系统将自动转换为负向红冲数量)" required>
          <el-input-number v-model="returnForm.quantity" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="退货原因" required>
          <el-input v-model="returnForm.remark" placeholder="例如: 外包装轻微受潮破损退供应商" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnSupplierVisible = false">取消</el-button>
        <el-button type="danger" @click="handleSubmitReturnSupplier">提交第1阶段 (待确认)</el-button>
      </template>
    </el-dialog>

    <!-- 期初数据建账填报对话框 -->
    <el-dialog
      v-model="initStockVisible"
      title="科室仓库期初数据建账填报 (第1次提交)"
      width="500px"
      append-to-body
      class="fusion-dialog"
    >
      <div class="dialog-warning-banner">
        重要提醒：期初建账单第 1 次提交后处于待确认状态；一旦在外层完成第 2 次确认提交，将永久锁定只读！
      </div>
      <el-form label-position="top">
        <el-form-item label="目标科室仓库" required>
          <el-select v-model="initForm.warehouse_code" style="width: 100%;">
            <el-option label="总务仓库 (WH_ZONGWU)" value="WH_ZONGWU" />
            <el-option label="设备库房 (WH_EQUIP)" value="WH_EQUIP" />
            <el-option label="骨科病区二级库 (WH_SEC_ORTHO)" value="WH_SEC_ORTHO" />
          </el-select>
        </el-form-item>
        <el-form-item label="期初库存数量" required>
          <el-input-number v-model="initForm.quantity" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="建账备注">
          <el-input v-model="initForm.remark" placeholder="例如: 2026科室期初资产建账" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="initStockVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitInitStock">填单提交 (进入待确认)</el-button>
      </template>
    </el-dialog>

    <!-- 两阶段确认状态机对话框组件 -->
    <TwoStepConfirmDialog
      v-model="twoStepDialogVisible"
      :order-no="selectedOrder?.order_no || ''"
      :action-type="currentActionType"
      :operator-name="userStore.currentUser.realName"
      :is-irreversible="currentIsIrreversible"
      @submit="handleTwoStepActionSubmit"
    />

    <!-- 四联单据打印组件 -->
    <PrintVoucherDialog
      v-model="printModalVisible"
      voucher-type="医疗物资出入库四联签字确认单"
      :order-data="selectedPrintOrder"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus';
import { useFormDraft } from '@/composables/useFormDraft';
import { useBarcodeScanner } from '@/composables/useBarcodeScanner';
import {
  listInboundOutboundOrders,
  createInboundOutboundOrder,
  executeOrderTwoStepAction,
  type InboundOutboundOrder
} from '@/api/orderApi';
import {
  listMainRequisitions,
  approveRequisitionAndDispatch,
  rejectRequisition,
  createPurchaseInboundOrder,
  getMainStocktakeInventory,
  submitMainStocktake,
  type PurchaseInboundItemDTO,
  type StocktakeItemDTO
} from '@/api/stockApi';
import {
  listSpecs,
  listSuppliers,
  type SpecItem,
  type SupplierProfileItem
} from '@/api/dictApi';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';
import TwoStepConfirmDialog from '@/components/TwoStepConfirmDialog.vue';
import PrintVoucherDialog from '@/components/PrintVoucherDialog.vue';
import SelectProductDictDialog from '@/components/SelectProductDictDialog.vue';
import StocktakePlanWorkbench from '@/components/StocktakePlanWorkbench.vue';
import { httpGet, httpPost } from '@/api/request';

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const activeTab = ref('requisition');

// 列表与加载状态
const allOrders = ref<InboundOutboundOrder[]>([]);
const requisitions = ref<any[]>([]);
const stocktakeItems = ref<StocktakeItemDTO[]>([]);
const allSpecs = ref<SpecItem[]>([]);
const availableSuppliers = ref<SupplierProfileItem[]>([]);

// =========================================================================
// 全院/分仓实时库存查询状态与逻辑
// =========================================================================
const realtimeWhFilter = ref('ALL');
const realtimeKeyword = ref('');
const realtimePage = ref(1);
const realtimePageSize = ref(10);
const realtimeTotal = ref(0);
const realtimeStockList = ref<any[]>([]);
const loadingRealtimeStock = ref(false);

const accessibleWarehouses = computed(() => {
  return [
    { warehouse_code: 'WH_WEICAI', warehouse_name: '卫材库房 (耗材主仓)' },
    { warehouse_code: 'WH_EQUIP', warehouse_name: '设备库房 (设备配件仓)' },
    { warehouse_code: 'WH_ZONGWU', warehouse_name: '总务仓库 (低值易耗仓)' },
    { warehouse_code: 'WH_XINXI', warehouse_name: '信息科仓 (IT硬件耗材)' },
    { warehouse_code: 'WH_SEC_ORTHO', warehouse_name: '骨科病区二级库' },
    { warehouse_code: 'WH_SEC_CARDIO', warehouse_name: '心内科病区二级库' }
  ];
});

async function fetchRealtimeStock() {
  loadingRealtimeStock.value = true;
  try {
    const res = await httpGet<any>('/main-warehouse/realtime-stock', {
      warehouse_code: realtimeWhFilter.value,
      keyword: realtimeKeyword.value,
      page: realtimePage.value,
      page_size: realtimePageSize.value
    });
    realtimeStockList.value = res?.items || [];
    realtimeTotal.value = res?.total || 0;
  } catch (err: any) {
    ElMessage.error(err.message || '获取实时库存失败');
  } finally {
    loadingRealtimeStock.value = false;
  }
}

// =========================================================================
// 主库按需分发出库单 (Voucher) 录入与保存逻辑 (对标图 1 / 图 5 凭证规范)
// =========================================================================
const showOutboundVoucherModal = ref(false);
const submittingOutbound = ref(false);
const showOutboundDictModal = ref(false);
const selectedOutboundRowIndex = ref<number | null>(null);

const outboundForm = ref({
  order_no: '',
  dispatch_order_no: '',
  outbound_date: new Date().toISOString().slice(0, 10),
  outbound_type: '按需分发出库 (移库不计费)',
  dispatch_type: '按需分发出库 (移库不计费)',
  source_warehouse_code: 'WH_WEICAI',
  target_dept_code: 'WH_SEC_ORTHO',
  target_dept_id: 3,
  target_dept_name: '010101 内一科 (骨科病区二级库)',
  dispatcher_name: '系统管理员',
  receiver_name: '李晓琳(护士长)',
  remark: '常规临床病区周转物资补货按需分发出库',
  handler_name: '系统管理员',
  auto_approve: true
});

function handleTargetDeptChange() {
  if (outboundForm.value.target_dept_code === 'WH_SEC_ORTHO') {
    outboundForm.value.target_dept_id = 3;
    outboundForm.value.target_dept_name = '010101 内一科 (骨科病区二级库)';
  } else if (outboundForm.value.target_dept_code === 'WH_SEC_CARDIO') {
    outboundForm.value.target_dept_id = 4;
    outboundForm.value.target_dept_name = '010201 心血管内科 (心内科二级库)';
  } else {
    outboundForm.value.target_dept_id = 5;
    outboundForm.value.target_dept_name = '高值耗材专仓';
  }
}

function removeSelectedOutboundRow() {
  if (selectedOutboundRowIndex.value !== null && selectedOutboundRowIndex.value >= 0) {
    outboundItems.value.splice(selectedOutboundRowIndex.value, 1);
    selectedOutboundRowIndex.value = -1;
  }
}

const outboundItems = ref<any[]>([]);

const outboundTotalQty = computed(() =>
  outboundItems.value.reduce((acc, cur) => acc + (Number(cur.quantity) || 0), 0)
);

const outboundTotalAmount = computed(() =>
  outboundItems.value.reduce((acc, cur) => acc + (Number(cur.total_amount) || 0), 0)
);

function openCreateOutboundVoucherModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  outboundForm.value.order_no = `CK936${ts}`;
outboundForm.value.handler_name = userStore.currentUser.realName || '系统管理员';
  outboundForm.value.dispatcher_name = userStore.currentUser.realName || '系统管理员';
  outboundItems.value = [];
  showOutboundVoucherModal.value = true;
}

function recalcOutboundRow(row: any) {
  row.total_amount = (Number(row.quantity) || 0) * (Number(row.unit_price) || 0);
}

function handleOutboundDictConfirm(items: any[]) {
  for (const s of items) {
    const code = s.product_code || s.spec_code;
    const exists = outboundItems.value.find(i => (i.spec_code || i.product_code) === code);
    if (!exists) {
      outboundItems.value.push({
        spec_code: code,
        product_code: code,
        product_name: s.product_name,
        spec_name: s.spec_name || '',
        model_name: s.model_name || '',
        unit_name: s.pricing_unit || '支',
        manufacturer: s.manufacturer || '',
        batch_no: `B${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
        quantity: 10,
        unit_price: Number(s.unit_price) || 8.5,
        total_amount: (Number(s.unit_price) || 8.5) * 10
      });
    }
  }
  showOutboundDictModal.value = false;
  ElMessage.success(`已导入 ${items.length} 种耗材到出库明细`);
}

async function handleSaveOutboundVoucher() {
  if (outboundItems.value.length === 0) {
    ElMessage.warning('出库明细不能为空，请从产品字典添加耗材');
    return;
  }

  // 医疗顾问三甲内控强风控：FEFO 效期检查，对剩余有效天数 <= 30 天实施硬性阻断
  for (const it of outboundItems.value) {
    if (it.expiry_date) {
      const expTime = new Date(it.expiry_date).getTime();
      const nowTime = new Date().getTime();
      const diffDays = Math.ceil((expTime - nowTime) / (1000 * 3600 * 24));
      if (diffDays <= 30) {
        ElMessageBox.alert(
          `物料 [${it.product_name}] (批号:${it.batch_no}) 有效期至 ${it.expiry_date}，距离失效仅剩 ${diffDays} 天 (<= 30天强控阈值)，已触发三甲医疗物资 FEFO 强控熔断机制！\n\n系统严禁将临期或过期物资分发至临床科室，请发起退货供应商或报废审批流程。`,
          'FEFO 临期强控熔断拦截',
          { type: 'error', confirmButtonText: '已知晓并阻断出库' }
        );
        return;
      }
    }
  }

  submittingOutbound.value = true;
  try {
    const res = await httpPost<any>('/main-warehouse/outbound-voucher', {
      dispatch_order_no: outboundForm.value.order_no,
      source_warehouse_code: outboundForm.value.source_warehouse_code,
      target_dept_id: outboundForm.value.target_dept_id,
      target_dept_name: outboundForm.value.target_dept_name,
      dispatch_type: outboundForm.value.dispatch_type,
      dispatcher_name: outboundForm.value.dispatcher_name,
      receiver_name: outboundForm.value.receiver_name,
      auto_approve: outboundForm.value.auto_approve,
      remark: outboundForm.value.remark,
      items: outboundItems.value
    });
    ElMessage.success(`主库出库单 [${res.order_no || outboundForm.value.dispatch_order_no}] 保存成功！共出库 ${res.total_items} 种物资，总额 ¥${res.total_amount?.toFixed(2) || '0.00'}`);
    showOutboundVoucherModal.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '保存出库单失败');
  } finally {
    submittingOutbound.value = false;
  }
}

const loadingOrders = ref(false);
const loadingReq = ref(false);
const loadingStocktake = ref(false);
const submittingStocktake = ref(false);
const submittingPurchase = ref(false);

// 选中行状态 (用于高对比度亮色高亮)
const selectedRequisition = ref<any | null>(null);
const selectedOrder = ref<InboundOutboundOrder | null>(null);

// 弹窗状态
const showReqDetailModal = ref(false);
const activeReqDetail = ref<any | null>(null);

const showPurchaseInboundModal = ref(false);
const purchaseFormAutoPrint = ref(false);
const purchaseFormOrderNo = ref('');
const purchaseFormDate = ref(new Date().toISOString().slice(0, 10));

const purchaseForm = ref({
  delivery_order_no: '',
  inbound_type: 'PURCHASE_INBOUND',
  invoice_no: '',
  invoice_date: new Date().toISOString().slice(0, 10),
  warehouse_code: 'WH_WEICAI',
  supplier_id: 1,
  supplier_name: '普昂(杭州)医疗科技有限公司',
  delivery_person: '张师傅',
  delivery_phone: '13812345678',
  purchaser_name: '王建国',
  auto_approve: true,
  remark: '药械集采配送验收'
});

const {
  hasDraft: hasInboundDraft,
  draftTime: inboundDraftTime,
  restoreDraft: restoreInboundDraft,
  clearDraft: clearInboundDraft
} = useFormDraft({
  formKey: 'main_purchase_inbound',
  formData: purchaseForm
});

useBarcodeScanner({
  onScan: (res) => {
    ElNotification({
      title: '扫码枪识别成功',
      message: `已自动匹配物料/UDI条码: ${res.rawCode} ${res.piBatch ? '(批号:' + res.piBatch + ')' : ''}`,
      type: 'success',
      duration: 3500
    });
  }
});

const purchaseItems = ref<PurchaseInboundItemDTO[]>([]);
const selectedPurchaseRowIndex = ref<number>(-1);

// 选品弹窗状态
const showSpecSelectModal = ref(false);
const dictSearchKeyword = ref('');
const selectedDictSpecs = ref<SpecItem[]>([]);

// 漏账增补弹窗状态
const showSupplementModal = ref(false);
const supplementSelectedSpecId = ref<number>(1);
const supplementForm = ref({
  actual_qty: 10,
  batch_no: 'B20261103',
  reason: '盘点现场清点到账外备用耗材，按字典基准价增补入库'
});

// 退货与期初弹窗
const returnSupplierVisible = ref(false);
const returnForm = ref({
  warehouse_code: 'WH_WEICAI',
  target_dept_or_supplier: '普昂(杭州)医疗科技有限公司',
  quantity: 10,
  remark: '外包装破损退给供应商'
});

const initStockVisible = ref(false);
const initForm = ref({
  warehouse_code: 'WH_ZONGWU',
  quantity: 200,
  remark: '总务仓库期初数据建账'
});

// 两阶段确认与打印
const twoStepDialogVisible = ref(false);
const currentActionType = ref<'SECOND_CONFIRM' | 'CANCEL_SUBMIT' | 'EDIT_REMARK'>('SECOND_CONFIRM');
const currentIsIrreversible = ref(false);
const printModalVisible = ref(false);
const selectedPrintOrder = ref<Record<string, any>>({});

// 计算属性
const reqCurrentPage = ref(1);
const reqPageSize = ref(10);
const paginatedRequisitions = computed(() => {
  const start = (reqCurrentPage.value - 1) * reqPageSize.value;
  return requisitions.value.slice(start, start + reqPageSize.value);
});

const inboundCurrentPage = ref(1);
const inboundPageSize = ref(10);
const paginatedInboundOrders = computed(() => {
  const start = (inboundCurrentPage.value - 1) * inboundPageSize.value;
  return inboundOrders.value.slice(start, start + inboundPageSize.value);
});

const outboundCurrentPage = ref(1);
const outboundPageSize = ref(10);
const paginatedOutboundOrders = computed(() => {
  const start = (outboundCurrentPage.value - 1) * outboundPageSize.value;
  return outboundOrders.value.slice(start, start + outboundPageSize.value);
});

const inboundOrders = computed(() =>
  allOrders.value.filter((o) => o.order_type === 'GEN_INBOUND' || o.order_type === 'PURCHASE_INBOUND' || o.order_type === 'RETURN_TO_SUPPLIER')
);

const outboundOrders = computed(() =>
  allOrders.value.filter((o) => o.order_type === 'GEN_MANUAL_OUT' || o.order_type === 'REQ_AUTO_OUT')
);

const initStockOrders = computed(() =>
  allOrders.value.filter((o) => o.order_type === 'INIT_STOCK')
);

const totalStockQty = computed(() => 1870);

const pendingRequisitionCount = computed(() =>
  requisitions.value.filter((r) => r.req_status === 'PENDING_APPROVAL').length
);

const todayDispatchAmount = computed(() => 18400.0);

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

const purchaseTotalQty = computed(() =>
  purchaseItems.value.reduce((acc, cur) => acc + (Number(cur.quantity) || 0), 0)
);

const purchaseTotalAmount = computed(() =>
  purchaseItems.value.reduce((acc, cur) => acc + (Number(cur.total_amount) || 0), 0)
);

// 表格选中行高亮样式函数
function requisitionTableRowClassName({ row }: { row: any }) {
  if (selectedRequisition.value && selectedRequisition.value.id === row.id) {
    return 'is-row-selected-highlight';
  }
  return '';
}

function orderTableRowClassName({ row }: { row: InboundOutboundOrder }) {
  if (selectedOrder.value && selectedOrder.value.id === row.id) {
    return 'is-row-selected-highlight';
  }
  return '';
}

// 单击与双击处理
function handleRequisitionRowClick(row: any | null) {
  selectedRequisition.value = row;
}

function handleRequisitionRowDblClick(row: any) {
  selectedRequisition.value = row;
  openRequisitionDetail(row);
}

function handleOrderRowClick(row: InboundOutboundOrder | null) {
  selectedOrder.value = row;
}

function handleOrderRowDblClick(row: InboundOutboundOrder) {
  selectedOrder.value = row;
  openPrint(row);
}

/**
 * 获取主库请领受理待办列表
 * @route GET /api/v1/main-warehouse/requisitions
 */
async function fetchRequisitions() {
  loadingReq.value = true;
  try {
    const list = await listMainRequisitions({
      warehouse_code: userStore.currentWarehouseCode || undefined
    });
    requisitions.value = (list || []).map((r: any) => ({
      id: r.id,
      req_order_no: r.req_order_no,
      created_at: r.created_at,
      apply_dept_name: r.apply_dept_name,
      apply_warehouse_code: r.apply_warehouse || r.apply_warehouse_code || 'WH_SEC_ORTHO',
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
    ElMessage.error(err.message || '获取主库请领单失败');
  } finally {
    loadingReq.value = false;
  }
}

/**
 * 获取出入库台账
 */
async function fetchOrders() {
  loadingOrders.value = true;
  try {
    const list = await listInboundOutboundOrders();
    allOrders.value = list || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取出入库记录失败');
  } finally {
    loadingOrders.value = false;
  }
}

/**
 * 获取主库独立盘点底表
 */
async function fetchMainStocktake() {
  loadingStocktake.value = true;
  try {
    const list = await getMainStocktakeInventory();
    stocktakeItems.value = list || [];
    ElMessage.success(`已加载主库 ${stocktakeItems.value.length} 项在库盘点底表`);
  } catch (err: any) {
    ElMessage.error(err.message || '获取盘点底表失败');
  } finally {
    loadingStocktake.value = false;
  }
}

/**
 * 盘点实盘数变动重新计算盈亏
 */
function calculateStocktakeDiff(row: StocktakeItemDTO) {
  row.diff_qty = Number(row.actual_qty) - Number(row.book_qty);
}

/**
 * 提交主库盘点平账
 */
async function handleSubmitMainStocktake() {
  if (stocktakeItems.value.length === 0) {
    ElMessage.warning('请先加载主库盘点底表');
    return;
  }
  submittingStocktake.value = true;
  try {
    await submitMainStocktake({
      warehouse_code: userStore.currentWarehouseCode || 'WH_WEICAI',
      operator_name: userStore.currentUser.realName,
      reason_note: '主库例行实物盘点与对账平账',
      items: stocktakeItems.value
    });
    ElMessage.success('主库盘点已成功提交，系统已自动按盈亏结果生成对账入出库流水！');
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '提交盘点失败');
  } finally {
    submittingStocktake.value = false;
  }
}

/**
 * 打开申请单明细 (图 4)
 */
function openRequisitionDetail(row: any) {
  activeReqDetail.value = row;
  showReqDetailModal.value = true;
}

/**
 * 批准当前选中的申请单并出库
 */
async function handleApproveSelectedRequisition() {
  if (!selectedRequisition.value) return;
  try {
    const res = await approveRequisitionAndDispatch(selectedRequisition.value.id);
    ElMessage.success(`请领已批准通过！已自动生成主库出库单据 [${res.outbound_order_no}]`);
    selectedRequisition.value.req_status = 'APPROVED_DISPATCHED';
    showReqDetailModal.value = false;
    await fetchRequisitions();
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '审批出库失败');
  }
}

/**
 * 退回当前选中的申请单
 */
async function handleRejectSelectedRequisition() {
  if (!selectedRequisition.value) return;
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入退回科室原因说明:', '退回申请单', {
      confirmButtonText: '确定退回',
      cancelButtonText: '取消',
      inputPlaceholder: '例如: 主库当前批次正执行抽检，请稍后再试'
    });
    if (!reason) return;
    await rejectRequisition(selectedRequisition.value.id, reason);
    ElMessage.success('申请单已退回至临床科室');
    selectedRequisition.value.req_status = 'REJECTED';
    showReqDetailModal.value = false;
    await fetchRequisitions();
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '退回操作失败');
    }
  }
}

/**
 * 打开采购入库单录入弹窗 (图 5)
 */
function openPurchaseInboundModal() {
  const now = new Date();
  const dateStr = now.toISOString().replace(/[-:T.]/g, '').slice(0, 8);
  purchaseFormOrderNo.value = `IN${dateStr}${Math.floor(1000 + Math.random() * 9000)}`;
  purchaseFormDate.value = now.toISOString().slice(0, 10);
  purchaseForm.value.invoice_no = `FP${dateStr}${Math.floor(100 + Math.random() * 900)}`;
  purchaseForm.value.delivery_order_no = `PS${dateStr}${Math.floor(100 + Math.random() * 900)}`;

  // 默认填充两行示范物资
  purchaseItems.value = [
    {
      spec_code: '936010900135',
      product_name: '医用敷料贴 (透明敷料)',
      spec_name: '10cm*11.5cm',
      model_name: '9546HP',
      unit_name: '片',
      manufacturer: '普昂(杭州)医疗科技有限公司',
      unit_price: 8.7654,
      quantity: 200,
      total_amount: 1753.08,
      batch_no: `B${dateStr}01`,
      expiry_date: '2029-10-31'
    }
  ];
  selectedPurchaseRowIndex.value = 0;
  showPurchaseInboundModal.value = true;
}

function handlePurchaseSupplierChange() {
  const sup = availableSuppliers.value.find((s) => s.id === purchaseForm.value.supplier_id);
  if (sup) {
    purchaseForm.value.supplier_name = sup.supplier_name;
  }
}

function addEmptyPurchaseRow() {
  const dateStr = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 8);
  purchaseItems.value.push({
    spec_code: '',
    product_name: '',
    spec_name: '',
    model_name: '',
    unit_name: '件',
    manufacturer: '',
    unit_price: 10.0,
    quantity: 50,
    total_amount: 500.0,
    batch_no: `B${dateStr}02`,
    expiry_date: '2029-12-31'
  });
  selectedPurchaseRowIndex.value = purchaseItems.value.length - 1;
}

function removeSelectedPurchaseRow() {
  if (selectedPurchaseRowIndex.value >= 0 && selectedPurchaseRowIndex.value < purchaseItems.value.length) {
    purchaseItems.value.splice(selectedPurchaseRowIndex.value, 1);
    selectedPurchaseRowIndex.value = Math.max(0, purchaseItems.value.length - 1);
  }
}

function recalcPurchaseRow(item: PurchaseInboundItemDTO) {
  item.total_amount = Number(((item.quantity || 0) * (item.unit_price || 0)).toFixed(2));
}

// 选品弹窗
function openSpecSelectModal() {
  selectedDictSpecs.value = [];
  dictSearchKeyword.value = '';
  showSpecSelectModal.value = true;
}

function handleDictSpecSelection(rows: SpecItem[]) {
  selectedDictSpecs.value = rows;
}

function confirmSelectDictSpecs() {
  const dateStr = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 8);
  selectedDictSpecs.value.forEach((spec) => {
    purchaseItems.value.push({
      spec_code: spec.spec_code,
      product_name: spec.product_name,
      spec_name: spec.spec_name,
      model_name: spec.model_name,
      unit_name: spec.pricing_unit || '件',
      manufacturer: spec.manufacturer,
      unit_price: Number(spec.unit_price) || 10.0,
      quantity: 100,
      total_amount: Number((100 * (Number(spec.unit_price) || 10.0)).toFixed(2)),
      batch_no: `B${dateStr}${Math.floor(10 + Math.random() * 90)}`,
      expiry_date: '2029-12-31'
    });
  });
  showSpecSelectModal.value = false;
  ElMessage.success(`已导入 ${selectedDictSpecs.value.length} 项耗材到入库清单`);
}

/**
 * 保存采购入库单
 */
async function handleSavePurchaseInbound() {
  if (!purchaseForm.value.invoice_no) {
    ElMessage.warning('发票号为必填项');
    return;
  }
  if (purchaseItems.value.length === 0) {
    ElMessage.warning('入库明细不能为空，请至少添加一行耗材');
    return;
  }
  submittingPurchase.value = true;
  try {
    const res = await createPurchaseInboundOrder({
      delivery_order_no: purchaseForm.value.delivery_order_no,
      inbound_type: purchaseForm.value.inbound_type,
      invoice_no: purchaseForm.value.invoice_no,
      invoice_date: purchaseForm.value.invoice_date,
      warehouse_code: purchaseForm.value.warehouse_code,
      supplier_id: purchaseForm.value.supplier_id,
      supplier_name: purchaseForm.value.supplier_name,
      delivery_person: purchaseForm.value.delivery_person,
      delivery_phone: purchaseForm.value.delivery_phone,
      purchaser_name: purchaseForm.value.purchaser_name,
      handler_name: userStore.currentUser.realName,
      auto_approve: purchaseForm.value.auto_approve,
      remark: purchaseForm.value.remark,
      items: purchaseItems.value
    });
    ElMessage.success(`采购入库单 [${res.order_no}] 保存成功！共录入 ${res.total_items} 种物资，总额 ¥${res.total_amount.toFixed(2)}`);
    clearInboundDraft();
    showPurchaseInboundModal.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '保存入库单失败');
  } finally {
    submittingPurchase.value = false;
  }
}

const showStocktakeDictModal = ref(false);

// 盘点漏账增补 (采用全院统一图 3 表格选品规范)
function openAddSupplementDialog() {
  showStocktakeDictModal.value = true;
}

function handleStocktakeDictConfirm(items: any[]) {
  for (const s of items) {
    stocktakeItems.value.push({
      spec_code: s.spec_code,
      product_name: s.product_name,
      spec_name: s.spec_name || '常规规格',
      model_name: s.model_name || '标配',
      unit_name: s.pricing_unit || '支',
      manufacturer: s.manufacturer || '准入品牌药械',
      batch_no: `B${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
      book_qty: 0,
      actual_qty: 1,
      diff_qty: 1,
      unit_price: Number(s.unit_price) || 10.0,
      is_new_supplement: 1
    });
  }
  ElMessage.success(`已增补导入 ${items.length} 项漏账耗材进入盘点底表 (盘盈对账)！`);
}

function handleInboundDictConfirm(items: any[]) {
  for (const s of items) {
    purchaseItems.value.push({
      spec_code: s.spec_code,
      product_name: s.product_name,
      spec_name: s.spec_name || '',
      model_name: s.model_name || '',
      unit_name: s.pricing_unit || '支',
      manufacturer: s.manufacturer || '',
      unit_price: Number(s.unit_price) || 10.0,
      quantity: 100,
      total_amount: (Number(s.unit_price) || 10.0) * 100,
      batch_no: `B${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
      sterilization_batch: `ST${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
      produce_date: new Date().toISOString().slice(0, 10),
      expiry_date: '2029-12-31',
      register_card_no: '国械注准20260088'
    });
  }
  ElMessage.success(`已成功导入 ${items.length} 种耗材明细`);
}

// 退回供应商
function openReturnSupplierModal() {
  returnSupplierVisible.value = true;
}

async function handleSubmitReturnSupplier() {
  try {
    await createInboundOutboundOrder({
      order_type: 'RETURN_TO_SUPPLIER',
      warehouse_code: returnForm.value.warehouse_code,
      dept_code: 'CONSUMABLE_DEPT',
      target_dept_or_supplier: returnForm.value.target_dept_or_supplier,
      product_id: 1,
      quantity: returnForm.value.quantity,
      created_by: userStore.currentUser.realName,
      remark: returnForm.value.remark
    });
    ElMessage.success('退给供应商红字单第1次提交成功，进入待二次确认状态');
    returnSupplierVisible.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '退货单开具失败');
  }
}

// 期初建账
function openInitStockModal() {
  initStockVisible.value = true;
}

async function handleSubmitInitStock() {
  try {
    await createInboundOutboundOrder({
      order_type: 'INIT_STOCK',
      warehouse_code: initForm.value.warehouse_code,
      dept_code: 'CONSUMABLE_DEPT',
      target_dept_or_supplier: '科室期初建账',
      product_id: 1,
      quantity: initForm.value.quantity,
      created_by: userStore.currentUser.realName,
      remark: initForm.value.remark
    });
    ElMessage.success('期初建账填单成功，已进入待二次确认状态');
    initStockVisible.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '期初填报失败');
  }
}

// 两阶段确认
function openTwoStep(row: InboundOutboundOrder, action: 'SECOND_CONFIRM' | 'CANCEL_SUBMIT', isIrreversible = false) {
  selectedOrder.value = row;
  currentActionType.value = action;
  currentIsIrreversible.value = isIrreversible || row.order_type === 'INIT_STOCK' || row.is_irreversible_locked === 1;
  twoStepDialogVisible.value = true;
}

async function handleTwoStepActionSubmit(payload: { action: string; orderNo: string; remark?: string }) {
  try {
    await executeOrderTwoStepAction({
      order_no: payload.orderNo,
      action: payload.action as any,
      operator_name: userStore.currentUser.realName,
      new_remark: payload.remark
    });
    ElMessage.success(`单据[${payload.orderNo}]执行动作[${payload.action}]成功`);
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '状态机跃迁被拦截');
  }
}

function openPrint(row: InboundOutboundOrder) {
  selectedPrintOrder.value = { ...row };
  printModalVisible.value = true;
}

/**
 * 标签页切换响应
 * @param tabName 目标标签页标识
 * @returns void
 * @route 切换视图并同步更新浏览器 query.tab
 * @throws 无异常
 */
function handleTabChange(tabName: any) {
  router.replace({ query: { ...route.query, tab: tabName } });
  if (tabName === 'requisition') fetchRequisitions();
  else if (tabName === 'stocktake') fetchMainStocktake();
  else if (tabName === 'inventory') fetchRealtimeStock();
  else fetchOrders();
}

// 监听路由 Query 切换活动 Tab 并即时拉取对应数据源，彻底根治静默 No Data
watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab && typeof newTab === 'string') {
      const target = (newTab === 'dispatch') ? 'outbound' : newTab;
      activeTab.value = target;
      if (target === 'inventory') fetchRealtimeStock();
      else if (target === 'requisition') fetchRequisitions();
      else if (target === 'stocktake') fetchMainStocktake();
      else fetchOrders();
    }
  }
);

onMounted(async () => {
  const currentTab = (route.query.tab as string) || 'requisition';
  const target = (currentTab === 'dispatch') ? 'outbound' : currentTab;
  activeTab.value = target;
  if (target === 'inventory') {
    fetchRealtimeStock();
  } else if (target === 'requisition') {
    fetchRequisitions();
  } else if (target === 'stocktake') {
    fetchMainStocktake();
  } else {
    fetchOrders();
  }

  try {
    const [spRes, supRes] = await Promise.all([listSpecs(), listSuppliers()]);
    allSpecs.value = spRes || [];
    availableSuppliers.value = supRes || [];
  } catch {
    // 静默降级
  }
});
</script>

<style scoped>
.general-material-view {
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

.text-warn {
  color: var(--color-warning) !important;
}

.text-danger {
  color: var(--color-danger) !important;
}

.text-success {
  color: var(--color-success) !important;
}

.text-accent {
  color: var(--accent-primary) !important;
}

.text-muted {
  color: var(--text-muted) !important;
}

/* 毛玻璃容器 */
.glass-panel {
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
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
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.chip-info {
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
  border: 1px solid rgba(56, 189, 248, 0.25);
}

/* 点击选中行亮色突出 (满足用户“选择单据的时候一点都不明显要变成亮色突出”) */
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

/* 医院标准单据容器与印章 (图 4、图 5) */
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

.bill-top-options {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 审核印章 (图 4 右上角红章) */
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

/* 元数据网格 */
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

/* 采购入库与按需分发出库单单头网格 (统一现代单据规范) */
.purchase-header-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px 14px;
  background: rgba(255, 255, 255, 0.02);
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-card);
  box-sizing: border-box;
  width: 100%;
}

.form-item-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  box-sizing: border-box;
}

.form-item-inline label {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  width: 66px;
  flex-shrink: 0;
  text-align: right;
}

.form-item-inline label.required::before {
  content: '* ';
  color: var(--color-danger);
}

.spd-input, .spd-select {
  flex: 1;
  min-width: 0;
  box-sizing: border-box;
  width: 100%;
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

/* 单身明细表 */
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

.spd-btn.btn-danger {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.spd-btn.btn-sm {
  padding: 3px 8px;
  font-size: 11.5px;
}
</style>
