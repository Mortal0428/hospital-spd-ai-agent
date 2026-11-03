const fs = require('fs');
const filePath = 'frontend/src/views/SecondaryWarehouseView.vue';
let content = fs.readFileSync(filePath, 'utf8');

// 1. 检查并添加组件导入
if (!content.includes('import StocktakePlanWorkbench')) {
  content = content.replace(
    "import { useRoute, useRouter } from 'vue-router';",
    "import { useRoute, useRouter } from 'vue-router';\nimport StocktakePlanWorkbench from '@/components/StocktakePlanWorkbench.vue';\nimport SelectSecInventoryDialog from '@/components/SelectSecInventoryDialog.vue';"
  );
}

// 2. 移除 fetchPendingReceives 中的 mock fallback
const oldPendingFallback = `    pendingReceives.value = res || [];
    if (pendingReceives.value.length === 0) {
      pendingReceives.value = [
        {
          id: 1,
          dist_order_no: 'DIST-20261103-001',
          source_main_dept: 'CONSUMABLE_DEPT',
          target_dept_id: 3,
          target_dept_name: '骨科病区二级库',
          product_code: '936010900135',
          product_name: '医用敷料贴 (透明敷料 10cm*11.5cm)',
          batch_no: 'B2026110201',
          expiry_date: '2029-10-31',
          dist_qty: 50,
          unit_price: 8.7654,
          total_amount: 438.27,
          dispatcher_name: '王建国',
          created_at: '2026-11-03 11:30:00'
        }
      ];
    }`;

const newPendingFallback = `    pendingReceives.value = res || [];`;
if (content.includes(oldPendingFallback)) {
  content = content.replace(oldPendingFallback, newPendingFallback);
  console.log('Removed pendingReceives mock fallback');
}

// 3. 移除 fetchSecondaryInventory 中的 mock fallback
const oldInvFallback = `    secondaryInventoryList.value = res || [];
    if (secondaryInventoryList.value.length === 0) {
      secondaryInventoryList.value = [
        {
          id: 1,
          product_code: '936010900135',
          product_name: '医用敷料贴 (透明敷料)',
          batch_no: 'B2026102801',
          expiry_date: '2029-10-31',
          current_qty: 120,
          unit_price: 8.7654,
          shelf_location: '骨科病区备用柜-02层',
          safe_min_qty: 30,
          is_safety_warning: false
        }
      ];
    }`;

const newInvFallback = `    secondaryInventoryList.value = res || [];`;
if (content.includes(oldInvFallback)) {
  content = content.replace(oldInvFallback, newInvFallback);
  console.log('Removed secondaryInventoryList mock fallback');
}

// 4. 替换 Tab 6 独立盘点为 StocktakePlanWorkbench
const oldStocktakeRegex = /<!-- =====================================================================\s+Tab 3: 二级库独立盘点与对账\s+===================================================================== -->[\s\S]*?<\/el-tab-pane>/;

const newStocktakeTab = `<!-- =====================================================================
             Tab 3: 二级库独立盘点与对账 (对标图 2 两级盘点工作台)
             ===================================================================== -->
        <el-tab-pane label="病区独立盘点" name="stocktake">
          <div class="tab-content-area" style="padding-top: 4px;">
            <StocktakePlanWorkbench
              scope="SECONDARY"
              :default-warehouse-code="currentDeptCode"
            />
          </div>
        </el-tab-pane>`;

if (oldStocktakeRegex.test(content)) {
  content = content.replace(oldStocktakeRegex, newStocktakeTab);
  console.log('Replaced secondary stocktake tab with StocktakePlanWorkbench');
}

// 5. 替换手动发料出库弹窗为凭证式单据 (图 1 / 图 5 规范)
const oldManualOutRegex = /<!-- =========================================================================\s+弹窗 3：科室手动发料出库录入模态框[\s\S]*?<\/el-dialog>/;

const newManualOutModal = `<!-- =========================================================================
         弹窗 3：科室手动发料出库凭证式单据 (对标图 1 / 图 5 规范)
         ========================================================================= -->
    <el-dialog
      v-model="showManualOutModal"
      title="开具科室发料出库单 (核减在库库存)"
      width="920px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal voucher-dialog"
    >
      <div class="hospital-bill-container">
        <div class="dialog-warning-banner" style="background: rgba(2, 132, 199, 0.1); border-left: 4px solid var(--accent-primary); padding: 8px 12px; border-radius: 4px; font-size: 12px; margin-bottom: 12px;">
          业务提醒：因当前系统未直连 HIS 前端，科室通过本出库单据批量核减库存实物，直接结转为本科室当期耗材支出并留存 6W 流水日志！
        </div>

        <div class="voucher-header-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">发料出库单号</label>
            <input v-model="manualOutVoucherNo" readonly class="spd-input font-mono readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">发料所属病区/仓库</label>
            <input :value="currentDeptName" readonly class="spd-input font-bold readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">出库类别</label>
            <input value="科室发料出库 (病房定数消耗)" readonly class="spd-input readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label required font-bold" style="font-size: 11px;">领用责任人 / 医生</label>
            <input v-model="manualOutForm.receiver_name" placeholder="例如: 张主治医生 / 李护士长" class="spd-input" />
          </div>
          <div class="form-group">
            <label class="form-label required font-bold" style="font-size: 11px;">领用用途说明</label>
            <input v-model="manualOutForm.use_purpose" placeholder="例如: 病房换药日常消耗核减" class="spd-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">经办护士</label>
            <input :value="userStore.currentUser.realName" readonly class="spd-input readonly-input" />
          </div>
        </div>

        <!-- 凭证明细表格 -->
        <div class="voucher-items-section">
          <div class="table-action-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="font-bold" style="font-size: 13px;">发料耗材明细清单 (共 {{ manualOutItems.length }} 行)</span>
            <el-button type="primary" size="small" @click="showSecSelectModalForOut = true">
              <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
              + 从本科室在库台账选品
            </el-button>
          </div>

          <el-table :data="manualOutItems" border stripe size="small" class="fusion-styled-table">
            <el-table-column type="index" label="序号" width="50" align="center" />
            <el-table-column prop="product_code" label="物料代码" width="140" class-name="font-mono" />
            <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
            <el-table-column prop="spec_model" label="规格型号" width="120" show-overflow-tooltip />
            <el-table-column prop="batch_no" label="批次号" width="110" class-name="font-mono" />
            <el-table-column prop="current_qty" label="在库可用" width="90" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold text-success">{{ row.current_qty || row.available_qty || 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="发料数量" width="120" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.out_qty"
                  :min="1"
                  :max="row.current_qty || row.available_qty || 999"
                  size="small"
                  style="width: 100px;"
                />
              </template>
            </el-table-column>
            <el-table-column label="单价" width="85" align="right">
              <template #default="{ row }">
                <span class="font-mono">¥{{ Number(row.unit_price || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="95" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold">¥{{ ((row.out_qty || 1) * Number(row.unit_price || 0)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="65" align="center">
              <template #default="{ $index }">
                <el-button type="danger" text size="small" @click="manualOutItems.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="voucher-total-bar" style="display: flex; justify-content: flex-end; gap: 24px; padding: 10px 14px; background: var(--spd-bg-subtle); border-radius: 4px; margin-top: 8px; font-size: 13px;">
            <span>合计件数: <strong class="font-mono text-primary">{{ manualOutTotalQty }}</strong> 件</span>
            <span>合计金额: <strong class="font-mono text-danger">¥ {{ manualOutTotalAmount.toFixed(2) }}</strong></span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="showManualOutModal = false">取消</el-button>
          <el-button type="primary" :loading="submittingManualOut" :disabled="manualOutItems.length === 0" @click="handleSaveManualOutboundVoucher">
            确认发料并扣减库存
          </el-button>
        </div>
      </template>
    </el-dialog>`;

if (oldManualOutRegex.test(content)) {
  content = content.replace(oldManualOutRegex, newManualOutModal);
  console.log('Replaced manual outbound modal with standard hospital voucher');
}

// 6. 替换跨病区调拨弹窗为凭证式单据
const oldTransferRegex = /<!-- 跨病区应急调拨弹窗 -->[\s\S]*?<\/el-dialog>/;

const newTransferModal = `<!-- =========================================================================
         弹窗 4：跨病区科室调拨凭证式单据 (对标图 1 / 图 5 规范)
         ========================================================================= -->
    <el-dialog
      v-model="transferModalVisible"
      title="开具跨病区科室调拨出库单 (双方库房留存双向台账)"
      width="920px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal voucher-dialog"
    >
      <div class="hospital-bill-container">
        <div class="dialog-warning-banner" style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid var(--spd-success); padding: 8px 12px; border-radius: 4px; font-size: 12px; margin-bottom: 12px;">
          业务规则：调拨出库将直接核减调出病区在库库存，并在调入病区生成待接收记录，双方病区调拨单号同步双向留痕追溯！
        </div>

        <div class="voucher-header-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">调拨单号</label>
            <input v-model="transferVoucherNo" readonly class="spd-input font-mono readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">调出病区 (本仓)</label>
            <input :value="currentDeptName" readonly class="spd-input font-bold readonly-input" />
          </div>
          <div class="form-group">
            <label class="form-label required font-bold" style="font-size: 11px;">调入目标病区</label>
            <select v-model="transferForm.to_warehouse_code" class="spd-select font-bold">
              <option value="WH_SEC_CARDIO">心内科病区二级库 (WH_SEC_CARDIO)</option>
              <option value="WH_SEC_ORTHO">骨科病区二级库 (WH_SEC_ORTHO)</option>
            </select>
          </div>
          <div class="form-group" style="grid-column: span 2;">
            <label class="form-label required font-bold" style="font-size: 11px;">调拨事由 / 临床急用说明</label>
            <input v-model="transferForm.reason_note" placeholder="例如: 抢救急用跨病区应急调剂无菌敷料" class="spd-input" />
          </div>
          <div class="form-group">
            <label class="form-label font-bold" style="font-size: 11px;">经办护士</label>
            <input :value="userStore.currentUser.realName" readonly class="spd-input readonly-input" />
          </div>
        </div>

        <!-- 调拨明细表格 -->
        <div class="voucher-items-section">
          <div class="table-action-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="font-bold" style="font-size: 13px;">调拨物资明细清单 (共 {{ transferItems.length }} 行)</span>
            <el-button type="success" size="small" @click="showSecSelectModalForTransfer = true">
              <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
              + 从本科室在库台账选品
            </el-button>
          </div>

          <el-table :data="transferItems" border stripe size="small" class="fusion-styled-table">
            <el-table-column type="index" label="序号" width="50" align="center" />
            <el-table-column prop="product_code" label="物料代码" width="140" class-name="font-mono" />
            <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
            <el-table-column prop="spec_model" label="规格型号" width="120" show-overflow-tooltip />
            <el-table-column prop="batch_no" label="批次号" width="110" class-name="font-mono" />
            <el-table-column prop="current_qty" label="当前库存" width="90" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold text-success">{{ row.current_qty || row.available_qty || 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="调拨数量" width="120" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.transfer_qty"
                  :min="1"
                  :max="row.current_qty || row.available_qty || 999"
                  size="small"
                  style="width: 100px;"
                />
              </template>
            </el-table-column>
            <el-table-column label="单价" width="85" align="right">
              <template #default="{ row }">
                <span class="font-mono">¥{{ Number(row.unit_price || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="95" align="right">
              <template #default="{ row }">
                <span class="font-mono font-bold">¥{{ ((row.transfer_qty || 1) * Number(row.unit_price || 0)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="65" align="center">
              <template #default="{ $index }">
                <el-button type="danger" text size="small" @click="transferItems.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="voucher-total-bar" style="display: flex; justify-content: flex-end; gap: 24px; padding: 10px 14px; background: var(--spd-bg-subtle); border-radius: 4px; margin-top: 8px; font-size: 13px;">
            <span>调拨总件数: <strong class="font-mono text-primary">{{ transferTotalQty }}</strong> 件</span>
            <span>调拨总金额: <strong class="font-mono text-danger">¥ {{ transferTotalAmount.toFixed(2) }}</strong></span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="transferModalVisible = false">取消</el-button>
          <el-button type="success" :disabled="transferItems.length === 0" @click="handleSaveTransferVoucher">
            提交调拨单 (双方留存记录)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 5: 从本科室在库台账选品组件 -->
    <SelectSecInventoryDialog
      v-model="showSecSelectModalForOut"
      :inventory-list="secondaryInventoryList"
      title="从本科室在库台账选品开具备料发料出库单"
      @confirm="handleConfirmSecSelectForOut"
    />

    <SelectSecInventoryDialog
      v-model="showSecSelectModalForTransfer"
      :inventory-list="secondaryInventoryList"
      title="从本科室在库台账选品开具跨病区调拨单"
      @confirm="handleConfirmSecSelectForTransfer"
    />`;

if (oldTransferRegex.test(content)) {
  content = content.replace(oldTransferRegex, newTransferModal);
  console.log('Replaced transfer modal with standard hospital voucher');
}

fs.writeFileSync(filePath, content, 'utf8');
console.log('Template updates finished for SecondaryWarehouseView.vue');
