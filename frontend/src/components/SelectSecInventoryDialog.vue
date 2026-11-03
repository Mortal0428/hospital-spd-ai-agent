<template>
  <el-dialog
    v-model="visible"
    :title="title || '从本科室在库台账选品导入单据'"
    width="860px"
    append-to-body
    destroy-on-close
    class="fusion-dialog"
  >
    <div class="sec-select-container">
      <div class="search-toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索物料代码、品名或批次号..."
          clearable
          style="width: 320px;"
        >
          <template #prefix>
            <SvgIcon name="search" :size="14" />
          </template>
        </el-input>
        <div class="tip-text">
          当前科室在库物资共 <strong class="text-primary font-mono">{{ inventoryList.length }}</strong> 种
        </div>
      </div>

      <el-table
        ref="tableRef"
        :data="pagedList"
        border
        stripe
        class="fusion-styled-table"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="50" align="center" reserve-selection />
        <el-table-column prop="product_code" label="物料代码" width="150" class-name="font-mono" />
        <el-table-column prop="product_name" label="品名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="spec_model" label="规格型号" width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.spec_name || row.spec_model || '标准规格' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="batch_no" label="生产批次" width="130" class-name="font-mono" />
        <el-table-column prop="expiry_date" label="有效期至" width="115" class-name="font-mono text-muted" />
        <el-table-column prop="available_qty" label="在库可用数" width="110" align="right">
          <template #default="{ row }">
            <span class="font-mono font-bold text-success">{{ row.available_qty || row.current_qty || row.book_qty || 0 }}</span>
            <span class="unit-text" style="margin-left: 4px; font-size: 11px; color: var(--text-muted);">{{ row.unit_name || '件' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit_price" label="基准单价" width="100" align="right">
          <template #default="{ row }">
            <span class="font-mono">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-footer">
        <span class="selected-summary">
          已选中 <strong class="text-primary font-mono">{{ selectedRows.length }}</strong> 项物资
        </span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredList.length"
          :page-sizes="[5, 10, 20]"
          layout="total, sizes, prev, pager, next"
          size="small"
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="selectedRows.length === 0"
          @click="handleConfirm"
        >
          导入选中耗材 ({{ selectedRows.length }})
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @file SelectSecInventoryDialog.vue
 * @description 从本科室在库台账中多选选品导入发料/调拨单据组件 (对标图 3 规范)
 */
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  modelValue: boolean;
  inventoryList: any[];
  title?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
  (e: 'confirm', items: any[]): void;
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const keyword = ref('');
const currentPage = ref(1);
const pageSize = ref(10);
const selectedRows = ref<any[]>([]);

const filteredList = computed(() => {
  const kw = keyword.value.trim().toLowerCase();
  if (!kw) return props.inventoryList || [];
  return (props.inventoryList || []).filter((item: any) =>
    (item.product_code && item.product_code.toLowerCase().includes(kw)) ||
    (item.product_name && item.product_name.toLowerCase().includes(kw)) ||
    (item.batch_no && item.batch_no.toLowerCase().includes(kw))
  );
});

const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredList.value.slice(start, start + pageSize.value);
});

function handleSelectionChange(rows: any[]) {
  selectedRows.value = rows;
}

function handleConfirm() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请至少勾选一种在库耗材');
    return;
  }
  emit('confirm', selectedRows.value);
  visible.value = false;
  selectedRows.value = [];
}
</script>

<style scoped>
.sec-select-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tip-text {
  font-size: 12px;
  color: var(--text-muted);
}

.pagination-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.selected-summary {
  font-size: 12px;
  color: var(--text-muted);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
