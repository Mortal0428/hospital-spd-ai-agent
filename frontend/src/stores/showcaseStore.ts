import { defineStore } from 'pinia';

/**
 * @file showcaseStore.ts
 * @description 数字化展厅双模态全景门户与壁纸工坊 Pinia 状态管理
 * 管理 360° 全域轨道与 3D 弧面切片双模态切换、纯享壁纸态、动态壁纸图库资产 (41款)、
 * 模态安全登录弹窗开闭、环境音频同步与桌面防抖数字时钟等核心状态。
 */

/**
 * 壁纸工坊单项资产元数据接口
 */
export interface WallpaperItem {
  id: string;
  title: string;
  category: 'preset' | 'video' | 'scene';
  resolutionBadge?: string;
  isPreset?: boolean;
  type: string;
  hasVideo?: boolean;
  hasAudio?: boolean;
  hasExtractedTexture?: boolean;
  videoSizeMb?: string | null;
  previewUrl?: string;
  fullscreenUrl?: string;
  videoUrl?: string;
  audioUrl?: string;
  src: string;
  thumb?: string;
  folderPath?: string;
}

/**
 * 展厅展示的核心医疗资产定义
 */
export interface MedicalAsset {
  id: string;
  tag: string;
  title: string;
  sub: string;
  status: string;
  targetRoute: string;
}

/**
 * 10 大核心医疗物资业务流向数据源 (与 Demo 1:1 对齐)
 */
export const MEDICAL_ASSETS: MedicalAsset[] = [
  { id: '01', tag: '药监局UDI', title: '产品字典双维档案', sub: '耗材科/设备科主库双归口', status: '已建档 5 项标准物料', targetRoute: '/dict' },
  { id: '02', tag: '效期硬风控', title: '主库集中验收入库', sub: '冷链温控监测 · 注册证资质比对', status: '主库在库 1,870 件', targetRoute: '/general' },
  { id: '03', tag: 'FEFO优先', title: '主库按需分发调拨', sub: '近效期先出 · 院内移库不计费', status: '已下发调拨单 200 支', targetRoute: '/general' },
  { id: '04', tag: '一物一码SN', title: '高值专仓智能柜', sub: '由量到码智能拆包赋码锁定', status: '专柜锁定 37 套', targetRoute: '/high-value' },
  { id: '05', tag: '定数包补货', title: '临床二级库房管理', sub: '骨科/心内科病区安全水位预警', status: '低库存自动申领就绪', targetRoute: '/secondary' },
  { id: '06', tag: '消耗即结算', title: '患者扫码脱敏核销', sub: '临床手术消耗绑定住院号记账', status: '已脱敏核销: 张*丰', targetRoute: '/secondary' },
  { id: '07', tag: '100%穿透', title: '全流程 6W 物权台账', sub: '人/物/时间/流向完整快照', status: '审计合规率 100%', targetRoute: '/logs' },
  { id: '08', tag: '法定单据', title: '医院四联签字单据', sub: '制单/主库/领用/财务责任签章', status: '符合三甲内控规范', targetRoute: '/finance' },
  { id: '09', tag: '智能调拨', title: 'Agent 02 补货智能体', sub: 'LangGraph 驱动多库房水位扫描', status: '毫秒级调度就绪', targetRoute: '/general' },
  { id: '10', tag: '逆向召回', title: 'Agent 04 溯源与召回', sub: 'UDI 穿透溯源与问题批次冻结', status: '全链路闭环就绪', targetRoute: '/high-value' }
];

/**
 * 系统内置预设高洁光晕壁纸 (当本地 Steam 工坊路径缺失时作为优雅离线兜底)
 */
export const PRESET_WALLPAPERS: WallpaperItem[] = [
  {
    id: 'preset-cyan',
    title: '深空钛青医疗科技',
    category: 'preset',
    resolutionBadge: '矢量光晕',
    isPreset: true,
    type: 'gradient',
    hasVideo: false,
    hasAudio: false,
    src: 'radial-gradient(ellipse at center, #0c4a6e 0%, #080c14 70%)',
    thumb: ''
  },
  {
    id: 'preset-pure-white',
    title: '极简白瓷高洁',
    category: 'preset',
    resolutionBadge: '纯净高透',
    isPreset: true,
    type: 'gradient-white',
    hasVideo: false,
    hasAudio: false,
    src: 'linear-gradient(135deg, #f1f5f9 0%, #ffffff 100%)',
    thumb: ''
  }
];

export const useShowcaseStore = defineStore('showcase', {
  state: () => {
    const savedMode = (localStorage.getItem('spd_showcase_mode') || 'orbital') as 'orbital' | 'tilted';
    const savedWallpaperId = localStorage.getItem('spd_active_wallpaper_id') || 'preset-cyan';
    const savedAudioEnabled = localStorage.getItem('spd_audio_enabled') === 'true';
    const savedAudioVolume = parseFloat(localStorage.getItem('spd_audio_volume') || '0.65');
    const savedClockVisible = localStorage.getItem('spd_clock_visible') !== 'false';

    return {
      /** 当前展厅 3D 渲染模态：'orbital' (360° 环形轨道) | 'tilted' (3D 弧面立体切片) */
      currentMode: savedMode,
      /** 是否处于纯享壁纸态 (彻底隐退前景卡片并暂停动画) */
      isZenMode: false,
      /** 医慧通行现代医疗模态登录中枢开闭状态 */
      isLoginModalOpen: false,
      /** 壁纸工坊底部抽屉面板开闭状态 */
      isWallpaperDrawerOpen: false,
      /** 全量壁纸资产列表 (包含预设与 39 款本地工坊) */
      wallpapers: [...PRESET_WALLPAPERS] as WallpaperItem[],
      /** 当前激活的壁纸唯一标识 */
      activeWallpaperId: savedWallpaperId,
      /** 环境音效/背景视频音频是否播放中 */
      isAudioPlaying: savedAudioEnabled,
      /** 音频音量比例 (0.0 ~ 1.0) */
      audioVolume: isNaN(savedAudioVolume) ? 0.65 : Math.max(0, Math.min(1, savedAudioVolume)),
      /** 桌面实时防抖数字时钟是否开启展示 */
      isClockVisible: savedClockVisible,
      /** 是否由工作台入口触发的待跳转状态 */
      isWorkbenchEntryPending: false
    };
  },

  getters: {
    /**
     * 获取当前处于激活状态的壁纸对象
     * @param state Pinia 状态对象
     * @returns {WallpaperItem} 当前壁纸
     * @route internal://src/stores/showcaseStore/activeWallpaper
     * @throws 无异常抛出
     */
    activeWallpaper(state): WallpaperItem {
      const found = state.wallpapers.find((w) => w.id === state.activeWallpaperId);
      return found || state.wallpapers[0] || PRESET_WALLPAPERS[0];
    },

    /**
     * 获取当前壁纸图库总数
     * @param state Pinia 状态对象
     * @returns {number} 壁纸总数
     * @route internal://src/stores/showcaseStore/wallpaperCount
     * @throws 无异常抛出
     */
    wallpaperCount(state): number {
      return state.wallpapers.length;
    }
  },

  actions: {
    /**
     * 切换双模态渲染引擎 (orbital 环形轨道 vs tilted 弧面切片)
     * @param {'orbital' | 'tilted'} [targetMode] 可选目标模态
     * @returns {void}
     * @route internal://src/stores/showcaseStore/toggleMode
     * @throws 无异常抛出
     */
    toggleMode(targetMode?: 'orbital' | 'tilted'): void {
      const next = targetMode || (this.currentMode === 'orbital' ? 'tilted' : 'orbital');
      this.currentMode = next;
      try {
        localStorage.setItem('spd_showcase_mode', next);
      } catch {
        // 忽略本地存储写入限制
      }
    },

    /**
     * 设置纯享壁纸态开关
     * @param {boolean} val 是否进入纯享
     * @returns {void}
     * @route internal://src/stores/showcaseStore/setZenMode
     * @throws 无异常抛出
     */
    setZenMode(val: boolean): void {
      this.isZenMode = val;
      if (val) {
        this.isWallpaperDrawerOpen = false;
        document.body.classList.add('zen-pure-mode');
      } else {
        document.body.classList.remove('zen-pure-mode');
      }
    },

    /**
     * 唤起医慧通行模态登录卡片
     * @param {boolean} [forWorkbench=false] 是否由工作台跳转入口触发
     * @returns {void}
     * @route internal://src/stores/showcaseStore/openLoginModal
     * @throws 无异常抛出
     */
    openLoginModal(forWorkbench = false): void {
      this.isLoginModalOpen = true;
      this.isWorkbenchEntryPending = forWorkbench;
    },

    /**
     * 关闭医慧通行模态登录卡片
     * @returns {void}
     * @route internal://src/stores/showcaseStore/closeLoginModal
     * @throws 无异常抛出
     */
    closeLoginModal(): void {
      this.isLoginModalOpen = false;
    },

    /**
     * 开闭壁纸工坊底部抽屉面板
     * @param {boolean} [open] 可选显隐状态
     * @returns {void}
     * @route internal://src/stores/showcaseStore/toggleWallpaperDrawer
     * @throws 无异常抛出
     */
    toggleWallpaperDrawer(open?: boolean): void {
      if (open !== undefined) {
        this.isWallpaperDrawerOpen = open;
      } else {
        this.isWallpaperDrawerOpen = !this.isWallpaperDrawerOpen;
      }
    },

    /**
     * 选取并切换当前激活的动态壁纸
     * @param {WallpaperItem} wp 目标壁纸对象
     * @returns {void}
     * @route internal://src/stores/showcaseStore/selectWallpaper
     * @throws 无异常抛出
     */
    selectWallpaper(wp: WallpaperItem): void {
      if (!wp || !wp.id) return;
      this.activeWallpaperId = wp.id;
      try {
        localStorage.setItem('spd_active_wallpaper_id', wp.id);
      } catch {
        // 忽略异常
      }
    },

    /**
     * 自由切换环境背景音乐/视频音轨静音状态
     * @param {boolean} [playing] 目标播放状态
     * @returns {void}
     * @route internal://src/stores/showcaseStore/toggleAudio
     * @throws 无异常抛出
     */
    toggleAudio(playing?: boolean): void {
      const next = playing !== undefined ? playing : !this.isAudioPlaying;
      this.isAudioPlaying = next;
      try {
        localStorage.setItem('spd_audio_enabled', next ? 'true' : 'false');
      } catch {
        // 忽略异常
      }
    },

    /**
     * 调整音频增益音量比例
     * @param {number} vol 音量值 (0.0 ~ 1.0)
     * @returns {void}
     * @route internal://src/stores/showcaseStore/setAudioVolume
     * @throws 无异常抛出
     */
    setAudioVolume(vol: number): void {
      const clamped = Math.max(0, Math.min(1, vol));
      this.audioVolume = clamped;
      try {
        localStorage.setItem('spd_audio_volume', clamped.toString());
      } catch {
        // 忽略异常
      }
    },

    /**
     * 开关桌面实时数字时钟小部件
     * @param {boolean} [visible] 可选显隐状态
     * @returns {void}
     * @route internal://src/stores/showcaseStore/toggleClock
     * @throws 无异常抛出
     */
    toggleClock(visible?: boolean): void {
      const next = visible !== undefined ? visible : !this.isClockVisible;
      this.isClockVisible = next;
      try {
        localStorage.setItem('spd_clock_visible', next ? 'true' : 'false');
      } catch {
        // 忽略异常
      }
    },

    /**
     * 添加用户自定义拖拽或选取的本地壁纸/视频至清单首位并激活
     * @param {WallpaperItem} wp 自定义壁纸对象
     * @returns {void}
     * @route internal://src/stores/showcaseStore/addCustomWallpaper
     * @throws 无异常抛出
     */
    addCustomWallpaper(wp: WallpaperItem): void {
      this.wallpapers.unshift(wp);
      this.selectWallpaper(wp);
    },

    /**
     * 初始化加载全量壁纸清单 (从 window.WALLPAPERS_MANIFEST 读取或预设)
     * @returns {void}
     * @route internal://src/stores/showcaseStore/initStore
     * @throws 忽略解析异常
     */
    initStore(): void {
      interface ManifestWindow extends Window {
        WALLPAPERS_MANIFEST?: {
          items?: WallpaperItem[];
        };
        __WALLPAPERS_MANIFEST__?: {
          items?: WallpaperItem[];
        };
      }
      const win = typeof window !== 'undefined' ? (window as ManifestWindow) : null;
      const manifest = win?.WALLPAPERS_MANIFEST || win?.__WALLPAPERS_MANIFEST__;

      if (manifest?.items && Array.isArray(manifest.items) && manifest.items.length > 0) {
        this.wallpapers = manifest.items;
        // 若当前仍为初始渐变预设，自动升级激活工坊标志性超清壁纸或首款 4K 动态视频壁纸
        if (this.activeWallpaperId === 'preset-cyan') {
          const preferredWp = manifest.items.find((item) => item.id === '3814965952') ||
                              manifest.items.find((item) => item.hasVideo && item.videoUrl) ||
                              manifest.items[2] || manifest.items[0];
          if (preferredWp) {
            this.activeWallpaperId = preferredWp.id;
          }
        }
      } else {
        this.wallpapers = [...PRESET_WALLPAPERS];
      }

      // 若激活的壁纸不在清单中，回退至首选预设
      if (!this.wallpapers.some((w) => w.id === this.activeWallpaperId)) {
        this.activeWallpaperId = this.wallpapers[0]?.id || 'preset-cyan';
      }
    }
  }
});
