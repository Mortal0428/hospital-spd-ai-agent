<template>
  <div
    id="orbital-container"
    class="stage-orbital-view"
    :class="{ 'hidden-mode': showcaseStore.currentMode !== 'orbital' || showcaseStore.isZenMode }"
    aria-label="360度全域环形轨道系统"
  >
    <!-- 环形背景轨道虚线圈 -->
    <div class="orbit-track-ring"></div>

    <!-- 旋转旋转架轮系 -->
    <div id="orbit-rig" class="orbit-carousel-rig">
      <div
        v-for="(item, index) in computedSlots"
        :key="item.id"
        class="orbit-satellite-slot"
        :style="{ transform: `translate(${item.x}px, ${item.y}px)` }"
      >
        <div class="satellite-counter-spin">
          <div
            class="medical-card-pod"
            :title="`点击穿透至: ${item.title}`"
            @click="handleCardClick(item)"
          >
            <div class="pod-header">
              <span class="card-tag">{{ item.tag }}</span>
              <span class="pod-id">#{{ item.id }}</span>
            </div>
            <div class="pod-body">
              <div class="card-headline">{{ item.title }}</div>
              <div class="card-subtext">{{ item.sub }}</div>
            </div>
            <div class="pod-footer">
              <span class="pulse-mini-dot"></span>
              <span class="pod-status">{{ item.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useShowcaseStore, MEDICAL_ASSETS, type MedicalAsset } from '@/stores/showcaseStore';
import { useUserStore } from '@/stores/userStore';

/**
 * @file OrbitalGallery.vue
 * @description 360° 全域环形轨道拓扑系统 (Engine A)
 * 采用严密的三角函数极坐标分布算法与反向自转抵消机制 (Counter-spin)，
 * 确保各医疗资产卡片在轨道公转时始终正向朝向视口，且在未激活或纯享模式下彻底冻结 GPU 动画。
 */

const router = useRouter();
const showcaseStore = useShowcaseStore();
const userStore = useUserStore();

interface SlotItem extends MedicalAsset {
  x: number;
  y: number;
}

const RADIUS = 520;

/**
 * 计算 10 大医疗资产卡片在 520px 半径轨道上的极坐标几何坐标
 */
const computedSlots = computed<SlotItem[]>(() => {
  const total = MEDICAL_ASSETS.length;
  return MEDICAL_ASSETS.map((item, index) => {
    const angleDeg = (index * 360) / total;
    const angleRad = (angleDeg * Math.PI) / 180;
    const x = Math.round(Math.cos(angleRad) * RADIUS);
    const y = Math.round(Math.sin(angleRad) * RADIUS);
    return {
      ...item,
      x,
      y
    };
  });
});

/**
 * 点击卡片事件响应
 * 已登录跳转至对应业务页面，未登录弹出医慧通行模态中枢
 * @param {MedicalAsset} item 被点击的医疗资产项
 * @returns {void}
 * @route internal://src/components/showcase/OrbitalGallery.vue/handleCardClick
 * @throws 无异常抛出
 */
function handleCardClick(item: MedicalAsset): void {
  if (!userStore.isLoggedIn) {
    showcaseStore.openLoginModal();
    return;
  }
  router.push(item.targetRoute);
}
</script>

<style scoped>
.stage-orbital-view {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: none;
  opacity: 1;
  transition: opacity 350ms ease-out, transform 350ms ease-out;
}

/* 隐藏或纯享时彻底 display: none 并暂停动画，消除 GPU 复合层空转 */
.stage-orbital-view.hidden-mode {
  display: none !important;
  opacity: 0 !important;
  transform: scale(0.92);
  pointer-events: none !important;
}

.stage-orbital-view.hidden-mode .orbit-carousel-rig,
.stage-orbital-view.hidden-mode .satellite-counter-spin {
  animation-play-state: paused !important;
}

.orbit-track-ring {
  position: absolute;
  width: var(--orbit-size, 1040px);
  height: var(--orbit-size, 1040px);
  border-radius: 50%;
  border: 1px dashed var(--border-divider);
  opacity: 0.6;
}

.orbit-carousel-rig {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  animation: rig-orbit var(--orbit-duration, 38s) linear infinite;
  will-change: transform;
}

@keyframes rig-orbit {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.orbit-satellite-slot {
  position: absolute;
  width: 0;
  height: 0;
}

.satellite-counter-spin {
  position: absolute;
  top: 0;
  left: 0;
  animation: card-counter-spin var(--orbit-duration, 38s) linear infinite;
  will-change: transform;
}

@keyframes card-counter-spin {
  0% {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotate(-360deg);
  }
}

.medical-card-pod {
  width: 250px;
  height: 136px;
  border-radius: var(--radius-card, 20px);
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(18px) saturate(1.8);
  backdrop-filter: blur(18px) saturate(1.8);
  border: 1px solid var(--border-card);
  box-shadow: var(--shadow-card);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
  transition: transform 180ms ease-out, border-color 180ms ease-out, box-shadow 180ms ease-out;
  cursor: pointer;
  pointer-events: auto;
}

.medical-card-pod:hover {
  transform: scale(1.06);
  border-color: var(--accent-primary);
  box-shadow: 0 12px 32px rgba(2, 132, 199, 0.25);
}

.pod-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-tag {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: var(--radius-pill, 9999px);
  background: rgba(2, 132, 199, 0.14);
  color: var(--accent-primary);
  border: 1px solid rgba(2, 132, 199, 0.25);
  width: fit-content;
}

.pod-id {
  font-size: 11px;
  opacity: 0.6;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--text-muted);
}

.pod-body {
  margin: 4px 0;
}

.card-headline {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 2px;
  white-space: nowrap;
}

.card-subtext {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pod-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #059669;
  font-weight: 600;
}

.pulse-mini-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  flex-shrink: 0;
}

.pod-status {
  font-size: 11px;
}
</style>
