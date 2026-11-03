# 研发计划：Wallpaper Engine 本地工坊全量真 4K 自由选择与彻底杜绝模糊解决方案

- **计划文档路径**：`plans/2026-11-02_15-06-00_wallpaper_high_res_and_free_picker_plan.md`
- **记录时间戳**：`2026-11-02 15:06:00`
- **当前所处阶段**：展厅背景引擎升级（彻底根除模糊马赛克、全量 39 套创意工坊扫描、自由文件/文件夹选择与拖拽映入）
- **按需挂载全局 Skills**：
  - `emil-design-eng`（抽屉画廊滚动微动效、卡片分类徽标、拖拽全屏浮层指示、智能毛玻璃调光）
  - `apple-design`（原生 macOS / iPadOS 风格文件选择器、高对比清晰度守卫、去 AI 廉价感）
  - `animate` 与 `animation-performance`（视频硬件解码无卡顿、GPU 合成层保持 60fps）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_15-06-00_wallpaper_high_res_and_free_picker_plan.md
- 记录时间戳：2026-11-02 15:06:00
- 扫描工具脚本：
  scripts/scan_wallpapers.js —— 本地自动化扫描脚本，遍历 E:\SteamLibrary\steamapps\workshop\content\431960 下全部 39 个文件夹，解析 project.json，提取原生 1080P/4K MP4 视频路径与真实中文标题，过滤掉仅有 150px 缩略图的低清项目，输出 docs/design/wallpapers_manifest.json
- 前端目标文件：
  docs/design/spd_integrated_showcase_demo.html —— 升级壁纸引擎与画廊抽屉：
  1. 【彻底根除模糊】：优先选用 1080P/4K 原生动态视频流与 >=1024px 高清原画；
  2. 【全量工坊动态渲染】：动态读取 wallpapers_manifest.json，在抽屉中分类展示用户本地的真实 4K 视频与高清原画列表；
  3. 【自由文件/文件夹选择器】：在抽屉顶部新增“自由选择本地壁纸”按钮（支持选择电脑上任意图片或 MP4 视频）；
  4. 【全局拖拽映入支持 (Drag & Drop)】：支持将电脑中任意 MP4 视频或高清图片直接拖拽进浏览器窗口，自动设为全屏背景；
  5. 【纯享模式自适应】：纯享模式下根据当前壁纸类型自动全屏高清呈现。
- 测试与截图文件：
  1. tests/harness/verify_integrated_showcase.js —— 更新 Playwright 自动化回环测试，校验 4K 视频壁纸切换、本地文件拖拽与纯享模式无马赛克断言
  2. tests/screenshots/2026-11-02_15-06-00_integrated_showcase_4k_video_mode.png —— 4K 原生动态视频壁纸实机验证截图
  3. tests/screenshots/2026-11-02_15-06-00_integrated_showcase_free_picker_drawer.png —— 全量工坊抽屉与自由选择器实机截图
```

---

## 二、 核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`99%`
- **潜在技术风险与预案**：
  - **风险点 1（为什么之前模糊）**：先前展示的 `3025961040\preview.gif`（254x254）与 `3420909070\preview.gif`（150x150）是 Steam 商店微缩略图，拉伸全屏必然马赛克。**应对策略**：自动扫描脚本识别 `type === "video"` 的项目，提取其真正原生 4K/1080P 的 `.mp4` 文件（如丽芙极昼 3840x2160 4K60F、雷电将军 1080P、守岸人 1080P 等），用 `<video>` 原生硬件加速播放，清晰度达到像素级原生无损；
  - **风险点 2（跨浏览器文件读取安全限制）**：浏览器禁止网页 JS 随意访问本地未授权绝对路径。**应对策略**：
    - ① 提供预先索引好的本地 `wallpapers_manifest.json`（配合 `file:///` 协议无缝播放）；
    - ② 提供标准 HTML5 `<input type="file" accept="video/mp4,image/*">`，用户选取的任何文件均转为 `URL.createObjectURL(file)` 瞬间加载；
    - ③ 提供全屏 `dragover` / `drop` 事件监听，将用户拖入的任意文件瞬间设为全屏背景。

### 2. 存量功能与三方体验影响分析
- **用户体验（UX）**：彻底解决马赛克问题，让用户的 4K 动态壁纸以原生画质在大屏上流淌，配合“纯享模式”带来令人震撼的视觉享受；
- **开发者体验（DX）**：扫描脚本独立运行，代码解耦分明，前端壁纸引擎模块化封装；
- **AI 代理体验（AX）**：自动化测试可通过 Playwright 触发文件拖拽与壁纸选择，断言视频标签的 `readyState >= 2` 与分辨率属性；
- **存量功能零破坏**：后端数据库与工作台业务逻辑 100% 保持只读隔离。

### 3. Playwright 自动化回环测试方案
- 验证 `docs/design/wallpapers_manifest.json` 包含的工坊项目真实有效；
- 验证在展厅中切换至原生 4K 视频壁纸（如雷电将军或丽芙极昼），断言 `<video>` 元素成功激活并加载流媒体；
- 验证抽屉内“自由选择文件”按钮存在，拖拽提示遮罩渲染正常；
- 验证纯享模式下画面无马赛克，截取实机全景验证图。

---

## 三、 强制性原子实施清单

```markdown
实施清单（全部完成）：
1. [已完成] [scripts/] 创建 scripts/scan_wallpapers.js，扫描 E:\SteamLibrary\steamapps\workshop\content\431960 下全部 39 个文件夹，提取真实标题、分类（4K视频/高清原画）及物理文件路径，输出 docs/design/wallpapers_manifest.json 与 wallpapers_manifest.js。
2. [已完成] [docs/design/] 运行 node scripts/scan_wallpapers.js 生成全量壁纸清单。
3. [已完成] [docs/design/] 升级 docs/design/spd_integrated_showcase_demo.html：
   - 抽屉内动态渲染全量 39 款真实壁纸清单，带 4K 视频 / 原画徽标与分类过滤 Tab；
   - 增加原生本地文件选择按钮（<input type="file">）与全屏拖拽映入（Drag & Drop）支持；
   - 确保视频壁纸与高清原画加载无模糊、无拉伸变形。
4. [已完成] [tests/] 更新 tests/harness/verify_integrated_showcase.js，配置 Playwright 自动化验证脚本。
5. [已完成] [tests/ | plans/] 运行 node tests/harness/verify_integrated_showcase.js，截取 4K 视频模式与自由选择器实机图归档至 tests/screenshots/。
6. [已完成] [plans/] 更新 master 计划台账，向用户输出完整的交付与操作报告。
```
