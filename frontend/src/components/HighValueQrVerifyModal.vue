<template>
  <el-dialog
    v-model="visible"
    title="高值耗材专属一物一码 (UDI) 二维码扫码核销中枢"
    width="540px"
    append-to-body
    class="spd-qr-verify-modal"
  >
    <div class="qr-verify-box">
      <!-- 专属二维码与 UDI 展示区 -->
      <div class="qr-preview-panel">
        <div class="qr-code-canvas">
          <svg viewBox="0 0 100 100" class="qr-vector">
            <rect width="100" height="100" fill="#ffffff" />
            <!-- 二维码定位角标 -->
            <rect x="8" y="8" width="24" height="24" fill="#0f172a" />
            <rect x="12" y="12" width="16" height="16" fill="#ffffff" />
            <rect x="15" y="15" width="10" height="10" fill="#0f172a" />

            <rect x="68" y="8" width="24" height="24" fill="#0f172a" />
            <rect x="72" y="12" width="16" height="16" fill="#ffffff" />
            <rect x="75" y="15" width="10" height="10" fill="#0f172a" />

            <rect x="8" y="68" width="24" height="24" fill="#0f172a" />
            <rect x="12" y="72" width="16" height="16" fill="#ffffff" />
            <rect x="15" y="75" width="10" height="10" fill="#0f172a" />

            <!-- 数据伪随机特征方块 -->
            <rect x="38" y="12" width="8" height="8" fill="#0f172a" />
            <rect x="50" y="18" width="8" height="6" fill="#0f172a" />
            <rect x="38" y="38" width="14" height="14" fill="#0284c7" />
            <rect x="18" y="42" width="6" height="8" fill="#0f172a" />
            <rect x="62" y="42" width="10" height="12" fill="#0f172a" />
            <rect x="78" y="52" width="12" height="10" fill="#0f172a" />
            <rect x="42" y="68" width="12" height="8" fill="#0f172a" />
            <rect x="62" y="72" width="8" height="14" fill="#0f172a" />
          </svg>
        </div>
        <div class="qr-info-box">
          <div class="qr-title">{{ itemData.product_name || '高值耗材单品' }}</div>
          <div class="meta-line"><span>UDI 序列号：</span><strong class="spd-mono">{{ itemData.udi_sn }}</strong></div>
          <div class="meta-line"><span>加密载荷：</span><span class="spd-mono payload-text">{{ itemData.qr_code_payload || 'SPD-QR|UDI:' + itemData.udi_sn }}</span></div>
        </div>
      </div>

      <el-divider style="margin: 16px 0;" />

      <!-- 患者信息核销绑定表单 -->
      <el-form label-position="top">
        <el-form-item label="患者住院号 / 病案号" required>
          <el-input
            v-model="inpatientNo"
            placeholder="例如: ZY2026110288"
            class="spd-mono"
          />
        </el-form-item>

        <el-form-item label="患者真实姓名 (系统将依法自动脱敏存储与展示)" required>
          <el-input
            v-model="patientName"
            placeholder="请输入患者姓名 (如: 刘德华)"
            @input="updateMaskedPreview"
          />
          <div class="mask-preview">
            <span>隐私脱敏存储效果：</span>
            <strong class="text-success">{{ maskedPreview || '未录入' }}</strong>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!inpatientNo || !patientName"
          @click="handleVerifySubmit"
        >
          确认扫码核销并同步记账
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { verifyHighValueQrScan } from '@/api/highValueApi';
import { useUserStore } from '@/stores/userStore';

const props = defineProps<{
  modelValue: boolean;
  itemData: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
  (e: 'verified', resData: any): void;
}>();

const userStore = useUserStore();
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const inpatientNo = ref('');
const patientName = ref('');
const maskedPreview = ref('');
const submitting = ref(false);

/**
 * 实时计算患者姓名脱敏预览
 * @returns void
 * @route internal://HighValueQrVerifyModal/updateMaskedPreview
 * @throws 无异常抛出
 */
function updateMaskedPreview() {
  const clean = (patientName.value || '').trim();
  if (!clean) {
    maskedPreview.value = '';
    return;
  }
  if (clean.length === 1) {
    maskedPreview.value = '*';
  } else if (clean.length === 2) {
    maskedPreview.value = `${clean[0]}*`;
  } else {
    maskedPreview.value = `${clean[0]}*${clean[clean.length - 1]}`;
  }
}

/**
 * 提交扫码核销绑定请求
 * @returns Promise<void>
 * @route internal://HighValueQrVerifyModal/handleVerifySubmit
 * @throws 当核销接口返回异常时提示错误
 */
async function handleVerifySubmit() {
  if (!inpatientNo.value || !patientName.value) {
    ElMessage.warning('请填写完整的患者住院号与姓名');
    return;
  }

  submitting.value = true;
  try {
    const res = await verifyHighValueQrScan({
      udi_sn: props.itemData.udi_sn,
      patient_inpatient_no: inpatientNo.value,
      patient_name: patientName.value,
      operator_name: userStore.currentUser.realName
    });
    ElMessage.success(`高值单品[${props.itemData.udi_sn}]扫码核销成功，已绑定脱敏患者[${res.patient_name_masked}]`);
    emit('verified', res);
    visible.value = false;
    // 重置
    inpatientNo.value = '';
    patientName.value = '';
    maskedPreview.value = '';
  } catch (err: any) {
    ElMessage.error(err.message || '扫码核销失败');
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.qr-preview-panel {
  display: flex;
  gap: 16px;
  background: var(--spd-bg-subtle);
  border: 1px solid var(--spd-border-subtle);
  border-radius: var(--spd-radius-md);
  padding: 14px 16px;
  align-items: center;
}

.qr-code-canvas {
  width: 90px;
  height: 90px;
  background: #ffffff;
  padding: 4px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  flex-shrink: 0;
}

.qr-vector {
  width: 100%;
  height: 100%;
}

.qr-info-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.qr-title {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 2px;
}

.meta-line {
  font-size: 12px;
  color: var(--spd-text-regular);
}

.payload-text {
  font-size: 11px;
  color: var(--spd-primary);
  word-break: break-all;
}

.mask-preview {
  margin-top: 6px;
  font-size: 12px;
  color: var(--spd-text-muted);
}

.text-success {
  color: var(--spd-success);
}
</style>
