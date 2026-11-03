<template>
  <svg
    :class="['svg-icon', className]"
    :viewBox="viewBox"
    :width="computedSize"
    :height="computedSize"
    :fill="fill"
    :stroke="color"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    :aria-label="ariaLabel || name"
    v-html="iconSvgContent"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';

/**
 * @file SvgIcon.vue
 * @description 统一纯矢量 SVG 图标组件 (100% 严禁 Emoji 表情)
 * 严格遵照 Apple HIG 与现代化医疗物资系统的极简质感设计，
 * 封装了 38 种常用业务、拓扑、设备、审计及流向纯矢量路径。
 */

interface SvgIconProps {
  /** 图标唯一名称 */
  name: string;
  /** 图标尺寸 (像素数字或 CSS 尺寸字符串，默认 16) */
  size?: number | string;
  /** 图标描边颜色 (默认 currentColor，跟随父级文本色) */
  color?: string;
  /** 填充颜色 (默认 none) */
  fill?: string;
  /** 描边粗细 (默认 1.8) */
  strokeWidth?: number | string;
  /** 视口比例 (默认 0 0 24 24) */
  viewBox?: string;
  /** 附加 CSS 类名 */
  className?: string;
  /** 无障碍辅助标签 */
  ariaLabel?: string;
}

const props = withDefaults(defineProps<SvgIconProps>(), {
  size: 16,
  color: 'currentColor',
  fill: 'none',
  strokeWidth: 1.8,
  viewBox: '0 0 24 24',
  className: '',
  ariaLabel: ''
});

/**
 * 格式化尺寸属性，支持数字或带单位的字符串
 * @param {number|string} val 传入的尺寸值
 * @returns {string} 标准 CSS 尺寸单位
 * @route internal://SvgIcon.vue#formatSize
 * @throws 无
 */
function formatSize(val: number | string): string {
  if (typeof val === 'number') {
    return `${val}px`;
  }
  return /^\d+$/.test(val) ? `${val}px` : val;
}

const computedSize = computed(() => formatSize(props.size));

/**
 * 38 款无 Emoji 纯矢量 SVG 内联路径库字典
 */
const ICON_PATH_MAP: Record<string, string> = {
  // 1. 医疗系统品牌 Logo 图标 (Medical Cross Brand)
  'medical-cross': '<path d="M12 2v20M2 12h20M7 7l10 10M17 7L7 17"/>',
  'logo': '<path d="M12 2v20M2 12h20M7 7l10 10M17 7L7 17"/>',
  'brand': '<path d="M12 2v20M2 12h20M7 7l10 10M17 7L7 17"/>',

  // 2. 360° 轨道拓扑模式图标 (Orbital Mode)
  'orbital': '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 9 9M3 12a9 9 0 0 1 9-9"/>',
  'mode-orbital': '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 9 9M3 12a9 9 0 0 1 9-9"/>',

  // 3. 3D 弧面圆柱流光模式图标 (Tilted Grid Mode)
  'tilted': '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
  'mode-tilted': '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',

  // 4. 音频开启图标 (Audio On)
  'audio-on': '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>',
  'volume': '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>',

  // 5. 音频静音图标 (Audio Muted)
  'audio-muted': '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>',
  'mute': '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>',

  // 6. 壁纸工坊画廊图标 (Wallpaper Image Gallery)
  'wallpaper': '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
  'gallery': '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',

  // 7. 纯享模式眼睛图标 (Zen Pure Eye)
  'eye': '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
  'zen': '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',

  // 8. 密码切换闭眼图标 (Password Eye Slash)
  'eye-slash': '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>',
  'eye-off': '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>',

  // 9. 医护工号身份图标 (User Silhouette)
  'user': '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',

  // 10. 安全访问密码锁图标 (Lock Padlock)
  'lock': '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',

  // 11. 关闭与退出叉号图标 (Close Cross)
  'close': '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  'x': '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',

  // 12. 搜索放大镜图标 (Search Magnifier)
  'search': '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',

  // 13. 时钟表盘图标 (Clock Face)
  'clock': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',

  // 14. 本地文件选择与上传图标 (Upload Tray)
  'upload': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>',

  // 15. 耗材科管理员角色图标 (Cube Package)
  'package': '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
  'consumable': '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',

  // 16. 临床二级库角色图标 (ECG Heartbeat Pulse)
  'pulse': '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  'nurse': '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  'activity': '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',

  // 17. 财务科合规审计角色图标 (Financial Balance Scale)
  'scale': '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
  'finance': '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',

  // 18. 亮暗主题太阳图标 (Sun Rays)
  'sun': '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',

  // 19. 亮暗主题月亮图标 (Moon Crescent)
  'moon': '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',

  // 20. 法定单据四联打印机图标 (Printer Voucher)
  'printer': '<polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>',

  // 21. 智能体协同机器人图标 (Agent Robot)
  'robot': '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 16h0.01M16 16h0.01"/>',
  'agent': '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 16h0.01M16 16h0.01"/>',

  // 22. 全流程 6W 审计安全盾牌图标 (Security Shield)
  'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',

  // 23. 一物一码日历核销图标 (Calendar Check)
  'calendar': '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',

  // 24. 产品字典管理书本图标 (Book Dictionary)
  'book': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  'dict': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',

  // 25. 高值专仓保险箱图标 (High-Value Safe Box)
  'box-lock': '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
  'safe': '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',

  // 26. 临床二级库房房屋图标 (Secondary Department Room)
  'home': '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  'room': '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',

  // 27. 流转日志列表图标 (Workflow Log List)
  'list': '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
  'log': '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',

  // 28. 财务统计柱状图图标 (Stats Bar Chart)
  'bar-chart': '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
  'stats': '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',

  // 29. 方向箭头 (Chevron / Arrow)
  'arrow-right': '<polyline points="9 18 15 12 9 6"/>',
  'arrow-left': '<polyline points="15 18 9 12 15 6"/>',

  // 30. 成功对勾 (Check Mark)
  'check': '<polyline points="20 6 9 17 4 12"/>',

  // 31. 告警三角 (Alert Triangle)
  'alert-triangle': '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  'warning': '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',

  // 32. 消息提示圆圈 (Info Circle)
  'info': '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',

  // 33. 同步刷新 (Refresh Sync)
  'refresh': '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',

  // 34. 外部跳转链接 (External Link)
  'external-link': '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',

  // 35. 脉冲内核星标 (Pulse Star)
  'star': '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',

  // 36. 设备科管理角色图标 (Equipment Wrench Tool)
  'equip': '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  'wrench': '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',

  // 37. 漏斗筛选 (Filter Funnel)
  'filter': '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',

  // 38. 钥匙授权 (Key Token)
  'key': '<path d="M21 2l-2 2m-1.5 1.5L12 11l4 4 1.5-1.5M19 4l-4 4m2-2l-2 2M7.5 10.5a5 5 0 1 0 7 7 5 5 0 0 0-7-7z"/>'
};

/**
 * 依据传入名称获取对应的纯矢量 SVG 内部节点内容
 * @param {string} iconName 图标名称
 * @returns {string} 矢量路径字符串
 * @route internal://SvgIcon.vue#resolveIconContent
 * @throws 当未匹配到图标时优雅降级为默认圆点指示器，不抛出异常
 */
function resolveIconContent(iconName: string): string {
  if (!iconName) {
    return '<circle cx="12" cy="12" r="6"/>';
  }
  const cleanName = iconName.trim().toLowerCase();
  const matched = ICON_PATH_MAP[cleanName];
  if (matched) {
    return matched;
  }
  // 未知图标优雅兜底：纯圆圈加中心微标
  return '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2"/>';
}

const iconSvgContent = computed(() => resolveIconContent(props.name));
</script>

<style scoped>
.svg-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  transition: stroke 0.2s ease, transform 0.2s ease;
}
</style>
