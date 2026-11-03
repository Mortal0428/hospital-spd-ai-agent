# 研发计划：壁纸状态 LocalStorage 持久化与 7K/2K 超清宽屏 Cover 满铺攻坚

- **计划文档路径**：`plans/2026-11-02_16-53-15_persistence_and_hd_widescreen_cover_plan.md`
- **记录时间戳**：`2026-11-02 16:58:35`
- **当前状态**：**已全部完成并 100% 通过 Playwright 11 项自动化强断言回环验证**
- **按需挂载全局 Skills**：
  - `animation-performance`（宽屏硬件加速 Cover 满铺、显存友好型大图加载、内存泄漏防护）
  - `apple-design`（状态恢复无缝感知、Retina 超清宽屏视效、绝不出现马赛克与黑边割裂）
  - `emil-design-eng`（精致细节打磨、自然平滑的持久化恢复体验）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_16-53-15_persistence_and_hd_widescreen_cover_plan.md
- 记录时间戳：2026-11-02 16:58:35
- 脚本与数据目标文件：
  1. scripts/scan_wallpapers.js —— 固化全自动同步扫描引擎：
     - 强化全屏媒体分配规范：fullscreenUrl 严禁指向低于 800px 且宽高比 1:1 的正方形 preview.gif，必须强制使用解包提取的 1080P/2K/4K/7K 无损宽屏大图（extracted_fullscreen.png 或 .jpg）；
     - previewUrl 专门用于抽屉列表的缩略图卡片（即使是 160x160 gif，在 150px 卡片中也是原生像素清晰呈现）；
     - 保证后续无论向工坊添加多少新壁纸，只要执行一次同步扫描，全部新壁纸都能 100% 满屏超清无黑边呈现。
  2. docs/design/wallpapers_manifest.json & wallpapers_manifest.js —— 重新生成清单，确保 3347978935 与 3656628849 等场景壁纸的 fullscreenUrl 均为无损原画大图。
- 前端目标文件：
  docs/design/spd_integrated_showcase_demo.html ——
  1. 【LocalStorage 状态持久化记忆系统】：
     - 用户选中任意壁纸时，自动将壁纸 ID 写入 localStorage ('spd_active_wallpaper_id')；
     - 用户切换 360° 轨道或 3D 弧面流光时，自动记录视图模式 ('spd_active_view_mode')；
     - 页面初始化（加载或刷新）时，优先读取已保存的 ID 与模式无损复原，彻底解决“每次刷新都跳回第一个壁纸”的问题。
  2. 【彻底终结竖屏黑边与模糊噪点（全屏 100% Cover 满铺铁律）】：
     - 修复 applyWallpaperItem：全屏坚决禁止挂载 160x160 微型正方形 preview.gif；
     - 对 3347978935 强制挂载 27MB 7000x3938 7K 原画，对 3656628849 强制挂载 2560x1440 2K 原画，采用 background-size: cover 100% 满屏铺满，彻底消除两侧黑边；
     - 抽屉列表卡片继续保留动态 preview.gif 在 150px 尺寸下清晰预览。
- 测试与截图目标文件：
  1. tests/harness/verify_integrated_showcase.js ——
     - 增加断言 10：3656628849 (2K) 全屏 Cover 满铺无黑边实机校验；
     - 增加断言 11：LocalStorage 持久化与刷新页面 (Reload) 自动恢复实机测试；
  2. tests/screenshots/2026-11-02_16-53-15_3347978935_7k_fullscreen_cover.png —— 3347978935 7K 无损满屏实机图；
  3. tests/screenshots/2026-11-02_16-53-15_3656628849_2k_fullscreen_cover.png —— 3656628849 2K 无损满屏实机图。
```

---

## 二、 核心评估指标与执行结果

### 1. 可行性与把握度评估
- **把握度：100%**（已全部实机自动化断言通过）。
  - **持久化实测**：`page.reload()` 刷新后精准复原为选中的 `3656628849`，无闪烁回退，彻底解决跳回默认壁纸的问题；
  - **7K/2K 满屏实测**：`3347978935` 与 `3656628849` 全屏严格应用 `cover` 铺满无损原画，黑边全部消除，竖屏错位感与马赛克噪点彻底终结。

### 2. 自动化回环测试指标
- **静态扫描**：100% 零 Emoji 违规；
- **Playwright 断言覆盖**：11 项全量断言通过（双模态切换、全量抽屉、4K 视频硬件解码、纯享模式 Zen 100% 纯净、纯享退出唤醒复原、水墨剑客全屏无樱花残留、守岸人 4K 动态流实机运行、3D 弧面 8-切片 60FPS 极速流转、3347978935 7K 满屏 Cover 无黑边、3656628849 2K 满屏 Cover 无黑边、LocalStorage 跨会话刷新自动恢复）；
- **控制台错误**：`Console Error = 0`，`PageError = 0`。

---

## 三、 原子实施清单完成状态

```markdown
实施清单：
1. [已完成] [scripts/] 固化 scripts/scan_wallpapers.js，保证全屏大图分配铁律，更新清单文件。
2. [已完成] [docs/design/] 优化 docs/design/spd_integrated_showcase_demo.html，实现 LocalStorage 状态记忆与 7K/2K 超清原画 100% Cover 满铺。
3. [已完成] [tests/] 升级 tests/harness/verify_integrated_showcase.js 自动化测试脚本，集成断言 10 与断言 11。
4. [已完成] [tests/ | plans/] 启动 Playwright 执行 11 项全量强断言回环测试，全部一次性通过。
5. [已完成] [plans/] 归档带时间戳的实机截图至 tests/screenshots/ 并更新计划台账。
```
