const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');
const { launchPersistentPlaywright } = require('../e2e/browser_config');
const { checkNoEmoji } = require('./guardrails');

const ROOT_DIR = path.resolve(__dirname, '../..');
const BASE_URL = 'http://127.0.0.1:8000';
const SCREENSHOT_PATH = path.resolve(
  ROOT_DIR,
  'tests/screenshots/2026-11-02_19-15-00_full_spd_backend_and_matrix_verify.png'
);

/**
 * 发送 HTTP JSON 请求的轻量封装函数
 * @param {string} method HTTP 方法 (GET/POST)
 * @param {string} urlPath 接口相对路径 (如 /api/v1/ext/rbac/matrix)
 * @param {object | null} body JSON 请求体
 * @returns {Promise<{statusCode: number, data: any}>} 返回 HTTP 状态码与解析后的 JSON
 * @route internal://tests/harness/verify_full_spd_business.js/httpRequestJson
 * @throws {Error} 当网络异常或 JSON 解析失败时抛出错误
 */
function httpRequestJson(method, urlPath, body = null) {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : null;
    const req = http.request(
      `${BASE_URL}${urlPath}`,
      {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {})
        }
      },
      (res) => {
        let raw = '';
        res.on('data', (chunk) => {
          raw += chunk;
        });
        res.on('end', () => {
          try {
            const parsed = raw ? JSON.parse(raw) : {};
            resolve({ statusCode: res.statusCode, data: parsed });
          } catch (err) {
            resolve({ statusCode: res.statusCode, data: raw });
          }
        });
      }
    );
    req.on('error', reject);
    if (payload) {
      req.write(payload);
    }
    req.end();
  });
}

/**
 * 轮询等待 FastAPI 8000 端口服务就绪
 * @param {number} maxRetries 最大重试次数
 * @returns {Promise<boolean>} 服务就绪返回 true
 * @route internal://tests/harness/verify_full_spd_business.js/waitForServerReady
 * @throws {Error} 超时未就绪时抛出异常
 */
async function waitForServerReady(maxRetries = 30) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await httpRequestJson('GET', '/api/v1/health');
      if (res.statusCode === 200) {
        return true;
      }
    } catch (_) {
      // 继续等待启动
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error('FastAPI 服务在 8000 端口启动超时');
}

/**
 * 执行第一阶段深度扩展全套 SPD 业务模块、细粒度 RBAC、两阶段确认状态机与 Playwright 实机截图验证
 * @returns {Promise<void>} 异步执行完成无返回值
 * @route internal://tests/harness/verify_full_spd_business.js/runFullSpdBusinessVerification
 * @throws {Error} 任一断言未通过时抛出异常并终止进程
 */
async function runFullSpdBusinessVerification() {
  console.log('=== [Stage 2+ Harness] 开始执行全套 SPD 深度业务闭环与 12 项强断言验证 ===');

  // 断言 1: 静态护栏扫描 (零 Emoji + 扩展 7 张 ORM 模型 100% 中文 comment 覆盖)
  const targetFiles = [
    'AGENTS.md',
    'SKILL.md',
    'backend/app/models/spd_extended_models.py',
    'backend/app/schemas/spd_extended_schemas.py',
    'backend/app/services/rbac_and_confirm_service.py',
    'backend/app/routers/extended_spd_router.py'
  ];
  for (const rel of targetFiles) {
    const content = fs.readFileSync(path.resolve(ROOT_DIR, rel), 'utf-8');
    const emojiRes = checkNoEmoji(content, rel);
    if (!emojiRes.passed) {
      throw new Error(emojiRes.violation);
    }
  }
  const extModelContent = fs.readFileSync(
    path.resolve(ROOT_DIR, 'backend/app/models/spd_extended_models.py'),
    'utf-8'
  );
  const mappedCols = extModelContent.match(/mapped_column\(/g) || [];
  const colComments = extModelContent.match(/comment="[^"]+"/g) || [];
  const tableComments = extModelContent.match(/"comment":\s*"[^"]+"/g) || [];
  if (
    mappedCols.length === 0 ||
    colComments.length < mappedCols.length ||
    tableComments.length < 7
  ) {
    throw new Error(
      `[ORM-Comment-Fail] spd_extended_models.py 字段数(${mappedCols.length})、字段comment数(${colComments.length})或表comment数(${tableComments.length})不匹配`
    );
  }
  console.log(
    `[PASS 1/12] 静态护栏通过：0 Emoji，扩展 7 张 ORM 表(${tableComments.length}处表注释 + ${colComments.length}处字段注释) 100% 覆盖`
  );

  // 启动或复用 FastAPI 服务
  let serverProc = null;
  let alreadyRunning = false;
  try {
    const ping = await httpRequestJson('GET', '/api/v1/health');
    if (ping.statusCode === 200) {
      alreadyRunning = true;
    }
  } catch (_) {
    alreadyRunning = false;
  }

  if (!alreadyRunning) {
    serverProc = spawn('E:\\python\\python.exe', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
      cwd: path.resolve(ROOT_DIR, 'backend'),
      stdio: 'pipe'
    });
    await waitForServerReady(40);
  }

  let context = null;
  try {
    // 断言 2: 信息科解耦式 15 模块 x 8 动作细粒度权限矩阵查询与动态开关
    const rbacGet = await httpRequestJson('GET', '/api/v1/ext/rbac/matrix');
    if (rbacGet.statusCode !== 200 || rbacGet.data.data.total < 50) {
      throw new Error(`[Assert 2 Fail] RBAC 矩阵查询异常: ${JSON.stringify(rbacGet.data)}`);
    }
    const rbacToggle = await httpRequestJson('POST', '/api/v1/ext/rbac/toggle', {
      user_id: 5,
      module_code: 'GEN_INBOUND',
      action_key: 'can_second_confirm',
      enabled: 1,
      operator_name: '赵振华(信息科管理员)'
    });
    if (rbacToggle.statusCode !== 200 || rbacToggle.data.data.new_value !== 1) {
      throw new Error(`[Assert 2 Fail] 细粒度权限开关切换失败`);
    }
    console.log(`[PASS 2/12] 信息科解耦式 8 项原子动作 RBAC 权限矩阵查询(${rbacGet.data.data.total}条)与单人开关验证通过`);

    // 断言 3: 产品字典深度管理(左侧仓库树+分类树+自动拼音码+复制品名到其他仓库+调价管理)
    const dictRes = await httpRequestJson('GET', '/api/v1/ext/dict/overview');
    if (
      dictRes.statusCode !== 200 ||
      dictRes.data.data.warehouse_tree.length < 9 ||
      !dictRes.data.data.products[0].pinyin_code
    ) {
      throw new Error(`[Assert 3 Fail] 产品字典双树或拼音码缺失`);
    }
    const copyRes = await httpRequestJson('POST', '/api/v1/ext/dict/copy-warehouse', {
      product_id: 1,
      target_warehouse_code: 'WH_ZONGWU'
    });
    const priceRes = await httpRequestJson('POST', '/api/v1/ext/dict/adjust-price', {
      product_id: 1,
      new_price: 0.42,
      reason: '省级集采二次联动调价'
    });
    if (copyRes.statusCode !== 200 || priceRes.statusCode !== 200) {
      throw new Error(`[Assert 3 Fail] 复制品名到其他仓库或调价失败`);
    }
    console.log(`[PASS 3/12] 产品字典双树(9大仓库节点)、拼音助记码(${dictRes.data.data.products[0].pinyin_code})、跨仓复制与调价验证通过`);

    // 断言 4: 耗材入库模块【退给供应商红字退货单】及两阶段二次确认 + 取消提交状态机
    const retCreate = await httpRequestJson('POST', '/api/v1/ext/orders/inbound-outbound', {
      order_type: 'RETURN_TO_SUPPLIER',
      warehouse_code: 'WH_WEICAI',
      dept_code: 'CONSUMABLE_DEPT',
      target_dept_or_supplier: 'SUP_WEGO_01',
      product_id: 1,
      batch_no: 'B20261001',
      quantity: 15,
      created_by: '王建国',
      remark: '包装破损退回供应商'
    });
    const retOrderNo = retCreate.data.data.order_no;
    if (retCreate.data.data.quantity !== -15 || retCreate.data.data.confirm_stage !== 'PENDING_CONFIRM') {
      throw new Error(`[Assert 4 Fail] 退给供应商红字单第1次提交状态或负向数量异常`);
    }
    // 外层第 2 次确认提交 -> SUBMITTED
    const retConfirm2 = await httpRequestJson('POST', '/api/v1/ext/orders/two-step-action', {
      order_no: retOrderNo,
      action: 'SECOND_CONFIRM',
      operator_name: '王建国'
    });
    if (retConfirm2.data.data.confirm_stage !== 'SUBMITTED') {
      throw new Error(`[Assert 4 Fail] 外层二次确认未进入 SUBMITTED`);
    }
    // SUBMITTED 状态下直接修改必须被拦截 (400)
    const editBlocked = await httpRequestJson('POST', '/api/v1/ext/orders/two-step-action', {
      order_no: retOrderNo,
      action: 'EDIT_REMARK',
      operator_name: '王建国',
      new_remark: '尝试直接修改已二次确认单据'
    });
    if (editBlocked.statusCode !== 400) {
      throw new Error(`[Assert 4 Fail] 已二次确认单据未拦截直接修改`);
    }
    // 点击【取消提交 (CANCEL_SUBMIT)】退回 PENDING_CONFIRM 后允许修改
    const cancelRes = await httpRequestJson('POST', '/api/v1/ext/orders/two-step-action', {
      order_no: retOrderNo,
      action: 'CANCEL_SUBMIT',
      operator_name: '王建国'
    });
    if (cancelRes.data.data.confirm_stage !== 'PENDING_CONFIRM') {
      throw new Error(`[Assert 4 Fail] 取消提交未退回 PENDING_CONFIRM`);
    }
    console.log(`[PASS 4/12] 退给供应商红字退货单(${retOrderNo}, 数量-15)及两阶段确认 -> 锁死拦截 -> 取消提交回退闭环通过`);

    // 断言 5: 请领受理审核通过后，自动在【耗材出库】模块生成对应的审核出库记录
    const autoOutRes = await httpRequestJson('POST', '/api/v1/ext/orders/requisition-auto-outbound/1?auditor_name=王建国');
    if (
      autoOutRes.statusCode !== 200 ||
      !autoOutRes.data.data.auto_outbound_order_no.startsWith('OUT-AUTO-')
    ) {
      throw new Error(`[Assert 5 Fail] 请领审核通过未能自动生成耗材出库单`);
    }
    console.log(`[PASS 5/12] 请领受理审核通过自动联动生成耗材出库单(${autoOutRes.data.data.auto_outbound_order_no})验证通过`);

    // 断言 6: 各科室仓库【期初数据 (INIT_STOCK)】二次确认后永久锁定只读（只可填写一次，严禁取消提交或重复填报）
    const initCancelBlocked = await httpRequestJson('POST', '/api/v1/ext/orders/two-step-action', {
      order_no: 'INI20261101001',
      action: 'CANCEL_SUBMIT',
      operator_name: '赵振华'
    });
    const initDupBlocked = await httpRequestJson('POST', '/api/v1/ext/orders/inbound-outbound', {
      order_type: 'INIT_STOCK',
      warehouse_code: 'WH_WEICAI',
      dept_code: 'CONSUMABLE_DEPT',
      target_dept_or_supplier: '耗材科重复期初',
      product_id: 1,
      batch_no: 'B20261001',
      quantity: 500,
      created_by: '王建国'
    });
    if (initCancelBlocked.statusCode !== 400 || initDupBlocked.statusCode !== 400) {
      throw new Error(`[Assert 6 Fail] 期初数据永久只读或一次性填报拦截失效`);
    }
    console.log(`[PASS 6/12] 科室仓库期初数据(INI20261101001)二次确认后永久锁死只读与防重复填报硬护栏通过`);

    // 断言 7: 全院各科室独立盘点单（自动核算账实盈亏差额）与跨院调拨单
    const stkRes = await httpRequestJson('POST', '/api/v1/ext/orders/stocktake-transfer', {
      biz_category: 'SEC_STOCKTAKE',
      from_warehouse_code: 'WH_SEC_ORTHO',
      product_id: 1,
      book_qty: 150,
      actual_or_transfer_qty: 155,
      operator_name: '李晓琳(骨科护士)',
      reason_note: '骨科二级库月末盘盈5支'
    });
    if (stkRes.statusCode !== 200 || stkRes.data.data.diff_qty !== 5) {
      throw new Error(`[Assert 7 Fail] 科室仓库盘点盈亏差额计算错误`);
    }
    console.log(`[PASS 7/12] 科室独立仓库盘点单(${stkRes.data.data.order_no}, 账面150/实盘155/盘盈+5)验证通过`);

    // 断言 8: 高值耗材【科室退货出库单 (HV_DEPT_RETURN)】二次确认后永久不可改、不可取消提交
    const hvReturnBlocked = await httpRequestJson('POST', '/api/v1/ext/high-value/two-step-action', {
      order_no: 'HVR20261102001',
      action: 'CANCEL_SUBMIT',
      operator_name: '李晓琳'
    });
    if (hvReturnBlocked.statusCode !== 400) {
      throw new Error(`[Assert 8 Fail] 高值科室退货出库单二次确认后未永久锁死`);
    }
    console.log(`[PASS 8/12] 高值耗材科室退货出库单(HVR20261102001)二次确认后永久锁死不可逆铁律验证通过`);

    // 断言 9: 高值耗材一物一码生成专属二维码 + 扫码核销后方可在【高值核销查询】显示
    const verifiedBefore = await httpRequestJson('GET', '/api/v1/ext/high-value/verified-list');
    const unverifiedFoundBefore = verifiedBefore.data.data.some((x) => x.udi_sn === 'SN202610100001');
    if (unverifiedFoundBefore) {
      throw new Error(`[Assert 9 Fail] 未扫码核销的高值耗材不应出现在高值核销查询列表中`);
    }
    const qrScanRes = await httpRequestJson('POST', '/api/v1/ext/high-value/qr-verify', {
      udi_sn: 'SN202610100001',
      patient_inpatient_no: 'ZY2026110299',
      patient_name: '刘德华',
      operator_name: '李晓琳(骨科护士)'
    });
    const verifiedAfter = await httpRequestJson('GET', '/api/v1/ext/high-value/verified-list');
    const verifiedFoundAfter = verifiedAfter.data.data.find((x) => x.udi_sn === 'SN202610100001');
    if (
      qrScanRes.statusCode !== 200 ||
      !verifiedFoundAfter ||
      verifiedFoundAfter.patient_name_masked !== '刘*华'
    ) {
      throw new Error(`[Assert 9 Fail] 高值一物一码二维码扫码核销或患者姓名脱敏异常`);
    }
    console.log(`[PASS 9/12] 高值一物一码专属二维码扫码核销(SN202610100001 -> 患者脱敏:刘*华)与核销查询联动通过`);

    // 断言 10: 供应商经营资质准入硬拦截（未审核通过 QUAL_PENDING 的供应商严禁接单发货）
    const supBlocked = await httpRequestJson('POST', '/api/v1/ext/supplier-purchase/flow', {
      order_no: 'PUR20261102002',
      flow_action: 'SUPPLIER_PICK_AND_SHIP',
      operator_name: '未审资质供应商'
    });
    if (supBlocked.statusCode !== 403) {
      throw new Error(`[Assert 10 Fail] 未通过经营许可证审核的供应商未被 403 硬拦截`);
    }
    console.log(`[PASS 10/12] 供应商《医疗器械经营许可证》准入硬拦截(QUAL_PENDING 拒绝接单发货 403)验证通过`);

    // 断言 11: 多级采购计划 -> 耗材科审批 -> 合规供应商拣货二次确认发货 -> 自动同步生成医院《待验收入库单》
    const supShipOk = await httpRequestJson('POST', '/api/v1/ext/supplier-purchase/flow', {
      order_no: 'PUR20261102001',
      flow_action: 'SUPPLIER_PICK_AND_SHIP',
      picked_batch_no: 'BATCH-WEGO-20261102',
      picked_expiry_date: '2029-11-01',
      operator_name: '张明远(威高医药代表)'
    });
    const autoInbNo = supShipOk.data.data.auto_inbound_order_no;
    if (supShipOk.statusCode !== 200 || !autoInbNo || !autoInbNo.startsWith('INB-SUP-')) {
      throw new Error(`[Assert 11 Fail] 供应商二次确认发货后未自动生成医院待验收入库单`);
    }
    console.log(`[PASS 11/12] 多级采购与供应商二次确认发货自动生成医院待验收入库单(${autoInbNo})闭环通过`);

    // 断言 12: Playwright 真实浏览器访问 17 表全景监控大盘，校验 0 Console Error 并捕获实机截图
    const pw = await launchPersistentPlaywright();
    context = pw.context;
    const page = await context.newPage();
    await page.setViewportSize({ width: 1440, height: 1080 });

    const consoleErrors = [];
    const pageErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      pageErrors.push(err.message);
    });

    await page.goto(`${BASE_URL}/api/v1/health/dashboard`, { waitUntil: 'networkidle' });
    const tableCountText = await page.locator('#stat-orm-tables').innerText();
    const rowCount = await page.locator('tbody tr').count();
    if (!tableCountText.includes('17') || rowCount !== 17) {
      throw new Error(`[Assert 12 Fail] 监控大盘未完整渲染 17 张 ORM 表 (实际行数: ${rowCount})`);
    }
    if (consoleErrors.length > 0 || pageErrors.length > 0) {
      throw new Error(`[Assert 12 Fail] 页面存在控制台或运行时错误: ${consoleErrors.join('; ')}`);
    }

    fs.mkdirSync(path.dirname(SCREENSHOT_PATH), { recursive: true });
    await page.screenshot({ path: SCREENSHOT_PATH, fullPage: true });
    console.log(`[PASS 12/12] Playwright 实机验证 17 张 MySQL ORM 表全景大盘通过(0 错误)，截图已归档至: ${SCREENSHOT_PATH}`);
  } finally {
    if (context) {
      await context.close();
    }
    if (serverProc) {
      serverProc.kill();
    }
  }
}

runFullSpdBusinessVerification().catch((err) => {
  console.error('[FATAL] Stage 2+ 全套 SPD 深度业务闭环验证失败:', err.message);
  process.exit(1);
});
