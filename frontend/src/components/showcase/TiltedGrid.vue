<template>
  <div
    id="tilted-container"
    class="stage-tilted-view"
    :class="{ 'active-mode': showcaseStore.currentMode === 'tilted' && !showcaseStore.isZenMode }"
    aria-label="3D弧面圆柱多切片流光系统"
  >
    <div
      id="tgh-band"
      ref="bandRef"
      class="tgh-cylinder-band-wrap"
      :style="bandStyle"
    >
      <div
        v-for="tile in computedTiles"
        :key="tile.key"
        class="tgh-tile tgh-tile-stream-master"
        :style="{
          left: tile.left,
          top: tile.top,
          width: tile.width,
          height: tile.height,
          animationDelay: tile.animationDelay
        }"
        :title="`点击穿透至: ${tile.item.title}`"
        @click="handleTileClick(tile.item)"
      >
        <div
          v-for="(slice, sIdx) in tile.slices"
          :key="sIdx"
          class="tgh-slice"
          :class="{
            'slice-first': slice.isFirst,
            'slice-last': slice.isLast
          }"
          :style="{
            left: slice.left,
            width: slice.width,
            height: slice.height,
            transform: slice.transform
          }"
        >
          <div
            class="tgh-card-canvas"
            :style="{
              left: slice.canvasLeft,
              width: tile.width,
              height: tile.height
            }"
          >
            <div class="slice-canvas-header">
              <span class="card-tag">{{ tile.item.tag }}</span>
              <span class="slice-id">#{{ tile.item.id }}</span>
            </div>
            <div class="slice-canvas-body">
              <div class="card-headline">{{ tile.item.title }}</div>
              <div class="card-subtext">{{ tile.item.sub }}</div>
            </div>
            <div class="slice-canvas-footer">
              <span class="pulse-mini-dot"></span>
              <span class="slice-status">{{ tile.item.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useShowcaseStore, MEDICAL_ASSETS, type MedicalAsset } from '@/stores/showcaseStore';
import { useUserStore } from '@/stores/userStore';

/**
 * @file TiltedGrid.vue
 * @description 3D 弧面圆柱 8-切片 60FPS 极速流光系统 (Engine B)
 * 基于空间透视摄像机与弧面投影算法，将 10 大核心医疗卡片沿 75° 圆弧进行 8-切片空间微变形，
 * 兼具极致 3D 纵深立体质感与轻量级无模糊 GPU 渲染性能。
 */

const router = useRouter();
const showcaseStore = useShowcaseStore();
const userStore = useUserStore();

const bandRef = ref<HTMLElement | null>(null);

const winWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1920);
const winHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 1080);

const SLICES = 8;
const CAMERA = 1.6;
const MAX_WIDTH = 55;
const TILE_HEIGHT_PERCENT = 28;
const ASPECT_RATIO = 16 / 9;
const GAP_PERCENT = 6;
const CURVE_DEG = 75;
const SPEED = 4;
const AXIS_Y_PERCENT = 50;

/**
 * 计算弧面半径比例
 * @param {number} bendRad 弯曲弧度
 * @returns {number} 弧面几何半径
 * @route internal://src/components/showcase/TiltedGrid.vue/calcArcRadius
 * @throws 无异常抛出
 */
function calcArcRadius(bendRad: number): number {
  return (CAMERA - 1 + Math.cos(bendRad)) / (2 * CAMERA * Math.sin(bendRad));
}

interface TiltedLayout {
  h: number;
  radius: number;
  columns: number;
  sweep: number;
  unit: number;
  limit: number;
}

/**
 * 测量并计算当前视口下的 3D 弧面几何布局
 * @param {number} width 窗口宽度
 * @param {number} height 窗口高度
 * @returns {TiltedLayout} 布局参数集
 * @route internal://src/components/showcase/TiltedGrid.vue/measureTiltedLayout
 * @throws 无异常抛出
 */
function measureTiltedLayout(width: number, height: number): TiltedLayout {
  const bendRad = (CURVE_DEG * Math.PI) / 180;
  const h = Math.min((TILE_HEIGHT_PERCENT / 100) * height, ((MAX_WIDTH / 100) * width) / ASPECT_RATIO);
  const r = width * calcArcRadius(bendRad);
  const deg = (rad: number) => (rad * 180) / Math.PI;
  const unit = deg(h / r);
  const pitch = (ASPECT_RATIO + GAP_PERCENT / 100) * unit;
  const limit = deg(bendRad) + (ASPECT_RATIO * unit) / 2;
  const columns = Math.min(18, Math.max(8, Math.ceil((2 * limit) / pitch)));
  const sweep = +((columns * pitch) / 2).toFixed(4);
  return { h, radius: +r.toFixed(2), columns, sweep, unit: +unit.toFixed(4), limit: +Math.min(sweep, limit).toFixed(4) };
}

const currentLayout = computed(() => measureTiltedLayout(winWidth.value, winHeight.value));

const bandStyle = computed(() => {
  const { radius: r } = currentLayout.value;
  return {
    perspective: `${Math.round(r * CAMERA)}px`,
    perspectiveOrigin: `50% ${AXIS_Y_PERCENT}%`
  };
});

interface SliceData {
  left: string;
  width: string;
  height: string;
  transform: string;
  canvasLeft: string;
  isFirst: boolean;
  isLast: boolean;
}

interface TileComputed {
  key: string;
  item: MedicalAsset;
  left: string;
  top: string;
  width: string;
  height: string;
  animationDelay: string;
  slices: SliceData[];
}

const computedTiles = computed<TileComputed[]>(() => {
  const { h, radius: r, columns, unit } = currentLayout.value;
  const tileWidth = h * ASPECT_RATIO;
  const tileHeight = h;
  const share = ASPECT_RATIO / SLICES;
  const sliceWidth = tileWidth / SLICES;

  const result: TileComputed[] = [];

  for (let t = 0; t < columns; t++) {
    const first = columns - 1 - t;
    const tileIndex = first % MEDICAL_ASSETS.length;
    const item = MEDICAL_ASSETS[tileIndex >= 0 ? tileIndex : tileIndex + MEDICAL_ASSETS.length];

    const slices: SliceData[] = [];
    for (let k = 0; k < SLICES; k++) {
      const angle = (ASPECT_RATIO / 2 - (k + 0.5) * share) * unit;
      slices.push({
        left: `${(tileWidth - sliceWidth) / 2}px`,
        width: k === SLICES - 1 ? `${sliceWidth}px` : `${sliceWidth + 1}px`,
        height: `${tileHeight}px`,
        transform: `translateZ(${r}px) rotateY(${angle.toFixed(4)}deg) translateZ(-${r}px)`,
        canvasLeft: `-${k * sliceWidth}px`,
        isFirst: k === 0,
        isLast: k === SLICES - 1
      });
    }

    result.push({
      key: `tile-${t}-${item.id}`,
      item,
      left: `calc(50% - ${tileWidth / 2}px)`,
      top: `calc(${AXIS_Y_PERCENT}% - ${tileHeight / 2}px)`,
      width: `${tileWidth}px`,
      height: `${tileHeight}px`,
      animationDelay: `-${t * SPEED}s`,
      slices
    });
  }

  return result;
});

/**
 * 注入与更新 3D 弧面圆柱动画关键帧样式
 * @returns {void}
 * @route internal://src/components/showcase/TiltedGrid.vue/syncAnimationStyle
 * @throws 无异常抛出
 */
function syncAnimationStyle(): void {
  const { radius: r, sweep, columns } = currentLayout.value;
  const duration = columns * SPEED;
  const orbitAnimName = 'tgh-cylinder-stream-master-v2';

  let styleEl = document.getElementById('tgh-master-style-v2') as HTMLStyleElement | null;
  if (!styleEl) {
    styleEl = document.createElement('style');
    styleEl.id = 'tgh-master-style-v2';
    document.head.appendChild(styleEl);
  }

  styleEl.innerHTML = `
    @keyframes ${orbitAnimName} {
      from { transform: translateZ(${r}px) rotateY(-${sweep}deg) translateZ(-${r}px); }
      to { transform: translateZ(${r}px) rotateY(${sweep}deg) translateZ(-${r}px); }
    }
    .tgh-tile-stream-master {
      animation: ${orbitAnimName} ${duration}s linear infinite;
    }
  `;
}

/**
 * 窗口尺寸变化处理
 * @returns {void}
 * @route internal://src/components/showcase/TiltedGrid.vue/handleResize
 * @throws 无异常抛出
 */
function handleResize(): void {
  winWidth.value = window.innerWidth;
  winHeight.value = window.innerHeight;
  syncAnimationStyle();
}

/**
 * 点击卡片跳转
 * @param {MedicalAsset} item 医疗资产对象
 * @returns {void}
 * @route internal://src/components/showcase/TiltedGrid.vue/handleTileClick
 * @throws 无异常抛出
 */
function handleTileClick(item: MedicalAsset): void {
  if (!userStore.isLoggedIn) {
    showcaseStore.openLoginModal();
    return;
  }
  router.push(item.targetRoute);
}

onMounted(() => {
  window.addEventListener('resize', handleResize);
  syncAnimationStyle();
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  const styleEl = document.getElementById('tgh-master-style-v2');
  if (styleEl && styleEl.parentNode) {
    styleEl.parentNode.removeChild(styleEl);
  }
});
</script>

<style scoped>
.stage-tilted-view {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  opacity: 0;
  transform: scale(1.08);
  transition: opacity 350ms ease-out, transform 350ms ease-out;
}

.stage-tilted-view.active-mode {
  opacity: 1;
  transform: scale(1);
}

/* 未激活时彻底 display: none 并冻结所有切片动画 */
.stage-tilted-view:not(.active-mode) {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

.stage-tilted-view:not(.active-mode) :deep(.tgh-tile-stream-master) {
  animation-play-state: paused !important;
}

.tgh-cylinder-band-wrap {
  position: absolute;
  inset: 0;
  pointer-events: none;
  transform-style: preserve-3d;
  mask-image: linear-gradient(90deg, transparent 0%, #000 12%, #000 88%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, transparent 0%, #000 12%, #000 88%, transparent 100%);
}

.tgh-tile {
  position: absolute;
  transform-style: preserve-3d;
  will-change: transform;
  pointer-events: auto;
  cursor: pointer;
}

.tgh-slice {
  position: absolute;
  top: 0;
  overflow: hidden;
  transform-style: preserve-3d;
  background: rgba(15, 23, 42, 0.88);
  border-top: 1px solid rgba(56, 189, 248, 0.35);
  border-bottom: 1px solid rgba(56, 189, 248, 0.35);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35);
  transform: translateZ(0);
  will-change: transform;
  backface-visibility: hidden;
}

.tgh-slice.slice-first {
  border-left: 1px solid var(--tile-border, rgba(255, 255, 255, 0.16));
  border-top-left-radius: 14px;
  border-bottom-left-radius: 14px;
}

.tgh-slice.slice-last {
  border-right: 1px solid var(--tile-border, rgba(255, 255, 255, 0.16));
  border-top-right-radius: 14px;
  border-bottom-right-radius: 14px;
}

.tgh-card-canvas {
  position: absolute;
  top: 0;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  user-select: none;
  background: linear-gradient(180deg, rgba(2, 132, 199, 0.08) 0%, transparent 60%);
}

.slice-canvas-header {
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
  color: var(--accent-primary, #38bdf8);
  border: 1px solid rgba(2, 132, 199, 0.25);
  width: fit-content;
}

.slice-id {
  font-size: 11px;
  opacity: 0.6;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--text-muted);
}

.slice-canvas-body {
  margin: 6px 0;
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
}

.slice-canvas-footer {
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

.slice-status {
  font-size: 11px;
}
</style>
