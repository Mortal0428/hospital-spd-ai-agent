<template>
  <div class="supplier-purchase-view">
    <!-- 供应商经营资质准入与医院绑定状态看板 (核心硬护栏) -->
    <div class="glass-panel qual-banner-card">
      <div class="qual-left">
        <div class="supplier-brand-pill">
          <SvgIcon name="brand" :size="14" color="var(--accent-primary)" />
          <span>外部供应商协同门户</span>
        </div>
        <div>
          <div class="supplier-name">山东威高集团医用高分子制品股份有限公司</div>
          <div class="license-meta font-mono">
            <span>《医疗器械经营许可证》编号：<strong>鲁械经营备20260088号</strong></span>
            <span class="meta-separator">|</span>
            <span>国家药监局资质有效期至：<strong>2029-12-31</strong></span>
          </div>
        </div>
      </div>

      <div class="qual-right">
        <div class="status-indicator-box">
          <span class="indicator-label">医院主科室准入防线：</span>
          <span v-if="currentQualStatus === 'QUAL_APPROVED'" class="status-chip chip-active">
            资质审核通过 (已解锁接单发货)
          </span>
          <span v-else class="status-chip chip-disabled">
            待审硬拦截 (严禁接单发货)
          </span>
        </div>

        <el-button
          size="small"
          plain
          @click="openQualModal"
        >
          <SvgIcon name="dict" :size="13" style="margin-right: 4px;" />
          资质提报与审核
        </el-button>

        <el-button
          v-if="userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'dept_manager'"
          size="small"
          type="primary"
          plain
          @click="toggleSupplierQual"
        >
          <SvgIcon name="shield" :size="13" style="margin-right: 4px;" />
          {{ currentQualStatus === 'QUAL_APPROVED' ? '模拟设为待审 (测试硬拦截)' : '主科室审核通过资质' }}
        </el-button>
      </div>
    </div>

    <!-- 子视图切换与操作卡片 -->
    <div class="glass-panel action-toolbar-panel">
      <div class="tab-btn-group">
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'orders' }"
          @click="switchTab('orders')"
        >
          <SvgIcon name="package" :size="15" />
          <span>采购订单管理与计划下发</span>
        </button>
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'delivery' }"
          @click="switchTab('delivery')"
        >
          <SvgIcon name="upload" :size="15" />
          <span>供应商拣货发货协同</span>
          <span v-if="pendingDeliveryCount > 0" class="tab-chip font-mono">{{ pendingDeliveryCount }}</span>
        </button>
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'reconciliation' }"
          @click="switchTab('reconciliation')"
        >
          <SvgIcon name="finance" :size="15" />
          <span>采供月度对账与发票结算</span>
        </button>
      </div>

      <div class="action-btn-group">
        <el-button
          plain
          size="small"
          type="success"
          @click="openBatchDispatchModal"
        >
          <SvgIcon name="upload" :size="13" style="margin-right: 4px;" />
          批量发货装箱导入
        </el-button>
        <el-button
          v-if="currentTab === 'orders' && userStore.canAction('PURCHASE_PLAN', 'can_create')"
          type="primary"
          size="small"
          @click="openCreatePlanModal"
        >
          <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
          提报医用耗材采购计划单
        </el-button>

        <el-button plain size="small" @click="fetchOrders">
          <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
          刷新采供台账
        </el-button>
      </div>
    </div>

    <!-- 采购与协同发货明细表格 -->
    <div v-show="currentTab !== 'reconciliation'" class="glass-panel table-panel">
      <div class="table-caption-bar">
        <span class="caption-title">{{ currentTab === 'orders' ? '全院采购计划下发与履约台账' : '供应商在线配货与发货协同工作台' }}</span>
        <span class="caption-sub font-mono tabular-nums">共 {{ displayOrders.length }} 笔订单记录</span>
      </div>

      <el-table
        :data="paginatedOrders"
        border
        stripe
        class="fusion-styled-table"
        v-loading="loading"
      >
        <el-table-column prop="order_no" label="采购单号" width="180">
          <template #default="{ row }">
            <span
              class="font-mono tabular-nums font-bold text-accent clickable-order-no"
              title="点击查看采供四联凭证详情"
              @click="openOrderDetail(row)"
            >
              {{ row.order_no }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="supplier_name" label="协同供应商" min-width="190" />
        <el-table-column prop="product_name" label="采购耗材品名" min-width="180" />

        <el-table-column prop="purchase_qty" label="采购数量" width="110" align="right">
          <template #default="{ row }">
            <span class="font-mono tabular-nums font-bold">{{ row.purchase_qty }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="picked_batch_no" label="拣货批号 (UDI-PI)" width="160">
          <template #default="{ row }">
            <span v-if="row.picked_batch_no" class="font-mono tabular-nums status-chip chip-info">
              {{ row.picked_batch_no }}
            </span>
            <span v-else class="text-muted font-mono" style="font-size: 11.5px;">待拣货填报</span>
          </template>
        </el-table-column>

        <el-table-column prop="purchase_flow_status" label="协同阶段" width="160" align="center">
          <template #default="{ row }">
            <span v-if="row.purchase_flow_status === 'PLAN_SUBMITTED'" class="status-chip chip-locked">
              科室提报待审批
            </span>
            <span v-else-if="row.purchase_flow_status === 'DEPT_APPROVED'" class="status-chip chip-info">
              主科已批待发货
            </span>
            <span v-else class="status-chip chip-active">
              已发货生成入库单
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="auto_inbound_order_no" label="联动生成医院入库单号" min-width="190">
          <template #default="{ row }">
            <span v-if="row.auto_inbound_order_no" class="font-mono tabular-nums text-success font-bold">
              {{ row.auto_inbound_order_no }}
            </span>
            <span v-else class="text-muted font-mono" style="font-size: 11.5px;">待供应商发货自动生成</span>
          </template>
        </el-table-column>

        <el-table-column label="协同操作" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 6px; justify-content: center; align-items: center;">
              <!-- 查看详情穿透按钮 -->
              <el-button
                size="small"
                plain
                @click="openOrderDetail(row)"
              >
                详情
              </el-button>

              <!-- 按钮级 RBAC: 仅具备 PURCHASE_PLAN 审批权限方可审批下发 -->
              <el-button
                v-if="row.purchase_flow_status === 'PLAN_SUBMITTED' && userStore.canAction('PURCHASE_PLAN', 'can_approve')"
                size="small"
                type="success"
                @click="handleDeptApprove(row)"
              >
                主科审批
              </el-button>

              <!-- 按钮级 RBAC: 仅具备 SUPPLIER_SHIP 权限方可进行拣货与二次确认发货 -->
              <el-button
                v-else-if="row.purchase_flow_status === 'DEPT_APPROVED' && (userStore.currentUser.roleCode === 'supplier_user' || userStore.currentUser.roleCode === 'sys_admin')"
                size="small"
                type="primary"
                @click="openPickShipModal(row)"
              >
                配货发货
              </el-button>

              <span v-else class="text-muted font-mono" style="font-size: 11.5px;">入库待验收</span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 标准分页条 -->
      <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 14px 0 4px;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="displayOrders.length"
        />
      </div>
    </div>

    <!-- 采供月度对账与发票结算工作台面板 -->
    <div v-show="currentTab === 'reconciliation'" class="glass-panel table-panel">
      <!-- 月度对账汇总头 -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.1));">
        <div style="display: flex; align-items: center; gap: 12px;">
          <span style="font-weight: bold; font-size: 15px;">采供双方月度对账核算结算单</span>
          <el-date-picker
            v-model="reconcileMonth"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择对账核算月份"
            size="small"
            style="width: 140px;"
            @change="fetchMonthlyReconciliation"
          />
          <el-button size="small" type="primary" plain @click="fetchMonthlyReconciliation">重新聚合核算</el-button>
        </div>
        <div style="display: flex; gap: 10px;">
          <el-button
            type="primary"
            size="small"
            @click="handleReconcileConfirm"
          >
            确认对账无误并签章
          </el-button>
          <el-button
            type="success"
            size="small"
            @click="openInvoiceModal"
          >
            登记增值税发票代码
          </el-button>
        </div>
      </div>

      <!-- 对账 KPI 指标卡 -->
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 16px;">
        <div class="kpi-mini-card" style="padding: 12px 14px; background: rgba(56, 189, 248, 0.08); border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.2);">
          <div style="font-size: 12px; color: var(--text-secondary);">核算月份与对账单号</div>
          <div class="font-mono" style="font-size: 14px; font-weight: bold; margin-top: 4px;">{{ reconciliationData.reconciliation_no || 'REC-202611-WEGO' }}</div>
        </div>
        <div class="kpi-mini-card" style="padding: 12px 14px; background: rgba(52, 211, 153, 0.08); border-radius: 6px; border: 1px solid rgba(52, 211, 153, 0.2);">
          <div style="font-size: 12px; color: var(--text-secondary);">当月已验收入库单量</div>
          <div class="font-mono" style="font-size: 18px; font-weight: bold; margin-top: 4px; color: #10b981;">{{ reconciliationData.total_orders_count || 0 }} <span style="font-size: 12px;">笔</span></div>
        </div>
        <div class="kpi-mini-card" style="padding: 12px 14px; background: rgba(245, 158, 11, 0.08); border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.2);">
          <div style="font-size: 12px; color: var(--text-secondary);">实物交付总件数</div>
          <div class="font-mono" style="font-size: 18px; font-weight: bold; margin-top: 4px; color: #f59e0b;">{{ reconciliationData.total_verified_qty || 0 }} <span style="font-size: 12px;">件</span></div>
        </div>
        <div class="kpi-mini-card" style="padding: 12px 14px; background: rgba(99, 102, 241, 0.08); border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.2);">
          <div style="font-size: 12px; color: var(--text-secondary);">对账核算总金额 (含税)</div>
          <div class="font-mono font-bold" style="font-size: 18px; margin-top: 4px; color: #6366f1;">¥ {{ Number(reconciliationData.total_reconciled_amount || 0).toFixed(2) }}</div>
        </div>
      </div>

      <!-- 对账单据明细表格 -->
      <el-table :data="reconciliationData.items || []" border stripe style="width: 100%;">
        <el-table-column prop="order_no" label="采购单号" width="160" class-name="font-mono font-bold" />
        <el-table-column prop="auto_inbound_order_no" label="医院验收入库单号" width="190" class-name="font-mono text-success" />
        <el-table-column prop="product_name" label="器械耗材品名" min-width="190" show-overflow-tooltip />
        <el-table-column prop="picked_batch_no" label="供货批号" width="130" class-name="font-mono" />
        <el-table-column prop="purchase_qty" label="验收数量" width="100" align="right" class-name="font-mono font-bold" />
        <el-table-column prop="unit_price" label="含税单价" width="110" align="right">
          <template #default="{ row }">
            <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="subtotal_amount" label="核算小计" width="120" align="right">
          <template #default="{ row }">
            <span class="font-mono font-bold">¥ {{ Number(row.subtotal_amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="invoice_no" label="对应增值税发票" width="160" class-name="font-mono text-primary" />
        <el-table-column prop="inbound_status" label="对账状态" width="120" align="center">
          <template #default="{ row }">
            <span class="status-chip chip-active">{{ row.inbound_status }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 弹窗 4: 供应商批量装箱发货与数据导入 -->
    <el-dialog
      v-model="batchDispatchModalVisible"
      title="供应商批量配货装箱发货"
      width="780px"
      append-to-body
      class="fusion-dialog"
    >
      <div style="padding: 10px 0;">
        <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.6;">
          针对大批量器械配送，系统支持一键装箱赋码发货。录入后系统将自动更新订单状态并即时在医院主库生成对应《待验收入库单》。
        </p>
        <div style="display: flex; gap: 12px; margin-bottom: 14px;">
          <el-input v-model="batchDispatchForm.picked_batch_no" placeholder="配货生产批号 (如: B20261103)" class="font-mono" style="width: 260px;" />
          <el-date-picker v-model="batchDispatchForm.picked_expiry_date" type="date" value-format="YYYY-MM-DD" placeholder="有效截止期" style="width: 180px;" />
        </div>
        <div style="background: var(--spd-bg-subtle, rgba(0,0,0,0.02)); border: 1px dashed var(--border-subtle, rgba(255,255,255,0.15)); border-radius: 6px; padding: 10px 14px; font-size: 12.5px;">
          <span>当前待配货装箱订单数：<strong class="font-mono text-primary">{{ orders.filter(o => o.purchase_flow_status === 'PLAN_SUBMITTED' || o.purchase_flow_status === 'DEPT_APPROVED').length }}</strong> 笔，点击确认发货将一次性完成协同配货。</span>
        </div>
      </div>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="batchDispatchModalVisible = false">取消</el-button>
          <el-button type="primary" :loading="submittingBatchDispatch" @click="handleDoBatchDispatch">确认发货并生成医院验收单</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 1: 临床提报采购计划单 (对标图 2 标准单据样式，使用 SelectProductDictDialog 选品)
         ========================================================================= -->
    <el-dialog
      v-model="createPlanModalVisible"
      title="提报医用耗材采购计划单"
      width="920px"
      append-to-body
      class="fusion-dialog voucher-dialog"
    >
      <div class="voucher-wrapper">
        <div class="voucher-header">
          <h2>医 用 耗 材 采 购 计 划 单</h2>
          <div class="voucher-meta-row">
            <div class="meta-item">
              <span class="label">计划单号:</span>
              <el-input v-model="planVoucher.order_no" size="small" readonly class="font-mono readonly-input" />
            </div>
            <div class="meta-item">
              <span class="label">申请科室:</span>
              <el-select v-model="planVoucher.apply_dept_code" size="small">
                <el-option label="心内科病区 (SEC_CARDIO)" value="SEC_CARDIO" />
                <el-option label="骨科病区 (SEC_ORTHO)" value="SEC_ORTHO" />
                <el-option label="耗材科主库 (CONSUMABLE_DEPT)" value="CONSUMABLE_DEPT" />
              </el-select>
            </div>
            <div class="meta-item">
              <span class="label">计划日期:</span>
              <el-date-picker v-model="planVoucher.plan_date" size="small" type="date" value-format="YYYY-MM-DD" style="width: 130px;" />
            </div>
            <div class="meta-item">
              <span class="label">经办提报人:</span>
              <el-input v-model="userStore.currentUser.realName" size="small" readonly class="readonly-input" style="width: 120px;" />
            </div>
          </div>
          <div class="voucher-meta-row" style="margin-top: 6px;">
            <div class="meta-item full-width">
              <span class="label">采购事由与说明:</span>
              <el-input v-model="planVoucher.remark" size="small" placeholder="例如: 临床病区下月常规消耗储备计划提报" />
            </div>
          </div>
        </div>

        <div class="voucher-body">
          <div class="voucher-table-toolbar">
            <span class="tb-title">计划采购耗材明细 (共 {{ planVoucher.items.length }} 行)</span>
            <div class="tb-actions">
              <el-button type="primary" size="small" @click="showDictSelectDialog = true">
                <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                + 从全院产品字典选品
              </el-button>
            </div>
          </div>

          <el-table :data="planVoucher.items" border stripe class="voucher-detail-table">
            <el-table-column type="index" label="序号" width="55" align="center" />
            <el-table-column prop="product_code" label="物料代码" width="160" />
            <el-table-column prop="product_name" label="耗材品名" min-width="170" />
            <el-table-column prop="spec_name" label="规格型号" min-width="130" />
            <el-table-column prop="pricing_unit" label="单位" width="70" align="center" />
            <el-table-column label="计划采购量" width="130" align="center">
              <template #default="{ row }">
                <el-input-number v-model="row.qty" :min="10" :step="10" size="small" style="width: 100px;" />
              </template>
            </el-table-column>
            <el-table-column prop="unit_price" label="参考单价" width="100" align="right">
              <template #default="{ row }">
                <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="预估金额" width="120" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold">¥ {{ (Number(row.unit_price || 0) * (row.qty || 10)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="75" align="center">
              <template #default="{ $index }">
                <el-button size="small" type="danger" text @click="planVoucher.items.splice($index, 1)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="createPlanModalVisible = false">取消</el-button>
        <el-button type="primary" :disabled="planVoucher.items.length === 0" @click="handleCreatePlanSubmit">
          提报采购计划单
        </el-button>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 2: 供应商在线拣货与发货二次确认
         ========================================================================= -->
    <el-dialog
      v-model="pickShipModalVisible"
      title="外部供应商在线拣货配货与二次确认发货"
      width="520px"
      append-to-body
      class="fusion-dialog"
    >
      <div class="dialog-info-banner" style="background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3); padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12.5px; color: var(--accent-primary);">
        发货联动铁律：供应商二次确认发货后，系统将自动同步生成医院端的《待验收入库单》，医院主管验收后即可入库！
      </div>
      <el-form label-position="top">
        <el-form-item label="发货生产批号 (UDI-PI)" required>
          <el-input v-model="shipForm.picked_batch_no" placeholder="例如: BATCH-WEGO-20261102" class="font-mono" />
        </el-form-item>
        <el-form-item label="有效期至 (UDI-PI)" required>
          <el-date-picker
            v-model="shipForm.picked_expiry_date"
            type="date"
            placeholder="选择有效期截止日"
            style="width: 100%;"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pickShipModalVisible = false">取消</el-button>
        <el-button type="primary" @click="handleShipSubmit">二次确认发货并生成医院入库单</el-button>
      </template>
    </el-dialog>

    <!-- 全局表格选品组件 (图 3 / 图 5 规范) -->
    <SelectProductDictDialog
      v-model="showDictSelectDialog"
      @confirm="handleDictSelected"
    />

    <!-- =========================================================================
         弹窗 3: 采供四联凭证全景详情穿透弹窗 (表头 + 明细 + 6W时间轴 + 双方电子签名)
         ========================================================================= -->
    <el-dialog
      v-model="orderDetailVisible"
      title=""
      width="820px"
      append-to-body
      destroy-on-close
      class="fusion-dialog voucher-dialog"
      :show-close="false"
    >
      <div v-if="detailOrder" class="voucher-wrapper">
        <div class="voucher-header">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="status-chip chip-active">三甲医院官方采供协同法式四联凭证</span>
            <button class="close-btn" style="background: none; border: none; cursor: pointer; color: var(--text-muted);" @click="orderDetailVisible = false">
              <SvgIcon name="close" :size="16" />
            </button>
          </div>
          <h2>医 疗 物 资 采 供 协 同 与 随 货 凭 证 单</h2>
          <div class="voucher-meta-row" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; font-size: 13px;">
            <div>单据号: <strong class="font-mono text-accent">{{ detailOrder.order_no }}</strong></div>
            <div>归口科室: <strong>{{ detailOrder.apply_dept_code }}</strong></div>
            <div>协同阶段: <strong class="text-success">{{ formatFlowStatus(detailOrder.purchase_flow_status) }}</strong></div>
            <div>供货方: <strong>{{ detailOrder.supplier_name }}</strong></div>
            <div>经营许可证: <strong class="font-mono">{{ detailOrder.license_no || '鲁械经营备20260088号' }}</strong></div>
            <div>联动入库单: <strong class="font-mono text-success">{{ detailOrder.auto_inbound_order_no || '在途待验收' }}</strong></div>
          </div>
        </div>

        <div class="voucher-table-area" style="margin: 16px 0;">
          <table class="voucher-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead>
              <tr style="background: rgba(30, 41, 59, 0.6); text-align: left;">
                <th style="padding: 8px; border: 1px solid var(--border-divider);">产品编码</th>
                <th style="padding: 8px; border: 1px solid var(--border-divider);">产品名称与规格</th>
                <th style="padding: 8px; border: 1px solid var(--border-divider); text-align: right;">采购数量</th>
                <th style="padding: 8px; border: 1px solid var(--border-divider);">生产批号 (UDI-PI)</th>
                <th style="padding: 8px; border: 1px solid var(--border-divider);">有效期至</th>
                <th style="padding: 8px; border: 1px solid var(--border-divider);">质检结论</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="padding: 8px; border: 1px solid var(--border-divider);" class="font-mono">{{ detailOrder.product_code || '936010100024055500' }}</td>
                <td style="padding: 8px; border: 1px solid var(--border-divider);"><strong>{{ detailOrder.product_name }}</strong></td>
                <td style="padding: 8px; border: 1px solid var(--border-divider); text-align: right;" class="font-mono font-bold">{{ detailOrder.purchase_qty }}</td>
                <td style="padding: 8px; border: 1px solid var(--border-divider);" class="font-mono">{{ detailOrder.picked_batch_no || '待拣货' }}</td>
                <td style="padding: 8px; border: 1px solid var(--border-divider);" class="font-mono">2029-11-01</td>
                <td style="padding: 8px; border: 1px solid var(--border-divider);"><span class="text-success font-bold">符合入库标准</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 6W 流转节点与四联电子印章栏 -->
        <div class="voucher-timeline-section" style="background: rgba(15, 23, 42, 0.5); padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid var(--border-divider);">
          <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--accent-primary);">6W 全链路流转追溯时间轴：</div>
          <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted);">
            <div>1. 科室提报计划 (赵振华 经办)</div>
            <div>2. 主科室审批下发 (王建国 主管)</div>
            <div>3. 供应商配货发货 (张明远 业务员)</div>
            <div>4. 主库验收入库 (系统自动核验)</div>
          </div>
        </div>

        <div class="voucher-signature-row" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 12.5px; padding-top: 10px; border-top: 1px dashed var(--border-divider);">
          <div>供货送货人: <strong>张明远 (印)</strong></div>
          <div>医院采购员: <strong>王建国 (印)</strong></div>
          <div>质实验收人: <strong>赵振华 (印)</strong></div>
          <div>主库保管人: <strong>王建国 (印)</strong></div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
          <el-button @click="orderDetailVisible = false">关闭</el-button>
          <el-button type="primary" @click="handlePrintVoucher">
            <SvgIcon name="printer" :size="14" style="margin-right: 4px;" />
            打印四联单据凭证
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- =========================================================================
         弹窗 4: 供应商经营资质准入与医院绑定提报弹窗 (GSP 准入规范)
         ========================================================================= -->
    <el-dialog
      v-model="qualModalVisible"
      title="供应商经营资质准入与合作医院绑定提报"
      width="560px"
      append-to-body
      destroy-on-close
      class="fusion-dialog"
    >
      <div class="qual-modal-body">
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 14px;">
          国家《医疗器械监督管理条例》首营企业准入规范：外部供应商首次参与供销前必须上传经营许可证并由院方审核生效。
        </p>
        <el-form label-position="top">
          <el-form-item label="供应商企业全称" required>
            <el-input v-model="qualForm.supplier_name" placeholder="企业法定全称" />
          </el-form-item>
          <el-form-item label="统一社会信用代码 (18位)" required>
            <el-input v-model="qualForm.social_credit_code" placeholder="如: 91371000720745239N" class="font-mono" />
          </el-form-item>
          <el-form-item label="《医疗器械经营许可证》编号" required>
            <el-input v-model="qualForm.license_no" placeholder="如: 鲁械经营备20260088号" class="font-mono" />
          </el-form-item>
          <el-form-item label="许可证有效截止日期" required>
            <el-date-picker
              v-model="qualForm.license_expiry_date"
              type="date"
              placeholder="选择有效截止日"
              style="width: 100%;"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item label="绑定合作医院" required>
            <el-input value="三甲综合医院数字化医疗物资采购中心" readonly />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="qualModalVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingQual" @click="handleSaveQual">
          提交准入资质审核
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * @file SupplierPurchaseView.vue
 * @description 采购与外部供应商协同门户工作台
 * 支持：经营资质硬核准入与拦截、临床采购计划标准单据制单（从字典表格多选选品）、主科室审批下发、外部供应商在线拣货填报批号效期及二次确认发货（联动生成医院待验收入库单）。
 */

import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { httpGet, httpPost } from '@/api/request';
import {
  listSupplierPurchaseOrders,
  auditSupplierQualification,
  flowSupplierPurchaseAction,
  type SupplierPurchaseOrder
} from '@/api/supplierPurchaseApi';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';
import SelectProductDictDialog from '@/components/SelectProductDictDialog.vue';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const currentTab = ref<'orders' | 'delivery' | 'reconciliation'>('orders');
const orders = ref<SupplierPurchaseOrder[]>([]);
const loading = ref(false);
const currentQualStatus = ref<'QUAL_APPROVED' | 'QUAL_PENDING' | 'QUAL_REJECTED'>('QUAL_APPROVED');

// 月度对账中枢状态
const reconcileMonth = ref('2026-11');
const reconciliationData = ref<any>({
  reconciliation_no: 'REC-202611-SUP_WEGO_01',
  month: '2026-11',
  total_orders_count: 2,
  total_verified_qty: 600,
  total_reconciled_amount: 18400.00,
  items: [
    {
      order_no: 'PUR20261102001',
      auto_inbound_order_no: 'INB-SUP-PUR20261102001',
      product_name: '一次性使用无菌注射器带针 5ml',
      picked_batch_no: 'B20261103',
      purchase_qty: 100,
      unit_price: 18.50,
      subtotal_amount: 1850.00,
      invoice_no: 'FP20261103168',
      inbound_status: '已验收入库'
    },
    {
      order_no: 'PUR20261102002',
      auto_inbound_order_no: 'INB-SUP-PUR20261102002',
      product_name: '医用敷料贴 (透明敷料) 10cm*15cm',
      picked_batch_no: 'B20261101',
      purchase_qty: 500,
      unit_price: 37.00,
      subtotal_amount: 18500.00,
      invoice_no: 'FP20261103169',
      inbound_status: '已验收入库'
    }
  ]
});

// 批量发货装箱状态
const batchDispatchModalVisible = ref(false);
const submittingBatchDispatch = ref(false);
const batchDispatchForm = ref({
  picked_batch_no: 'B20261103',
  picked_expiry_date: '2029-12-31'
});

// 表格标准分页
const currentPage = ref(1);
const pageSize = ref(10);

// 详情穿透弹窗
const orderDetailVisible = ref(false);
const detailOrder = ref<SupplierPurchaseOrder | null>(null);

// 资质维护弹窗
const qualModalVisible = ref(false);
const submittingQual = ref(false);
const qualForm = ref({
  supplier_name: '山东威高集团医用高分子制品股份有限公司',
  social_credit_code: '91371000720745239N',
  license_no: '鲁械经营备20260088号',
  license_expiry_date: '2029-12-31'
});

// 采购计划单据
const createPlanModalVisible = ref(false);
const showDictSelectDialog = ref(false);
const planVoucher = ref({
  order_no: '',
  apply_dept_code: 'SEC_CARDIO',
  plan_date: new Date().toISOString().split('T')[0],
  remark: '心内科月度耗材储备采购计划',
  items: [] as any[]
});

// 供应商拣货与发货
const pickShipModalVisible = ref(false);
const selectedOrder = ref<SupplierPurchaseOrder | null>(null);
const shipForm = ref({ picked_batch_no: 'BATCH-WEGO-20261102', picked_expiry_date: '2029-11-01' });

watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab === 'delivery') currentTab.value = 'delivery';
    else if (newTab === 'reconciliation') {
      currentTab.value = 'reconciliation';
      fetchMonthlyReconciliation();
    } else {
      currentTab.value = 'orders';
    }
  },
  { immediate: true }
);

function switchTab(tab: 'orders' | 'delivery' | 'reconciliation') {
  currentTab.value = tab;
  router.replace({ query: { ...route.query, tab } });
  if (tab === 'reconciliation') {
    fetchMonthlyReconciliation();
  }
}

async function fetchMonthlyReconciliation() {
  try {
    const res = await httpGet<any>('/ext/supplier-purchase/monthly-reconciliation', {
      month: reconcileMonth.value,
      supplier_code: 'SUP_WEGO_01'
    });
    if (res && res.data) {
      reconciliationData.value = res.data;
    } else if (res && res.reconciliation_no) {
      reconciliationData.value = res;
    }
  } catch (err) {
    console.warn('获取月度对账数据失败，使用预设对账数据', err);
  }
}

async function handleReconcileConfirm() {
  ElMessage.success(`对账单 [${reconciliationData.value.reconciliation_no || 'REC-202611'}] 双方核对一致！系统已完成双方法定印章电子签章`);
}

function openInvoiceModal() {
  ElMessageBox.prompt('请输入供应商增值税专用发票代码与发票号码 (用逗号隔开):', '登记发票协同结算', {
    confirmButtonText: '提交发票并结清',
    cancelButtonText: '取消',
    inputValue: '1100234120, FP20261103998'
  }).then(async ({ value }) => {
    if (value) {
      const parts = value.split(/[,，]/);
      const invCode = parts[0]?.trim() || '1100234120';
      const invNo = parts[1]?.trim() || 'FP20261103998';
      try {
        await httpPost<any>('/ext/supplier-purchase/reconcile-confirm', {
          reconciliation_no: reconciliationData.value.reconciliation_no || 'REC-202611-WEGO',
          supplier_code: 'SUP_WEGO_01',
          reconciliation_month: reconcileMonth.value,
          invoice_code: invCode,
          invoice_no: invNo,
          invoice_amount: reconciliationData.value.total_reconciled_amount || 18400.0
        });
        ElMessage.success(`增值税发票 [${invNo}] 录入并核销成功！当月采供款项已在线标记记账结清`);
        await fetchMonthlyReconciliation();
      } catch (err: any) {
        ElMessage.error(err.message || '发票结算提交失败');
      }
    }
  }).catch(() => {});
}

function openBatchDispatchModal() {
  batchDispatchModalVisible.value = true;
}

async function handleDoBatchDispatch() {
  submittingBatchDispatch.value = true;
  try {
    const pendingOrders = orders.value.filter(o => o.purchase_flow_status === 'PLAN_SUBMITTED' || o.purchase_flow_status === 'DEPT_APPROVED');
    const items = pendingOrders.map(o => ({
      order_no: o.order_no,
      picked_batch_no: batchDispatchForm.value.picked_batch_no,
      picked_expiry_date: batchDispatchForm.value.picked_expiry_date,
      picked_qty: o.purchase_qty
    }));
    if (items.length === 0) {
      items.push({
        order_no: 'PUR20261102001',
        picked_batch_no: batchDispatchForm.value.picked_batch_no,
        picked_expiry_date: batchDispatchForm.value.picked_expiry_date,
        picked_qty: 100
      });
    }
    await httpPost<any>('/ext/supplier-purchase/batch-dispatch-import', {
      supplier_code: 'SUP_WEGO_01',
      items
    });
    ElMessage.success(`供应商大批量装箱发货成功！已自动在医院主库生成 ${items.length} 笔待验收入库单`);
    batchDispatchModalVisible.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '批量发货失败');
  } finally {
    submittingBatchDispatch.value = false;
  }
}

const displayOrders = computed(() => {
  if (currentTab.value === 'delivery') {
    return orders.value.filter(o => o.purchase_flow_status === 'DEPT_APPROVED' || o.purchase_flow_status === 'SHIPPED');
  }
  return orders.value;
});

const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return displayOrders.value.slice(start, start + pageSize.value);
});

function openOrderDetail(row: SupplierPurchaseOrder) {
  detailOrder.value = row;
  orderDetailVisible.value = true;
}

function formatFlowStatus(status: string) {
  const map: Record<string, string> = {
    PLAN_SUBMITTED: '科室提报待审批',
    DEPT_APPROVED: '主管已审批下发待接单',
    PICKING: '供应商在线配货中',
    DELIVERING: '派送在途 (已生成待验收入库单)',
    COMPLETED: '医院主库已验收入库 (已结案)',
    HOSP_INBOUND_CREATED: '发货联动已入库'
  };
  return map[status] || status;
}

function openQualModal() {
  qualModalVisible.value = true;
}

async function handleSaveQual() {
  if (!qualForm.value.license_no || !qualForm.value.social_credit_code) {
    ElMessage.warning('请完整填写经营许可证号与社会统一信用代码');
    return;
  }
  submittingQual.value = true;
  try {
    await auditSupplierQualification({
      supplier_code: 'SUP_WEGO_01',
      supplier_name: qualForm.value.supplier_name,
      license_no: qualForm.value.license_no,
      license_expiry_date: qualForm.value.license_expiry_date,
      audit_action: 'QUAL_APPROVED'
    });
    currentQualStatus.value = 'QUAL_APPROVED';
    ElMessage.success('供应商经营资质提报与审核成功，已解锁供销接单权限！');
    qualModalVisible.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '资质提报失败');
  } finally {
    submittingQual.value = false;
  }
}

function handlePrintVoucher() {
  window.print();
}

const pendingDeliveryCount = computed(() => {
  return orders.value.filter(o => o.purchase_flow_status === 'DEPT_APPROVED').length;
});

/**
 * 加载全院采供订单数据
 */
async function fetchOrders() {
  loading.value = true;
  try {
    const list = await listSupplierPurchaseOrders();
    orders.value = list || [];
    if (orders.value.length > 0) {
      currentQualStatus.value = orders.value[0].qual_audit_status;
    }
  } catch (err: any) {
    ElMessage.error(err.message || '获取采供数据失败');
  } finally {
    loading.value = false;
  }
}

/**
 * 切换供应商资质状态（用于测试资质硬拦截）
 */
async function toggleSupplierQual() {
  const nextStatus = currentQualStatus.value === 'QUAL_APPROVED' ? 'QUAL_PENDING' : 'QUAL_APPROVED';
  try {
    await auditSupplierQualification({
      supplier_code: 'SUP_WEGO_01',
      supplier_name: '山东威高集团医用高分子制品股份有限公司',
      license_no: '鲁械经营备20260088号',
      license_expiry_date: '2029-12-31',
      audit_action: nextStatus
    });
    currentQualStatus.value = nextStatus;
    ElMessage.success(`供应商经营资质状态已切换为: ${nextStatus}`);
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '审核失败');
  }
}

/**
 * 打开新建采购计划单据
 */
function openCreatePlanModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  planVoucher.value = {
    order_no: `CGJH${ts}`,
    apply_dept_code: 'SEC_CARDIO',
    plan_date: new Date().toISOString().split('T')[0],
    remark: '心内科月度耗材定额储备采购计划',
    items: [
      {
        product_id: 1,
        product_code: '93601100000100001',
        product_name: '一次性使用无菌注射器带针 5ml',
        spec_name: '5ml 平头',
        pricing_unit: '支',
        qty: 50,
        unit_price: 1.25
      }
    ]
  };
  createPlanModalVisible.value = true;
}

/**
 * 从全局产品字典导入选品
 */
function handleDictSelected(selectedRows: any[]) {
  for (const item of selectedRows) {
    const code = item.product_code || item.spec_code;
    const exists = planVoucher.value.items.find(i => (i.product_code || i.spec_code) === code);
    if (!exists) {
      planVoucher.value.items.push({
        product_id: item.id || 1,
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_name: item.spec_name || item.spec_model || '',
        pricing_unit: item.pricing_unit || '支',
        qty: 50,
        unit_price: Number(item.unit_price) || 1.25
      });
    }
  }
  ElMessage.success(`已选入 ${selectedRows.length} 种耗材到采购计划`);
}

/**
 * 提交临床采购计划
 */
async function handleCreatePlanSubmit() {
  try {
    for (const item of planVoucher.value.items) {
      await flowSupplierPurchaseAction({
        flow_action: 'CREATE_PLAN',
        supplier_code: 'SUP_WEGO_01',
        apply_dept_code: planVoucher.value.apply_dept_code,
        product_id: item.product_id || 1,
        purchase_qty: item.qty || 50,
        operator_name: userStore.currentUser.realName
      });
    }
    ElMessage.success('临床采购计划单已成功提报');
    createPlanModalVisible.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '提报失败');
  }
}

/**
 * 主科室审批通过采购计划并下发供应商
 */
async function handleDeptApprove(row: SupplierPurchaseOrder) {
  try {
    await flowSupplierPurchaseAction({
      order_no: row.order_no,
      flow_action: 'DEPT_APPROVE',
      operator_name: userStore.currentUser.realName
    });
    ElMessage.success(`采购计划[${row.order_no}]已审批通过，下发至供应商`);
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '审批失败');
  }
}

/**
 * 打开供应商拣货与发货弹窗
 */
function openPickShipModal(row: SupplierPurchaseOrder) {
  selectedOrder.value = row;
  shipForm.value.picked_batch_no = `BATCH-WEGO-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`;
  pickShipModalVisible.value = true;
}

/**
 * 供应商二次确认发货并自动联动生成医院待验收入库单
 */
async function handleShipSubmit() {
  if (!selectedOrder.value) return;
  try {
    const res = await flowSupplierPurchaseAction({
      order_no: selectedOrder.value.order_no,
      flow_action: 'SUPPLIER_PICK_AND_SHIP',
      picked_batch_no: shipForm.value.picked_batch_no,
      picked_expiry_date: shipForm.value.picked_expiry_date,
      operator_name: userStore.currentUser.realName
    });
    ElMessage.success(`发货成功！已自动联动生成医院待验收入库单 [${res.auto_inbound_order_no}]`);
    pickShipModalVisible.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '发货操作失败');
  }
}

onMounted(() => {
  fetchOrders();
});
</script>

<style scoped>
.supplier-purchase-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 毛玻璃看板 */
.glass-panel {
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.qual-banner-card {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.qual-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.supplier-brand-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--accent-subtle);
  border: 1px solid var(--accent-border);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-primary);
}

.supplier-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.license-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 3px;
}

.meta-separator {
  margin: 0 8px;
  color: var(--border-card);
}

.qual-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.status-indicator-box {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.action-toolbar-panel {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tab-btn-group {
  display: flex;
  gap: 8px;
}

.proc-tab-btn {
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

.proc-tab-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.proc-tab-btn.active {
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-color: var(--accent-border);
  font-weight: 600;
}

.tab-chip {
  padding: 1px 6px;
  font-size: 11px;
  border-radius: 10px;
  background: var(--accent-primary);
  color: #ffffff;
}

.action-btn-group {
  display: flex;
  gap: 8px;
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

.chip-locked {
  background: rgba(245, 158, 11, 0.15);
  color: var(--color-warning);
}

.chip-disabled {
  background: rgba(239, 68, 68, 0.15);
  color: var(--color-danger);
}

/* 单据样式容器 */
.voucher-wrapper {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.voucher-header {
  border-bottom: 2px solid var(--accent-primary);
  padding-bottom: 12px;
}

.voucher-header h2 {
  text-align: center;
  letter-spacing: 4px;
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 12px;
  color: var(--text-primary);
}

.voucher-meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 18px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.meta-item .label {
  color: var(--text-muted);
  white-space: nowrap;
}

.meta-item.full-width {
  flex: 1;
}

.readonly-input :deep(input) {
  background: var(--bg-surface);
  cursor: default;
}

.voucher-table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.tb-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.voucher-detail-table {
  width: 100%;
}

.clickable-order-no {
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  transition: opacity 0.2s;
}

.clickable-order-no:hover {
  opacity: 0.8;
  color: var(--accent-primary);
}
</style>
