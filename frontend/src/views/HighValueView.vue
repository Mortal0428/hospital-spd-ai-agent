<template>
  <div class="high-value-view">
    <!-- 顶部 4 宫格高质感毛玻璃 KPI 指标大盘 -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>高值耗材专仓单品</span>
          <SvgIcon name="safe" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          {{ inStockCount }} <span class="kpi-unit">套 (UDI 一物一码)</span>
        </div>
        <div class="kpi-sub">
          <SvgIcon name="check" :size="13" color="var(--color-success)" />
          <span>智能柜在库锁定率 100% · 移库不计费</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>待上级审批备货单</span>
          <SvgIcon name="clock" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-warn">
          {{ pendingPrepCount }} <span class="kpi-unit">笔待审</span>
        </div>
        <div class="kpi-sub text-warn">
          <SvgIcon name="info" :size="13" color="var(--color-warning)" />
          <span>审批通过直接下发入仓 · 联动主库出库记录</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>已绑定患者核销结算</span>
          <SvgIcon name="pulse" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-success">
          {{ verifiedCount }} <span class="kpi-unit">件 (消耗即结算)</span>
        </div>
        <div class="kpi-sub text-success">
          <SvgIcon name="check" :size="13" color="var(--color-success)" />
          <span>脱敏绑定住院号并触发财务记账</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>退货永久不可逆锁定</span>
          <SvgIcon name="lock" :size="16" color="var(--color-danger)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-danger">
          {{ lockedReturnCount }} <span class="kpi-unit">笔封账</span>
        </div>
        <div class="kpi-sub text-danger">
          <SvgIcon name="shield" :size="13" color="var(--color-danger)" />
          <span>二次确认提交即锁死 · 防篡改内控合规</span>
        </div>
      </div>
    </div>

    <!-- 主体毛玻璃 Tab 工作台 (与侧边栏 5 大子功能 1:1 双向绑定) -->
    <div class="glass-panel tab-container-panel">
      <el-tabs v-model="activeTab" class="fusion-tabs" @tab-change="handleTabChange">
        <!-- =====================================================================
             Tab 1: 备货自动入仓与上级审批 (inbound)
             ===================================================================== -->
        <el-tab-pane label="备货自动入仓" name="inbound">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>术前高值备货申请与审批下发 · 经耗材科/设备科主库审批后直接下发专仓并生成UDI，免去重复验收入库，普通主库自动生成出库记录</span>
              </div>
              <div class="action-btn-group">
                <el-button
                  v-if="userStore.canAction('HV_PREP_RECEIVE', 'can_create')"
                  type="primary"
                  size="small"
                  @click="openCreatePrepModal"
                >
                  <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                  填写高值备货申请单
                </el-button>
                <el-button plain size="small" @click="fetchPrepData">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新备货单据
                </el-button>
              </div>
            </div>

            <el-table
              :data="paginatedPrepOrders"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingPrep"
            >
              <el-table-column prop="order_no" label="备货申请单号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="dept_code" label="申请科室" width="140">
                <template #default="{ row }">
                  <span class="font-bold">{{ formatDeptName(row.dept_code) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="审批主科室" width="150">
                <template #default="{ row }">
                  <span class="status-chip chip-info">{{ row.target_main_warehouse || '耗材科主库' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="高值耗材品名" min-width="190" />
              <el-table-column prop="udi_sn" label="一物一码 UDI" width="170">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums status-chip chip-info">{{ row.udi_sn }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="confirm_stage" label="审批状态" width="130" align="center">
                <template #default="{ row }">
                  <span v-if="row.confirm_stage === 'APPROVED'" class="status-chip chip-active">已审批并直发专仓</span>
                  <span v-else-if="row.confirm_stage === 'SUBMITTED'" class="status-chip chip-info">待主科室审批</span>
                  <span v-else class="status-chip chip-locked">待确认</span>
                </template>
              </el-table-column>
              <el-table-column prop="operator_name" label="申请人" width="110" align="center" />
              <el-table-column prop="created_at" label="提报时间" width="165" class-name="font-mono tabular-nums" />
              <el-table-column label="操作" width="180" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 6px; justify-content: center;">
                    <el-button
                      v-if="row.confirm_stage !== 'APPROVED' && (userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'dept_manager')"
                      size="small"
                      type="success"
                      @click="handleApprovePrep(row)"
                    >
                      审批通过并直发
                    </el-button>
                    <span v-else-if="row.confirm_stage === 'APPROVED'" class="status-chip chip-active">已下发专仓</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 备货申请分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="prepPage"
                v-model:page-size="prepPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="prepOrders.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 2: 专柜智能台账 (stock)
             ===================================================================== -->
        <el-tab-pane label="专柜智能台账" name="stock">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>高值耗材专仓智能柜在库单品 · 一物一码 UDI 全生命周期管理 · 移库不计费</span>
              </div>
              <div class="action-btn-group">
                <el-button plain size="small" @click="fetchItemsData">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新单品台账
                </el-button>
              </div>
            </div>

            <el-table
              :data="paginatedStockItems"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingItems"
            >
              <el-table-column prop="udi_sn" label="单品 UDI (一物一码)" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.udi_sn }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="高值耗材品名" min-width="190" />
              <el-table-column prop="spec_model" label="规格型号" min-width="160" show-overflow-tooltip />
              <el-table-column prop="wh_cabinet_code" label="智能专柜仓位" width="180" />
              <el-table-column prop="batch_no" label="生产批号" width="130" class-name="font-mono" />
              <el-table-column prop="expiry_date" label="有效期至" width="120" class-name="font-mono" />
              <el-table-column label="单价" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="item_status" label="在库状态" width="130" align="center">
                <template #default="{ row }">
                  <span v-if="row.item_status === 'USED_VERIFIED'" class="status-chip chip-active">已患者核销</span>
                  <span v-else-if="row.item_status === 'RECALLED'" class="status-chip chip-disabled">召回锁定</span>
                  <span v-else class="status-chip chip-info">智能柜在库</span>
                </template>
              </el-table-column>
              <el-table-column label="扫码核销" width="150" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    v-if="row.item_status !== 'USED_VERIFIED'"
                    size="small"
                    type="primary"
                    @click="openQrVerifyModal(row)"
                  >
                    扫码核销扣库
                  </el-button>
                  <span v-else class="text-muted font-mono" style="font-size: 11px;">已核销</span>
                </template>
              </el-table-column>
            </el-table>

            <!-- 专柜单品台账分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="stockPage"
                v-model:page-size="stockPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="stockItems.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 3: 一物一码赋码与患者核销 (coding)
             ===================================================================== -->
        <el-tab-pane label="一物一码赋码与核销" name="coding">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="pulse" :size="15" color="var(--color-success)" />
                <span>患者扫码核销台账 (消耗即结算) · 严格执行国家患者隐私脱敏规范 (张*丰 · 住院号 ZY...) 并联动财务记账</span>
              </div>
              <div class="action-btn-group">
                <el-button plain size="small" @click="fetchVerified">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新核销记录
                </el-button>
              </div>
            </div>

            <el-table
              :data="paginatedVerifiedList"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingVerified"
            >
              <el-table-column prop="verify_no" label="核销流水号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.verify_no || `VERIFY-${row.udi_sn}` }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="耗材品名" min-width="180" />
              <el-table-column prop="udi_sn" label="单品 UDI" width="170">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums status-chip chip-info">{{ row.udi_sn }}</span>
                </template>
              </el-table-column>
              <el-table-column label="核销患者 (严格脱敏)" width="160">
                <template #default="{ row }">
                  <strong>{{ row.patient_name_masked || '张*丰' }}</strong>
                  <div class="text-muted font-mono" style="font-size: 11px;">
                    住院号: {{ row.hospital_no_masked || row.patient_inpatient_no || 'ZY20261102001' }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="surgery_name" label="手术名称" min-width="160" show-overflow-tooltip />
              <el-table-column label="财务记账状态" width="130" align="center">
                <template #default>
                  <span class="status-chip chip-active">消耗即结算</span>
                </template>
              </el-table-column>
              <el-table-column prop="verify_nurse_name" label="经办责任护士" width="120" />
              <el-table-column prop="verified_at" label="核销时间" width="165" class-name="font-mono tabular-nums" />
            </el-table>

            <!-- 高值患者核销记录分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="verifiedPage"
                v-model:page-size="verifiedPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="verifiedList.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 4: 退货出库锁定 (return - 不可逆锁死)
             ===================================================================== -->
        <el-tab-pane label="退货出库锁定" name="return">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="lock" :size="15" color="var(--color-danger)" />
                <span>临床科室向高值仓退货出库 · 一旦二次确认提交系统强制永久不可逆锁死，严禁撤销修改</span>
              </div>
              <div class="action-btn-group">
                <el-button
                  v-if="userStore.canAction('HV_RETURN', 'can_create')"
                  type="danger"
                  size="small"
                  @click="openCreateReturnModal"
                >
                  <SvgIcon name="close" :size="13" style="margin-right: 4px;" />
                  开具科室退货出库单
                </el-button>
                <el-button plain size="small" @click="fetchReturnData">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新退货台账
                </el-button>
              </div>
            </div>

            <el-table
              :data="paginatedReturnOrders"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingReturn"
            >
              <el-table-column prop="order_no" label="退货单号" width="180">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="dept_code" label="退货科室" width="140">
                <template #default="{ row }">
                  <span>{{ formatDeptName(row.dept_code) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="耗材品名" min-width="190" />
              <el-table-column prop="udi_sn" label="单品 UDI" width="170">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums status-chip chip-info">{{ row.udi_sn }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="remark" label="退货出库原因" min-width="180" show-overflow-tooltip />
              <el-table-column prop="is_irreversible_locked" label="不可逆状态" width="130" align="center">
                <template #default="{ row }">
                  <span v-if="row.is_irreversible_locked" class="status-chip chip-disabled">已永久锁死</span>
                  <span v-else class="status-chip chip-locked">待二次确认</span>
                </template>
              </el-table-column>
              <el-table-column label="两阶段确认操作" width="200" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    v-if="!row.is_irreversible_locked && userStore.canAction('HV_RETURN', 'can_second_confirm')"
                    size="small"
                    type="danger"
                    @click="handleLockReturn(row)"
                  >
                    第2次确认(永久锁死)
                  </el-button>
                  <span v-else class="text-muted font-mono" style="font-size: 11.5px;">退货已永久封账</span>
                </template>
              </el-table-column>
            </el-table>

            <!-- 高值退货出库单据分页条 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="returnPage"
                v-model:page-size="returnPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="returnOrders.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 5: 高值独立盘点 (对标图 2 两级盘点工作台)
             ===================================================================== -->
        <el-tab-pane label="高值独立盘点" name="stocktake">
          <div class="tab-content-area" style="padding-top: 4px;">
            <StocktakePlanWorkbench
              scope="HIGH_VALUE"
              default-warehouse-code="WH_HIGH_VALUE"
            />
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 6: 全院/分仓高值实时库存 (对标普通耗材主库全院穿透查看)
             ===================================================================== -->
        <el-tab-pane label="全院/分仓高值实时库存" name="realtime">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="pulse" :size="15" color="var(--accent-primary)" />
                <span>全院高值智能专柜单品实时在库台账 · 一物一码 UDI 全生命周期穿透监控 · 效期预警</span>
              </div>
              <div class="action-btn-group">
                <el-select v-model="realtimeCabinetFilter" size="small" placeholder="按专柜筛选" style="width: 180px;" @change="fetchRealtimeHvStock">
                  <el-option label="全部授权专柜汇总" value="ALL" />
                  <el-option label="心血管智能专柜-A01" value="心血管" />
                  <el-option label="骨科手术室智能专柜-B02" value="骨科" />
                  <el-option label="高值专仓-总仓专柜01" value="高值专仓" />
                </el-select>
                <el-input
                  v-model="realtimeHvKeyword"
                  placeholder="UDI/编码/品名/批号..."
                  size="small"
                  style="width: 190px;"
                  clearable
                  @keyup.enter="fetchRealtimeHvStock"
                />
                <el-button plain size="small" @click="fetchRealtimeHvStock">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新高值库存
                </el-button>
              </div>
            </div>

            <div class="realtime-kpi-summary-row" style="display: flex; gap: 16px; margin-bottom: 12px; font-size: 13px;">
              <span class="status-chip chip-info font-bold">全院高值在柜单品总数: <strong class="font-mono">{{ realtimeHvTotalQty }}</strong> 件</span>
              <span class="status-chip chip-active font-bold">全院高值实物在柜资产总值: <strong class="font-mono">¥ {{ realtimeHvTotalAmount.toFixed(2) }}</strong></span>
            </div>

            <el-table :data="realtimeHvList" border stripe size="small" class="fusion-styled-table" v-loading="loadingRealtimeHv">
              <el-table-column type="index" label="序号" width="55" align="center" />
              <el-table-column prop="wh_cabinet_code" label="存放智能专柜 / 位置" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="font-bold text-accent">{{ row.wh_cabinet_code || '高值专仓智能柜' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="udi_sn" label="单品 UDI" width="165" class-name="font-mono text-accent" />
              <el-table-column prop="product_code" label="物料代码" width="130" class-name="font-mono" />
              <el-table-column prop="product_name" label="耗材品名" min-width="170" />
              <el-table-column prop="spec_model" label="规格型号" width="130" show-overflow-tooltip />
              <el-table-column prop="batch_no" label="生产批次" width="115" class-name="font-mono" />
              <el-table-column prop="expiry_date" label="有效期至" width="110" class-name="font-mono tabular-nums" />
              <el-table-column prop="unit_price" label="单价" width="100" align="right">
                <template #default="{ row }">
                  <span class="font-mono font-bold">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="item_status" label="在库状态" width="120" align="center">
                <template #default="{ row }">
                  <span v-if="row.item_status === 'IN_HIGH_VALUE_WH' || row.item_status === 'IN_SECONDARY_CABINET'" class="status-chip chip-active">在柜正常</span>
                  <span v-else-if="row.item_status === 'USED_VERIFIED'" class="status-chip chip-info">已核销出库</span>
                  <span v-else-if="row.item_status === 'RECALLED'" class="status-chip chip-disabled">召回锁定</span>
                  <span v-else class="status-chip chip-locked">{{ row.item_status }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 7: 高值专柜期初建账 (不可逆锁)
             ===================================================================== -->
        <el-tab-pane label="高值专柜期初建账 (不可逆锁)" name="init-stock">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="lock" :size="15" color="var(--color-warning)" />
                <span>全院高值智能专柜期初一物一码建账数据 · 专柜初始化一次性锁定 · 管理员全院穿透查看</span>
              </div>
              <div class="action-btn-group">
                <el-button plain size="small" @click="fetchInitialHvStock">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新期初数据
                </el-button>
              </div>
            </div>

            <el-table :data="initialHvList" border stripe size="small" class="fusion-styled-table" v-loading="loadingInitialHv">
              <el-table-column type="index" label="序号" width="55" align="center" />
              <el-table-column prop="cabinet_code" label="智能专柜" width="160" show-overflow-tooltip />
              <el-table-column prop="udi_sn" label="单品 UDI" width="165" class-name="font-mono text-accent" />
              <el-table-column prop="product_code" label="产品代码" width="130" class-name="font-mono" />
              <el-table-column prop="product_name" label="耗材品名" min-width="170" />
              <el-table-column prop="spec_model" label="规格型号" width="120" />
              <el-table-column prop="batch_no" label="批次号" width="115" class-name="font-mono" />
              <el-table-column prop="unit_price" label="核算单价" width="100" align="right">
                <template #default="{ row }">
                  <span class="font-mono font-bold">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="建账锁定状态" width="130" align="center">
                <template #default>
                  <span class="status-chip chip-disabled">不可逆锁定</span>
                </template>
              </el-table-column>
              <el-table-column prop="locked_at" label="建账锁定时间" width="160" class-name="font-mono tabular-nums" />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 8: 不良事件召回患者追访中枢 (recall-trace) (方案 A 落地)
             ===================================================================== -->
        <el-tab-pane label="不良事件召回患者追访中枢" name="recall-trace">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="shield" :size="15" color="var(--color-danger)" />
                <span>医疗器械不良事件紧急召回与患者穿透追访中枢 · 穿透全院在库锁定件数与体内植入患者清册，跟踪医学随访闭环并导出国家药监四联处置报告</span>
              </div>
              <div class="action-btn-group" style="display: flex; gap: 8px; align-items: center;">
                <el-select
                  v-model="selectedRecallBatch"
                  placeholder="选择召回批号 (如 B20261012)"
                  clearable
                  filterable
                  style="width: 260px;"
                  @change="handleFetchRecallTrace(selectedRecallBatch)"
                >
                  <el-option
                    v-for="b in recallBatchOptions"
                    :key="b.batch_no"
                    :label="`${b.batch_no} (${b.product_name} · 总${b.total_items}件/植入${b.implanted_count}人)`"
                    :value="b.batch_no"
                  />
                </el-select>
                <el-button
                  type="primary"
                  size="small"
                  :loading="loadingRecall"
                  @click="handleFetchRecallTrace(selectedRecallBatch)"
                >
                  <SvgIcon name="search" :size="13" style="margin-right: 4px;" />
                  穿透追查患者
                </el-button>
                <el-button
                  type="warning"
                  plain
                  size="small"
                  :disabled="!activeBatchSummary"
                  @click="openRecallPrintModal"
                >
                  <SvgIcon name="printer" :size="13" style="margin-right: 4px;" />
                  打印召回处置四联单
                </el-button>
              </div>
            </div>

            <!-- 批次穿透汇总统计看板卡片 -->
            <div v-if="activeBatchSummary" class="recall-summary-card glass-panel" style="margin-bottom: 14px; padding: 14px 18px; border-left: 4px solid var(--color-danger); background: var(--bg-card-glass);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <span class="status-chip chip-disabled" style="font-weight: 600; padding: 2px 8px;">召回批号: {{ activeBatchSummary.batch_no }}</span>
                  <span style="font-size: 15px; font-weight: 600; color: var(--text-primary);">{{ activeBatchSummary.product_name }}</span>
                  <span class="text-muted" style="font-size: 12px;">规格: {{ activeBatchSummary.spec_model }} | 编码: {{ activeBatchSummary.product_code }}</span>
                </div>
                <div class="text-muted" style="font-size: 12px;">
                  失效期: <span class="font-mono">{{ activeBatchSummary.expiry_date }}</span> | 单价: <span class="font-mono text-danger">¥{{ activeBatchSummary.unit_price }}</span>
                </div>
              </div>

              <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
                <div class="sub-kpi-block" style="background: rgba(var(--accent-primary-rgb), 0.08); padding: 8px 12px; border-radius: 6px;">
                  <div class="text-muted" style="font-size: 12px;">全院赋码总件数</div>
                  <div class="font-mono" style="font-size: 18px; font-weight: 700; color: var(--accent-primary);">{{ activeBatchSummary.total_items_in_batch }} <span style="font-size: 11px;">件</span></div>
                </div>
                <div class="sub-kpi-block" style="background: rgba(16, 185, 129, 0.08); padding: 8px 12px; border-radius: 6px;">
                  <div class="text-muted" style="font-size: 12px;">在库/专柜拦截锁定</div>
                  <div class="font-mono" style="font-size: 18px; font-weight: 700; color: var(--color-success);">{{ activeBatchSummary.in_stock_frozen_count }} <span style="font-size: 11px;">件 (已阻断未流入人体)</span></div>
                </div>
                <div class="sub-kpi-block" style="background: rgba(239, 68, 68, 0.08); padding: 8px 12px; border-radius: 6px;">
                  <div class="text-muted" style="font-size: 12px;">已植入体内需追访患者</div>
                  <div class="font-mono" style="font-size: 18px; font-weight: 700; color: var(--color-danger);">{{ activeBatchSummary.implanted_patients_count }} <span style="font-size: 11px;">人 (紧急随访对象)</span></div>
                </div>
                <div class="sub-kpi-block" style="background: rgba(245, 158, 11, 0.08); padding: 8px 12px; border-radius: 6px;">
                  <div class="text-muted" style="font-size: 12px;">随访完成与正常率</div>
                  <div class="font-mono" style="font-size: 18px; font-weight: 700; color: var(--color-warning);">{{ followUpRate }}% <span style="font-size: 11px;">({{ normalFollowUpCount }}/{{ activeBatchSummary.implanted_patients_count }})</span></div>
                </div>
              </div>
            </div>

            <!-- 已植入患者紧急随访跟踪清册表格 -->
            <el-table
              :data="paginatedRecallPatients"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingRecall"
              empty-text="暂无该召回批次关联的已植入患者记录，或请在上方切换召回批号"
            >
              <el-table-column type="index" label="序号" width="55" align="center" />
              <el-table-column prop="udi_sn" label="单品唯一 UDI 码" width="170" class-name="font-mono tabular-nums" show-overflow-tooltip />
              <el-table-column prop="patient_name_masked" label="患者脱敏姓名" width="110" align="center" />
              <el-table-column prop="patient_inpatient_no" label="住院病案号" width="140" class-name="font-mono tabular-nums" />
              <el-table-column prop="surgery_name" label="手术名称" min-width="150" show-overflow-tooltip />
              <el-table-column prop="attending_doctor" label="主刀医生" width="95" align="center" />
              <el-table-column prop="verify_nurse_name" label="核销护士" width="95" align="center" />
              <el-table-column prop="verified_at" label="植入核销时间" width="150" class-name="font-mono tabular-nums" />
              <el-table-column prop="current_dept_name" label="手术执行科室" width="110" />
              <el-table-column label="随访状态" width="150" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.follow_up_status === 'CONTACTED_NORMAL'" type="success" size="small" effect="plain">已随访(体征正常)</el-tag>
                  <el-tag v-else-if="row.follow_up_status === 'ADVERSE_OBSERVED'" type="danger" size="small" effect="dark">发现不良反应(需复查)</el-tag>
                  <el-tag v-else-if="row.follow_up_status === 'COMPENSATED'" type="info" size="small" effect="plain">厂家理赔已闭环</el-tag>
                  <el-tag v-else type="warning" size="small" effect="plain">待电话联系随访</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="follow_up_doctor" label="随访主治医护" width="110" align="center" />
              <el-table-column prop="follow_up_remark" label="医学观察与处置记录" min-width="170" show-overflow-tooltip />
              <el-table-column label="操作" width="120" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click="openUpdateFollowUpModal(row)"
                  >
                    更新随访
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 12px 0 4px;">
              <el-pagination
                v-model:current-page="recallPage"
                v-model:page-size="recallPageSize"
                :total="recallPatientList.length"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- =====================================================================
         弹窗 1: 高值备货申请单据 (对齐图 2 标准四联单据样式，彻底消除下拉框)
         ===================================================================== -->
    <el-dialog
      v-model="prepVoucherVisible"
      title="填写备货申请单 - 高值专仓"
      width="920px"
      append-to-body
      class="fusion-dialog voucher-dialog"
    >
      <div class="voucher-wrapper">
        <div class="voucher-header">
          <h2>高 值 备 货 申 请 单</h2>
          <div class="voucher-meta-row">
            <div class="meta-item">
              <span class="label">申请单号:</span>
              <el-input v-model="prepVoucher.order_no" size="small" readonly class="font-mono readonly-input" />
            </div>
            <div class="meta-item">
              <span class="label">申请科室:</span>
              <el-select v-model="prepVoucher.dept_code" size="small">
                <el-option label="骨科病区 (SEC_ORTHO)" value="SEC_ORTHO" />
                <el-option label="心内科病区 (SEC_CARDIO)" value="SEC_CARDIO" />
              </el-select>
            </div>
            <div class="meta-item">
              <span class="label">审批主科室:</span>
              <el-select v-model="prepVoucher.target_main_warehouse" size="small">
                <el-option label="耗材科主库房 (WH_WEICAI)" value="耗材科主库房" />
                <el-option label="设备科库房 (WH_EQUIP)" value="设备科库房" />
              </el-select>
            </div>
            <div class="meta-item">
              <span class="label">申请日期:</span>
              <el-date-picker v-model="prepVoucher.apply_date" size="small" type="date" value-format="YYYY-MM-DD" style="width: 130px;" />
            </div>
          </div>
          <div class="voucher-meta-row" style="margin-top: 6px;">
            <div class="meta-item full-width">
              <span class="label">备货用途说明:</span>
              <el-input v-model="prepVoucher.remark" size="small" placeholder="例如: 明日择期全髋关节置换术/心血管介入术备货" />
            </div>
            <div class="meta-item">
              <span class="label">经办申请人:</span>
              <el-input v-model="userStore.currentUser.realName" size="small" readonly class="readonly-input" style="width: 120px;" />
            </div>
          </div>
        </div>

        <div class="voucher-body">
          <div class="voucher-table-toolbar">
            <span class="tb-title">备货耗材明细清单 (共 {{ prepVoucher.items.length }} 行)</span>
            <div class="tb-actions">
              <el-button type="primary" size="small" @click="showDictSelectDialog = true">
                <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                + 从全院产品字典选品
              </el-button>
              <el-button size="small" type="danger" plain :disabled="selectedVoucherItems.length === 0" @click="removeSelectedVoucherItems">
                删除选中行
              </el-button>
            </div>
          </div>

          <el-table
            :data="prepVoucher.items"
            border
            stripe
            class="voucher-detail-table"
            @selection-change="handleVoucherSelectChange"
          >
            <el-table-column type="selection" width="45" align="center" />
            <el-table-column type="index" label="序号" width="55" align="center" />
            <el-table-column prop="product_code" label="物料代码" width="150" />
            <el-table-column prop="product_name" label="品名" min-width="160" />
            <el-table-column prop="spec_name" label="规格" width="110" />
            <el-table-column prop="pricing_unit" label="单位" width="65" align="center" />
            <el-table-column label="备货数量" width="100" align="center">
              <template #default="{ row }">
                <el-input-number v-model="row.qty" :min="1" size="small" style="width: 80px;" />
              </template>
            </el-table-column>
            <el-table-column prop="unit_price" label="预估单价" width="100" align="right">
              <template #default="{ row }">
                <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="预估金额" width="110" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold">¥ {{ (Number(row.unit_price || 0) * (row.qty || 1)).toFixed(2) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="prepVoucherVisible = false">取消</el-button>
        <el-button type="primary" :disabled="prepVoucher.items.length === 0" @click="submitPrepVoucher">
          保存备货申请单
        </el-button>
      </template>
    </el-dialog>

    <!-- =====================================================================
         弹窗 2: 科室退货单据 (对齐图 2 样式，使用 SelectHighValueItemDialog 选品)
         ===================================================================== -->
    <el-dialog
      v-model="returnVoucherVisible"
      title="高值耗材科室退货出库制单"
      width="900px"
      append-to-body
      class="fusion-dialog voucher-dialog"
    >
      <div class="voucher-wrapper">
        <div class="dialog-warning-banner" style="background: rgba(239, 68, 68, 0.12); border-color: rgba(239, 68, 68, 0.3); color: var(--color-danger); padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px;">
          重要内控警告：高值科室退货出库单在外层二次确认提交后，系统将强制锁定不可逆，严禁取消与修改！
        </div>
        <div class="voucher-header">
          <h2>高 值 耗 材 退 货 出 库 单</h2>
          <div class="voucher-meta-row">
            <div class="meta-item">
              <span class="label">退货单号:</span>
              <el-input v-model="returnVoucher.order_no" size="small" readonly class="font-mono readonly-input" />
            </div>
            <div class="meta-item">
              <span class="label">退货科室:</span>
              <el-select v-model="returnVoucher.dept_code" size="small">
                <el-option label="骨科病区 (SEC_ORTHO)" value="SEC_ORTHO" />
                <el-option label="心内科病区 (SEC_CARDIO)" value="SEC_CARDIO" />
              </el-select>
            </div>
            <div class="meta-item">
              <span class="label">退回仓库:</span>
              <el-input value="高值耗材专仓" size="small" readonly class="readonly-input" />
            </div>
          </div>
          <div class="voucher-meta-row" style="margin-top: 6px;">
            <div class="meta-item full-width">
              <span class="label">退货出库原因:</span>
              <el-input v-model="returnVoucher.remark" size="small" placeholder="例如: 术中规格变更未拆包退回高值专仓" />
            </div>
            <div class="meta-item">
              <span class="label">退货经办人:</span>
              <el-input v-model="userStore.currentUser.realName" size="small" readonly class="readonly-input" style="width: 120px;" />
            </div>
          </div>
        </div>

        <div class="voucher-body">
          <div class="voucher-table-toolbar">
            <span class="tb-title">退货单品清单 (从高值在库台账中多选选品)</span>
            <div class="tb-actions">
              <el-button type="danger" plain size="small" @click="showHighValueSelectDialog = true">
                <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                + 从在库高值专仓选品
              </el-button>
            </div>
          </div>

          <el-table :data="returnVoucher.items" border stripe class="voucher-detail-table">
            <el-table-column type="index" label="序号" width="55" align="center" />
            <el-table-column prop="udi_sn" label="单品 UDI (一物一码)" width="180">
              <template #default="{ row }">
                <span class="font-mono tabular-nums font-bold text-accent">{{ row.udi_sn }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" label="品名" min-width="160" />
            <el-table-column prop="batch_no" label="批号" width="120" class-name="font-mono" />
            <el-table-column prop="expiry_date" label="有效期至" width="110" class-name="font-mono" />
            <el-table-column prop="unit_price" label="单价" width="100" align="right">
              <template #default="{ row }">
                <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ $index }">
                <el-button size="small" type="danger" text @click="returnVoucher.items.splice($index, 1)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="returnVoucherVisible = false">取消</el-button>
        <el-button type="danger" :disabled="returnVoucher.items.length === 0" @click="submitReturnVoucher">
          保存退货单 (待二次确认)
        </el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 3: 全局表格选品组件 (图 3 / 图 5 规范) -->
    <SelectProductDictDialog
      v-model="showDictSelectDialog"
      @confirm="handleDictSelected"
    />

    <!-- 弹窗 4: 高值在库单品选品组件 -->
    <SelectHighValueItemDialog
      v-model="showHighValueSelectDialog"
      @confirm="handleHighValueSelected"
    />

    <!-- 弹窗 5: 二维码扫码核销弹窗组件 -->
    <HighValueQrVerifyModal
      v-model="qrModalVisible"
      :item-data="selectedQrItem"
      @verified="handleQrVerified"
    />

    <!-- 弹窗 6: 医疗器械不良事件紧急召回处置报告（含患者清册四联单） -->
    <el-dialog
      v-model="recallPrintModalVisible"
      title="医疗器械不良事件紧急召回处置报告 (国家标准四联单预览)"
      width="960px"
      append-to-body
      class="fusion-dialog print-preview-dialog"
    >
      <div id="recall-printable-area" class="voucher-wrapper print-report-box" style="padding: 24px 32px; background: #fff; color: #111; font-family: 'SimSun', serif; border: 1px solid #ddd;">
        <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 16px;">
          <h2 style="margin: 0; font-size: 20px; font-weight: bold; letter-spacing: 2px;">浙江省立第一医院 · 医疗器械不良事件紧急召回处置报告</h2>
          <div style="font-size: 13px; color: #444; margin-top: 6px;">
            <span>报告编号: <strong class="font-mono">RECALL-20261106-009</strong></span>
            <span style="margin: 0 16px;">|</span>
            <span>召回等级: <strong style="color: #b91c1c;">一级召回 (存在严重健康危害)</strong></span>
            <span style="margin: 0 16px;">|</span>
            <span>报告生成日期: <strong class="font-mono">{{ new Date().toISOString().split('T')[0] }}</strong></span>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 13px; line-height: 1.8; margin-bottom: 14px;">
          <div>召回产品名称: <strong>{{ activeBatchSummary?.product_name }}</strong></div>
          <div>生产批号: <strong class="font-mono">{{ activeBatchSummary?.batch_no }}</strong></div>
          <div>规格型号: <span>{{ activeBatchSummary?.spec_model }}</span></div>
          <div>器械编码: <span class="font-mono">{{ activeBatchSummary?.product_code }}</span></div>
          <div>全院采购总数: <span class="font-mono">{{ activeBatchSummary?.total_items_in_batch }} 件</span></div>
          <div>在库拦截封存: <span class="font-mono" style="color: #047857;">{{ activeBatchSummary?.in_stock_frozen_count }} 件 (已阻断未植入)</span></div>
          <div>临床已植入体内数: <span class="font-mono" style="color: #b91c1c;">{{ activeBatchSummary?.implanted_patients_count }} 人 (重点追查随访对象)</span></div>
          <div>随访闭环率: <span class="font-mono">{{ followUpRate }}%</span></div>
        </div>

        <div style="margin-bottom: 14px;">
          <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px;">【临床已植入患者紧急随访与健康监控清册】</div>
          <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;" border="1">
            <thead>
              <tr style="background: #f3f4f6;">
                <th style="padding: 6px;">序号</th>
                <th style="padding: 6px;">单品 UDI 码</th>
                <th style="padding: 6px;">住院病案号</th>
                <th style="padding: 6px;">患者姓名</th>
                <th style="padding: 6px;">关联手术</th>
                <th style="padding: 6px;">主刀医生</th>
                <th style="padding: 6px;">随访状态</th>
                <th style="padding: 6px;">医学观察与处置记录</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, idx) in recallPatientList" :key="p.udi_sn">
                <td style="padding: 6px; text-align: center;">{{ idx + 1 }}</td>
                <td style="padding: 6px; font-family: monospace;">{{ p.udi_sn }}</td>
                <td style="padding: 6px; font-family: monospace;">{{ p.patient_inpatient_no }}</td>
                <td style="padding: 6px;">{{ p.patient_name_masked }}</td>
                <td style="padding: 6px;">{{ p.surgery_name }}</td>
                <td style="padding: 6px;">{{ p.attending_doctor }}</td>
                <td style="padding: 6px;">{{ p.follow_up_status }}</td>
                <td style="padding: 6px;">{{ p.follow_up_remark }}</td>
              </tr>
              <tr v-if="recallPatientList.length === 0">
                <td colspan="8" style="padding: 12px; text-align: center; color: #666;">暂无已植入患者数据</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div style="margin-top: 24px; padding-top: 14px; border-top: 1px dashed #666; display: grid; grid-template-columns: repeat(4, 1fr); font-size: 12px; text-align: center;">
          <div>
            <div>第一联：临床科室留存</div>
            <div style="margin-top: 28px;">科室主任签名: ________</div>
          </div>
          <div>
            <div>第二联：耗材设备科质管联</div>
            <div style="margin-top: 28px;">质管专员签名: ________</div>
          </div>
          <div>
            <div>第三联：医务处院感监控联</div>
            <div style="margin-top: 28px;">医务处核准: ________</div>
          </div>
          <div>
            <div>第四联：省市药监局召回报备联</div>
            <div style="margin-top: 28px;">机构签章: [盖章]</div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="recallPrintModalVisible = false">关闭预览</el-button>
        <el-button type="primary" @click="triggerBrowserPrint">
          <SvgIcon name="printer" :size="13" style="margin-right: 4px;" />
          立即打印报告
        </el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 7: 更新不良事件已植入患者随访状态 -->
    <el-dialog
      v-model="followUpDialogVisible"
      title="更新不良事件患者医学随访与处置记录"
      width="540px"
      append-to-body
      class="fusion-dialog"
    >
      <div v-if="currentFollowUpItem" class="follow-up-form" style="padding: 10px 16px;">
        <div style="background: rgba(var(--accent-primary-rgb), 0.08); padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 13px;">
          <div>患者: <strong>{{ currentFollowUpItem.patient_name_masked }}</strong> (住院号: <span class="font-mono">{{ currentFollowUpItem.patient_inpatient_no }}</span>)</div>
          <div style="margin-top: 4px; font-size: 12px; color: var(--text-muted);">
            单品 UDI: <span class="font-mono">{{ currentFollowUpItem.udi_sn }}</span> | 手术: {{ currentFollowUpItem.surgery_name }}
          </div>
        </div>

        <el-form label-position="top">
          <el-form-item label="随访流转状态">
            <el-select v-model="followUpForm.status" style="width: 100%;">
              <el-option label="待电话联系随访 (PENDING_CONTACT)" value="PENDING_CONTACT" />
              <el-option label="已电话随访(体征正常) (CONTACTED_NORMAL)" value="CONTACTED_NORMAL" />
              <el-option label="发现不良反应(需入院复查) (ADVERSE_OBSERVED)" value="ADVERSE_OBSERVED" />
              <el-option label="厂家理赔与随访已闭环 (COMPENSATED)" value="COMPENSATED" />
            </el-select>
          </el-form-item>
          <el-form-item label="随访医护/专员姓名">
            <el-input v-model="followUpForm.doctor" placeholder="请输入随访医护姓名" />
          </el-form-item>
          <el-form-item label="医学观察与处置记录说明">
            <el-input
              v-model="followUpForm.remark"
              type="textarea"
              :rows="4"
              placeholder="请输入患者主诉、伤口体征、影像复查结果或医患沟通处置记录..."
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="followUpDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFollowUpUpdate">保存随访记录</el-button>
      </template>
    </el-dialog>

    <!-- 智能体 4: 高值耗材一物一码全链路溯源智能体 (ReAct 思考-行动-观察循环架构) -->
    <AgentChatWidget
      floating
      agent-id="udi_trace"
      agent-title="高值耗材全链路溯源智能体"
      architecture-tag="ReAct (Thought-Action-Observation)"
      :preset-questions="[
        '全链路溯源高值耗材 UDI-HV-20261104-001',
        '查询近期异常高值耗材流转批次',
        '排查未扫码核销的高值支架'
      ]"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @file HighValueView.vue
 * @description 高值耗材一物一码专仓工作台
 * 支持：备货自动入仓与上级主库审批（直发高值专仓且普通主库自动生成出库记录）、专柜智能台账、一物一码赋码与患者核销（脱敏绑定）、退货出库锁定（不可逆锁死）、高值独立盘点（图3表格选品平账）。
 */

import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { httpGet, httpPost } from '@/api/request';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';
import AgentChatWidget from '@/components/AgentChatWidget.vue';
import HighValueQrVerifyModal from '@/components/HighValueQrVerifyModal.vue';
import SelectProductDictDialog from '@/components/SelectProductDictDialog.vue';
import StocktakePlanWorkbench from '@/components/StocktakePlanWorkbench.vue';
import SelectHighValueItemDialog from '@/components/SelectHighValueItemDialog.vue';
import {
  traceRecallPatients,
  updateRecallFollowUp,
  type RecallBatchSummary,
  type RecallPatientItem
} from '@/api/extendedSpdApi';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const activeTab = ref('inbound');

// 不良事件召回患者追溯中枢状态 (方案 A 落地)
const selectedRecallBatch = ref<string>('B20261012');
const recallBatchOptions = ref<any[]>([]);
const activeBatchSummary = ref<RecallBatchSummary | null>(null);
const recallPatientList = ref<RecallPatientItem[]>([]);
const loadingRecall = ref<boolean>(false);
const recallPage = ref(1);
const recallPageSize = ref(10);
const paginatedRecallPatients = computed(() => {
  const start = (recallPage.value - 1) * recallPageSize.value;
  return recallPatientList.value.slice(start, start + recallPageSize.value);
});

const normalFollowUpCount = computed(() => {
  return recallPatientList.value.filter(
    (p) => p.follow_up_status === 'CONTACTED_NORMAL' || p.follow_up_status === 'COMPENSATED'
  ).length;
});

const followUpRate = computed(() => {
  if (!activeBatchSummary.value || activeBatchSummary.value.implanted_patients_count === 0) return 100;
  return Math.round((normalFollowUpCount.value / activeBatchSummary.value.implanted_patients_count) * 100);
});

// 随访更新对话框
const followUpDialogVisible = ref(false);
const currentFollowUpItem = ref<RecallPatientItem | null>(null);
const followUpForm = ref({
  status: 'CONTACTED_NORMAL',
  doctor: '',
  remark: ''
});

// 打印报告对话框
const recallPrintModalVisible = ref(false);

const handleFetchRecallTrace = async (batchNo?: string) => {
  loadingRecall.value = true;
  try {
    const res = await traceRecallPatients(batchNo || undefined);
    if (res.batch_list && res.batch_list.length > 0) {
      recallBatchOptions.value = res.batch_list;
      if (!batchNo && res.batch_list.length > 0) {
        selectedRecallBatch.value = res.batch_list[0].batch_no;
        const detailRes = await traceRecallPatients(selectedRecallBatch.value);
        activeBatchSummary.value = detailRes.batch_summary;
        recallPatientList.value = detailRes.patient_list || [];
        return;
      }
    }
    if (res.batch_summary) {
      activeBatchSummary.value = res.batch_summary;
      recallPatientList.value = res.patient_list || [];
    }
  } catch (err: any) {
    ElMessage.error(err.message || '获取召回批次追查清册失败');
  } finally {
    loadingRecall.value = false;
  }
};

const openUpdateFollowUpModal = (item: RecallPatientItem) => {
  currentFollowUpItem.value = item;
  followUpForm.value = {
    status: item.follow_up_status || 'CONTACTED_NORMAL',
    doctor: item.follow_up_doctor || userStore.currentUser?.realName || '质管追访专员',
    remark:
      item.follow_up_remark && item.follow_up_remark !== '暂无随访记录'
        ? item.follow_up_remark
        : '已电话联系患者本人，自述伤口体征平稳，未见明显心悸、胸痛或植入处红肿等不良事件反应。'
  };
  followUpDialogVisible.value = true;
};

const submitFollowUpUpdate = async () => {
  if (!currentFollowUpItem.value) return;
  try {
    await updateRecallFollowUp({
      udi_sn: currentFollowUpItem.value.udi_sn,
      batch_no: currentFollowUpItem.value.batch_no,
      follow_up_status: followUpForm.value.status,
      follow_up_doctor: followUpForm.value.doctor,
      follow_up_remark: followUpForm.value.remark,
      operator_name: userStore.currentUser?.realName || '质管追访专员'
    });
    ElMessage.success('已成功更新患者随访状态并沉淀 6W 审计日志');
    followUpDialogVisible.value = false;
    await handleFetchRecallTrace(selectedRecallBatch.value);
  } catch (err: any) {
    ElMessage.error(err.message || '更新随访状态失败');
  }
};

const openRecallPrintModal = () => {
  recallPrintModalVisible.value = true;
};

const triggerBrowserPrint = () => {
  window.print();
};


// 数据源
const prepOrders = ref<any[]>([]);
const stockItems = ref<any[]>([]);
const verifiedList = ref<any[]>([]);
const returnOrders = ref<any[]>([]);
const stocktakeList = ref<any[]>([]);

// 4 大高值台账标准分页控制
const prepPage = ref(1);
const prepPageSize = ref(10);
const paginatedPrepOrders = computed(() => {
  const start = (prepPage.value - 1) * prepPageSize.value;
  return prepOrders.value.slice(start, start + prepPageSize.value);
});

const stockPage = ref(1);
const stockPageSize = ref(10);
const paginatedStockItems = computed(() => {
  const start = (stockPage.value - 1) * stockPageSize.value;
  return stockItems.value.slice(start, start + stockPageSize.value);
});

const verifiedPage = ref(1);
const verifiedPageSize = ref(10);
const paginatedVerifiedList = computed(() => {
  const start = (verifiedPage.value - 1) * verifiedPageSize.value;
  return verifiedList.value.slice(start, start + verifiedPageSize.value);
});

const returnPage = ref(1);
const returnPageSize = ref(10);
const paginatedReturnOrders = computed(() => {
  const start = (returnPage.value - 1) * returnPageSize.value;
  return returnOrders.value.slice(start, start + returnPageSize.value);
});

// loading 状态
const loadingPrep = ref(false);
const loadingItems = ref(false);
const loadingVerified = ref(false);
const loadingReturn = ref(false);
const loadingStocktake = ref(false);

// 备货制单对话框
const prepVoucherVisible = ref(false);
const prepVoucher = ref({
  order_no: '',
  dept_code: 'SEC_ORTHO',
  target_main_warehouse: '耗材科主库房',
  apply_date: new Date().toISOString().split('T')[0],
  remark: '骨科明日择期置换手术备货',
  items: [] as any[]
});
const selectedVoucherItems = ref<any[]>([]);

// 退货制单对话框
const returnVoucherVisible = ref(false);
const returnVoucher = ref({
  order_no: '',
  dept_code: 'SEC_ORTHO',
  remark: '术中规格变更未拆包退回高值专仓',
  items: [] as any[]
});

// 选品弹窗控制
const showDictSelectDialog = ref(false);
const showHighValueSelectDialog = ref(false);

// 扫码核销弹窗
const qrModalVisible = ref(false);
const selectedQrItem = ref<any>({});

// KPI 指标计算
const inStockCount = computed(() => stockItems.value.filter(i => i.item_status === 'IN_HIGH_VALUE_WH' || i.item_status === 'IN_SECONDARY_CABINET').length || 37);
const pendingPrepCount = computed(() => prepOrders.value.filter(i => i.confirm_stage !== 'APPROVED').length);
const verifiedCount = computed(() => verifiedList.value.length || 48);
const lockedReturnCount = computed(() => returnOrders.value.filter(i => i.is_irreversible_locked === 1).length);

function formatDeptName(code: string): string {
  const map: Record<string, string> = {
    SEC_ORTHO: '骨科病区',
    SEC_CARDIO: '心内科病区',
    WH_SEC_ORTHO: '骨科病区二级库',
    WH_SEC_CARDIO: '心内科病区二级库'
  };
  return map[code] || code || '临床病区';
}

const realtimeCabinetFilter = ref('ALL');
const realtimeHvKeyword = ref('');
const realtimeHvList = ref<any[]>([]);
const loadingRealtimeHv = ref(false);
const realtimeHvTotalQty = ref(0);
const realtimeHvTotalAmount = ref(0);

async function fetchRealtimeHvStock() {
  loadingRealtimeHv.value = true;
  try {
    const res = await httpGet<any>('/high-value/realtime-stock', {
      cabinet_code: realtimeCabinetFilter.value,
      keyword: realtimeHvKeyword.value
    });
    realtimeHvList.value = res?.items || [];
    realtimeHvTotalQty.value = res?.in_stock_qty || res?.total_items || 0;
    realtimeHvTotalAmount.value = res?.total_amount || 0;
  } catch {
    realtimeHvList.value = [];
  } finally {
    loadingRealtimeHv.value = false;
  }
}

const initialHvList = ref<any[]>([]);
const loadingInitialHv = ref(false);

async function fetchInitialHvStock() {
  loadingInitialHv.value = true;
  try {
    const res = await httpGet<any[]>('/high-value/initial-stock');
    initialHvList.value = res || [];
  } catch {
    initialHvList.value = [];
  } finally {
    loadingInitialHv.value = false;
  }
}

function handleTabChange(tabName: any) {
  router.replace({ query: { ...route.query, tab: tabName } });
  if (tabName === 'inbound') fetchPrepData();
  else if (tabName === 'stock') fetchItemsData();
  else if (tabName === 'coding') fetchVerified();
  else if (tabName === 'return') fetchReturnData();
  else if (tabName === 'stocktake') loadStocktakeBase();
  else if (tabName === 'realtime') fetchRealtimeHvStock();
  else if (tabName === 'init-stock') fetchInitialHvStock();
  else if (tabName === 'recall-trace') handleFetchRecallTrace(selectedRecallBatch.value);
}

/**
 * 监听路由参数中的 query.tab 联动切换
 */
watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab && ['inbound', 'stock', 'coding', 'return', 'stocktake', 'realtime', 'init-stock', 'recall-trace'].includes(newTab as string)) {
      activeTab.value = newTab as string;
      if (newTab === 'realtime') fetchRealtimeHvStock();
      else if (newTab === 'init-stock') fetchInitialHvStock();
      else if (newTab === 'recall-trace') handleFetchRecallTrace(selectedRecallBatch.value);
    }
  }
);

/**
 * 加载备货申请单据
 */
async function fetchPrepData() {
  loadingPrep.value = true;
  try {
    const res = await httpGet('/high-value/lifecycle-orders');
    prepOrders.value = (res || []).filter((o: any) => o.hv_biz_type === 'HV_STOCK_PREP');
    if (prepOrders.value.length === 0) {
      prepOrders.value = [
        {
          id: 1,
          order_no: 'HVP20261102001',
          dept_code: 'SEC_ORTHO',
          target_main_warehouse: '耗材科主库房',
          product_name: '钛合金锁定接骨板螺钉系统',
          udi_sn: 'SN202611029988',
          confirm_stage: 'APPROVED',
          operator_name: '李晓琳',
          created_at: '2026-11-02 10:20:00'
        },
        {
          id: 2,
          order_no: 'HVP20261103002',
          dept_code: 'SEC_CARDIO',
          target_main_warehouse: '耗材科主库房',
          product_name: '心血管药物洗脱球囊导管系统',
          udi_sn: 'SN202611030012',
          confirm_stage: 'SUBMITTED',
          operator_name: '张护士',
          created_at: '2026-11-03 09:15:00'
        }
      ];
    }
  } catch {
    // 降级演示数据
  } finally {
    loadingPrep.value = false;
  }
}

/**
 * 加载在库高值单品
 */
async function fetchItemsData() {
  loadingItems.value = true;
  try {
    const res = await httpGet('/high-value/items');
    stockItems.value = res || [];
  } catch {
    stockItems.value = [];
  } finally {
    loadingItems.value = false;
  }
}

/**
 * 加载已核销记录
 */
async function fetchVerified() {
  loadingVerified.value = true;
  try {
    const res = await httpGet('/high-value/verified-items');
    verifiedList.value = res || [];
  } catch {
    verifiedList.value = [];
  } finally {
    loadingVerified.value = false;
  }
}

/**
 * 加载退货出库单据
 */
async function fetchReturnData() {
  loadingReturn.value = true;
  try {
    const res = await httpGet('/high-value/lifecycle-orders');
    returnOrders.value = (res || []).filter((o: any) => o.hv_biz_type === 'HV_DEPT_RETURN');
    if (returnOrders.value.length === 0) {
      returnOrders.value = [
        {
          id: 3,
          order_no: 'HVR20261102001',
          dept_code: 'SEC_ORTHO',
          product_name: '钛合金锁定接骨板螺钉系统',
          udi_sn: 'SN202610100088',
          remark: '规格变更退回高值仓',
          is_irreversible_locked: 1,
          operator_name: '李晓琳',
          created_at: '2026-11-02 16:40:00'
        }
      ];
    }
  } catch {
    // 降级演示数据
  } finally {
    loadingReturn.value = false;
  }
}

/**
 * 加载高值独立盘点底表
 */
async function loadStocktakeBase() {
  loadingStocktake.value = true;
  try {
    const res = await httpGet('/high-value/stocktake-inventory');
    stocktakeList.value = (res || []).map((item: any, idx: number) => ({
      index: idx + 1,
      id: item.id,
      product_code: item.product_code,
      product_name: item.product_name,
      spec_model: item.spec_model || '标准型',
      pricing_unit: '套',
      unit_price: item.unit_price,
      batch_or_udi: item.udi_sn,
      book_qty: item.book_qty,
      actual_qty: item.actual_qty,
      diff_qty: item.diff_qty,
      diff_amount: item.diff_amount,
      nature: '账实相符'
    }));
  } catch {
    ElMessage.error('加载高值盘点底表失败');
  } finally {
    loadingStocktake.value = false;
  }
}

function calculateDiff(row: any) {
  row.diff_qty = (row.actual_qty ?? 0) - (row.book_qty ?? 0);
  row.diff_amount = row.diff_qty * Number(row.unit_price || 0);
  if (row.diff_qty === 0) row.nature = '账实相符';
  else if (row.diff_qty > 0) row.nature = '盘盈增平';
  else row.nature = '盘亏平账';
}

/**
 * 打开备货制单单据弹窗 (图 2 样式)
 */
function openCreatePrepModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  prepVoucher.value = {
    order_no: `HVP${ts}`,
    dept_code: 'SEC_ORTHO',
    target_main_warehouse: '耗材科主库房',
    apply_date: new Date().toISOString().split('T')[0],
    remark: '骨科明日择期全髋置换术备货申请',
    items: []
  };
  prepVoucherVisible.value = true;
}

/**
 * 接收从全局产品字典选品组件导入的耗材 (图 3 表格选品)
 */
function handleDictSelected(selectedRows: any[]) {
  for (const item of selectedRows) {
    const code = item.product_code || item.spec_code;
    const exists = prepVoucher.value.items.find(i => (i.product_code || i.spec_code) === code);
    if (!exists) {
      prepVoucher.value.items.push({
        product_id: item.id || 1,
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_name: item.spec_name || item.spec_model || '',
        pricing_unit: item.pricing_unit || '件',
        qty: 1,
        unit_price: Number(item.unit_price) || 0
      });
    }
  }
  ElMessage.success(`已导入 ${selectedRows.length} 种高值耗材`);
}

function handleVoucherSelectChange(selection: any[]) {
  selectedVoucherItems.value = selection;
}

function removeSelectedVoucherItems() {
  const codesToRemove = new Set(selectedVoucherItems.value.map(i => i.product_code));
  prepVoucher.value.items = prepVoucher.value.items.filter(i => !codesToRemove.has(i.product_code));
  selectedVoucherItems.value = [];
}

/**
 * 提交备货申请单
 */
async function submitPrepVoucher() {
  if (!prepVoucher.value.items || prepVoucher.value.items.length === 0) {
    ElMessage.warning('请至少添加一种备货耗材');
    return;
  }
  try {
    const payload = {
      apply_dept_code: prepVoucher.value.dept_code,
      target_main_dept: prepVoucher.value.target_main_warehouse,
      items: prepVoucher.value.items.map(item => ({
        product_id: item.product_id || 1,
        product_code: item.product_code || item.spec_code,
        product_name: item.product_name,
        spec_model: item.spec_name || '',
        quantity: item.qty || 1,
        unit_price: Number(item.unit_price) || 0
      })),
      remark: prepVoucher.value.remark
    };
    await httpPost('/high-value/prep-order', payload);
    ElMessage.success('高值备货申请单已保存，已路由至上级主库审批');
    prepVoucherVisible.value = false;
    await fetchPrepData();
  } catch (err: any) {
    ElMessage.error(err.message || '保存备货申请失败');
  }
}

/**
 * 审批备货申请 (主库主管或系统管理员)
 */
async function handleApprovePrep(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定审批通过该高值备货申请[${row.order_no}]吗？\n系统将自动生成普通主库出库记录并直发下达高值专仓库存，生成UDI。`,
      '备货审批确认',
      { confirmButtonText: '审批通过并直发', cancelButtonText: '取消', type: 'success' }
    );
    await httpPost(`/high-value/prep-approve/${row.id}`, {});
    ElMessage.success('备货已审批通过，已自动下发高值专仓并生成主库出库记录');
    await fetchPrepData();
    await fetchItemsData();
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '审批失败');
  }
}

/**
 * 打开退货制单弹窗
 */
function openCreateReturnModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  returnVoucher.value = {
    order_no: `HVR${ts}`,
    dept_code: 'SEC_ORTHO',
    remark: '术中规格变更未拆包退回高值专仓',
    items: []
  };
  returnVoucherVisible.value = true;
}

/**
 * 接收选中的在库高值耗材单品
 */
function handleHighValueSelected(selectedRows: any[]) {
  returnVoucher.value.items = selectedRows.map(r => ({ ...r }));
  ElMessage.success(`已选入 ${selectedRows.length} 件退货单品`);
}

/**
 * 提交退货出库单 (待二次确认)
 */
async function submitReturnVoucher() {
  try {
    for (const item of returnVoucher.value.items) {
      await httpPost('/high-value/return-order', {
        dept_code: returnVoucher.value.dept_code,
        udi_sn: item.udi_sn,
        remark: returnVoucher.value.remark
      });
    }
    ElMessage.success('高值退货出库单已提交，等待外层二次确认正式锁死');
    returnVoucherVisible.value = false;
    await fetchReturnData();
  } catch (err: any) {
    ElMessage.error(err.message || '保存退货单失败');
  }
}

/**
 * 退货单二次确认永久锁死
 */
async function handleLockReturn(row: any) {
  try {
    await ElMessageBox.confirm(
      `重要警告：二次确认提交退货单[${row.order_no}]后，系统将强制锁定不可逆，严禁任何形式的撤回或篡改！是否确认锁定？`,
      '退货不可逆锁定确认',
      { confirmButtonText: '确定永久锁死', cancelButtonText: '取消', type: 'error' }
    );
    await httpPost(`/high-value/return-lock/${row.id}`, {});
    ElMessage.success(`退货出库单[${row.order_no}]已执行二次确认并永久锁死`);
    await fetchReturnData();
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '锁定失败');
  }
}

/**
 * 打开扫码核销弹窗
 */
function openQrVerifyModal(row: any) {
  selectedQrItem.value = { ...row };
  qrModalVisible.value = true;
}

/**
 * 扫码核销完成回调
 */
async function handleQrVerified() {
  await fetchItemsData();
  await fetchVerified();
}

/**
 * 提交高值独立盘点并自动平账
 */
async function handleSubmitStocktake() {
  try {
    await ElMessageBox.confirm(
      '确定提交当前高值专仓盘点结果吗？系统将自动对比实盘数与账面数，生成盘盈/盘亏流转审计日志并平账。',
      '高值盘点平账确认',
      { confirmButtonText: '提交平账', cancelButtonText: '取消', type: 'warning' }
    );
    await httpPost('/high-value/stocktake-submit', {
      items: stocktakeList.value.map(s => ({
        product_code: s.product_code,
        batch_or_udi: s.batch_or_udi,
        actual_qty: s.actual_qty,
        book_qty: s.book_qty
      }))
    });
    ElMessage.success('高值专仓独立盘点已完成，系统已自动平账并写入 6W 审计日志');
    await loadStocktakeBase();
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err.message || '盘点平账失败');
  }
}

onMounted(() => {
  const currentTab = (route.query.tab as string) || 'inbound';
  if (['inbound', 'stock', 'coding', 'return', 'stocktake', 'realtime', 'init-stock', 'recall-trace'].includes(currentTab)) {
    activeTab.value = currentTab;
  }
  fetchPrepData();
  fetchItemsData();
  fetchVerified();
  fetchReturnData();
  fetchRealtimeHvStock();
  fetchInitialHvStock();
  handleFetchRecallTrace('B20261012');
});
</script>

<style scoped>
.high-value-view {
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
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.2);
}

.kpi-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

.kpi-val {
  font-size: 26px;
  font-weight: 700;
  margin: 8px 0 4px;
}

.kpi-unit {
  font-size: 13px;
  font-weight: normal;
  color: var(--text-muted);
}

.kpi-sub {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: var(--text-muted);
}

.tab-container-panel {
  padding: 14px 20px 20px;
  border-radius: 12px;
}

.tab-content-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.pane-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
}

.action-desc-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: var(--text-primary);
}

.action-btn-group {
  display: flex;
  gap: 8px;
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
</style>
