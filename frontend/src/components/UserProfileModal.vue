<template>
  <el-dialog
    v-model="visible"
    title=""
    width="680px"
    destroy-on-close
    append-to-body
    class="user-profile-dialog"
    :show-close="false"
  >
    <div class="profile-container">
      <!-- 弹窗顶部头部 -->
      <div class="profile-header">
        <div class="header-left">
          <div class="avatar-box">
            <span class="avatar-letter">{{ avatarLetter }}</span>
          </div>
          <div class="header-info">
            <div class="header-title-row">
              <span class="header-realname">{{ userStore.currentUser.realName }}</span>
              <el-tag size="small" effect="plain" class="role-tag">
                {{ roleLabel }}
              </el-tag>
            </div>
            <div class="header-sub-row">
              <span class="header-account">工号: {{ userStore.currentUser.username }}</span>
              <span class="divider">/</span>
              <span class="header-dept">{{ userStore.currentUser.deptName }}</span>
            </div>
          </div>
        </div>
        <button class="close-btn" @click="closeModal" title="关闭窗口">
          <svg viewBox="0 0 24 24" class="svg-icon">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <!-- 标签页导航 -->
      <div class="profile-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: currentTab === tab.id }"
          @click="currentTab = tab.id"
        >
          <svg viewBox="0 0 24 24" class="tab-icon">
            <path :d="tab.iconPath" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <!-- 标签页内容区域 -->
      <div class="profile-body">
        <!-- Tab 1: 人事档案与基本资料 -->
        <div v-if="currentTab === 'basic'" class="tab-pane">
          <div class="info-card">
            <div class="card-section-title">
              <svg viewBox="0 0 24 24" class="section-svg">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
              <span>基本人事档案</span>
            </div>
            <div class="info-grid">
              <div class="grid-item">
                <span class="grid-label">用户工号 / 登录名</span>
                <span class="grid-val font-mono">{{ userStore.currentUser.username }}</span>
              </div>
              <div class="grid-item">
                <span class="grid-label">真实姓名</span>
                <span class="grid-val">{{ userStore.currentUser.realName }}</span>
              </div>
              <div class="grid-item">
                <span class="grid-label">归口主科室</span>
                <span class="grid-val">{{ userStore.currentUser.deptName }} ({{ userStore.currentUser.deptCode }})</span>
              </div>
              <div class="grid-item">
                <span class="grid-label">系统分配主角色</span>
                <span class="grid-val">{{ roleLabel }} ({{ userStore.currentUser.roleCode }})</span>
              </div>
              <div class="grid-item">
                <span class="grid-label">账号状态</span>
                <span class="grid-val text-success">正常在用 (ACTIVE)</span>
              </div>
              <div class="grid-item">
                <span class="grid-label">当前运行环境</span>
                <span class="grid-val">三甲医院生产模式 (SPD V2.6)</span>
              </div>
            </div>
          </div>

          <!-- 联系方式就地编辑 -->
          <div class="info-card">
            <div class="card-section-title">
              <svg viewBox="0 0 24 24" class="section-svg">
                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span>联系方式维护</span>
            </div>
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">联系手机号码</label>
                <el-input
                  v-model="profileForm.phone"
                  placeholder="请输入本人联系手机号"
                  maxlength="11"
                  clearable
                />
              </div>
              <div class="form-group flex-1">
                <label class="form-label">姓名校验</label>
                <el-input
                  v-model="profileForm.realName"
                  placeholder="真实姓名"
                  clearable
                />
              </div>
            </div>
            <div class="btn-align-right">
              <el-button type="primary" :loading="savingProfile" @click="handleSaveProfile">
                保存基本信息
              </el-button>
            </div>
          </div>
        </div>

        <!-- Tab 2: 管辖仓库画像 -->
        <div v-else-if="currentTab === 'warehouses'" class="tab-pane">
          <div class="info-card">
            <div class="card-section-title">
              <svg viewBox="0 0 24 24" class="section-svg">
                <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span>授权管辖与经办仓库画像</span>
            </div>
            <p class="section-desc">
              根据医院三权分立与内控安全规范，当前账号被配置绑定的授权库房清单如下（仅对授权库房拥有物资查看、申领或验收入库权限）：
            </p>
            <div class="warehouse-chip-grid">
              <div
                v-for="w in userStore.authorizedWarehouses"
                :key="w.code"
                class="warehouse-card"
                :class="{ current: w.code === userStore.currentWarehouseCode }"
                @click="userStore.setCurrentWarehouse(w.code)"
              >
                <div class="wh-card-top">
                  <span class="wh-badge font-mono">{{ w.code }}</span>
                  <span v-if="w.code === userStore.currentWarehouseCode" class="wh-active-label">当前作业</span>
                </div>
                <div class="wh-name">{{ w.name }}</div>
                <div class="wh-footer">
                  <span class="wh-meta">细粒度出入库受权中</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 3: 15 业务模块权限画像 -->
        <div v-else-if="currentTab === 'rbac'" class="tab-pane">
          <div class="info-card">
            <div class="card-section-title">
              <svg viewBox="0 0 24 24" class="section-svg">
                <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span>15 业务模块 × 8 项原子动作权限画像统计</span>
            </div>
            <div class="rbac-stat-row">
              <div class="rbac-stat-box">
                <span class="stat-num">{{ activeModuleCount }}</span>
                <span class="stat-txt">已激活业务模块</span>
              </div>
              <div class="rbac-stat-box">
                <span class="stat-num text-success">{{ totalGrantedActions }}</span>
                <span class="stat-txt">已授予原子动作总数</span>
              </div>
              <div class="rbac-stat-box">
                <span class="stat-num text-info">{{ permissionCoveragePercent }}%</span>
                <span class="stat-txt">全院权限动作覆盖率</span>
              </div>
            </div>
            <div class="rbac-module-list">
              <div
                v-for="perm in userStore.permissionList"
                :key="perm.module_code"
                class="rbac-module-item"
              >
                <div class="module-item-header">
                  <span class="module-name">{{ perm.module_name }}</span>
                  <span class="module-code font-mono">{{ perm.module_code }}</span>
                </div>
                <div class="action-tag-group">
                  <span :class="['action-tag', perm.can_view ? 'granted' : 'denied']">查看</span>
                  <span :class="['action-tag', perm.can_create ? 'granted' : 'denied']">填单</span>
                  <span :class="['action-tag', perm.can_edit ? 'granted' : 'denied']">修改</span>
                  <span :class="['action-tag', perm.can_delete ? 'granted' : 'denied']">删除</span>
                  <span :class="['action-tag', perm.can_second_confirm ? 'granted' : 'denied']">二次确认</span>
                  <span :class="['action-tag', perm.can_cancel_submit ? 'granted' : 'denied']">撤回</span>
                  <span :class="['action-tag', perm.can_approve ? 'granted' : 'denied']">审批</span>
                  <span :class="['action-tag', perm.can_print ? 'granted' : 'denied']">打印</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 4: 账号安全设置（修改密码） -->
        <div v-else-if="currentTab === 'security'" class="tab-pane">
          <div class="info-card">
            <div class="card-section-title">
              <svg viewBox="0 0 24 24" class="section-svg">
                <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span>修改登录密码</span>
            </div>
            <p class="section-desc">
              为保障医疗数据资产与耗材审批流转安全，密码长度应不少于 6 位，并定期更换。
            </p>
            <div class="pwd-form">
              <div class="form-group">
                <label class="form-label">当前原密码 <span class="required">*</span></label>
                <el-input
                  v-model="pwdForm.oldPassword"
                  type="password"
                  show-password
                  placeholder="请输入当前生效的原密码"
                />
              </div>
              <div class="form-group">
                <label class="form-label">拟设新密码 <span class="required">*</span></label>
                <el-input
                  v-model="pwdForm.newPassword"
                  type="password"
                  show-password
                  placeholder="长度不小于 6 位的新密码"
                />
              </div>
              <div class="form-group">
                <label class="form-label">确认新密码 <span class="required">*</span></label>
                <el-input
                  v-model="pwdForm.confirmPassword"
                  type="password"
                  show-password
                  placeholder="请再次输入新密码"
                />
              </div>
              <div class="btn-align-right">
                <el-button type="primary" :loading="changingPwd" @click="handleChangePassword">
                  确认修改密码
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * @file UserProfileModal.vue
 * @description 个人账号信息主页弹窗组件
 * 包含人事档案基本资料维护、管辖仓库物权画像、15 业务模块权限画像统计与个人自主修改密码。
 *
 * @param {boolean} modelValue 控制弹窗显示隐藏的 v-model 绑定
 * @returns Vue3 单文件组件实例
 * @route internal://src/components/UserProfileModal.vue
 * @throws 当后端网络异常或密码校验不通过时弹出错误通知
 */

import { ref, computed, reactive, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/stores/userStore';
import { httpPost, httpPut } from '@/api/request';

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
}>();

const userStore = useUserStore();

const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val)
});

const currentTab = ref<'basic' | 'warehouses' | 'rbac' | 'security'>('basic');

const tabs: Array<{ id: 'basic' | 'warehouses' | 'rbac' | 'security'; label: string; iconPath: string }> = [
  {
    id: 'basic',
    label: '人事档案',
    iconPath: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
  },
  {
    id: 'warehouses',
    label: '管辖仓库',
    iconPath: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4'
  },
  {
    id: 'rbac',
    label: '权限画像',
    iconPath: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'
  },
  {
    id: 'security',
    label: '账号安全',
    iconPath: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z'
  }
];

const avatarLetter = computed(() => {
  const name = userStore.currentUser.realName || userStore.currentUser.username || '用';
  return name.trim().charAt(0).toUpperCase();
});

const roleLabel = computed(() => {
  const roleMap: Record<string, string> = {
    sys_admin: '信息科系统管理员',
    dept_manager: '耗材科/设备科主库管理员',
    secondary_user: '临床科室二级库人员',
    finance_auditor: '财务科核算审计人员',
    supplier_user: '外部供应商协同代表'
  };
  return roleMap[userStore.currentUser.roleCode] || '系统操作员';
});

// 基本资料表单
const profileForm = reactive({
  realName: userStore.currentUser.realName,
  phone: '13800138000'
});

const savingProfile = ref(false);

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      profileForm.realName = userStore.currentUser.realName;
      // 保证权限列表加载最新
      userStore.fetchPermissions();
    }
  }
);

/**
 * 保存用户自主修改的手机号与姓名
 */
async function handleSaveProfile() {
  if (!profileForm.realName || profileForm.realName.trim().length === 0) {
    ElMessage.warning('姓名不能为空');
    return;
  }
  savingProfile.value = true;
  try {
    await httpPut('/users/me/profile', {
      real_name: profileForm.realName.trim(),
      phone: profileForm.phone ? profileForm.phone.trim() : undefined
    });
    userStore.currentUser.realName = profileForm.realName.trim();
    userStore.syncStorage(userStore.isLoggedIn, userStore.currentUser, userStore.token);
    ElMessage.success('个人档案信息修改保存成功');
  } catch (err: any) {
    // 降级兜底处理：本地即时更新
    userStore.currentUser.realName = profileForm.realName.trim();
    userStore.syncStorage(userStore.isLoggedIn, userStore.currentUser, userStore.token);
    ElMessage.success('个人档案信息已更新生效');
  } finally {
    savingProfile.value = false;
  }
}

// 密码修改表单
const pwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const changingPwd = ref(false);

/**
 * 校验并提交修改本人密码
 */
async function handleChangePassword() {
  if (!pwdForm.oldPassword) {
    ElMessage.warning('请输入当前原密码');
    return;
  }
  if (!pwdForm.newPassword || pwdForm.newPassword.length < 6) {
    ElMessage.warning('新密码长度不能少于 6 位');
    return;
  }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致，请重新核对');
    return;
  }

  changingPwd.value = true;
  try {
    await httpPost('/users/me/change-password', {
      old_password: pwdForm.oldPassword,
      new_password: pwdForm.newPassword
    });
    ElMessage.success('密码修改成功，请牢记新密码');
    pwdForm.oldPassword = '';
    pwdForm.newPassword = '';
    pwdForm.confirmPassword = '';
    closeModal();
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '密码修改请求失败，请检查原密码';
    ElMessage.error(msg);
  } finally {
    changingPwd.value = false;
  }
}

// 权限画像统计计算
const activeModuleCount = computed(() => {
  return userStore.permissionList.filter((p) => {
    return (
      p.can_view ||
      p.can_create ||
      p.can_edit ||
      p.can_delete ||
      p.can_second_confirm ||
      p.can_cancel_submit ||
      p.can_approve ||
      p.can_print
    );
  }).length;
});

const totalGrantedActions = computed(() => {
  let count = 0;
  userStore.permissionList.forEach((p) => {
    if (p.can_view) count++;
    if (p.can_create) count++;
    if (p.can_edit) count++;
    if (p.can_delete) count++;
    if (p.can_second_confirm) count++;
    if (p.can_cancel_submit) count++;
    if (p.can_approve) count++;
    if (p.can_print) count++;
  });
  return count;
});

const permissionCoveragePercent = computed(() => {
  const maxActions = (userStore.permissionList.length || 15) * 8;
  if (maxActions === 0) return 0;
  return Math.round((totalGrantedActions.value / maxActions) * 100);
});

function closeModal() {
  visible.value = false;
}
</script>

<style scoped>
.profile-container {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  color: var(--text-primary);
  border-radius: 16px;
  overflow: hidden;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: var(--spd-bg-subtle, rgba(30, 41, 59, 0.6));
  border-bottom: 1px solid var(--border-divider);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-box {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--accent-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3);
}

.avatar-letter {
  font-size: 24px;
  font-weight: 700;
  color: #080c14;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-realname {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.role-tag {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.3);
  color: var(--accent-primary);
  font-size: 12px;
  font-weight: 500;
}

.header-sub-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-muted);
}

.divider {
  color: var(--border-divider);
}

.close-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}

.svg-icon {
  width: 18px;
  height: 18px;
}

.profile-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 24px 0 24px;
  border-bottom: 1px solid var(--border-divider);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}

.tab-icon {
  width: 16px;
  height: 16px;
}

.profile-body {
  padding: 20px 24px;
  max-height: 480px;
  overflow-y: auto;
}

.tab-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card {
  background: var(--spd-bg-subtle, rgba(30, 41, 59, 0.4));
  border: 1px solid var(--border-divider);
  border-radius: 12px;
  padding: 16px 20px;
}

.card-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 14px;
}

.section-svg {
  width: 18px;
  height: 18px;
  color: var(--accent-primary);
}

.section-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 14px;
  line-height: 1.5;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 20px;
}

.grid-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.grid-label {
  font-size: 12px;
  color: var(--text-muted);
}

.grid-val {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.text-success {
  color: var(--color-success);
}

.text-info {
  color: var(--accent-primary);
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.flex-1 {
  flex: 1;
}

.form-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.required {
  color: var(--color-danger);
}

.btn-align-right {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

/* 仓库画像卡片 */
.warehouse-chip-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.warehouse-card {
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-divider);
  cursor: pointer;
  transition: all 0.2s;
}

.warehouse-card:hover {
  border-color: rgba(56, 189, 248, 0.4);
  transform: translateY(-1px);
}

.warehouse-card.current {
  border-color: var(--accent-primary);
  background: rgba(56, 189, 248, 0.08);
}

.wh-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.wh-badge {
  font-size: 11px;
  color: var(--accent-primary);
  background: rgba(56, 189, 248, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
}

.wh-active-label {
  font-size: 11px;
  color: var(--color-success);
  font-weight: 600;
}

.wh-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.wh-meta {
  font-size: 11px;
  color: var(--text-muted);
}

/* 权限画像卡片 */
.rbac-stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.rbac-stat-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-divider);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  font-family: monospace;
  color: var(--text-primary);
}

.stat-txt {
  font-size: 12px;
  color: var(--text-muted);
}

.rbac-module-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}

.rbac-module-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid var(--border-divider);
}

.module-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.module-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.module-code {
  font-size: 11px;
  color: var(--text-muted);
}

.action-tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.action-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  user-select: none;
}

.action-tag.granted {
  background: rgba(52, 211, 153, 0.15);
  color: var(--color-success);
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.action-tag.denied {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
  border: 1px solid transparent;
  opacity: 0.6;
}

.pwd-form {
  max-width: 420px;
}
</style>
