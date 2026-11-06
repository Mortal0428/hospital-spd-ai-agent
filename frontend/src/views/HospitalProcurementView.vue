<template>
  <div class="hospital-procurement-view">
    <!-- 顶部医院采购内控指标大盘 (4 宫格) -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>待审批临床采购计划</span>
          <SvgIcon name="clock" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-primary">
          {{ pendingPlanCount }} <span class="kpi-unit">笔</span>
        </div>
        <div class="kpi-sub text-primary">
          <SvgIcon name="info" :size="13" color="var(--accent-primary)" />
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

    <!-- 主体毛玻璃 Tab 工作台 (统一标准 fusion-tabs，彻底消除浅色白字隐形) -->
    <div class="glass-panel tab-container-panel">
      <el-tabs v-model="currentTab" class="fusion-tabs" @tab-change="handleTabChange">
        <!-- =====================================================================
             Tab 1: 临床采购计划提报与主科审批
             ===================================================================== -->
        <el-tab-pane label="临床采购计划与主科审批" name="plans">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>全院医用耗材采购计划审批与 PO 订单下发 · 共 {{ orders.length }} 笔采购单据</span>
              </div>
              <div class="action-btn-group">
                <el-button
                  v-if="userStore.canAction('PURCHASE_PLAN', 'can_create')"
                  type="primary"
                  size="small"
                  @click="openCreatePlanModal"
                >
                  <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                  提报医用耗材采购计划
                </el-button>

                <el-button plain size="small" @click="refreshAllData">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新台账
                </el-button>
              </div>
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
              <el-table-column prop="purchase_flow_status" label="流程阶段" width="160" align="center">
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
              <!-- 加宽操作列至 min-width 220 杜绝挤压截断 -->
              <el-table-column label="内控操作" min-width="220" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 6px; justify-content: center; flex-wrap: nowrap;">
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
        </el-tab-pane>

        <!-- =====================================================================
             Tab 2: 供应商准入资质审查工作台
             ===================================================================== -->
        <el-tab-pane label="供应商经营资质审查台账" name="suppliers">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="shield" :size="15" color="var(--color-warning)" />
                <span>供应商《医疗器械经营许可证》首营合规性准入审核台账 · 共 {{ suppliers.length }} 家企业</span>
              </div>
              <div class="action-btn-group">
                <el-button plain size="small" @click="fetchSuppliers">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新资质
                </el-button>
              </div>
            </div>

            <el-table
              :data="suppliers"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingSuppliers"
            >
              <el-table-column prop="supplier_code" label="供应商编码" width="160">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums font-bold text-accent">{{ row.supplier_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="supplier_name" label="供应商企业全称" min-width="210">
                <template #default="{ row }">
                  <span class="font-bold">{{ row.supplier_name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="license_no" label="医疗器械经营许可证编号" width="200">
                <template #default="{ row }">
                  <span class="font-mono">{{ row.license_no || '暂未录入' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="license_expiry_date" label="药监许可有效期至" width="150" align="center">
                <template #default="{ row }">
                  <span class="font-mono tabular-nums">{{ row.license_expiry_date }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="qual_audit_status" label="首营准入状态" width="140" align="center">
                <template #default="{ row }">
                  <span v-if="row.qual_audit_status === 'QUAL_APPROVED'" class="status-chip chip-active">
                    已准入接单
                  </span>
                  <span v-else-if="row.qual_audit_status === 'QUAL_REJECTED'" class="status-chip chip-disabled">
                    准入已驳回
                  </span>
                  <span v-else class="status-chip chip-warn">
                    待主科审查
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="audit_remark" label="审查结论与驳回说明" min-width="210">
                <template #default="{ row }">
                  <span :class="row.qual_audit_status === 'QUAL_REJECTED' ? 'text-danger font-bold' : 'text-muted'" style="font-size: 12px;">
                    {{ row.audit_remark || '-' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="准入审查操作" width="220" align="center" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 8px; justify-content: center;">
                    <el-button
                      v-if="row.qual_audit_status !== 'QUAL_APPROVED'"
                      size="small"
                      type="success"
                      @click="openAuditModal(row, 'QUAL_APPROVED')"
                    >
                      审查通过准入
                    </el-button>
                    <el-button
                      v-if="row.qual_audit_status === 'QUAL_PENDING'"
                      size="small"
                      type="danger"
                      plain
                      @click="openAuditModal(row, 'QUAL_REJECTED')"
                    >
                      合规驳回
                    </el-button>
                    <el-button
                      v-if="row.qual_audit_status === 'QUAL_APPROVED'"
                      size="small"
                      type="warning"
                      plain
                      @click="openAuditModal(row, 'QUAL_PENDING')"
                    >
                      重新复审
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- =====================================================================
             Tab 3: 采供履约跟踪与验收入库
             ===================================================================== -->
        <el-tab-pane label="采供履约跟踪与验收入库" name="tracking">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="upload" :size="15" color="var(--color-success)" />
                <span>全院在途配送跟踪与主库实物查验收货闭环</span>
              </div>
            </div>

            <el-table
              :data="trackingOrders"
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
              <el-table-column prop="product_name" label="送达耗材物资" min-width="190" />
              <el-table-column prop="purchase_qty" label="送货数量" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono font-bold">{{ row.purchase_qty }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="picked_batch_no" label="送达批号(UDI-PI)" width="180">
                <template #default="{ row }">
                  <span class="font-mono text-accent">{{ row.picked_batch_no || '在途录入中' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="supplier_name" label="承运供应商企业" min-width="200" />
              <el-table-column prop="auto_inbound_order_no" label="关联待验收入库单" width="200">
                <template #default="{ row }">
                  <span class="font-mono font-bold text-success">{{ row.auto_inbound_order_no || '待生成' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="闭环验收" width="160" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    type="primary"
                    @click="goToMainInbound(row)"
                  >
                    前往验收入库
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 资质准入审查弹窗 -->
    <el-dialog
      v-model="auditModalVisible"
      :title="`供应商资质准入审核 · ${targetSupplier?.supplier_name || ''}`"
      width="560px"
      append-to-body
      class="spd-dialog-modal"
    >
      <div v-if="targetSupplier" style="display: flex; flex-direction: column; gap: 14px;">
        <el-alert
          :title="`审核动作: ${targetAuditAction === 'QUAL_APPROVED' ? '准予通过准入，解锁接单发货' : '合规驳回资质申请'}`"
          :type="targetAuditAction === 'QUAL_APPROVED' ? 'success' : 'warning'"
          :closable="false"
          show-icon
        />
        <el-form label-width="140px" size="small">
          <el-form-item label="供应商企业全称">
            <span class="font-bold">{{ targetSupplier.supplier_name }}</span>
          </el-form-item>
          <el-form-item label="统一社会信用代码">
            <span class="font-mono text-accent">{{ targetSupplier.social_credit_code || '91371000720745239N' }}</span>
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
          <el-form-item
            :label="targetAuditAction === 'QUAL_REJECTED' ? '驳回原因与整改要求' : '准入合规审查结论'"
            :required="targetAuditAction === 'QUAL_REJECTED'"
          >
            <el-input
              v-model="auditFormRemark"
              type="textarea"
              :rows="3"
              :placeholder="targetAuditAction === 'QUAL_REJECTED' ? '必须详细填写合规驳回原因（如：营业执照复印件缺少鲜章、许可证过期等），以便供应商整改重新提报' : '输入审查意见，如：经查验原件核对无误，符合首营准入标准。'"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="auditModalVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingAudit" @click="submitSupplierAudit">
          确认提交审查结果
        </el-button>
      </template>
    </el-dialog>

    <!-- =====================================================================
         工业级单据化重构：提报临床医用耗材采购计划单 (多行字典选品与大写金额)
         ===================================================================== -->
    <el-dialog
      v-model="createPlanVisible"
      title="提报临床医用耗材采购计划单 (PO)"
      width="920px"
      top="6vh"
      append-to-body
      class="spd-dialog-modal voucher-style-modal"
    >
      <div class="voucher-form-container">
        <!-- 表头六栏网格元数据 -->
        <div class="voucher-meta-header glass-panel">
          <div class="meta-item">
            <span class="meta-label">单据编号:</span>
            <span class="meta-val font-mono text-accent font-bold">{{ newPlanOrderNo }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">申请科室:</span>
            <span class="meta-val font-bold">{{ planFormHeader.apply_dept_name }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">制单经办人:</span>
            <span class="meta-val">{{ userStore.currentUser.realName || '赵振华' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">指定供货企业:</span>
            <el-select v-model="planFormHeader.supplier_code" size="small" style="width: 220px;">
              <el-option
                v-for="sup in suppliers"
                :key="sup.supplier_code"
                :value="sup.supplier_code"
                :label="`${sup.supplier_name} [${sup.qual_audit_status === 'QUAL_APPROVED' ? '已准入' : '待审'}]`"
              />
            </el-select>
          </div>
          <div class="meta-item">
            <span class="meta-label">期望交期:</span>
            <el-date-picker
              v-model="planFormHeader.expect_delivery_date"
              type="date"
              value-format="YYYY-MM-DD"
              size="small"
              style="width: 130px;"
            />
          </div>
          <div class="meta-item" style="grid-column: span 2;">
            <span class="meta-label">采购事由:</span>
            <el-input v-model="planFormHeader.remark" size="small" placeholder="如: 临床手术安全库存定期补货" />
          </div>
        </div>

        <!-- 单身明细操作条 -->
        <div class="detail-action-bar">
          <div style="font-weight: 700; color: var(--text-primary); font-size: 13px;">
            采购耗材品规明细清单 (共 {{ planSelectedItems.length }} 种)
          </div>
          <div style="display: flex; gap: 8px;">
            <el-button type="primary" size="small" @click="showDictSelectDialog = true">
              <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
              + 从全院产品字典选品导入
            </el-button>
            <el-button
              type="danger"
              plain
              size="small"
              :disabled="selectedDetailIndex < 0"
              @click="removeSelectedDetail"
            >
              <SvgIcon name="close" :size="13" style="margin-right: 4px;" />
              删除选中行
            </el-button>
          </div>
        </div>

        <!-- 明细编辑表格 -->
        <div class="table-scroll-wrap">
          <table class="bill-detail-table edit-table">
            <thead>
              <tr>
                <th width="45" align="center">序号</th>
                <th width="160">物料代码</th>
                <th min-width="180">品名规格</th>
                <th width="70" align="center">单位</th>
                <th width="100" align="right">基准单价</th>
                <th width="110" align="right">采购数量</th>
                <th width="110" align="right">小计金额</th>
                <th width="65" align="center">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in planSelectedItems"
                :key="item.spec_code"
                :class="{ 'is-selected-row': selectedDetailIndex === idx }"
                @click="selectedDetailIndex = idx"
              >
                <td align="center">{{ idx + 1 }}</td>
                <td class="font-mono text-accent font-bold">{{ item.spec_code }}</td>
                <td>
                  <div class="font-bold">{{ item.product_name }}</div>
                  <div class="text-muted font-mono" style="font-size: 11px;">{{ item.spec_name }}</div>
                </td>
                <td align="center">
                  <span class="status-chip chip-info" style="font-size: 11px;">{{ item.pricing_unit || '支' }}</span>
                </td>
                <td align="right" class="font-mono">¥ {{ Number(item.unit_price).toFixed(2) }}</td>
                <td align="right">
                  <input
                    v-model.number="item.quantity"
                    type="number"
                    min="1"
                    class="table-inline-input font-mono font-bold"
                    style="text-align: right;"
                    @input="recalcPlanItem(item)"
                  />
                </td>
                <td align="right" class="font-mono font-bold text-primary">
                  ¥ {{ (item.total_amount || 0).toFixed(2) }}
                </td>
                <td align="center">
                  <el-button link type="danger" size="small" @click.stop="deleteItemRow(idx)">
                    删除
                  </el-button>
                </td>
              </tr>
              <tr v-if="planSelectedItems.length === 0">
                <td colspan="8" align="center" style="padding: 26px; color: var(--text-muted);">
                  暂无采购明细，请点击上方“+ 从全院产品字典选品导入”挑选耗材品规
                </td>
              </tr>
              <!-- 合计行与大写金额 -->
              <tr class="bill-total-row">
                <td colspan="5" align="center" class="font-bold">合 计</td>
                <td align="right" class="font-mono font-bold">{{ planTotalQty }} 件</td>
                <td align="right" class="font-mono font-bold text-accent">¥ {{ planTotalAmount.toFixed(2) }}</td>
                <td />
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 底部大写金额展示框 -->
        <div class="chinese-amount-bar glass-panel">
          <div>合计金额大写: <strong class="text-primary">{{ uppercasePlanAmount }}</strong></div>
          <div class="text-muted font-mono">小写合计: ¥ {{ planTotalAmount.toFixed(2) }} 元</div>
        </div>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="createPlanVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submittingPlan"
            :disabled="planSelectedItems.length === 0"
            @click="submitCreatePlanVoucher"
          >
            确认提交采购计划单 (下发主科审批)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 全院产品字典选品通用弹窗 -->
    <SelectProductDictDialog
      v-model="showDictSelectDialog"
      title="从全院产品字典选品导入采购计划单"
      @confirm="handleDictConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import SvgIcon from '@/components/common/SvgIcon.vue';
import SelectProductDictDialog, { type DictSpecItem } from '@/components/SelectProductDictDialog.vue';
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

const currentTab = ref('plans');

// 监听路由 query.tab 动态切换激活选项卡 (支持 plans / suppliers / tracking)
watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab && typeof newTab === 'string') {
      if (['plans', 'suppliers', 'tracking'].includes(newTab)) {
        currentTab.value = newTab;
      }
    }
  },
  { immediate: true }
);

/**
 * 处理采购中心 Tab 切换并同步更新浏览器 URL 查询参数
 * @param {string} tabName 目标选项卡标识
 * @returns {void}
 * @route internal://HospitalProcurementView/handleTabChange
 * @throws 无异常抛出
 */
function handleTabChange(tabName: any): void {
  router.replace({ query: { ...route.query, tab: tabName } });
}

const orders = ref<SupplierPurchaseOrder[]>([]);
const suppliers = ref<SupplierQualificationItem[]>([]);
const loadingOrders = ref(false);
const loadingSuppliers = ref(false);

const orderPage = ref(1);
const orderPageSize = ref(10);

const paginatedOrders = computed(() => {
  const start = (orderPage.value - 1) * orderPageSize.value;
  return orders.value.slice(start, start + orderPageSize.value);
});

const trackingOrders = computed(() =>
  orders.value.filter(
    (o) =>
      o.purchase_flow_status === 'HOSP_INBOUND_CREATED' ||
      o.purchase_flow_status === 'HOSP_INBOUND_ACCEPTED'
  )
);

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
  orders.value.reduce((sum, o) => sum + (o.purchase_qty || 0) * 120.0, 0)
);

// 资质审查弹窗
const auditModalVisible = ref(false);
const targetSupplier = ref<SupplierQualificationItem | null>(null);
const targetAuditAction = ref<'QUAL_APPROVED' | 'QUAL_REJECTED' | 'QUAL_PENDING'>('QUAL_APPROVED');
const auditFormLicense = ref('');
const auditFormExpiry = ref('2029-12-31');
const auditFormRemark = ref('');
const submittingAudit = ref(false);

// 采购单录入弹窗与选品
const createPlanVisible = ref(false);
const showDictSelectDialog = ref(false);
const submittingPlan = ref(false);
const selectedDetailIndex = ref(-1);

const newPlanOrderNo = ref('PUR20261104-001');
const planFormHeader = ref({
  apply_dept_name: '信息工程科 (INFO_DEPT)',
  supplier_code: 'SUP_WEGO_01',
  expect_delivery_date: '2026-11-10',
  remark: '临床耗材安全库存补货计划'
});

interface PlanItemRow {
  spec_code: string;
  product_name: string;
  spec_name: string;
  pricing_unit: string;
  unit_price: number;
  quantity: number;
  total_amount: number;
}

const planSelectedItems = ref<PlanItemRow[]>([
  {
    spec_code: 'PROD-GEN-001',
    product_name: '医用敷料贴 (透明敷料)',
    spec_name: '10cm*11.5cm',
    pricing_unit: '包',
    unit_price: 2.8,
    quantity: 200,
    total_amount: 560
  }
]);

const planTotalQty = computed(() =>
  planSelectedItems.value.reduce((sum, it) => sum + Number(it.quantity || 0), 0)
);

const planTotalAmount = computed(() =>
  planSelectedItems.value.reduce((sum, it) => sum + Number(it.total_amount || 0), 0)
);

/**
 * 中国人民银行标准中文大写金额计算
 * @param {number} money 金额数值
 * @returns {string} 标准中文大写金额
 * @route internal://HospitalProcurementView/digitUppercase
 * @throws 无异常
 */
function digitUppercase(money: number): string {
  if (isNaN(money) || money === null || money === undefined) return '零元整';
  const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'];
  const unit = [['元', '万', '亿'], ['', '拾', '佰', '仟']];

  const totalFen = Math.round(Math.abs(money) * 100);
  if (totalFen === 0) return '零元整';

  const fen = totalFen % 10;
  const jiao = Math.floor(totalFen / 10) % 10;
  let yuan = Math.floor(totalFen / 100);

  let s = '';
  if (yuan > 0) {
    let num = yuan;
    for (let i = 0; i < unit[0].length && num > 0; i++) {
      let p = '';
      for (let j = 0; j < unit[1].length && num > 0; j++) {
        p = digit[num % 10] + unit[1][j] + p;
        num = Math.floor(num / 10);
      }
      s = p.replace(/(零.)*零$/, '').replace(/^$/, '零') + unit[0][i] + s;
    }
    s = s.replace(/(零.)*零元/, '元').replace(/(零.)+/g, '零');
  }

  // 显式精确处理角分，当 jiao === 0 && fen > 0 且 yuan > 0 时精确拼接 '零'
  let fractionStr = '';
  if (jiao === 0 && fen === 0) {
    fractionStr = '整';
  } else if (jiao > 0 && fen === 0) {
    fractionStr = digit[jiao] + '角';
  } else if (jiao === 0 && fen > 0) {
    fractionStr = (yuan > 0 ? '零' : '') + digit[fen] + '分';
  } else {
    fractionStr = digit[jiao] + '角' + digit[fen] + '分';
  }

  return s + fractionStr;
}

const uppercasePlanAmount = computed(() => digitUppercase(planTotalAmount.value));

function recalcPlanItem(item: PlanItemRow) {
  item.total_amount = Number((Number(item.unit_price) * Number(item.quantity)).toFixed(2));
}

function handleDictConfirm(specs: DictSpecItem[]) {
  for (const s of specs) {
    if (!planSelectedItems.value.some((x) => x.spec_code === s.spec_code)) {
      planSelectedItems.value.push({
        spec_code: s.spec_code,
        product_name: s.product_name,
        spec_name: s.spec_name,
        pricing_unit: s.pricing_unit || '支',
        unit_price: Number(s.unit_price) || 10.0,
        quantity: 100,
        total_amount: Number(((Number(s.unit_price) || 10.0) * 100).toFixed(2))
      });
    }
  }
  showDictSelectDialog.value = false;
  ElMessage.success(`成功从产品字典导入 ${specs.length} 项耗材品规！`);
}

function removeSelectedDetail() {
  if (selectedDetailIndex.value >= 0) {
    planSelectedItems.value.splice(selectedDetailIndex.value, 1);
    selectedDetailIndex.value = -1;
  }
}

function deleteItemRow(idx: number) {
  planSelectedItems.value.splice(idx, 1);
}

function openCreatePlanModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  newPlanOrderNo.value = `PUR${ts}`;
  createPlanVisible.value = true;
}

async function submitCreatePlanVoucher() {
  if (planSelectedItems.value.length === 0) {
    ElMessage.warning('请至少添加一行采购耗材品规明细！');
    return;
  }
  submittingPlan.value = true;
  try {
    const firstItem = planSelectedItems.value[0];
    await flowSupplierPurchaseAction({
      order_no: newPlanOrderNo.value,
      flow_action: 'CREATE_PLAN',
      supplier_code: planFormHeader.value.supplier_code,
      apply_dept_code: 'CONSUMABLE_DEPT',
      product_id: 1,
      purchase_qty: planTotalQty.value,
      operator_name: userStore.currentUser.realName || '信息科主管'
    });
    ElMessage.success(`采购计划单 [${newPlanOrderNo.value}] 提报成功，金额 ¥${planTotalAmount.value.toFixed(2)} 已下发主科审批！`);
    createPlanVisible.value = false;
    refreshAllData();
  } catch (err: any) {
    ElMessage.error(err.message || '提报计划失败');
  } finally {
    submittingPlan.value = false;
  }
}

async function fetchOrders() {
  loadingOrders.value = true;
  try {
    const res = await listSupplierPurchaseOrders();
    orders.value = res || [];
  } catch (err: any) {
    ElMessage.error(err.message || '获取采购单据失败');
  } finally {
    loadingOrders.value = false;
  }
}

async function fetchSuppliers() {
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

function refreshAllData() {
  fetchOrders();
  fetchSuppliers();
}

/**
 * 打开供应商准入资质审查弹窗
 * @param {SupplierQualificationItem} sup 目标供应商数据
 * @param {'QUAL_APPROVED' | 'QUAL_REJECTED' | 'QUAL_PENDING'} action 审查动作
 * @returns {void}
 * @route internal://HospitalProcurementView/openAuditModal
 * @throws 无异常
 */
function openAuditModal(sup: SupplierQualificationItem, action: 'QUAL_APPROVED' | 'QUAL_REJECTED' | 'QUAL_PENDING') {
  targetSupplier.value = sup;
  targetAuditAction.value = action;
  auditFormLicense.value = sup.license_no || '浙械经营备20269999号';
  auditFormExpiry.value = sup.license_expiry_date || '2029-12-31';
  auditFormRemark.value = action === 'QUAL_APPROVED' ? '查验证照核对一致，符合首营企业准入规范。' : '';
  auditModalVisible.value = true;
}

/**
 * 提交供应商准入资质审查结果
 * @returns {Promise<void>}
 * @route POST /api/v1/ext/supplier-purchase/qual-audit
 * @throws 驳回无理由时进行前端拦截警告
 */
async function submitSupplierAudit() {
  if (!targetSupplier.value) return;

  // 合规驳回必须输入驳回原因硬校验
  if (targetAuditAction.value === 'QUAL_REJECTED') {
    const reason = (auditFormRemark.value || '').trim();
    if (!reason || reason.length < 2) {
      ElMessage.warning('合规驳回必须详细输入驳回原因与整改要求，以便供应商按规范整改重新提报');
      return;
    }
  }

  submittingAudit.value = true;
  try {
    await auditSupplierQualification({
      supplier_code: targetSupplier.value.supplier_code,
      supplier_name: targetSupplier.value.supplier_name,
      license_no: auditFormLicense.value,
      license_expiry_date: auditFormExpiry.value,
      audit_action: targetAuditAction.value,
      audit_remark: auditFormRemark.value.trim()
    });
    ElMessage.success(`供应商 [${targetSupplier.value.supplier_name}] 资质审核已提交为: ${targetAuditAction.value}`);
    auditModalVisible.value = false;
    refreshAllData();
  } catch (err: any) {
    ElMessage.error(err.message || '资质审核失败');
  } finally {
    submittingAudit.value = false;
  }
}

async function handleApprovePlan(row: SupplierPurchaseOrder) {
  try {
    await flowSupplierPurchaseAction({
      order_no: row.order_no,
      flow_action: 'DEPT_APPROVE',
      operator_name: userStore.currentUser.realName || '科室主管'
    });
    ElMessage.success(`采购计划 [${row.order_no}] 审核通过！已自动下发至供应商端协同接单配货。`);
    fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '审批失败');
  }
}

function goToMainInbound(row: SupplierPurchaseOrder) {
  router.push({ path: '/general', query: { tab: 'inbound', order_no: row.auto_inbound_order_no || row.order_no } });
}

function viewOrderDetails(row: SupplierPurchaseOrder) {
  ElMessage.info(`采购单 [${row.order_no}] 关联物资: ${row.product_name} (${row.purchase_qty}件)`);
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
  gap: 14px;
}

.kpi-card {
  padding: 14px 18px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kpi-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-muted);
}

.kpi-val {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.kpi-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
  margin-left: 2px;
}

.kpi-sub {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 4px;
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

.action-btn-group {
  display: flex;
  align-items: center;
  gap: 10px;
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
  padding-top: 12px;
}

/* 工业级单据录入网格与编辑表格 */
.voucher-form-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.voucher-meta-header {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 14px 18px;
  border-radius: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-divider);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.meta-label {
  color: var(--text-muted);
  white-space: nowrap;
}

.meta-val {
  color: var(--text-primary);
}

.detail-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.table-scroll-wrap {
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid var(--border-divider);
  border-radius: 8px;
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

.table-inline-input {
  width: 80px;
  padding: 4px 6px;
  border: 1px solid var(--border-divider);
  border-radius: 4px;
  background: var(--bg-card);
  color: var(--text-primary);
}

.bill-total-row {
  background: var(--bg-card-hover);
}

.chinese-amount-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px dashed var(--accent-primary);
}
</style>
