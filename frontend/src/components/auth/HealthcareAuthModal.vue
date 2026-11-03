<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      id="spd-login-modal"
      class="spd-auth-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="spd-auth-title"
      @click="handleBackdropClick"
    >
      <div id="spd-auth-card" class="spd-auth-card" @click.stop>
        <!-- 头部品牌标识与关闭按钮 -->
        <div class="spd-auth-header">
          <div class="spd-auth-brand">
            <div class="brand-logo">
              <SvgIcon name="medical-cross" size="24" color="#38bdf8" />
            </div>
            <div>
              <div id="spd-auth-title" class="spd-auth-title">医慧通行 · 统一安全接入中枢</div>
              <div class="spd-auth-sub">医院 SPD 医疗物资全链管理与智能体协同平台</div>
            </div>
          </div>
          <button
            id="btn-close-login"
            type="button"
            class="spd-auth-close"
            aria-label="关闭认证弹窗"
            @click="handleClose"
          >
            <SvgIcon name="close" size="16" />
          </button>
        </div>

        <!-- 表单区域 -->
        <form id="spd-auth-form" class="spd-auth-form" @submit.prevent="handleSubmit">
          <!-- 字段 1: 医护工号 / 登录账号 -->
          <div class="spd-auth-field">
            <label class="spd-auth-label" for="login-account">医护工号 / 登录账号</label>
            <div class="spd-auth-input-wrap">
              <SvgIcon name="user" size="18" className="spd-input-icon" />
              <input
                id="login-account"
                v-model="account"
                type="text"
                class="spd-auth-input"
                placeholder="请输入医护人员工号 (如 SPD-ADMIN-01)"
                autocomplete="username"
                required
              />
            </div>
          </div>

          <!-- 字段 2: 系统访问密钥 -->
          <div class="spd-auth-field">
            <label class="spd-auth-label" for="login-password">系统访问密钥</label>
            <div class="spd-auth-input-wrap">
              <SvgIcon name="lock" size="18" className="spd-input-icon" />
              <input
                id="login-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="spd-auth-input"
                placeholder="请输入安全密码"
                autocomplete="current-password"
                required
              />
              <button
                id="btn-toggle-pwd"
                type="button"
                class="spd-pwd-toggle"
                aria-label="切换密码明暗文"
                @click="togglePasswordVisibility"
              >
                <SvgIcon :name="showPassword ? 'eye-off' : 'eye'" size="16" />
              </button>
            </div>
          </div>

          <!-- 会话记住与协助操作行 -->
          <div class="spd-auth-row">
            <label class="spd-checkbox-label">
              <input id="login-remember" v-model="remember" type="checkbox" />
              <span>记住此工作台认证会话</span>
            </label>
            <a href="javascript:void(0)" class="spd-auth-link" @click="handleHelpLink">
              安全证书协助
            </a>
          </div>

          <!-- 提交登录按钮 -->
          <button id="btn-submit-login" type="submit" class="spd-auth-submit" :disabled="loading">
            <span>{{ loading ? '正在验证凭证...' : '立即验证并登录' }}</span>
          </button>

          <!-- 分割线 -->
          <div class="spd-auth-divider">
            <span>或选择演示角色一键免密体验</span>
          </div>

          <!-- 演示角色一键免密网格 (4大核心角色 + 系统管理员) -->
          <div class="spd-role-fast-grid">
            <!-- 角色 1: 耗材科管理 -->
            <button
              type="button"
              class="spd-role-btn"
              data-role="consumable"
              title="耗材科管理 (王建国，主库管辖，SPD-CONSUMABLE-01)"
              @click="handleFastRole('consumable', 'SPD-CONSUMABLE-01', '耗材科管理员')"
            >
              <SvgIcon name="package" size="18" />
              <span>耗材科管理</span>
            </button>

            <!-- 角色 2: 设备科管理 -->
            <button
              type="button"
              class="spd-role-btn"
              data-role="equip"
              title="设备科管理 (周天海，设备专库，SPD-EQUIP-02)"
              @click="handleFastRole('equip', 'SPD-EQUIP-02', '设备科管理员')"
            >
              <SvgIcon name="equip" size="18" />
              <span>设备科管理</span>
            </button>

            <!-- 角色 3: 临床二级库 -->
            <button
              type="button"
              class="spd-role-btn"
              data-role="nurse"
              title="临床二级库 (李晓琳，临床二级库，SPD-NURSE-06)"
              @click="handleFastRole('nurse', 'SPD-NURSE-06', '临床二级库责任护士')"
            >
              <SvgIcon name="activity" size="18" />
              <span>临床二级库</span>
            </button>

            <!-- 角色 4: 财务合规审计 -->
            <button
              type="button"
              class="spd-role-btn"
              data-role="finance"
              title="财务合规审计 (孙丽娟，成本与单据，SPD-AUDIT-08)"
              @click="handleFastRole('finance', 'SPD-AUDIT-08', '财务科审计主管')"
            >
              <SvgIcon name="scale" size="18" />
              <span>财务合规审计</span>
            </button>

            <!-- 角色 5: 系统管理员 -->
            <button
              type="button"
              class="spd-role-btn spd-role-btn-wide"
              data-role="admin"
              title="系统管理员 (赵振华，信息科，SPD-ADMIN-01)"
              @click="handleFastRole('admin', 'SPD-ADMIN-01', '信息科系统管理员')"
            >
              <SvgIcon name="shield" size="18" />
              <span>系统管理员</span>
            </button>
          </div>
        </form>
      </div>

      <!-- CA 认证双环脉冲微加载指示器 -->
      <div v-if="loading" class="spd-spinner-backdrop" @click.stop>
        <div class="spd-spinner-box">
          <div class="spd-spinner-outer-ring">
            <div class="spd-spinner-inner-pulse">
              <SvgIcon name="star" size="20" color="#38bdf8" />
            </div>
          </div>
          <div class="spd-spinner-text">{{ spinnerText }}</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import SvgIcon from '@/components/common/SvgIcon.vue';
import { useUserStore } from '@/stores/userStore';

/**
 * 组件属性定义
 */
interface HealthcareAuthModalProps {
  /** 控制模态卡片显示与隐藏状态 */
  modelValue?: boolean;
}

const props = withDefaults(defineProps<HealthcareAuthModalProps>(), {
  modelValue: true
});

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
  (e: 'success'): void;
  (e: 'close'): void;
}>();

const userStore = useUserStore();

const account = ref('SPD-ADMIN-01');
const password = ref('123456');
const showPassword = ref(false);
const remember = ref(true);
const loading = ref(false);
const spinnerText = ref('正在核验 CA 数字证书与安全令牌...');

/**
 * 切换密码输入框明暗文显示模式
 * @param {void} 无入参
 * @returns {void}
 * @route internal://HealthcareAuthModal/togglePasswordVisibility
 * @throws 无异常抛出
 */
function togglePasswordVisibility(): void {
  showPassword.value = !showPassword.value;
}

/**
 * 关闭模态弹窗并向父级组件发送关闭事件
 * @param {void} 无入参
 * @returns {void}
 * @route internal://HealthcareAuthModal/handleClose
 * @throws 无异常抛出
 */
function handleClose(): void {
  emit('update:modelValue', false);
  emit('close');
}

/**
 * 点击遮罩空白区域关闭弹窗
 * @param {MouseEvent} event 鼠标点击事件
 * @returns {void}
 * @route internal://HealthcareAuthModal/handleBackdropClick
 * @throws 无异常抛出
 */
function handleBackdropClick(event: MouseEvent): void {
  if (event.target === event.currentTarget) {
    handleClose();
  }
}

/**
 * 响应键盘 ESC 按键以关闭当前激活的模态窗
 * @param {KeyboardEvent} event 键盘按键事件
 * @returns {void}
 * @route internal://HealthcareAuthModal/handleKeyDown
 * @throws 无异常抛出
 */
function handleKeyDown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && props.modelValue) {
    handleClose();
  }
}

/**
 * 提交账号密码执行双轨验证登录
 * @param {void} 无入参
 * @returns {Promise<void>}
 * @route internal://HealthcareAuthModal/handleSubmit
 * @throws 当登录验证发生不可恢复异常时给予安全提示
 */
async function handleSubmit(): Promise<void> {
  if (!account.value.trim()) {
    ElMessage.warning('请输入医护工号');
    return;
  }
  loading.value = true;
  spinnerText.value = '正在核验 CA 数字证书与安全令牌...';

  try {
    await userStore.login(account.value, password.value);
    setTimeout(() => {
      loading.value = false;
      ElMessage.success(`欢迎接入工作台：${userStore.currentUser.realName}`);
      emit('update:modelValue', false);
      emit('success');
    }, 600);
  } catch (err: any) {
    loading.value = false;
    ElMessage.error(err.message || 'CA 安全凭据核验未通过');
  }
}

/**
 * 触发演示角色一键免密通道
 * @param {string} roleKey 角色唯一键
 * @param {string} roleAccount 角色标准工号
 * @param {string} roleTitle 角色岗位名称
 * @returns {Promise<void>}
 * @route internal://HealthcareAuthModal/handleFastRole
 * @throws 无异常抛出，自动降级保证通道平滑
 */
async function handleFastRole(roleKey: string, roleAccount: string, roleTitle: string): Promise<void> {
  account.value = roleAccount;
  loading.value = true;
  spinnerText.value = `正在以 [${roleTitle}] 身份建立双向通道...`;

  try {
    await userStore.loginAsRole(roleKey);
    setTimeout(() => {
      loading.value = false;
      ElMessage.success(`已以 [${userStore.currentUser.realName}] 身份建立双向凭据通道`);
      emit('update:modelValue', false);
      emit('success');
    }, 600);
  } catch (err: any) {
    loading.value = false;
    ElMessage.error(err.message || '快捷免密通道建立失败');
  }
}

/**
 * 安全证书协助弹窗说明
 * @param {void} 无入参
 * @returns {void}
 * @route internal://HealthcareAuthModal/handleHelpLink
 * @throws 无异常抛出
 */
function handleHelpLink(): void {
  ElMessage.info('医慧通行采用 CA 电子签章与国密 SM2/SM3 算法，请将 USB Key 插入读卡槽或选择演示角色。');
}

// 监听键盘按键
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<style scoped>
/* 医慧通行 3D 展厅右侧通透悬浮毛玻璃中枢面板 (无全屏黑雾遮挡，右侧自适应悬浮) */
.spd-auth-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1500;
  background: transparent;
  pointer-events: auto;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 32px;
  animation: fadeInBackdrop 280ms ease-out;
}

.spd-auth-card {
  width: 440px;
  max-width: 90vw;
  max-height: calc(100vh - 120px);
  margin-top: 48px;
  background: var(--bg-card, rgba(15, 23, 42, 0.88));
  border: 1px solid var(--border-card, rgba(255, 255, 255, 0.18));
  border-radius: 24px;
  padding: 26px 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 14px;
  -webkit-backdrop-filter: blur(28px);
  backdrop-filter: blur(28px);
  overflow-y: auto;
  pointer-events: auto;
  animation: slideInFromRight 320ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeInBackdrop {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInFromRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.spd-auth-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-card, rgba(255, 255, 255, 0.14));
}

.spd-auth-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(56, 189, 248, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(56, 189, 248, 0.25);
}

.spd-auth-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary, #f8fafc);
  letter-spacing: -0.2px;
}

.spd-auth-sub {
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
  margin-top: 1px;
}

.spd-auth-close {
  border: none;
  background: transparent;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease, color 0.15s ease;
}

.spd-auth-close:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.spd-auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.spd-auth-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.spd-auth-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary, #f8fafc);
}

.spd-auth-input-wrap {
  border: 1.5px solid var(--border-card, rgba(255, 255, 255, 0.14));
  border-radius: 10px;
  height: 44px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  background: rgba(15, 23, 42, 0.35);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

[data-theme="light"] .spd-auth-input-wrap {
  background: #f8fafc;
}

.spd-auth-input-wrap:focus-within {
  border-color: #38bdf8;
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.15);
}

.spd-input-icon {
  width: 18px;
  height: 18px;
  color: var(--text-muted, #94a3b8);
  margin-right: 8px;
  flex-shrink: 0;
}

.spd-auth-input {
  border: none;
  background: transparent;
  outline: none;
  width: 100%;
  height: 100%;
  color: var(--text-primary, #f8fafc);
  font-size: 13px;
  font-family: inherit;
}

.spd-auth-input::placeholder {
  color: var(--text-muted, #94a3b8);
  font-size: 12px;
}

.spd-pwd-toggle {
  border: none;
  background: transparent;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s ease;
}

.spd-pwd-toggle:hover {
  color: var(--text-primary, #f8fafc);
}

.spd-auth-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.spd-checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  user-select: none;
}

.spd-checkbox-label input {
  accent-color: #38bdf8;
  cursor: pointer;
}

.spd-auth-link {
  color: #38bdf8;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.15s ease;
}

.spd-auth-link:hover {
  text-decoration: underline;
  opacity: 0.9;
}

.spd-auth-submit {
  height: 46px;
  background: var(--accent-primary, #0284c7);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
  transition: background 0.2s ease, transform 0.15s ease, filter 0.2s ease;
  box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
  user-select: none;
}

.spd-auth-submit:hover:not(:disabled) {
  filter: brightness(1.1);
}

.spd-auth-submit:active:not(:disabled) {
  transform: scale(0.98);
}

.spd-auth-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spd-auth-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 4px 0;
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
  position: relative;
}

.spd-auth-divider::before,
.spd-auth-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border-card, rgba(255, 255, 255, 0.14));
}

.spd-auth-divider span {
  padding: 0 10px;
}

.spd-role-fast-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.spd-role-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 64px;
  border-radius: 10px;
  border: 1px solid var(--border-card, rgba(255, 255, 255, 0.14));
  background: rgba(15, 23, 42, 0.4);
  color: var(--text-primary, #f8fafc);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.15s ease;
  user-select: none;
}

[data-theme="light"] .spd-role-btn {
  background: #f8fafc;
}

.spd-role-btn:hover {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  transform: translateY(-2px);
}

.spd-role-btn:active {
  transform: scale(0.96);
}

.spd-role-btn-wide {
  grid-column: span 2;
  flex-direction: row;
  gap: 8px;
}

/* CA 认证双环脉冲微加载指示器 */
.spd-spinner-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(15, 23, 42, 0.65);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeInPill 200ms ease-out;
}

.spd-spinner-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px 32px;
  border-radius: 20px;
  background: var(--bg-card, rgba(15, 23, 42, 0.95));
  border: 1px solid var(--border-card, rgba(255, 255, 255, 0.18));
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
}

.spd-spinner-outer-ring {
  width: 64px;
  height: 64px;
  border: 4px solid rgba(56, 189, 248, 0.2);
  border-top-color: #38bdf8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: spdSpin 0.9s linear infinite;
}

.spd-spinner-inner-pulse {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #38bdf8;
  animation: spdPulsePing 1.6s cubic-bezier(0, 0, 0.2, 1) infinite;
}

.spd-spinner-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #f8fafc);
  letter-spacing: 0.2px;
}

@keyframes spdSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes spdPulsePing {
  0% {
    transform: scale(0.85);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.15);
    opacity: 1;
  }
  100% {
    transform: scale(0.85);
    opacity: 0.8;
  }
}

@keyframes fadeInPill {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
