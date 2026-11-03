<template>
  <div
    v-if="showcaseStore.isZenMode"
    id="zen-control-bar"
    class="zen-control-bar"
    role="toolbar"
    aria-label="纯享模式控制栏"
  >
    <!-- 音乐开关小胶囊 -->
    <button
      id="btn-zen-toggle-audio"
      type="button"
      class="zen-mini-pill"
      :class="{ 'active-audio': showcaseStore.isAudioPlaying }"
      title="纯享环境音效开关 (快捷键 M)"
      @click.stop="handleToggleAudio"
    >
      <SvgIcon
        :name="showcaseStore.isAudioPlaying ? 'audio-on' : 'audio-muted'"
        size="15"
        color="currentColor"
      />
      <span id="zen-audio-label">{{ showcaseStore.isAudioPlaying ? '音乐开' : '静音' }}</span>
    </button>

    <!-- 退出纯享胶囊 -->
    <button
      id="btn-exit-zen"
      type="button"
      class="zen-exit-pill"
      title="退出纯享模式并唤醒工作台 (快捷键 ESC)"
      @click.stop="handleExitZen"
    >
      <SvgIcon name="close" size="14" color="currentColor" />
      <span>退出纯享 (ESC)</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useShowcaseStore } from '@/stores/showcaseStore';
import SvgIcon from '@/components/common/SvgIcon.vue';

/**
 * @file ZenControlBar.vue
 * @description 纯享壁纸态右上角悬浮控制微条
 * 包含环境音效即时开关与“退出纯享 (ESC)”交互胶囊，确保纯享状态下仍能随心退出与调音。
 */

const showcaseStore = useShowcaseStore();

/**
 * 切换背景环境音频播放状态
 * @param {void} 无入参
 * @returns {void}
 * @route internal://src/components/showcase/ZenControlBar.vue/handleToggleAudio
 * @throws 无异常抛出
 */
function handleToggleAudio(): void {
  showcaseStore.toggleAudio();
}

/**
 * 退出纯享模式并唤醒展厅与工作台
 * @param {void} 无入参
 * @returns {void}
 * @route internal://src/components/showcase/ZenControlBar.vue/handleExitZen
 * @throws 无异常抛出
 */
function handleExitZen(): void {
  showcaseStore.setZenMode(false);
}
</script>

<style scoped>
.zen-control-bar {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 1000;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  animation: fadeInPill 300ms ease-out;
}

.zen-mini-pill,
.zen-exit-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--radius-pill, 9999px);
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #f1f5f9;
  font-size: 13px;
  font-weight: 500;
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
  cursor: pointer;
  transition: all 200ms ease-out;
  user-select: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.zen-mini-pill:hover,
.zen-exit-pill:hover {
  background: rgba(30, 41, 59, 0.90);
  border-color: rgba(56, 189, 248, 0.5);
  color: #38bdf8;
  box-shadow: 0 4px 20px rgba(56, 189, 248, 0.25);
}

.zen-mini-pill:active,
.zen-exit-pill:active {
  transform: scale(0.96);
}

.zen-mini-pill.active-audio {
  background: rgba(56, 189, 248, 0.20);
  border-color: rgba(56, 189, 248, 0.55);
  color: #38bdf8;
}

@keyframes fadeInPill {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
