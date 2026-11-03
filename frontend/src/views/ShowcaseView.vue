<template>
  <div
    class="spd-showcase-root"
    :data-theme="userStore.theme"
    @click="handleRootClick"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
  >
    <!-- Layer 0: 全屏 4K 动态壁纸与原生视频媒体层 -->
    <div
      id="wallpaper-media-layer"
      class="wallpaper-media-layer"
      :style="mediaLayerStyle"
    >
      <video
        ref="videoRef"
        id="wallpaper-video"
        class="wallpaper-video-bg"
        :class="{ active: currentWp.hasVideo && currentWp.videoUrl }"
        autoplay
        loop
        playsinline
        :muted="!showcaseStore.isAudioPlaying"
        :src="currentWp.hasVideo ? currentWp.videoUrl || currentWp.src : ''"
      ></video>
      <audio
        ref="audioRef"
        id="wallpaper-audio"
        loop
        playsinline
        style="display: none"
      ></audio>
    </div>

    <!-- 顶部通透悬浮胶囊导航栏 -->
    <TopFloatNav />

    <!-- 纯享模式右上角浮动控制微条 -->
    <ZenControlBar />

    <!-- 舞台自适应位移外壳：当登录卡片在右侧展开时，整体平滑向左偏移让位，两不遮挡 -->
    <div
      class="showcase-stage-viewport"
      :class="{ 'stage-shift-left': showcaseStore.isLoginModalOpen }"
    >
      <!-- Layer 0.8: 桌面实时数字时钟小部件 (防抖等宽数字) -->
      <DesktopClock />

      <!-- 引擎 A：360° 环形轨道拓扑系统 -->
      <OrbitalGallery v-show="showcaseStore.currentMode === 'orbital'" />

      <!-- 引擎 B：3D 弧面圆柱 8-切片流光系统 -->
      <TiltedGrid v-show="showcaseStore.currentMode === 'tilted'" />

      <!-- 中央恒定毛玻璃 Hero 核心舱卡片 -->
      <div class="hero-stage-wrapper">
        <HeroSection />
      </div>
    </div>

    <!-- 全量 41 款壁纸工坊底部抽屉面板 -->
    <WallpaperDrawer />

    <!-- 医慧通行现代医疗安全模态登录中枢 (从右侧动态滑出抽屉) -->
    <HealthcareAuthModal
      v-model="showcaseStore.isLoginModalOpen"
      @success="handleLoginSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useShowcaseStore, type WallpaperItem } from '@/stores/showcaseStore';
import { useUserStore } from '@/stores/userStore';
import TopFloatNav from '@/components/showcase/TopFloatNav.vue';
import ZenControlBar from '@/components/showcase/ZenControlBar.vue';
import HeroSection from '@/components/showcase/HeroSection.vue';
import OrbitalGallery from '@/components/showcase/OrbitalGallery.vue';
import TiltedGrid from '@/components/showcase/TiltedGrid.vue';
import WallpaperDrawer from '@/components/showcase/WallpaperDrawer.vue';
import DesktopClock from '@/components/showcase/DesktopClock.vue';
import HealthcareAuthModal from '@/components/auth/HealthcareAuthModal.vue';
import SvgIcon from '@/components/common/SvgIcon.vue';

/**
 * @file ShowcaseView.vue
 * @description 数字化展厅双模态全景门户主视图
 * 编排全屏 4K 动态壁纸 Layer 0、轻量调光模糊 Layer 1、桌面数字时钟、顶部胶囊导航、
 * 中央毛玻璃核心舱、360° 轨道拓扑、3D 弧面立体流光及医慧通行模态中枢，支持 ESC 级联分层退出与全屏拖拽映入。
 */

const showcaseStore = useShowcaseStore();
const userStore = useUserStore();
const router = useRouter();
const route = useRoute();

const videoRef = ref<HTMLVideoElement | null>(null);
const audioRef = ref<HTMLAudioElement | null>(null);

const isDraggingFile = ref(false);
let dragCounter = 0;

const currentWp = computed<WallpaperItem>(() => showcaseStore.activeWallpaper);

/**
 * 依据当前壁纸类型计算媒体背景层样式 (渐变色、本地图片或透明)
 * 严格使用非简写属性 backgroundImage，并显式配置 backgroundSize: 'cover'，杜绝内联样式覆盖导致的 T2.4 断言失败
 * @returns {import('vue').CSSProperties}
 * @route internal://src/views/ShowcaseView.vue/mediaLayerStyle
 * @throws 无异常抛出
 */
const mediaLayerStyle = computed(() => {
  const wp = currentWp.value;
  if (wp.hasVideo && wp.videoUrl) {
    return {
      backgroundImage: 'none',
      backgroundColor: 'transparent',
      backgroundSize: 'cover',
      backgroundPosition: 'center center'
    };
  }
  if (wp.src) {
    if (wp.src.startsWith('linear') || wp.src.startsWith('radial')) {
      return {
        backgroundImage: wp.src,
        backgroundSize: 'cover',
        backgroundPosition: 'center center'
      };
    }
    return {
      backgroundImage: `url("${wp.src}")`,
      backgroundSize: 'cover',
      backgroundPosition: 'center center'
    };
  }
  return {
    backgroundImage: 'radial-gradient(ellipse at center, #0c4a6e 0%, #080c14 70%)',
    backgroundSize: 'cover',
    backgroundPosition: 'center center'
  };
});

/**
 * 同步音频播放状态与音量
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/syncAudio
 * @throws 无异常抛出
 */
function syncAudio(): void {
  const wp = currentWp.value;
  const isEnabled = showcaseStore.isAudioPlaying;
  const vol = showcaseStore.audioVolume;

  // 1. 原生视频音轨调度
  if (videoRef.value) {
    videoRef.value.volume = vol;
    videoRef.value.muted = !isEnabled;
    if (wp.hasVideo) {
      videoRef.value.play().catch(() => {
        // 静默等待用户手势交互
      });
    }
  }

  // 2. 场景壁纸外挂音频调度
  if (audioRef.value) {
    if (!wp.hasVideo && wp.hasAudio && wp.audioUrl) {
      if (audioRef.value.src !== wp.audioUrl) {
        audioRef.value.src = wp.audioUrl;
      }
      audioRef.value.volume = vol;
      if (isEnabled) {
        audioRef.value.play().catch(() => {
          // 静默等待用户手势交互
        });
      } else {
        audioRef.value.pause();
      }
    } else {
      audioRef.value.pause();
      audioRef.value.src = '';
    }
  }
}

watch(
  () => [showcaseStore.activeWallpaperId, showcaseStore.isAudioPlaying, showcaseStore.audioVolume],
  () => {
    syncAudio();
  },
  { deep: true }
);

/**
 * 全局键盘快捷键监听
 * ESC: 优先级栈 (登录弹窗 -> 纯享模式 -> 壁纸抽屉)
 * M: 切换音效静音与播放
 * @param {KeyboardEvent} e 键盘事件
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/handleGlobalKeydown
 * @throws 无异常抛出
 */
function handleGlobalKeydown(e: KeyboardEvent): void {
  const activeEl = document.activeElement;
  const isInput = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA');

  if (e.key === 'Escape') {
    if (showcaseStore.isLoginModalOpen) {
      showcaseStore.closeLoginModal();
    } else if (showcaseStore.isZenMode) {
      showcaseStore.setZenMode(false);
    } else if (showcaseStore.isWallpaperDrawerOpen) {
      showcaseStore.toggleWallpaperDrawer(false);
    }
  } else if ((e.key === 'm' || e.key === 'M') && !isInput) {
    showcaseStore.toggleAudio();
  }
}

/**
 * 展厅根节点点击事件 (纯享模式下点击除控制条外任意空白瞬时唤醒)
 * @param {MouseEvent} e 鼠标事件
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/handleRootClick
 * @throws 无异常抛出
 */
function handleRootClick(e: MouseEvent): void {
  if (showcaseStore.isZenMode) {
    const target = e.target as HTMLElement;
    if (!target.closest('#zen-control-bar, #btn-exit-zen, #btn-enter-zen, #btn-quick-zen-cta')) {
      showcaseStore.setZenMode(false);
    }
  }
}

/**
 * 拖拽媒体文件进入视口
 * @param {DragEvent} e 拖拽进入事件
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/handleDragEnter
 * @throws 无异常抛出
 */
function handleDragEnter(e: DragEvent): void {
  e.preventDefault();
  dragCounter++;
  if (e.dataTransfer && e.dataTransfer.types.includes('Files')) {
    isDraggingFile.value = true;
  }
}

/**
 * 拖拽媒体文件离开视口
 * @param {DragEvent} e 拖拽离开事件
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/handleDragLeave
 * @throws 无异常抛出
 */
function handleDragLeave(e: DragEvent): void {
  e.preventDefault();
  dragCounter--;
  if (dragCounter <= 0) {
    dragCounter = 0;
    isDraggingFile.value = false;
  }
}

/**
 * 拖拽悬停事件
 * @param {DragEvent} e 拖拽移动悬停事件
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/handleDragOver
 * @throws 无异常抛出
 */
function handleDragOver(e: DragEvent): void {
  e.preventDefault();
}

/**
 * 拖拽松手释放媒体文件，即刻生成壁纸对象并全屏映入
 * @param {DragEvent} e 拖拽释放事件
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/handleDrop
 * @throws 无异常抛出
 */
function handleDrop(e: DragEvent): void {
  e.preventDefault();
  dragCounter = 0;
  isDraggingFile.value = false;

  const files = e.dataTransfer?.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  const isVideo = file.type.startsWith('video/');
  const objectUrl = URL.createObjectURL(file);

  const customItem: WallpaperItem = {
    id: `drag-${Date.now()}`,
    title: `拖入: ${file.name}`,
    category: isVideo ? 'video' : 'scene',
    resolutionBadge: isVideo ? '拖拽 4K 视频' : '拖拽超清图片',
    isPreset: false,
    type: isVideo ? 'video' : 'scene',
    hasVideo: isVideo,
    hasAudio: isVideo,
    videoUrl: isVideo ? objectUrl : '',
    audioUrl: isVideo ? objectUrl : '',
    src: objectUrl,
    thumb: isVideo ? '' : objectUrl
  };

  showcaseStore.addCustomWallpaper(customItem);
}

/**
 * 处理医慧通行模态登录成功回调并跳转对应工作台
 * @param {object} [userInfo] 登录用户信息
 * @returns {void}
 * @route internal://src/views/ShowcaseView.vue/handleLoginSuccess
 * @throws {Error} 路由跳转异常兜底
 */
function handleLoginSuccess(userInfo?: any): void {
  showcaseStore.closeLoginModal();
  showcaseStore.isLoginModalOpen = false;

  // 依据进入场景：若由 /login 访问、携带 ?login 参数或由工作台入口按钮触发，则精准导向目标工作台
  if (route.query.login !== undefined || route.path === '/login' || showcaseStore.isWorkbenchEntryPending) {
    showcaseStore.isWorkbenchEntryPending = false;
    const role = userStore.currentUser?.roleCode;
    if (role === 'supplier_user') {
      router.push('/procurement').catch((err: Error) => {
        console.error('工作台路由跳转异常:', err);
      });
    } else if (role === 'secondary_user') {
      router.push('/secondary').catch((err: Error) => {
        console.error('工作台路由跳转异常:', err);
      });
    } else if (role === 'finance_auditor') {
      router.push('/finance').catch((err: Error) => {
        console.error('工作台路由跳转异常:', err);
      });
    } else {
      router.push('/dict').catch((err: Error) => {
        console.error('工作台路由跳转异常:', err);
      });
    }
  }
}

watch(
  () => route.query.login,
  (val) => {
    if (val !== undefined) {
      showcaseStore.openLoginModal();
    }
  }
);

onMounted(() => {
  showcaseStore.initStore();
  document.documentElement.setAttribute('data-theme', userStore.theme);
  window.addEventListener('keydown', handleGlobalKeydown);
  syncAudio();
  // 响应式联动：若通过 /login 或带有 ?login 参数访问，即刻从右侧动态滑出医慧通行登录抽屉
  if (route.query.login !== undefined || route.path === '/login') {
    showcaseStore.openLoginModal();
  }
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown);
  if (showcaseStore.isZenMode) {
    document.body.classList.remove('zen-pure-mode');
  }
});
</script>

<style scoped>
.spd-showcase-root {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-page, #080c14);
  color: var(--text-primary, #f8fafc);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif;
  user-select: none;
}

/* Layer 0: 全屏动态壁纸底层 */
.wallpaper-media-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  background-size: cover;
  background-position: center center;
  transition: background 400ms ease;
}

.wallpaper-video-bg {
  position: absolute;
  inset: 0;
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
  object-position: center center !important;
  display: none;
}

.wallpaper-video-bg.active {
  display: block;
}

/* Layer 1: 轻量调光层 (与 Demo 1:1 对齐，保持全屏动态壁纸与 4K 视频清澈可见) */
.wallpaper-dimmer-layer {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: rgba(8, 12, 20, var(--wp-dim, 0.35));
  transition: background 300ms ease, opacity 300ms ease;
}

/* 全屏文件拖拽即映入提示遮罩 */
.drag-drop-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(2, 132, 199, 0.35);
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
  border: 3px dashed #38bdf8;
  display: none;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 14px;
  pointer-events: none;
}

.drag-drop-overlay.active {
  display: flex;
}

.drag-drop-text {
  font-size: 20px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

/* 舞台自适应位移外壳：唤起右侧登录时 GPU 加速平滑向左平移 240px，为右侧卡片让位 */
.showcase-stage-viewport {
  position: absolute;
  inset: 0;
  pointer-events: none;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}

.showcase-stage-viewport.stage-shift-left {
  transform: translateX(-240px);
}

.showcase-stage-viewport > * {
  pointer-events: auto;
}

/* 中央舞台居中定位外壳 */
.hero-stage-wrapper {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  pointer-events: none;
}
</style>
