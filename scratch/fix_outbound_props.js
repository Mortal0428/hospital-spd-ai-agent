const fs = require('fs');
let gm = fs.readFileSync('frontend/src/views/GeneralMaterialView.vue', 'utf8');

const oldDef = `const outboundForm = ref({
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
});`;

const newDef = `const outboundForm = ref({
  order_no: '',
  dispatch_order_no: '',
  outbound_date: new Date().toISOString().slice(0, 10),
  outbound_type: '按需分发出库 (移库不计费)',
  dispatch_type: '按需分发出库 (移库不计费)',
  source_warehouse_code: 'WH_WEICAI',
  target_dept_code: 'WH_SEC_ORTHO',
  target_dept_id: 3,
  target_dept_name: '010101 内一科 (骨科病区二级库)',
  dispatcher_name: '系统管理员',
  receiver_name: '李晓琳(护士长)',
  remark: '常规临床病区周转物资补货按需分发出库',
  handler_name: '系统管理员',
  auto_approve: true
});`;

if (gm.includes(oldDef)) {
  gm = gm.replace(oldDef, newDef);
  fs.writeFileSync('frontend/src/views/GeneralMaterialView.vue', gm, 'utf8');
  console.log('outboundForm properties updated.');
} else {
  console.error('oldDef not found');
}
