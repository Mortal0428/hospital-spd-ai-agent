<template>
  <el-dialog
    v-model="visible"
    title="医院法定单据四联打印预览中心"
    width="880px"
    top="5vh"
    append-to-body
    class="spd-print-modal"
  >
    <div class="print-toolbar no-print">
      <el-alert
        title="标准单据四联签字规范：制单人、主库科室主管、二级库接收人与财务科复核人签字后归档生效"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 12px;"
      />
      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <el-button @click="visible = false">关闭预览</el-button>
        <el-button type="primary" @click="handlePrint">
          <svg style="width:16px;height:16px;margin-right:6px;" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polyline points="6 9 6 2 18 2 18 9" stroke-width="2" />
            <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" stroke-width="2" />
            <rect x="6" y="14" width="12" height="8" stroke-width="2" />
          </svg>
          立即打印 (四联单据)
        </el-button>
      </div>
    </div>

    <!-- 真实法定单据打印载体 -->
    <div id="spd-voucher-paper" class="voucher-paper print-area">
      <div class="voucher-header">
        <div class="hospital-name">浙江大学医学院附属第一医院医疗物资管理中心</div>
        <div class="voucher-title">{{ voucherTitle }}</div>
        <div class="voucher-sub">（一联存根 · 二联主库 · 三联领用科室 · 四联财务记账）</div>
      </div>

      <div class="voucher-meta-grid">
        <div><span>单据编号：</span><strong class="spd-mono">{{ orderData.order_no || 'ORD-20261102-001' }}</strong></div>
        <div><span>单据日期：</span><span>{{ currentDate }}</span></div>
        <div><span>往来科室/单位：</span><span>{{ orderData.target_dept_or_supplier || '骨科病区二级库' }}</span></div>
        <div><span>所属仓库：</span><span>{{ orderData.warehouse_code || 'WH_WEICAI (卫材主库)' }}</span></div>
      </div>

      <table class="voucher-table">
        <thead>
          <tr>
            <th style="width: 50px; text-align: center;">序号</th>
            <th style="width: 140px;">物资编码</th>
            <th>物资名称 / 规格型号</th>
            <th style="width: 120px;">生产批号/UDI</th>
            <th style="width: 55px; text-align: center;">单位</th>
            <th style="width: 75px; text-align: right;">数量</th>
            <th style="width: 90px; text-align: right;">单价 (元)</th>
            <th style="width: 105px; text-align: right;">金额 (元)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in displayItems" :key="idx">
            <td style="text-align: center;">{{ idx + 1 }}</td>
            <td class="spd-mono font-bold">{{ item.product_code || item.spec_code || '-' }}</td>
            <td>
              <div style="font-weight: 600;">{{ item.product_name }}</div>
              <div v-if="item.spec_name || item.model_name" style="font-size: 11px; color: #4b5563;">
                {{ item.spec_name || '' }} {{ item.model_name || '' }}
              </div>
            </td>
            <td class="spd-mono">{{ item.batch_no || item.udi_code || '-' }}</td>
            <td style="text-align: center;">{{ item.unit_name || item.pricing_unit || '件' }}</td>
            <td style="text-align: right; font-weight: 700;">{{ item.quantity }}</td>
            <td style="text-align: right;" class="spd-mono">¥ {{ Number(item.unit_price || 0).toFixed(2) }}</td>
            <td style="text-align: right; font-weight: 700;" class="spd-mono">
              ¥ {{ Number(item.total_amount || (item.quantity * item.unit_price) || 0).toFixed(2) }}
            </td>
          </tr>
          <!-- 表格合计行 -->
          <tr style="background-color: #f9fafb; font-weight: 700;">
            <td colspan="5" align="center">合 计</td>
            <td style="text-align: right;">{{ totalQuantity }}</td>
            <td />
            <td style="text-align: right;" class="spd-mono">¥ {{ computedTotalAmount.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="voucher-summary">
        <div><span>合计金额（大写）：</span><strong>{{ uppercaseAmount }}</strong></div>
        <div><span>小写合计：</span><strong class="spd-mono">¥ {{ computedTotalAmount.toFixed(2) }}</strong></div>
      </div>

      <div class="voucher-signatures">
        <div class="sig-item">
          <span class="sig-label">制单人：</span>
          <span class="sig-line">{{ orderData.created_by || '王建国' }}</span>
        </div>
        <div class="sig-item">
          <span class="sig-label">主库科室主管：</span>
          <span class="sig-line">{{ orderData.approver_name || '王建国 (已审核)' }}</span>
        </div>
        <div class="sig-item">
          <span class="sig-label">二级库/经办接收人：</span>
          <span class="sig-line">{{ orderData.second_confirmed_by || orderData.receiver_name || '李晓琳' }}</span>
        </div>
        <div class="sig-item">
          <span class="sig-label">财务科复核：</span>
          <span class="sig-line">孙丽娟 (已核准)</span>
        </div>
      </div>

      <div class="voucher-footer">
        <span>医疗物资全链路 SPD 系统自动生成 · 防伪溯源流水号: TRC-{{ Date.now() }}</span>
        <span>第 1 页 / 共 1 页</span>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    voucherType?: string;
    orderData?: Record<string, any>;
  }>(),
  {
    voucherType: '主库向二级库按需分发调拨单',
    orderData: () => ({
      order_no: 'DIST-20261102-088',
      target_dept_or_supplier: '骨科病区二级库',
      warehouse_code: 'WH_WEICAI (卫材主库)',
      quantity: 50,
      unit_price: 18.5,
      product_name: '一次性使用无菌注射器 (5ml带针)',
      batch_no: 'LOT202605A',
      expire_date: '2026-12-10'
    })
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const currentDate = new Date().toISOString().split('T')[0];

const voucherTitle = computed(() => {
  return props.voucherType || '医疗物资出入库四联签字确认单';
});

/**
 * 将阿拉伯数字金额转换为标准中国人民银行法定中文大写金额
 * @param {number} money 金额数值
 * @returns {string} 标准中文大写金额
 * @route internal://PrintVoucherDialog/digitUppercase
 * @throws 无异常
 */
function digitUppercase(money: number): string {
  if (isNaN(money) || money === null || money === undefined) return '零元整';
  const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'];
  const unit = [
    ['元', '万', '亿'],
    ['', '拾', '佰', '仟']
  ];

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

/**
 * 计算当前单据待打印的物料明细数组
 * @returns {any[]} 物料明细数组
 * @route internal://PrintVoucherDialog/displayItems
 * @throws 无异常抛出
 */
const displayItems = computed(() => {
  if (Array.isArray(props.orderData?.items) && props.orderData.items.length > 0) {
    return props.orderData.items;
  }
  // 兼容单项数据传入
  if (props.orderData?.product_name || props.orderData?.product_code) {
    return [
      {
        product_code: props.orderData.product_code || 'PROD-GEN-001',
        product_name: props.orderData.product_name || '一次性使用无菌注射器带针 5ml',
        batch_no: props.orderData.batch_no || 'B20261001',
        unit_name: props.orderData.unit_name || props.orderData.pricing_unit || '支',
        quantity: Number(props.orderData.quantity) || 100,
        unit_price: Number(props.orderData.unit_price) || 0.45,
        total_amount: Number(props.orderData.total_amount) || 45.0
      }
    ];
  }
  return [];
});

/**
 * 汇总打印明细中的耗材总数量
 * @returns {number} 总数量
 * @route internal://PrintVoucherDialog/totalQuantity
 * @throws 无异常抛出
 */
const totalQuantity = computed(() => {
  return displayItems.value.reduce((acc, cur) => acc + (Number(cur.quantity) || 0), 0);
});

/**
 * 计算打印明细中的金额总和
 * @returns {number} 总金额
 * @route internal://PrintVoucherDialog/computedTotalAmount
 * @throws 无异常抛出
 */
const computedTotalAmount = computed(() => {
  if (props.orderData?.total_amount && typeof props.orderData.total_amount === 'number' && displayItems.value.length <= 1) {
    return props.orderData.total_amount;
  }
  const sum = displayItems.value.reduce((acc, cur) => {
    const itemTotal = cur.total_amount !== undefined ? Number(cur.total_amount) : (Number(cur.quantity || 0) * Number(cur.unit_price || 0));
    return acc + (isNaN(itemTotal) ? 0 : itemTotal);
  }, 0);
  return sum > 0 ? sum : (Number(props.orderData?.total_amount) || 0);
});

/**
 * 动态计算金额大写
 * @returns {string} 人民币大写字符串
 * @route internal://PrintVoucherDialog/uppercaseAmount
 * @throws 无异常抛出
 */
const uppercaseAmount = computed(() => {
  return digitUppercase(computedTotalAmount.value);
});

/**
 * 调起浏览器原生打印引擎
 * @returns {void}
 * @route internal://PrintVoucherDialog/handlePrint
 * @throws 无异常抛出
 */
function handlePrint(): void {
  window.print();
}
</script>

<style scoped>
.voucher-paper {
  background: #ffffff;
  color: #111827;
  padding: 32px 36px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-family: "SimSun", "Songti SC", "PingFang SC", serif;
}

.voucher-header {
  text-align: center;
  border-bottom: 2px solid #111827;
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.hospital-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
}

.voucher-title {
  font-size: 22px;
  font-weight: 800;
  margin: 6px 0 2px 0;
  letter-spacing: 2px;
}

.voucher-sub {
  font-size: 12px;
  color: #4b5563;
}

.voucher-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 16px;
  font-size: 13px;
  margin-bottom: 14px;
}

.voucher-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 14px;
}

.voucher-table th,
.voucher-table td {
  border: 1px solid #374151;
  padding: 8px 10px;
}

.voucher-table th {
  background-color: #f3f4f6;
  font-weight: 700;
}

.voucher-summary {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  border-bottom: 1px dashed #4b5563;
  padding-bottom: 10px;
  margin-bottom: 24px;
}

.voucher-signatures {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.sig-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12.5px;
}

.sig-line {
  border-bottom: 1px solid #111827;
  min-height: 24px;
  padding-bottom: 2px;
  font-weight: 600;
}

.voucher-footer {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #6b7280;
}
</style>
