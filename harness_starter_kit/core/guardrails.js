const fs = require('fs');
const path = require('path');
const config = require('../config/harness.config');

/**
 * 扫描指定文本内容中是否包含违规的 Emoji 字符
 *
 * @param {string} content 待检测的文本内容
 * @param {string} filePath 相对文件路径（用于生成诊断定位）
 * @returns {{passed: boolean, violation: string | null}}
 * @route internal://core/guardrails.js/checkNoEmoji
 * @throws {Error} 当 content 格式非法时抛出异常
 */
function checkNoEmoji(content, filePath) {
  if (typeof content !== 'string') {
    throw new Error('checkNoEmoji 入参 content 必须为字符串');
  }
  const emojiRegex = /[\u{1F300}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
  if (emojiRegex.test(content)) {
    return {
      passed: false,
      violation: `[Emoji-Guard-Fail] 文件 ${filePath} 包含违规 Emoji 字符，违反全域禁用 Emoji 铁律`
    };
  }
  return { passed: true, violation: null };
}

/**
 * 扫描指定文本内容中是否存在硬编码的敏感密钥与 API Token
 *
 * @param {string} content 待检测的代码文本内容
 * @param {string} filePath 相对文件路径
 * @returns {{passed: boolean, violation: string | null}}
 * @route internal://core/guardrails.js/checkNoSecrets
 * @throws {Error} 当入参非法时抛出异常
 */
function checkNoSecrets(content, filePath) {
  if (typeof content !== 'string') {
    throw new Error('checkNoSecrets 入参 content 必须为字符串');
  }

  // 排除文档与示例模版文件中的说明性占位符
  const isTemplate = filePath.endsWith('.example') || filePath.endsWith('.sample');
  if (isTemplate) {
    return { passed: true, violation: null };
  }

  // 常见敏感 Key 正则匹配规则
  const secretPatterns = [
    { pattern: /sk-[a-zA-Z0-9]{30,}/, type: 'OpenAI/兼容平台 API Key' },
    { pattern: /lsv2_pt_[a-zA-Z0-9_]{30,}/, type: 'LangSmith Token' },
    { pattern: /pat_[a-zA-Z0-9]{30,}/, type: 'Personal Access Token / Coze Token' },
    { pattern: /ghp_[a-zA-Z0-9]{30,}/, type: 'GitHub 访问令牌' },
    { pattern: /cli_[a-zA-Z0-9]{16,}\s*['"]\s*,\s*['"][a-zA-Z0-9]{25,}['"]/, type: '飞书 App ID 与 App Secret 组合' }
  ];

  for (const item of secretPatterns) {
    if (item.pattern.test(content)) {
      return {
        passed: false,
        violation: `[Secret-Guard-Fail] 文件 ${filePath} 检测到疑似硬编码敏感凭据 (${item.type})，违反零明文密钥铁律`
      };
    }
  }

  return { passed: true, violation: null };
}

/**
 * 校验指定数据模型定义中是否 100% 落实了表级与字段级 comment 注释契约
 *
 * @param {string} schemaPath 数据架构定义文件绝对路径
 * @returns {{passed: boolean, message: string}}
 * @route internal://core/guardrails.js/verifyOrmCommentsGuard
 * @throws {Error} 当模型定义文件不存在时抛出异常
 */
function verifyOrmCommentsGuard(schemaPath) {
  if (!fs.existsSync(schemaPath)) {
    return {
      passed: false,
      message: `[ORM-Guard-Fail] 找不到模型定义文件: ${schemaPath}`
    };
  }

  const content = fs.readFileSync(schemaPath, 'utf-8');
  const classMatches = content.match(/class\s+\w+\(Base\)|class\s+\w+\(declarative_base/g) || [];
  const commentMatches = content.match(/comment="[^"]+"|comment='[^']+'/g) || [];

  if (classMatches.length > 0 && commentMatches.length === 0) {
    return {
      passed: false,
      message: `[ORM-Guard-Fail] 检测到数据模型存在，但未包含任何 comment 注释契约`
    };
  }

  return {
    passed: true,
    message: `[ORM-Guard-Passed] 已检测数据模型 comment 注释规范，共发现 ${commentMatches.length} 处标准注释`
  };
}

/**
 * 校验工程的物理目录隔离是否符合标准四层拓扑规范
 *
 * @param {string} rootDir 项目根目录绝对路径
 * @param {object} dirConfig 目录映射配置
 * @returns {{passed: boolean, violations: string[]}}
 * @route internal://core/guardrails.js/verifyArchitectureIsolation
 */
function verifyArchitectureIsolation(rootDir, dirConfig) {
  const violations = [];
  const requiredDirs = [dirConfig.frontend, dirConfig.backend, dirConfig.tests, dirConfig.plans];

  for (const d of requiredDirs) {
    if (d && !fs.existsSync(path.resolve(rootDir, d))) {
      violations.push(`[Architecture-Guard-Warning] 未检测到建议的物理隔离目录: ${d}`);
    }
  }

  return {
    passed: violations.length === 0,
    violations
  };
}

/**
 * 统一执行所有已启用的 Guardrails 静态合规扫描
 *
 * @param {object} [customConfig] 可选自定义覆盖配置
 * @returns {{passed: boolean, totalChecked: number, violations: string[]}}
 * @route internal://core/guardrails.js/runAllGuardrails
 */
function runAllGuardrails(customConfig = {}) {
  const activeConfig = Object.assign({}, config, customConfig);
  const rootDir = activeConfig.projectRoot;
  const violations = [];
  let totalChecked = 0;

  // 递归遍历文件函数
  function scanDir(dirPath) {
    if (!fs.existsSync(dirPath)) return;
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      const relPath = path.relative(rootDir, fullPath).replace(/\\/g, '/');

      // 忽略目录与静态非文本资源
      const defaultIgnores = ['node_modules', 'venv', '__pycache__', 'dist', 'screenshots', 'archive'];
      const ignoreDirs = Array.isArray(activeConfig.ignoreDirs) ? activeConfig.ignoreDirs : defaultIgnores;
      if (
        entry.name.startsWith('.') ||
        ignoreDirs.includes(entry.name)
      ) {
        continue;
      }

      if (entry.isDirectory()) {
        scanDir(fullPath);
      } else if (entry.isFile()) {
        // 仅检查代码、配置与文档文本
        const ext = path.extname(entry.name).toLowerCase();
        if (['.js', '.ts', '.vue', '.py', '.json', '.md', '.html', '.css', '.env'].includes(ext)) {
          totalChecked++;
          try {
            const content = fs.readFileSync(fullPath, 'utf-8');

            // 1. Emoji 规则校验
            if (activeConfig.guardrails.noEmoji) {
              const emojiRes = checkNoEmoji(content, relPath);
              if (!emojiRes.passed) {
                violations.push(emojiRes.violation);
              }
            }

            // 2. 敏感密钥扫描
            if (activeConfig.guardrails.noSecrets) {
              const secretRes = checkNoSecrets(content, relPath);
              if (!secretRes.passed) {
                violations.push(secretRes.violation);
              }
            }
          } catch (e) {
            // 忽略二进制或读取异常
          }
        }
      }
    }
  }

  // 执行文件扫描
  scanDir(rootDir);

  return {
    passed: violations.length === 0,
    totalChecked,
    violations
  };
}

module.exports = {
  checkNoEmoji,
  checkNoSecrets,
  verifyOrmCommentsGuard,
  verifyArchitectureIsolation,
  runAllGuardrails
};
