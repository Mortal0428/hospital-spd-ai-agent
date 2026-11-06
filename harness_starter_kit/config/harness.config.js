const path = require('path');

/**
 * Harness 质量护栏与自检套件全局可配置参数
 * 在新项目中套用时，仅需根据当前项目的实际物理目录调整此配置文件
 */
module.exports = {
  // 待扫描与自检的目标目录（套件自测默认为套件目录自身，套用到新项目时可指定为工程根目录）
  projectRoot: process.env.HARNESS_ROOT ? path.resolve(process.env.HARNESS_ROOT) : path.resolve(__dirname, '..'),

  // 扫描忽略的目录名单
  ignoreDirs: [
    'node_modules',
    'venv',
    '.git',
    '.agents',
    'dist',
    'screenshots',
    'archive',
    '__pycache__'
  ],

  // 质量护栏检查开关
  guardrails: {
    // 全域禁用 Emoji 检查（建议始终开启）
    noEmoji: true,
    // 敏感凭证与 API Key 泄露检查（建议始终开启）
    noSecrets: true,
    // 数据库 ORM 模型与 100% 注释契约检查（根据项目是否含数据库按需开启）
    ormComments: true,
    // 四大物理目录拓扑隔离合规检查
    architectureIsolation: true
  },

  // 物理目录配置（新工程按需映射实际路径）
  directories: {
    frontend: 'frontend',
    backend: 'backend',
    tests: 'tests',
    plans: 'plans',
    screenshots: 'tests/screenshots'
  },

  // 核心规范文件清单（runner.js 启动时校验完整性）
  specFiles: [
    { relPath: 'GEMINI.md', role: 'AI 代理核心执行铁律与防错契约' },
    { relPath: 'AGENTS.md', role: '研发子 Agent 专业化分工契约' },
    { relPath: 'HARNESS_PITFALLS_AND_LESSONS.md', role: '全栈防踩坑高危反模式与防退化军规' },
    { relPath: 'core/guardrails.js', role: '合规静态扫描引擎' },
    { relPath: 'core/browser.js', role: '无锁持久化 Playwright 浏览器驱动' }
  ],

  // 浏览器与 Playwright 配置
  browser: {
    headless: true,
    channel: 'msedge', // 可选 'msedge' 或 'chromium'
    viewport: { width: 1440, height: 900 }
  }
};
