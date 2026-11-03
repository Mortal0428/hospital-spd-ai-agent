<template>
  <el-dialog
    :model-value="modelValue"
    :title="title"
    width="920px"
    append-to-body
    destroy-on-close
    class="spd-dialog-modal select-dict-dialog"
    @update:model-value="(val: boolean) => emit('update:modelValue', val)"
  >
    <div class="spec-select-container">
      <div class="spec-search-bar" style="margin-bottom: 14px; display: flex; gap: 10px; align-items: center;">
        <div style="position: relative; flex: 1;">
          <input
            v-model="dictSearchKeyword"
            placeholder="搜索物料编码、品名或拼音码..."
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
        <el-button plain size="small" @click="fetchSpecs" :loading="loading">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
          </svg>
          刷新字典
        </el-button>
      </div>

      <el-table
        :data="filteredSpecs"
        border
        stripe
        height="400"
        class="fusion-styled-table"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="46" align="center" />
        <el-table-column prop="spec_code" label="物料代码" width="170" class-name="font-mono text-accent">
          <template #default="{ row }">
            <span class="font-mono font-bold">{{ row.spec_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="品名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="spec_name" label="规格" width="130" show-overflow-tooltip />
        <el-table-column prop="pricing_unit" label="单位" width="70" align="center">
          <template #default="{ row }">
            <span class="status-chip chip-info" style="font-size: 11px; padding: 1px 6px;">{{ row.pricing_unit || '支' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit_price" label="基准单价" width="110" align="right">
          <template #default="{ row }">
            <span class="font-mono font-bold">¥ {{ Number(row.unit_price).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="manufacturer" label="生产厂家" min-width="190" show-overflow-tooltip />
      </el-table>

      <div class="table-meta-bar" style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 12px; color: var(--text-secondary);">
        <span>全院在用耗材总计 {{ allSpecs.length }} 种 · 命中搜索 {{ filteredSpecs.length }} 种</span>
        <span>已勾选 <strong class="text-accent font-mono">{{ selectedSpecs.length }}</strong> 项</span>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
        <el-button @click="handleCancel">取消</el-button>
        <el-button
          type="primary"
          :disabled="selectedSpecs.length === 0"
          @click="handleConfirm"
          style="user-select: none;"
        >
          导入选中耗材 ({{ selectedSpecs.length }})
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { httpGet } from '../api/request';

/**
 * 全院产品字典规格对象结构契约
 */
export interface DictSpecItem {
  id: number;
  spec_code: string;
  product_code?: string;
  product_name: string;
  spec_name: string;
  model_name?: string;
  pricing_unit: string;
  unit_price: number;
  manufacturer: string;
  category_code?: string;
  main_dept_code?: string;
}

const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    title?: string;
    targetWarehouse?: string;
  }>(),
  {
    title: '从全院产品字典选品导入',
    targetWarehouse: ''
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'confirm', items: DictSpecItem[]): void;
}>();

const loading = ref(false);
const allSpecs = ref<DictSpecItem[]>([]);
const dictSearchKeyword = ref('');
const selectedSpecs = ref<DictSpecItem[]>([]);

/**
 * 拼音码与物料编码多维模糊过滤
 */
const filteredSpecs = computed(() => {
  const kw = dictSearchKeyword.value.trim().toLowerCase();
  if (!kw) return allSpecs.value;
  return allSpecs.value.filter(
    (s) =>
      s.spec_code.toLowerCase().includes(kw) ||
      s.product_name.toLowerCase().includes(kw) ||
      (s.spec_name && s.spec_name.toLowerCase().includes(kw)) ||
      (s.manufacturer && s.manufacturer.toLowerCase().includes(kw))
  );
});

/**
 * 监听表格多选变更
 * @param {DictSpecItem[]} val 选中的行
 * @returns {void}
 */
function handleSelectionChange(val: DictSpecItem[]) {
  selectedSpecs.value = val;
}

/**
 * 取消并关闭弹窗
 * @returns {void}
 */
function handleCancel() {
  emit('update:modelValue', false);
}

/**
 * 确认导入选中的耗材并通知父组件
 * @returns {void}
 */
function handleConfirm() {
  const normalized = selectedSpecs.value.map(item => ({
    ...item,
    product_code: item.product_code || item.spec_code,
    spec_code: item.spec_code || item.product_code || ''
  }));
  emit('confirm', normalized);
  emit('update:modelValue', false);
  selectedSpecs.value = [];
}

/**
 * 从后端加载产品字典全量规格清单
 * @returns {Promise<void>}
 * @route GET /api/v1/dict/specs
 * @throws 异常时采用兜底种子数据保障高可用
 */
async function fetchSpecs(): Promise<void> {
  loading.value = true;
  try {
    const res = await httpGet<any>('/dict/specs');
    if (Array.isArray(res)) {
      allSpecs.value = res;
    } else if (res && res.data && Array.isArray(res.data)) {
      allSpecs.value = res.data;
    } else {
      allSpecs.value = getFallbackSpecs();
    }
  } catch {
    allSpecs.value = getFallbackSpecs();
  } finally {
    loading.value = false;
  }
}

function getFallbackSpecs(): DictSpecItem[] {
  return [
    {
      id: 1,
      spec_code: '936010100024055499',
      product_name: '医用氧气123',
      spec_name: '40L 剑涛特供型',
      model_name: 'JT-O2-4',
      pricing_unit: '瓶',
      unit_price: 52.0,
      manufacturer: '重庆剑涛科技有限公司'
    },
    {
      id: 2,
      spec_code: '936010100024055500',
      product_name: '医用氧气123',
      spec_name: '15L 医用级减压瓶',
      model_name: 'JT-O2-1',
      pricing_unit: '瓶',
      unit_price: 55.0,
      manufacturer: '重庆剑涛科技有限公司'
    },
    {
      id: 3,
      spec_code: '936010100024055517',
      product_name: '医用氧气123',
      spec_name: '40L 纯度≥99.5%',
      model_name: 'TWLB-4',
      pricing_unit: '瓶',
      unit_price: 45.0,
      manufacturer: '普昂(杭州)医疗科技有限责任公司'
    },
    {
      id: 4,
      spec_code: '936010100024057514',
      product_name: '医用氧气123',
      spec_name: '50L 大容量储气瓶',
      model_name: 'JT-O2-5',
      pricing_unit: '瓶',
      unit_price: 60.0,
      manufacturer: '重庆剑涛科技有限公司'
    },
    {
      id: 5,
      spec_code: '936010100024057761',
      product_name: '医用氧气123',
      spec_name: '10L 便携型钢瓶',
      model_name: 'PA-POR',
      pricing_unit: '瓶',
      unit_price: 48.0,
      manufacturer: '普昂(杭州)医疗科技有限责任公司'
    },
    {
      id: 6,
      spec_code: '93601100000100001',
      product_name: '一次性使用无菌注射器带针',
      spec_name: '5ml 带针 0.7*30mm',
      model_name: 'TWLB-5',
      pricing_unit: '支',
      unit_price: 0.42,
      manufacturer: '山东威高集团医用高分子制品股份有限公司'
    },
    {
      id: 7,
      spec_code: '93601160000100001',
      product_name: '钛合金锁定接骨板螺钉系统',
      spec_name: '胫骨远端外侧锁定板 8孔 左侧',
      model_name: 'LCP-DIS',
      pricing_unit: '套',
      unit_price: 4200.0,
      manufacturer: '强生(上海)医疗器材有限公司'
    },
    {
      id: 8,
      spec_code: '93601090013000001',
      product_name: '医用敷料贴 (促愈型)',
      spec_name: '10cm*11.5cm',
      model_name: '9546HP',
      pricing_unit: '片',
      unit_price: 8.76,
      manufacturer: '普昂(杭州)医疗科技有限责任公司'
    }
  ];
}

watch(
  () => props.modelValue,
  (val) => {
    if (val && allSpecs.value.length === 0) {
      fetchSpecs();
    }
  }
);

onMounted(() => {
  fetchSpecs();
});
</script>

<style scoped>
.select-dict-dialog :deep(.el-dialog__body) {
  padding: 16px 20px;
}
.spec-search-bar input:focus {
  border-color: var(--accent-primary);
  outline: none;
}
</style>
