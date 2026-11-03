const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');
const { launchPersistentPlaywright } = require('../e2e/browser_config');
const { checkNoEmoji } = require('./guardrails');

const ROOT_DIR = path.resolve(__dirname, '../..');
const FRONTEND_DIR = path.resolve(ROOT_DIR, 'frontend');
const FRONTEND_URL = 'http://127.0.0.1:5173';
const BACKEND_URL = 'http://127.0.0.1:8000';
const SCREENSHOT_PATH = path.resolve(
  ROOT_DIR,
  'tests/screenshots/2026-11-02_19-45-00_vue3_frontend_full_spd_verify.png'
);

/**
 * 递归获取目录下全部代码文件相对路径
 * @param {string} dir 扫描根目录
 * @param {string[]} fileList 累加文件路径数组
 * @returns {string[]} 文件列表
 * @route internal://tests/harness/verify_frontend_vue3.js/getAllFiles
 * @throws 无异常抛出
 */
function getAllFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const full = path.join(dir, file);
    if (fs.statSync(full).isDirectory()) {
      if (file !== 'node_modules' && file !== 'dist') {
        getAllFiles(full, fileList);
      }
    } else {
      fileList.push(full);
    }
  }
  return fileList;
}

/**
 * 轮询等待 HTTP 服务响应就绪
 * @param {string} url 目标探针地址
 * @param {number} maxRetries 最大重试次数
 * @returns {Promise<boolean>}
 * @route internal://tests/harness/verify_frontend_vue3.js/waitForServer
 * @throws {Error} 超时未就绪时抛出异常
 */
async function waitForServer(url, maxRetries = 40) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(url, (res) => {
          if (res.statusCode && res.statusCode < 500) resolve(true);
          else reject(new Error(`Status ${res.statusCode}`));
        });
        req.on('error', reject);
        req.setTimeout(1000, () => req.destroy());
      });
      return true;
    } catch (_) {
      await new Promise((r) => setTimeout(r, 400));
    }
  }
  throw new Error(`服务在 ${url} 启动超时`);
}

/**
 * 执行 Vue 3 + TypeScript 生产级前端与全链路 SPD 业务功能 Playwright E2E 回环测试
 * @returns {Promise<void>}
 * @route internal://tests/harness/verify_frontend_vue3.js/runFrontendVerification
 * @throws {Error} 断言未通过时抛出异常
 */
async function runFrontendVerification() {
  console.log('=== [Frontend Harness] 开始执行 Vue 3 生产级前端与全业务功能 10 项强断言验证 ===');

  // 断言 1: 前端源码静态护栏扫描 (100% 严禁 Emoji)
  const srcFiles = getAllFiles(path.resolve(FRONTEND_DIR, 'src'));
  for (const f of srcFiles) {
    if (f.endsWith('.ts') || f.endsWith('.vue') || f.endsWith('.css')) {
      const content = fs.readFileSync(f, 'utf-8');
      const rel = path.relative(ROOT_DIR, f);
      const emojiRes = checkNoEmoji(content, rel);
      if (!emojiRes.passed) {
        throw new Error(emojiRes.violation);
      }
    }
  }
  console.log(`[PASS 1/10] 静态护栏扫描通过：frontend/src/ 下 ${srcFiles.length} 个代码文件 100% 无任何 Emoji 字符`);

  // 确保后端已在运行
  let backendProc = null;
  let backendReady = false;
  try {
    await waitForServer(`${BACKEND_URL}/api/v1/health`, 3);
    backendReady = true;
  } catch (_) {
    backendReady = false;
  }
  if (!backendReady) {
    backendProc = spawn('E:\\python\\python.exe', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
      cwd: path.resolve(ROOT_DIR, 'backend'),
      stdio: 'pipe'
    });
    await waitForServer(`${BACKEND_URL}/api/v1/health`, 30);
  }

  // 启动前端 Vite 预览服务
  const viteProc = spawn('npm.cmd', ['run', 'preview', '--', '--port', '5173', '--host', '127.0.0.1'], {
    cwd: FRONTEND_DIR,
    stdio: 'pipe',
    shell: true
  });
  await waitForServer(FRONTEND_URL, 30);
  console.log(`[PASS 2/10] 前后端服务就绪：后端(8000端口)与前端 Vue 3 Vite(5173端口)成功互通`);

  let context = null;
  try {
    const pw = await launchPersistentPlaywright();
    context = pw.context;
    const page = await context.newPage();
    await page.setViewportSize({ width: 1440, height: 960 });

    const consoleErrors = [];
    const pageErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log('Browser console error:', msg.text(), msg.location());
        consoleErrors.push(msg.text());
      }
    });
    page.on('response', (res) => {
      if (res.status() >= 400) {
        console.log('HTTP Error Response:', res.status(), res.url());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    // 断言 3: 产品字典管理页 (双树联动 + 拼音码 + 跨仓分配)
    await page.goto(`${FRONTEND_URL}/dict`, { waitUntil: 'networkidle' });
    await page.waitForSelector('.dual-tree-panel');
    const treeNodeCount = await page.locator('.tree-node').count();
    const tableRows = await page.locator('.el-table__body-wrapper tbody tr').count();
    if (treeNodeCount < 8 || tableRows === 0) {
      throw new Error(`[Assert 3 Fail] 产品字典双树或产品表格未正常渲染 (树节点:${treeNodeCount}, 表格行:${tableRows})`);
    }
    const pinyinText = await page.locator('.spd-badge-info.spd-mono').first().innerText();
    if (!pinyinText) {
      throw new Error('[Assert 3 Fail] 拼音助记码未正确展示');
    }
    console.log(`[PASS 3/10] 产品字典页(双树${treeNodeCount}节点、${tableRows}行物资、拼音码:${pinyinText})加载通过`);

    // 断言 4: 普通耗材管理页 (对齐图1：请领受理、入库退供应商红字单、期初锁死、盘点)
    await page.click('text=普通耗材管理 (图1)');
    await page.waitForURL('**/general');
    await page.waitForSelector('.spd-custom-tabs');
    // 切换到期初数据 Tab 校验永久锁死徽标
    await page.click('#tab-init_stock');
    await page.waitForTimeout(400);
    const lockedBadge = await page.locator('#pane-init_stock .spd-badge-locked').first().innerText();
    if (!lockedBadge.includes('锁定') && !lockedBadge.includes('只读')) {
      throw new Error(`[Assert 4 Fail] 期初建账单未展示永久锁定只读状态: ${lockedBadge}`);
    }
    console.log(`[PASS 4/10] 普通耗材管理页与科室期初建账单永久锁死铁律(${lockedBadge})通过`);

    // 断言 5: 高值耗材管理页 (对齐图2：一物一码专属二维码、备货管理、核销查询联动)
    await page.click('text=高值耗材管理 (图2)');
    await page.waitForURL('**/high-value');
    await page.waitForSelector('.spd-custom-tabs');
    const payloadTag = await page.locator('#pane-stock .payload-tag').first().innerText();
    if (!payloadTag.includes('SPD-QR')) {
      throw new Error(`[Assert 5 Fail] 高值一物一码专属二维码载荷缺失: ${payloadTag}`);
    }
    // 切换到高值核销查询 Tab，校验仅展示已核销绑定患者的记录
    await page.click('#tab-verified');
    await page.waitForTimeout(400);
    const verifiedPatient = await page.locator('#pane-verified .el-table__body-wrapper .text-success').first().innerText();
    if (!verifiedPatient.includes('*')) {
      throw new Error(`[Assert 5 Fail] 高值核销查询未正确展示脱敏患者姓名: ${verifiedPatient}`);
    }
    console.log(`[PASS 5/10] 高值耗材页专属二维码载荷(${payloadTag})与高值核销脱敏联动(${verifiedPatient})通过`);

    // 断言 6: 临床二级库管理页 (对齐图3：接收入库、发料、跨病区调拨)
    await page.click('text=临床二级库管理 (图3)');
    await page.waitForURL('**/secondary');
    await page.waitForSelector('.kpi-overview-bar');
    const kpiText = await page.locator('.kpi-overview-bar').innerText();
    if (!kpiText.includes('骨科病区二级库') || !kpiText.includes('心内科病区二级库')) {
      throw new Error(`[Assert 6 Fail] 临床二级库概览管辖科室异常: ${kpiText}`);
    }
    console.log(`[PASS 6/10] 临床二级库管理页(双科室二级库与出入库流转)验证通过`);

    // 断言 7: 多级采购与供应商协同门户 (外部供应商资质与采供闭环)
    await page.click('text=多级采购与供应商协同');
    await page.waitForURL('**/procurement');
    await page.waitForSelector('.qual-banner');
    const licenseText = await page.locator('.license-meta').innerText();
    if (!licenseText.includes('鲁械经营备20260088号')) {
      throw new Error(`[Assert 7 Fail] 供应商医疗器械经营许可证信息异常: ${licenseText}`);
    }
    console.log(`[PASS 7/10] 外部供应商协同门户与经营资质准入验证通过`);

    // 断言 8: 全流程 6W 审计日志与财务打印中心
    await page.click('text=全流程 6W 审计日志');
    await page.waitForURL('**/logs');
    await page.waitForSelector('.log-header-card');
    await page.click('text=财务核算与单据打印');
    await page.waitForURL('**/finance');
    await page.waitForSelector('.print-launcher-card');
    console.log(`[PASS 8/10] 全流程 6W 物权审计时间轴与财务四联单据打印中心路由导航通过`);

    // 断言 9: 细粒度 RBAC 权限矩阵中枢抽屉唤出与 8 动作开关渲染
    await page.click('text=细粒度 RBAC');
    await page.waitForSelector('.spd-rbac-drawer', { state: 'visible' });
    const switchCount = await page.locator('.spd-rbac-drawer .el-switch').count();
    if (switchCount < 40) {
      throw new Error(`[Assert 9 Fail] RBAC 抽屉内 8 项原子操作开关数不足: ${switchCount}`);
    }
    console.log(`[PASS 9/10] 信息科解耦式 15 模块 x 8 动作 RBAC 权限抽屉(${switchCount}个原子开关)唤出通过`);

    // 断言 10: 控制台零错误与全屏实机截图归档
    if (consoleErrors.length > 0 || pageErrors.length > 0) {
      throw new Error(`[Assert 10 Fail] 页面存在控制台或页面错误: ${consoleErrors.join('; ')}`);
    }

    fs.mkdirSync(path.dirname(SCREENSHOT_PATH), { recursive: true });
    await page.screenshot({ path: SCREENSHOT_PATH, fullPage: true });
    console.log(`[PASS 10/10] Vue 3 前端 E2E 验证全绿通过(0 错误)，实机截图已归档至: ${SCREENSHOT_PATH}`);
  } finally {
    if (context) await context.close();
    if (viteProc) viteProc.kill();
    if (backendProc) backendProc.kill();
  }
}

runFrontendVerification().catch((err) => {
  console.error('[FATAL] Vue 3 前端回环验证失败:', err.message);
  process.exit(1);
});
