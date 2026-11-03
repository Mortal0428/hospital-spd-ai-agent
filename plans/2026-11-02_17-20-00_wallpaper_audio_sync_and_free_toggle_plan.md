# 研发计划：Wallpaper Engine 动态壁纸音频全模态同步与自由音乐控制系统

- **计划文档路径**：`plans/2026-11-02_17-20-00_wallpaper_audio_sync_and_free_toggle_plan.md`
- **记录时间戳**：`2026-11-02 17:20:00`
- **当前所处阶段**：工坊音频逆向解包与视频音轨解锁、双模式音频互斥调度引擎、全域自由音乐开关与持久化
- **按需挂载全局 Skills**：
  - `animation-performance`（防杂音防爆音、音轨切换淡入淡出、浏览器自动播放策略安全适配）
  - `apple-design`（拟态科技音量声波胶囊、微交互滑块、全域禁用 Emoji、Retina 级精简内联矢量 SVG）
  - `emil-design-eng`（快捷键 M 随心静音、纯享全屏控制微条、无缝跨会话持久化）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_17-20-00_wallpaper_audio_sync_and_free_toggle_plan.md
- 记录时间戳：2026-11-02 17:20:00
- 脚本与数据目标文件：
  1. scripts/scan_wallpapers.js ——
     - 升级 extractScenePkgMedia 函数：在逆向解包 scene.pkg 时，全面扫描并提取内嵌的原生音频流（.mp3 / .flac / .ogg / .wav），导出为 extracted_audio.[ext]；
     - 完善清单元数据：对 17 款 MP4 视频标注 hasAudio: true，对 6 款具备提取音频的场景壁纸标注 hasAudio: true 与 audioUrl，输出全新的 wallpapers_manifest.json 与 wallpapers_manifest.js。
- 前端目标文件：
  docs/design/spd_integrated_showcase_demo.html ——
  1. 【音频播放引擎与双流互斥调度】：
     - 部署 <audio id="wallpaper-audio" loop playsinline> 独立场景音频层，与 <video id="wallpaper-video"> 组成双模音频调度引擎；
     - 切歌互斥保护：切换壁纸时自动停止旧音轨，若为视频则解锁视频音轨，若为场景壁纸则加载对应 extracted_audio，杜绝多音轨混响重叠；
  2. 【全域自由音乐开关与音量胶囊】：
     - 在顶部浮动导航栏右侧装配高质感音量控制胶囊 (#nav-audio-control)：
       - 内置一键静音/播放按钮 (#btn-toggle-audio)，使用精简语义化 SVG 绘制动态声波微条与静音斜杠图标，100% 杜绝 Emoji；
       - 悬浮展开微型音量滑块 (#audio-volume-slider)，支持 0% - 100% 平滑调节；
       - 键盘快捷键：支持随时按键盘 M 键瞬间静音/恢复音乐；
  3. 【一键纯享模式 (Zen Mode) 音频联动】：
     - 在纯享退出微胶囊旁增设纯享音乐微开关 (#btn-zen-toggle-audio)，支持在 100% 全屏无遮挡沉浸壁纸下自由掌控背景乐；
  4. 【LocalStorage 音频偏好持久化】：
     - 记录用户音频偏好 ('spd_audio_enabled') 与音量大小 ('spd_audio_volume')，跨刷新、跨会话长久记忆。
- 测试与截图目标文件：
  1. tests/harness/verify_integrated_showcase.js ——
     - 增加断言 12：音频全量解包与清单校验（断言 23 款壁纸具备原生/提取音轨，audioUrl 路径有效）；
     - 增加断言 13：前端音乐开关激活、音量调节、快捷键 M 响应与纯享微条联动实机测试；
  2. tests/screenshots/2026-11-02_17-20-00_audio_toggle_active.png —— 前台展厅音乐开启与声波微胶囊实机截图；
  3. tests/screenshots/2026-11-02_17-20-00_zen_audio_control.png —— 纯享模式下音乐开关联动实机截图。
```

---

## 二、 核心评估指标

### 1. 可行性与把握度评估
- **把握度：100%**。
  - **解包可行性已实机测试验证**：已成功从 `3420909070`、`3393455874`、`2869409186` 等 scene.pkg 中精准提取出完整无损的原声音乐，文件格式完全符合标准 HTML5 `<audio>` 规范；
  - **浏览器自动播放策略安全兼容**：默认按推荐选项处于静音状态，用户点击界面任意交互控件或音乐开关后平滑解除静音，完全符合 W3C Autoplay 规范，零控制台报错。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：视听全方位沉浸，动态壁纸原声 BGM 自由启闭，声波微动效赋予科技生命力，随时按 M 键静音；
- **开发者体验（DX）**：统一的音量调度状态机，无冗余定时器，内存安全销毁；
- **存量功能保护**：原有 4K 满屏 Cover、3D 弧面 60FPS 流光、双模态切换和 LocalStorage 持久化全部 100% 保持稳定。

---

## 三、 技术与 UI 细节规范

1. **音频状态机数据契约**：
   ```javascript
   const STORAGE_KEY_AUDIO_ENABLED = "spd_audio_enabled";
   const STORAGE_KEY_AUDIO_VOLUME = "spd_audio_volume";
   let isAudioEnabled = false; // 默认静音，用户开启后持久化记忆
   let currentVolume = 0.65;   // 默认舒适听觉音量 65%
   ```
2. **纯矢量内联 SVG 图标规范（全域严禁 Emoji）**：
   - 音频开启：`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">...音量喇叭+双弧形声波...</svg>`
   - 音频静音：`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">...音量喇叭+对角斜线横切杠...</svg>`
3. **音轨互斥切换逻辑**：
   - 当切换到视频壁纸：`wallpaperAudio.pause(); wallpaperAudio.src = ""; wallpaperVideo.muted = !isAudioEnabled; wallpaperVideo.volume = currentVolume;`
   - 当切换到带音频场景壁纸：`wallpaperVideo.muted = true; wallpaperAudio.src = item.audioUrl; if (isAudioEnabled) wallpaperAudio.play(); wallpaperAudio.volume = currentVolume;`
   - 当切换到无音频壁纸：两者均暂停或静音。

---

## 四、 强制性原子实施清单

```markdown
实施清单：
1. [已完成] [scripts/] 升级 scripts/scan_wallpapers.js：
   - 在 extractScenePkgMedia 中加入从 scene.pkg 提取 .mp3/.flac/.ogg 音频流至 extracted_audio.[ext] 逻辑；
   - 在 scanAllWallpapers 中标记 hasAudio 与 audioUrl；
   - 重新运行脚本生成全量音频清单 wallpapers_manifest.json 与 wallpapers_manifest.js。
2. [已完成] [docs/design/] 优化 docs/design/spd_integrated_showcase_demo.html：
   - 部署 <audio id="wallpaper-audio"> 播放容器；
   - 在顶部导航栏与纯享微条中装配音量开关胶囊 (#btn-toggle-audio 与 #btn-zen-toggle-audio) 及音量滑块；
   - 实现双模音频互斥调度引擎、快捷键 M 监听与 LocalStorage 音频偏好持久化。
3. [已完成] [tests/] 升级 tests/harness/verify_integrated_showcase.js 自动化测试脚本：
   - 增加断言 12：校验全量工坊壁纸音频提取结果与清单字段；
   - 增加断言 13：校验音乐开启播放、音轨互斥切换、快捷键 M 静音与纯享微条联动；
   - 捕获对应实机截图并归档至 tests/screenshots/。
4. [已完成] [tests/ | plans/] 启动 Playwright 执行 13 项全量强断言自动化回环测试，校验全部通过。
5. [已完成] [plans/] 更新计划进度台账，向用户交付实机截图与验证结果。
```

---

## 五、 执行与回环验收结果

- **验收时间戳**: `2026-11-02 17:34:00`
- **自动化测试结果**: 13 项强断言 100% 全部通过，0 错误，0 Emoji 违规。
- **实机截图归档**:
  1. `tests/screenshots/2026-11-02_17-20-00_audio_toggle_active.png`
  2. `tests/screenshots/2026-11-02_17-20-00_zen_audio_control.png`
- **当前状态**: 已圆满完成交付。
