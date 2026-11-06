import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { ElMessage } from 'element-plus';
import MainLayout from '@/layouts/MainLayout.vue';
import LoginView from '@/views/LoginView.vue';
import { useUserStore } from '@/stores/userStore';

/**
 * @file index.ts
 * @description 前端全局路由注册与动态安全导航守卫
 * 配置 3D 数字化展厅主门户、医慧通行登录页及 7 大三级工作台核心业务视图。
 */

const routes: RouteRecordRaw[] = [
  {
    path: '/showcase',
    name: 'Showcase',
    component: () => import('@/views/ShowcaseView.vue'),
    meta: { title: '数字化展厅 · 双模态全景门户' }
  },
  {
    path: '/login',
    name: 'Login',
    redirect: '/showcase?login=1'
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/showcase',
    children: [
      {
        path: 'dict',
        name: 'ProductDict',
        component: () => import('@/views/ProductDictView.vue'),
        meta: { title: '1. 产品字典管理 (双维分类)', roles: ['sys_admin', 'dept_manager'] }
      },
      {
        path: 'general',
        name: 'GeneralMaterial',
        component: () => import('@/views/GeneralMaterialView.vue'),
        meta: { title: '2. 普通耗材管理 (主库按需分发)', roles: ['sys_admin', 'dept_manager'] }
      },
      {
        path: 'high-value',
        name: 'HighValue',
        component: () => import('@/views/HighValueView.vue'),
        meta: { title: '3. 高值耗材管理 (一物一码专仓)', roles: ['sys_admin', 'dept_manager', 'secondary_user'] }
      },
      {
        path: 'secondary',
        name: 'SecondaryWarehouse',
        component: () => import('@/views/SecondaryWarehouseView.vue'),
        meta: { title: '4. 二级库管理 (临床科室库房)', roles: ['sys_admin', 'secondary_user', 'dept_manager'] }
      },
      {
        path: 'logs',
        name: 'WorkflowLog',
        component: () => import('@/views/WorkflowLogView.vue'),
        meta: { title: '5. 全流程业务链路日志 (6W)', roles: ['sys_admin', 'dept_manager', 'finance_auditor'] }
      },
      {
        path: 'finance',
        name: 'FinancePrint',
        component: () => import('@/views/FinancePrintView.vue'),
        meta: { title: '6. 统计查询与单据打印中心', roles: ['sys_admin', 'finance_auditor', 'dept_manager'] }
      },
      {
        path: 'procurement',
        name: 'HospitalProcurement',
        component: () => import('@/views/HospitalProcurementView.vue'),
        meta: { title: '7. 采购管理与准入中心', roles: ['sys_admin', 'dept_manager', 'secondary_user', 'finance_auditor'] }
      },
      {
        path: 'supplier-portal',
        name: 'ExternalSupplierPortal',
        component: () => import('@/views/ExternalSupplierPortalView.vue'),
        meta: { title: '8. 外部供应商协同门户', roles: ['sys_admin', 'supplier_user'] }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/UserManagementView.vue'),
        meta: { title: '9. 全院人员管理与RBAC权限中心', roles: ['sys_admin'] }
      },
      {
        path: 'rag-hub',
        name: 'RagAgentHub',
        component: () => import('@/views/RagAgentHubView.vue'),
        meta: { title: '10. Agentic RAG 知识工程与控制中台', roles: ['sys_admin', 'dept_manager', 'secondary_user', 'finance_auditor'] }
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

/**
 * 全局前置导航守卫
 * 处理网页标题同步、公共免登录页面放行与受保护路由鉴权
 */
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 医院医疗物资全链路管理系统`;
  }

  const userStore = useUserStore();
  const publicPaths = ['/showcase', '/login'];

  if (to.path === '/') {
    // 根路径默认定向到数字展厅全景门户
    next({ path: '/showcase' });
  } else if (!userStore.isLoggedIn && !publicPaths.includes(to.path)) {
    // 未认证人员尝试访问三级工作台业务视图，重定向至展厅门户并可唤起模态登录
    next({ path: '/showcase' });
  } else if (userStore.isLoggedIn && to.path === '/login') {
    // 已登录状态下访问独立登录页，自动进入工作台
    next({ path: '/dict' });
  } else if (userStore.isLoggedIn && to.meta.roles && Array.isArray(to.meta.roles)) {
    // 细粒度岗位角色鉴权：非管理员访问无授权页面明确告警提示并取消无响应回弹
    const currentRole = userStore.currentUser.roleCode;
    if (currentRole !== 'sys_admin' && !to.meta.roles.includes(currentRole)) {
      ElMessage.warning(`无权访问：当前岗位角色 [${currentRole}] 尚未开放 [${to.meta.title || to.path}] 模块权限，请联系管理员开通`);
      // 若已有合法前置页面，保留在当前页；若为直接敲地址，回退至该角色主页
      if (from && from.path && from.path !== to.path && from.path !== '/') {
        next(false);
      } else {
        if (currentRole === 'secondary_user') next({ path: '/secondary' });
        else if (currentRole === 'finance_auditor') next({ path: '/finance' });
        else if (currentRole === 'supplier_user') next({ path: '/supplier-portal' });
        else if (currentRole === 'dept_manager') next({ path: '/general' });
        else next({ path: '/showcase' });
      }
      return;
    }
    next();
  } else {
    next();
  }
});

export default router;
