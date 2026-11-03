const fs = require('fs');
const filePath = 'frontend/src/views/WorkflowLogView.vue';
let content = fs.readFileSync(filePath, 'utf8');

// 1. 替换静态 timelineNodes 为响应式/计算属性与选中单据状态
const oldTimelineNodes = `const timelineNodes = [
  { step: 1, title: '字典建档', sub: '药监局UDI', status: 'passed' },
  { step: 2, title: '主库验收', sub: '效期强校验', status: 'passed' },
  { step: 3, title: '按需分发', sub: '移库不计费', status: 'passed' },
  { step: 4, title: '高值拆码', sub: '一物一码SN', status: 'passed' },
  { step: 5, title: '二级库签收', sub: '差异可拒收', status: 'passed' },
  { step: 6, title: '定数申领', sub: '主科室审批', status: 'passed' },
  { step: 7, title: '患者核销', sub: '消耗即结算', status: 'active' },
  { step: 8, title: '财务审计', sub: '四联合规', status: 'pending' }
];`;

const newTimelineNodes = `const selectedTraceRow = ref<any>(null);

const activeStepIndex = computed(() => {
  if (!selectedTraceRow.value) return 7;
  const act = selectedTraceRow.value.node_action || '';
  if (act.includes('1_') || act.includes('DICT')) return 1;
  if (act.includes('2_') || act.includes('INBOUND')) return 2;
  if (act.includes('3_') || act.includes('DISPATCH')) return 3;
  if (act.includes('4_') || act.includes('SPLIT')) return 4;
  if (act.includes('5_') || act.includes('RECEIVE')) return 5;
  if (act.includes('6_') || act.includes('APPLY')) return 6;
  if (act.includes('7_') || act.includes('CONSUME') || act.includes('VERIFY')) return 7;
  if (act.includes('8_') || act.includes('AUDIT') || act.includes('FINANCE')) return 8;
  return 3;
});

const timelineNodes = computed(() => {
  const stepIdx = activeStepIndex.value;
  const baseNodes = [
    { step: 1, title: '字典建档', sub: '药监局UDI' },
    { step: 2, title: '主库验收', sub: '效期强校验' },
    { step: 3, title: '按需分发', sub: '移库不计费' },
    { step: 4, title: '高值拆码', sub: '一物一码SN' },
    { step: 5, title: '二级库签收', sub: '差异可拒收' },
    { step: 6, title: '定数申领', sub: '主科室审批' },
    { step: 7, title: '患者核销', sub: '消耗即结算' },
    { step: 8, title: '财务审计', sub: '四联合规' }
  ];
  return baseNodes.map(n => {
    let status = 'pending';
    if (n.step < stepIdx) status = 'passed';
    else if (n.step === stepIdx) status = 'active';
    return { ...n, status };
  });
});

function handleTraceRowClick(row: any) {
  selectedTraceRow.value = row;
  ElMessage.info(\`已激活单据 [\${row.biz_order_no || row.trace_no}] 动态全链路穿透追溯图谱\`);
}`;

if (content.includes(oldTimelineNodes)) {
  content = content.replace(oldTimelineNodes, newTimelineNodes);
  console.log('Replaced timelineNodes with dynamic computed trace');
}

// 2. 替换流转交接横幅为动态绑定
const oldStrip = `<div class="highlight-audit-strip">
          <div class="strip-left">
            <SvgIcon name="shield" :size="16" color="var(--color-success)" />
            <span class="strip-text">
              <strong>最新物权流转审计穿透：</strong>
              交出方: 耗材科主库房 [王建国] &nbsp;→&nbsp; 接收方: 骨科病区二级库 [李晓琳] &nbsp;|&nbsp; 变动数量: 200 支 (移库不计费 · 完好签收)
            </span>
          </div>
          <div class="strip-right">
            <span class="status-chip chip-active">100% 审计合规 (VERIFIED)</span>
          </div>
        </div>`;

const newStrip = `<div class="highlight-audit-strip">
          <div class="strip-left">
            <SvgIcon name="shield" :size="16" color="var(--color-success)" />
            <span class="strip-text" v-if="selectedTraceRow">
              <strong>当前穿透单据 [{{ selectedTraceRow.biz_order_no || selectedTraceRow.trace_no }}]：</strong>
              物资: {{ selectedTraceRow.product_name }} &nbsp;|&nbsp;
              交接: {{ selectedTraceRow.from_dept_name }} [{{ selectedTraceRow.from_user_name || '经办人' }}] &nbsp;→&nbsp; {{ selectedTraceRow.to_dept_name }} [{{ selectedTraceRow.to_user_name || '接收人' }}] &nbsp;|&nbsp;
              数量: {{ selectedTraceRow.change_qty }} 件 (变动前: {{ selectedTraceRow.before_stock_snapshot ?? 0 }} → 变动后: {{ selectedTraceRow.after_stock_snapshot ?? selectedTraceRow.change_qty }})
            </span>
            <span class="strip-text" v-else>
              <strong>全院物资流转动态监控中：</strong>点击下方表格任意单据流水行，即可高亮激活其 8 节点全生命周期穿透路径与物权交接凭证。
            </span>
          </div>
          <div class="strip-right">
            <span class="status-chip" :class="selectedTraceRow?.audit_status === 'FLAGGED' ? 'chip-disabled' : 'chip-active'">
              {{ selectedTraceRow ? (selectedTraceRow.audit_status === 'FLAGGED' ? '异常预警 (FLAGGED)' : '合规通过 (VERIFIED)') : '实时监控中' }}
            </span>
          </div>
        </div>`;

if (content.includes(oldStrip)) {
  content = content.replace(oldStrip, newStrip);
  console.log('Replaced strip with dynamic strip');
}

// 3. 在表格中添加 highlight-current-row 和 @row-click
const oldTable = `<el-table
          :data="pagedLogs"
          border
          stripe
          class="fusion-styled-table"
          v-loading="loadingTrace"
        >`;

const newTable = `<el-table
          :data="pagedLogs"
          border
          stripe
          highlight-current-row
          class="fusion-styled-table"
          v-loading="loadingTrace"
          @row-click="handleTraceRowClick"
        >`;

if (content.includes(oldTable)) {
  content = content.replace(oldTable, newTable);
  console.log('Added row click to logs table');
}

fs.writeFileSync(filePath, content, 'utf8');
console.log('WorkflowLogView.vue dynamic trace updated successfully.');
