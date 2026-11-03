全面重构前端页面与交互体验，将其构建为高质感的医疗物资数字化展厅（Showcase），彻底推翻与原型风格偏离的现有视图，严格对齐 docs/design/spd_integrated_showcase_demo.html 的现代医疗视觉质感、设计系统 Tokens 与模态登录交互体系。

Working directory: frontend
Integrity mode: development

参考原型文件：docs/design/spd_integrated_showcase_demo.html

## Requirements

### R1. 全局设计系统与视觉规范对齐
严格对齐 docs/design/spd_integrated_showcase_demo.html 中的设计规范与 CSS 变量体系（包含深色/浅色自适应主题、毛玻璃背景卡片、微边框、分层投影与流光过渡）。全域严禁使用任何 Emoji 表情字符，所有图标统一采用符合 Apple HIG 与现代化医疗风格的纯矢量内联 SVG 或原生矢量组件图标，所有新增及修改的函数必须配备规范的标准化中文注释。

### R2. 现代医疗安全模态登录中枢重构
全面推翻原有简易登录界面，严格依照 demo 中的“医慧通行 · 现代医疗模态登录中枢”（Healthcare Modal Auth Card）交互架构进行重写：包含 4 大演示角色一键免密接入通道（耗材科管理、设备科管理、临床二级库、财务合规审计）、标准工号与密码输入验证、密码明暗文切换、会话记住状态以及医疗品牌头部标识。

### R3. 业务视图页面结构与逻辑彻底重构
全面推翻 frontend/src/views/ 下与 demo 质感割裂的现有页面（包括但不限于产品字典、普通耗材主库、高值专仓管理、临床二级库、采购协同、全流程日志流向及财务核算打印等），依照 demo 原型页面结构彻底重写视图结构与展示逻辑，并按需重新串联与适配后端真实业务接口及 Pinia 状态，确保在 Vue 3 + TypeScript 架构下业务数据流通畅、界面视觉高度统一。

## Acceptance Criteria

### UI 质感与交互对齐
- [ ] 全域代码与界面中文本、图标、按钮无任何 Emoji 表情符号，所有图标均为矢量 SVG
- [ ] 登录模块完全复刻 demo 的模态卡片样式，4 大角色一键免密通道及工号密码登录均能正常触发身份认证与视图跳转
- [ ] 页面在深色模式与浅色模式之间平滑自适应，背景调光、毛玻璃卡片、边框及文字层级对比均与 demo 保持视觉一致
- [ ] 重构后的各业务视图结构与排版与原型展示规范一致，消除生硬的默认表单与割裂风格

### 编译构建与自动化回环测试
- [ ] 前端 TypeScript 严格类型检查与 Vite 生产构建打包（npm run build）0 错误、0 警告顺利通过
- [ ] Playwright 无头浏览器自动化回环测试通过：页面控制台无任何未捕获异常（无 Console Error / PageError），关键 DOM 节点正常可见，登录模态弹窗与核心页面交互链路顺畅
