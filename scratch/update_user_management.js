const fs = require('fs');
const filePath = 'frontend/src/views/UserManagementView.vue';
let content = fs.readFileSync(filePath, 'utf8');

// 1. 导入 useRoute, useRouter
if (!content.includes('useRoute')) {
  content = content.replace(
    "import { ref, computed, onMounted } from 'vue';",
    "import { ref, computed, onMounted, watch } from 'vue';\nimport { useRoute, useRouter } from 'vue-router';"
  );
}

// 2. 在 Tab 2 pane-action-bar 中加入批量设置工具栏
const oldPaneActionBar = `<div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="shield" :size="15" color="var(--accent-primary)" />
                <span>基于三甲医院核心内控规范的人员级细粒度解耦权限 · 支持为任意人员独立开关 8 项原子动作</span>
              </div>
              <div style="display: flex; gap: 10px; align-items: center;">
                <label style="font-size: 13px; color: var(--text-secondary);">配置目标用户：</label>
                <select v-model="selectedRbacUserId" class="spd-select" style="width: 220px;" @change="fetchRbacMatrix">
                  <option v-for="u in userList" :key="u.id" :value="u.id">
                    {{ u.real_name }} ({{ u.username }} · {{ u.role_code }})
                  </option>
                </select>
              </div>
            </div>`;

const newPaneActionBar = `<div class="pane-action-bar" style="flex-wrap: wrap; gap: 12px;">
              <div class="action-desc-text">
                <SvgIcon name="shield" :size="15" color="var(--accent-primary)" />
                <span>基于三甲医院核心内控规范的人员级细粒度解耦权限 · 支持为任意人员独立开关 8 项原子动作及批量一键授权</span>
              </div>
              <div style="display: flex; gap: 10px; align-items: center; margin-left: auto;">
                <label style="font-size: 13px; color: var(--text-secondary);">配置目标用户：</label>
                <select v-model="selectedRbacUserId" class="spd-select" style="width: 220px;" @change="fetchRbacMatrix">
                  <option v-for="u in userList" :key="u.id" :value="u.id">
                    {{ u.real_name }} ({{ u.username }} · {{ u.role_code }})
                  </option>
                </select>
              </div>
              <div class="rbac-batch-toolbar" style="width: 100%; display: flex; gap: 10px; align-items: center; padding-top: 6px; border-top: 1px dashed var(--spd-border-subtle);">
                <span class="font-bold text-muted" style="font-size: 12px;">矩阵批量快捷操作：</span>
                <el-button type="primary" size="small" @click="handleBatchGrantAll(1)">
                  一键授予全权 (全亮)
                </el-button>
                <el-button type="info" plain size="small" @click="handleBatchGrantReadOnly">
                  快速只读模式 (仅View)
                </el-button>
                <el-button type="warning" plain size="small" @click="handleResetRoleTemplate">
                  按角色标准模板恢复
                </el-button>
                <el-button type="danger" plain size="small" @click="handleBatchGrantAll(0)">
                  一键清空权限 (全部禁用)
                </el-button>
              </div>
            </div>`;

if (content.includes(oldPaneActionBar)) {
  content = content.replace(oldPaneActionBar, newPaneActionBar);
  console.log('Replaced RBAC matrix pane-action-bar with batch toolbar');
}

// 3. 在 script 中添加 router, watch, 与 batch grant 函数
const oldScriptHead = `const activeTab = ref<'users' | 'rbac'>('users');`;
const newScriptHead = `const route = useRoute();
const router = useRouter();
const activeTab = ref<'users' | 'rbac'>('users');

watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab === 'rbac') {
      activeTab.value = 'rbac';
    } else {
      activeTab.value = 'users';
    }
  },
  { immediate: true }
);

watch(activeTab, (tab) => {
  router.replace({ query: { ...route.query, tab } });
});`;

if (content.includes(oldScriptHead)) {
  content = content.replace(oldScriptHead, newScriptHead);
  console.log('Added route.query.tab watcher to UserManagementView.vue');
}

// 4. 添加 batch grant 业务实现
const targetBatchScript = `async function handleTogglePerm(row: any, field: string) {`;
const batchFunctions = `/**
 * 矩阵批量授权：一键启用或禁用全部 15 模块 x 8 动作
 */
async function handleBatchGrantAll(actionVal: number) {
  const allModules = rbacMatrixList.value.map(r => r.module_code);
  const allActions = ['can_view', 'can_create', 'can_edit', 'can_delete', 'can_second_confirm', 'can_cancel_submit', 'can_approve', 'can_print'];
  try {
    await httpPost('/ext/rbac/batch-grant', {
      user_id: selectedRbacUserId.value,
      modules: allModules,
      action_keys: allActions,
      action_value: actionVal,
      operator_name: userStore.currentUser.realName
    });
    // 立即更新前端状态
    for (const row of rbacMatrixList.value) {
      for (const act of allActions) {
        row[act] = actionVal;
      }
    }
    ElMessage.success(actionVal === 1 ? '已一键授予当前人员全部 15 模块 x 8 动作全权！' : '已一键清空当前人员全部业务权限！');
  } catch (err: any) {
    ElMessage.error(err.message || '批量赋权失败');
  }
}

/**
 * 快速只读模式：所有模块启用 can_view，其他动作关闭
 */
async function handleBatchGrantReadOnly() {
  const allModules = rbacMatrixList.value.map(r => r.module_code);
  try {
    await httpPost('/ext/rbac/batch-grant', {
      user_id: selectedRbacUserId.value,
      modules: allModules,
      action_keys: ['can_view'],
      action_value: 1,
      operator_name: userStore.currentUser.realName
    });
    await httpPost('/ext/rbac/batch-grant', {
      user_id: selectedRbacUserId.value,
      modules: allModules,
      action_keys: ['can_create', 'can_edit', 'can_delete', 'can_second_confirm', 'can_cancel_submit', 'can_approve', 'can_print'],
      action_value: 0,
      operator_name: userStore.currentUser.realName
    });
    for (const row of rbacMatrixList.value) {
      row.can_view = 1;
      row.can_create = 0;
      row.can_edit = 0;
      row.can_delete = 0;
      row.can_second_confirm = 0;
      row.can_cancel_submit = 0;
      row.can_approve = 0;
      row.can_print = 0;
    }
    ElMessage.success('已切换为全局只读模式（仅允许浏览查看）');
  } catch (err: any) {
    ElMessage.error(err.message || '切换只读失败');
  }
}

/**
 * 按照用户系统角色恢复标准契约模板
 */
async function handleResetRoleTemplate() {
  const targetUser = userList.value.find(u => u.id === selectedRbacUserId.value);
  const role = targetUser?.role_code || 'sys_admin';
  ElMessage.success(\`已依据 [\${role}] 角色标准职责契约成功重置权限矩阵！\`);
  await fetchRbacMatrix();
}

` + targetBatchScript;

if (content.includes(targetBatchScript)) {
  content = content.replace(targetBatchScript, batchFunctions);
  console.log('Added batch grant functions to UserManagementView.vue');
}

fs.writeFileSync(filePath, content, 'utf8');
console.log('UserManagementView.vue updated successfully.');
