const fs = require('fs');

// 1. 修复 FinancePrintView.vue
let fpContent = fs.readFileSync('frontend/src/views/FinancePrintView.vue', 'utf8');
if (!fpContent.includes("from '@/api/request'")) {
  fpContent = fpContent.replace(
    "import { ElMessage } from 'element-plus';",
    "import { ElMessage } from 'element-plus';\nimport { httpGet } from '@/api/request';"
  );
  fs.writeFileSync('frontend/src/views/FinancePrintView.vue', fpContent, 'utf8');
  console.log('FinancePrintView.vue import httpGet fixed.');
}

// 2. 修复 UserManagementView.vue
let umContent = fs.readFileSync('frontend/src/views/UserManagementView.vue', 'utf8');
if (!umContent.includes("useUserStore")) {
  umContent = umContent.replace(
    "import { httpGet, httpPost, httpPut, httpDelete } from '@/api/request';",
    "import { httpGet, httpPost, httpPut, httpDelete } from '@/api/request';\nimport { useUserStore } from '@/stores/userStore';"
  );
  umContent = umContent.replace(
    "const activeTab = ref<'users' | 'rbac'>('users');",
    "const userStore = useUserStore();\nconst activeTab = ref<'users' | 'rbac'>('users');"
  );
  fs.writeFileSync('frontend/src/views/UserManagementView.vue', umContent, 'utf8');
  console.log('UserManagementView.vue userStore fixed.');
}

// 3. 修复 GeneralMaterialView.vue
let gmContent = fs.readFileSync('frontend/src/views/GeneralMaterialView.vue', 'utf8');
const gmTarget = `const availableSuppliers = ref<SupplierProfileItem[]>([]);`;
const gmCodeToInject = `const availableSuppliers = ref<SupplierProfileItem[]>([]);

// =========================================================================
// 全院/分仓实时库存查询状态与逻辑
// =========================================================================
const realtimeWhFilter = ref('ALL');
const realtimeKeyword = ref('');
const realtimePage = ref(1);
const realtimePageSize = ref(10);
const realtimeTotal = ref(0);
const realtimeStockList = ref<any[]>([]);
const loadingRealtimeStock = ref(false);

const accessibleWarehouses = computed(() => {
  return userStore.authorizedWarehouses || [
    { code: 'WH_WEICAI', name: '卫材库房 (耗材主仓)' },
    { code: 'WH_EQUIP', name: '设备库房 (设备配件仓)' },
    { code: 'WH_ZONGWU', name: '总务仓库 (低值易耗仓)' },
    { code: 'WH_XINXI', name: '信息科仓 (IT硬件耗材)' },
    { code: 'WH_SEC_ORTHO', name: '骨科病区二级库' },
    { code: 'WH_SEC_CARDIO', name: '心内科病区二级库' }
  ];
});

async function fetchRealtimeStock() {
  loadingRealtimeStock.value = true;
  try {
    const res = await httpGet<any>('/main-warehouse/realtime-stock', {
      warehouse_code: realtimeWhFilter.value,
      keyword: realtimeKeyword.value,
      page: realtimePage.value,
      page_size: realtimePageSize.value
    });
    realtimeStockList.value = res?.items || [];
    realtimeTotal.value = res?.total || 0;
  } catch (err: any) {
    ElMessage.error(err.message || '获取实时库存失败');
  } finally {
    loadingRealtimeStock.value = false;
  }
}

// =========================================================================
// 主库按需分发出库单 (Voucher) 录入与保存逻辑 (对标图 1 / 图 5 凭证规范)
// =========================================================================
const showOutboundVoucherModal = ref(false);
const submittingOutbound = ref(false);
const showOutboundDictModal = ref(false);
const selectedOutboundRowIndex = ref<number | null>(null);

const outboundForm = ref({
  dispatch_order_no: '',
  source_warehouse_code: 'WH_WEICAI',
  target_dept_id: 3,
  target_dept_name: '骨科病区二级库',
  dispatch_type: '临床请领按需分发',
  dispatcher_name: '',
  receiver_name: '李晓琳',
  auto_approve: true,
  remark: '常规临床病区周转物资补货按需分发出库'
});

const outboundItems = ref<any[]>([]);

const outboundTotalQty = computed(() =>
  outboundItems.value.reduce((acc, cur) => acc + (Number(cur.quantity) || 0), 0)
);

const outboundTotalAmount = computed(() =>
  outboundItems.value.reduce((acc, cur) => acc + (Number(cur.total_amount) || 0), 0)
);

function openCreateOutboundVoucherModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  outboundForm.value.dispatch_order_no = \`CK936\${ts}\`;
  outboundForm.value.dispatcher_name = userStore.currentUser.realName || '系统管理员';
  outboundItems.value = [];
  showOutboundVoucherModal.value = true;
}

function recalcOutboundRow(row: any) {
  row.total_amount = (Number(row.quantity) || 0) * (Number(row.unit_price) || 0);
}

function handleOutboundDictConfirm(items: any[]) {
  for (const s of items) {
    const code = s.product_code || s.spec_code;
    const exists = outboundItems.value.find(i => (i.spec_code || i.product_code) === code);
    if (!exists) {
      outboundItems.value.push({
        spec_code: code,
        product_code: code,
        product_name: s.product_name,
        spec_name: s.spec_name || '',
        model_name: s.model_name || '',
        unit_name: s.pricing_unit || '支',
        manufacturer: s.manufacturer || '',
        batch_no: \`B\${new Date().toISOString().slice(0, 10).replace(/-/g, '')}\`,
        quantity: 10,
        unit_price: Number(s.unit_price) || 8.5,
        total_amount: (Number(s.unit_price) || 8.5) * 10
      });
    }
  }
  showOutboundDictModal.value = false;
  ElMessage.success(\`已导入 \${items.length} 种耗材到出库明细\`);
}

async function handleSaveOutboundVoucher() {
  if (outboundItems.value.length === 0) {
    ElMessage.warning('出库明细不能为空，请从产品字典添加耗材');
    return;
  }
  submittingOutbound.value = true;
  try {
    const res = await httpPost<any>('/main-warehouse/outbound-voucher', {
      dispatch_order_no: outboundForm.value.dispatch_order_no,
      source_warehouse_code: outboundForm.value.source_warehouse_code,
      target_dept_id: outboundForm.value.target_dept_id,
      target_dept_name: outboundForm.value.target_dept_name,
      dispatch_type: outboundForm.value.dispatch_type,
      dispatcher_name: outboundForm.value.dispatcher_name,
      receiver_name: outboundForm.value.receiver_name,
      auto_approve: outboundForm.value.auto_approve,
      remark: outboundForm.value.remark,
      items: outboundItems.value
    });
    ElMessage.success(\`主库出库单 [\${res.order_no || outboundForm.value.dispatch_order_no}] 保存成功！共出库 \${res.total_items} 种物资，总额 ¥\${res.total_amount?.toFixed(2) || '0.00'}\`);
    showOutboundVoucherModal.value = false;
    await fetchOrders();
  } catch (err: any) {
    ElMessage.error(err.message || '保存出库单失败');
  } finally {
    submittingOutbound.value = false;
  }
}`;

if (gmContent.includes(gmTarget)) {
  gmContent = gmContent.replace(gmTarget, gmCodeToInject);
  fs.writeFileSync('frontend/src/views/GeneralMaterialView.vue', gmContent, 'utf8');
  console.log('GeneralMaterialView.vue variables & methods injected.');
} else {
  console.error('gmTarget not found in GeneralMaterialView.vue');
}
