<template>
  <div class="fusion-app-shell" :data-theme="userStore.theme">
    <!-- 背景流光与微粒子质感层 -->
    <div class="fusion-ambient-glow" />

    <!-- 顶部全局沉浸式毛玻璃导航栏 (1:1 延展自 Demo 原型与 Fusion 变体) -->
    <header class="top-navbar">
      <div class="brand-box">
        <div class="brand-logo-badge">
          <SvgIcon name="brand" :size="20" color="#ffffff" />
        </div>
        <div class="brand-text">
          <h1>医院医疗物资全链路管理系统</h1>
          <p>三甲医院数字化 SPD + 多智能体协同生产工作台</p>
        </div>
      </div>

      <div class="top-controls">
        <!-- 全局当前操作仓库沉浸切换器 -->
        <div class="warehouse-switch-wrap" title="当前经办操作仓库">
          <SvgIcon name="package" :size="14" color="var(--accent-primary)" />
          <span class="wh-label">当前仓库:</span>
          <select
            id="warehouse-selector"
            :value="userStore.currentWarehouseCode"
            aria-label="切换当前经办仓库"
            @change="handleWarehouseChange"
          >
            <option
              v-for="wh in userStore.authorizedWarehouses"
              :key="wh.code"
              :value="wh.code"
            >
              {{ wh.name }}
            </option>
          </select>
        </div>

        <!-- 真实登录人员芯片卡 (点击唤出个人主页与账号安全中心) -->
        <div
          class="user-profile-chip"
          title="点击查看个人主页、管辖仓库与账号安全"
          @click="showProfileModal = true"
        >
          <div class="user-chip-avatar font-mono">
            {{ userStore.currentUser.realName ? userStore.currentUser.realName.trim().charAt(0).toUpperCase() : '医' }}
          </div>
          <div class="user-chip-text">
            <span class="user-chip-name">{{ userStore.currentUser.realName }}</span>
            <span class="user-chip-badge">{{ userRoleLabel }}</span>
          </div>
        </div>

        <!-- 切换账号通道 -->
        <button
          class="btn-ctrl btn-ctrl-switch"
          title="切换全院其他人员账号登录"
          @click="openSwitchUserModal"
        >
          <SvgIcon name="user" :size="14" color="currentColor" />
          <span>切换账号</span>
        </button>

        <!-- 细粒度 RBAC 抽屉唤出按钮 -->
        <button
          v-if="userStore.currentUser.roleCode === 'sys_admin'"
          class="btn-ctrl btn-ctrl-rbac"
          title="信息科 15 模块 x 8 动作细粒度 RBAC 抽屉"
          @click="showRbacDrawer = true"
        >
          <SvgIcon name="lock" :size="14" color="currentColor" />
          <span>细粒度 RBAC 授权</span>
        </button>

        <!-- 法定四联单据打印预览按钮 -->
        <button
          class="btn-ctrl"
          title="查看法定单据四联打印中枢"
          @click="showPrintModal = true"
        >
          <SvgIcon name="printer" :size="14" color="currentColor" />
          <span>四联单据打印</span>
        </button>

        <!-- 3D 数字展厅跳转按钮 -->
        <button
          class="btn-ctrl btn-ctrl-primary"
          title="进入 3D 数字化全景展厅"
          @click="handleJumpShowcase"
        >
          <SvgIcon name="orbital" :size="14" color="#ffffff" />
          <span>3D 数字展厅</span>
        </button>

        <!-- 亮暗模式切换 -->
        <button
          class="btn-ctrl btn-ctrl-icon"
          title="切换深空暗色 / 极简白瓷主题"
          @click="userStore.toggleTheme()"
        >
          <SvgIcon
            :name="userStore.theme === 'light' ? 'moon' : 'sun'"
            :size="16"
            color="currentColor"
          />
        </button>

        <!-- 退出登录按钮 -->
        <button
          class="btn-ctrl btn-ctrl-danger"
          title="安全退出当前会话"
          @click="handleLogout"
        >
          <SvgIcon name="close" :size="14" color="currentColor" />
          <span>退出</span>
        </button>
      </div>
    </header>

    <!-- 主体融合工作台容器 (Fusion Master Layout) -->
    <div class="fusion-body">
      <!-- 浮动占位锚点 (未固定时占位) -->
      <div v-if="!isPinned" class="sidebar-placeholder-strip" />

      <!-- 左侧动态树形自适应侧边栏 (支持自动收缩、悬停展开与图钉常驻固定) -->
      <aside
        class="fusion-sidebar"
        :class="{
          'is-pinned': isPinned,
          'is-floating': !isPinned,
          'is-expanded': isExpanded,
          'is-collapsed': !isExpanded
        }"
        @mouseenter="handleMouseEnter"
        @mouseleave="handleMouseLeave"
      >
        <!-- 侧边栏顶部工具行：标题与 Pin 图钉切换 -->
        <div class="sidebar-header-row">
          <div v-show="isExpanded" class="side-nav-group-title">
            授权业务模块
          </div>
          <button
            class="btn-pin-toggle"
            :class="{ active: isPinned }"
            :title="isPinned ? '点击切换为自动收缩模式(鼠标移入滑出)' : '点击固定侧边栏常驻展示'"
            @click.stop="togglePin"
          >
            <SvgIcon :name="isPinned ? 'lock' : 'unlock'" :size="13" />
            <span v-show="isExpanded" class="pin-hint-text">{{ isPinned ? '已固定' : '浮动收起' }}</span>
          </button>
        </div>

        <!-- 1. 产品字典管理 (主库/信息科) -->
        <div v-if="canViewProductDict" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/dict' && !currentTab }"
            @click="toggleGroup('dict', '/dict')"
          >
            <SvgIcon name="dict" :size="16" />
            <span v-show="isExpanded" class="item-title">产品字典管理</span>
            <span v-show="isExpanded" class="side-badge">双维</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.dict }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.dict" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/dict' && (!currentTab || currentTab === 'specs') }"
              @click="navigateMenu('/dict', 'specs')"
            >
              <span class="sub-dot" />
              <span>耗材规格目录</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/dict' && currentTab === 'warehouses' }"
              @click="navigateMenu('/dict', 'warehouses')"
            >
              <span class="sub-dot" />
              <span>仓库架构维护</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/dict' && currentTab === 'categories' }"
              @click="navigateMenu('/dict', 'categories')"
            >
              <span class="sub-dot" />
              <span>耗材分类设置</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/dict' && currentTab === 'suppliers' }"
              @click="navigateMenu('/dict', 'suppliers')"
            >
              <span class="sub-dot" />
              <span>供应商资质档案</span>
            </div>
          </div>
        </div>

        <!-- 2. 普通耗材主库 (主库按需分发) -->
        <div v-if="canViewGeneralMaterial" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/general' && !currentTab }"
            @click="toggleGroup('general', '/general')"
          >
            <SvgIcon name="package" :size="16" />
            <span v-show="isExpanded" class="item-title">普通耗材主库</span>
            <span v-show="isExpanded" class="side-badge">FEFO</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.general }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.general" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/general' && (currentTab === 'requisition' || !currentTab) }"
              @click="navigateMenu('/general', 'requisition')"
            >
              <span class="sub-dot" />
              <span>临床请领受理</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/general' && currentTab === 'inbound' }"
              @click="navigateMenu('/general', 'inbound')"
            >
              <span class="sub-dot" />
              <span>耗材验收入库</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/general' && (currentTab === 'dispatch' || currentTab === 'outbound') }"
              @click="navigateMenu('/general', 'outbound')"
            >
              <span class="sub-dot" />
              <span>按需分发出库</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/general' && (currentTab === 'stock' || currentTab === 'init-stock') }"
              @click="navigateMenu('/general', 'init-stock')"
            >
              <span class="sub-dot" />
              <span>主库实时台账</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/general' && currentTab === 'stocktake' }"
              @click="navigateMenu('/general', 'stocktake')"
            >
              <span class="sub-dot" />
              <span>主库独立盘点</span>
            </div>
          </div>
        </div>

        <!-- 3. 高值耗材专仓 (一物一码专仓) -->
        <div v-if="canViewHighValue" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/high-value' && !currentTab }"
            @click="toggleGroup('highValue', '/high-value')"
          >
            <SvgIcon name="safe" :size="16" />
            <span v-show="isExpanded" class="item-title">高值耗材专仓</span>
            <span v-show="isExpanded" class="side-badge">UDI</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.highValue }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.highValue" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/high-value' && (!currentTab || currentTab === 'inbound') }"
              @click="navigateMenu('/high-value', 'inbound')"
            >
              <span class="sub-dot" />
              <span>备货自动入仓</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/high-value' && currentTab === 'stock' }"
              @click="navigateMenu('/high-value', 'stock')"
            >
              <span class="sub-dot" />
              <span>专柜智能台账</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/high-value' && currentTab === 'coding' }"
              @click="navigateMenu('/high-value', 'coding')"
            >
              <span class="sub-dot" />
              <span>一物一码赋码</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/high-value' && currentTab === 'return' }"
              @click="navigateMenu('/high-value', 'return')"
            >
              <span class="sub-dot" />
              <span>退货出库锁定</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/high-value' && currentTab === 'stocktake' }"
              @click="navigateMenu('/high-value', 'stocktake')"
            >
              <span class="sub-dot" />
              <span>高值独立盘点</span>
            </div>
          </div>
        </div>

        <!-- 4. 临床二级库房 (临床科室库房及申领发料) -->
        <div v-if="canViewSecondaryWarehouse" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/secondary' && !currentTab }"
            @click="toggleGroup('secondary', '/secondary')"
          >
            <SvgIcon name="room" :size="16" />
            <span v-show="isExpanded" class="item-title">临床二级库房</span>
            <span v-show="isExpanded" class="side-badge">病区</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.secondary }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.secondary" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/secondary' && (currentTab === 'apply' || currentTab === 'requisition' || !currentTab) }"
              @click="navigateMenu('/secondary', 'requisition')"
            >
              <span class="sub-dot" />
              <span>科室物资申领</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/secondary' && currentTab === 'receive' }"
              @click="navigateMenu('/secondary', 'receive')"
            >
              <span class="sub-dot" />
              <span>二级库接收入库</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/secondary' && currentTab === 'stock' }"
              @click="navigateMenu('/secondary', 'stock')"
            >
              <span class="sub-dot" />
              <span>科室在库台账</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/secondary' && (currentTab === 'manual-outbound' || currentTab === 'manual-out') }"
              @click="navigateMenu('/secondary', 'manual-out')"
            >
              <span class="sub-dot" />
              <span>手动发料出库</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/secondary' && currentTab === 'transfer' }"
              @click="navigateMenu('/secondary', 'transfer')"
            >
              <span class="sub-dot" />
              <span>跨病区调拨</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/secondary' && currentTab === 'stocktake' }"
              @click="navigateMenu('/secondary', 'stocktake')"
            >
              <span class="sub-dot" />
              <span>科室独立盘点</span>
            </div>
          </div>
        </div>

        <!-- 5. 财务精算与对账 -->
        <div v-if="canViewFinancePrint" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/finance' && !currentTab }"
            @click="toggleGroup('finance', '/finance')"
          >
            <SvgIcon name="stats" :size="16" />
            <span v-show="isExpanded" class="item-title">财务精算与对账</span>
            <span v-show="isExpanded" class="side-badge">四联</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.finance }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.finance" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/finance' && (currentTab === 'main-reconciliation' || !currentTab) }"
              @click="navigateMenu('/finance', 'main-reconciliation')"
            >
              <span class="sub-dot" />
              <span>主库发料流向对账</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/finance' && currentTab === 'dept-reconciliation' }"
              @click="navigateMenu('/finance', 'dept-reconciliation')"
            >
              <span class="sub-dot" />
              <span>科室领用消耗对账</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/finance' && currentTab === 'monthly-balance' }"
              @click="navigateMenu('/finance', 'monthly-balance')"
            >
              <span class="sub-dot" />
              <span>进销存月度收发存</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/finance' && currentTab === 'print' }"
              @click="navigateMenu('/finance', 'print')"
            >
              <span class="sub-dot" />
              <span>四联单据标准打印</span>
            </div>
          </div>
        </div>

        <!-- 6. 全院物资流转追溯台账 (去生硬化重构) -->
        <div v-if="canViewWorkflowLog" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/logs' && !currentTab }"
            @click="toggleGroup('logs', '/logs')"
          >
            <SvgIcon name="log" :size="16" />
            <span v-show="isExpanded" class="item-title">物资流转追溯</span>
            <span v-show="isExpanded" class="side-badge">审计</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.logs }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.logs" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/logs' && (!currentTab || currentTab === 'trace') }"
              @click="navigateMenu('/logs', 'trace')"
            >
              <span class="sub-dot" />
              <span>出入库流转台账</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/logs' && currentTab === 'actions' }"
              @click="navigateMenu('/logs', 'actions')"
            >
              <span class="sub-dot" />
              <span>全员操作安全审计</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/logs' && currentTab === 'warning' }"
              @click="navigateMenu('/logs', 'warning')"
            >
              <span class="sub-dot" />
              <span>异常审计预警</span>
            </div>
          </div>
        </div>

        <!-- 7. 医院采购管理与准入中心 (医院内控端) -->
        <div v-if="canViewHospitalProcurement" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/procurement' && !currentTab }"
            @click="toggleGroup('hospitalProc', '/procurement')"
          >
            <SvgIcon name="package" :size="16" />
            <span v-show="isExpanded" class="item-title">采购管理与准入</span>
            <span v-show="isExpanded" class="side-badge">内控</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.hospitalProc }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.hospitalProc" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/procurement' && (!currentTab || currentTab === 'plans') }"
              @click="navigateMenu('/procurement', 'plans')"
            >
              <span class="sub-dot" />
              <span>采购计划与审批</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/procurement' && currentTab === 'suppliers' }"
              @click="navigateMenu('/procurement', 'suppliers')"
            >
              <span class="sub-dot" />
              <span>供应商资质审查</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/procurement' && currentTab === 'tracking' }"
              @click="navigateMenu('/procurement', 'tracking')"
            >
              <span class="sub-dot" />
              <span>采供履约与入库</span>
            </div>
          </div>
        </div>

        <!-- 8. 外部供应商协同门户 (B2B 外部端) -->
        <div v-if="canViewSupplierPortal" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/supplier-portal' && !currentTab }"
            @click="toggleGroup('supplierPortal', '/supplier-portal')"
          >
            <SvgIcon name="upload" :size="16" />
            <span v-show="isExpanded" class="item-title">外部供应商协同</span>
            <span v-show="isExpanded" class="side-badge">协同</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.supplierPortal }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.supplierPortal" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/supplier-portal' && (!currentTab || currentTab === 'orders') }"
              @click="navigateMenu('/supplier-portal', 'orders')"
            >
              <span class="sub-dot" />
              <span>在线配货发货</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/supplier-portal' && currentTab === 'reconcile' }"
              @click="navigateMenu('/supplier-portal', 'reconcile')"
            >
              <span class="sub-dot" />
              <span>采供月度对账</span>
            </div>
          </div>
        </div>

        <!-- 9. 系统与人员管理 (sys_admin 专享 RBAC 一体化) -->
        <div v-if="canViewUsers" class="nav-tree-group">
          <div
            class="side-nav-item parent-item"
            :class="{ active: currentPath === '/users' && !currentTab }"
            @click="toggleGroup('users', '/users')"
          >
            <SvgIcon name="shield" :size="16" />
            <span v-show="isExpanded" class="item-title">系统与人员管理</span>
            <span v-show="isExpanded" class="side-badge">RBAC</span>
            <span v-show="isExpanded" class="chevron-arrow" :class="{ 'is-open': expandedGroups.users }">▾</span>
          </div>
          <div v-show="isExpanded && expandedGroups.users" class="sub-nav-list">
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/users' && (!currentTab || currentTab === 'list') }"
              @click="navigateMenu('/users', 'users')"
            >
              <span class="sub-dot" />
              <span>人员与账号台账</span>
            </div>
            <div
              class="sub-nav-item"
              :class="{ active: currentPath === '/users' && currentTab === 'rbac' }"
              @click="navigateMenu('/users', 'rbac')"
            >
              <span class="sub-dot" />
              <span>RBAC权限矩阵</span>
            </div>
          </div>
        </div>

        <!-- 侧边栏底部在线人员卡片 -->
        <div v-show="isExpanded" class="user-badge-card">
          <div class="user-badge-header">
            <span>当前在线医护凭据</span>
            <span class="online-dot" />
          </div>
          <div class="user-badge-name-row">
            <span class="user-realname">{{ userStore.currentUser.realName }}</span>
            <span class="user-dept-pill">{{ userStore.currentUser.deptName }}</span>
          </div>
          <div class="user-badge-mono-meta font-mono tabular-nums">
            工号: {{ userStore.currentUser.username }} · {{ userStore.currentUser.roleCode }}
          </div>
        </div>
      </aside>

      <!-- 右侧主工作区 (Fusion Workspace Core) -->
      <main class="fusion-main-area">
        <!-- 权限上下文高亮横幅 -->
        <div class="fusion-context-banner">
          <div class="context-desc-box">
            <SvgIcon name="shield" :size="18" color="var(--accent-primary)" />
            <div class="context-text">
              <strong>当前权限上下文：</strong>
              <span>{{ userStore.roleDescription }}</span>
            </div>
          </div>
          <div class="context-meta-tags">
            <span class="context-tag font-mono tabular-nums">经办仓库: {{ currentWarehouseName }}</span>
            <span class="context-tag font-mono tabular-nums">RBAC 15模块 x 8动作</span>
            <span class="context-tag tag-success">全生命周期物权穿透</span>
          </div>
        </div>

        <!-- 核心业务路由视口 -->
        <div class="fusion-router-viewport">
          <router-view />
        </div>
      </main>
    </div>

    <!-- 弹窗组件：15 模块 x 8 动作细粒度 RBAC 抽屉 (sys_admin 独占) -->
    <RbacMatrixDrawer v-model="showRbacDrawer" />

    <!-- 弹窗组件：法定单据四联打印预览中心 -->
    <PrintVoucherDialog v-model="showPrintModal" />

    <!-- 弹窗组件：个人主页与账号安全中心 -->
    <UserProfileModal v-model="showProfileModal" />

    <!-- 弹窗组件：切换系统操作人员账号 (直连数据库真实全院人员) -->
    <el-dialog
      v-model="switchUserModalVisible"
      title="切换系统操作人员账号"
      width="620px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="switch-user-dialog-body">
        <p class="dialog-tip-text">
          从后端数据库实时加载的全院人员档案（包含系统管理员新增人员），点击即可切换当前会话：
        </p>
        <div class="user-search-bar" style="margin-bottom: 12px;">
          <el-input
            v-model="userSearchQuery"
            placeholder="搜索人员姓名、工号或科室..."
            clearable
          />
        </div>
        <div class="user-switch-grid" v-loading="loadingSwitchUsers">
          <div
            v-for="u in filteredSwitchUsers"
            :key="u.id"
            class="switch-user-card"
            :class="{ active: u.id === userStore.currentUser.id }"
            @click="handleDoSwitchUser(u)"
          >
            <div class="switch-avatar font-mono">
              {{ (u.real_name || u.username).trim().charAt(0).toUpperCase() }}
            </div>
            <div class="switch-user-meta">
              <div class="switch-name-row">
                <span class="switch-name">{{ u.real_name || u.username }}</span>
                <span v-if="u.id === userStore.currentUser.id" class="active-badge">当前在用</span>
              </div>
              <div class="switch-sub-row">
                <span class="switch-dept">{{ u.dept_name || '科室' }}</span>
                <span class="switch-role-tag">{{ formatRoleName(u.role_code) }}</span>
              </div>
              <div class="switch-account font-mono">工号: {{ u.username }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * @file MainLayout.vue
 * @description 医院医疗物资全链路管理系统主布局
 * 集成：树形自适应侧边栏（自动收缩、悬停滑动展开、图钉Pin常驻切换）、顶栏当前仓库沉浸切换器、两级树形菜单导航。
 */

import { ref, computed, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore, PRESET_USERS, type UserProfile } from '@/stores/userStore';
import { httpGet } from '@/api/request';
import SvgIcon from '@/components/common/SvgIcon.vue';
import RbacMatrixDrawer from '@/components/RbacMatrixDrawer.vue';
import PrintVoucherDialog from '@/components/PrintVoucherDialog.vue';
import UserProfileModal from '@/components/UserProfileModal.vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const showRbacDrawer = ref(false);
const showPrintModal = ref(false);
const showProfileModal = ref(false);

// 真实切换人员弹窗与数据
const switchUserModalVisible = ref(false);
const loadingSwitchUsers = ref(false);
const allDbUsers = ref<any[]>([]);
const userSearchQuery = ref('');

// 侧边栏折叠与固定状态控制
const isPinned = ref(localStorage.getItem('spd_sidebar_pinned') !== 'false');
const isHovered = ref(false);
let hoverTimeout: any = null;

const isExpanded = computed(() => isPinned.value || isHovered.value);

const currentPath = computed(() => route.path);
const currentTab = computed(() => (route.query.tab as string) || '');

// 两级树形菜单展开折叠状态
const expandedGroups = ref<Record<string, boolean>>({
  dict: true,
  general: true,
  highValue: false,
  secondary: true,
  finance: false,
  logs: false,
  hospitalProc: false,
  supplierPortal: false,
  users: false
});

/**
 * 切换侧边栏图钉固定状态
 */
function togglePin() {
  isPinned.value = !isPinned.value;
  localStorage.setItem('spd_sidebar_pinned', String(isPinned.value));
  ElMessage.success({
    message: isPinned.value ? '侧边栏已固定为常驻展开模式' : '侧边栏已设置为自适应模式(鼠标移入自动滑出)',
    duration: 1800
  });
}

/**
 * 鼠标移入侧边栏展开
 */
function handleMouseEnter() {
  if (isPinned.value) return;
  if (hoverTimeout) clearTimeout(hoverTimeout);
  hoverTimeout = setTimeout(() => {
    isHovered.value = true;
  }, 100);
}

/**
 * 鼠标移出侧边栏收缩
 */
function handleMouseLeave() {
  if (isPinned.value) return;
  if (hoverTimeout) clearTimeout(hoverTimeout);
  hoverTimeout = setTimeout(() => {
    isHovered.value = false;
  }, 150);
}

/**
 * 切换一级菜单树折叠与跳转
 */
function toggleGroup(groupKey: string, defaultPath: string) {
  expandedGroups.value[groupKey] = !expandedGroups.value[groupKey];
  if (currentPath.value !== defaultPath) {
    router.push(defaultPath);
  }
}

/**
 * 点击二级子菜单导航
 */
function navigateMenu(path: string, tab?: string) {
  if (tab) {
    router.push({ path, query: { tab } });
  } else {
    router.push(path);
  }
}

/**
 * 切换全局当前经办仓库
 */
function handleWarehouseChange(e: Event) {
  const target = e.target as HTMLSelectElement;
  userStore.setCurrentWarehouse(target.value);
  ElMessage.success(`已切换当前经办仓库为：${currentWarehouseName.value}`);
}

const currentWarehouseName = computed(() => {
  const found = userStore.authorizedWarehouses.find(w => w.code === userStore.currentWarehouseCode);
  return found ? found.name : '卫材库房';
});

// 细粒度 RBAC 权限判断
const canViewProductDict = computed(() => userStore.canAction('DICT_MANAGE', 'can_view'));
const canViewGeneralMaterial = computed(() => userStore.canAction('GEN_INBOUND', 'can_view') || userStore.canAction('GEN_OUTBOUND', 'can_view'));
const canViewHighValue = computed(() => (
  userStore.canAction('HV_PREP_RECEIVE', 'can_view') ||
  userStore.canAction('HV_QR_VERIFY', 'can_view') ||
  userStore.canAction('HV_RETURN', 'can_view')
));
const canViewSecondaryWarehouse = computed(() => userStore.canAction('SEC_WAREHOUSE', 'can_view'));
const canViewWorkflowLog = computed(() => userStore.canAction('WORKFLOW_LOG', 'can_view'));
const canViewFinancePrint = computed(() => userStore.canAction('FINANCE_AUDIT', 'can_view'));
const canViewHospitalProcurement = computed(() => userStore.currentUser.roleCode !== 'supplier_user');
const canViewSupplierPortal = computed(() => (
  userStore.currentUser.roleCode === 'supplier_user' || userStore.currentUser.roleCode === 'sys_admin'
));
const canViewUsers = computed(() => userStore.currentUser.roleCode === 'sys_admin');

watch(
  () => userStore.currentUser.roleCode,
  async () => {
    await userStore.fetchPermissions();
  }
);

onMounted(() => {
  document.documentElement.setAttribute('data-theme', userStore.theme);
  userStore.fetchPermissions();
});

const userRoleLabel = computed(() => {
  const roleMap: Record<string, string> = {
    sys_admin: '信息科管理员',
    dept_manager: '主库科室主管',
    secondary_user: '二级库护士/技师',
    finance_auditor: '财务科审计主管',
    supplier_user: '外部供应商代表'
  };
  return roleMap[userStore.currentUser.roleCode] || '操作人员';
});

function formatRoleName(roleCode: string) {
  const roleMap: Record<string, string> = {
    sys_admin: '系统管理员',
    dept_manager: '主库房主管',
    secondary_user: '二级库人员',
    finance_auditor: '财务审计员',
    supplier_user: '供应商代表'
  };
  return roleMap[roleCode] || roleCode;
}

/**
 * 过滤可供切换的人员列表
 */
const filteredSwitchUsers = computed(() => {
  const q = userSearchQuery.value.trim().toLowerCase();
  if (!q) return allDbUsers.value;
  return allDbUsers.value.filter((u) => {
    return (
      (u.real_name && u.real_name.toLowerCase().includes(q)) ||
      (u.username && u.username.toLowerCase().includes(q)) ||
      (u.dept_name && u.dept_name.toLowerCase().includes(q)) ||
      (u.role_code && u.role_code.toLowerCase().includes(q))
    );
  });
});

/**
 * 打开切换人员账号弹窗，从数据库实时拉取全员清单
 */
async function openSwitchUserModal() {
  switchUserModalVisible.value = true;
  loadingSwitchUsers.value = true;
  try {
    const res = await httpGet<any>('/users');
    if (Array.isArray(res)) {
      allDbUsers.value = res;
    } else if (res && res.data) {
      allDbUsers.value = Array.isArray(res.data) ? res.data : (res.data.items || []);
    } else if (res && res.items) {
      allDbUsers.value = res.items;
    } else {
      allDbUsers.value = [];
    }
  } catch (err) {
    console.warn('获取全院人员列表失败，使用本地预设人员', err);
    allDbUsers.value = PRESET_USERS.map((u) => ({
      id: u.id,
      username: u.username,
      real_name: u.realName,
      role_code: u.roleCode,
      dept_name: u.deptName,
      dept_code: u.deptCode
    }));
  } finally {
    loadingSwitchUsers.value = false;
  }
}

/**
 * 选中目标人员，即时无缝切换会话凭据并根据新角色分发路由与工作仓
 */
async function handleDoSwitchUser(target: any) {
  const roleCode = target.role_code;
  const mappedUser: UserProfile = {
    id: target.id,
    username: target.username,
    realName: target.real_name || target.username,
    roleCode: roleCode as any,
    deptCode: target.dept_code || 'INFO_DEPT',
    deptName: target.dept_name || '信息科'
  };

  userStore.currentUser = mappedUser;
  userStore.token = `spd_token_${mappedUser.username}_${Date.now()}`;
  userStore.syncStorage(true, mappedUser, userStore.token);
  await userStore.fetchPermissions();

  ElMessage.success(`已成功切换工作台人员会话：${mappedUser.realName} (${mappedUser.deptName})`);
  switchUserModalVisible.value = false;

  // 根据切换后的角色自动进入其有权限的核心视图与作业仓
  if (roleCode === 'secondary_user') {
    userStore.setCurrentWarehouse('WH_SEC_ORTHO');
    router.push('/secondary');
  } else if (roleCode === 'finance_auditor') {
    router.push('/finance');
  } else if (roleCode === 'supplier_user') {
    router.push('/supplier-portal');
  } else if (roleCode === 'dept_manager') {
    userStore.setCurrentWarehouse('WH_WEICAI');
    router.push('/general');
  } else {
    userStore.setCurrentWarehouse('ALL');
    router.push('/dict');
  }
}

function handleJumpShowcase() {
  router.push('/showcase');
}

function handleLogout() {
  userStore.logout();
  ElMessage.info('已安全退出当前会话');
  router.push('/showcase?login=1');
}
</script>

<style scoped>
.fusion-app-shell {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  color: var(--text-primary);
  overflow: hidden;
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.fusion-ambient-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 280px;
  background: radial-gradient(circle at 50% -20%, rgba(56, 189, 248, 0.12) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* 顶部全局导航栏 */
.top-navbar {
  height: 60px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-card);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  z-index: 30;
}

.brand-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
}

.brand-text h1 {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.brand-text p {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.2px;
  margin: 2px 0 0 0;
}

.top-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 仓库切换下拉 */
.warehouse-switch-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.35);
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12.5px;
  transition: all 0.15s ease;
}

.warehouse-switch-wrap .wh-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent-primary);
}

.warehouse-switch-wrap select {
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 12.5px;
  font-weight: 700;
  outline: none;
  cursor: pointer;
}

.warehouse-switch-wrap select option {
  background: var(--bg-card);
  color: var(--text-primary);
}

/* 真实登录人员芯片卡 */
.user-profile-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.28);
  padding: 3px 10px 3px 6px;
  border-radius: 20px;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.user-profile-chip:hover {
  background: rgba(56, 189, 248, 0.16);
  border-color: var(--accent-primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
}

.user-chip-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--accent-gradient);
  color: #080c14;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-chip-text {
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-chip-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-chip-badge {
  font-size: 11px;
  color: var(--accent-primary);
  background: rgba(56, 189, 248, 0.12);
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 500;
}

.btn-ctrl-switch {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.24);
  color: var(--text-secondary);
}

.btn-ctrl-switch:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

/* 切换人员弹窗卡片网格 */
.switch-user-dialog-body {
  padding: 4px;
}

.dialog-tip-text {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.user-switch-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-height: 380px;
  overflow-y: auto;
  padding-right: 4px;
}

.switch-user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid var(--border-divider);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-user-card:hover {
  border-color: var(--accent-primary);
  background: rgba(56, 189, 248, 0.08);
  transform: translateY(-1px);
}

.switch-user-card.active {
  border-color: var(--color-success);
  background: rgba(52, 211, 153, 0.08);
}

.switch-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--accent-gradient);
  color: #080c14;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.switch-user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.switch-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.switch-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.active-badge {
  font-size: 10.5px;
  color: var(--color-success);
  font-weight: 600;
}

.switch-sub-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  color: var(--text-muted);
}

.switch-role-tag {
  color: var(--accent-primary);
}

.switch-account {
  font-size: 11px;
  color: var(--text-muted);
  opacity: 0.8;
}

.btn-ctrl {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.15s ease-out;
  user-select: none;
}

.btn-ctrl:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  transform: translateY(-1px);
}

.btn-ctrl-primary {
  background: linear-gradient(135deg, #0284c7, #0ea5e9);
  color: #ffffff;
  border-color: #0ea5e9;
  box-shadow: 0 2px 10px rgba(14, 165, 233, 0.35);
}

.btn-ctrl-primary:hover {
  color: #ffffff;
  opacity: 0.94;
}

.btn-ctrl-rbac {
  border-color: rgba(56, 189, 248, 0.4);
  color: var(--accent-primary);
}

.btn-ctrl-danger {
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--color-danger);
}

.btn-ctrl-danger:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.btn-ctrl-icon {
  padding: 7px 9px;
}

/* 主体融合工作台 */
.fusion-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* 浮动模式下的占位窄边 */
.sidebar-placeholder-strip {
  width: 58px;
  flex-shrink: 0;
}

/* 树形自适应侧边栏 */
.fusion-sidebar {
  background: var(--bg-card);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid var(--border-card);
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow-y: auto;
  flex-shrink: 0;
  user-select: none;
  transition: width 0.28s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}

.fusion-sidebar.is-pinned {
  width: 248px;
  position: relative;
}

.fusion-sidebar.is-floating {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 100;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.24);
}

.fusion-sidebar.is-floating.is-collapsed {
  width: 58px;
  padding: 12px 6px;
}

.fusion-sidebar.is-floating.is-expanded {
  width: 248px;
}

.sidebar-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px 8px;
  border-bottom: 1px solid var(--border-divider);
  margin-bottom: 6px;
}

.side-nav-group-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-pin-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-card);
  color: var(--text-secondary);
  border-radius: 6px;
  padding: 3px 6px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-pin-toggle:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
}

.btn-pin-toggle.active {
  background: rgba(56, 189, 248, 0.14);
  color: var(--accent-primary);
  border-color: rgba(56, 189, 248, 0.35);
}

/* 导航树组 */
.nav-tree-group {
  display: flex;
  flex-direction: column;
}

.side-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease-out;
  border: 1px solid transparent;
}

.side-nav-item:hover {
  background: rgba(56, 189, 248, 0.08);
  color: var(--text-primary);
}

.side-nav-item.active {
  background: rgba(56, 189, 248, 0.14);
  color: var(--accent-primary);
  border-color: rgba(56, 189, 248, 0.3);
}

.item-title {
  white-space: nowrap;
}

.chevron-arrow {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-muted);
  transition: transform 0.2s ease;
}

.chevron-arrow.is-open {
  transform: rotate(180deg);
}

.side-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.15);
  color: var(--accent-primary);
  margin-left: auto;
  margin-right: 4px;
}

/* 二级子菜单列表 */
.sub-nav-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 3px 0 5px 22px;
}

.sub-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.12s ease;
}

.sub-nav-item:hover {
  background: rgba(56, 189, 248, 0.08);
  color: var(--text-primary);
}

.sub-nav-item.active {
  background: rgba(56, 189, 248, 0.18);
  color: var(--accent-primary);
  font-weight: 700;
}

.sub-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: all 0.15s;
}

.sub-nav-item.active .sub-dot {
  background: var(--accent-primary);
  box-shadow: 0 0 6px var(--accent-primary);
}

/* 侧边栏底部在线人员卡片 */
.user-badge-card {
  margin-top: auto;
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-badge-header {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.online-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 5px var(--color-success);
}

.user-badge-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.user-realname {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

.user-dept-pill {
  font-size: 10.5px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
  white-space: nowrap;
}

.user-badge-mono-meta {
  font-size: 10.5px;
  color: var(--text-muted);
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 右侧主工作区 */
.fusion-main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-page);
}

.fusion-context-banner {
  height: 44px;
  padding: 0 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-divider);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.context-desc-box {
  display: flex;
  align-items: center;
  gap: 10px;
}

.context-text {
  font-size: 12.5px;
  color: var(--text-secondary);
}

.context-text strong {
  color: var(--accent-primary);
  font-weight: 700;
}

.context-meta-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.context-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(56, 189, 248, 0.1);
  color: var(--accent-primary);
  border: 1px solid rgba(56, 189, 248, 0.2);
}

.tag-success {
  background: var(--color-success-bg);
  color: var(--color-success);
  border-color: rgba(16, 185, 129, 0.3);
}

.fusion-router-viewport {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}
</style>
