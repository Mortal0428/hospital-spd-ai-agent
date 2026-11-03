<template>
  <div
    id="wallpaper-drawer"
    class="wallpaper-drawer-panel"
    :class="{ open: showcaseStore.isWallpaperDrawerOpen }"
    role="dialog"
    aria-label="壁纸工坊全量图库抽屉"
  >
    <!-- 抽屉头部标题与关闭按钮 -->
    <div class="drawer-header">
      <div class="drawer-title-group">
        <SvgIcon name="wallpaper" size="18" color="#38bdf8" />
        <span>Wallpaper Engine 本地工坊全量壁纸库 ({{ showcaseStore.wallpaperCount }}款)</span>
      </div>
      <button
        id="btn-close-wallpaper"
        type="button"
        class="drawer-close-btn"
        aria-label="关闭壁纸工坊抽屉"
        @click="showcaseStore.toggleWallpaperDrawer(false)"
      >
        <SvgIcon name="close" size="14" />
      </button>
    </div>

    <!-- 抽屉顶部操作工具栏：类别过滤、动态下划线搜索与自由选图 -->
    <div class="drawer-toolbar">
      <!-- 类别过滤选项卡 -->
      <div class="filter-tabs" role="tablist">
        <button
          type="button"
          class="filter-btn"
          :class="{ active: currentCategory === 'all' }"
          @click="currentCategory = 'all'"
        >
          全部壁纸 ({{ countAll }})
        </button>
        <button
          type="button"
          class="filter-btn"
          :class="{ active: currentCategory === 'video' }"
          @click="currentCategory = 'video'"
        >
          4K/1080P 动态视频 ({{ countVideo }})
        </button>
        <button
          type="button"
          class="filter-btn"
          :class="{ active: currentCategory === 'scene' }"
          @click="currentCategory = 'scene'"
        >
          超清原画/场景 ({{ countScene }})
        </button>
        <button
          type="button"
          class="filter-btn"
          :class="{ active: currentCategory === 'preset' }"
          @click="currentCategory = 'preset'"
        >
          系统预设 ({{ countPreset }})
        </button>
      </div>

      <!-- 动态底线微交互搜索框 (微动效 ③) -->
      <form
        id="spd-wallpaper-search-form"
        class="spd-search-form"
        @submit.prevent
      >
        <button type="button" class="spd-search-btn" aria-label="搜索壁纸">
          <SvgIcon name="search" size="14" />
        </button>
        <input
          id="spd-search-input"
          v-model="searchQuery"
          class="spd-search-input"
          placeholder="输入壁纸名称或序号筛选..."
          type="text"
          autocomplete="off"
        />
        <button
          id="spd-search-reset"
          type="button"
          class="spd-search-reset"
          aria-label="清空搜索"
          @click="searchQuery = ''"
        >
          <SvgIcon name="close" size="12" />
        </button>
      </form>

      <!-- 自由文件选取与桌面时钟联动 -->
      <div class="drawer-custom-actions">
        <button
          id="btn-toggle-clock"
          type="button"
          class="btn-custom-picker"
          title="切换桌面实时数字时钟小部件"
          @click="showcaseStore.toggleClock()"
        >
          <SvgIcon name="clock" size="14" />
          <span id="clock-toggle-text">
            桌面时钟: {{ showcaseStore.isClockVisible ? '开启' : '关闭' }}
          </span>
        </button>
        <button
          id="btn-pick-custom-file"
          type="button"
          class="btn-custom-picker"
          title="自由选取电脑中任意 MP4 视频或超清图片"
          @click="handleTriggerFilePicker"
        >
          <SvgIcon name="upload" size="14" />
          <span>自由选取本地壁纸/视频</span>
        </button>
        <input
          id="local-file-picker"
          ref="fileInputRef"
          type="file"
          accept="video/mp4,video/webm,image/*"
          style="display: none"
          @change="handleLocalFileChange"
        />
      </div>
    </div>

    <!-- 动态滚动画廊网格 -->
    <div class="wallpaper-scroll-container">
      <div id="wallpaper-grid-dynamic" class="wallpaper-grid">
        <div
          v-for="item in filteredWallpapers"
          :key="item.id"
          class="wallpaper-thumb-card"
          :class="{ active: item.id === showcaseStore.activeWallpaperId }"
          :title="item.title"
          @click="handleSelectWallpaper(item)"
        >
          <!-- 缩略图呈现或渐变兜底 -->
          <img
            v-if="item.thumb || item.previewUrl"
            :src="item.thumb || item.previewUrl"
            :alt="item.title"
            loading="lazy"
            @error="handleImageError($event, item)"
          />
          <div
            v-else
            class="wallpaper-gradient-placeholder"
            :style="{ background: item.src }"
          ></div>

          <!-- 类别角标 -->
          <span
            class="wallpaper-type-badge"
            :class="{
              'badge-4k': item.hasVideo,
              'badge-scene': item.category === 'scene',
              'badge-preset': item.isPreset
            }"
          >
            {{ item.resolutionBadge || (item.hasVideo ? '4K 视频' : item.isPreset ? '系统预设' : '场景壁纸') }}
          </span>

          <!-- 壁纸标题栏 -->
          <div class="wallpaper-thumb-title">
            {{ item.title }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useShowcaseStore, type WallpaperItem } from '@/stores/showcaseStore';
import SvgIcon from '@/components/common/SvgIcon.vue';

/**
 * @file WallpaperDrawer.vue
 * @description 升级版 41 款壁纸工坊底部抽屉面板
 * 包含类别分类过滤、动态底线微交互搜索框、桌面时钟开关、本地文件上传及 41 款缩略图自适应网格。
 */

const showcaseStore = useShowcaseStore();

const fileInputRef = ref<HTMLInputElement | null>(null);
const currentCategory = ref<'all' | 'video' | 'scene' | 'preset'>('all');
const searchQuery = ref('');

const countAll = computed(() => showcaseStore.wallpapers.length);
const countVideo = computed(() => showcaseStore.wallpapers.filter((w) => w.hasVideo || w.category === 'video').length);
const countScene = computed(() => showcaseStore.wallpapers.filter((w) => !w.isPreset && !w.hasVideo && w.category === 'scene').length);
const countPreset = computed(() => showcaseStore.wallpapers.filter((w) => w.isPreset || w.category === 'preset').length);

/**
 * 依据当前分类 Tab 与搜索关键字过滤壁纸列表
 */
const filteredWallpapers = computed<WallpaperItem[]>(() => {
  let list = showcaseStore.wallpapers;

  // 1. 类别过滤
  if (currentCategory.value === 'video') {
    list = list.filter((w) => w.hasVideo || w.category === 'video');
  } else if (currentCategory.value === 'scene') {
    list = list.filter((w) => !w.isPreset && !w.hasVideo && w.category === 'scene');
  } else if (currentCategory.value === 'preset') {
    list = list.filter((w) => w.isPreset || w.category === 'preset');
  }

  // 2. 关键字过滤
  const q = searchQuery.value.trim().toLowerCase();
  if (q) {
    list = list.filter((w) => w.title.toLowerCase().includes(q) || w.id.toLowerCase().includes(q));
  }

  return list;
});

/**
 * 选取壁纸项
 * @param {WallpaperItem} item 壁纸项
 * @returns {void}
 * @route internal://src/components/showcase/WallpaperDrawer.vue/handleSelectWallpaper
 * @throws 无异常抛出
 */
function handleSelectWallpaper(item: WallpaperItem): void {
  showcaseStore.selectWallpaper(item);
}

/**
 * 唤起本地文件选择框
 * @returns {void}
 * @route internal://src/components/showcase/WallpaperDrawer.vue/handleTriggerFilePicker
 * @throws 无异常抛出
 */
function handleTriggerFilePicker(): void {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
}

/**
 * 监听本地文件选择事件，将其封装为壁纸对象并即刻激活
 * @param {Event} e DOM变更事件
 * @returns {void}
 * @route internal://src/components/showcase/WallpaperDrawer.vue/handleLocalFileChange
 * @throws 异常时静默拦截
 */
function handleLocalFileChange(e: Event): void {
  const target = e.target as HTMLInputElement;
  const files = target.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  const isVideo = file.type.startsWith('video/');
  const objectUrl = URL.createObjectURL(file);

  const customItem: WallpaperItem = {
    id: `local-${Date.now()}`,
    title: `本地选入: ${file.name}`,
    category: isVideo ? 'video' : 'scene',
    resolutionBadge: isVideo ? '本地视频' : '本地超清',
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
 * 图片加载失败兜底
 * @param {Event} e 错误事件
 * @param {WallpaperItem} item 对应壁纸项
 * @returns {void}
 * @route internal://src/components/showcase/WallpaperDrawer.vue/handleImageError
 * @throws 无异常抛出
 */
function handleImageError(e: Event, item: WallpaperItem): void {
  const imgEl = e.target as HTMLImageElement;
  imgEl.style.display = 'none';
  if (imgEl.parentElement) {
    imgEl.parentElement.style.background = item.src.startsWith('linear') || item.src.startsWith('radial')
      ? item.src
      : 'radial-gradient(ellipse at center, #0c4a6e 0%, #080c14 70%)';
  }
}
</script>

<style scoped>
.wallpaper-drawer-panel {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%) translateY(120%);
  z-index: 150;
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(28px) saturate(2);
  backdrop-filter: blur(28px) saturate(2);
  border: 1px solid var(--border-card);
  border-radius: 24px;
  padding: 20px 24px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.45);
  max-width: 1040px;
  width: 94%;
  max-height: 440px;
  display: flex;
  flex-direction: column;
  transition: transform 350ms cubic-bezier(0.16, 1, 0.3, 1);
  pointer-events: auto;
}

.wallpaper-drawer-panel.open {
  transform: translateX(-50%) translateY(0);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.drawer-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.drawer-close-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 150ms ease-out;
}

.drawer-close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

.drawer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.filter-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-btn {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-card);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 150ms ease-out, color 150ms ease-out, border-color 150ms ease-out;
}

.filter-btn:hover {
  color: var(--text-primary);
}

.filter-btn.active {
  background: var(--accent-primary);
  color: #ffffff;
  border-color: var(--accent-primary);
  box-shadow: 0 2px 8px rgba(2, 132, 199, 0.4);
}

.drawer-custom-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-custom-picker {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  background: rgba(2, 132, 199, 0.14);
  border: 1px solid rgba(2, 132, 199, 0.3);
  color: var(--accent-primary);
  cursor: pointer;
  transition: background 150ms ease-out;
}

.btn-custom-picker:hover {
  background: rgba(2, 132, 199, 0.25);
}

.wallpaper-scroll-container {
  overflow-y: auto;
  flex-grow: 1;
  padding-right: 4px;
}

.wallpaper-scroll-container::-webkit-scrollbar {
  width: 6px;
}

.wallpaper-scroll-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.wallpaper-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

@media (max-width: 1200px) {
  .wallpaper-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .wallpaper-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.wallpaper-thumb-card {
  border-radius: 12px;
  border: 2px solid transparent;
  overflow: hidden;
  cursor: pointer;
  transition: transform 150ms ease-out, border-color 150ms ease-out, box-shadow 150ms ease-out;
  position: relative;
  aspect-ratio: 16 / 9;
  background: #1e293b;
}

.wallpaper-thumb-card:hover {
  transform: scale(1.04);
  border-color: var(--accent-primary);
  box-shadow: 0 4px 16px rgba(2, 132, 199, 0.3);
}

.wallpaper-thumb-card.active {
  border-color: #38bdf8;
  box-shadow: 0 0 16px rgba(56, 189, 248, 0.55);
}

.wallpaper-thumb-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.wallpaper-gradient-placeholder {
  width: 100%;
  height: 100%;
}

.wallpaper-thumb-title {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 4px 6px;
  font-size: 10px;
  font-weight: 600;
  background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.88));
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wallpaper-type-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 8px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: #38bdf8;
}

.badge-4k {
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.4);
}

.badge-scene {
  color: #10b981;
}

.badge-preset {
  color: #f59e0b;
}
</style>
