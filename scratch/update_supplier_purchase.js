const fs = require('fs');
const filePath = 'frontend/src/views/SupplierPurchaseView.vue';
let content = fs.readFileSync(filePath, 'utf8');

const targetOld = `function handleDictSelected(selectedRows: any[]) {
  for (const item of selectedRows) {
    const exists = planVoucher.value.items.find(i => i.product_code === item.product_code);
    if (!exists) {
      planVoucher.value.items.push({
        product_id: item.id,
        product_code: item.product_code,
        product_name: item.product_name,
        spec_name: item.spec_name,
        pricing_unit: item.pricing_unit,
        qty: 50,
        unit_price: item.unit_price
      });
    }
  }
  ElMessage.success(\`已选入 \${selectedRows.length} 种耗材到采购计划\`);
}`;

const replacementNew = `function handleDictSelected(selectedRows: any[]) {
  for (const item of selectedRows) {
    const code = item.product_code || item.spec_code;
    const exists = planVoucher.value.items.find(i => (i.product_code || i.spec_code) === code);
    if (!exists) {
      planVoucher.value.items.push({
        product_id: item.id || 1,
        product_code: code,
        spec_code: code,
        product_name: item.product_name,
        spec_name: item.spec_name || item.spec_model || '',
        pricing_unit: item.pricing_unit || '支',
        qty: 50,
        unit_price: Number(item.unit_price) || 1.25
      });
    }
  }
  ElMessage.success(\`已选入 \${selectedRows.length} 种耗材到采购计划\`);
}`;

if (content.includes(targetOld)) {
  content = content.replace(targetOld, replacementNew);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('SupplierPurchaseView.vue handleDictSelected updated');
} else {
  console.error('targetOld not found in SupplierPurchaseView.vue');
}
