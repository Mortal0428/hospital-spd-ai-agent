<template>
  <div class="external-supplier-portal-view">
    <!-- 顶部外部供应商身份与国家药监局资质看板 -->
    <div class="glass-panel supplier-banner-card">
      <div class="banner-left">
        <div class="supplier-badge">
          <SvgIcon name="shield" :size="15" color="var(--accent-primary)" />
          <span>外部供应商数字化协同门户 (B2B)</span>
        </div>
        <div class="supplier-info-line">
          <div class="supplier-title-select">
            <span class="supplier-main-name font-bold">{{ activeSupplier.supplier_name }}</span>
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
                :label="`${sup.supplier_name} [${sup.qual_audit_status === 'QUAL_APPROVED' ? '已准入' : '待审'}]`"
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
          <span v-else-if="activeSupplier.qual_audit_status === 'QUAL_REJECTED'" class="status-chip chip-disabled">
            准入已驳回 (请查看原因并重报)
          </span>
          <span v-else class="status-chip chip-warn">
            待审硬拦截 (严禁接单发货)
          </span>
        </div>

        <el-button size="small" plain @click="openQualUploadModal">
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
        根据国家药品监督管理局《医疗器械经营监督管理办法》与三甲医院物资采购内控条例，未经医院审核通过前，<strong>严禁进行在线接单、拣货配货与发货业务</strong>！请联系院方耗材科审批准入资质。
      </div>

      <!-- 驳回原因醒目展示区 -->
      <div v-if="activeSupplier.qual_audit_status === 'QUAL_REJECTED'" class="reject-reason-box" style="margin-top: 12px; padding: 12px 16px; background: rgba(239, 68, 68, 0.08); border-left: 4px solid var(--color-danger); border-radius: 6px;">
        <div style="font-weight: 700; color: var(--color-danger); font-size: 13px; display: flex; align-items: center; gap: 6px;">
          <SvgIcon name="info" :size="14" color="var(--color-danger)" />
          <span>【医院耗材科审核驳回意见】:</span>
        </div>
        <div style="color: var(--text-primary); font-size: 13px; margin-top: 4px; padding-left: 20px; font-weight: 500;">
          {{ activeSupplier.audit_remark || '企业资质证明材料不全，请根据国家医疗器械首营规定重新上传并加盖鲜章。' }}
        </div>
      </div>

      <!-- 快速提报操作引导条 -->
      <div style="margin-top: 14px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
        <el-button type="primary" size="small" @click="openQualUploadModal">
          <SvgIcon name="upload" :size="13" style="margin-right: 4px;" />
          立即完善并提报资质认证申请
        </el-button>
        <span class="text-muted" style="font-size: 12px;">提交后将自动同步至医院耗材科/设备科【供应商资质审查】待审台账</span>
      </div>
    </div>

    <!-- 主体毛玻璃 Tab 工作台 (统一标准 fusion-tabs，彻底消除浅色白字隐形) -->
    <div class="glass-panel tab-container-panel">
      <el-tabs v-model="currentTab" class="fusion-tabs" @tab-change="handleTabChange">
        <!-- =====================================================================
             Tab 1: 企业专属采购订单接单与拣货发货协同
             ===================================================================== -->
        <el-tab-pane label="企业专属采购订单接单与拣货发货协同" name="orders">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="package" :size="15" color="var(--accent-primary)" />
                <span>当前企业 [{{ activeSupplier.supplier_name }}] 共有 {{ myOrders.length }} 笔订单 · 待发货 {{ pendingShipCount }} 笔</span>
              </div>
              <div class="action-btn-group">
                <el-button plain size="small" @click="fetchMyOrders">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新订单数据
                </el-button>
              </div>
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
                  <span class="font-mono">{{ row.product_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="purchase_qty" label="采购订货数" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono font-bold">{{ row.purchase_qty }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="picked_batch_no" label="发货批号 (UDI-PI)" width="180">
                <template #default="{ row }">
                  <span class="font-mono text-accent">{{ row.picked_batch_no || '待拣货装箱' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="purchase_flow_status" label="协同状态" width="160" align="center">
                <template #default="{ row }">
                  <span v-if="row.purchase_flow_status === 'PLAN_SUBMITTED'" class="status-chip chip-warn">
                    医院待审批
                  </span>
                  <span v-else-if="row.purchase_flow_status === 'DEPT_APPROVED'" class="status-chip chip-info">
                    主科已批·待发货
                  </span>
                  <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED'" class="status-chip chip-active">
                    已发货·待医院验收
                  </span>
                  <span v-else-if="row.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'" class="status-chip chip-active">
                    已验收入库
                  </span>
                  <span v-else class="status-chip chip-info">{{ row.purchase_flow_status }}</span>
                </template>
              </el-table-column>

              <!-- 协同操作列：完整包含查看单据、拣货、四联打印、发货 -->
              <el-table-column label="协同操作" min-width="260" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 6px; justify-content: center; flex-wrap: nowrap;">
                    <!-- 查看采购单据 (PO) -->
                    <el-button size="small" plain @click="openViewVoucherModal(row)">
                      查看单据
                    </el-button>

                    <!-- 配货发货 (含装箱与物流) -->
                    <el-button
                      v-if="row.purchase_flow_status === 'DEPT_APPROVED'"
                      size="small"
                      type="primary"
                      :disabled="activeSupplier.qual_audit_status !== 'QUAL_APPROVED'"
                      @click="openShipModal(row)"
                    >
                      配货发货
                    </el-button>

                    <!-- 打印随货同行单 (已发货后随时打印) -->
                    <el-button
                      v-if="row.purchase_flow_status === 'HOSP_INBOUND_CREATED' || row.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'"
                      size="small"
                      type="success"
                      plain
                      @click="openPrintDeliveryVoucher(row)"
                    >
                      四联同行单
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 2: 采供月度对账与发票结算
             ===================================================================== -->
        <el-tab-pane label="采供月度对账与发票结算" name="reconcile">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="finance" :size="15" color="var(--color-info)" />
                <span>供应商与医院财务科月度核算对账凭证中心</span>
              </div>
              <div class="action-btn-group">
                <el-date-picker
                  v-model="reconcileMonth"
                  type="month"
                  value-format="YYYY-MM"
                  size="small"
                  placeholder="选择对账月份"
                />
                <el-button type="primary" size="small" @click="handleInvoiceConfirm">
                  确认双方已开票对账
                </el-button>
              </div>
            </div>

            <div class="glass-panel" style="padding: 20px; border-radius: 12px; display: flex; flex-direction: column; gap: 14px;">
              <div style="font-weight: 700; font-size: 14px;">核算月份 [{{ reconcileMonth }}] 双方采供明细总额: ¥ 13,320.00</div>
              <div class="text-muted" style="font-size: 13px;">包含已验收入库高值耗材与普通卫材共 3 笔单据，符合国家三甲医疗器械两票制规范。</div>
              <div style="display: flex; gap: 12px; align-items: center; margin-top: 8px;">
                <el-input v-model="invoiceCode" size="small" placeholder="增值税发票代码" style="width: 200px;" />
                <el-input v-model="invoiceNo" size="small" placeholder="增值税发票号码" style="width: 200px;" />
                <span class="status-chip chip-active">已通过国家税务底账核验</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 弹窗 1: 查看医院正式采购订单明细 (PO) -->
    <el-dialog
      v-model="viewVoucherVisible"
      title="医院正式采购订单 (PO) 单据查阅"
      width="680px"
      append-to-body
      class="spd-dialog-modal"
    >
      <div v-if="targetOrder" style="display: flex; flex-direction: column; gap: 12px;">
        <div class="glass-panel" style="padding: 14px; border-radius: 8px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 12px;">
          <div>单据编号: <strong class="font-mono text-accent">{{ targetOrder.order_no }}</strong></div>
          <div>下发科室: <strong>{{ targetOrder.audit_main_dept_code === 'CONSUMABLE_DEPT' ? '耗材科主库' : '设备科主库' }}</strong></div>
          <div>指定供应商: <strong>{{ targetOrder.supplier_name }}</strong></div>
          <div>首营资质: <span class="status-chip chip-active">通过准入</span></div>
        </div>

        <table class="bill-detail-table">
          <thead>
            <tr>
              <th>物料代码</th>
              <th>物资品名</th>
              <th align="right">采购订货数</th>
              <th align="center">流转状态</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="font-mono text-accent">{{ targetOrder.product_code }}</td>
              <td><strong>{{ targetOrder.product_name }}</strong></td>
              <td align="right" class="font-mono font-bold">{{ targetOrder.purchase_qty }} 件</td>
              <td align="center"><span class="status-chip chip-info">{{ targetOrder.purchase_flow_status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <el-button @click="viewVoucherVisible = false">关闭查阅</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 2: 在线拣货装箱与录入物流配送信息 -->
    <el-dialog
      v-model="shipModalVisible"
      title="外部供应商在线拣货装箱与发货确认"
      width="600px"
      append-to-body
      class="spd-dialog-modal"
    >
      <div v-if="targetOrder" style="display: flex; flex-direction: column; gap: 14px;">
        <el-alert
          title="发货联动机制：发货提交后，系统将自动向医院主库生成《待验收入库单》，并生成医疗器械随货同行出库单。"
          type="info"
          :closable="false"
          show-icon
        />

        <el-form label-width="140px" size="small">
          <el-form-item label="关联采购单号">
            <span class="font-mono font-bold text-accent">{{ targetOrder.order_no }}</span>
          </el-form-item>
          <el-form-item label="拟发货耗材物资">
            <span>{{ targetOrder.product_name }} ({{ targetOrder.purchase_qty }}件)</span>
          </el-form-item>
          <el-form-item label="出厂生产批号 (UDI-PI)" required>
            <el-input v-model="shipBatchNo" placeholder="如: BATCH-WEGO-20261104" />
          </el-form-item>
          <el-form-item label="有效截止日期" required>
            <el-date-picker
              v-model="shipExpiryDate"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%;"
            />
          </el-form-item>
          <el-form-item label="物流配送承运商">
            <el-select v-model="shipLogisticsCompany" style="width: 100%;">
              <el-option value="顺丰冷链医药专配" label="顺丰冷链医药专配 (2~8℃温控)" />
              <el-option value="企业专车专人直达" label="企业专车专人直达配送" />
              <el-option value="国药外配物流" label="国药外配智慧医药物流" />
            </el-select>
          </el-form-item>
          <el-form-item label="物流运单号/配送人">
            <el-input v-model="shipLogisticsNo" placeholder="输入运单编号或专车配送人姓名" />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="shipModalVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submittingShip"
          @click="submitShipAction"
        >
          确认发货并生成医院入库单
        </el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 3: 医疗器械随货同行单 (标准四联单据打印) -->
    <PrintVoucherDialog
      v-model="printDeliveryVoucherVisible"
      voucher-type="外部供应商医疗器械随货同行出库单"
      :order-data="printDeliveryOrderData"
    />

    <!-- 弹窗 4: 外部供应商医疗器械经营资质准入申报/重新上传证照 -->
    <el-dialog
      v-model="qualUploadVisible"
      title="外部供应商医疗器械经营资质准入申报"
      width="640px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div style="display: flex; flex-direction: column; gap: 14px;">
        <el-alert
          title="合规须知：根据三甲医院物资采购内控条例与国家药监局两票制合规要求，首次合作或证照变更必须提交经营许可备案证明材料。"
          type="info"
          :closable="false"
          show-icon
        />

        <el-form label-width="150px" size="small">
          <el-form-item label="供应商企业全称" required>
            <el-input v-model="qualForm.supplier_name" placeholder="如: 威海高技术产业开发区医疗器械商贸有限公司" />
          </el-form-item>
          <el-form-item label="企业代码/识别码" required>
            <el-input v-model="qualForm.supplier_code" :disabled="isExistingCode" placeholder="如: SUP_WEGO_NEW" class="font-mono" />
          </el-form-item>
          <el-form-item label="统一社会信用代码" required>
            <el-input v-model="qualForm.social_credit_code" placeholder="18位法人和其他组织统一社会信用代码" class="font-mono" />
          </el-form-item>
          <el-form-item label="医疗器械经营许可证" required>
            <el-input v-model="qualForm.license_no" placeholder="如: 鲁械经营备20268888号" class="font-mono" />
          </el-form-item>
          <el-form-item label="药监许可有效截止日" required>
            <el-date-picker
              v-model="qualForm.license_expiry_date"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%;"
              placeholder="选择有效期"
            />
          </el-form-item>
          <el-form-item label="法定业务授权代表" required>
            <el-input v-model="qualForm.contact_person" placeholder="输入经办人姓名" />
          </el-form-item>
          <el-form-item label="业务代表联系手机" required>
            <el-input v-model="qualForm.contact_phone" placeholder="输入手机号码" />
          </el-form-item>
          <el-form-item label="资质证书电子扫描件">
            <div class="mock-upload-box" style="width: 100%; padding: 12px; border: 1px dashed var(--spd-border-subtle); border-radius: 6px; background: rgba(0,0,0,0.02); display: flex; align-items: center; justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <SvgIcon name="upload" :size="16" color="var(--accent-primary)" />
                <span style="font-size: 12px;">{{ uploadedFileName || '医疗器械经营许可证_正本_加盖鲜章.pdf' }}</span>
              </div>
              <el-button size="small" plain @click="handleMockFileUpload">
                {{ uploadedFileName ? '重新上传' : '选择文件' }}
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="qualUploadVisible = false">取消</el-button>
          <el-button type="primary" :loading="submittingQual" @click="submitQualApplication">
            确认提报院方耗材科审核
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import SvgIcon from '@/components/common/SvgIcon.vue';
import PrintVoucherDialog from '@/components/PrintVoucherDialog.vue';
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
const route = useRoute();
const userStore = useUserStore();

const currentTab = ref('orders');

// 监听路由 query.tab 动态切换激活选项卡 (支持 orders / reconcile)
watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab && typeof newTab === 'string') {
      if (['orders', 'reconcile'].includes(newTab)) {
        currentTab.value = newTab;
      }
    }
  },
  { immediate: true }
);

/**
 * 处理外部供应商门户 Tab 切换并同步更新浏览器 URL 查询参数
 * @param {string} tabName 目标选项卡标识
 * @returns {void}
 * @route internal://ExternalSupplierPortalView/handleTabChange
 * @throws 无异常抛出
 */
function handleTabChange(tabName: any): void {
  router.replace({ query: { ...route.query, tab: tabName } });
}

const supplierOptions = ref<SupplierQualificationItem[]>([]);
const currentSupplierCode = ref('SUP_WEGO_01');

const myOrders = ref<SupplierPurchaseOrder[]>([]);
const loadingOrders = ref(false);

const targetOrder = ref<SupplierPurchaseOrder | null>(null);
const viewVoucherVisible = ref(false);

const shipModalVisible = ref(false);
const shipBatchNo = ref('BATCH-WEGO-20261104');
const shipExpiryDate = ref('2029-11-01');
const shipLogisticsCompany = ref('顺丰冷链医药专配');
const shipLogisticsNo = ref('SF202611048899');
const submittingShip = ref(false);

const qualUploadVisible = ref(false);
const isExistingCode = ref(false);
const submittingQual = ref(false);
const uploadedFileName = ref('医疗器械经营许可证_正本_加盖鲜章.pdf');

const qualForm = ref({
  supplier_code: '',
  supplier_name: '',
  social_credit_code: '',
  license_no: '',
  license_expiry_date: '2029-12-31',
  contact_person: '',
  contact_phone: ''
});

const reconcileMonth = ref('2026-11');
const invoiceCode = ref('3300261108');
const invoiceNo = ref('08921102');

// 四联随货同行单打印
const printDeliveryVoucherVisible = ref(false);
const printDeliveryOrderData = ref<Record<string, any>>({});

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

async function fetchSuppliers(): Promise<void> {
  try {
    const res = await listSupplierQualifications();
    supplierOptions.value = res || [];
    if (supplierOptions.value.length > 0 && !supplierOptions.value.some((s) => s.supplier_code === currentSupplierCode.value)) {
      currentSupplierCode.value = supplierOptions.value[0].supplier_code;
    }
  } catch (err: any) {
    ElMessage.error(err.message || '获取供应商资质列表失败');
  }
}

function handleSupplierSwitch(): void {
  ElMessage.info(`已切换至外部供应商企业: ${activeSupplier.value.supplier_name}`);
  fetchMyOrders();
}

async function fetchMyOrders(): Promise<void> {
  loadingOrders.value = true;
  try {
    const res = await listSupplierPurchaseOrders(currentSupplierCode.value);
    myOrders.value = res || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取企业采购订单失败');
  } finally {
    loadingOrders.value = false;
  }
}

function openViewVoucherModal(row: SupplierPurchaseOrder): void {
  targetOrder.value = row;
  viewVoucherVisible.value = true;
}

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

function openPrintDeliveryVoucher(row: SupplierPurchaseOrder): void {
  printDeliveryOrderData.value = {
    order_no: `DELIVERY-${row.order_no}`,
    target_dept_or_supplier: '浙江大学医学院附属第一医院耗材总库',
    warehouse_code: row.audit_main_dept_code === 'CONSUMABLE_DEPT' ? 'WH_WEICAI (卫材主库)' : 'WH_EQUIP (设备库)',
    product_name: row.product_name,
    product_code: row.product_code,
    quantity: row.purchase_qty,
    unit_price: 18.5,
    batch_no: row.picked_batch_no || 'BATCH-WEGO-20261102',
    expire_date: '2029-11-01',
    carrier: shipLogisticsCompany.value
  };
  printDeliveryVoucherVisible.value = true;
}

function handleInvoiceConfirm(): void {
  ElMessage.success(`发票 [${invoiceCode.value}-${invoiceNo.value}] 核验通过，双方月度结算已结清记账！`);
}

/**
 * 打开资质准入申报/重新上传证照弹窗并初始化数据
 * @returns {void}
 * @route internal://ExternalSupplierPortalView/openQualUploadModal
 * @throws 无异常
 */
function openQualUploadModal(): void {
  const current = activeSupplier.value;
  qualForm.value = {
    supplier_code: current.supplier_code || `SUP_${userStore.currentUser.username.toUpperCase()}`,
    supplier_name: current.supplier_name || '某新注册医疗器械商贸公司',
    social_credit_code: current.social_credit_code || '91330108MA28K9999X',
    license_no: current.license_no || '浙械经营备20269999号',
    license_expiry_date: current.license_expiry_date || '2029-12-31',
    contact_person: current.contact_person || userStore.currentUser.realName || '业务代表',
    contact_phone: current.contact_phone || '13912345678'
  };
  isExistingCode.value = Boolean(current.supplier_code);
  qualUploadVisible.value = true;
}

/**
 * 模拟资质扫描件文件选择上传
 * @returns {void}
 * @route internal://ExternalSupplierPortalView/handleMockFileUpload
 * @throws 无异常
 */
function handleMockFileUpload(): void {
  uploadedFileName.value = `医疗器械经营许可证_${qualForm.value.supplier_name || '正本'}_已盖鲜章.pdf`;
  ElMessage.success('资质电子证照扫描件已载入缓存！');
}

/**
 * 提交供应商经营资质申报材料至医院耗材科审核池
 * @returns {Promise<void>}
 * @route POST /api/v1/ext/supplier-purchase/qual-audit
 * @throws 异常时弹出错误信息
 */
async function submitQualApplication(): Promise<void> {
  if (!qualForm.value.supplier_name.trim()) {
    ElMessage.warning('请输入供应商企业法定全称');
    return;
  }
  if (!qualForm.value.license_no.trim()) {
    ElMessage.warning('请输入《医疗器械经营许可证》编号');
    return;
  }
  if (!qualForm.value.license_expiry_date) {
    ElMessage.warning('请选择药监许可证有效截止日期');
    return;
  }

  submittingQual.value = true;
  try {
    await auditSupplierQualification({
      supplier_code: qualForm.value.supplier_code,
      supplier_name: qualForm.value.supplier_name,
      social_credit_code: qualForm.value.social_credit_code,
      license_no: qualForm.value.license_no,
      license_expiry_date: qualForm.value.license_expiry_date,
      contact_person: qualForm.value.contact_person,
      contact_phone: qualForm.value.contact_phone,
      audit_action: 'QUAL_PENDING',
      audit_remark: '供应商已完善证照材料提报，等待院方耗材科资质查验'
    });
    ElMessage.success(`企业 [${qualForm.value.supplier_name}] 经营资质申报已提交！已送达院方耗材科待审池。`);
    qualUploadVisible.value = false;
    currentSupplierCode.value = qualForm.value.supplier_code;
    await fetchSuppliers();
    await fetchMyOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '提交资质申报失败');
  } finally {
    submittingQual.value = false;
  }
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
  border-left: 4px solid var(--accent-primary);
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
  color: var(--accent-primary);
  text-transform: uppercase;
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
  color: var(--border-divider);
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

.tab-container-panel {
  padding: 16px 20px;
  border-radius: 14px;
}

.pane-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0 14px 0;
  border-bottom: 1px solid var(--border-divider);
  margin-bottom: 14px;
}

.action-desc-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
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

.bill-detail-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.bill-detail-table th {
  background: var(--bg-card-hover);
  padding: 8px 10px;
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-divider);
}

.bill-detail-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-divider);
}
</style>
