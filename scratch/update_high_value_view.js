const fs = require('fs');
const filePath = 'frontend/src/views/HighValueView.vue';
let content = fs.readFileSync(filePath, 'utf8');

// 1. 导入 StocktakePlanWorkbench
if (!content.includes("import StocktakePlanWorkbench")) {
  content = content.replace(
    "import SelectProductDictDialog from '@/components/SelectProductDictDialog.vue';",
    "import SelectProductDictDialog from '@/components/SelectProductDictDialog.vue';\nimport StocktakePlanWorkbench from '@/components/StocktakePlanWorkbench.vue';"
  );
}

// 2. 替换 Tab 5 内容为 StocktakePlanWorkbench
const tab5Start = '<!-- =====================================================================\n             Tab 5: 高值独立盘点 (stocktake)\n             ===================================================================== -->';
const tab5End = '</el-tab-pane>\n      </el-tabs>';

const oldTab5Regex = /<!-- =====================================================================\s+Tab 5: 高值独立盘点 \(stocktake\)\s+===================================================================== -->[\s\S]*?<\/el-tab-pane>/;

const newTab5 = `<!-- =====================================================================
             Tab 5: 高值独立盘点 (对标图 2 两级盘点工作台)
             ===================================================================== -->
        <el-tab-pane label="高值独立盘点" name="stocktake">
          <div class="tab-content-area" style="padding-top: 4px;">
            <StocktakePlanWorkbench
              scope="HIGH_VALUE"
              default-warehouse-code="WH_HIGH_VALUE"
            />
          </div>
        </el-tab-pane>`;

if (oldTab5Regex.test(content)) {
  content = content.replace(oldTab5Regex, newTab5);
  console.log('Replaced Tab 5 with StocktakePlanWorkbench');
}

// 3. 修复扫码核销按钮权限
const oldVerifyBtn = `<el-button
                    v-if="row.item_status !== 'USED_VERIFIED' && userStore.canAction('HV_QR_VERIFY', 'can_second_confirm')"
                    size="small"
                    type="primary"
                    @click="openQrVerifyModal(row)"
                  >
                    扫码核销扣库
                  </el-button>
                  <span v-else class="text-muted font-mono" style="font-size: 11px;">不可核销</span>`;

const newVerifyBtn = `<el-button
                    v-if="row.item_status !== 'USED_VERIFIED'"
                    size="small"
                    type="primary"
                    @click="openQrVerifyModal(row)"
                  >
                    扫码核销扣库
                  </el-button>
                  <span v-else class="text-muted font-mono" style="font-size: 11px;">已核销</span>`;

if (content.includes(oldVerifyBtn)) {
  content = content.replace(oldVerifyBtn, newVerifyBtn);
  console.log('Fixed verify button condition');
}

// 4. 修复 handleDictSelected 与 submitPrepVoucher
const oldHandleDict = `function handleDictSelected(selectedRows: any[]) {
  if (activeTab.value === 'stocktake') {
    // 盘点增补
    for (const item of selectedRows) {
      const exists = stocktakeList.value.find(s => s.product_code === item.product_code);
      if (!exists) {
        stocktakeList.value.push({
          index: stocktakeList.value.length + 1,
          id: item.id,
          product_code: item.product_code,
          product_name: item.product_name,
          spec_model: item.spec_name,
          pricing_unit: item.pricing_unit,
          unit_price: item.unit_price,
          batch_or_udi: \`SN\${new Date().toISOString().slice(0, 10).replace(/-/g, '')}\${Math.floor(Math.random() * 8999 + 1000)}\`,
          book_qty: 0,
          actual_qty: 1,
          diff_qty: 1,
          diff_amount: Number(item.unit_price || 0),
          nature: '盘盈增平'
        });
      }
    }
    ElMessage.success(\`已从产品字典增补 \${selectedRows.length} 品项到高值盘点单\`);
  } else {
    // 备货单选品
    for (const item of selectedRows) {
      const exists = prepVoucher.value.items.find(i => i.product_code === item.product_code);
      if (!exists) {
        prepVoucher.value.items.push({
          product_id: item.id,
          product_code: item.product_code,
          product_name: item.product_name,
          spec_name: item.spec_name,
          pricing_unit: item.pricing_unit,
          qty: 1,
          unit_price: item.unit_price
        });
      }
    }
    ElMessage.success(\`已导入 \${selectedRows.length} 种高值耗材\`);
  }
}`;

const newHandleDict = `function handleDictSelected(selectedRows: any[]) {
  for (const item of selectedRows) {
    const code = item.product_code || item.spec_code;
    const exists = prepVoucher.value.items.find(i => (i.product_code || i.spec_code) === code);
    if (!exists) {
      prepVoucher.value.items.push({
        product_id: item.id || 1,
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_name: item.spec_name || item.spec_model || '',
        pricing_unit: item.pricing_unit || '件',
        qty: 1,
        unit_price: Number(item.unit_price) || 0
      });
    }
  }
  ElMessage.success(\`已导入 \${selectedRows.length} 种高值耗材\`);
}`;

if (content.includes(oldHandleDict)) {
  content = content.replace(oldHandleDict, newHandleDict);
  console.log('Fixed handleDictSelected');
}

const oldSubmitPrep = `async function submitPrepVoucher() {
  try {
    for (const item of prepVoucher.value.items) {
      const udiSn = \`SN\${new Date().toISOString().slice(0, 10).replace(/-/g, '')}\${Math.floor(Math.random() * 8999 + 1000)}\`;
      await httpPost('/high-value/prep-order', {
        dept_code: prepVoucher.value.dept_code,
        target_main_warehouse: prepVoucher.value.target_main_warehouse,
        product_id: item.product_id || 1,
        udi_sn: udiSn,
        remark: prepVoucher.value.remark
      });
    }
    ElMessage.success('高值备货申请单已保存，已路由至上级主库审批');
    prepVoucherVisible.value = false;
    await fetchPrepData();
  } catch (err: any) {
    ElMessage.error(err.message || '保存备货申请失败');
  }
}`;

const newSubmitPrep = `async function submitPrepVoucher() {
  if (!prepVoucher.value.items || prepVoucher.value.items.length === 0) {
    ElMessage.warning('请至少添加一种备货耗材');
    return;
  }
  try {
    const payload = {
      apply_dept_code: prepVoucher.value.dept_code,
      target_main_dept: prepVoucher.value.target_main_warehouse,
      items: prepVoucher.value.items.map(item => ({
        product_id: item.product_id || 1,
        product_code: item.product_code || item.spec_code,
        product_name: item.product_name,
        spec_model: item.spec_name || '',
        quantity: item.qty || 1,
        unit_price: Number(item.unit_price) || 0
      })),
      remark: prepVoucher.value.remark
    };
    await httpPost('/high-value/prep-order', payload);
    ElMessage.success('高值备货申请单已保存，已路由至上级主库审批');
    prepVoucherVisible.value = false;
    await fetchPrepData();
  } catch (err: any) {
    ElMessage.error(err.message || '保存备货申请失败');
  }
}`;

if (content.includes(oldSubmitPrep)) {
  content = content.replace(oldSubmitPrep, newSubmitPrep);
  console.log('Fixed submitPrepVoucher');
}

fs.writeFileSync(filePath, content, 'utf8');
console.log('HighValueView.vue successfully updated.');
