import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
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
        meta: { title: '1. 产品字典管理 (双维分类)' }
      },
      {
        path: 'general',
        name: 'GeneralMaterial',
        component: () => import('@/views/GeneralMaterialView.vue'),
        meta: { title: '2. 普通耗材管理 (主库按需分发)' }
      },
      {
        path: 'high-value',
        name: 'HighValue',
        component: () => import('@/views/HighValueView.vue'),
        meta: { title: '3. 高值耗材管理 (一物一码专仓)' }
      },
      {
        path: 'secondary',
        name: 'SecondaryWarehouse',
        component: () => import('@/views/SecondaryWarehouseView.vue'),
        meta: { title: '4. 二级库管理 (临床科室库房)' }
      },
      {
        path: 'logs',
        name: 'WorkflowLog',
        component: () => import('@/views/WorkflowLogView.vue'),
        meta: { title: '5. 全流程业务链路日志 (6W)' }
      },
      {
        path: 'finance',
        name: 'FinancePrint',
        component: () => import('@/views/FinancePrintView.vue'),
        meta: { title: '6. 统计查询与单据打印中心' }
      },
      {
        path: 'procurement',
        name: 'SupplierPurchase',
        component: () => import('@/views/SupplierPurchaseView.vue'),
        meta: { title: '7. 多级采购与供应商协同' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/UserManagementView.vue'),
        meta: { title: '8. 全院人员管理与RBAC权限中心' }
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
router.beforeEach((to, _from, next) => {
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
  } else {
    next();
  }
});

export default router;
