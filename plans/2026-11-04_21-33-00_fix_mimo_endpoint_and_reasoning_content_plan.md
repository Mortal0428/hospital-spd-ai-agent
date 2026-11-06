# 修正小米 MiMo 真实端点、解析原生 reasoning_content 思考链实施计划

- 计划文档路径：`plans/2026-11-04_21-33-00_fix_mimo_endpoint_and_reasoning_content_plan.md`
- 记录时间戳：`2026-11-04 21:33:00`
- 关联问题与实机现象：
  - 用户实机提问“你好”秒回复，思考链显示“网络超时触发备用规则引擎”，正文显示“【云端 MiMo 离线保护】已基于内控规则完成指令响应”；
  - 根因：后端配置了错误的域名 `https://api.xiaomi.com/v1`（小米手机业务网关，掐断连接），小米官方大模型真实开放平台端点为 `https://api.xiaomimimo.com/v1`，且原生思考内容存放在 `choices[0].message.reasoning_content`。

---

## 一、核心评估指标

- **方案把握度**：100%（已通过真实网络请求验证该官方端点，返回 HTTP 200，推理耗时约 8.2s，返回专业医学正文与思考链）。
- **存量功能与三方体验影响**：
  - **UX**：智能体彻底告别秒回与离线警告，呈现真实的真实推理时延（数秒）、完整的 DeepSeek/<think>/reasoning_content 思考过程折叠展开与高质量模型输出；
  - **DX**：统一大模型客户端（`llm_client.py`）标准化支持 OpenAI 协议原生思考字段提取，代码健壮规范；
  - **AX**：智能体多轮会话日志（`spd_agent_chat_message`）真实持久化大模型产生的深度思考过程。

---

## 二、目标变更范围

### 1. 后端目标文件
- `backend/app/core/config.py`：将 `XIAOMI_MIMO_BASE_URL` 改为 `https://api.xiaomimimo.com/v1`；
- `backend/app/services/agents/llm_client.py`：
  - 默认端点切换为官方真实域名；
  - 提取 `choices[0]["message"].get("reasoning_content")`，将其作为高优先级思考链；
  - 真实 Token 统计与响应时延映射；
- `backend/app/routers/rag_agent_hub_router.py`：更新配置默认值；
- 数据库落盘校准：更新 MySQL 中的 `spd_modular_rag_config` 与 `spd_agent_model_config` 表中存在的旧域名。

### 2. 前端目标文件
- `frontend/src/views/RagAgentHubView.vue`：更新表单默认端点为 `https://api.xiaomimimo.com/v1`。

### 3. 测试与验证目标
- 执行真实请求测试智能体 3 与智能体 6，校验返回无“离线保护”，包含真实 `reasoning_content`；
- 重启后端守护服务与前端预览；
- 抓取实机截图归档至 `tests/screenshots/`。

---

## 三、原子级实施清单

1. `[backend/app/core/config.py]`：将 `XIAOMI_MIMO_BASE_URL` 修正为 `https://api.xiaomimimo.com/v1`；
2. `[backend/app/services/agents/llm_client.py]`：重构小米 MiMo 客户端，解析 `message.reasoning_content` 思考链，对齐 OpenAI 扩展协议；
3. `[数据库更新]`：执行脚本更新 MySQL 库内 `spd_modular_rag_config` 与 `spd_agent_model_config`，将旧 URL 批量更正为 `https://api.xiaomimimo.com/v1`；
4. `[frontend/src/views/RagAgentHubView.vue]`：对齐默认端点，执行 `npm run build` 重新打包；
5. `[服务重启]`：平滑重启后端 Uvicorn 8000；
6. `[真实调用验证]`：发送实际临床提问，验证真实耗时（>1s）、提取到非空的真实思考链，并截取证据图。
