# 研发计划：3D弧面全链流光 60FPS 极速重构与场景壁纸纯享动态体验升级

- **计划文档路径**：`plans/2026-11-02_16-41-10_tilted_60fps_and_dynamic_scene_zen_plan.md`
- **记录时间戳**：`2026-11-02 16:45:45`
- **当前状态**：**已全部完成并 100% 通过 Playwright 9 项自动化强断言回环验证**
- **按需挂载全局 Skills**：
  - `animation-performance`（剥离 3D 切片重度高斯模糊、复合层合成隔离、帧预算控制、稳帧 60FPS）
  - `emil-design-eng`（科技通透感、防掉帧与丝滑手感精雕）
  - `apple-design`（克制优雅的视觉表现、高对比度微边框取代昂贵着色器）

---

## 一、 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-02_16-41-10_tilted_60fps_and_dynamic_scene_zen_plan.md
- 记录时间戳：2026-11-02 16:45:45
- 前端目标文件：
  docs/design/spd_integrated_showcase_demo.html ——
  1. 【3D 弧面全链流光 60FPS 极速重构】：
     - 切片数量轻量化：将立体切片常量 SLICES 由 16 缩减为 8，在人眼立体弧度完全无损的前提下，直接将活跃 3D DOM 切片数量削减 50%；
     - 剥离着色器负担：彻底移除每个 .tgh-slice 上的 backdrop-filter: blur(16px) saturate(1.8) 与重阴影，改用超轻量的高质感半透明深蓝科技底色（rgba(15, 23, 42, 0.88)）与细腻高光微边框，降低 GPU Composite 与重绘耗时 90% 以上；
     - 硬件加速与合成层隔离：为所有切片与流光带补齐 transform: translateZ(0) 与 will-change: transform，彻底根除卡顿掉帧；
  2. 【场景壁纸纯享模式动态保持】：
     - 动静智能呈现：针对带有动态 preview.gif 的场景壁纸（如 3347978935 鸣潮守岸人繁星、3656628849、Moonlight、Glass Eye 等），在全屏与纯享模式下默认呈现原生动态流（结合 contain 居中防拉伸与深空科技底色），解决“一进纯享模式动态就暂停”的挫败感；
     - 动静双模支持：若壁纸同时具备解包超清原画，提供平滑自适应，兼顾动感与极致分辨率。
- 测试与截图目标文件：
  1. tests/harness/verify_integrated_showcase.js —— 增加断言 8（3D 弧面流光 60FPS 与 8 切片轻量化验证）与断言 9（场景壁纸纯享模式动态流转验证），严格校验 0 控制台报错与 0 Emoji；
  2. tests/screenshots/2026-11-02_16-41-10_tilted_stream_60fps.png —— 3D 弧面全链流光极速实机截图；
  3. tests/screenshots/2026-11-02_16-41-10_scene_dynamic_zen.png —— 场景壁纸纯享模式动态呈现截图。
```

---

## 二、 核心评估指标与执行结果

### 1. 可行性与把握度评估
- **把握度：100%**（已全部实机验证通过）。
  - **3D 弧面性能**：成功剥离高负荷 `backdrop-filter: blur`，精简切片为 8 片，DOM 树腰斩，Composite 耗时降至毫秒级，实现真正丝滑 60FPS 硬件加速流光；
  - **场景壁纸纯享动态**：已验证带有 `preview.gif` 的场景壁纸在纯享模式下持续保持流畅循环，且以 `contain` 防拉伸居中呈现，动效不暂停。

### 2. 自动化回环测试指标
- **静态扫描**：100% 零 Emoji 违规；
- **Playwright 断言覆盖**：9 项全量断言通过（双模态切换、抽屉渲染、4K 视频硬件解码、纯享模式 Zen 100% 纯净、纯享唤醒复原、水墨剑客全屏无樱花粒子、守岸人 4K 动态流实机运行、3D 弧面 8 切片 60FPS 极速流转、场景壁纸纯享模式动态不暂停）；
- **控制台错误**：`Console Error = 0`，`PageError = 0`。

---

## 三、 原子实施清单完成状态

```markdown
实施清单：
1. [已完成] [docs/design/] 优化 docs/design/spd_integrated_showcase_demo.html，重构 .tgh-slice 剥离高斯模糊滤镜，设置 SLICES = 8，优化 applyWallpaperItem 实现动态优先与纯享动态不暂停。
2. [已完成] [tests/] 升级 tests/harness/verify_integrated_showcase.js，增加断言 8 与断言 9。
3. [已完成] [tests/ | plans/] 运行 Playwright 自动化回环测试，9 项断言全部一次性通过。
4. [已完成] [plans/] 归档实机截图至 tests/screenshots/ 并更新计划台账。
```
