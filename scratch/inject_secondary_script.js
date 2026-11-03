const fs = require('fs');
const filePath = 'frontend/src/views/SecondaryWarehouseView.vue';
let content = fs.readFileSync(filePath, 'utf8');

// 找到 openManualOutboundModal 并替换成新的凭证式逻辑
const targetOldOutbound = `function openManualOutboundModal() {
  if (currentDeptStockList.value.length > 0) {
    selectedStockItemSpecCode.value = currentDeptStockList.value[0].spec_code;
  }
  manualOutForm.value.quantity = 5;
  showManualOutModal.value = true;
}

function handleStockItemSelectChange() {
  // 联动
}

/**
 * 提交科室手动发料出库 (扣减库存)
 */
async function handleSaveManualOutbound() {
  const stockItem = currentDeptStockList.value.find((s) => s.spec_code === selectedStockItemSpecCode.value);
  if (!stockItem) {
    ElMessage.warning('请选择在库耗材品规');
    return;
  }
  if (manualOutForm.value.quantity > stockItem.book_qty) {
    ElMessage.warning(\`发料数量 (\${manualOutForm.value.quantity}) 不得超出当前在库数 (\${stockItem.book_qty})\`);
    return;
  }
  submittingManualOut.value = true;
  try {
    const res = await createManualOutbound({
      warehouse_code: currentDeptCode.value,
      dept_code: currentDeptCode.value === 'WH_SEC_ORTHO' ? '010101' : '010201',
      receiver_name: manualOutForm.value.receiver_name,
      operator_name: userStore.currentUser.realName,
      use_purpose: manualOutForm.value.use_purpose,
      items: [
        {
          spec_code: stockItem.spec_code,
          batch_no: stockItem.batch_no,
          quantity: manualOutForm.value.quantity,
          unit_price: stockItem.unit_price,
          remark: manualOutForm.value.use_purpose
        }
      ]
    });
    // 立即核减前端展示库存
    stockItem.book_qty -= manualOutForm.value.quantity;
    ElMessage.success(\`科室发料单 [\${res.outbound_order_no}] 出库成功！已核减库存 \${res.total_qty} 件，结转支出 ¥\${res.total_amount.toFixed(2)}\`);
    showManualOutModal.value = false;
    await fetchManualOutbounds();
  } catch (err: any) {
    ElMessage.error(err.message || '手动发料失败');
  } finally {
    submittingManualOut.value = false;
  }
}`;

const replacementOutbound = `const manualOutVoucherNo = ref('');
const manualOutItems = ref<any[]>([]);
const showSecSelectModalForOut = ref(false);

const manualOutTotalQty = computed(() =>
  manualOutItems.value.reduce((acc, cur) => acc + (Number(cur.out_qty) || 0), 0)
);

const manualOutTotalAmount = computed(() =>
  manualOutItems.value.reduce((acc, cur) => acc + (Number(cur.out_qty) || 0) * (Number(cur.unit_price) || 0), 0)
);

/**
 * 打开凭证式手动发料出库制单窗口 (对标图 1 / 图 5 规范)
 */
function openManualOutboundModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  manualOutVoucherNo.value = \`CK936\${ts}\`;
  manualOutItems.value = [];
  manualOutForm.value.receiver_name = '张主治医生';
  manualOutForm.value.use_purpose = '病房换药日常消耗核减';
  showManualOutModal.value = true;
}

function handleConfirmSecSelectForOut(selectedItems: any[]) {
  for (const item of selectedItems) {
    const code = item.product_code || item.spec_code;
    const exists = manualOutItems.value.find(i => (i.product_code || i.spec_code) === code && i.batch_no === item.batch_no);
    if (!exists) {
      manualOutItems.value.push({
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_model: item.spec_name || item.spec_model || '标准规格',
        batch_no: item.batch_no,
        current_qty: item.current_qty || item.available_qty || 10,
        out_qty: 1,
        unit_price: Number(item.unit_price) || 8.5
      });
    }
  }
  ElMessage.success(\`已选入 \${selectedItems.length} 项在库耗材\`);
}

/**
 * 提交科室发料出库凭证并扣减在库库存
 */
async function handleSaveManualOutboundVoucher() {
  if (manualOutItems.value.length === 0) {
    ElMessage.warning('发料明细不能为空，请从在库台账中选品');
    return;
  }
  submittingManualOut.value = true;
  try {
    const res = await createManualOutbound({
      warehouse_code: currentDeptCode.value,
      dept_code: currentDeptCode.value === 'WH_SEC_ORTHO' ? '010101' : '010201',
      receiver_name: manualOutForm.value.receiver_name || '临床医生',
      operator_name: userStore.currentUser.realName,
      use_purpose: manualOutForm.value.use_purpose || '科室发料消耗',
      items: manualOutItems.value.map(item => ({
        spec_code: item.spec_code || item.product_code,
        batch_no: item.batch_no,
        quantity: item.out_qty || 1,
        unit_price: item.unit_price || 8.5,
        remark: manualOutForm.value.use_purpose || '病房换药日常消耗核减'
      }))
    });
    ElMessage.success(\`科室发料单 [\${res.outbound_order_no}] 出库成功！共核减 \${res.total_qty} 件，结转支出 ¥\${res.total_amount.toFixed(2)}\`);
    showManualOutModal.value = false;
    await fetchSecondaryInventory();
    await fetchManualOutbounds();
  } catch (err: any) {
    ElMessage.error(err.message || '手动发料出库失败');
  } finally {
    submittingManualOut.value = false;
  }
}

// 跨病区调拨单状态与处理
const transferVoucherNo = ref('');
const transferItems = ref<any[]>([]);
const showSecSelectModalForTransfer = ref(false);

const transferTotalQty = computed(() =>
  transferItems.value.reduce((acc, cur) => acc + (Number(cur.transfer_qty) || 0), 0)
);

const transferTotalAmount = computed(() =>
  transferItems.value.reduce((acc, cur) => acc + (Number(cur.transfer_qty) || 0) * (Number(cur.unit_price) || 0), 0)
);

function openTransferModal() {
  const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  transferVoucherNo.value = \`TR936\${ts}\`;
  transferItems.value = [];
  transferForm.value.to_warehouse_code = currentDeptCode.value === 'WH_SEC_ORTHO' ? 'WH_SEC_CARDIO' : 'WH_SEC_ORTHO';
  transferForm.value.reason_note = '抢救急用跨病区应急调剂无菌敷料';
  transferModalVisible.value = true;
}

function handleConfirmSecSelectForTransfer(selectedItems: any[]) {
  for (const item of selectedItems) {
    const code = item.product_code || item.spec_code;
    const exists = transferItems.value.find(i => (i.product_code || i.spec_code) === code && i.batch_no === item.batch_no);
    if (!exists) {
      transferItems.value.push({
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_model: item.spec_name || item.spec_model || '标准规格',
        batch_no: item.batch_no,
        current_qty: item.current_qty || item.available_qty || 10,
        transfer_qty: 1,
        unit_price: Number(item.unit_price) || 8.5
      });
    }
  }
  ElMessage.success(\`已选入 \${selectedItems.length} 项调拨耗材\`);
}

async function handleSaveTransferVoucher() {
  if (transferItems.value.length === 0) {
    ElMessage.warning('调拨物资明细不能为空，请从在库台账中选品');
    return;
  }
  try {
    const targetName = transferForm.value.to_warehouse_code === 'WH_SEC_CARDIO' ? '心内科病区二级库' : '骨科病区二级库';
    await httpPost('/ext/orders/ward-transfer', {
      from_warehouse_code: currentDeptCode.value,
      from_dept_name: currentDeptName.value,
      to_warehouse_code: transferForm.value.to_warehouse_code,
      to_dept_name: targetName,
      operator_name: userStore.currentUser.realName,
      reason_note: transferForm.value.reason_note || '跨病区应急调剂',
      items: transferItems.value.map(item => ({
        spec_code: item.spec_code || item.product_code,
        product_name: item.product_name,
        batch_no: item.batch_no,
        quantity: item.transfer_qty || 1,
        unit_price: item.unit_price || 8.5
      }))
    });
    ElMessage.success('跨病区科室调拨单已生成并生效！双方库房已留存调拨流水记录并增减库存。');
    transferModalVisible.value = false;
    await fetchSecondaryInventory();
    await fetchManualOutbounds();
  } catch (err: any) {
    ElMessage.error(err.message || '调拨出库失败');
  }
}`;

if (content.includes(targetOldOutbound)) {
  content = content.replace(targetOldOutbound, replacementOutbound);
  console.log('Replaced outbound and transfer scripts successfully');
} else {
  console.error('targetOldOutbound not matched');
}

// 确保 fetchPendingReceives 和 fetchSecondaryInventory 传参 warehouse_code
const oldFetchRec = `async function fetchPendingReceives() {
  loadingReceives.value = true;
  try {
    const res = await httpGet('/secondary-warehouse/pending-receives');
    pendingReceives.value = res || [];`;

const newFetchRec = `async function fetchPendingReceives() {
  loadingReceives.value = true;
  try {
    const res = await httpGet('/secondary-warehouse/pending-receives', {
      warehouse_code: currentDeptCode.value
    });
    pendingReceives.value = res || [];`;

if (content.includes(oldFetchRec)) {
  content = content.replace(oldFetchRec, newFetchRec);
  console.log('Updated fetchPendingReceives warehouse_code param');
}

const oldFetchInv = `async function fetchSecondaryInventory() {
  loadingInventory.value = true;
  try {
    const res = await httpGet('/secondary-warehouse/inventory');
    secondaryInventoryList.value = res || [];`;

const newFetchInv = `async function fetchSecondaryInventory() {
  loadingInventory.value = true;
  try {
    const res = await httpGet('/secondary-warehouse/inventory', {
      warehouse_code: currentDeptCode.value
    });
    secondaryInventoryList.value = res || [];`;

if (content.includes(oldFetchInv)) {
  content = content.replace(oldFetchInv, newFetchInv);
  console.log('Updated fetchSecondaryInventory warehouse_code param');
}

fs.writeFileSync(filePath, content, 'utf8');
console.log('Finished updating script in SecondaryWarehouseView.vue');
