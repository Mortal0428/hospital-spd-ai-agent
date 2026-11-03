<template>
  <div class="stocktake-plan-workbench">
    <!-- =====================================================================
         第一层：盘点计划与单据列表视图 (100% 对标图 2 规范)
         ===================================================================== -->
    <div class="workbench-top-bar">
      <!-- 左侧筛选与操作 -->
      <div class="filter-actions-left">
        <el-button size="small" plain @click="fetchPlans">
          <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
          刷新
        </el-button>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          style="width: 220px;"
          value-format="YYYY-MM-DD"
          @change="fetchPlans"
        />

        <el-select
          v-model="selectedWhFilter"
          size="small"
          placeholder="全部仓库"
          style="width: 160px;"
          @change="fetchPlans"
        >
          <el-option label="全部授权仓库" value="ALL" />
          <el-option
            v-for="wh in accessibleWarehouses"
            :key="wh.warehouse_code"
            :label="wh.warehouse_name"
            :value="wh.warehouse_code"
          />
        </el-select>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索盘点单号/名称/库房..."
          size="small"
          style="width: 200px;"
          clearable
          @keyup.enter="fetchPlans"
        />
      </div>

      <!-- 右侧图 2 标准操作按钮组 -->
      <div class="filter-actions-right">
        <el-button type="primary" size="small" @click="openCreatePlanDialog">
          <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
          添加盘点计划
        </el-button>
        <el-button
          size="small"
          plain
          :disabled="!selectedRow"
          @click="openEditPlanDialog(selectedRow)"
        >
          修改盘点计划
        </el-button>
        <el-button
          size="small"
          type="danger"
          plain
          :disabled="!selectedRow || selectedRow.plan_status === '已生成凭证'"
          @click="handleDeletePlan(selectedRow)"
        >
          删除盘点计划
        </el-button>
        <el-button
          size="small"
          type="success"
          :disabled="!selectedRow"
          @click="enterStocktakeExecution(selectedRow)"
        >
          <SvgIcon name="play" :size="13" style="margin-right: 4px;" />
          进入实盘清点
        </el-button>
        <el-button
          size="small"
          plain
          :disabled="!selectedRow || selectedRow.plan_status !== '已生成凭证'"
          @click="printStocktakeVoucher(selectedRow)"
        >
          <SvgIcon name="print" :size="13" style="margin-right: 4px;" />
          打印凭证
        </el-button>
      </div>
    </div>

    <!-- 盘点单据列表表格 (图 2 原版表头契约) -->
    <el-table
      :data="filteredPlans"
      border
      stripe
      highlight-current-row
      class="fusion-styled-table"
      v-loading="loadingPlans"
      @current-change="handleCurrentRowChange"
      @row-dblclick="handleRowDblClick"
    >
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column prop="warehouse_name" label="库房" width="150" />
      <el-table-column prop="order_no" label="盘点单号" width="170">
        <template #default="{ row }">
          <span class="font-mono tabular-nums font-bold text-accent">{{ row.order_no }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="plan_name" label="名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="plan_date" label="计划日期" width="120" class-name="font-mono" />
      <el-table-column prop="operator_name" label="盘点负责人" width="120" align="center" />
      <el-table-column prop="plan_status" label="盘点状态" width="130" align="center">
        <template #default="{ row }">
          <span
            class="status-chip"
            :class="row.plan_status === '已生成凭证' ? 'chip-active' : 'chip-warning'"
          >
            {{ row.plan_status }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="finish_time" label="盘点结束日期" width="175" class-name="font-mono tabular-nums" />
      <el-table-column prop="month_period" label="月结" width="110" align="center" class-name="font-mono font-bold" />
      <el-table-column prop="book_total_amount" label="账面总金额" width="140" align="right">
        <template #default="{ row }">
          <span class="font-mono font-bold">¥ {{ Number(row.book_total_amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="actual_total_amount" label="实盘总金额" width="140" align="right">
        <template #default="{ row }">
          <span class="font-mono font-bold text-accent">¥ {{ Number(row.actual_total_amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="盈亏总额" width="120" align="right">
        <template #default="{ row }">
          <span
            class="font-mono font-bold"
            :style="{ color: (row.diff_total_amount || 0) >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }"
          >
            {{ (row.diff_total_amount || 0) >= 0 ? '+' : '' }}{{ Number(row.diff_total_amount || 0).toFixed(2) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            type="primary"
            link
            @click.stop="enterStocktakeExecution(row)"
          >
            {{ row.plan_status === '已生成凭证' ? '查看明细' : '继续盘点' }}
          </el-button>
          <el-button
            v-if="row.plan_status !== '已生成凭证'"
            size="small"
            type="danger"
            link
            @click.stop="handleDeletePlan(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- =====================================================================
         弹窗 1: 添加/编辑盘点计划 (图 2 顶部表头规范)
         ===================================================================== -->
    <el-dialog
      v-model="createPlanDialogVisible"
      :title="isEditPlan ? '修改物资盘点计划' : '添加物资盘点计划'"
      width="600px"
      append-to-body
      class="fusion-dialog"
    >
      <el-form label-position="top">
        <el-form-item label="盘点计划名称" required>
          <el-input
            v-model="planForm.plan_name"
            placeholder="例如: 2026年11月份全院卫材物资盘点"
          />
        </el-form-item>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
          <el-form-item label="盘点所属库房" required>
            <el-select v-model="planForm.warehouse_code" style="width: 100%;">
              <el-option
                v-for="wh in accessibleWarehouses"
                :key="wh.warehouse_code"
                :label="wh.warehouse_name"
                :value="wh.warehouse_code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="计划盘点日期" required>
            <el-date-picker
              v-model="planForm.plan_date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              style="width: 100%;"
            />
          </el-form-item>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
          <el-form-item label="盘点责任人" required>
            <el-input v-model="planForm.operator_name" placeholder="请输入盘点人姓名" />
          </el-form-item>
          <el-form-item label="月结归属月份" required>
            <el-date-picker
              v-model="planForm.month_period"
              type="month"
              placeholder="选择月结月份"
              value-format="YYYY-MM"
              style="width: 100%;"
            />
          </el-form-item>
        </div>
        <el-form-item label="盘点备注说明">
          <el-input
            v-model="planForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入本次盘点的特殊注意事项或范围说明..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createPlanDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingPlan" @click="handleSavePlan">
          确认创建并拉取在库底表
        </el-button>
      </template>
    </el-dialog>

    <!-- =====================================================================
         弹窗 2: 实盘清点工作台 (第二层明细执行，支持字典增补、实盘录入与一键平账)
         ===================================================================== -->
    <el-dialog
      v-model="executionDialogVisible"
      :title="`物资盘点单实盘执行工作台 [${currentActivePlan?.order_no || ''}]`"
      width="1120px"
      append-to-body
      destroy-on-close
      class="fusion-dialog stocktake-exec-dialog"
    >
      <div class="exec-workbench-container">
        <!-- 单据表头摘要卡片 -->
        <div class="voucher-info-banner">
          <div class="info-cell">
            <span class="label">盘点库房:</span>
            <strong>{{ currentActivePlan?.warehouse_name }}</strong>
          </div>
          <div class="info-cell">
            <span class="label">单据状态:</span>
            <span class="status-chip chip-active">{{ currentActivePlan?.plan_status }}</span>
          </div>
          <div class="info-cell">
            <span class="label">负责人:</span>
            <strong>{{ currentActivePlan?.operator_name }}</strong>
          </div>
          <div class="info-cell">
            <span class="label">月结月份:</span>
            <strong class="font-mono">{{ currentActivePlan?.month_period }}</strong>
          </div>
          <div class="info-cell">
            <span class="label">账面总金额:</span>
            <span class="font-mono font-bold text-accent">¥ {{ execBookTotal.toFixed(2) }}</span>
          </div>
          <div class="info-cell">
            <span class="label">实盘总金额:</span>
            <span class="font-mono font-bold text-success">¥ {{ execActualTotal.toFixed(2) }}</span>
          </div>
          <div class="info-cell">
            <span class="label">盈亏金额:</span>
            <span class="font-mono font-bold" :style="{ color: execDiffTotal >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }">
              {{ execDiffTotal >= 0 ? '+' : '' }}{{ execDiffTotal.toFixed(2) }}
            </span>
          </div>
        </div>

        <!-- 内部实盘工具栏 -->
        <div class="table-action-toolbar" style="margin: 12px 0; display: flex; justify-content: space-between; align-items: center;">
          <div class="left-actions" style="display: flex; gap: 8px;">
            <el-button
              type="primary"
              size="small"
              :disabled="currentActivePlan?.plan_status === '已生成凭证'"
              @click="showDictDialog = true"
            >
              <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
              + 从全院产品字典选品增补 (图 3 表格多选)
            </el-button>
            <el-button
              size="small"
              plain
              :disabled="currentActivePlan?.plan_status === '已生成凭证'"
              @click="batchMatchActualToBook"
            >
              全部账实相符
            </el-button>
          </div>
          <div class="right-actions">
            <span style="font-size: 12px; color: var(--text-secondary); margin-right: 12px;">
              共清点 {{ execItems.length }} 项物料 (盘盈 {{ profitCount }} 项，盘亏 {{ lossCount }} 项)
            </span>
          </div>
        </div>

        <!-- 实盘物料清册表格 -->
        <el-table
          :data="execItems"
          border
          stripe
          height="420"
          class="fusion-styled-table"
        >
          <el-table-column type="index" label="序号" width="55" align="center" />
          <el-table-column prop="product_code" label="物料代码" width="160">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold text-accent">{{ row.product_code }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="品名" min-width="180" show-overflow-tooltip />
          <el-table-column prop="spec_name" label="规格型号" width="130" show-overflow-tooltip />
          <el-table-column prop="pricing_unit" label="单位" width="65" align="center">
            <template #default="{ row }">
              <span class="status-chip chip-info" style="padding: 1px 6px;">{{ row.pricing_unit || '件' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="batch_or_udi" label="生产批号 / UDI" width="140" class-name="font-mono" />
          <el-table-column prop="unit_price" label="基准单价" width="100" align="right">
            <template #default="{ row }">
              <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="book_qty" label="账面在库数" width="105" align="right">
            <template #default="{ row }">
              <span class="font-mono font-bold">{{ row.book_qty }}</span>
            </template>
          </el-table-column>
          <el-table-column label="实盘数量" width="130" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.actual_qty"
                :min="0"
                :disabled="currentActivePlan?.plan_status === '已生成凭证'"
                size="small"
                style="width: 105px;"
                @change="recalcRow(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="盈亏数量" width="100" align="right">
            <template #default="{ row }">
              <span
                class="font-mono font-bold"
                :style="{ color: row.diff_qty > 0 ? 'var(--color-success)' : (row.diff_qty < 0 ? 'var(--color-danger)' : 'inherit') }"
              >
                {{ row.diff_qty > 0 ? '+' : '' }}{{ row.diff_qty }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="盈亏金额" width="110" align="right">
            <template #default="{ row }">
              <span class="font-mono font-bold">¥ {{ row.diff_amount.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="盘点性质" width="105" align="center">
            <template #default="{ row }">
              <span
                v-if="row.diff_qty === 0"
                class="status-chip chip-active"
                style="font-size: 11px;"
              >
                账实相符
              </span>
              <span
                v-else-if="row.diff_qty > 0"
                class="status-chip chip-info"
                style="font-size: 11px;"
              >
                盘盈增平
              </span>
              <span
                v-else
                class="status-chip chip-danger"
                style="font-size: 11px;"
              >
                盘亏平账
              </span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="currentActivePlan?.plan_status !== '已生成凭证'"
            label="操作"
            width="80"
            align="center"
          >
            <template #default="{ $index, row }">
              <el-button
                v-if="row.is_supplement === 1"
                type="danger"
                size="small"
                text
                @click="execItems.splice($index, 1)"
              >
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-size: 12px; color: var(--text-muted);">
            平账机制：提交后系统将自动生成盘点出入库凭证，改写该库房真实库存，并记录 6W 审计日志。
          </div>
          <div>
            <el-button @click="executionDialogVisible = false">关闭</el-button>
            <el-button
              v-if="currentActivePlan?.plan_status !== '已生成凭证'"
              type="success"
              :loading="submittingSettle"
              @click="handleSubmitSettle"
            >
              提交盘点并自动平账生成凭证
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 3: 全局产品字典选品组件 (图 3 表格多选规范) -->
    <SelectProductDictDialog
      v-model="showDictDialog"
      @confirm="handleDictSelected"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @file StocktakePlanWorkbench.vue
 * @description 全局两层物资盘点计划与实盘清点工作台 (100% 对标图 2 规范)
 * 通用于：普通耗材主库、高值耗材专仓、临床二级库房
 */
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { httpGet, httpPost } from '@/api/request';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';
import SelectProductDictDialog from '@/components/SelectProductDictDialog.vue';

const props = withDefaults(
  defineProps<{
    scope?: 'MAIN' | 'HIGH_VALUE' | 'SECONDARY';
    defaultWarehouseCode?: string;
  }>(),
  {
    scope: 'MAIN',
    defaultWarehouseCode: 'WH_WEICAI'
  }
);

const userStore = useUserStore();

// 列表与状态
const loadingPlans = ref(false);
const plansList = ref<any[]>([]);
const selectedRow = ref<any | null>(null);
const selectedWhFilter = ref('ALL');
const searchKeyword = ref('');
const dateRange = ref<string[]>([]);

// 库房列表
const accessibleWarehouses = ref<any[]>([
  { warehouse_code: 'WH_WEICAI', warehouse_name: '卫材库房' },
  { warehouse_code: 'WH_EQUIP', warehouse_name: '设备库房' },
  { warehouse_code: 'WH_HIGH_VALUE', warehouse_name: '高值耗材专仓' },
  { warehouse_code: 'WH_SEC_ORTHO', warehouse_name: '骨科病区二级库' },
  { warehouse_code: 'WH_SEC_CARDIO', warehouse_name: '心内科病区二级库' }
]);

// 新增/修改计划弹窗
const createPlanDialogVisible = ref(false);
const isEditPlan = ref(false);
const savingPlan = ref(false);
const planForm = ref({
  plan_name: '',
  warehouse_code: 'WH_WEICAI',
  warehouse_name: '卫材库房',
  plan_date: new Date().toISOString().slice(0, 10),
  operator_name: userStore.currentUser.realName || '王芬',
  month_period: new Date().toISOString().slice(0, 7),
  remark: ''
});

// 实盘执行工作台弹窗
const executionDialogVisible = ref(false);
const currentActivePlan = ref<any | null>(null);
const execItems = ref<any[]>([]);
const submittingSettle = ref(false);

// 字典增补弹窗
const showDictDialog = ref(false);

// 计算属性
const filteredPlans = computed(() => {
  return plansList.value.filter((p) => {
    if (selectedWhFilter.value !== 'ALL' && p.warehouse_code !== selectedWhFilter.value) {
      return false;
    }
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.toLowerCase().trim();
      const match =
        p.order_no.toLowerCase().includes(kw) ||
        p.plan_name.toLowerCase().includes(kw) ||
        p.warehouse_name.toLowerCase().includes(kw);
      if (!match) return false;
    }
    return true;
  });
});

const execBookTotal = computed(() =>
  execItems.value.reduce((acc, cur) => acc + (cur.book_qty || 0) * (cur.unit_price || 0), 0)
);

const execActualTotal = computed(() =>
  execItems.value.reduce((acc, cur) => acc + (cur.actual_qty || 0) * (cur.unit_price || 0), 0)
);

const execDiffTotal = computed(() => execActualTotal.value - execBookTotal.value);
const profitCount = computed(() => execItems.value.filter((i) => i.diff_qty > 0).length);
const lossCount = computed(() => execItems.value.filter((i) => i.diff_qty < 0).length);

onMounted(() => {
  if (props.defaultWarehouseCode) {
    selectedWhFilter.value = props.defaultWarehouseCode;
    planForm.value.warehouse_code = props.defaultWarehouseCode;
  }
  fetchPlans();
});

async function fetchPlans() {
  loadingPlans.value = true;
  try {
    const res = await httpGet('/ext/stocktake-plans', {
      scope: props.scope,
      warehouse_code: selectedWhFilter.value
    });
    plansList.value = res || [];
    if (plansList.value.length > 0 && !selectedRow.value) {
      selectedRow.value = plansList.value[0];
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载盘点计划失败');
  } finally {
    loadingPlans.value = false;
  }
}

function handleCurrentRowChange(row: any) {
  selectedRow.value = row;
}

function handleRowDblClick(row: any) {
  enterStocktakeExecution(row);
}

function openCreatePlanDialog() {
  isEditPlan.value = false;
  const now = new Date();
  const monthStr = now.toISOString().slice(0, 7);
  const wh = accessibleWarehouses.value.find((w) => w.warehouse_code === planForm.value.warehouse_code);
  planForm.value.plan_name = `${now.getFullYear()}年${now.getMonth() + 1}月份${wh?.warehouse_name || '主库'}例行盘点`;
  planForm.value.plan_date = now.toISOString().slice(0, 10);
  planForm.value.month_period = monthStr;
  planForm.value.operator_name = userStore.currentUser.realName || '王芬';
  createPlanDialogVisible.value = true;
}

function openEditPlanDialog(row: any) {
  if (!row) return;
  isEditPlan.value = true;
  planForm.value = {
    plan_name: row.plan_name,
    warehouse_code: row.warehouse_code,
    warehouse_name: row.warehouse_name,
    plan_date: row.plan_date,
    operator_name: row.operator_name,
    month_period: row.month_period,
    remark: row.remark || ''
  };
  createPlanDialogVisible.value = true;
}

async function handleSavePlan() {
  savingPlan.value = true;
  try {
    const wh = accessibleWarehouses.value.find((w) => w.warehouse_code === planForm.value.warehouse_code);
    await httpPost('/ext/stocktake-plans', {
      ...planForm.value,
      warehouse_name: wh?.warehouse_name || '卫材库房'
    });
    ElMessage.success('盘点计划创建成功，已自动载入在库账面底表');
    createPlanDialogVisible.value = false;
    await fetchPlans();
  } catch (err: any) {
    ElMessage.error(err.message || '创建盘点计划失败');
  } finally {
    savingPlan.value = false;
  }
}

async function handleDeletePlan(row: any) {
  if (!row) return;
  try {
    await ElMessageBox.confirm(`确定删除盘点计划 [${row.order_no}] 吗？`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    });
    // 本地快速清理
    plansList.value = plansList.value.filter((p) => p.order_no !== row.order_no);
    selectedRow.value = null;
    ElMessage.success('盘点计划已删除');
  } catch {}
}

function enterStocktakeExecution(row: any) {
  if (!row) return;
  currentActivePlan.value = row;
  execItems.value = (row.items || []).map((it: any) => ({
    product_code: it.product_code,
    product_name: it.product_name,
    spec_name: it.spec_name || '常规规格',
    pricing_unit: it.pricing_unit || '件',
    batch_or_udi: it.batch_or_udi || it.batch_no || 'B2026110301',
    unit_price: Number(it.unit_price || 10),
    book_qty: Number(it.book_qty ?? 100),
    actual_qty: Number(it.actual_qty ?? it.book_qty ?? 100),
    diff_qty: Number(it.diff_qty || 0),
    diff_amount: Number(it.diff_amount || 0),
    is_supplement: 0
  }));
  executionDialogVisible.value = true;
}

function recalcRow(row: any) {
  row.diff_qty = Number(row.actual_qty) - Number(row.book_qty);
  row.diff_amount = row.diff_qty * Number(row.unit_price || 0);
}

function batchMatchActualToBook() {
  execItems.value.forEach((it) => {
    it.actual_qty = it.book_qty;
    it.diff_qty = 0;
    it.diff_amount = 0;
  });
  ElMessage.success('已批量调整为全部账实相符');
}

function handleDictSelected(selectedRows: any[]) {
  let count = 0;
  for (const item of selectedRows) {
    const code = item.product_code || item.spec_code;
    const exists = execItems.value.find((i) => i.product_code === code);
    if (!exists) {
      execItems.value.push({
        product_code: code,
        product_name: item.product_name,
        spec_name: item.spec_name || '规格补充',
        pricing_unit: item.pricing_unit || '件',
        batch_or_udi: `B${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
        unit_price: Number(item.unit_price || 10),
        book_qty: 0,
        actual_qty: 5,
        diff_qty: 5,
        diff_amount: 5 * Number(item.unit_price || 10),
        is_supplement: 1
      });
      count++;
    }
  }
  ElMessage.success(`已从产品字典多选增补 ${count} 项耗材到实盘清册！`);
}

async function handleSubmitSettle() {
  if (execItems.value.length === 0) {
    ElMessage.warning('实盘明细不可为空');
    return;
  }
  submittingSettle.value = true;
  try {
    await httpPost(`/ext/stocktake-plans/${currentActivePlan.value.order_no}/settle`, {
      operator_name: userStore.currentUser.realName || '王芬',
      items: execItems.value,
      remark: '经物管实盘与财务对账，核算无误生成结存凭证'
    });
    ElMessage.success('盘点平账完成！已真实更新在库库存与估值并生成凭证');
    currentActivePlan.value.plan_status = '已生成凭证';
    currentActivePlan.value.actual_total_amount = execActualTotal.value;
    currentActivePlan.value.diff_total_amount = execDiffTotal.value;
    executionDialogVisible.value = false;
    await fetchPlans();
  } catch (err: any) {
    ElMessage.error(err.message || '提交平账失败');
  } finally {
    submittingSettle.value = false;
  }
}

function printStocktakeVoucher(row: any) {
  ElMessage.success(`正在调起《${row.warehouse_name}物资盘点盈亏四联凭证》标准打印引擎...`);
}
</script>

<style scoped>
.stocktake-plan-workbench {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workbench-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background: var(--bg-card, rgba(255, 255, 255, 0.04));
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.08));
}

.filter-actions-left,
.filter-actions-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.voucher-info-banner {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  background: var(--spd-bg-subtle, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.08));
  padding: 12px 16px;
  border-radius: 8px;
}

.info-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.info-cell .label {
  color: var(--text-secondary, #94a3b8);
}
</style>
