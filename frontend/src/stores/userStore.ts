import { defineStore } from 'pinia';
import { getRbacMatrix, type UserModulePermissionItem } from '@/api/rbacApi';
import { httpGet, httpPost } from '@/api/request';

/**
 * 系统人员用户信息定义
 */
export interface UserProfile {
  id: number;
  username: string;
  realName: string;
  roleCode: 'sys_admin' | 'dept_manager' | 'secondary_user' | 'finance_auditor' | 'supplier_user';
  deptCode: string;
  deptName: string;
}

/**
 * 后端登录接口响应数据结构
 */
interface BackendLoginResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
  real_name: string;
  role_code: string;
  dept_id: number;
  dept_code: string;
  dept_name: string;
}

/**
 * 院内核心业务角色代表人员清单 (严格对齐后端真实种子账号与医院 SPD 三级人员权限体系)
 */
export const PRESET_USERS: UserProfile[] = [
  {
    id: 1,
    username: 'admin',
    realName: '赵振华 (系统管理员)',
    roleCode: 'sys_admin',
    deptCode: 'INFO_DEPT',
    deptName: '信息科'
  },
  {
    id: 2,
    username: 'mgr_consumable',
    realName: '王建国 (耗材科主管)',
    roleCode: 'dept_manager',
    deptCode: 'CONSUMABLE_DEPT',
    deptName: '耗材科主库'
  },
  {
    id: 3,
    username: 'mgr_equip',
    realName: '周天海 (设备科主管)',
    roleCode: 'dept_manager',
    deptCode: 'EQUIP_DEPT',
    deptName: '设备科主库'
  },
  {
    id: 6,
    username: 'nurse_cardio',
    realName: '李晓琳 (临床二级库)',
    roleCode: 'secondary_user',
    deptCode: 'SEC_CARDIO',
    deptName: '心内科/骨科二级库'
  },
  {
    id: 4,
    username: 'mgr_finance',
    realName: '孙丽娟 (财务审计主管)',
    roleCode: 'finance_auditor',
    deptCode: 'FINANCE_DEPT',
    deptName: '财务科'
  },
  {
    id: 7,
    username: 'supplier_wego',
    realName: '张明远 (威高医药代表)',
    roleCode: 'supplier_user',
    deptCode: 'SUPPLIER_EXT',
    deptName: '威高医疗(供应商协同)'
  },
  {
    id: 8,
    username: 'cyx',
    realName: '陈永兴 (系统管理员)',
    roleCode: 'sys_admin',
    deptCode: 'INFO_DEPT',
    deptName: '信息科'
  },
  {
    id: 9,
    username: 'cyx01',
    realName: '陈永兴01 (外部供应商代表)',
    roleCode: 'supplier_user',
    deptCode: 'SUPPLIER_ORG',
    deptName: '外部签约供应商'
  }
];

export const useUserStore = defineStore('user', {
  state: () => {
    const savedUserStr = localStorage.getItem('spd_active_user');
    let initialUser = PRESET_USERS[0];
    if (savedUserStr) {
      try {
        initialUser = JSON.parse(savedUserStr);
      } catch {
        initialUser = PRESET_USERS[0];
      }
    }
    const savedLogin = localStorage.getItem('spd_is_logged_in') === 'true';

    return {
      isLoggedIn: savedLogin,
      currentUser: initialUser,
      token: localStorage.getItem('spd_token') || '',
      permissionList: [] as UserModulePermissionItem[],
      loadingPermissions: false,
      theme: (localStorage.getItem('spd_theme') || 'light') as 'light' | 'dark',
      currentWarehouseCode: localStorage.getItem('spd_current_warehouse') || 'WH_WEICAI',
      assignedWarehouseList: [] as Array<{ code: string; name: string }>
    };
  },

  getters: {
    /**
     * 当前角色授权可操作的仓库列表
     */
    authorizedWarehouses(state): Array<{ code: string; name: string }> {
      const allWarehouses = [
        { code: 'WH_WEICAI', name: '卫材库房 (耗材主库)' },
        { code: 'WH_EQUIP', name: '设备库房 (设备主库)' },
        { code: 'WH_ZONGWU', name: '总务仓库 (低值易耗)' },
        { code: 'WH_XINXI', name: '信息仓库 (IT耗材)' },
        { code: 'WH_SEC_ORTHO', name: '骨科病区二级库' },
        { code: 'WH_SEC_CARDIO', name: '心内科病区二级库' },
        { code: 'WH_ZHUANXIANG', name: '专项耗材库房 (高值专仓)' }
      ];

      if (state.currentUser.roleCode === 'sys_admin') {
        return [{ code: 'ALL', name: '全院全部仓库 (穿透模式)' }, ...allWarehouses];
      }
      if (state.assignedWarehouseList && state.assignedWarehouseList.length > 0) {
        return state.assignedWarehouseList;
      }
      if (state.currentUser.roleCode === 'dept_manager') {
        return allWarehouses.filter(w => ['WH_WEICAI', 'WH_EQUIP', 'WH_ZONGWU', 'WH_XINXI'].includes(w.code));
      }
      if (state.currentUser.roleCode === 'secondary_user') {
        return allWarehouses.filter(w => ['WH_SEC_ORTHO', 'WH_SEC_CARDIO'].includes(w.code));
      }
      return allWarehouses;
    },
    /**
     * 构建以 module_code 为一级键、action_key 为二级键的高速鉴权字典
     * @param state Pinia 状态对象
     * @returns Record<string, Record<string, boolean>> 权限映射表
     * @route internal://src/stores/userStore/permissionMap
     * @throws 无异常抛出
     */
    permissionMap(state): Record<string, Record<string, boolean>> {
      const map: Record<string, Record<string, boolean>> = {};
      state.permissionList.forEach((item) => {
        map[item.module_code] = {
          can_view: Boolean(item.can_view),
          can_create: Boolean(item.can_create),
          can_edit: Boolean(item.can_edit),
          can_delete: Boolean(item.can_delete),
          can_second_confirm: Boolean(item.can_second_confirm),
          can_cancel_submit: Boolean(item.can_cancel_submit),
          can_approve: Boolean(item.can_approve),
          can_print: Boolean(item.can_print)
        };
      });
      return map;
    },

    /**
     * 1:1 复刻 Demo 原型顶部的角色权限上下文描述文本
     * @param state Pinia 状态对象
     * @returns string 角色权限上下文横幅文字
     * @route internal://src/stores/userStore/roleDescription
     * @throws 无异常抛出
     */
    roleDescription(state): string {
      const descMap: Record<string, string> = {
        sys_admin:
          '信息科系统管理员（sys_admin）—— 拥有全院最大权限，管理全院科室与人员，执行全流程业务链路日志增删改查及 15 模块细粒度 RBAC 授权。',
        dept_manager:
          '耗材科/设备科主库管理员（dept_manager）—— 管辖归口主库的产品字典、普通耗材主库入库及向各临床二级库/高值仓按需分发。',
        secondary_user:
          '临床二级库人员（secondary_user）—— 管辖【骨科/心内科二级库】库存盘点、向主库发起申领、签收分发单及患者高值耗材专属码扫码核销。',
        finance_auditor:
          '财务科管理员（finance_auditor）—— 负责全院主库与二级库流水核对、遵循“移库不计费/消耗即结算”执行月度科室耗材成本核算与报表打印。',
        supplier_user:
          '外部供应商协同代表（supplier_user）—— 资质审核准入拦截、在线接收采购订单、录入批号效期拣货、发货联动生成医院待验收入库单。'
      };
      return descMap[state.currentUser.roleCode] || descMap.sys_admin;
    }
  },

  actions: {
    /**
     * 同步本地持久化会话凭据与人员状态
     * @param {boolean} isLoggedIn 是否处于已登录状态
     * @param {UserProfile} user 用户信息档案
     * @param {string} token 认证令牌字符串
     * @returns {void}
     * @route internal://src/stores/userStore/syncStorage
     * @throws 无异常抛出
     */
    syncStorage(isLoggedIn: boolean, user: UserProfile, token: string): void {
      if (isLoggedIn) {
        localStorage.setItem('spd_is_logged_in', 'true');
        localStorage.setItem('spd_token', token);
        localStorage.setItem('spd_active_user', JSON.stringify(user));
        localStorage.setItem('spd_active_username', user.username);
      } else {
        localStorage.removeItem('spd_is_logged_in');
        localStorage.removeItem('spd_token');
        localStorage.removeItem('spd_active_user');
        localStorage.removeItem('spd_active_username');
      }
    },

    /**
     * 医护账号密码双轨高韧性登录验证
     * @param {string} account 医护工号
     * @param {string} [password] 安全密码 (默认 123456)
     * @returns {Promise<boolean>} 是否登录成功
     * @route internal://src/stores/userStore/login
     * @throws 当登录逻辑异常时捕获并兜底为模拟成功，确保演示不白屏
     */
    async login(account: string, password?: string): Promise<boolean> {
      const trimmedAccount = (account || '').trim();
      const effectivePwd = password || '';
      if (!trimmedAccount || !effectivePwd) {
        throw new Error('请输入医护工号及系统访问密码');
      }

      // 映射演示工号 (如 SPD-CONSUMABLE-01 -> mgr_consumable)
      const mappedUsername = this.resolveDemoUsername(trimmedAccount);

      try {
        const resp = await httpPost<BackendLoginResponse>('/auth/login', {
          username: mappedUsername,
          password: effectivePwd
        });

        if (resp && resp.access_token) {
          this.token = resp.access_token;
          const matched = PRESET_USERS.find((u) => u.username === resp.username);
          const mappedRoleCode =
            resp.role_code === 'dept_manager' && resp.dept_code === 'FINANCE_DEPT'
              ? 'finance_auditor'
              : (resp.role_code as UserProfile['roleCode']);

          this.currentUser = {
            id: resp.user_id,
            username: resp.username,
            realName: resp.real_name || (matched ? matched.realName : resp.username),
            roleCode: mappedRoleCode || (matched ? matched.roleCode : 'sys_admin'),
            deptCode: resp.dept_code,
            deptName: resp.dept_name
          };

          this.isLoggedIn = true;
          this.syncStorage(true, this.currentUser, this.token);
          await this.fetchPermissions();
          await this.refreshAuthorizedWarehouses();
          return true;
        } else {
          throw new Error('认证中心凭证签发异常');
        }
      } catch (err: any) {
        this.isLoggedIn = false;
        this.token = '';
        this.syncStorage(false, PRESET_USERS[0], '');
        const errMsg = err?.response?.data?.detail || err?.message || '医护工号或访问密码不正确，请核对后重试';
        throw new Error(errMsg);
      }
    },

    /**
     * 将演示工号或别名映射为标准系统账号
     * @param {string} rawAccount 原始输入的工号或角色名称
     * @returns {string} 映射后的标准系统账号
     * @route internal://src/stores/userStore/resolveDemoUsername
     * @throws 无异常抛出
     */
    resolveDemoUsername(rawAccount: string): string {
      const upper = rawAccount.trim().toUpperCase();
      if (upper === 'SPD-CONSUMABLE-01' || upper === 'CONSUMABLE') return 'mgr_consumable';
      if (upper === 'SPD-EQUIP-02' || upper === 'EQUIP') return 'mgr_equip';
      if (upper === 'SPD-NURSE-06' || upper === 'NURSE') return 'nurse_cardio';
      if (upper === 'SPD-AUDIT-08' || upper === 'FINANCE') return 'mgr_finance';
      if (upper === 'SPD-ADMIN-01' || upper === 'ADMIN') return 'admin';
      return rawAccount.trim();
    },

    /**
     * 1:1 复刻 Demo 中的 4 大核心演示角色及管理员一键免密极速登录通道
     * @param {string} roleKey 角色别名 ('consumable' | 'equip' | 'nurse' | 'finance' | 'admin' 等)
     * @returns {Promise<void>}
     * @route internal://src/stores/userStore/loginAsRole
     * @throws 无异常抛出
     */
    async loginAsRole(roleKey: string): Promise<void> {
      const roleMap: Record<string, string> = {
        consumable: 'mgr_consumable',
        mgr_consumable: 'mgr_consumable',
        dept_manager: 'mgr_consumable',
        equip: 'mgr_equip',
        mgr_equip: 'mgr_equip',
        nurse: 'nurse_cardio',
        nurse_cardio: 'nurse_cardio',
        nurse_ortho: 'nurse_ortho',
        secondary_user: 'nurse_cardio',
        finance: 'mgr_finance',
        mgr_finance: 'mgr_finance',
        finance_auditor: 'mgr_finance',
        admin: 'admin',
        sys_admin: 'admin',
        supplier: 'supplier_wego',
        supplier_user: 'supplier_wego',
        supplier_wego: 'supplier_wego'
      };

      const targetUsername = roleMap[roleKey.toLowerCase()] || 'admin';
      await this.login(targetUsername, '123456');
    },

    /**
     * 退出当前登录并彻底清理本地会话
     * @param {void} 无入参
     * @returns {void}
     * @route internal://src/stores/userStore/logout
     * @throws 无异常抛出
     */
    logout(): void {
      this.isLoggedIn = false;
      this.token = '';
      this.syncStorage(false, this.currentUser, '');
    },

    /**
     * 切换当前操作人员角色上下文并同步持久化
     * @param {UserProfile} targetUser 目标用户信息对象
     * @returns {Promise<void>}
     * @route internal://src/stores/userStore/switchUser
     * @throws 无异常抛出
     */
    async switchUser(targetUser: UserProfile): Promise<void> {
      this.currentUser = targetUser;
      this.syncStorage(this.isLoggedIn, targetUser, this.token);
      await this.fetchPermissions();
    },

    /**
     * 切换亮暗模式
     * @param {string} [mode] 可选目标模式 ('light' | 'dark')
     * @returns {void}
     * @route internal://src/stores/userStore/toggleTheme
     * @throws 无异常抛出
     */
    toggleTheme(mode?: 'light' | 'dark'): void {
      const nextTheme = mode || (this.theme === 'light' ? 'dark' : 'light');
      this.theme = nextTheme;
      localStorage.setItem('spd_theme', nextTheme);
      document.documentElement.setAttribute('data-theme', nextTheme);
    },

    /**
     * 切换全局当前经办操作仓库
     * @param {string} code 仓库唯一编码
     * @returns {void}
     */
    setCurrentWarehouse(code: string): void {
      this.currentWarehouseCode = code;
      localStorage.setItem('spd_current_warehouse', code);
    },

    /**
     * 动态拉取当前用户在数据库中真实授权的经办库藏列表
     * @returns {Promise<void>} 异步刷新全局经办仓库列表
     * @route GET /api/v1/dict/user-warehouse-perms
     * @throws 网络或鉴权失败时回退到角色默认模板
     */
    async refreshAuthorizedWarehouses(): Promise<void> {
      try {
        const res = await httpGet<any>(`/dict/user-warehouse-perms?user_id=${this.currentUser.id}`);
        const list = Array.isArray(res) ? res : (res?.data || []);
        const validWarehouses = list.filter((p: any) => p.can_view === 1);
        if (validWarehouses.length > 0) {
          const mapped = validWarehouses.map((p: any) => ({
            code: p.warehouse_code,
            name: p.warehouse_name || p.warehouse_code
          }));
          if (this.currentUser.roleCode === 'sys_admin' && !mapped.some((m: any) => m.code === 'ALL')) {
            this.assignedWarehouseList = [{ code: 'ALL', name: '全院全部仓库 (穿透模式)' }, ...mapped];
          } else {
            this.assignedWarehouseList = mapped;
          }
          const validCodes = this.authorizedWarehouses.map((w) => w.code);
          if (!validCodes.includes(this.currentWarehouseCode) && this.authorizedWarehouses.length > 0) {
            this.setCurrentWarehouse(this.authorizedWarehouses[0].code);
          }
        }
      } catch {
        // 安全降级至角色静态默认模板
      }
    },

    /**
     * 从后端 API 异步加载当前用户的 15 模块 x 8 动作细粒度 RBAC 权限配置
     * @param {void} 无入参
     * @returns {Promise<void>}
     * @route internal://src/stores/userStore/fetchPermissions
     * @throws 当后端网络异常时向控制台记录警告
     */
    /**
     * 从后端 API 或本地持久化配置加载当前用户的 15 模块 x 8 动作细粒度 RBAC 权限
     * @param {void} 无入参
     * @returns {Promise<void>}
     * @route internal://src/stores/userStore/fetchPermissions
     * @throws 无异常抛出
     */
    async fetchPermissions(): Promise<void> {
      this.loadingPermissions = true;
      try {
        const res = await getRbacMatrix({ user_id: this.currentUser.id });
        if (res && res.permissions && res.permissions.length > 0) {
          this.permissionList = res.permissions;
        } else {
          // 降级使用内置预设权限矩阵
          this.permissionList = this.loadLocalOrDefaultPermissions();
        }
      } catch {
        // 离线/单机演示高韧性降级
        this.permissionList = this.loadLocalOrDefaultPermissions();
      } finally {
        this.loadingPermissions = false;
      }
    },

    /**
     * 读取本地缓存的管理员动态调整权限，若无则使用标准角色预设
     * @returns {UserModulePermissionItem[]} 权限列表
     * @route internal://src/stores/userStore/loadLocalOrDefaultPermissions
     * @throws 无异常抛出
     */
    loadLocalOrDefaultPermissions(): UserModulePermissionItem[] {
      const storageKey = `spd_rbac_perms_${this.currentUser.id}`;
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch {
          // 静默降级
        }
      }
      return generateDefaultPermissions(this.currentUser);
    },

    /**
     * 管理员在 RBAC 抽屉中独立开启/关闭某模块单项权限时，即时响应更新
     * @param {number} userId 目标用户ID
     * @param {string} moduleCode 模块编码
     * @param {string} actionKey 动作键名
     * @param {number} enabled 开关状态 (0 或 1)
     * @returns {void}
     * @route internal://src/stores/userStore/applyPermissionToggle
     * @throws 无异常抛出
     */
    applyPermissionToggle(userId: number, moduleCode: string, actionKey: string, enabled: number): void {
      const storageKey = `spd_rbac_perms_${userId}`;
      let list = this.permissionList;
      if (userId !== this.currentUser.id) {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          try {
            list = JSON.parse(saved);
          } catch {
            const targetUser = PRESET_USERS.find(u => u.id === userId) || this.currentUser;
            list = generateDefaultPermissions(targetUser);
          }
        } else {
          const targetUser = PRESET_USERS.find(u => u.id === userId) || this.currentUser;
          list = generateDefaultPermissions(targetUser);
        }
      }

      const found = list.find(p => p.module_code === moduleCode);
      if (found) {
        (found as any)[actionKey] = enabled;
      }
      localStorage.setItem(storageKey, JSON.stringify(list));

      if (userId === this.currentUser.id) {
        this.permissionList = [...list];
      }
    },

    /**
     * 核心细粒度鉴权函数：校验当前用户在指定模块下是否具备某项原子操作权限
     * @param moduleCode 业务模块编码 (如: DICT_MANAGE, GEN_INBOUND, HV_RETURN)
     * @param actionKey 原子动作名 ('can_view' | 'can_create' | 'can_edit' | 'can_delete' | 'can_second_confirm' | 'can_cancel_submit' | 'can_approve' | 'can_print')
     * @returns boolean 是否允许操作
     * @route internal://src/stores/userStore/canAction
     * @throws 无异常抛出
     */
    canAction(
      moduleCode: string,
      actionKey:
        | 'can_view'
        | 'can_create'
        | 'can_edit'
        | 'can_delete'
        | 'can_second_confirm'
        | 'can_cancel_submit'
        | 'can_approve'
        | 'can_print'
    ): boolean {
      if (this.currentUser.roleCode === 'sys_admin') {
        return true;
      }
      // 模块编码别名映射兼容表，保障前端与后端各版本契约无缝对齐
      const aliasMap: Record<string, string[]> = {
        'DICT_MANAGE': ['DICT_MANAGE', 'DICT_SPEC'],
        'DICT_SPEC': ['DICT_MANAGE', 'DICT_SPEC'],
        'FINANCE_AUDIT': ['FINANCE_AUDIT', 'FIN_AUDIT'],
        'FIN_AUDIT': ['FINANCE_AUDIT', 'FIN_AUDIT'],
        'WORKFLOW_LOG': ['WORKFLOW_LOG', 'TRACE_LOGS'],
        'TRACE_LOGS': ['WORKFLOW_LOG', 'TRACE_LOGS'],
        'SUPPLIER_SHIP': ['SUPPLIER_SHIP', 'SUPPLIER_PORTAL'],
        'SUPPLIER_PORTAL': ['SUPPLIER_SHIP', 'SUPPLIER_PORTAL'],
        'PURCHASE_PLAN': ['PURCHASE_PLAN'],
        'AGENT_HUB': ['AGENT_HUB']
      };

      const candidateCodes = aliasMap[moduleCode] || [moduleCode];
      for (const code of candidateCodes) {
        const modPerms = this.permissionMap[code];
        if (modPerms && modPerms[actionKey] !== undefined) {
          return Number(modPerms[actionKey]) === 1;
        }
      }
      return false;
    }
  }
});

/**
 * 依据用户角色与身份生成完备的 12 模块 x 8 动作细粒度 RBAC 权限默认契约
 * 严格对齐医院三级管理架构与用户指示：
 * - sys_admin: 全模块全权
 * - secondary_user: 仅二级库(SEC_WAREHOUSE)与高值核销(HV_QR_VERIFY/HV_PREP_RECEIVE)
 * - finance_auditor: 仅财务打印中心(FINANCE_AUDIT)与全流程日志(WORKFLOW_LOG)
 * - supplier_user: 仅采购与供应商协同(SUPPLIER_SHIP)
 * - dept_manager: 产品字典(DICT_MANAGE)、普通主库(GEN_INBOUND/GEN_OUTBOUND/GEN_INIT_STOCK)、采购(PURCHASE_PLAN)
 * @param {UserProfile} user 用户实体信息
 * @returns {UserModulePermissionItem[]} 权限条目列表
 * @route internal://src/stores/userStore/generateDefaultPermissions
 * @throws 无异常抛出
 */
export function generateDefaultPermissions(user: UserProfile): UserModulePermissionItem[] {
  const isSysAdmin = user.roleCode === 'sys_admin';
  const isSecondary = user.roleCode === 'secondary_user';
  const isFinance = user.roleCode === 'finance_auditor' || user.username === 'mgr_finance';
  const isSupplier = user.roleCode === 'supplier_user';
  const isDeptManager = user.roleCode === 'dept_manager' && !isFinance;

  const moduleDefinitions = [
    { code: 'DICT_MANAGE', name: '产品字典深度管理' },
    { code: 'GEN_INBOUND', name: '普通耗材验收入库与退货' },
    { code: 'GEN_OUTBOUND', name: '普通耗材出库与请领审核' },
    { code: 'GEN_INIT_STOCK', name: '各科室仓库期初数据建账' },
    { code: 'HV_PREP_RECEIVE', name: '高值耗材备货与科室接收' },
    { code: 'HV_RETURN', name: '高值耗材科室退货出库(不可逆)' },
    { code: 'HV_QR_VERIFY', name: '高值一物一码二维码扫码核销' },
    { code: 'SEC_WAREHOUSE', name: '临床二级库全模块管理' },
    { code: 'PURCHASE_PLAN', name: '多级采购计划与准入审核' },
    { code: 'SUPPLIER_SHIP', name: '外部供应商资质上传与拣货发货' },
    { code: 'WORKFLOW_LOG', name: '全流程业务链路日志 (6W)' },
    { code: 'FINANCE_AUDIT', name: '统计查询与单据打印中心' },
    { code: 'AGENT_HUB', name: '6大智能体与知识工程中台' }
  ];

  return moduleDefinitions.map((mod, index) => {
    let v = 0, c = 0, e = 0, d = 0, sc = 0, cs = 0, ap = 0, pr = 0;

    if (isSysAdmin) {
      v = 1; c = 1; e = 1; d = 1; sc = 1; cs = 1; ap = 1; pr = 1;
    } else if (isSecondary) {
      if (mod.code === 'SEC_WAREHOUSE') {
        v = 1; c = 1; e = 1; d = 0; sc = 1; cs = 1; ap = 0; pr = 1;
      } else if (mod.code === 'HV_QR_VERIFY') {
        v = 1; c = 1; e = 1; d = 0; sc = 1; cs = 0; ap = 0; pr = 1;
      } else if (mod.code === 'HV_PREP_RECEIVE') {
        v = 1; c = 1; e = 0; d = 0; sc = 1; cs = 0; ap = 0; pr = 1;
      } else if (mod.code === 'DICT_MANAGE') {
        v = 1; c = 0; e = 0; d = 0; sc = 0; cs = 0; ap = 0; pr = 0;
      } else if (mod.code === 'PURCHASE_PLAN') {
        v = 1; c = 1; e = 0; d = 0; sc = 0; cs = 1; ap = 0; pr = 1; // 护士拥有采购计划提报权与撤销权
      } else if (mod.code === 'AGENT_HUB') {
        v = 1; c = 0; e = 0; d = 0; sc = 0; cs = 0; ap = 0; pr = 1; // 护士开放使用临床问答与高值追溯智能体
      }
    } else if (isFinance) {
      if (mod.code === 'FINANCE_AUDIT') {
        v = 1; c = 0; e = 0; d = 0; sc = 0; cs = 0; ap = 1; pr = 1;
      } else if (mod.code === 'WORKFLOW_LOG') {
        v = 1; c = 0; e = 0; d = 0; sc = 0; cs = 0; ap = 0; pr = 1;
      } else if (mod.code === 'PURCHASE_PLAN') {
        v = 1; c = 0; e = 0; d = 0; sc = 1; cs = 0; ap = 1; pr = 1; // 财务主管拥有采购预算审核与对账权
      } else if (mod.code === 'AGENT_HUB') {
        v = 1; c = 0; e = 0; d = 0; sc = 0; cs = 0; ap = 0; pr = 1; // 财务开放使用精算审计智能体与知识库查阅
      }
    } else if (isSupplier) {
      if (mod.code === 'SUPPLIER_SHIP') {
        v = 1; c = 1; e = 1; d = 0; sc = 1; cs = 0; ap = 0; pr = 1;
      }
    } else if (isDeptManager) {
      if (['DICT_MANAGE', 'GEN_INBOUND', 'GEN_OUTBOUND', 'GEN_INIT_STOCK', 'PURCHASE_PLAN'].includes(mod.code)) {
        v = 1; c = 1; e = 1; d = 0; sc = 1; cs = 1; ap = 1; pr = 1;
      } else if (['HV_PREP_RECEIVE', 'HV_RETURN'].includes(mod.code)) {
        v = 1; c = 0; e = 0; d = 0; sc = 0; cs = 0; ap = 1; pr = 1;
      } else if (mod.code === 'AGENT_HUB') {
        v = 1; c = 1; e = 1; d = 0; sc = 1; cs = 0; ap = 1; pr = 1;
      }
    }

    return {
      id: index + 1,
      user_id: user.id,
      username: user.username,
      role_code: user.roleCode,
      module_code: mod.code,
      module_name: mod.name,
      can_view: v,
      can_create: c,
      can_edit: e,
      can_delete: d,
      can_second_confirm: sc,
      can_cancel_submit: cs,
      can_approve: ap,
      can_print: pr,
      updated_by: '赵振华(信息科系统管理员)'
    };
  });
}
