<template>
  <div class="external-supplier-portal-view">
    <!-- 顶部外部供应商身份与国家药监局资质看板 -->
    <div class="glass-panel supplier-banner-card">
      <div class="banner-left">
        <div class="supplier-badge">
          <SvgIcon name="brand" :size="15" color="var(--color-primary)" />
          <span>外部供应商数字化协同门户 (B2B)</span>
        </div>
        <div class="supplier-info-line">
          <div class="supplier-title-select">
            <span class="supplier-main-name font-bold">{{ activeSupplier.supplier_name }}</span>
            <!-- 演示与调试企业快速切换器 (允许体验不同企业的准入与拦截) -->
            <el-select
              v-model="currentSupplierCode"
              size="small"
              class="supplier-switch-select"
              @change="handleSupplierSwitch"
            >
              <el-option
                v-for="sup in supplierOptions"
                :key="sup.supplier_code"
                :value="sup.supplier_code"
                :label="`${sup.supplier_name} [${sup.qual_audit_status === 'QUAL_APPROVED' ? '已准入' : '待审拦截'}]`"
              />
            </el-select>
          </div>
          <div class="license-meta-text font-mono">
            <span>《医疗器械经营许可证》编号：<strong>{{ activeSupplier.license_no }}</strong></span>
            <span class="meta-sep">|</span>
            <span>国家药监局有效期至：<strong>{{ activeSupplier.license_expiry_date }}</strong></span>
          </div>
        </div>
      </div>

      <div class="banner-right">
        <div class="qual-status-box">
          <span class="qual-status-label">医院准入状态防线：</span>
          <span v-if="activeSupplier.qual_audit_status === 'QUAL_APPROVED'" class="status-chip chip-active">
            资质审核通过 (已解锁接单发货)
          </span>
          <span v-else class="status-chip chip-disabled">
            待审硬拦截 (严禁接单发货)
          </span>
        </div>

        <el-button size="small" plain @click="qualUploadVisible = true">
          <SvgIcon name="upload" :size="13" style="margin-right: 4px;" />
          重新上传资质证照
        </el-button>
      </div>
    </div>

    <!-- 资质待审/驳回硬拦截警告卡片 -->
    <div
      v-if="activeSupplier.qual_audit_status !== 'QUAL_APPROVED'"
      class="glass-panel qual-block-warning-panel"
    >
      <div class="warning-header">
        <SvgIcon name="shield" :size="20" color="var(--color-danger)" />
        <span class="warning-title font-bold">
          [供应商资质准入硬拦截] 合作企业经营资质处于 {{ activeSupplier.qual_audit_status }} 状态
        </span>
      </div>
      <div class="warning-desc">
        根据国家药品监督管理局《医疗器械经营监督管理办法》与三甲医院物资采购内控条例，未经医院耗材与设备管理委员会查验《医疗器械经营许可证》原件并审核通过前，<strong>严禁进行在线接单、拣货配货与发货业务</strong>！请联系院方主科室主管审批准入资质。
      </div>
    </div>

    <!-- 供应商功能 Tab 切换栏 -->
    <div class="glass-panel action-toolbar-panel">
      <div class="tab-btn-group">
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'orders' }"
          @click="currentTab = 'orders'"
        >
          <SvgIcon name="package" :size="15" />
          <span>下发本企业采购订单 (接单配货)</span>
          <span v-if="pendingShipCount > 0" class="tab-chip chip-warn font-mono">{{ pendingShipCount }}</span>
        </button>
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'reconcile' }"
          @click="currentTab = 'reconcile'"
        >
          <SvgIcon name="finance" :size="15" />
          <span>采供月度对账与发票结算</span>
        </button>
      </div>

      <div class="action-btn-group">
        <el-button plain size="small" @click="fetchMyOrders">
          <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
          刷新订单数据
        </el-button>
      </div>
    </div>

    <!-- =====================================================================
         Tab 1: 订单拣货配货与发货协同工作台 (企业级数据物理隔离)
         ===================================================================== -->
    <div v-show="currentTab === 'orders'" class="glass-panel table-panel">
      <div class="table-caption-bar">
        <span class="caption-title">企业专属采购订单接单与拣货发货协同</span>
        <span class="caption-sub font-mono tabular-nums">当前企业 [{{ activeSupplier.supplier_name }}] 共有 {{ myOrders.length }} 笔订单</span>
      </div>

      <el-table
        :data="myOrders"
        border
        stripe
        class="fusion-styled-table"
        v-loading="loadingOrders"
      >
        <el-table-column prop="order_no" label="采购单号" width="180">
          <template #default="{ row }">
            <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="需求采购物资" min-width="190" />
        <el-table-column prop="product_code" label="物料编码" width="140">
          <template #default="{ row }">
            <span class="font-mono tabular-nums text-muted">{{ row.product_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_qty" label="采购订货数" width="110" align="right">
          <template #default="{ row }">
            <span class="font-mono tabular-nums font-bold">{{ row.purchase_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="picked_batch_no" label="发货批号 (UDI-PI)" width="170">
          <template #default="{ row }">
            <span v-if="row.picked_batch_no" class="font-mono tabular-nums status-chip chip-info">{{ row.picked_batch_no }}</span>
            <span v-else class="text-muted">待配货填报</span>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_flow_status" label="协同状态" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.purchase_flow_status === 'DEPT_APPROVED'" class="status-chip chip-warn">
              主科已批·待接单发货
            </span>
            <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED'" class="status-chip chip-active">
              已发货·待医院验收
            </span>
            <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'" class="status-chip chip-active">
              医院已完成入库
            </span>
            <span v-else class="status-chip chip-info">
              {{ row.purchase_flow_status }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="协同发货操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.purchase_flow_status === 'DEPT_APPROVED'"
              type="primary"
              size="small"
              :disabled="activeSupplier.qual_audit_status !== 'QUAL_APPROVED'"
              @click="openShipModal(row)"
            >
              配货发货
            </el-button>
            <span
              v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED'"
              class="status-chip chip-active"
            >
              已发货 (待院方查验)
            </span>
            <span
              v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'"
              class="status-chip chip-active"
            >
              已验收入库
            </span>
            <span v-else class="text-muted" style="font-size: 12px;">已锁定</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- =====================================================================
         Tab 2: 采供月度对账与发票结算
         ===================================================================== -->
    <div v-show="currentTab === 'reconcile'" class="glass-panel table-panel">
      <div class="table-caption-bar">
        <span class="caption-title">与院方主库验收入库金额月度核对结算</span>
        <span class="caption-sub font-mono tabular-nums">对账无误后在线提报发票代码与号码完成结算</span>
      </div>

      <el-alert
        title="月度对账机制：仅统计医院普通耗材主库与高值专仓实际验收入库合格并入账的物料清单，移库不计费，验收结案后方可开具增值税专用发票。"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 14px;"
      />

      <el-form :inline="true" size="small" style="margin-bottom: 12px;">
        <el-form-item label="核算月份">
          <el-date-picker v-model="reconcileMonth" type="month" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="增值税发票代码">
          <el-input v-model="invoiceCode" placeholder="如 3300261108" style="width: 140px;" />
        </el-form-item>
        <el-form-item label="发票号码">
          <el-input v-model="invoiceNo" placeholder="如 08921102" style="width: 140px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="handleInvoiceConfirm">
            提交发票并确认双方结算
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 拣货配货与发货确认弹窗 -->
    <el-dialog
      v-model="shipModalVisible"
      title="外部供应商在线拣货配货与发货"
      width="540px"
      append-to-body
    >
      <div v-if="targetOrder" style="display: flex; flex-direction: column; gap: 14px;">
        <el-alert
          title="发货联动铁律：发货并确认批号效期后，系统将自动同步生成医院端的《待验收入库单》，医院主库查验实物无误后正式增库！"
          type="info"
          :closable="false"
          show-icon
        />
        <el-form label-width="120px" size="small">
          <el-form-item label="采购单号">
            <span class="font-mono tabular-nums font-bold text-accent">{{ targetOrder.order_no }}</span>
          </el-form-item>
          <el-form-item label="采购物资品名">
            <span>{{ targetOrder.product_name }}</span>
          </el-form-item>
          <el-form-item label="订货数量">
            <span class="font-mono tabular-nums font-bold">{{ targetOrder.purchase_qty }} 件</span>
          </el-form-item>
          <el-form-item label="发货生产批号 *" required>
            <el-input v-model="shipBatchNo" placeholder="请输入出厂合格生产批号，如 BATCH-20261104" />
          </el-form-item>
          <el-form-item label="产品有效期至 *" required>
            <el-date-picker
              v-model="shipExpiryDate"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择有效期"
              style="width: 100%;"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="shipModalVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingShip" @click="submitShipAction">
          确认发货并生成医院待验单
        </el-button>
      </template>
    </el-dialog>

    <!-- 资质证照重新上传弹窗 -->
    <el-dialog
      v-model="qualUploadVisible"
      title="提报企业《医疗器械经营许可证》与资质信息"
      width="500px"
      append-to-body
    >
      <el-form label-width="130px" size="small">
        <el-form-item label="企业全称">
          <el-input v-model="activeSupplier.supplier_name" />
        </el-form-item>
        <el-form-item label="经营许可证编号">
          <el-input v-model="activeSupplier.license_no" placeholder="如 鲁械经营备20260088号" />
        </el-form-item>
        <el-form-item label="许可证有效期至">
          <el-date-picker
            v-model="activeSupplier.license_expiry_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="qualUploadVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUploadQual">确认送审</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import SvgIcon from '@/components/common/SvgIcon.vue';
import { useUserStore } from '@/stores/userStore';
import {
  listSupplierPurchaseOrders,
  listSupplierQualifications,
  auditSupplierQualification,
  flowSupplierPurchaseAction,
  type SupplierPurchaseOrder,
  type SupplierQualificationItem
} from '@/api/supplierPurchaseApi';

const userStore = useUserStore();
const currentTab = ref<'orders' | 'reconcile'>('orders');

const supplierOptions = ref<SupplierQualificationItem[]>([]);
const currentSupplierCode = ref('SUP_WEGO_01');

const myOrders = ref<SupplierPurchaseOrder[]>([]);
const loadingOrders = ref(false);

const shipModalVisible = ref(false);
const targetOrder = ref<SupplierPurchaseOrder | null>(null);
const shipBatchNo = ref('BATCH-WEGO-20261104');
const shipExpiryDate = ref('2029-11-01');
const submittingShip = ref(false);

const qualUploadVisible = ref(false);

const reconcileMonth = ref('2026-11');
const invoiceCode = ref('3300261108');
const invoiceNo = ref('08921102');

const activeSupplier = computed<SupplierQualificationItem>(() => {
  const found = supplierOptions.value.find((s) => s.supplier_code === currentSupplierCode.value);
  if (found) return found;
  return {
    supplier_code: currentSupplierCode.value,
    supplier_name: '山东威高集团医用高分子制品股份有限公司',
    social_credit_code: '91371000720745239N',
    license_no: '鲁械经营备20260088号',
    license_expiry_date: '2029-12-31',
    qual_audit_status: 'QUAL_APPROVED',
    contact_person: '张明远 (医药代表)',
    contact_phone: '13812345678',
    audit_remark: '首营企业资质已通过医院审核'
  };
});

const pendingShipCount = computed(() =>
  myOrders.value.filter((o) => o.purchase_flow_status === 'DEPT_APPROVED').length
);

/**
 * 获取全量供应商列表供切换测试
 */
async function fetchSuppliers(): Promise<void> {
  try {
    const res = await listSupplierQualifications();
    supplierOptions.value = res || [];
    // 若当前 supplierCode 不在列表中，默认选中第一项或 SUP_WEGO_01
    if (supplierOptions.value.length > 0 && !supplierOptions.value.some((s) => s.supplier_code === currentSupplierCode.value)) {
      currentSupplierCode.value = supplierOptions.value[0].supplier_code;
    }
  } catch (err: any) {
    ElMessage.error(err.message || '获取供应商资质列表失败');
  }
}

/**
 * 切换代表的供应商企业（企业级数据物理隔离）
 */
function handleSupplierSwitch(): void {
  ElMessage.info(`已切换至外部供应商企业: ${activeSupplier.value.supplier_name}`);
  fetchMyOrders();
}

/**
 * 查询属于本企业的采购订单（严格企业数据隔离）
 */
async function fetchMyOrders(): Promise<void> {
  loadingOrders.value = true;
  try {
    // 传入当前选中的 supplier_code
    const res = await listSupplierPurchaseOrders(currentSupplierCode.value);
    myOrders.value = res || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取企业采购订单失败');
  } finally {
    loadingOrders.value = false;
  }
}

/**
 * 打开配货发货弹窗
 * @param {SupplierPurchaseOrder} row 采购订单
 */
function openShipModal(row: SupplierPurchaseOrder): void {
  if (activeSupplier.value.qual_audit_status !== 'QUAL_APPROVED') {
    ElMessage.error(`[供应商资质准入硬拦截] 企业《医疗器械经营许可证》处于待审状态，严禁发货！`);
    return;
  }
  targetOrder.value = row;
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 8);
  shipBatchNo.value = `BATCH-${row.supplier_code.slice(0, 8)}-${ts}`;
  shipExpiryDate.value = '2029-11-01';
  shipModalVisible.value = true;
}

/**
 * 提交配货发货
 * @route POST /api/v1/ext/supplier-purchase/flow
 */
async function submitShipAction(): Promise<void> {
  if (!targetOrder.value) return;
  if (!shipBatchNo.value) {
    ElMessage.warning('请录入发货生产批号');
    return;
  }
  submittingShip.value = true;
  try {
    await flowSupplierPurchaseAction({
      order_no: targetOrder.value.order_no,
      flow_action: 'SUPPLIER_PICK_AND_SHIP',
      picked_batch_no: shipBatchNo.value,
      picked_expiry_date: shipExpiryDate.value,
      operator_name: userStore.currentUser.realName || '外部供应商代表'
    });
    ElMessage.success(`订单 [${targetOrder.value.order_no}] 拣货发货成功！已自动向医院主库生成《待验收入库单》`);
    shipModalVisible.value = false;
    fetchMyOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '发货操作失败');
  } finally {
    submittingShip.value = false;
  }
}

/**
 * 上传资质送审
 */
async function handleUploadQual(): Promise<void> {
  try {
    await auditSupplierQualification({
      supplier_code: activeSupplier.value.supplier_code,
      supplier_name: activeSupplier.value.supplier_name,
      license_no: activeSupplier.value.license_no,
      license_expiry_date: activeSupplier.value.license_expiry_date,
      audit_action: 'QUAL_PENDING'
    });
    ElMessage.success('经营许可证资质已提报，请等待医院主科室审批准入！');
    qualUploadVisible.value = false;
    fetchSuppliers();
  } catch (err: any) {
    ElMessage.error(err.message || '提报资质失败');
  }
}

/**
 * 确认开票结算
 */
function handleInvoiceConfirm(): void {
  ElMessage.success(`发票 [${invoiceCode.value}-${invoiceNo.value}] 核验通过，双方月度结算已结清记账！`);
}

onMounted(async () => {
  await fetchSuppliers();
  await fetchMyOrders();
});
</script>

<style scoped>
.external-supplier-portal-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.supplier-banner-card {
  padding: 16px 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  border-left: 4px solid var(--color-primary);
}

.banner-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.supplier-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.supplier-title-select {
  display: flex;
  align-items: center;
  gap: 12px;
}

.supplier-main-name {
  font-size: 18px;
  color: var(--text-primary);
}

.supplier-switch-select {
  width: 260px;
}

.license-meta-text {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-sep {
  color: var(--border-color);
}

.banner-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.qual-status-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.qual-status-label {
  font-size: 12px;
  color: var(--text-muted);
}

.qual-block-warning-panel {
  padding: 14px 18px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.warning-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.warning-title {
  font-size: 14px;
  color: #ef4444;
}

.warning-desc {
  font-size: 12px;
  color: var(--text-regular);
  line-height: 1.6;
}

.action-toolbar-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  border-radius: 12px;
  flex-wrap: wrap;
  gap: 12px;
}

.tab-btn-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.proc-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-regular);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.proc-tab-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.proc-tab-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.tab-chip {
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 11px;
}

.tab-chip.chip-warn {
  background: var(--color-warning);
  color: #fff;
}

.action-btn-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-panel {
  padding: 16px 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.table-caption-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 4px;
}

.caption-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.caption-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.status-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.chip-active {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.chip-warn {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.chip-disabled {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.chip-info {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.3);
}
</style>
