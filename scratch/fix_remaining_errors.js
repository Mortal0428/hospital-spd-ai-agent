const fs = require('fs');

// 1. 修复 UserManagementView.vue 中的 userStore
let um = fs.readFileSync('frontend/src/views/UserManagementView.vue', 'utf8');
if (!um.includes("const userStore = useUserStore();")) {
  um = um.replace(
    "const activeTab = ref('users');",
    "const userStore = useUserStore();\nconst activeTab = ref('users');"
  );
  fs.writeFileSync('frontend/src/views/UserManagementView.vue', um, 'utf8');
  console.log('UserManagementView.vue userStore added.');
}

// 2. 修复 GeneralMaterialView.vue
let gm = fs.readFileSync('frontend/src/views/GeneralMaterialView.vue', 'utf8');

// 修复 template line 1002
gm = gm.replace(
  ':disabled="selectedOutboundRowIndex < 0"',
  ':disabled="selectedOutboundRowIndex === null || selectedOutboundRowIndex < 0"'
);

// 替换 script 中的 accessibleWarehouses 和 outboundForm 相关定义
const oldScriptBlock = `const accessibleWarehouses = computed(() => {
  return userStore.authorizedWarehouses || [
    { code: 'WH_WEICAI', name: '卫材库房 (耗材主仓)' },
    { code: 'WH_EQUIP', name: '设备库房 (设备配件仓)' },
    { code: 'WH_ZONGWU', name: '总务仓库 (低值易耗仓)' },
    { code: 'WH_XINXI', name: '信息科仓 (IT硬件耗材)' },
    { code: 'WH_SEC_ORTHO', name: '骨科病区二级库' },
    { code: 'WH_SEC_CARDIO', name: '心内科病区二级库' }
  ];
});`;

const newScriptBlock = `const accessibleWarehouses = computed(() => {
  return [
    { warehouse_code: 'WH_WEICAI', warehouse_name: '卫材库房 (耗材主仓)' },
    { warehouse_code: 'WH_EQUIP', warehouse_name: '设备库房 (设备配件仓)' },
    { warehouse_code: 'WH_ZONGWU', warehouse_name: '总务仓库 (低值易耗仓)' },
    { warehouse_code: 'WH_XINXI', warehouse_name: '信息科仓 (IT硬件耗材)' },
    { warehouse_code: 'WH_SEC_ORTHO', warehouse_name: '骨科病区二级库' },
    { warehouse_code: 'WH_SEC_CARDIO', warehouse_name: '心内科病区二级库' }
  ];
});`;

if (gm.includes(oldScriptBlock)) {
  gm = gm.replace(oldScriptBlock, newScriptBlock);
  console.log('accessibleWarehouses replaced.');
}

const oldOutboundDef = `const outboundForm = ref({
  dispatch_order_no: '',
  source_warehouse_code: 'WH_WEICAI',
  target_dept_id: 3,
  target_dept_name: '骨科病区二级库',
  dispatch_type: '临床请领按需分发',
  dispatcher_name: '',
  receiver_name: '李晓琳',
  auto_approve: true,
  remark: '常规临床病区周转物资补货按需分发出库'
});`;

const newOutboundDef = `const outboundForm = ref({
  order_no: '',
  outbound_date: new Date().toISOString().slice(0, 10),
  outbound_type: '按需分发出库 (移库不计费)',
  source_warehouse_code: 'WH_WEICAI',
  target_dept_code: 'WH_SEC_ORTHO',
  target_dept_id: 3,
  target_dept_name: '010101 内一科 (骨科病区二级库)',
  receiver_name: '李晓琳(护士长)',
  remark: '常规临床病区周转物资补货按需分发出库',
  handler_name: '系统管理员',
  auto_approve: true
});

function handleTargetDeptChange() {
  if (outboundForm.value.target_dept_code === 'WH_SEC_ORTHO') {
    outboundForm.value.target_dept_id = 3;
    outboundForm.value.target_dept_name = '010101 内一科 (骨科病区二级库)';
  } else if (outboundForm.value.target_dept_code === 'WH_SEC_CARDIO') {
    outboundForm.value.target_dept_id = 4;
    outboundForm.value.target_dept_name = '010201 心血管内科 (心内科二级库)';
  } else {
    outboundForm.value.target_dept_id = 5;
    outboundForm.value.target_dept_name = '高值耗材专仓';
  }
}

function removeSelectedOutboundRow() {
  if (selectedOutboundRowIndex.value !== null && selectedOutboundRowIndex.value >= 0) {
    outboundItems.value.splice(selectedOutboundRowIndex.value, 1);
    selectedOutboundRowIndex.value = -1;
  }
}`;

if (gm.includes(oldOutboundDef)) {
  gm = gm.replace(oldOutboundDef, newOutboundDef);
  console.log('outboundForm definition replaced.');
}

// 修复 openCreateOutboundVoucherModal
gm = gm.replace(
  "outboundForm.value.dispatch_order_no = `CK936${ts}`;",
  "outboundForm.value.order_no = `CK936${ts}`;\noutboundForm.value.handler_name = userStore.currentUser.realName || '系统管理员';"
);

// 修复 handleSaveOutboundVoucher dispatch_order_no
gm = gm.replace(
  "dispatch_order_no: outboundForm.value.dispatch_order_no,",
  "dispatch_order_no: outboundForm.value.order_no,"
);

fs.writeFileSync('frontend/src/views/GeneralMaterialView.vue', gm, 'utf8');
console.log('GeneralMaterialView.vue successfully updated.');
