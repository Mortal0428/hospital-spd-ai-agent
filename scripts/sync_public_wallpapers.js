/**
 * 医疗物资系统前端 public 壁纸清单同步脚本
 * 将 docs/design/wallpapers_manifest.json (39款) 与 2 款系统预设整合为 41 款完整清单
 * 输出至 frontend/public/wallpapers_manifest.js
 */
const fs = require('fs');
const path = require('path');

const jsonPath = path.resolve(__dirname, '../docs/design/wallpapers_manifest.json');
const targetPath = path.resolve(__dirname, '../frontend/public/wallpapers_manifest.js');

const raw = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));

const presets = [
  {
    id: 'preset-cyan',
    title: '深空钛青医疗科技',
    category: 'preset',
    resolutionBadge: '矢量光晕',
    isPreset: true,
    type: 'gradient',
    hasVideo: false,
    hasAudio: false,
    hasExtractedTexture: false,
    videoSizeMb: null,
    previewUrl: '',
    fullscreenUrl: '',
    videoUrl: '',
    audioUrl: '',
    src: 'radial-gradient(ellipse at center, #0c4a6e 0%, #080c14 70%)',
    thumb: '',
    folderPath: ''
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
    hasExtractedTexture: false,
    videoSizeMb: null,
    previewUrl: '',
    fullscreenUrl: '',
    videoUrl: '',
    audioUrl: '',
    src: 'linear-gradient(135deg, #f1f5f9 0%, #ffffff 100%)',
    thumb: '',
    folderPath: ''
  }
];

const normalizedItems = raw.items.map(it => ({
  ...it,
  src: it.videoUrl || it.fullscreenUrl || it.previewUrl || '',
  thumb: it.previewUrl || it.fullscreenUrl || ''
}));

const allItems = [...presets, ...normalizedItems];

const finalManifest = {
  scanTime: raw.scanTime,
  totalCount: allItems.length,
  presetCount: presets.length,
  videoCount: raw.videoCount,
  audioCount: raw.audioCount,
  sceneCount: raw.sceneCount,
  workshopPath: raw.workshopPath,
  items: allItems
};

const headerComment = [
  '/**',
  ' * @file wallpapers_manifest.js',
  ' * @description 数字化展厅 4K 动态壁纸与系统预设全量资产清单 (41款)',
  ' * 包含 2 款系统预设高洁光晕 + 39 款本地工坊超清/4K 原生动态壁纸。',
  ' * 暴露 window.WALLPAPERS_MANIFEST 与 window.__WALLPAPERS_MANIFEST__。',
  ' *',
  ' * @param 无',
  ' * @returns {object} 壁纸资产清单对象',
  ' * @route internal://public/wallpapers_manifest.js',
  ' * @throws 无',
  ' */',
  '',
  'const manifestData = ' + JSON.stringify(finalManifest, null, 2) + ';',
  '',
  'if (typeof window !== "undefined") {',
  '  window.WALLPAPERS_MANIFEST = manifestData;',
  '  window.__WALLPAPERS_MANIFEST__ = manifestData;',
  '}',
  'if (typeof module !== "undefined" && module.exports) {',
  '  module.exports = manifestData;',
  '}',
  ''
].join('\n');

const dir = path.dirname(targetPath);
if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}

fs.writeFileSync(targetPath, headerComment, 'utf8');
console.log('Successfully written wallpapers_manifest.js with totalCount:', allItems.length);
