<template>
  <el-dialog
    :model-value="modelValue"
    :title="title"
    width="960px"
    append-to-body
    destroy-on-close
    class="spd-dialog-modal select-hv-item-dialog"
    @update:model-value="(val: boolean) => emit('update:modelValue', val)"
  >
    <div class="hv-item-select-container">
      <div class="spec-search-bar" style="margin-bottom: 14px; display: flex; gap: 10px; align-items: center;">
        <div style="position: relative; flex: 1;">
          <input
            v-model="searchKeyword"
            placeholder="搜索单品 UDI 序列号、耗材名称或专柜货位..."
            class="spd-input font-mono"
            style="width: 100%; padding-left: 32px;"
          />
          <span style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </span>
        </div>
        <el-button plain size="small" @click="fetchItems" :loading="loading">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
          </svg>
          刷新在库单品
        </el-button>
      </div>

      <el-table
        :data="filteredItems"
        border
        stripe
        height="380"
        class="fusion-styled-table"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="46" align="center" />
        <el-table-column prop="udi_sn" label="单品 UDI 序列号" width="180" class-name="font-mono text-accent">
          <template #default="{ row }">
            <span class="status-chip chip-info font-mono tabular-nums font-bold">{{ row.udi_sn }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="高值耗材名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="spec_model" label="规格型号" width="140" show-overflow-tooltip />
        <el-table-column prop="wh_cabinet_code" label="专柜存放货位" width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="font-mono" style="font-size: 11px;">{{ row.wh_cabinet_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit_price" label="核算单价" width="110" align="right">
          <template #default="{ row }">
            <span class="font-mono font-bold">¥ {{ Number(row.unit_price).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="item_status" label="在库状态" width="110" align="center">
          <template #default>
            <span class="status-chip chip-active">在库正常</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-meta-bar" style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 12px; color: var(--text-secondary);">
        <span>高值专仓可退在库单品共 {{ allItems.length }} 件 · 命中筛选 {{ filteredItems.length }} 件</span>
        <span>已勾选 <strong class="text-accent font-mono">{{ selectedItems.length }}</strong> 件</span>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
        <el-button @click="handleCancel">取消</el-button>
        <el-button
          type="primary"
          :disabled="selectedItems.length === 0"
          @click="handleConfirm"
          style="user-select: none;"
        >
          导入选中单品 ({{ selectedItems.length }})
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { httpGet } from '../api/request';

export interface HighValueItemRow {
  id: number;
  udi_sn: string;
  product_id?: number;
  product_code: string;
  product_name: string;
  spec_model: string;
  batch_no: string;
  wh_cabinet_code: string;
  unit_price: number;
  item_status: string;
}

const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    title?: string;
  }>(),
  {
    title: '选择高值在库单品'
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'confirm', items: HighValueItemRow[]): void;
}>();

const loading = ref(false);
const allItems = ref<HighValueItemRow[]>([]);
const searchKeyword = ref('');
const selectedItems = ref<HighValueItemRow[]>([]);

const filteredItems = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase();
  if (!kw) return allItems.value;
  return allItems.value.filter(
    (i) =>
      i.udi_sn.toLowerCase().includes(kw) ||
      i.product_name.toLowerCase().includes(kw) ||
      (i.wh_cabinet_code && i.wh_cabinet_code.toLowerCase().includes(kw))
  );
});

function handleSelectionChange(val: HighValueItemRow[]) {
  selectedItems.value = val;
}

function handleCancel() {
  emit('update:modelValue', false);
}

function handleConfirm() {
  emit('confirm', [...selectedItems.value]);
  emit('update:modelValue', false);
  selectedItems.value = [];
}

async function fetchItems(): Promise<void> {
  loading.value = true;
  try {
    const res = await httpGet<any>('/high-value/items?item_status=IN_HIGH_VALUE_WH');
    if (Array.isArray(res)) {
      allItems.value = res;
    } else if (res && res.data && Array.isArray(res.data)) {
      allItems.value = res.data;
    } else {
      allItems.value = getFallbackItems();
    }
  } catch {
    allItems.value = getFallbackItems();
  } finally {
    loading.value = false;
  }
}

function getFallbackItems(): HighValueItemRow[] {
  return [
    {
      id: 1,
      udi_sn: 'SN202610100088',
      product_code: '93601160000100001',
      product_name: '钛合金锁定接骨板螺钉系统',
      spec_model: '胫骨远端外侧锁定板 8孔 左侧',
      batch_no: 'B20261010',
      wh_cabinet_code: '高值专仓-智能专柜01-A01格',
      unit_price: 4200.0,
      item_status: 'IN_HIGH_VALUE_WH'
    },
    {
      id: 2,
      udi_sn: 'SN202610100089',
      product_code: '93601160000100001',
      product_name: '钛合金锁定接骨板螺钉系统',
      spec_model: '胫骨近端内侧锁定板 6孔 右侧',
      batch_no: 'B20261010',
      wh_cabinet_code: '高值专仓-智能专柜01-A02格',
      unit_price: 4200.0,
      item_status: 'IN_HIGH_VALUE_WH'
    },
    {
      id: 3,
      udi_sn: 'SN202610100090',
      product_code: '93601160000100002',
      product_name: '药物洗脱冠状动脉支架系统',
      spec_model: '支架直径 3.0mm * 长度 18mm',
      batch_no: 'B20261015',
      wh_cabinet_code: '高值专仓-智能专柜02-B01格',
      unit_price: 6480.0,
      item_status: 'IN_HIGH_VALUE_WH'
    }
  ];
}

watch(
  () => props.modelValue,
  (val) => {
    if (val && allItems.value.length === 0) {
      fetchItems();
    }
  }
);

onMounted(() => {
  fetchItems();
});
</script>

<style scoped>
.select-hv-item-dialog :deep(.el-dialog__body) {
  padding: 16px 20px;
}
</style>
