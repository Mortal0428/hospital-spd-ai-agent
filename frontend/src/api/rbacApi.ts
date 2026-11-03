import { httpGet, httpPost } from './request';

/**
 * 用户级模块细粒度 8 动作权限条目
 */
export interface UserModulePermissionItem {
  id: number;
  user_id: number;
  username: string;
  role_code: string;
  module_code: string;
  module_name: string;
  can_view: number;
  can_create: number;
  can_edit: number;
  can_delete: number;
  can_second_confirm: number;
  can_cancel_submit: number;
  can_approve: number;
  can_print: number;
  updated_by: string;
}

/**
 * 查询细粒度 RBAC 权限矩阵
 * @param params 可选 user_id 参数过滤
 * @returns Promise 包含 permissions 与 atomic_actions 的响应
 * @route GET /ext/rbac/matrix
 * @throws Error 当请求异常时抛出
 */
export function getRbacMatrix(params?: { user_id?: number }): Promise<{
  total: number;
  atomic_actions: string[];
  permissions: UserModulePermissionItem[];
}> {
  return httpGet('/ext/rbac/matrix', params);
}

/**
 * 信息科管理员针对具体人员账号独立开关某模块下的原子操作权限
 * @param data 包含 user_id, module_code, action_key, enabled, operator_name 的开关请求
 * @returns Promise 更新后的原子权限详情
 * @route POST /ext/rbac/toggle
 * @throws Error 当动作键名非法时抛出 400
 */
export function toggleUserPermission(data: {
  user_id: number;
  module_code: string;
  action_key: string;
  enabled: number;
  operator_name: string;
}): Promise<{ user_id: number; username: string; module_code: string; action_key: string; new_value: number }> {
  return httpPost('/ext/rbac/toggle', data);
}
