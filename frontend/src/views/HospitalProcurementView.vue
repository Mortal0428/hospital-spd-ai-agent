<template>
  <div class="hospital-procurement-view">
    <!-- 顶部医院采购内控指标大盘 (4 宫格) -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>待审批临床采购计划</span>
          <SvgIcon name="clock" :size="16" color="var(--color-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-primary">
          {{ pendingPlanCount }} <span class="kpi-unit">笔</span>
        </div>
        <div class="kpi-sub text-primary">
          <SvgIcon name="info" :size="13" color="var(--color-primary)" />
          <span>耗材科/设备科归口协同审批</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>待审核供应商准入资质</span>
          <SvgIcon name="shield" :size="16" color="var(--color-warning)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-warn">
          {{ pendingQualCount }} <span class="kpi-unit">家</span>
        </div>
        <div class="kpi-sub text-warn">
          <SvgIcon name="clock" :size="13" color="var(--color-warning)" />
          <span>国家药监局经营许可首营准入硬拦截</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>在途待验收到货送货单</span>
          <SvgIcon name="upload" :size="16" color="var(--color-success)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-success">
          {{ pendingInboundCount }} <span class="kpi-unit">笔</span>
        </div>
        <div class="kpi-sub text-success">
          <SvgIcon name="safe" :size="13" color="var(--color-success)" />
          <span>供应商已送达·主库待实物查验增库</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>本期采购下发累计发生额</span>
          <SvgIcon name="finance" :size="16" color="var(--color-info)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-info">
          ¥ {{ totalPurchaseAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}
        </div>
        <div class="kpi-sub text-muted">
          <SvgIcon name="dict" :size="13" color="var(--text-muted)" />
          <span>全院两级主库向合规供应商采购台账</span>
        </div>
      </div>
    </div>

    <!-- 主控操作栏与 Tab 切换 -->
    <div class="glass-panel action-toolbar-panel">
      <div class="tab-btn-group">
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'plans' }"
          @click="switchTab('plans')"
        >
          <SvgIcon name="package" :size="15" />
          <span>临床采购计划与主科审批</span>
          <span v-if="pendingPlanCount > 0" class="tab-chip font-mono">{{ pendingPlanCount }}</span>
        </button>
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'suppliers' }"
          @click="switchTab('suppliers')"
        >
          <SvgIcon name="shield" :size="15" />
          <span>供应商经营资质审查台账</span>
          <span v-if="pendingQualCount > 0" class="tab-chip chip-warn font-mono">{{ pendingQualCount }}</span>
        </button>
        <button
          class="proc-tab-btn"
          :class="{ active: currentTab === 'tracking' }"
          @click="switchTab('tracking')"
        >
          <SvgIcon name="upload" :size="15" />
          <span>采供履约跟踪与验收入库</span>
          <span v-if="pendingInboundCount > 0" class="tab-chip chip-success font-mono">{{ pendingInboundCount }}</span>
        </button>
      </div>

      <div class="action-btn-group">
        <el-button
          v-if="currentTab === 'plans' && userStore.canAction('PURCHASE_PLAN', 'can_create')"
          type="primary"
          size="small"
          @click="openCreatePlanModal"
        >
          <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
          提报医用耗材采购计划
        </el-button>

        <el-button plain size="small" @click="refreshAllData">
          <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
          刷新采购与准入台账
        </el-button>
      </div>
    </div>

    <!-- =====================================================================
         Tab 1: 临床采购计划提报与主科审批
         ===================================================================== -->
    <div v-show="currentTab === 'plans'" class="glass-panel table-panel">
      <div class="table-caption-bar">
        <span class="caption-title">全院医用耗材采购计划审批与 PO 订单下发</span>
        <span class="caption-sub font-mono tabular-nums">共 {{ orders.length }} 笔采购单据</span>
      </div>

      <el-table
        :data="paginatedOrders"
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
        <el-table-column prop="product_name" label="采购耗材品名" min-width="190" />
        <el-table-column prop="product_code" label="物料代码" width="140">
          <template #default="{ row }">
            <span class="font-mono tabular-nums text-muted">{{ row.product_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_qty" label="采购数量" width="100" align="right">
          <template #default="{ row }">
            <span class="font-mono tabular-nums font-bold">{{ row.purchase_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="指定供应商" min-width="190">
          <template #default="{ row }">
            <span>{{ row.supplier_name }}</span>
            <span
              v-if="row.qual_audit_status === 'QUAL_APPROVED'"
              class="status-chip chip-active"
              style="margin-left: 6px; font-size: 11px;"
            >
              已准入
            </span>
            <span
              v-else
              class="status-chip chip-disabled"
              style="margin-left: 6px; font-size: 11px;"
            >
              待审硬拦截
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="audit_main_dept_code" label="审批归口科室" width="130" align="center">
          <template #default="{ row }">
            <span class="status-chip chip-info">
              {{ row.audit_main_dept_code === 'CONSUMABLE_DEPT' ? '耗材科主库' : '设备科主库' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_flow_status" label="流程阶段" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.purchase_flow_status === 'PLAN_SUBMITTED'" class="status-chip chip-warn">
              待主科审批
            </span>
            <span v-else-if="row.purchase_flow_status === 'DEPT_APPROVED'" class="status-chip chip-info">
              主科已批·待供应商配货
            </span>
            <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED'" class="status-chip chip-active">
              供应商已发货·待主库验收
            </span>
            <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'" class="status-chip chip-active">
              已完成验收入库
            </span>
            <span v-else class="status-chip chip-info">{{ row.purchase_flow_status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="内控操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 6px; justify-content: center;">
              <el-button
                v-if="row.purchase_flow_status === 'PLAN_SUBMITTED' && (userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'dept_manager')"
                size="small"
                type="primary"
                @click="handleApprovePlan(row)"
              >
                审批通过下发
              </el-button>
              <el-button
                v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED'"
                size="small"
                type="warning"
                plain
                @click="goToMainInbound(row)"
              >
                前往验收入库
              </el-button>
              <el-button size="small" plain @click="viewOrderDetails(row)">
                详情
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-footer">
        <el-pagination
          v-model:current-page="orderPage"
          v-model:page-size="orderPageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="orders.length"
        />
      </div>
    </div>

    <!-- =====================================================================
         Tab 2: 供应商准入资质审查工作台 (彻底根治死循环)
         ===================================================================== -->
    <div v-show="currentTab === 'suppliers'" class="glass-panel table-panel">
      <div class="table-caption-bar">
        <span class="caption-title">供应商《医疗器械经营许可证》首营合规性准入审核台账</span>
        <span class="caption-sub font-mono tabular-nums">共 {{ suppliers.length }} 家合作供应商企业</span>
      </div>

      <el-table
        :data="suppliers"
        border
        stripe
        class="fusion-styled-table"
        v-loading="loadingSuppliers"
      >
        <el-table-column prop="supplier_code" label="供应商编码" width="150">
          <template #default="{ row }">
            <span class="font-mono tabular-nums font-bold text-accent">{{ row.supplier_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商企业全称" min-width="210">
          <template #default="{ row }">
            <span class="font-bold">{{ row.supplier_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="license_no" label="医疗器械经营许可证号" width="190">
          <template #default="{ row }">
            <span class="font-mono tabular-nums text-primary">{{ row.license_no || '暂无备案' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="license_expiry_date" label="药监资质效期至" width="130" align="center">
          <template #default="{ row }">
            <span class="font-mono tabular-nums">{{ row.license_expiry_date || '2029-12-31' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="qual_audit_status" label="医院准入状态" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.qual_audit_status === 'QUAL_APPROVED'" class="status-chip chip-active">
              已准入·允许供货
            </span>
            <span v-else-if="row.qual_audit_status === 'QUAL_PENDING'" class="status-chip chip-warn">
              待审硬拦截
            </span>
            <span v-else class="status-chip chip-disabled">
              已驳回不予准入
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="audit_remark" label="合规审查意见" min-width="180" show-overflow-tooltip />
        <el-table-column label="准入审查操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 6px; justify-content: center;">
              <el-button
                v-if="row.qual_audit_status !== 'QUAL_APPROVED'"
                size="small"
                type="success"
                @click="openAuditModal(row, 'QUAL_APPROVED')"
              >
                审核通过并准入
              </el-button>
              <el-button
                v-if="row.qual_audit_status === 'QUAL_APPROVED'"
                size="small"
                type="warning"
                plain
                @click="openAuditModal(row, 'QUAL_PENDING')"
              >
                设为待审测试拦截
              </el-button>
              <el-button
                v-if="row.qual_audit_status !== 'QUAL_REJECTED'"
                size="small"
                type="danger"
                plain
                @click="openAuditModal(row, 'QUAL_REJECTED')"
              >
                驳回
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- =====================================================================
         Tab 3: 全院采供履约与验收入库看板
         ===================================================================== -->
    <div v-show="currentTab === 'tracking'" class="glass-panel table-panel">
      <div class="table-caption-bar">
        <span class="caption-title">采购订单全流程履约监控与主库验收入库直通看板</span>
        <span class="caption-sub font-mono tabular-nums">覆盖下发、接单、发货、到货实物查验与入库增数</span>
      </div>

      <el-table
        :data="orders"
        border
        stripe
        class="fusion-styled-table"
        v-loading="loadingOrders"
      >
        <el-table-column prop="order_no" label="采购单号" width="170">
          <template #default="{ row }">
            <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商" width="180" />
        <el-table-column prop="product_name" label="物资品名" min-width="180" />
        <el-table-column prop="purchase_qty" label="采购数" width="90" align="right" />
        <el-table-column prop="picked_batch_no" label="发货生产批次" width="160">
          <template #default="{ row }">
            <span v-if="row.picked_batch_no" class="font-mono tabular-nums status-chip chip-info">{{ row.picked_batch_no }}</span>
            <span v-else class="text-muted">待供应商配货录入</span>
          </template>
        </el-table-column>
        <el-table-column prop="auto_inbound_order_no" label="关联主库入库单" width="180">
          <template #default="{ row }">
            <span v-if="row.auto_inbound_order_no" class="font-mono tabular-nums font-bold text-success">{{ row.auto_inbound_order_no }}</span>
            <span v-else class="text-muted">待发货自动生成</span>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_flow_status" label="履约状态" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED'" class="status-chip chip-active">
              已发货·待医院验收
            </span>
            <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'" class="status-chip chip-active">
              已验收入库结案
            </span>
            <span v-else-if="row.purchase_flow_status === 'DEPT_APPROVED'" class="status-chip chip-info">
              待供应商接单配货
            </span>
            <span v-else class="status-chip chip-warn">
              待主科审批
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED'"
              type="primary"
              size="small"
              @click="goToMainInbound(row)"
            >
              前往验收入库
            </el-button>
            <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'" class="status-chip chip-active">
              入库增数完毕
            </span>
            <span v-else class="text-muted" style="font-size: 12px;">等待流转</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 资质准入审查弹窗 -->
    <el-dialog
      v-model="auditModalVisible"
      :title="`供应商经营资质准入审核 · ${targetSupplier?.supplier_name || ''}`"
      width="540px"
      append-to-body
    >
      <div v-if="targetSupplier" style="display: flex; flex-direction: column; gap: 14px;">
        <el-alert
          :title="`当前审核动作：${targetAuditAction === 'QUAL_APPROVED' ? '准予通过准入，解锁接单发货' : (targetAuditAction === 'QUAL_REJECTED' ? '合规驳回资质申请' : '重设为待审核状态')}`"
          :type="targetAuditAction === 'QUAL_APPROVED' ? 'success' : 'warning'"
          :closable="false"
          show-icon
        />
        <el-form label-width="130px" size="small">
          <el-form-item label="供应商企业全称">
            <span class="font-bold">{{ targetSupplier.supplier_name }}</span>
          </el-form-item>
          <el-form-item label="供应商统一编码">
            <span class="font-mono tabular-nums text-accent">{{ targetSupplier.supplier_code }}</span>
          </el-form-item>
          <el-form-item label="医疗器械经营许可证">
            <el-input v-model="auditFormLicense" placeholder="请输入许可证编号" />
          </el-form-item>
          <el-form-item label="药监资质有效期至">
            <el-date-picker
              v-model="auditFormExpiry"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择有效期"
              style="width: 100%;"
            />
          </el-form-item>
          <el-form-item label="准入合规审查结论">
            <el-input
              v-model="auditFormRemark"
              type="textarea"
              :rows="2"
              placeholder="输入审查意见，如：经医学工程科与质管部门查验原件核对无误，符合首营企业准入规范。"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="auditModalVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submittingAudit"
          @click="submitSupplierAudit"
        >
          确认提交审查结果
        </el-button>
      </template>
    </el-dialog>

    <!-- 提报采购计划弹窗 -->
    <el-dialog
      v-model="createPlanVisible"
      title="提报临床医用耗材采购计划单"
      width="520px"
      append-to-body
    >
      <el-form :model="planForm" label-width="110px" size="small">
        <el-form-item label="提报科室">
          <el-input v-model="planForm.apply_dept_code" disabled />
        </el-form-item>
        <el-form-item label="采购物资品名">
          <el-select v-model="planForm.product_id" placeholder="选择耗材品名" style="width: 100%;">
            <el-option :value="1" label="医用敷料贴 (透明敷料) 10cm*11.5cm [PROD-GEN-001]" />
            <el-option :value="2" label="一次性使用无菌注射器带针 5ml [PROD-GEN-002]" />
            <el-option :value="3" label="冠脉药物洗脱支架系统 [PROD-HV-001]" />
          </el-select>
        </el-form-item>
        <el-form-item label="采购需求数量">
          <el-input-number v-model="planForm.purchase_qty" :min="1" :max="10000" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="拟合作供应商">
          <el-select v-model="planForm.supplier_code" placeholder="指定供应商" style="width: 100%;">
            <el-option
              v-for="sup in suppliers"
              :key="sup.supplier_code"
              :value="sup.supplier_code"
              :label="`${sup.supplier_name} (${sup.qual_audit_status === 'QUAL_APPROVED' ? '已准入' : '待审'})`"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createPlanVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingPlan" @click="submitCreatePlan">
          确认提报计划
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
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

const router = useRouter();
const userStore = useUserStore();

const currentTab = ref<'plans' | 'suppliers' | 'tracking'>('plans');

const orders = ref<SupplierPurchaseOrder[]>([]);
const suppliers = ref<SupplierQualificationItem[]>([]);
const loadingOrders = ref(false);
const loadingSuppliers = ref(false);

const orderPage = ref(1);
const orderPageSize = ref(10);

const auditModalVisible = ref(false);
const targetSupplier = ref<SupplierQualificationItem | null>(null);
const targetAuditAction = ref<'QUAL_APPROVED' | 'QUAL_REJECTED' | 'QUAL_PENDING'>('QUAL_APPROVED');
const auditFormLicense = ref('');
const auditFormExpiry = ref('2029-12-31');
const auditFormRemark = ref('');
const submittingAudit = ref(false);

const createPlanVisible = ref(false);
const submittingPlan = ref(false);
const planForm = ref({
  apply_dept_code: userStore.currentUser.deptCode || 'WH_SEC_ORTHO',
  product_id: 1,
  purchase_qty: 200,
  supplier_code: 'SUP_WEGO_01'
});

const paginatedOrders = computed(() => {
  const start = (orderPage.value - 1) * orderPageSize.value;
  return orders.value.slice(start, start + orderPageSize.value);
});

const pendingPlanCount = computed(() =>
  orders.value.filter((o) => o.purchase_flow_status === 'PLAN_SUBMITTED').length
);

const pendingQualCount = computed(() =>
  suppliers.value.filter((s) => s.qual_audit_status === 'QUAL_PENDING').length
);

const pendingInboundCount = computed(() =>
  orders.value.filter((o) => o.purchase_flow_status === 'HOSP_INBOUND_CREATED').length
);

const totalPurchaseAmount = computed(() =>
  orders.value.reduce((acc, cur) => acc + (cur.purchase_qty * 18.5), 0)
);

/**
 * 切换业务标签页
 * @param {'plans' | 'suppliers' | 'tracking'} tab 目标标签
 * @returns {void}
 * @route internal://HospitalProcurementView/switchTab
 * @throws 无异常
 */
function switchTab(tab: 'plans' | 'suppliers' | 'tracking'): void {
  currentTab.value = tab;
}

/**
 * 获取全院采购订单列表
 * @returns {Promise<void>}
 * @route internal://HospitalProcurementView/fetchOrders
 * @throws 异常时提示网络错误
 */
async function fetchOrders(): Promise<void> {
  loadingOrders.value = true;
  try {
    const res = await listSupplierPurchaseOrders();
    orders.value = res || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取采购订单失败');
  } finally {
    loadingOrders.value = false;
  }
}

/**
 * 获取全院供应商准入资质审查列表
 * @returns {Promise<void>}
 * @route internal://HospitalProcurementView/fetchSuppliers
 * @throws 异常时提示网络错误
 */
async function fetchSuppliers(): Promise<void> {
  loadingSuppliers.value = true;
  try {
    const res = await listSupplierQualifications();
    suppliers.value = res || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取供应商资质列表失败');
  } finally {
    loadingSuppliers.value = false;
  }
}

/**
 * 刷新全部采供台账
 */
function refreshAllData(): void {
  fetchOrders();
  fetchSuppliers();
}

/**
 * 打开准入资质审查弹窗
 * @param {SupplierQualificationItem} sup 目标供应商
 * @param {'QUAL_APPROVED' | 'QUAL_REJECTED' | 'QUAL_PENDING'} action 审核动作
 * @returns {void}
 */
function openAuditModal(sup: SupplierQualificationItem, action: 'QUAL_APPROVED' | 'QUAL_REJECTED' | 'QUAL_PENDING'): void {
  targetSupplier.value = sup;
  targetAuditAction.value = action;
  auditFormLicense.value = sup.license_no || '鲁械经营备20260088号';
  auditFormExpiry.value = sup.license_expiry_date || '2029-12-31';
  auditFormRemark.value = action === 'QUAL_APPROVED'
    ? '经医院耗材管理委员会查验《医疗器械经营许可证》原件无误，准予资质通过。'
    : '资质文件不全或未达标，予以驳回。';
  auditModalVisible.value = true;
}

/**
 * 提交供应商资质准入审查结果
 * @returns {Promise<void>}
 * @route POST /api/v1/ext/supplier-purchase/qual-audit
 * @throws 写入异常时抛出错误提示
 */
async function submitSupplierAudit(): Promise<void> {
  if (!targetSupplier.value) return;
  submittingAudit.value = true;
  try {
    await auditSupplierQualification({
      supplier_code: targetSupplier.value.supplier_code,
      supplier_name: targetSupplier.value.supplier_name,
      license_no: auditFormLicense.value,
      license_expiry_date: auditFormExpiry.value,
      audit_action: targetAuditAction.value
    });
    ElMessage.success(`供应商 [${targetSupplier.value.supplier_name}] 准入审查已成功提交！`);
    auditModalVisible.value = false;
    refreshAllData();
  } catch (err: any) {
    ElMessage.error(err.message || '审查提交失败');
  } finally {
    submittingAudit.value = false;
  }
}

/**
 * 耗材科/设备科主管审批通过采购计划
 * @param {SupplierPurchaseOrder} row 采购计划单行
 * @returns {Promise<void>}
 * @route POST /api/v1/ext/supplier-purchase/flow
 */
async function handleApprovePlan(row: SupplierPurchaseOrder): Promise<void> {
  try {
    await flowSupplierPurchaseAction({
      order_no: row.order_no,
      flow_action: 'DEPT_APPROVE',
      operator_name: userStore.currentUser.realName
    });
    ElMessage.success(`采购计划 [${row.order_no}] 审核通过，正式 PO 订单已下发至供应商！`);
    fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '审批采购计划失败');
  }
}

/**
 * 前往普通主库查验送货实物并验收入库
 * @param {SupplierPurchaseOrder} row 订单行
 */
function goToMainInbound(row: SupplierPurchaseOrder): void {
  const inbNo = row.auto_inbound_order_no || `INB-SUP-${row.order_no}`;
  router.push(`/general?tab=inbound&inb_no=${encodeURIComponent(inbNo)}`);
}

/**
 * 打开提报采购计划弹窗
 */
function openCreatePlanModal(): void {
  createPlanVisible.value = true;
}

/**
 * 提交采购计划单
 */
async function submitCreatePlan(): Promise<void> {
  submittingPlan.value = true;
  try {
    await flowSupplierPurchaseAction({
      flow_action: 'CREATE_PLAN',
      supplier_code: planForm.value.supplier_code,
      apply_dept_code: planForm.value.apply_dept_code,
      product_id: planForm.value.product_id,
      purchase_qty: planForm.value.purchase_qty,
      operator_name: userStore.currentUser.realName
    });
    ElMessage.success('采购计划提报成功，已流转至耗材管理科室审批！');
    createPlanVisible.value = false;
    fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '提报采购计划失败');
  } finally {
    submittingPlan.value = false;
  }
}

function viewOrderDetails(row: SupplierPurchaseOrder): void {
  ElMessage.info(`单号: ${row.order_no} · 供应商: ${row.supplier_name} · 状态: ${row.purchase_flow_status}`);
}

onMounted(() => {
  refreshAllData();
});
</script>

<style scoped>
.hospital-procurement-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

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
  font-size: 26px;
  font-weight: 800;
  margin: 10px 0 6px;
  line-height: 1.1;
}

.kpi-unit {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

.kpi-sub {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 6px;
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
  background: rgba(255, 255, 255, 0.25);
  color: inherit;
}

.tab-chip.chip-warn {
  background: var(--color-warning);
  color: #fff;
}

.tab-chip.chip-success {
  background: var(--color-success);
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

.pagination-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 10px;
}
</style>
