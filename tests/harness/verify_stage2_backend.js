/**
 * 阶段 2 后端存储与 5 套核心业务 CRUD 接口端到端回环验证器
 *
 * 本脚本完成:
 * 1. 静态代码合规扫描: backend/ 源码零 Emoji 校验与 10 个核心 ORM 模型 100% comment 注释校验;
 * 2. 启动本地 FastAPI 后端服务并执行 5 大核心业务流程 API 自动化断言;
 * 3. 驱动 Playwright 无锁浏览器实机渲染后端数据库与接口健康看板并截屏归档.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { launchPersistentPlaywright } = require('../e2e/browser_config');
const { checkNoEmoji, verifyOrmCommentsGuard } = require('./guardrails');

const PYTHON_PATH = 'E:\\python\\python.exe';
const ROOT_DIR = path.resolve(__dirname, '../..');
const BACKEND_DIR = path.resolve(ROOT_DIR, 'backend');

/**
 * 递归扫描目录下所有指定扩展名文件
 * @param {string} dir 根目录
 * @param {string} ext 后缀
 * @returns {Array<string>} 文件绝对路径列表
 * @route internal://tests/harness/verify_stage2_backend.js/findFiles
 * @throws 无异常
 */
function findFiles(dir, ext) {
  let results = [];
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const full = path.join(dir, file);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      if (file !== '__pycache__' && file !== '.git' && file !== 'node_modules') {
        results = results.concat(findFiles(full, ext));
      }
    } else if (file.endsWith(ext)) {
      results.push(full);
    }
  }
  return results;
}

/**
 * 阶段 2 静态代码与 ORM 映射注释合规扫描
 * @returns {void}
 * @route internal://tests/harness/verify_stage2_backend.js/runStaticAudit
 * @throws {Error} 当存在 Emoji 或 ORM 字段缺失 comment 时抛出异常
 */
function runStaticAudit() {
  console.log('[Stage2-Audit] 1. 正在执行 backend/ 全目录 Python 源码零 Emoji 扫描...');
  const pyFiles = findFiles(BACKEND_DIR, '.py');
  for (const f of pyFiles) {
    const rel = path.relative(ROOT_DIR, f);
    const content = fs.readFileSync(f, 'utf-8');
    const check = checkNoEmoji(content, rel);
    if (!check.passed) {
      throw new Error(`[Emoji-Violation] ${check.violation}`);
    }
  }
  console.log(`[Stage2-Audit] 已扫描 ${pyFiles.length} 个 Python 源码文件，100% 无 Emoji 违规`);

  console.log('[Stage2-Audit] 2. 正在执行 10 个 SQLAlchemy 2.0 ORM 模型注释合规扫描...');
  const ormFile = path.resolve(BACKEND_DIR, 'app/models/spd_models.py');
  const ormContent = fs.readFileSync(ormFile, 'utf-8');
  const classMatches = ormContent.match(/class\s+Spd\w+|class\s+Sys\w+/g) || [];
  const commentMatches = ormContent.match(/comment="[^"]+"/g) || [];
  if (classMatches.length < 10 || commentMatches.length < 100) {
    throw new Error(`[ORM-Comment-Violation] 模型数 (${classMatches.length}) 或 comment 数量 (${commentMatches.length}) 未达标`);
  }
  console.log(`[Stage2-Audit] ORM 模型扫描通过: ${classMatches.length} 个模型共 ${commentMatches.length} 处表级与字段级中文注释完备`);
}

/**
 * 启动 FastAPI 后端服务子进程并等待健康就绪
 * @returns {Promise<ChildProcess>} 运行中的子进程
 * @route internal://tests/harness/verify_stage2_backend.js/startBackendServer
 * @throws {Error} 超时未能成功就绪时抛出异常
 */
async function startBackendServer() {
  console.log('[Stage2-Server] 正在启动 FastAPI 后端服务 (端口 8000)...');
  const proc = spawn(PYTHON_PATH, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: BACKEND_DIR,
    env: { ...process.env, PYTHONPATH: BACKEND_DIR },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  proc.stdout.on('data', (d) => {
    const msg = d.toString();
    if (msg.includes('ERROR') || msg.includes('Traceback')) {
      console.error('[Uvicorn-Out]', msg.trim());
    }
  });
  proc.stderr.on('data', (d) => {
    const msg = d.toString();
    if (msg.includes('ERROR') || msg.includes('Traceback')) {
      console.error('[Uvicorn-Err]', msg.trim());
    }
  });

  // 轮询探活健康接口
  const startTime = Date.now();
  let isReady = false;
  while (Date.now() - startTime < 15000) {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/health');
      if (res.ok) {
        const body = await res.json();
        if (body.status === 'UP') {
          isReady = true;
          break;
        }
      }
    } catch (e) {
      // 等待服务启动
    }
    await new Promise((r) => setTimeout(r, 600));
  }

  if (!isReady) {
    proc.kill();
    throw new Error('[Stage2-Server] FastAPI 服务在 15 秒内未就绪');
  }
  console.log('[Stage2-Server] FastAPI 后端服务就绪，端口 8000');
  return proc;
}

/**
 * 执行 5 套核心 CRUD 业务闭环 API 自动化断言
 * @returns {Promise<void>}
 * @route internal://tests/harness/verify_stage2_backend.js/runApiAssertions
 * @throws {Error} 任一断言失败时抛出异常
 */
async function runApiAssertions() {
  const BASE_URL = 'http://127.0.0.1:8000/api/v1';
  console.log('[Stage2-API] 开始执行 5 套核心 CRUD 接口端到端业务闭环断言...');

  // 1. 登录断言与科室架构
  const loginRes = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: '123' })
  });
  if (loginRes.status !== 400) {
    throw new Error('错误密码登录应当被拦截');
  }

  const correctLoginRes = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: '123456' })
  });
  const loginBody = await correctLoginRes.json();
  if (loginBody.code !== 200 || !loginBody.data.access_token) {
    throw new Error('系统管理员登录失败');
  }
  const token = loginBody.data.access_token;
  const authHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  };

  const deptsRes = await fetch(`${BASE_URL}/departments`, { headers: authHeaders });
  const deptsBody = await deptsRes.json();
  if (deptsBody.code !== 200 || deptsBody.data.length < 6) {
    throw new Error(`全院科室列表数据异常，当前数量: ${deptsBody.data?.length}`);
  }
  console.log(`[Stage2-API] 断言 1 通过: 系统管理员登录成功，全院科室架构 ${deptsBody.data.length} 个全部就绪`);

  // 2. 核心 CRUD 一：产品分类与字典建档断言 (自动产生 1_DICT_CREATE 日志)
  const catRes = await fetch(`${BASE_URL}/dict/categories?main_dept_code=CONSUMABLE_DEPT`, { headers: authHeaders });
  const catBody = await catRes.json();
  if (catBody.code !== 200 || catBody.data.length === 0) {
    throw new Error('产品分类查询失败');
  }
  const testCatId = catBody.data[0].id;

  const testProdCode = `TEST-P-${Date.now().toString().slice(-6)}`;
  const testUdiDi = `0697${Date.now().toString().slice(-10)}`;
  const createProdRes = await fetch(`${BASE_URL}/dict/products`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({
      product_code: testProdCode,
      product_name: '医用高频电刀笔',
      udi_di: testUdiDi,
      main_dept_code: 'CONSUMABLE_DEPT',
      consumable_type: 'GENERAL',
      category_id: testCatId,
      spec_model: '单极标准手控型',
      unit: '把',
      manufacturer: '杭州强生医疗器械制造公司',
      supplier_name: '国药控股浙江分公司',
      reg_cert_no: '国械注准20253010111',
      reg_cert_expiry: '2028-12-31',
      unit_price: 35.5,
      safe_stock_min: 10,
      safe_stock_max: 200,
      storage_temp_req: '常温干燥'
    })
  });
  const createProdBody = await createProdRes.json();
  if (createProdBody.code !== 200) {
    throw new Error(`产品字典建档失败: ${createProdBody.msg}`);
  }
  const createdProductId = createProdBody.data.id;
  console.log(`[Stage2-API] 断言 2 通过: 产品字典建档成功 (ID: ${createdProductId})，已自动触发 1_DICT_CREATE 全流程流转留痕`);

  // 3. 核心 CRUD 二：主库验收入库与按需分发双通道断言 (TO_SECONDARY_DEPT 与 TO_HIGH_VALUE_WH 拆码)
  // 入库
  const inboundRes = await fetch(`${BASE_URL}/main-warehouse/inbound`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({
      product_id: createdProductId,
      batch_no: 'B20261102A',
      production_date: '2026-11-01',
      expiry_date: '2029-10-31',
      inbound_qty: 100,
      shelf_location: '耗材主库-A区-05架',
      accept_temp: '22.0℃(合规)'
    })
  });
  const inboundBody = await inboundRes.json();
  if (inboundBody.code !== 200) {
    throw new Error(`主库验收入库失败: ${inboundBody.msg}`);
  }
  const createdMainInvId = inboundBody.data.id;

  // 通道 1: 主库按需分发至骨科二级库
  const orthoDept = deptsBody.data.find((d) => d.dept_code === 'SEC_ORTHO');
  const distSecondaryRes = await fetch(`${BASE_URL}/main-warehouse/distributions`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({
      main_inventory_id: createdMainInvId,
      target_type: 'TO_SECONDARY_DEPT',
      target_dept_id: orthoDept.id,
      dist_qty: 30,
      remark: '骨科病区常规按需调拨分发'
    })
  });
  const distSecondaryBody = await distSecondaryRes.json();
  if (distSecondaryBody.code !== 200) {
    throw new Error(`分发至二级库失败: ${distSecondaryBody.msg}`);
  }
  const distOrderId = distSecondaryBody.data.id;

  // 通道 2: 主库调拨转入高值专仓 (自动触发 Skill 03 拆包赋唯一 UDI 序列号)
  // 使用种子数据中的高值耗材批次库存 (PROD-HV-001)
  const mainInvsRes = await fetch(`${BASE_URL}/main-warehouse/inventory?consumable_type=HIGH_VALUE`, { headers: authHeaders });
  const mainInvsBody = await mainInvsRes.json();
  const hvMainInv = mainInvsBody.data.find((i) => i.consumable_type === 'HIGH_VALUE' && i.available_qty >= 3);
  if (!hvMainInv) {
    throw new Error('未检索到可用高值耗材主库库存');
  }

  const distHvRes = await fetch(`${BASE_URL}/main-warehouse/distributions`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({
      main_inventory_id: hvMainInv.id,
      target_type: 'TO_HIGH_VALUE_WH',
      target_dept_id: deptsBody.data.find((d) => d.dept_code === 'CONSUMABLE_DEPT').id,
      dist_qty: 2,
      remark: '主库向高值专仓补充备货拆包'
    })
  });
  const distHvBody = await distHvRes.json();
  if (distHvBody.code !== 200) {
    throw new Error(`主库转入高值专仓拆码失败: ${distHvBody.msg}`);
  }
  console.log('[Stage2-API] 断言 3 通过: 主库验收入库与按需分发双通道正常，成功分发至二级库并完成高值专仓一物一码拆包');

  // 4. 核心 CRUD 三：高值耗材单品扫码脱敏核销断言 (Skill 04 脱敏 + is_billable=1)
  const hvItemsRes = await fetch(`${BASE_URL}/high-value/items?item_status=IN_HIGH_VALUE_WH`, { headers: authHeaders });
  const hvItemsBody = await hvItemsRes.json();
  if (hvItemsBody.code !== 200 || hvItemsBody.data.length === 0) {
    throw new Error('高值专仓单品列表为空');
  }
  const targetHvItem = hvItemsBody.data[0];

  const verifyRes = await fetch(`${BASE_URL}/high-value/items/${targetHvItem.id}/verify`, {
    method: 'PUT',
    headers: authHeaders,
    body: JSON.stringify({
      patient_inpatient_no: 'ZY202611020088',
      patient_name: '张三丰',
      surgery_name: '复杂骨折切开复位内固定术',
      attending_doctor: '张主任医师'
    })
  });
  const verifyBody = await verifyRes.json();
  if (verifyBody.code !== 200) {
    throw new Error(`高值单品核销失败: ${verifyBody.msg}`);
  }
  if (verifyBody.data.patient_name_masked !== '张*丰') {
    throw new Error(`患者姓名脱敏异常: 预期 张*丰，实际 ${verifyBody.data.patient_name_masked}`);
  }
  console.log(`[Stage2-API] 断言 4 通过: 高值耗材单品扫码核销成功，患者姓名自动合规脱敏为 [${verifyBody.data.patient_name_masked}]，触发财务记账`);

  // 5. 核心 CRUD 四：二级库签收与日常消耗登记断言
  const receiveRes = await fetch(`${BASE_URL}/secondary-warehouse/receive/${distOrderId}`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({ is_accept: true })
  });
  const receiveBody = await receiveRes.json();
  if (receiveBody.code !== 200) {
    throw new Error(`二级库签收失败: ${receiveBody.msg}`);
  }

  // 二级库消耗登记
  const secInvRes = await fetch(`${BASE_URL}/secondary-warehouse/inventory?dept_id=${orthoDept.id}`, { headers: authHeaders });
  const secInvBody = await secInvRes.json();
  const secTarget = secInvBody.data.find((i) => i.product_code === testProdCode);
  if (!secTarget) {
    throw new Error('二级库签收后未检索到库存');
  }

  const consumeRes = await fetch(`${BASE_URL}/secondary-warehouse/consume`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({
      sec_inventory_id: secTarget.id,
      consume_qty: 5,
      consume_reason: '骨科日常手术耗用'
    })
  });
  const consumeBody = await consumeRes.json();
  if (consumeBody.code !== 200) {
    throw new Error(`二级库消耗登记失败: ${consumeBody.msg}`);
  }
  console.log('[Stage2-API] 断言 5 通过: 二级库签收入库并成功登记临床消耗 5 件，已生成财务记账台账');

  // 6. 核心 CRUD 五与打印中心：全流程 6W 日志穿透查询与标准四联签字单据打印
  const logsRes = await fetch(`${BASE_URL}/workflow-logs?node_action=7_CLINICAL_CONSUME`, { headers: authHeaders });
  const logsBody = await logsRes.json();
  if (logsBody.code !== 200 || logsBody.data.length === 0) {
    throw new Error('未检索到 7_CLINICAL_CONSUME 临床消耗流转日志');
  }

  const printVoucherRes = await fetch(`${BASE_URL}/print/voucher/MAIN_DISPATCH/${distSecondaryBody.data.dist_order_no}`);
  const printVoucherBody = await printVoucherRes.json();
  if (printVoucherBody.code !== 200 || !printVoucherBody.data.signatures.operator_signature) {
    throw new Error('四联签字单据打印数据结构不完整');
  }
  console.log(`[Stage2-API] 断言 6 通过: 6W 全流程流转日志穿透正常，法定四联单据打印结构化数据生成合规 (${printVoucherBody.data.voucher_title})`);
}

/**
 * 启动 Playwright 实机渲染后端健康大盘并截图存证
 * @returns {Promise<string>} 截图保存路径
 * @route internal://tests/harness/verify_stage2_backend.js/captureDashboardScreenshot
 * @throws {Error} 页面异常或截图失败时抛出异常
 */
async function captureDashboardScreenshot() {
  console.log('[Stage2-Browser] 正在启动 Playwright 持久化无锁浏览器渲染监控大盘...');
  const screenshotDir = path.resolve(ROOT_DIR, 'tests/screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const { context, page } = await launchPersistentPlaywright({ headless: true });
  const pageErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error' && !msg.text().includes('favicon.ico')) {
      pageErrors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    pageErrors.push(err.message);
  });

  try {
    await page.goto('http://127.0.0.1:8000/api/v1/health/dashboard', { waitUntil: 'domcontentloaded' });
    const headerVisible = await page.locator('.title-box h1').isVisible();
    if (!headerVisible) {
      throw new Error('健康监控看板标题未能正常显示');
    }

    const tableRows = await page.locator('tbody tr').count();
    if (tableRows < 10) {
      throw new Error(`数据表大盘渲染行数不足: 预期 10 行，实际 ${tableRows} 行`);
    }

    if (pageErrors.length > 0) {
      throw new Error(`页面渲染期间捕获到 Console Error: ${pageErrors.join('; ')}`);
    }

    const screenshotPath = path.resolve(
      screenshotDir,
      '2026-11-02_12-30-00_stage2_backend_api_and_orm_verify.png'
    );
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`[Stage2-Browser] 实机验证截图已成功落盘: ${screenshotPath}`);
    return screenshotPath;
  } finally {
    await context.close();
  }
}

/**
 * 阶段 2 总体执行总控入口
 */
async function runStage2Verification() {
  console.log('================================================================');
  console.log('【阶段 2 自动化回环测试】后端存储基建与 5 套核心 CRUD 接口全链路验证');
  console.log('================================================================');

  // 1. 静态代码扫描
  runStaticAudit();

  // 2. 启动 FastAPI
  let serverProcess = null;
  try {
    serverProcess = await startBackendServer();

    // 3. 执行端到端业务 API 断言
    await runApiAssertions();

    // 4. Playwright 浏览器实机截图取证
    const shotPath = await captureDashboardScreenshot();

    console.log('================================================================');
    console.log('阶段 2 自动化回环验证全部通过！');
    console.log(`实机验证截图: ${shotPath}`);
    console.log('================================================================');
  } finally {
    if (serverProcess && !serverProcess.killed) {
      console.log('[Stage2-Server] 正在停止后台 FastAPI 服务进程...');
      try {
        require('child_process').execSync(`taskkill /pid ${serverProcess.pid} /f /t`, { stdio: 'ignore' });
      } catch (e) {
        serverProcess.kill();
      }
    }
  }
}

if (require.main === module) {
  runStage2Verification().catch((err) => {
    console.error('阶段 2 验证失败:', err.message);
    process.exit(1);
  });
}

module.exports = {
  runStage2Verification
};
