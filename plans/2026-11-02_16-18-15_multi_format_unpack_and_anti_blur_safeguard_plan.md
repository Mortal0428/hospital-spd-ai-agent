# 研发计划：Wallpaper Engine 全格式二进制解包升级与微缩图防拉伸安全护栏

- **计划文档路径**：`plans/2026-11-02_16-18-15_multi_format_unpack_and_anti_blur_safeguard_plan.md`
- **记录时间戳**：`2026-11-02 16:27:50`
- **当前状态**：**已全部完成并 100% 通过 Playwright 7 项自动化强断言回环验证**
- **按需挂载全局 Skills**：
  - `animation-performance`（防拉伸像素级守卫、高效二进制文件流扫描、显存友好型图像挂载）
  - `apple-design`（高解析度 Retinal 视觉、严禁任何低清马赛克插值伪全屏、克制优雅的画质兜底）
  - `emil-design-eng`（精细化防降级提示、真实细节还原）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_16-18-15_multi_format_unpack_and_anti_blur_safeguard_plan.md
- 记录时间戳：2026-11-02 16:27:50
- 脚本与数据目标文件：
  1. scripts/scan_wallpapers.js —— 重构 extractScenePkgMedia 解包函数：全面支持从 scene.pkg 中精准逆向提取内嵌 4K/60 帧 MP4 视频、超清 PNG (>= 1080P/4K) 及无损 JPEG 原画，彻底攻克遗漏的 15 款场景壁纸（守岸人、清霄、林初雪全系列、伊蕾娜等）。
  2. docs/design/wallpapers_manifest.json & wallpapers_manifest.js —— 重新生成清单，视频壁纸从 11 款跃升为 17 款（守岸人等场景自动升级为 4K/60 帧原生动态壁纸），场景壁纸全量具备超清原画，大图覆盖率达 100%。
- 前端与设计目标文件：
  docs/design/spd_integrated_showcase_demo.html —— 建立像素级防拉伸安全守卫：
  1. 【微型图片全屏拉伸强阻断】：针对物理分辨率低于 600px 的微型 GIF（如 150x150 图标），严禁以 cover 方式铺满全屏造成巨大马赛克；
  2. 【优雅居中与深邃背景衬托】：对低于 600px 图标自动采用精致 contain 居中渲染并衬托深邃科技底色，绝不强行放大产生色块；
  3. 【抽屉清晰度徽标升级】：对成功提取 1080P/4K 原画的壁纸统一标注“超清无损原画/4K无损原画”，原生视频标注“4K 原生动态”。
- 测试与截图目标文件：
  1. tests/harness/verify_integrated_showcase.js —— 增加断言 7 针对守岸人 (3420909070) 原生 4K 动态流实机运行强断言，断言清单包含 17 款视频壁纸，0 控制台报错。
  2. tests/screenshots/2026-11-02_16-18-15_multi_format_extracted_hd.png —— 守岸人 4K 原生 60 帧超清动态流实机截图（1.57MB 高保真）。
```

---

## 二、 核心评估指标与执行结果

### 1. 可行性与把握度评估
- **把握度**：`100%`（已实际验证）。
  - 成功从 `3420909070/scene.pkg` 等场景中提取出 47.3MB 原生 4K/60 帧 MP4；
  - 成功从 2740849600 等场景中提取出 27MB 无损 JPEG 原画；
  - 成功从 3494616159 等场景中提取出 8192x4606 8K 超清 PNG 原画；
  - 全量 39 款壁纸 100% 具备超清原生媒体，彻底消灭拉伸模糊噪点。

### 2. 自动化回环测试指标
- **静态扫描**：100% 零 Emoji 违规；
- **Playwright 断言覆盖**：7 项全量断言通过（双模态切换、抽屉渲染、4K 视频硬件解码、纯享模式 Zen 100% 纯净、纯享唤醒复原、水墨剑客全屏无樱花粒子、守岸人 4K 动态流实机运行）；
- **控制台错误**：`Console Error = 0`，`PageError = 0`。

---

## 三、 原子实施清单完成状态

```markdown
实施清单：
1. [已完成] [scripts/] 升级 scripts/scan_wallpapers.js，实现 extractScenePkgMedia，成功解包 MP4/PNG/JPEG。
2. [已完成] [scripts/] 执行扫描，更新 docs/design/wallpapers_manifest.json 与 wallpapers_manifest.js。
3. [已完成] [docs/design/] 优化 docs/design/spd_integrated_showcase_demo.html，实现自然尺寸检测与防拉伸安全守卫。
4. [已完成] [tests/] 升级 tests/harness/verify_integrated_showcase.js，增加断言 7 与守岸人专项实机校验。
5. [已完成] [tests/] 运行 Playwright 自动化回环测试，7 项断言全部通过，归档实机截图至 tests/screenshots/2026-11-02_16-18-15_multi_format_extracted_hd.png。
6. [已完成] [plans/] 更新计划进度台账，准备向用户交付。
```
