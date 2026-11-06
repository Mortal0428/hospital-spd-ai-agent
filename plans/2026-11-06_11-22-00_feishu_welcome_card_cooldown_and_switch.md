# 研发实施规划：飞书单聊欢迎卡片频控防打扰机制与前台热插拔控制开关

- **计划文档路径**：`plans/2026-11-06_11-22-00_feishu_welcome_card_cooldown_and_switch.md`
- **记录时间戳**：`2026-11-06 11:22:00`
- **前端目标文件**：
  - `frontend/src/views/RagAgentHubView.vue`（在第 6 模块飞书协同面板中集成欢迎卡片总开关、快捷周期档位与自定义小时输入控件）
- **后端目标文件**：
  - `backend/app/models/rag_agent_models.py`（在 `SpdModularRagConfig` 中新增 `enable_feishu_welcome_card` 与 `feishu_welcome_cooldown_hours` 持久化字段）
  - `backend/app/services/feishu_ws_service.py`（在 `_on_chat_entered` 中注入全局开关校验与用户维度时间戳频控拦截缓存）
  - `backend/app/routers/rag_agent_hub_router.py`（在配置保存与下发接口中同步支持新字段）
- **测试与截图文件**：
  - `tests/test_feishu_welcome_cooldown.py`（后端频控阻断与开关单元测试）
  - `tests/screenshots/2026-11-06_11-30-00_feishu_welcome_card_control_ui.png`（前端配置面板实机截图）

---

## 一、核心评估指标

1. **可行性与把握度评估**：
   - **把握度：99%**。
   - **技术路径**：
     - 在后端内存中维护 `_user_welcome_timestamp: Dict[str, float]`，以用户唯一标识（`open_id` 或 `chat_id`）为键；
     - 当收到飞书 `p2_im_chat_access_event_bot_p2p_chat_entered_v1` 事件时，首先读取 `SpdModularRagConfig`：
       - 若 `enable_feishu_welcome_card == 0`，直接记录日志并熔断返回；
       - 若开启，计算当前时间戳距离上次推送是否小于 `feishu_welcome_cooldown_hours * 3600`，小于则阻断推送；
       - 超过冷却期或首次进入，执行推送并更新时间戳缓存；
     - 前端提供四档快捷周期（每 12 小时、每天 1 次 / 24小时、每周 1 次 / 168小时、自定义小时数），并在【保存全部配置】时持久化落盘。

2. **存量功能与三方体验（UX/DX/AX）影响分析**：
   - **用户体验（UX）**：彻底解决飞书用户每次打开私聊都被大卡片刷屏骚扰的痛点；管理员可在控制台中随心所欲设定“每天弹 1 次”或“自定义 N 小时后才弹”，或一键彻底关闭。
   - **开发者体验（DX）**：命名规范，状态持久化到 MySQL，进程重启有 DB 配置托底；函数带有清晰的中文四要素注释。
   - **AI 代理体验（AX）**：结构显式声明，易于后续跨轮次测试与状态追踪。
   - **零破坏底线**：普通私聊提问、群聊 @ 机器人交互、8 大业务智能体执行链路 100% 保持稳定，长连接心跳保活不中断。

3. **Playwright 自动化回环测试与截图验证方案**：
   - **测试点 1**：执行后端频控测试脚本，模拟同一用户连续 5 次进入单聊，断言第 1 次成功推送、第 2~5 次 100% 被频控冷却拦截；
   - **测试点 2**：模拟将全局开关置为关闭（`enable_feishu_welcome_card = 0`），断言无论冷却是否过期均 100% 阻断；
   - **测试点 3**：使用 Playwright 访问 `http://127.0.0.1:5173/rag-agent-hub`，切换至第 2 个 Tab，定位至第 6 模块飞书配置区，验证开关、单选档位与自定义输入框渲染正常；
   - **测试点 4**：捕获实机截图保存至 `tests/screenshots/2026-11-06_11-30-00_feishu_welcome_card_control_ui.png`。

---

## 二、技术与 UI 细节规范

### 1. 数据模型与迁移规范 (`rag_agent_models.py`)

在 `SpdModularRagConfig` 类中追加两个标准化字段：
```python
# 飞书单聊欢迎卡片频控与开关
enable_feishu_welcome_card: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="是否启用进入单聊自动弹出引导卡片: 1-开启, 0-关闭")
feishu_welcome_cooldown_hours: Mapped[float] = mapped_column(Numeric(6, 2), default=24.0, nullable=False, comment="飞书引导卡片用户频控冷却时间(小时，如24表示每天仅弹窗1次)")
```
通过安全脚本执行：
```sql
ALTER TABLE spd_modular_rag_config ADD COLUMN enable_feishu_welcome_card SMALLINT NOT NULL DEFAULT 1 COMMENT '是否启用进入单聊自动弹出引导卡片: 1-开启, 0-关闭';
ALTER TABLE spd_modular_rag_config ADD COLUMN feishu_welcome_cooldown_hours DECIMAL(6,2) NOT NULL DEFAULT 24.00 COMMENT '飞书引导卡片用户频控冷却时间(小时)';
```

### 2. 飞书长连接服务频控拦截引擎 (`feishu_ws_service.py`)

在 `FeishuWsService` 中追加属性与频控逻辑：
```python
self._user_welcome_timestamp: Dict[str, float] = {}
```
在 `_on_chat_entered` 中实现：
1. 查询配置：从数据库读取 `SpdModularRagConfig`（带本地内存短缓存优化）；
2. 校验 `enable_feishu_welcome_card`：为 0 则直接退出；
3. 校验时间跨度：`elapsed_seconds = now - last_time`；
4. 若 `elapsed_seconds < cooldown_hours * 3600`，输出跳过日志并 `return`；
5. 若满足推送条件，更新时间戳并调用 `feishu_service.send_interactive_card`。

### 3. 前端交互与管理界面规范 (`RagAgentHubView.vue`)

- **位置**：`RagAgentHubView.vue` 中的“6. 外部生态与开放平台协同通道 (官方 SDK 长连接 & 原生卡片 & Coze 云端)”卡片内；
- **组件结构**：
  - 顶部栏：标签“单聊进入自动引导卡片” + “防打扰频控”徽章 + `el-switch` 开关；
  - 展开区（仅当开启时可见）：
    - 频控周期单选组（`el-radio-group`）：
      - `12h`（每 12 小时）
      - `24h`（每天 1 次，默认）
      - `168h`（每周 1 次）
      - `custom`（自定义时间）
    - 自定义小时输入框（`el-input-number`）：仅当选择 `custom` 时显示，支持 `0.1` 至 `720` 小时，精度 1 位小数；
- **状态流转**：
  - 同步集成至 `configForm`，并在点击【一键手动保存全部配置并立即生效】时持久化到后端。

---

## 三、原子级实施清单

```markdown
实施清单：
1. [backend/] 扩展数据库模型与数据表字段（rag_agent_models.py 与 DB Migration）：
   - 在 SpdModularRagConfig 中新增 enable_feishu_welcome_card 与 feishu_welcome_cooldown_hours；
   - 执行安全的数据库迁移脚本添加该列并赋予默认值 (1 与 24.0)。
2. [backend/] 重构飞书单聊进入事件处理引擎（feishu_ws_service.py）：
   - 在 FeishuWsService 构造函数中初始化 self._user_welcome_timestamp 用户时间戳字典；
   - 在 _on_chat_entered 回调中增加开关判定与以秒为单位的冷却阈值计算；
   - 增加冷却期剩余时间日志并正确阻断高频重发。
3. [backend/] 适配配置接口与持久化通道（rag_agent_hub_router.py）：
   - 确保 /api/v1/rag-hub/config 和 /api/v1/rag-hub/config/save-all 正确回显并持久化两个新字段。
4. [frontend/] 在 RagAgentHubView.vue 飞书控制台中集成前端开关与周期控制器：
   - 编写飞书单聊欢迎卡片频控控制面板模板（el-switch + el-radio-group + el-input-number）；
   - 在 configForm 中双向绑定新配置，并实现周期档位切换逻辑；
   - 确保全域禁用 Emoji，样式适配明暗主题 CSS 变量。
5. [frontend/] 运行全量 TypeScript 校验与生产级构建测试（npm run build），确保 0 警告 0 错误。
6. [tests/] 编写并运行频控单元测试（test_feishu_welcome_cooldown.py），验证高频访问阻断与开关生效；
7. [tests/] 按需重启后端服务并通过 Playwright 捕获前端配置面板实机截图，归档至 tests/screenshots/。
```

计划已同步落盘归档至：[plans/2026-11-06_11-22-00_feishu_welcome_card_cooldown_and_switch.md](file:///e:/个人项目作品/杭电集训项目/0728_陈永兴_医疗物资系统/plans/2026-11-06_11-22-00_feishu_welcome_card_cooldown_and_switch.md)

请审阅上述计划。若认可该实施方案，请回复指示进入执行模式（例如回复“执行”或“同意”），我将立即按清单逐项落地。
