<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="480px"
    :before-close="handleClose"
    append-to-body
    class="spd-two-step-modal"
  >
    <div class="two-step-content">
      <div v-if="actionType === 'SECOND_CONFIRM'" class="dialog-body-box">
        <div class="warn-alert">
          <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" stroke-width="2" />
            <line x1="12" y1="8" x2="12" y2="12" stroke-width="2" />
            <line x1="12" y1="16" x2="12.01" y2="16" stroke-width="2" />
          </svg>
          <div>
            <div class="warn-title">外层列表两阶段二次确认提交</div>
            <div class="warn-desc">
              正式确认后单据将立即生效并触发库存变动或审批流。
              <span v-if="isIrreversible" class="text-danger font-bold">
                [特例警告] 该单据为不可逆单据（期初建账 / 高值科室退货），确认后将永久锁死，严禁取消提交或修改！
              </span>
            </div>
          </div>
        </div>
        <div class="meta-row"><span>单据编号：</span><strong class="spd-mono">{{ orderNo }}</strong></div>
        <div class="meta-row"><span>确认责任人：</span><span>{{ operatorName }}</span></div>
      </div>

      <div v-else-if="actionType === 'CANCEL_SUBMIT'" class="dialog-body-box">
        <div class="info-alert">
          <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polyline points="1 4 1 10 7 10" stroke-width="2" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" stroke-width="2" />
          </svg>
          <div>
            <div class="info-title">取消提交回退</div>
            <div class="info-desc">
              取消提交后，单据将退回第一阶段（待二次确认 PENDING_CONFIRM），您将可以重新修改或删除该单据。
            </div>
          </div>
        </div>
        <div class="meta-row"><span>目标单据：</span><strong class="spd-mono">{{ orderNo }}</strong></div>
      </div>

      <div v-else-if="actionType === 'EDIT_REMARK'" class="dialog-body-box">
        <el-form label-position="top">
          <el-form-item label="修改业务备注">
            <el-input
              v-model="editRemarkText"
              type="textarea"
              :rows="3"
              placeholder="请输入修改后的单据备注信息..."
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleConfirm"
        >
          确定执行
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  modelValue: boolean;
  orderNo: string;
  actionType: 'SECOND_CONFIRM' | 'CANCEL_SUBMIT' | 'EDIT_REMARK';
  operatorName: string;
  isIrreversible?: boolean;
  initialRemark?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
  (e: 'submit', payload: { action: string; orderNo: string; remark?: string }): void;
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const submitting = ref(false);
const editRemarkText = ref(props.initialRemark || '');

const dialogTitle = computed(() => {
  if (props.actionType === 'SECOND_CONFIRM') return '单据二次确认提交';
  if (props.actionType === 'CANCEL_SUBMIT') return '单据取消提交';
  return '修改单据备注';
});

/**
 * 关闭弹窗重置状态
 * @returns void
 * @route internal://TwoStepConfirmDialog/handleClose
 * @throws 无异常抛出
 */
function handleClose() {
  visible.value = false;
  submitting.value = false;
}

/**
 * 确认触发动作
 * @returns void
 * @route internal://TwoStepConfirmDialog/handleConfirm
 * @throws 无异常抛出
 */
function handleConfirm() {
  submitting.value = true;
  emit('submit', {
    action: props.actionType,
    orderNo: props.orderNo,
    remark: editRemarkText.value
  });
  submitting.value = false;
  visible.value = false;
}
</script>

<style scoped>
.dialog-body-box {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.warn-alert {
  display: flex;
  gap: 12px;
  background: var(--spd-warning-light);
  border: 1px solid rgba(217, 119, 6, 0.25);
  border-radius: var(--spd-radius-md);
  padding: 12px 14px;
}

.info-alert {
  display: flex;
  gap: 12px;
  background: var(--spd-primary-light);
  border: 1px solid rgba(2, 132, 199, 0.25);
  border-radius: var(--spd-radius-md);
  padding: 12px 14px;
}

.alert-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  stroke: var(--spd-warning);
}

.info-alert .alert-icon {
  stroke: var(--spd-primary);
}

.warn-title,
.info-title {
  font-weight: 700;
  font-size: 13.5px;
  margin-bottom: 4px;
}

.warn-desc,
.info-desc {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--spd-text-regular);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 6px 4px;
  border-bottom: 1px dashed var(--spd-border-subtle);
}

.text-danger {
  color: var(--spd-danger);
}
.font-bold {
  font-weight: 700;
}
</style>
