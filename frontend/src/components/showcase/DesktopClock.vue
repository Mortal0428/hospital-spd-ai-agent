<template>
  <div
    v-if="showcaseStore.isClockVisible"
    id="desktop-clock-widget"
    class="desktop-clock-widget active"
    :class="{ 'zen-show': showcaseStore.isZenMode }"
    aria-label="桌面实时数字时钟"
  >
    <div id="clock-time" class="clock-time">{{ currentTimeStr }}</div>
    <div id="clock-date" class="clock-date">{{ currentDateStr }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useShowcaseStore } from '@/stores/showcaseStore';

/**
 * @file DesktopClock.vue
 * @description 极简桌面实时数字时钟小部件 (Layer 0.8)
 * 采用 font-variant-numeric: tabular-nums 消除数字跳动造成的横向抖动，
 * 精确同步本地时分秒与年月日星期，并支持纯享模式下的独立浮动展示。
 */

const showcaseStore = useShowcaseStore();

const currentTimeStr = ref('00:00:00');
const currentDateStr = ref('2026年11月2日 星期一');

let timerId: number | null = null;

const DAY_NAMES = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];

/**
 * 更新时钟显示内容 (时分秒与年月日星期)
 * @param {void} 无入参
 * @returns {void}
 * @route internal://src/components/showcase/DesktopClock.vue/updateClock
 * @throws 无异常抛出
 */
function updateClock(): void {
  const now = new Date();
  const h = String(now.getHours()).padStart(2, '0');
  const m = String(now.getMinutes()).padStart(2, '0');
  const s = String(now.getSeconds()).padStart(2, '0');
  currentTimeStr.value = `${h}:${m}:${s}`;

  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  const date = now.getDate();
  const dayName = DAY_NAMES[now.getDay()];
  currentDateStr.value = `${year}年${month}月${date}日 ${dayName}`;
}

onMounted(() => {
  updateClock();
  timerId = window.setInterval(updateClock, 1000);
});

onUnmounted(() => {
  if (timerId !== null) {
    clearInterval(timerId);
    timerId = null;
  }
});
</script>

<style scoped>
.desktop-clock-widget {
  position: fixed;
  top: 76px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  text-align: center;
  pointer-events: none;
  opacity: 0;
  transition: opacity 400ms ease-out, transform 400ms ease-out;
  user-select: none;
}

.desktop-clock-widget.active {
  opacity: 1;
}

.clock-time {
  font-size: 54px;
  font-weight: 200;
  letter-spacing: -2px;
  color: #ffffff;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.7);
  font-variant-numeric: tabular-nums;
  line-height: 1;
  margin-bottom: 4px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
}

.clock-date {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6);
}
</style>
