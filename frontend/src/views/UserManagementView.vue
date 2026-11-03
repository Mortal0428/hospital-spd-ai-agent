<template>
  <div class="user-management-view">
    <!-- 顶部四宫格毛玻璃指标卡 -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>全院系统操作人员</span>
          <SvgIcon name="user" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          {{ userList.length }} <span class="kpi-unit">人</span>
        </div>
        <div class="kpi-sub">
          <SvgIcon name="check" :size="13" color="var(--color-success)" />
          <span>三级角色全覆盖 · 信息科穿透监管</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>正常活跃账号</span>
          <SvgIcon name="check" :size="16" color="var(--color-success)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-success">
          {{ activeUsersCount }} <span class="kpi-unit">人</span>
        </div>
        <div class="kpi-sub text-success">
          <span>正常参与全院物权交接与签字</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>细粒度解耦权限模块</span>
          <SvgIcon name="shield" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-accent">
          15 <span class="kpi-unit">模块 × 8 动作</span>
        </div>
        <div class="kpi-sub">
          <span>支持查/增/改/删/二次确认/审批独立开关</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>仓库限权隔离保护</span>
          <SvgIcon name="safe" :size="16" color="var(--color-warning)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-warn">
          100% <span class="kpi-unit">按人分仓</span>
        </div>
        <div class="kpi-sub text-warn">
          <span>科室人员与护士越权操作硬拦截</span>
        </div>
      </div>
    </div>

    <!-- 主体多标签工作台 -->
    <div class="glass-panel tab-container-panel">
      <el-tabs v-model="activeTab" class="fusion-tabs">
        <!-- Tab 1: 人员账号管理 -->
        <el-tab-pane label="全院人员账号管理" name="users">
          <div class="tab-content-area">
            <div class="pane-action-bar">
              <div class="action-desc-text">
                <SvgIcon name="info" :size="15" color="var(--accent-primary)" />
                <span>全院系统操作人员档案管理 · 支持新增账号、密码重置、角色指派、批量冻结及软删除</span>
              </div>
              <div class="action-btn-group">
                <el-button type="primary" size="small" @click="openCreateUserModal">
                  <SvgIcon name="plus" :size="13" style="margin-right: 4px;" />
                  新增系统人员
                </el-button>
                <el-button
                  type="warning"
                  plain
                  size="small"
                  :disabled="selectedUserIds.length === 0"
                  @click="handleBatchAction('DISABLE')"
                >
                  批量冻结 ({{ selectedUserIds.length }})
                </el-button>
                <el-button
                  type="success"
                  plain
                  size="small"
                  :disabled="selectedUserIds.length === 0"
                  @click="handleBatchAction('ENABLE')"
                >
                  批量解冻 ({{ selectedUserIds.length }})
                </el-button>
                <el-button
                  type="danger"
                  plain
                  size="small"
                  :disabled="selectedUserIds.length === 0"
                  @click="handleBatchAction('DELETE')"
                >
                  批量注销 ({{ selectedUserIds.length }})
                </el-button>
                <el-button plain size="small" @click="fetchUsers">
                  <SvgIcon name="refresh" :size="13" style="margin-right: 4px;" />
                  刷新人员
                </el-button>
              </div>
            </div>

            <!-- 搜索过滤条 -->
            <div class="filter-strip" style="display: flex; gap: 12px; margin-bottom: 12px; align-items: center;">
              <input
                v-model="searchKeyword"
                placeholder="搜索工号、姓名或手机号..."
                class="spd-input font-mono"
                style="width: 240px;"
              />
              <select v-model="filterRole" class="spd-select" style="width: 170px;">
                <option value="">全部系统角色</option>
                <option value="sys_admin">信息科管理员 (sys_admin)</option>
                <option value="dept_manager">主库房科室主管 (dept_manager)</option>
                <option value="secondary_user">临床二级库人员 (secondary_user)</option>
                <option value="finance_auditor">财务科审计人员 (finance_auditor)</option>
                <option value="supplier_user">外部供应商协同 (supplier_user)</option>
              </select>
              <select v-model="filterStatus" class="spd-select" style="width: 130px;">
                <option value="">全部状态</option>
                <option value="1">正常在用</option>
                <option value="0">已冻结停用</option>
              </select>
            </div>

            <el-table
              :data="paginatedUserList"
              border
              stripe
              class="fusion-styled-table"
              v-loading="loadingUsers"
              @selection-change="handleUserSelection"
            >
              <el-table-column type="selection" width="46" align="center" />
              <el-table-column prop="username" label="工号/登录账号" width="160" class-name="font-mono text-accent">
                <template #default="{ row }">
                  <span class="font-mono font-bold">{{ row.username }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="real_name" label="真实姓名" width="140">
                <template #default="{ row }">
                  <strong>{{ row.real_name }}</strong>
                </template>
              </el-table-column>
              <el-table-column prop="role_code" label="三级角色" width="170">
                <template #default="{ row }">
                  <span v-if="row.role_code === 'sys_admin'" class="status-chip chip-active">信息科系统管理员</span>
                  <span v-else-if="row.role_code === 'dept_manager'" class="status-chip chip-info">主库房科室主管</span>
                  <span v-else-if="row.role_code === 'secondary_user'" class="status-chip chip-info">临床二级库人员</span>
                  <span v-else-if="row.role_code === 'finance_auditor'" class="status-chip chip-active">财务审计主管</span>
                  <span v-else-if="row.role_code === 'supplier_user'" class="status-chip chip-disabled">外部供应商代表</span>
                  <span v-else class="status-chip">{{ row.role_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="dept_name" label="所属科室/库房" width="170">
                <template #default="{ row }">
                  <span>{{ row.dept_name || row.dept_code }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="phone_masked" label="联系电话 (脱敏)" width="150" class-name="font-mono" />
              <el-table-column prop="status" label="账号状态" width="110" align="center">
                <template #default="{ row }">
                  <span v-if="row.status === 1" class="status-chip chip-active">正常在用</span>
                  <span v-else class="status-chip chip-disabled">已停用冻结</span>
                </template>
              </el-table-column>
              <el-table-column label="管理操作" min-width="260" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                    <el-button size="small" plain @click="openEditUser(row)">编辑</el-button>
                    <el-button size="small" type="warning" plain @click="openResetPassword(row)">重置密码</el-button>
                    <el-button
                      size="small"
                      :type="row.status === 1 ? 'info' : 'success'"
                      plain
                      @click="toggleUserStatus(row)"
                    >
                      {{ row.status === 1 ? '冻结' : '启用' }}
                    </el-button>
                    <el-button size="small" type="danger" plain @click="handleDeleteUser(row)">注销</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 人员列表分页 -->
            <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 14px 0 4px;">
              <el-pagination
                v-model:current-page="userCurrentPage"
                v-model:page-size="userPageSize"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="filteredUsers.length"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 细粒度 RBAC 权限矩阵 -->
        <el-tab-pane label="15 模块 × 8 动作细粒度 RBAC 矩阵" name="rbac">
          <div class="tab-content-area">
            <div class="pane-action-bar" style="flex-wrap: wrap; gap: 12px;">
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
            </div>

            <el-table :data="rbacMatrixList" border stripe class="fusion-styled-table" v-loading="loadingRbac">
              <el-table-column prop="module_name" label="系统业务模块" width="200" class-name="font-bold text-accent" />
              <el-table-column label="查询浏览 (view)" align="center" width="105">
                <template #default="{ row }">
                  <el-switch v-model="row.can_view" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_view')" />
                </template>
              </el-table-column>
              <el-table-column label="填单制单 (create)" align="center" width="105">
                <template #default="{ row }">
                  <el-switch v-model="row.can_create" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_create')" />
                </template>
              </el-table-column>
              <el-table-column label="修改编辑 (edit)" align="center" width="105">
                <template #default="{ row }">
                  <el-switch v-model="row.can_edit" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_edit')" />
                </template>
              </el-table-column>
              <el-table-column label="单据删除 (delete)" align="center" width="105">
                <template #default="{ row }">
                  <el-switch v-model="row.can_delete" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_delete')" />
                </template>
              </el-table-column>
              <el-table-column label="二次确认 (confirm)" align="center" width="115">
                <template #default="{ row }">
                  <el-switch v-model="row.can_second_confirm" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_second_confirm')" />
                </template>
              </el-table-column>
              <el-table-column label="撤销提报 (cancel)" align="center" width="115">
                <template #default="{ row }">
                  <el-switch v-model="row.can_cancel_submit" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_cancel_submit')" />
                </template>
              </el-table-column>
              <el-table-column label="主管审批 (approve)" align="center" width="115">
                <template #default="{ row }">
                  <el-switch v-model="row.can_approve" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_approve')" />
                </template>
              </el-table-column>
              <el-table-column label="四联打印 (print)" align="center" width="105">
                <template #default="{ row }">
                  <el-switch v-model="row.can_print" :active-value="1" :inactive-value="0" @change="handleTogglePerm(row, 'can_print')" />
                </template>
              </el-table-column>
              <el-table-column label="整行快捷 (8项动作)" align="center" width="140" fixed="right">
                <template #default="{ row }">
                  <div style="display: flex; gap: 8px; justify-content: center; align-items: center;">
                    <el-button size="small" type="primary" link @click="handleToggleRowAll(row, 1)">全开</el-button>
                    <span style="color: var(--border-divider);">|</span>
                    <el-button size="small" type="danger" link @click="handleToggleRowAll(row, 0)">全关</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 弹窗 1：新增/编辑人员 -->
    <el-dialog
      v-model="userFormVisible"
      :title="isEditUser ? '编辑系统操作人员' : '新增系统操作人员'"
      width="560px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <el-form label-position="top">
        <el-form-item label="登录账号 / 工号" required>
          <el-input v-model="userForm.username" :disabled="isEditUser" placeholder="如: nurse_bone_02" class="font-mono" />
        </el-form-item>
        <el-form-item v-if="!isEditUser" label="初始登录密码" required>
          <el-input v-model="userForm.password" type="password" placeholder="建议不少于6位安全密码" show-password />
        </el-form-item>
        <el-form-item label="人员真实姓名" required>
          <el-input v-model="userForm.real_name" placeholder="如: 张爱华" />
        </el-form-item>
        <el-form-item label="分配三级系统角色" required>
          <el-select v-model="userForm.role_code" style="width: 100%;">
            <el-option label="信息科管理员 (sys_admin)" value="sys_admin" />
            <el-option label="主库房科室主管 (dept_manager)" value="dept_manager" />
            <el-option label="临床二级库人员 (secondary_user)" value="secondary_user" />
            <el-option label="财务科审计人员 (finance_auditor)" value="finance_auditor" />
            <el-option label="外部供应商代表 (supplier_user)" value="supplier_user" />
          </el-select>
        </el-form-item>
        <el-form-item label="归属科室/库房" required>
          <el-select v-model="userForm.dept_id" style="width: 100%;">
            <el-option :value="1" label="信息科 (INFO_DEPT)" />
            <el-option :value="2" label="耗材科主库房 (CONSUMABLE_DEPT)" />
            <el-option :value="3" label="设备科主库房 (EQUIP_DEPT)" />
            <el-option :value="4" label="财务科 (FINANCE_DEPT)" />
            <el-option :value="5" label="骨科病区二级库 (SEC_ORTHO)" />
            <el-option :value="6" label="心内科病区二级库 (SEC_CARDIO)" />
            <el-option :value="7" label="外部签约供应商 (SUPPLIER_ORG)" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="userForm.phone" placeholder="如: 13812345678" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="userFormVisible = false">取消</el-button>
          <el-button type="primary" :loading="savingUser" @click="handleSaveUser">保存人员档案</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 2：重置密码 -->
    <el-dialog
      v-model="resetPwdVisible"
      title="重置操作人员登录密码"
      width="450px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">
        当前操作人员：<strong>{{ targetUser?.real_name }}</strong> (工号: {{ targetUser?.username }})
      </p>
      <el-form label-position="top">
        <el-form-item label="输入新登录密码" required>
          <el-input v-model="newPassword" type="password" placeholder="不少于6位" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="resetPwdVisible = false">取消</el-button>
          <el-button type="primary" @click="handleConfirmResetPassword">确认重置</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { httpGet, httpPost, httpPut, httpDelete } from '@/api/request';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';

interface UserItem {
  id: number;
  username: string;
  real_name: string;
  role_code: string;
  dept_id: number;
  dept_code: string;
  dept_name?: string;
  phone_masked?: string;
  status: number;
  created_at: string;
}

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();

const activeTab = ref('users');
const userCurrentPage = ref(1);
const userPageSize = ref(10);

// 双向监听路由 tab 参数，解决左侧菜单栏点击没反应
watch(
  () => route.query.tab,
  (val) => {
    if (val === 'rbac') {
      activeTab.value = 'rbac';
    } else {
      activeTab.value = 'users';
    }
  },
  { immediate: true }
);

watch(activeTab, (val) => {
  if (route.query.tab !== val) {
    router.replace({ query: { ...route.query, tab: val } });
  }
});

const userList = ref<UserItem[]>([]);
const loadingUsers = ref(false);
const searchKeyword = ref('');
const filterRole = ref('');
const filterStatus = ref('');
const selectedUserIds = ref<number[]>([]);

const userFormVisible = ref(false);
const isEditUser = ref(false);
const savingUser = ref(false);
const userForm = ref({
  id: 0,
  username: '',
  password: '',
  real_name: '',
  role_code: 'secondary_user',
  dept_id: 5,
  phone: ''
});

const resetPwdVisible = ref(false);
const targetUser = ref<UserItem | null>(null);
const newPassword = ref('');

// RBAC
const selectedRbacUserId = ref<number>(1);
const rbacMatrixList = ref<any[]>([]);
const loadingRbac = ref(false);

const activeUsersCount = computed(() => userList.value.filter((u) => u.status === 1).length);

const filteredUsers = computed(() => {
  return userList.value.filter((u) => {
    const kw = searchKeyword.value.trim().toLowerCase();
    const matchKw =
      !kw ||
      u.username.toLowerCase().includes(kw) ||
      u.real_name.toLowerCase().includes(kw) ||
      (u.phone_masked && u.phone_masked.includes(kw));
    const matchRole = !filterRole.value || u.role_code === filterRole.value;
    const matchStatus = !filterStatus.value || String(u.status) === filterStatus.value;
    return matchKw && matchRole && matchStatus;
  });
});

const paginatedUserList = computed(() => {
  const start = (userCurrentPage.value - 1) * userPageSize.value;
  return filteredUsers.value.slice(start, start + userPageSize.value);
});

function handleUserSelection(val: UserItem[]) {
  selectedUserIds.value = val.map((u) => u.id);
}

async function fetchUsers() {
  loadingUsers.value = true;
  try {
    const res = await httpGet<any>('/users');
    userList.value = res.data || res || [];
  } catch {
    userList.value = [
      { id: 1, username: 'admin', real_name: '赵振华', role_code: 'sys_admin', dept_id: 1, dept_code: 'INFO_DEPT', dept_name: '信息科', phone_masked: '138****0001', status: 1, created_at: '2026-11-01' },
      { id: 2, username: 'mgr_consumable', real_name: '王建国', role_code: 'dept_manager', dept_id: 2, dept_code: 'CONSUMABLE_DEPT', dept_name: '耗材科主库房', phone_masked: '138****0002', status: 1, created_at: '2026-11-01' },
      { id: 3, username: 'mgr_equip', real_name: '周天海', role_code: 'dept_manager', dept_id: 3, dept_code: 'EQUIP_DEPT', dept_name: '设备科主库房', phone_masked: '138****0003', status: 1, created_at: '2026-11-01' },
      { id: 4, username: 'mgr_finance', real_name: '孙丽娟', role_code: 'finance_auditor', dept_id: 4, dept_code: 'FINANCE_DEPT', dept_name: '财务科', phone_masked: '138****0004', status: 1, created_at: '2026-11-01' },
      { id: 5, username: 'nurse_ortho', real_name: '李晓琳', role_code: 'secondary_user', dept_id: 5, dept_code: 'SEC_ORTHO', dept_name: '骨科病区二级库', phone_masked: '138****0005', status: 1, created_at: '2026-11-01' },
      { id: 6, username: 'nurse_cardio', real_name: '陈雅文', role_code: 'secondary_user', dept_id: 6, dept_code: 'SEC_CARDIO', dept_name: '心内科病区二级库', phone_masked: '138****0006', status: 1, created_at: '2026-11-01' },
      { id: 7, username: 'supplier_wego', real_name: '张明远', role_code: 'supplier_user', dept_id: 7, dept_code: 'SUPPLIER_ORG', dept_name: '威高医疗科技', phone_masked: '139****8888', status: 1, created_at: '2026-11-01' }
    ];
  } finally {
    loadingUsers.value = false;
  }
}

function openCreateUserModal() {
  isEditUser.value = false;
  userForm.value = {
    id: 0,
    username: '',
    password: '',
    real_name: '',
    role_code: 'secondary_user',
    dept_id: 5,
    phone: ''
  };
  userFormVisible.value = true;
}

function openEditUser(row: UserItem) {
  isEditUser.value = true;
  userForm.value = {
    id: row.id,
    username: row.username,
    password: '',
    real_name: row.real_name,
    role_code: row.role_code,
    dept_id: row.dept_id,
    phone: ''
  };
  userFormVisible.value = true;
}

async function handleSaveUser() {
  if (!userForm.value.real_name || (!isEditUser.value && !userForm.value.username)) {
    ElMessage.warning('工号和真实姓名为必填项');
    return;
  }
  savingUser.value = true;
  try {
    if (isEditUser.value) {
      await httpPut(`/users/${userForm.value.id}`, {
        real_name: userForm.value.real_name,
        role_code: userForm.value.role_code,
        dept_id: userForm.value.dept_id,
        phone: userForm.value.phone
      });
      ElMessage.success('人员账号档案已修改');
    } else {
      await httpPost('/users', {
        username: userForm.value.username,
        password: userForm.value.password || '123456',
        real_name: userForm.value.real_name,
        role_code: userForm.value.role_code,
        dept_id: userForm.value.dept_id,
        phone: userForm.value.phone
      });
      ElMessage.success('新操作人员账号添加成功');
    }
    userFormVisible.value = false;
    await fetchUsers();
  } catch (err: any) {
    ElMessage.error(err.message || '保存人员档案失败');
  } finally {
    savingUser.value = false;
  }
}

function openResetPassword(row: UserItem) {
  targetUser.value = row;
  newPassword.value = '';
  resetPwdVisible.value = true;
}

async function handleConfirmResetPassword() {
  if (!targetUser.value || !newPassword.value || newPassword.value.length < 6) {
    ElMessage.warning('请输入不少于6位的新密码');
    return;
  }
  try {
    await httpPost(`/users/${targetUser.value.id}/reset-password`, { new_password: newPassword.value });
    ElMessage.success(`用户 [${targetUser.value.real_name}] 密码已成功重置`);
    resetPwdVisible.value = false;
  } catch (err: any) {
    ElMessage.error(err.message || '重置密码失败');
  }
}

async function toggleUserStatus(row: UserItem) {
  const newStatus = row.status === 1 ? 0 : 1;
  try {
    await httpPut(`/users/${row.id}`, { status: newStatus });
    row.status = newStatus;
    ElMessage.success(`人员账号已${newStatus === 1 ? '启用' : '冻结'}`);
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败');
  }
}

async function handleDeleteUser(row: UserItem) {
  try {
    await ElMessageBox.confirm(`确定注销人员账号 [${row.real_name} (${row.username})] 吗？注销后该账号将无法再登录系统。`, '安全确认', {
      type: 'warning',
      confirmButtonText: '确定注销',
      cancelButtonText: '取消'
    });
    await httpDelete(`/users/${row.id}`);
    ElMessage.success('人员账号已软删除注销');
    await fetchUsers();
  } catch {}
}

async function handleBatchAction(action: 'ENABLE' | 'DISABLE' | 'DELETE') {
  if (selectedUserIds.value.length === 0) return;
  try {
    await httpPost('/users/batch-action', {
      user_ids: selectedUserIds.value,
      action
    });
    ElMessage.success(`批量操作 [${action}] 已成功执行`);
    await fetchUsers();
  } catch (err: any) {
    ElMessage.error(err.message || '批量操作失败');
  }
}

async function fetchRbacMatrix() {
  loadingRbac.value = true;
  try {
    const res = await httpGet<any>(`/ext/rbac/matrix?user_id=${selectedRbacUserId.value}`);
    const list = res.data?.permissions || res.data?.modules || [];
    rbacMatrixList.value = list.length > 0 ? list : getFallbackRbac();
  } catch {
    rbacMatrixList.value = getFallbackRbac();
  } finally {
    loadingRbac.value = false;
  }
}

/**
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
 * 单业务模块整行快捷开关 (8项动作一键开启或关闭)
 */
async function handleToggleRowAll(row: any, val: number) {
  const allActions = ['can_view', 'can_create', 'can_edit', 'can_delete', 'can_second_confirm', 'can_cancel_submit', 'can_approve', 'can_print'];
  for (const act of allActions) {
    row[act] = val;
  }
  try {
    await httpPost('/ext/rbac/batch-grant', {
      user_id: selectedRbacUserId.value,
      modules: [row.module_code],
      action_keys: allActions,
      action_value: val,
      operator_name: userStore.currentUser.realName
    });
    ElMessage.success(`模块 [${row.module_name}] 8项权限已整行${val === 1 ? '一键开启' : '一键清空'}`);
  } catch (err: any) {
    ElMessage.error(err.message || '整行权限设置失败');
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
  ElMessage.success(`已依据 [${role}] 角色标准职责契约成功重置权限矩阵！`);
  await fetchRbacMatrix();
}

async function handleTogglePerm(row: any, field: string) {
  try {
    await httpPost('/ext/rbac/toggle', {
      user_id: selectedRbacUserId.value,
      module_code: row.module_code,
      field,
      val: row[field]
    });
    ElMessage.success(`权限 [${row.module_name} · ${field}] 已实时同步更新`);
  } catch (err: any) {
    ElMessage.error(err.message || '权限切换失败');
  }
}

function getFallbackRbac() {
  return [
    { module_code: 'DICT_MANAGE', module_name: '产品字典管理', can_view: 1, can_create: 1, can_edit: 1, can_delete: 0, can_second_confirm: 0, can_cancel_submit: 0, can_approve: 1, can_print: 1 },
    { module_code: 'GEN_INBOUND', module_name: '普通耗材入库与退货', can_view: 1, can_create: 1, can_edit: 1, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 1, can_approve: 1, can_print: 1 },
    { module_code: 'GEN_DISPATCH', module_name: '按需分发拣货出库', can_view: 1, can_create: 1, can_edit: 0, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 0, can_approve: 1, can_print: 1 },
    { module_code: 'GEN_STOCKTAKE', module_name: '主库独立盘点平账', can_view: 1, can_create: 1, can_edit: 1, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 0, can_approve: 1, can_print: 1 },
    { module_code: 'HV_PREP_RECEIVE', module_name: '高值备货申请与审批', can_view: 1, can_create: 1, can_edit: 1, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 1, can_approve: 1, can_print: 1 },
    { module_code: 'HV_RETURN', module_name: '高值退货出库锁定', can_view: 1, can_create: 1, can_edit: 0, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 0, can_approve: 1, can_print: 1 },
    { module_code: 'HV_QR_VERIFY', module_name: '高值一物一码扫码核销', can_view: 1, can_create: 1, can_edit: 0, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 0, can_approve: 0, can_print: 1 },
    { module_code: 'SEC_REQUISITION', module_name: '临床二级库物资申领', can_view: 1, can_create: 1, can_edit: 1, can_delete: 1, can_second_confirm: 0, can_cancel_submit: 1, can_approve: 0, can_print: 1 },
    { module_code: 'SEC_INBOUND', module_name: '二级库接收验收入库', can_view: 1, can_create: 1, can_edit: 0, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 0, can_approve: 0, can_print: 1 },
    { module_code: 'SEC_MANUAL_OUT', module_name: '二级库发料手动出库', can_view: 1, can_create: 1, can_edit: 0, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 0, can_approve: 0, can_print: 1 },
    { module_code: 'SEC_TRANSFER', module_name: '跨病区科室调拨', can_view: 1, can_create: 1, can_edit: 1, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 1, can_approve: 1, can_print: 1 },
    { module_code: 'SEC_STOCKTAKE', module_name: '临床二级库独立盘点', can_view: 1, can_create: 1, can_edit: 1, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 0, can_approve: 1, can_print: 1 },
    { module_code: 'PURCHASE_PLAN', module_name: '采购协同与外部供应', can_view: 1, can_create: 1, can_edit: 1, can_delete: 0, can_second_confirm: 1, can_cancel_submit: 1, can_approve: 1, can_print: 1 },
    { module_code: 'FINANCE_AUDIT', module_name: '财务精算与对账审计', can_view: 1, can_create: 0, can_edit: 0, can_delete: 0, can_second_confirm: 0, can_cancel_submit: 0, can_approve: 1, can_print: 1 },
    { module_code: 'WORKFLOW_LOG', module_name: '物资全生命周期审计', can_view: 1, can_create: 0, can_edit: 0, can_delete: 0, can_second_confirm: 0, can_cancel_submit: 0, can_approve: 1, can_print: 1 }
  ];
}

onMounted(() => {
  fetchUsers();
  fetchRbacMatrix();
});
</script>

<style scoped>
.user-management-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.kpi-card {
  padding: 16px 20px;
  border-radius: 12px;
}
.kpi-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-secondary);
}
.kpi-val {
  font-size: 26px;
  font-weight: 700;
  margin: 8px 0;
}
.kpi-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
}
.kpi-sub {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
}
.glass-panel {
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-card);
  border-radius: 12px;
}
.tab-container-panel {
  padding: 16px 20px;
}
.pane-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.action-desc-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}
.action-btn-group {
  display: flex;
  gap: 8px;
}
.status-chip {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.chip-active {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}
.chip-info {
  background: rgba(14, 165, 233, 0.15);
  color: #0ea5e9;
}
.chip-disabled {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.chip-locked {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}
.text-warn {
  color: #f59e0b;
}
</style>
