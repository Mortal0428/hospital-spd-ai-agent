/**
 * Wallpaper Engine 本地工坊壁纸扫描与全量清单生成脚本 (全格式原画与原声音频解包同步版)
 *
 * 核心功能:
 * 1. 扫描 E:\SteamLibrary\steamapps\workshop\content\431960 下的所有工坊壁纸;
 * 2. 深度解析 project.json，提取标题、类型、标签及关联的真实媒体文件;
 * 3. 逆向提取内嵌 4K/60帧 MP4 视频、1080P/2K/4K/7K 无损宽屏原画 (PNG/JPEG);
 * 4. 深度提取 scene.pkg 中打包的原声音频流 (.mp3 / .flac / .ogg / .wav) 并导出为 extracted_audio.[ext];
 * 5. 规范媒体字段分层：区分全屏宽屏超清大图 (fullscreenUrl)、缩略图 (previewUrl) 与原声音频 (audioUrl);
 * 6. 输出结构化的 docs/design/wallpapers_manifest.json 与 wallpapers_manifest.js.
 *
 * @returns {object} 扫描并生成的清单元数据
 * @route internal://scripts/scan_wallpapers.js
 * @throws {Error} 工坊路径不可访问时抛出
 */

const fs = require('fs');
const path = require('path');

const WORKSHOP_DIR = 'E:\\SteamLibrary\\steamapps\\workshop\\content\\431960';
const OUTPUT_FILE = path.resolve(__dirname, '../docs/design/wallpapers_manifest.json');

/**
 * 安全解析 JSON，处理部分创意工坊 project.json 中的不规范换行与尾部逗号
 * @param {string} raw 原始文本
 * @returns {object|null} 解析后的对象
 */
function safeParseJson(raw) {
  try {
    return JSON.parse(raw);
  } catch (e) {
    try {
      const cleaned = raw
        .replace(/[\u0000-\u001F]+/g, ' ')
        .replace(/,\s*([\]}])/g, '$1');
      return JSON.parse(cleaned);
    } catch (e2) {
      return null;
    }
  }
}

/**
 * 从 scene.pkg 中多模态逆向提取原画、内嵌视频与原声音频 (MP4 / PNG / JPEG / MP3 / FLAC / OGG)
 * @param {string} folderPath 壁纸根路径
 * @param {string} folderId 壁纸工坊 ID
 * @returns {{ extractedVideo: string|null, extractedImage: string|null, extractedAudio: string|null, resolutionBadge: string|null }}
 */
function extractScenePkgMedia(folderPath, folderId) {
  const pkgPath = path.join(folderPath, 'scene.pkg');
  if (!fs.existsSync(pkgPath)) {
    return { extractedVideo: null, extractedImage: null, extractedAudio: null, resolutionBadge: null };
  }

  const extractedMp4 = path.join(folderPath, 'extracted_fullscreen.mp4');
  const extractedPng = path.join(folderPath, 'extracted_fullscreen.png');
  const extractedJpg = path.join(folderPath, 'extracted_fullscreen.jpg');

  let extractedAudio = null;
  const audioExts = ['.mp3', '.flac', '.ogg', '.wav'];
  for (const ext of audioExts) {
    const candidate = path.join(folderPath, 'extracted_audio' + ext);
    if (fs.existsSync(candidate) && fs.statSync(candidate).size > 10000) {
      extractedAudio = candidate;
      break;
    }
  }

  let extractedVideo = null;
  let extractedImage = null;
  let resolutionBadge = null;

  if (fs.existsSync(extractedMp4) && fs.statSync(extractedMp4).size > 500000) {
    extractedVideo = extractedMp4;
    resolutionBadge = '4K/60帧原生动效';
  } else if (fs.existsSync(extractedPng) && fs.statSync(extractedPng).size > 50000) {
    extractedImage = extractedPng;
    resolutionBadge = '4K无损原画';
  } else if (fs.existsSync(extractedJpg) && fs.statSync(extractedJpg).size > 50000) {
    extractedImage = extractedJpg;
    resolutionBadge = '超清无损原画';
  }

  try {
    const buf = fs.readFileSync(pkgPath);

    // 解析 PKG 文件表以提取音频与精准视频
    let pos = 4 + buf.readUInt32LE(0);
    const fileCount = buf.readUInt32LE(pos);
    pos += 4;
    const pkgFiles = [];
    for (let i = 0; i < fileCount; i++) {
      const nameLen = buf.readUInt32LE(pos);
      pos += 4;
      const name = buf.slice(pos, pos + nameLen).toString('utf-8');
      pos += nameLen;
      const fileOffset = buf.readUInt32LE(pos);
      pos += 4;
      const fileSize = buf.readUInt32LE(pos);
      pos += 4;
      pkgFiles.push({ name, fileOffset, fileSize });
    }
    const dataBase = pos;

    // 1. 优先提取独立原声音频 (MP3 / FLAC / OGG / WAV)
    if (!extractedAudio) {
      const audioEntry = pkgFiles.find(f => /\.(mp3|flac|ogg|wav)$/i.test(f.name) && f.fileSize > 20000);
      if (audioEntry) {
        const ext = path.extname(audioEntry.name).toLowerCase();
        const outAudioPath = path.join(folderPath, 'extracted_audio' + ext);
        const audioBuf = buf.slice(dataBase + audioEntry.fileOffset, dataBase + audioEntry.fileOffset + audioEntry.fileSize);
        fs.writeFileSync(outAudioPath, audioBuf);
        extractedAudio = outAudioPath;
        console.log(`[Scanner] 成功从 ${folderId} 解包提取原声音频: ${audioEntry.name} (${(audioBuf.length / 1024).toFixed(1)}KB)`);
      }
    }

    // 2. 检测并提取原生 MP4 视频
    if (!extractedVideo && !extractedImage) {
      const ftypIdx = buf.indexOf(Buffer.from('ftyp', 'ascii'));
      if (ftypIdx !== -1 && ftypIdx >= 4) {
        const mp4Start = ftypIdx - 4;
        const targetTex = pkgFiles.find(f => f.name.endsWith('.tex') && f.fileSize > 500000);
        let targetSize = buf.length - mp4Start;
        if (targetTex) {
          targetSize = targetTex.fileSize - (ftypIdx - 4 - targetTex.fileOffset);
        }
        const mp4Buf = buf.slice(mp4Start, Math.min(buf.length, mp4Start + targetSize));
        fs.writeFileSync(extractedMp4, mp4Buf);
        extractedVideo = extractedMp4;
        resolutionBadge = '4K/60帧原生动效';
        console.log(`[Scanner] 成功从 ${folderId} 解包提取原生 4K/60帧 MP4: ${(mp4Buf.length / (1024 * 1024)).toFixed(1)}MB`);
      }
    }

    // 3. 检索 PNG 原画 (魔数: 89 50 4E 47 0D 0A 1A 0A)
    if (!extractedVideo && !extractedImage) {
      const pngHeader = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
      let searchPos = 0;
      let foundPng = null;
      while (true) {
        const idx = buf.indexOf(pngHeader, searchPos);
        if (idx === -1) break;
        if (idx + 24 < buf.length) {
          const w = buf.readUInt32BE(idx + 16);
          const h = buf.readUInt32BE(idx + 20);
          if (w >= 1280 && (!foundPng || w > foundPng.w)) {
            foundPng = { idx, w, h };
          }
        }
        searchPos = idx + 8;
      }

      if (foundPng) {
        const iendHeader = Buffer.from([0x49, 0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82]);
        const iendIdx = buf.indexOf(iendHeader, foundPng.idx);
        const endPos = iendIdx !== -1 ? iendIdx + 8 : buf.length;
        const pngBuf = buf.slice(foundPng.idx, endPos);
        fs.writeFileSync(extractedPng, pngBuf);
        extractedImage = extractedPng;
        resolutionBadge = `${foundPng.w >= 3840 ? '4K' : '超清'}无损原画`;
        console.log(`[Scanner] 成功从 ${folderId} 解包提取 PNG 原画: ${foundPng.w}x${foundPng.h}`);
      }
    }

    // 4. 检索 JPEG 原画 (魔数: FF D8 FF)
    if (!extractedVideo && !extractedImage) {
      let jSearchPos = 0;
      let foundJpg = null;
      while (true) {
        const idx = buf.indexOf(Buffer.from([0xff, 0xd8, 0xff]), jSearchPos);
        if (idx === -1) break;
        const endIdx = buf.indexOf(Buffer.from([0xff, 0xd9]), idx + 2);
        if (endIdx !== -1) {
          const len = endIdx - idx + 2;
          if (len > 50000 && (!foundJpg || len > foundJpg.len)) {
            foundJpg = { idx, endIdx: endIdx + 2, len };
          }
        }
        jSearchPos = idx + 3;
      }

      if (foundJpg) {
        const jpgBuf = buf.slice(foundJpg.idx, foundJpg.endIdx);
        fs.writeFileSync(extractedJpg, jpgBuf);
        extractedImage = extractedJpg;
        resolutionBadge = '超清无损原画';
        console.log(`[Scanner] 成功从 ${folderId} 解包提取 JPEG 原画: ${(foundJpg.len / 1024).toFixed(1)}KB`);
      }
    }
  } catch (err) {
    console.warn(`[Scanner] 解包 ${folderId} 异常: ${err.message}`);
  }

  return { extractedVideo, extractedImage, extractedAudio, resolutionBadge };
}

/**
 * 扫描指定工坊目录下所有壁纸，并生成标准 JSON 与 JS 清单
 * @returns {object} 全量清单数据
 * @route internal://scripts/scan_wallpapers.js/scanAllWallpapers
 * @throws {Error} 目录不存在时抛出
 */
function scanAllWallpapers() {
  console.log(`[Scanner] 正在扫描工坊目录: ${WORKSHOP_DIR}`);
  if (!fs.existsSync(WORKSHOP_DIR)) {
    throw new Error(`Wallpaper Engine 创意工坊目录不存在: ${WORKSHOP_DIR}`);
  }

  const entries = fs.readdirSync(WORKSHOP_DIR, { withFileTypes: true });
  const items = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const folderId = entry.name;
    const folderPath = path.join(WORKSHOP_DIR, folderId);

    const projectJsonPath = path.join(folderPath, 'project.json');
    let title = folderId;
    let type = 'unknown';
    let videoFile = null;
    let previewFile = null;
    let directAudioFile = null;
    let tags = [];

    if (fs.existsSync(projectJsonPath)) {
      const raw = fs.readFileSync(projectJsonPath, 'utf-8');
      const data = safeParseJson(raw);
      if (data) {
        title = data.title || folderId;
        type = (data.type || 'unknown').toLowerCase();
        tags = data.tags || [];
      }
    }

    // 扫描文件夹中的原生 mp4 视频文件与直接音频文件
    const files = fs.readdirSync(folderPath);
    for (const f of files) {
      const lower = f.toLowerCase();
      if (lower.endsWith('.mp4') && !videoFile && f !== 'extracted_fullscreen.mp4') {
        const fullVideoPath = path.join(folderPath, f);
        const stat = fs.statSync(fullVideoPath);
        videoFile = {
          fileName: f,
          fullPath: fullVideoPath,
          sizeBytes: stat.size,
          sizeMb: (stat.size / (1024 * 1024)).toFixed(1)
        };
      }
      if ((lower === 'preview.jpg' || lower === 'preview.png' || lower === 'preview.gif') && !previewFile) {
        previewFile = f;
      }
      if (/\.(mp3|flac|ogg|wav)$/i.test(f) && !directAudioFile && !f.startsWith('extracted_')) {
        directAudioFile = path.join(folderPath, f);
      }
    }

    if (!previewFile) {
      const anyImg = files.find(f => /\.(jpg|jpeg|png|webp)$/i.test(f));
      if (anyImg) previewFile = anyImg;
    }

    // 针对 Scene 壁纸，从 scene.pkg 中多模态逆向解包 (原画 + 内嵌视频 + 原声音频)
    const { extractedVideo, extractedImage, extractedAudio, resolutionBadge: extractedBadge } = extractScenePkgMedia(folderPath, folderId);

    // 若从 PKG 提取出了原生 MP4 且原本无视频文件，自动升级为动态视频壁纸
    if (extractedVideo && !videoFile) {
      const stat = fs.statSync(extractedVideo);
      videoFile = {
        fileName: 'extracted_fullscreen.mp4',
        fullPath: extractedVideo,
        sizeBytes: stat.size,
        sizeMb: (stat.size / (1024 * 1024)).toFixed(1)
      };
    }

    // 缩略图保留原始 preview，以保持抽屉卡片渲染轻量敏捷
    let finalPreviewUrl = previewFile ? `file:///${path.join(folderPath, previewFile).replace(/\\/g, '/')}` : '';
    // 全屏展示时强制优先使用解包提取的 1080P/2K/4K/7K 宽屏无损原画，严禁使用 1:1 正方形微型 preview.gif
    let fullscreenUrl = extractedImage ? `file:///${extractedImage.replace(/\\/g, '/')}` : '';
    if (!fullscreenUrl && previewFile && !previewFile.toLowerCase().endsWith('.gif')) {
      fullscreenUrl = finalPreviewUrl;
    }

    const videoUrl = videoFile ? `file:///${videoFile.fullPath.replace(/\\/g, '/')}` : '';

    // 音频资产解析：原生视频自带音轨，或独立提取的原声音频
    const activeAudioPath = extractedAudio || directAudioFile;
    const hasAudio = !!videoFile || !!activeAudioPath;
    const audioUrl = activeAudioPath ? `file:///${activeAudioPath.replace(/\\/g, '/')}` : (videoFile ? videoUrl : '');

    let category = 'scene';
    let resolutionBadge = extractedBadge || '超清场景';

    if (videoFile) {
      category = 'video';
      resolutionBadge = videoFile.sizeBytes > 25 * 1024 * 1024 ? '4K 原生动态' : '1080P 动态视频';
    } else if (previewFile && previewFile.endsWith('.gif')) {
      resolutionBadge = '动态封面';
    }

    items.push({
      id: folderId,
      title: title.trim(),
      type,
      category,
      resolutionBadge,
      hasVideo: !!videoFile,
      hasAudio,
      hasExtractedTexture: !!(extractedImage || extractedVideo),
      videoSizeMb: videoFile ? videoFile.sizeMb : null,
      previewUrl: finalPreviewUrl,
      fullscreenUrl,
      videoUrl,
      audioUrl,
      folderPath
    });
  }

  // 排序：真正的高清视频排在最前，其次按标题中文排序
  items.sort((a, b) => {
    if (a.hasVideo && !b.hasVideo) return -1;
    if (!a.hasVideo && b.hasVideo) return 1;
    return a.title.localeCompare(b.title, 'zh-CN');
  });

  const manifest = {
    scanTime: new Date().toISOString(),
    totalCount: items.length,
    videoCount: items.filter(i => i.hasVideo).length,
    audioCount: items.filter(i => i.hasAudio).length,
    sceneCount: items.filter(i => !i.hasVideo).length,
    workshopPath: WORKSHOP_DIR,
    items
  };

  const outputDir = path.dirname(OUTPUT_FILE);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(manifest, null, 2), 'utf-8');

  // 同步生成 JS 格式，彻底规避 Chromium file:// 协议下的 fetch CORS 限制
  const jsOutputFile = path.resolve(outputDir, 'wallpapers_manifest.js');
  fs.writeFileSync(jsOutputFile, `window.WALLPAPERS_MANIFEST = ${JSON.stringify(manifest, null, 2)};`, 'utf-8');

  console.log(`[Scanner] 扫描完成! 共收录 ${items.length} 个壁纸项目 (其中原生 4K/1080P 视频: ${manifest.videoCount} 个, 带原声音频壁纸: ${manifest.audioCount} 个)`);
  console.log(`[Scanner] 清单已输出至: ${OUTPUT_FILE} 与 ${jsOutputFile}`);
  return manifest;
}

if (require.main === module) {
  scanAllWallpapers();
}

module.exports = { scanAllWallpapers };
