# docs/api_spec.md - FastAPI 后端接口契约、MCP 工具协议与大模型可插拔配置规范

> 本文件作为 **Harness 组件①（接口开发渐进式披露源）** 与 **组件④（前后端通信与大模型集成契约）**。

---

## 一、 全局 RESTful 响应规范与状态码约定

1. **基础路由前缀**：`/api/v1`
2. **认证方式**：`Authorization: Bearer <JWT_TOKEN>`（登录态与用户三级角色缓存在本地 Redis 中）
3. **统一 JSON 返回格式（Pydantic V2 泛型封装）**：
   ```json
   {
     "code": 200,
     "msg": "操作成功",
     "data": {}
   }
   ```
4. **标准业务状态码约定**：
   - `200`：请求执行成功
   - `400`：入参校验失败或业务规则阻断（如：物资已过期禁止分发、仍有在库库存禁止删除字典）
   - `401`：未登录或 Token 已过期
   - `403`：跨角色越权拦截（如：耗材科管理员尝试审批设备科归口单据，或二级库人员尝试访问信息科日志删除接口）
   - `404`：目标资源或单据不存在
   - `500`：服务端内部异常（统一由全局异常处理器捕获并输出高信噪比诊断信息）

---

## 二、 核心业务模块 RESTful 接口清单

### 1. 登录、注册与三级人员科室管理 (`/api/v1/auth` & `/api/v1/users`)
- `POST /api/v1/auth/login` —— 用户登录（返回 JWT Token、角色 `sys_admin / dept_manager / secondary_user`、所属科室编码）
- `POST /api/v1/auth/register` —— 新用户注册或信息科管理员直接添加人员账号
- `GET  /api/v1/users/me` —— 获取当前登录人员详情与权限菜单
- `GET  /api/v1/users` —— 分页查询全院用户列表（支持按角色、科室筛选）
- `PUT  /api/v1/users/{user_id}` —— 修改人员信息、所属科室或启停状态
- `DELETE /api/v1/users/{user_id}` —— 软删除人员账号（仅 `sys_admin`）
- `GET  /api/v1/departments` —— 获取全院科室架构树（区分主库房管理科室、财务科与临床二级库科室）

### 2. 核心 CRUD 一：产品字典与双维分类管理 (`/api/v1/dict`)
- `GET    /api/v1/dict/categories` —— 获取“主库房主科室（耗材科/设备科）+ 耗材多级分类（普通/高值/设备配件）”树形列表
- `POST   /api/v1/dict/categories` —— 新增产品分类节点
- `GET    /api/v1/dict/products` —— 多条件分页查询产品字典（按归口主科室、耗材分类、UDI-DI 码、关键词筛选）
- `POST   /api/v1/dict/products` —— 新增产品字典档案（自动记录全流程日志节点 `1_DICT_CREATE`）
- `PUT    /api/v1/dict/products/{product_id}` —— 修改产品字典信息、归口主科室、分类或安全库存阈值
- `DELETE /api/v1/dict/products/{product_id}` —— 软删除停用产品字典（前置校验主库、高值仓、二级库库存均为 0）

### 3. 核心 CRUD 二：普通耗材管理——主库全部物资与按需分发 (`/api/v1/main-warehouse`)
- `GET    /api/v1/main-warehouse/inventory` —— 分页查询主库总仓批次库存（支持按主科室归口、临期预警、缺货预警筛选）
- `POST   /api/v1/main-warehouse/inbound` —— 主库采购验收入库（校验注册证与效期，写入批次库存与流转日志节点 `2_MAIN_INBOUND`）
- `PUT    /api/v1/main-warehouse/inventory/{id}` —— 调整主库货位、盘点修正数量或更新效期冻结状态
- `DELETE /api/v1/main-warehouse/inventory/{id}` —— 撤销未发生分发的错误入库记录
- `GET    /api/v1/main-warehouse/distributions` —— 查询主库按需分发调拨单列表
- `POST   /api/v1/main-warehouse/distributions` —— 创建主库按需分发调拨单（支持发往**临床二级库**或转入**高值耗材仓库**，扣减主库库存并写入流转日志节点 `3_MAIN_DISPATCH`）

### 4. 核心 CRUD 三：高值耗材管理——一物一码专仓 (`/api/v1/high-value`)
- `GET    /api/v1/high-value/items` —— 分页查询高值耗材一物一码台账（按 UDI 唯一序列号、状态、所在专柜、患者住院号检索）
- `POST   /api/v1/high-value/activate` —— 主库分拨转入高值仓时触发“由量到码”拆包赋码（写入流转日志节点 `4_HIGH_VALUE_CODE`）
- `PUT    /api/v1/high-value/items/{id}/verify` —— 临床手术/诊疗绑定患者住院号扫码核销（状态变为 `USED_VERIFIED`，触发财务记账并写入日志节点 `7_CLINICAL_CONSUME`）
- `PUT    /api/v1/high-value/items/{id}/status` —— 变更跟台锁定、退回专仓或不良事件召回冻结状态
- `DELETE /api/v1/high-value/items/{id}` —— 作废未启用的错误条码记录

### 5. 核心 CRUD 四：二级库管理——临床科室库房 (`/api/v1/secondary-warehouse`)
- `GET    /api/v1/secondary-warehouse/inventory` —— 查询当前临床科室二级库库存与定数包预警
- `POST   /api/v1/secondary-warehouse/receive/{dist_id}` —— 临床二级库签收主库按需分发单（支持正常签收增加二级库库存，或差异拒收退回主库，写入日志节点 `5_SEC_RECEIVE`）
- `POST   /api/v1/secondary-warehouse/consume` —— 登记二级库日常耗材临床消耗（扣减二级库库存并触发财务科室成本记账，写入日志节点 `7_CLINICAL_CONSUME`）
- `GET    /api/v1/secondary-warehouse/requisitions` —— 查询二级库向主库发起的申领单与逆向退库单
- `POST   /api/v1/secondary-warehouse/requisitions` —— 临床二级库新建物资申领单或逆向退库单（按产品归口主科室定向流转至耗材科或设备科）
- `PUT    /api/v1/secondary-warehouse/requisitions/{id}/approve` —— 耗材科/设备科管理员审批申领单或退库单（写入日志节点 `6_SEC_APPLY` / `8_REVERSE_AUDIT`）
- `DELETE /api/v1/secondary-warehouse/requisitions/{id}` —— 撤回处于待审批状态的申领单

### 6. 核心 CRUD 五：全流程业务链路日志管理 (`/api/v1/workflow-logs`)
- `GET    /api/v1/workflow-logs` —— 多维穿透查询全流程流转日志（按业务单号、物资编码、源科室/交出人、目标科室/接收人、8 大节点类型查询）
- `POST   /api/v1/workflow-logs` —— 信息科管理员手动补录异常审计日志
- `PUT    /api/v1/workflow-logs/{id}` —— 信息科管理员或财务科对流转日志更新审计状态（`VERIFIED / FLAGGED / RECTIFIED`）与复核备注
- `DELETE /api/v1/workflow-logs/{id}` —— 信息科系统管理员清理无效测试日志或执行归档（仅 `sys_admin`）

### 7. 统计查询与单据打印中心 (`/api/v1/stats` & `/api/v1/print`)
- `GET /api/v1/stats/overview` —— 全院主库、高值仓、各二级库库存与近效期/低库存汇总大盘
- `GET /api/v1/stats/dept-consumption` —— 各临床二级库耗材消耗金额排行与普通/高值耗占比统计（供财务科核算）
- `GET /api/v1/print/voucher/{voucher_type}/{order_no}` —— 获取 5 类医院标准法定单据打印结构化数据（含四联责任签字栏信息）

### 8. 5 大业务智能体与流程图接口 (`/api/v1/agents`)
- `POST /api/v1/agents/{agent_id}/invoke` —— 调用指定智能体（`agent_01` 至 `agent_05`），返回智能体推理结果、每个 LangGraph 节点的执行轨迹、调用的 MCP 工具及 Chroma RAG 引用片段
- `GET  /api/v1/agents/metadata` —— 获取 5 大智能体的职责说明、挂载的 MCP 工具列表及标准节点流程图定义

---

## 三、 大模型与宿主环境可插拔配置规范 (`backend/.env.example`)

为保障极高的可维护性，所有外部服务与大模型连接参数统一通过环境变量注入，严禁在业务代码中硬编码：

```ini
# 1. 本地关系型数据库与缓存配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=medical_spd_system

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

# 2. 向量数据库与本地 Ollama 配置
CHROMA_PERSIST_DIR=./chroma_data
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=qwen2.5:7b

# 3. 云端小米 MiMo 大模型配置（可随时填入切换为默认推理引擎）
LLM_PROVIDER=ollama  # 可选值: ollama | xiaomi_mimo
XIAOMI_MIMO_API_KEY=your_xiaomi_mimo_api_key
XIAOMI_MIMO_BASE_URL=https://api.xiaomi.com/v1
XIAOMI_MIMO_MODEL=mimo-pro

# 4. 可选 Coze 智能体协同配置（用于第 4/5 个智能体双模运行）
COZE_ENABLED=false
COZE_API_TOKEN=your_coze_pat_token
COZE_BOT_ID=your_coze_bot_id
```
