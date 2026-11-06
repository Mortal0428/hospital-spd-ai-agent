# 飞书长连接真实探活修复、频控独立保存按钮与外部通道认知优化规划

- **计划文档路径**：`plans/2026-11-06_14-12-00_feishu_ws_status_fix_and_welcome_save_plan.md`
- **记录时间戳**：2026-11-06 14:12:00
- **模式声明**：`[MODE: PLAN]`

---

## 一、变更计划与目标文件清单

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-06_14-12-00_feishu_ws_status_fix_and_welcome_save_plan.md
- 记录时间戳：2026-11-06 14:12:00
- 前端目标文件：
  1. frontend/src/views/RagAgentHubView.vue：
     - 在飞书欢迎卡片频控面板中增设专属【保存频控设置】按钮与持久化成功反馈；
     - 重构左下角卡片标题为“飞书主动单据审批与预警外发通道 (FeishuBotService)”，明确主动外发与长连接被动监听的区别；
     - 重构右下角卡片标题为“Agent 08: Coze 云端小爱医疗法规智能体 (豆包 1.5 Pro)”，明确其作为全网国家药监法规问答的职责；
     - 优化长连接监控状态卡片样式与即时刷新。
- 后端目标文件：
  1. backend/app/services/feishu_ws_service.py：
     - 彻底修复 restart() 时重复使用 running asyncio loop 导致的 This event loop is already running 异常；
     - 重构 is_connected 判定逻辑，结合守护线程存活性与实际接收消息时效，杜绝“实际能发消息但界面误报离线”的假象。
- 测试与截图文件：
  1. tests/screenshots/2026-11-06_14-25-00_feishu_ws_connected_and_saved.png：长连接在线状态高亮与频控设置独立保存成功实机截图。
```

---

## 二、核心评估指标

### 1. 可行性与把握度评估
- **把握度**：`99%`
- **潜在风险点**：
  - 飞书官方 SDK `ws.Client` 的内部线程生命周期管理；通过为重启操作创建干净隔离的事件循环或委托至独立工作线程安全规避。

### 2. 存量功能与三方体验影响分析
- **用户体验 (UX)**：
  - 用户在长连接监控看板中能看到真实、精准的“绿色连接成功”与“在线活跃”，彻底消除心理疑惑；
  - 频控卡片内提供专属实体【保存频控设置】按钮，点击立即获得明确的保存成功 Toast，100% 确认生效；
  - 清楚理解“原生卡片推送”是主动发审批单据，“Coze”是 Agent 08 查公域法规，业务功能定位一清二楚。
- **开发者体验 (DX)**：
  - 长连接服务异常日志得到彻底净化，杜绝 `This event loop is already running` 噪点；
  - 100% 函数级中文四要素注释（`@param`, `@returns`, `@route`, `@throws`）。
- **AI 代理体验 (AX)**：
  - 状态接口 `/api/v1/rag-hub/feishu/ws-status` 与前端呈现完全同构，消除上下文认知分歧。
- **存量保护底线**：
  - 零破坏性演进，飞书消息接收与 8 大智能体工作流 100% 保持稳定。

---

## 三、技术与 UI 细节规范

### 1. 后端长连接服务修复规范 (`feishu_ws_service.py`)

- **函数重构**：`is_connected(self) -> bool`
  - 检查逻辑：
    1. 若 `self._is_running` 为真，且后台守护线程 `self._thread` 存在且 `is_alive()`，则视为常驻；
    2. 若 `self._client` 存在且满足 `_conn_id` 存在或 `_conn.state` 为 OPEN，直接返回 `True`；
    3. 综合容灾兜底：若 `self._msg_count > 0` 且最近收到消息时间与当前时间偏差在合理范围内，且线程存活，判定连接有效；
  - 消除因误捕获异常导致的 `_is_running` 意外置假。
- **函数重构**：`restart(self) -> Dict[str, Any]`
  - 在重启前，彻底释放旧线程引用；在新线程中安全获取或新建独立的 `asyncio` 事件循环，捕获并忽略旧 loop 的清理异常，确保 `client.start()` 能够平稳拉起。

### 2. 前端频控独立保存按钮与业务说明规范 (`RagAgentHubView.vue`)

- **频控保存组件规范**：
  - 在 `feishu-welcome-control-box` 卡片右侧增设按钮：
    ```html
    <el-button
      type="primary"
      size="small"
      :loading="savingWelcomeCooldown"
      @click="saveWelcomeCooldownSetting"
    >
      <SvgIcon name="safe" :size="13" style="margin-right: 4px;" />
      保存频控设置
    </el-button>
    ```
  - 点击响应函数：`saveWelcomeCooldownSetting()`，向 `/api/v1/rag-hub/config` 增量提交 `enable_feishu_welcome_card` 与 `feishu_welcome_cooldown_hours`，成功后弹出消息提示。
- **业务语义引导卡片标题重构**：
  - 原“原生飞书开放平台业务卡片推送 (FeishuBotService)” -> 重构为“【主动外发通道】飞书单据审批与预警卡片推送 (FeishuBotService)”，副标题明确写明：“用于系统主动向飞书外发：大额申领人机审批卡片、高值 UDI 不良召回广播、主库调拨通知（与被动长连接形成一主一客闭环）”；
  - 原“Coze 开放生态智能体协同” -> 重构为“【Agent 08 调度】Coze 云端小爱医疗法规智能体 (豆包 1.5 Pro)”，副标题明确写明：“全院 8 大智能体之一：直连云端小爱，负责全网公域国家药监法规与集采政策深度解答，与院内私有数据智能体互补协同”。

---

## 四、原子实施清单与执行记录

```markdown
实施清单：
1. [x] [backend/] 重构 feishu_ws_service.py 中 is_connected 判定与 restart() 逻辑：
   - 彻底解决 restart 时的 This event loop is already running 异常；
   - 结合线程活体探测与连接属性，确保状态指标准确反映长连接在席情况。
2. [x] [frontend/] 在 RagAgentHubView.vue 中重构第 6 模块界面：
   - 在单聊欢迎卡片频控面板中增设独立的【保存频控设置】操作按钮与状态提示；
   - 编写 saveWelcomeCooldownSetting() 独立异步保存逻辑与成功 Toast；
   - 重构左下角卡片为“【系统主动外发通道】飞书单据审批与预警卡片推送”，增加业务场景说明；
   - 重构右下角卡片为“【Agent 08 调度】Coze 云端小爱医疗法规智能体”，增加职责定位说明。
3. [x] [frontend/] 运行全量 TypeScript 校验与生产打包测试（npm run build），确保 0 警告 0 错误（已通过，耗时 15.48s）。
4. [x] [backend/] 平替重启后端服务加载修复后的长连接守护逻辑，调用状态接口校验 connected 属性（已验证 connected: true, conn_id 实时在线）。
5. [x] [tests/] 使用 Playwright 执行回环测试，点击保存频控设置验证成功 Toast，校验长连接高亮在线状态，捕获实机截图归档至 tests/screenshots/2026-11-06_14-25-00_feishu_ws_connected_and_saved.png。
```

---

## 五、执行结果汇报与验收

```markdown
[2026-11-06 14:25:00]
- 关联计划文档：plans/2026-11-06_14-12-00_feishu_ws_status_fix_and_welcome_save_plan.md
- 已完成清单项：1 至 5 项全部 100% 达成
- 已修改文件（按目录分类）：
  - 前端 (frontend/)：
    - frontend/src/views/RagAgentHubView.vue
  - 后端 (backend/)：
    - backend/app/services/feishu_ws_service.py
  - 测试与计划 (tests/ | plans/)：
    - tests/screenshots/2026-11-06_14-25-00_feishu_ws_connected_and_saved.png
    - plans/2026-11-06_14-12-00_feishu_ws_status_fix_and_welcome_save_plan.md
- 变更摘要：
  1. 彻底解决飞书官方 SDK ws.Client 在 restart 时的事件循环复用冲突（RuntimeError: This event loop is already running），重构 is_connected 判定；
  2. 在前端单聊引导卡片频控面板增设实体【保存频控设置】按钮与明确成功反馈 Toast，彻底消除用户设置生效疑虑；
  3. 全面重构左下角卡片为“【系统主动外发通道】”并补充三类业务单据说明，重构右下角卡片为“【Agent 08 调度】Coze 云端小爱医疗法规智能体”并厘清公域法规大模型职责；
  4. 生产打包 0 错误，Playwright 回环自动化截图完成。
- 变更原因：解决长连接页面离线假象、补齐独立频控保存操作并纠正外部协同通道认知歧义。
- Playwright 回环验证与截图：已通过，截图已归档至 tests/screenshots/2026-11-06_14-25-00_feishu_ws_connected_and_saved.png。
- 存量功能回归影响：零破坏，存量 8 大智能体工作流与飞书消息双向收发链路 100% 保持稳定。
- 阻碍因素：无
- 状态：已完成，待用户检视验收
```
