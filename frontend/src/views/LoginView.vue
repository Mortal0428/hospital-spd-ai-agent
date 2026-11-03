<template>
  <div class="spd-login-landing-container">
    <!-- 环境微光球与质感网格底层 -->
    <div class="spd-ambient-glow spd-glow-primary"></div>
    <div class="spd-ambient-glow spd-glow-secondary"></div>
    <div class="spd-grid-overlay"></div>

    <!-- 顶部极简品牌悬浮条 -->
    <header class="spd-landing-header">
      <div class="spd-brand-pill">
        <SvgIcon name="medical-cross" size="20" color="#38bdf8" />
        <span class="spd-brand-name">医院医疗物资全链路管理系统 · 统一安全入口</span>
      </div>
      <div class="spd-header-actions">
        <button
          type="button"
          class="spd-ghost-btn"
          aria-label="切换明暗主题"
          title="切换深浅主题"
          @click="toggleTheme"
        >
          <SvgIcon :name="userStore.theme === 'light' ? 'moon' : 'sun'" size="16" />
        </button>
      </div>
    </header>

    <!-- 中央核心引导区 (当模态框被临时关闭时优雅展现) -->
    <main v-if="!modalVisible" class="spd-landing-hero">
      <div class="spd-hero-cross-wrap">
        <SvgIcon name="medical-cross" size="48" color="#38bdf8" />
      </div>
      <h1 class="spd-hero-title">医慧通行 · 统一安全接入中枢</h1>
      <p class="spd-hero-desc">
        全生命周期物权穿透 · 100% 审计追溯 · 移库不计费 · 智能体全链路协同
      </p>
      <div class="spd-hero-actions">
        <button type="button" class="spd-action-btn primary" @click="openModal">
          <SvgIcon name="lock" size="16" />
          <span>唤起医慧通行登录中枢</span>
        </button>
        <button type="button" class="spd-action-btn secondary" @click="handleFastAdmin">
          <SvgIcon name="shield" size="16" />
          <span>免密以系统管理员接入</span>
        </button>
      </div>
    </main>

    <!-- 现代医疗模态登录中枢卡片 -->
    <HealthcareAuthModal
      v-model="modalVisible"
      @success="handleSuccess"
      @close="handleModalClose"
    />

    <!-- 底部三甲合规声明微条 -->
    <footer class="spd-landing-footer">
      <span>医院医疗物资全链路 SPD 数字化管理平台 · 遵循国家医疗器械唯一标识 (UDI) 与三甲内控审计规范</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import SvgIcon from '@/components/common/SvgIcon.vue';
import HealthcareAuthModal from '@/components/auth/HealthcareAuthModal.vue';
import { useUserStore } from '@/stores/userStore';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

/** 模态卡片可见性状态 (默认置为 true，进入 /login 路由即刻呈现) */
const modalVisible = ref(true);

/**
 * 打开医慧通行登录模态窗口
 * @param {void} 无入参
 * @returns {void}
 * @route internal://LoginView.vue/openModal
 * @throws 无异常抛出
 */
function openModal(): void {
  modalVisible.value = true;
}

/**
 * 响应模态窗口关闭事件
 * @param {void} 无入参
 * @returns {void}
 * @route internal://LoginView.vue/handleModalClose
 * @throws 无异常抛出
 */
function handleModalClose(): void {
  modalVisible.value = false;
}

/**
 * 登录认证成功后的视图跳转与通知处理
 * @param {void} 无入参
 * @returns {void}
 * @route internal://LoginView.vue/handleSuccess
 * @throws 无异常抛出
 */
function handleSuccess(): void {
  if (route.query.redirect) {
    router.push(route.query.redirect as string);
    return;
  }
  // 依据登录人员真实角色身份定向路由至对应专属工作台，杜绝越权与混乱
  const role = userStore.currentUser.roleCode;
  if (role === 'secondary_user') {
    router.push('/secondary');
  } else if (role === 'finance_auditor') {
    router.push('/finance');
  } else if (role === 'supplier_user') {
    router.push('/procurement');
  } else {
    router.push('/dict');
  }
}

/**
 * 快速以系统管理员角色一键建立通道并跳转
 * @param {void} 无入参
 * @returns {Promise<void>}
 * @route internal://LoginView.vue/handleFastAdmin
 * @throws 登录异常时通过 ElMessage 进行错误兜底
 */
async function handleFastAdmin(): Promise<void> {
  try {
    await userStore.loginAsRole('admin');
    ElMessage.success(`已以 [${userStore.currentUser.realName}] 身份进入工作台`);
    handleSuccess();
  } catch (err: any) {
    ElMessage.error(err.message || '快捷通道连接失败');
  }
}

/**
 * 切换全局明暗主题模式
 * @param {void} 无入参
 * @returns {void}
 * @route internal://LoginView.vue/toggleTheme
 * @throws 无异常抛出
 */
function toggleTheme(): void {
  userStore.toggleTheme();
}
</script>

<style scoped>
.spd-login-landing-container {
  min-height: 100vh;
  width: 100%;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  background-color: var(--bg-page, #080c14);
  color: var(--text-primary, #f8fafc);
  font-family: inherit;
  padding: 24px 32px;
  box-sizing: border-box;
  transition: background-color 0.3s ease;
}

/* 环境高斯微光球 */
.spd-ambient-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  pointer-events: none;
  z-index: 0;
  opacity: 0.45;
}

.spd-glow-primary {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.35) 0%, rgba(14, 165, 233, 0.05) 70%, transparent 100%);
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
}

.spd-glow-secondary {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
  bottom: 10%;
  right: 15%;
}

[data-theme="light"] .spd-glow-primary {
  opacity: 0.25;
}

[data-theme="light"] .spd-glow-secondary {
  opacity: 0.15;
}

/* 微网格装饰线 */
.spd-grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

[data-theme="light"] .spd-grid-overlay {
  background-image:
    linear-gradient(rgba(15, 23, 42, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 23, 42, 0.04) 1px, transparent 1px);
}

/* 顶部品牌条 */
.spd-landing-header {
  width: 100%;
  max-width: 1200px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
}

.spd-brand-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: var(--bg-card, rgba(15, 23, 42, 0.75));
  border: 1px solid var(--border-card, rgba(255, 255, 255, 0.12));
  border-radius: 9999px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
}

.spd-brand-name {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: -0.2px;
  color: var(--text-primary, #f8fafc);
}

.spd-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.spd-ghost-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border-card, rgba(255, 255, 255, 0.12));
  background: var(--bg-card, rgba(15, 23, 42, 0.75));
  color: var(--text-primary, #f8fafc);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.15s ease, background-color 0.2s ease;
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
}

.spd-ghost-btn:hover {
  border-color: #38bdf8;
  color: #38bdf8;
  transform: translateY(-1px);
}

/* 中央引导卡片 */
.spd-landing-hero {
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 640px;
  padding: 40px 32px;
  background: var(--bg-card, rgba(15, 23, 42, 0.8));
  border: 1px solid var(--border-card, rgba(255, 255, 255, 0.14));
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
  -webkit-backdrop-filter: blur(24px);
  backdrop-filter: blur(24px);
  animation: fadeInPill 300ms ease-out;
}

.spd-hero-cross-wrap {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  background: rgba(56, 189, 248, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  border: 1px solid rgba(56, 189, 248, 0.3);
  box-shadow: 0 8px 24px rgba(56, 189, 248, 0.2);
}

.spd-hero-title {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.4px;
  margin: 0 0 12px 0;
  color: var(--text-primary, #f8fafc);
}

.spd-hero-desc {
  font-size: 13px;
  color: var(--text-muted, #94a3b8);
  line-height: 1.6;
  margin: 0 0 28px 0;
}

.spd-hero-actions {
  display: flex;
  gap: 14px;
  width: 100%;
}

.spd-action-btn {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.15s ease, filter 0.2s ease, border-color 0.2s ease;
  user-select: none;
}

.spd-action-btn.primary {
  background: var(--accent-primary, #0284c7);
  color: #ffffff;
  border: none;
  box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
}

.spd-action-btn.primary:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.spd-action-btn.secondary {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid var(--border-card, rgba(255, 255, 255, 0.14));
  color: var(--text-primary, #f8fafc);
}

[data-theme="light"] .spd-action-btn.secondary {
  background: #ffffff;
}

.spd-action-btn.secondary:hover {
  border-color: #38bdf8;
  color: #38bdf8;
  transform: translateY(-1px);
}

/* 底部合规说明 */
.spd-landing-footer {
  z-index: 10;
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
  text-align: center;
  padding: 8px 16px;
  line-height: 1.5;
}

@keyframes fadeInPill {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
