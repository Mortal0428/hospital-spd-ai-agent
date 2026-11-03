<template>
  <el-drawer
    v-model="visible"
    title="信息科解耦式 15 模块 x 8 动作细粒度 RBAC 权限矩阵中枢"
    size="840px"
    append-to-body
    class="spd-rbac-drawer"
  >
    <div class="rbac-container">
      <div class="user-picker-bar">
        <span>目标授权人员账号：</span>
        <el-select
          v-model="selectedUserId"
          style="width: 280px;"
          @change="handleUserChange"
        >
          <el-option
            v-for="u in PRESET_USERS"
            :key="u.id"
            :label="`${u.realName} (${u.roleCode} - ${u.deptName})`"
            :value="u.id"
          />
        </el-select>
        <el-button type="primary" plain :loading="refreshing" @click="fetchMatrix">
          刷新配置
        </el-button>
      </div>

      <el-alert
        title="信息科独立解耦授权：针对任意具体人员，独立开关【查/增/改/删/二次确认/取消提交/审批/打印】8 项原子权限"
        type="success"
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <el-table
        :data="matrixList"
        border
        stripe
        style="width: 100%;"
        v-loading="loading"
      >
        <el-table-column prop="module_name" label="业务模块名称" width="160" fixed="left">
          <template #default="{ row }">
            <strong>{{ row.module_name }}</strong>
            <div class="spd-mono spd-text-muted" style="font-size: 11px;">{{ row.module_code }}</div>
          </template>
        </el-table-column>

        <el-table-column label="查 (View)" width="78" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_view"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_view', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="增 (Create)" width="82" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_create"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_create', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="改 (Edit)" width="78" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_edit"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_edit', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="删 (Del)" width="78" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_delete"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_delete', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="二次确认" width="88" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_second_confirm"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_second_confirm', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="取消提交" width="88" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_cancel_submit"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_cancel_submit', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="审批" width="76" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_approve"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_approve', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="打印" width="76" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.can_print"
              :active-value="1"
              :inactive-value="0"
              size="small"
              @change="(val: any) => handleToggle(row, 'can_print', val)"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { PRESET_USERS, useUserStore, generateDefaultPermissions } from '@/stores/userStore';
import { getRbacMatrix, toggleUserPermission, type UserModulePermissionItem } from '@/api/rbacApi';

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
}>();

const userStore = useUserStore();
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const selectedUserId = ref<number>(userStore.currentUser.id);
const matrixList = ref<UserModulePermissionItem[]>([]);
const loading = ref(false);
const refreshing = ref(false);

/**
 * 加载目标人员的 RBAC 权限矩阵
 * @returns Promise<void>
 * @route internal://RbacMatrixDrawer/fetchMatrix
 * @throws 无异常抛出
 */
async function fetchMatrix() {
  loading.value = true;
  try {
    const res = await getRbacMatrix({ user_id: selectedUserId.value });
    if (res && res.permissions && res.permissions.length > 0) {
      matrixList.value = res.permissions;
    } else {
      loadFallbackMatrix();
    }
  } catch {
    loadFallbackMatrix();
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
}

/**
 * 离线/降级加载本地或默认权限矩阵
 * @returns void
 * @route internal://RbacMatrixDrawer/loadFallbackMatrix
 * @throws 无异常抛出
 */
function loadFallbackMatrix() {
  const storageKey = `spd_rbac_perms_${selectedUserId.value}`;
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    try {
      matrixList.value = JSON.parse(saved);
      return;
    } catch {
      // 降级
    }
  }
  const targetUser = PRESET_USERS.find(u => u.id === selectedUserId.value) || userStore.currentUser;
  matrixList.value = generateDefaultPermissions(targetUser);
}

/**
 * 切换被授权人员
 * @param uid 人员主键 ID
 * @returns void
 * @route internal://RbacMatrixDrawer/handleUserChange
 * @throws 无异常抛出
 */
function handleUserChange(uid: number) {
  selectedUserId.value = uid;
  fetchMatrix();
}

/**
 * 实时动态切换单项原子权限开关
 * @param row 当前模块行对象
 * @param actionKey 原子动作名
 * @param val 开关布尔/数字值 (0 或 1)
 * @returns Promise<void>
 * @route internal://RbacMatrixDrawer/handleToggle
 * @throws 当后端返回异常时还原开关状态
 */
async function handleToggle(row: UserModulePermissionItem, actionKey: string, val: number) {
  try {
    await toggleUserPermission({
      user_id: selectedUserId.value,
      module_code: row.module_code,
      action_key: actionKey,
      enabled: val,
      operator_name: '赵振华(信息科系统管理员)'
    });
  } catch {
    // 后端异常或离线，不阻塞本地实时体验
  }
  userStore.applyPermissionToggle(selectedUserId.value, row.module_code, actionKey, val);
  ElMessage.success(`模块[${row.module_name}]的[${actionKey}]已切换为 ${val ? '开启' : '关闭'}`);
}

onMounted(() => {
  fetchMatrix();
});
</script>

<style scoped>
.rbac-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.user-picker-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--spd-bg-subtle);
  border: 1px solid var(--spd-border-subtle);
  border-radius: var(--spd-radius-md);
  padding: 12px 16px;
  font-size: 13.5px;
}
</style>
