const path = require('path');
const fs = require('fs');

/**
 * 动态加载并解析系统环境中可用的 Playwright 核心对象
 * 优先读取本地 node_modules，其次尝试全局与常见缓存路径
 *
 * @returns {object} Playwright 核心模块对象
 * @route internal://core/browser.js/resolvePlaywright
 * @throws {Error} 若未找到任何可用的 Playwright 运行时则抛出异常
 */
function resolvePlaywright() {
  try {
    return require('playwright');
  } catch (err) {
    const commonFallbackPaths = [
      'C:/Users/27705/.gemini/config/mcp-playwright/node_modules/playwright',
      path.resolve(__dirname, '../../node_modules/playwright')
    ];
    for (const fallback of commonFallbackPaths) {
      if (fs.existsSync(fallback)) {
        try {
          return require(fallback);
        } catch (e) {
          // 继续尝试下一个路径
        }
      }
    }
    throw new Error('[Browser-Resolve-Fail] 未能检测到 Playwright 依赖，请在套件目录下执行 npm install playwright');
  }
}

/**
 * 启动无锁持久化浏览器上下文（避免与用户正在运行的本地浏览器发生文件锁冲突）
 *
 * @param {object} [options={}] 启动配置选项
 * @param {boolean} [options.headless=true] 是否无头模式运行
 * @param {string} [options.channel='msedge'] 浏览器内核通道（推荐 'msedge' 或 'chromium'）
 * @param {string} [options.profileDir] 持久化数据隔离目录
 * @param {object} [options.viewport={width: 1440, height: 900}] 视口尺寸
 * @returns {Promise<{context: import('playwright').BrowserContext, page: import('playwright').Page}>}
 * @route internal://core/browser.js/launchHarnessBrowser
 * @throws {Error} 启动失败时抛出格式化异常
 */
async function launchHarnessBrowser(options = {}) {
  const { chromium } = resolvePlaywright();
  const isHeadless = options.headless !== undefined ? options.headless : true;
  const channel = options.channel || 'msedge';
  const viewport = options.viewport || { width: 1440, height: 900 };

  const defaultProfile = path.resolve(__dirname, '../.automation_profile');
  const profileDir = options.profileDir || defaultProfile;

  if (!fs.existsSync(profileDir)) {
    fs.mkdirSync(profileDir, { recursive: true });
  }

  try {
    const context = await chromium.launchPersistentContext(profileDir, {
      channel,
      headless: isHeadless,
      viewport,
      args: [
        '--no-default-browser-check',
        '--no-first-run',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--disable-popup-blocking'
      ]
    });

    const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();
    return { context, page };
  } catch (err) {
    // 降级机制：如果指定通道启动失败，尝试使用默认 chromium 启动
    if (channel !== 'chromium') {
      console.warn(`[Browser-Warning] 通道 ${channel} 启动失败，正在尝试降级为默认 chromium 启动:`, err.message);
      const context = await chromium.launchPersistentContext(profileDir, {
        headless: isHeadless,
        viewport,
        args: ['--no-first-run', '--disable-blink-features=AutomationControlled']
      });
      const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();
      return { context, page };
    }
    throw new Error(`[Browser-Launch-Fail] 无法启动持久化浏览器实例: ${err.message}`);
  }
}

module.exports = {
  resolvePlaywright,
  launchHarnessBrowser
};
