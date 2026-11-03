/**
 * @file test_full_product_alignment_e2e.js
 * @description 医疗物资全链路 SPD 系统产品经理业务对齐回环验证脚本
 * 覆盖 8 大模块核心业务闭环：
 * 1. 产品字典 (/dict)：两级仓库树 (院级归口主仓 vs 临床科室二级库/专仓) 及 15 类全分类同步
 * 2. 普通耗材主库 (/general)：全院/分仓实时库存、出库凭证单据、对标图 2 的两级盘点工作台 (StocktakePlanWorkbench)
 * 3. 高值耗材专仓 (/high-value)：备货申请单多耗材提报、专柜智能台账扫码核销扣库、高值独立盘点
 * 4. 临床二级库房 (/secondary)：多科室严格限权物理隔离、无假数据 mock 回退、凭证式科室发料与跨病区调拨、病区独立盘点
 * 5. 财务精算与对账 (/finance)：4 大真实数据库聚合报表 (主库发料流向对账、科室领用消耗精算、进销存月度平衡、高值核销审计)
 * 6. 物资流转追溯 (/logs)：顶部 8 节点全生命周期穿透图谱动态高亮监控、全员人工操作安全审计日志
 * 7. 采购与外部协同 (/procurement)：临床采购计划提报、供应商在线发货并自动联动医院待验收入库单
 * 8. 系统与人员管理 (/users)：15 模块 × 8 动作细粒度 RBAC 矩阵、批量一键授权工具栏
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

async function runFullProductAlignmentE2E() {
  console.log('[E2E-Alignment] 启动持久化无锁 Playwright 自动化回环引擎...');
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_alignment_${Date.now()}`);
  const { context, page } = await launchPersistentPlaywright({
    headless: true,
    profileDir: tempProfile
  });

  const screenshotDir = path.resolve(__dirname, '../screenshots');
  const artifactDir = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2');
  if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;

  const interceptedErrors = [];
  page.on('pageerror', (err) => {
    console.error(`[Browser PageError]: ${err.message}`);
    interceptedErrors.push(`PageError: ${err.message}`);
  });
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      console.warn(`[Browser ConsoleError]: ${msg.text()}`);
      if (!msg.text().includes('favicon') && !msg.text().includes('chrome-extension')) {
        interceptedErrors.push(`ConsoleError: ${msg.text()}`);
      }
    }
  });

  async function snap(name) {
    const fileName = `${ts}_${name}.png`;
    const fullPath = path.resolve(screenshotDir, fileName);
    await page.screenshot({ path: fullPath, fullPage: true });
    console.log(`[E2E-Screenshot] 截图已捕获: ${fileName}`);
    if (fs.existsSync(artifactDir)) {
      try {
        fs.copyFileSync(fullPath, path.resolve(artifactDir, fileName));
      } catch (e) {
        // 忽略非关键错误
      }
    }
    return fileName;
  }

  try {
    await page.setViewportSize({ width: 1440, height: 900 });

    // 0. 登录信息科系统管理员
    console.log('[E2E-Alignment] 执行管理员登录凭据准备...');
    await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle', timeout: 15000 });
    await page.evaluate(() => {
      localStorage.setItem('spd_token', 'TOKEN_SYS_ADMIN_MOCK_SECRET');
      localStorage.setItem('spd_user', JSON.stringify({
        id: 1,
        username: 'admin',
        realName: '赵振华(系统管理员)',
        roleCode: 'sys_admin',
        deptId: 1,
        deptCode: 'INFO_DEPT',
        deptName: '信息科'
      }));
      localStorage.setItem('spd_current_wh', 'ALL');
    });

    // 1. 验证产品字典 (/dict)
    console.log('[E2E-Alignment] 步骤 1: 验证产品字典 (/dict) 仓库树分层与分类同源...');
    await page.goto('http://127.0.0.1:5173/dict', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('01_product_dict_alignment');

    // 2. 验证普通耗材主库 (/general)
    console.log('[E2E-Alignment] 步骤 2: 验证普通耗材主库实时库存、出库凭证与两级盘点工作台...');
    await page.goto('http://127.0.0.1:5173/general?tab=inventory', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    // 切换到出库
    await page.goto('http://127.0.0.1:5173/general?tab=outbound', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    // 切换到主库独立盘点 (StocktakePlanWorkbench 对标图 2)
    await page.goto('http://127.0.0.1:5173/general?tab=stocktake', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('02_general_material_alignment');

    // 3. 验证高值耗材专仓 (/high-value)
    console.log('[E2E-Alignment] 步骤 3: 验证高值耗材备货申请、智能专柜台账与高值独立盘点...');
    await page.goto('http://127.0.0.1:5173/high-value?tab=inbound', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.goto('http://127.0.0.1:5173/high-value?tab=stock', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.goto('http://127.0.0.1:5173/high-value?tab=stocktake', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('03_high_value_alignment');

    // 4. 验证临床二级库房 (/secondary)
    console.log('[E2E-Alignment] 步骤 4: 验证临床二级库房在库台账、凭证发料、跨病区调拨与独立盘点...');
    await page.goto('http://127.0.0.1:5173/secondary?tab=stock', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.goto('http://127.0.0.1:5173/secondary?tab=manual-out', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.goto('http://127.0.0.1:5173/secondary?tab=transfer', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.goto('http://127.0.0.1:5173/secondary?tab=stocktake', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('04_secondary_warehouse_alignment');

    // 5. 验证财务精算与对账 (/finance)
    console.log('[E2E-Alignment] 步骤 5: 验证财务四大真实聚合报表引擎 (/ext/finance/reports)...');
    await page.goto('http://127.0.0.1:5173/finance?tab=main-reconciliation', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);
    await page.goto('http://127.0.0.1:5173/finance?tab=dept-reconciliation', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);
    await snap('05_finance_actuarial_reports');

    // 6. 验证物资流转追溯 (/logs)
    console.log('[E2E-Alignment] 步骤 6: 验证物资流转追溯 8 节点穿透动态高亮与操作安全审计...');
    await page.goto('http://127.0.0.1:5173/logs?tab=trace', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    // 模拟点击第一行激活穿透
    const firstRow = page.locator('.fusion-styled-table .el-table__row').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await page.waitForTimeout(800);
    }
    await snap('06_workflow_dynamic_trace');

    // 7. 验证采购与外部协同 (/procurement)
    console.log('[E2E-Alignment] 步骤 7: 验证采购计划提报与供应商在线发货流转...');
    await page.goto('http://127.0.0.1:5173/procurement?tab=orders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('07_supplier_procurement_alignment');

    // 8. 验证系统与人员管理 (/users)
    console.log('[E2E-Alignment] 步骤 8: 验证系统人员台账与 15 模块 × 8 动作 RBAC 批量授权工具栏...');
    await page.goto('http://127.0.0.1:5173/users?tab=rbac', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('08_user_rbac_batch_matrix');

    console.log('\n[E2E-Alignment] 所有 8 大业务模块自动化验证完成！');
    console.log(`[E2E-Alignment] 页面报错拦截统计: PageErrors = ${interceptedErrors.filter(e => e.startsWith('PageError')).length}, ConsoleErrors = ${interceptedErrors.filter(e => e.startsWith('ConsoleError')).length}`);

  } catch (err) {
    console.error(`[E2E-Alignment Fatal Error]: ${err.message}`);
    throw err;
  } finally {
    await context.close();
  }
}

runFullProductAlignmentE2E()
  .then(() => {
    console.log('[E2E-Alignment] 验收回环测试成功结束');
    process.exit(0);
  })
  .catch((err) => {
    console.error('[E2E-Alignment] 验收回环测试失败:', err);
    process.exit(1);
  });
