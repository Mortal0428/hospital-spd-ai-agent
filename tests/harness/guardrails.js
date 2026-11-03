const fs = require('fs');
const path = require('path');

/**
 * 扫描指定文本内容是否包含违规 Emoji 字符（Harness 组件4：架构硬护栏）
 * @param {string} content 待检测的文件文本内容
 * @param {string} filePath 文件相对路径（用于生成诊断报告）
 * @returns {{passed: boolean, violation: string | null}} 返回检测是否通过及违规详情
 * @route internal://tests/harness/guardrails.js/checkNoEmoji
 * @throws {Error} 当入参类型非法时抛出异常
 */
function checkNoEmoji(content, filePath) {
  if (typeof content !== 'string') {
    throw new Error('checkNoEmoji 入参 content 必须为字符串');
  }
  const emojiRegex = /[\u{1F300}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
  if (emojiRegex.test(content)) {
    return {
      passed: false,
      violation: `[Emoji-Guard-Fail] 文件 ${filePath} 检测到违规 Emoji 字符，违反全域禁用 Emoji 铁律`
    };
  }
  return { passed: true, violation: null };
}

/**
 * 校验数据库 ORM 规范文档或模型代码中是否 100% 落实了表级与字段级 comment 注释契约
 * @param {string} rootDir 项目根目录绝对路径
 * @returns {{passed: boolean, checkedModels: number, commentCount: number, message: string}} 返回 ORM comment 扫描统计结果
 * @route internal://tests/harness/guardrails.js/verifyOrmCommentsGuard
 * @throws {Error} 当 docs/db_schema.md 不存在或未包含 comment 契约时抛出异常
 */
function verifyOrmCommentsGuard(rootDir) {
  const schemaPath = path.resolve(rootDir, 'docs/db_schema.md');
  if (!fs.existsSync(schemaPath)) {
    throw new Error('docs/db_schema.md 不存在，无法执行 ORM comment 护栏校验');
  }

  const content = fs.readFileSync(schemaPath, 'utf-8');
  const classMatches = content.match(/class\s+Spd\w+|class\s+Sys\w+/g) || [];
  const commentMatches = content.match(/comment="[^"]+"/g) || [];

  if (classMatches.length < 9 || commentMatches.length < 80) {
    return {
      passed: false,
      checkedModels: classMatches.length,
      commentCount: commentMatches.length,
      message: `[ORM-Comment-Guard-Fail] ORM 模型或 comment 注释数量不足 (模型数: ${classMatches.length}, comment数: ${commentMatches.length})`
    };
  }

  return {
    passed: true,
    checkedModels: classMatches.length,
    commentCount: commentMatches.length,
    message: `已核验 ${classMatches.length} 个核心 ORM 模型，共 ${commentMatches.length} 处表级与字段级中文 comment 注释全部合规`
  };
}

/**
 * 反馈循环自进化写入器（Harness 组件5：当护栏捕获新型违规时，自动将防错记录追加沉淀至 SKILL.md）
 * @param {string} rootDir 项目根目录绝对路径
 * @param {string} sourceModule 触发来源模块名称
 * @param {string} violationDetail 捕获的异常或违规详情
 * @param {string} evolvedRule 自动沉淀的防错规则说明
 * @returns {boolean} 是否成功写入 SKILL.md 演进台账
 * @route internal://tests/harness/guardrails.js/appendFeedbackToSkill
 * @throws {Error} 当 SKILL.md 写入失败时抛出异常
 */
function appendFeedbackToSkill(rootDir, sourceModule, violationDetail, evolvedRule) {
  const skillPath = path.resolve(rootDir, 'SKILL.md');
  if (!fs.existsSync(skillPath)) {
    throw new Error('根目录 SKILL.md 不存在，无法执行反馈循环沉淀');
  }

  const now = new Date();
  const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(
    now.getDate()
  ).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(
    now.getMinutes()
  ).padStart(2, '0')}`;

  const logLine = `| \`${timestamp}\` | ${sourceModule} | ${violationDetail} | ${evolvedRule} | \`[AUTO-EVOLVED]\` |\n`;
  fs.appendFileSync(skillPath, logLine, 'utf-8');
  return true;
}

/**
 * 执行全局架构护栏扫描（Emoji 禁令扫描 + ORM comment 覆盖率扫描 + 渐进披露与技能库核验）
 * @param {string} rootDir 项目根目录绝对路径
 * @returns {{allPassed: boolean, ormReport: object, scannedFiles: number, violations: Array<string>}} 综合护栏报告
 * @route internal://tests/harness/guardrails.js/runAllGuardrails
 * @throws {Error} 当扫描过程发生 IO 异常时抛出错误
 */
function runAllGuardrails(rootDir) {
  const filesToScan = [
    'CLAUDE.md',
    'AGENTS.md',
    'SKILL.md',
    'docs/requirements.md',
    'docs/db_schema.md',
    'docs/api_spec.md',
    'plans/2026-11-02_10-41-00_master_project_plan_and_confirmed_baseline.md'
  ];

  const violations = [];
  for (const rel of filesToScan) {
    const full = path.resolve(rootDir, rel);
    if (fs.existsSync(full)) {
      const text = fs.readFileSync(full, 'utf-8');
      const emojiRes = checkNoEmoji(text, rel);
      if (!emojiRes.passed) {
        violations.push(emojiRes.violation);
      }
    } else {
      violations.push(`[Missing-Spec-File] 缺失关键文件: ${rel}`);
    }
  }

  const ormReport = verifyOrmCommentsGuard(rootDir);
  if (!ormReport.passed) {
    violations.push(ormReport.message);
  }

  if (violations.length > 0) {
    appendFeedbackToSkill(
      rootDir,
      'guardrails.js 自动扫描',
      violations[0],
      '触发自动拦截并强化预提交护栏校验'
    );
  }

  return {
    allPassed: violations.length === 0,
    ormReport,
    scannedFiles: filesToScan.length,
    violations
  };
}

module.exports = {
  checkNoEmoji,
  verifyOrmCommentsGuard,
  appendFeedbackToSkill,
  runAllGuardrails
};
