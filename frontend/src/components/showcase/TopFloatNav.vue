<template>
  <nav id="top-nav" class="top-float-nav" role="navigation" aria-label="展厅顶部浮动导航">
    <!-- 左侧医疗品牌徽标 -->
    <div class="brand-badge">
      <div class="brand-logo">
        <SvgIcon name="medical-cross" size="18" color="#ffffff" />
      </div>
      <div class="brand-title">医院医疗物资全链路管理系统 · 统一双模态展厅</div>
    </div>

    <!-- 居中双模态分段切换胶囊 -->
    <div id="mode-segmented-pill" class="mode-segmented-pill" role="tablist">
      <button
        id="btn-mode-orbital"
        type="button"
        class="segment-btn"
        :class="{ active: showcaseStore.currentMode === 'orbital' }"
        role="tab"
        :aria-selected="showcaseStore.currentMode === 'orbital'"
        @click="showcaseStore.toggleMode('orbital')"
      >
        <SvgIcon name="orbital" size="15" />
        <span>360° 全域轨道拓扑</span>
      </button>
      <button
        id="btn-mode-tilted"
        type="button"
        class="segment-btn"
        :class="{ active: showcaseStore.currentMode === 'tilted' }"
        role="tab"
        :aria-selected="showcaseStore.currentMode === 'tilted'"
        @click="showcaseStore.toggleMode('tilted')"
      >
        <SvgIcon name="tilted" size="15" />
        <span>3D 弧面全链流光</span>
      </button>
    </div>

    <!-- 右侧功能胶囊集合 -->
    <div class="nav-actions">
      <!-- 背景环境音乐开关与音量滑动弹出层 (快捷键 M) -->
      <div id="nav-audio-group" class="nav-audio-group">
        <button
          id="btn-toggle-audio"
          type="button"
          class="nav-action-pill"
          :class="{ 'active-audio': showcaseStore.isAudioPlaying }"
          title="开启/静音动态壁纸背景音乐 (快捷键 M)"
          @click="showcaseStore.toggleAudio()"
        >
          <span id="audio-icon-slot">
            <SvgIcon :name="showcaseStore.isAudioPlaying ? 'audio-on' : 'audio-muted'" size="15" />
          </span>
          <span id="audio-label-text">{{ showcaseStore.isAudioPlaying ? '音乐开' : '静音' }}</span>
        </button>
        <div id="audio-slider-popover" class="audio-slider-popover">
          <input
            id="audio-volume-slider"
            type="range"
            min="0"
            max="1"
            step="0.05"
            :value="showcaseStore.audioVolume"
            title="音量调节"
            @input="handleVolumeInput"
          />
        </div>
      </div>

      <!-- 壁纸工坊抽屉开关 -->
      <button
        id="btn-toggle-wallpaper"
        type="button"
        class="nav-action-pill"
        title="展开全量 41 款 Wallpaper Engine 壁纸工坊"
        @click="showcaseStore.toggleWallpaperDrawer()"
      >
        <SvgIcon name="wallpaper" size="15" />
        <span id="label-wp-btn">壁纸工坊 ({{ showcaseStore.wallpaperCount }})</span>
      </button>

      <!-- 纯享模式开关 -->
      <button
        id="btn-enter-zen"
        type="button"
        class="nav-action-pill"
        title="进入 100% 绝对纯净壁纸纯享模式 (快捷键 ESC)"
        @click="showcaseStore.setZenMode(true)"
      >
        <SvgIcon name="zen" size="15" />
        <span>纯享模式</span>
      </button>

      <!-- 医慧通行登录认证入口 -->
      <button
        id="btn-open-login"
        type="button"
        class="nav-action-pill"
        title="医慧通行安全认证与角色切换"
        @click="showcaseStore.openLoginModal()"
      >
        <SvgIcon name="user" size="15" />
        <span>医慧通行</span>
      </button>

      <!-- 返回生产级工作台链接 -->
      <button
        id="btn-back-variants"
        type="button"
        class="nav-action-pill"
        title="进入 SPD 医疗物资三级工作台"
        @click="handleNavigateWorkbench"
      >
        <SvgIcon name="arrow-right" size="15" />
        <span>工作台原型</span>
      </button>

      <!-- 亮暗主题切换按钮 -->
      <button
        id="theme-toggle-btn"
        type="button"
        class="btn-theme"
        aria-label="切换亮暗主题"
        :title="userStore.theme === 'light' ? '切换为深空暗黑模式' : '切换为极简白瓷模式'"
        @click="userStore.toggleTheme()"
      >
        <SvgIcon :name="userStore.theme === 'light' ? 'moon' : 'sun'" size="16" />
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useShowcaseStore } from '@/stores/showcaseStore';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';

/**
 * @file TopFloatNav.vue
 * @description 顶部通透悬浮胶囊导航栏组件
 * 封装了品牌徽标、360°/3D 双模态书签切换胶囊、音量滑动调节、壁纸工坊开关、纯享开关及主题切换。
 */

const router = useRouter();
const showcaseStore = useShowcaseStore();
const userStore = useUserStore();

/**
 * 音量滑块输入事件处理
 * @param {Event} e DOM 输入事件
 * @returns {void}
 * @route internal://src/components/showcase/TopFloatNav.vue/handleVolumeInput
 * @throws 无异常抛出
 */
function handleVolumeInput(e: Event): void {
  const target = e.target as HTMLInputElement;
  const val = parseFloat(target.value);
  if (!isNaN(val)) {
    showcaseStore.setAudioVolume(val);
  }
}

/**
 * 跳转至业务工作台 (严格遵循 RBAC 角色权限与登录状态)
 * @param {void} 无入参
 * @returns {void}
 * @route internal://src/components/showcase/TopFloatNav.vue/handleNavigateWorkbench
 * @throws 无异常抛出
 */
function handleNavigateWorkbench(): void {
  if (!userStore.isLoggedIn) {
    showcaseStore.openLoginModal(true);
    return;
  }
  // 依据当前登录人员角色定向路由至归口首选页面
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
</script>

<style scoped>
.top-float-nav {
  position: fixed;
  top: 20px;
  left: 28px;
  right: 28px;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
  transition: opacity 300ms ease-out, transform 300ms ease-out;
}

.brand-badge {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-pill);
  padding: 8px 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.brand-logo {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: linear-gradient(135deg, #0284c7, #0ea5e9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
}

.brand-title {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: var(--text-primary);
}

/* 双模态书签切换胶囊 (Segmented View Switcher) */
.mode-segmented-pill {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-pill);
  padding: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  gap: 4px;
}

.segment-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 160ms ease-out, color 160ms ease-out, transform 120ms ease-out;
}

.segment-btn:hover {
  color: var(--text-primary);
}

.segment-btn.active {
  background: var(--accent-primary);
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(2, 132, 199, 0.4);
}

.segment-btn:active {
  transform: scale(0.96);
}

.nav-actions {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-action-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-card);
  color: var(--text-primary);
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: transform 150ms ease-out, background 150ms ease-out, border-color 150ms ease-out;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.nav-action-pill:hover {
  border-color: var(--accent-primary);
}

.nav-action-pill:active {
  transform: scale(0.96);
}

.btn-theme {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-card);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 150ms ease-out, border-color 150ms ease-out;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-theme:hover {
  border-color: var(--accent-primary);
}

.btn-theme:active {
  transform: scale(0.92);
}

.nav-audio-group {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.audio-slider-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 12px;
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
  display: none;
  align-items: center;
  gap: 8px;
  z-index: 100;
}

.nav-audio-group:hover .audio-slider-popover {
  display: flex;
}

#audio-volume-slider {
  width: 80px;
  height: 4px;
  cursor: pointer;
  accent-color: #38bdf8;
}

.nav-action-pill.active-audio {
  background: rgba(56, 189, 248, 0.20);
  border-color: rgba(56, 189, 248, 0.55);
  color: #38bdf8;
}
</style>
