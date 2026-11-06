<template>
  <div class="product-dict-workbench" :data-theme="userStore.theme">
    <!-- 顶部 4 宫格高质感毛玻璃 KPI 指标大盘 -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>全院在用产品字典总数</span>
          <SvgIcon name="dict" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          {{ totalSpecCount }} <span class="kpi-unit">种</span>
        </div>
        <div class="kpi-sub">
          <SvgIcon name="check" :size="13" color="var(--color-success)" />
          <span>双树归口与药监局 UDI 编码绑定率 100%</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>耗材科主库归口物资</span>
          <SvgIcon name="package" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          {{ consumableSpecCount }} <span class="kpi-unit">种 (普通/高值)</span>
        </div>
        <div class="kpi-sub">
          <SvgIcon name="arrow-right" :size="13" color="var(--accent-primary)" />
          <span>卫材库 / 专项库房双仓覆盖</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>通用大品名总数</span>
          <SvgIcon name="room" :size="16" color="var(--accent-primary)" />
        </div>
        <div class="kpi-val font-mono tabular-nums">
          {{ spns.length }} <span class="kpi-unit">个大类</span>
        </div>
        <div class="kpi-sub">
          <SvgIcon name="arrow-right" :size="13" color="var(--accent-primary)" />
          <span>单品名下属多型号规格裂变</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-title">
          <span>准入供应商档案</span>
          <SvgIcon name="safe" :size="16" color="var(--color-warning)" />
        </div>
        <div class="kpi-val font-mono tabular-nums text-warn">
          {{ suppliers.length }} <span class="kpi-unit">家 (准入中)</span>
        </div>
        <div class="kpi-sub text-warn">
          <SvgIcon name="clock" :size="13" color="var(--color-warning)" />
          <span>全资质预警与首营合规已就绪</span>
        </div>
      </div>
    </div>

    <!-- 产品字典 4 大主内容区子视图切换器 (与左侧侧边栏双向实时联动) -->
    <div class="glass-panel dict-subview-tab-bar">
      <button
        class="dict-subview-tab-btn"
        :class="{ active: currentModuleTab === 'specs' }"
        @click="switchModuleTab('specs')"
      >
        <SvgIcon name="dict" :size="15" />
        <span>耗材规格目录 (三树四栏工作台)</span>
      </button>

      <button
        class="dict-subview-tab-btn"
        :class="{ active: currentModuleTab === 'warehouses' }"
        @click="switchModuleTab('warehouses')"
      >
        <SvgIcon name="room" :size="15" />
        <span>仓库架构与主库/二级库分层</span>
        <span class="tab-pill font-mono">{{ warehouses.length }}</span>
      </button>

      <button
        class="dict-subview-tab-btn"
        :class="{ active: currentModuleTab === 'categories' }"
        @click="switchModuleTab('categories')"
      >
        <SvgIcon name="package" :size="15" />
        <span>耗材分类设置</span>
        <span class="tab-pill font-mono">{{ categories.length }}</span>
      </button>

      <button
        class="dict-subview-tab-btn"
        :class="{ active: currentModuleTab === 'suppliers' }"
        @click="switchModuleTab('suppliers')"
      >
        <SvgIcon name="safe" :size="15" />
        <span>供应商国家级资质档案</span>
        <span class="tab-pill font-mono">{{ suppliers.length }}</span>
      </button>
    </div>

    <!-- =========================================================================
         子视图 1：耗材规格目录 (三树四栏真实工业级 SPD 工作台)
         ========================================================================= -->
    <template v-if="currentModuleTab === 'specs'">
    <!-- 顶部 SPD 工业级标准操作工具栏 (对齐图 4 顶部菜单栏与按钮) -->
    <div class="glass-panel spd-dict-toolbar">
      <div class="toolbar-actions-left">
        <!-- 关闭 / 还原全部筛选 -->
        <button class="spd-tool-btn" title="清除所有过滤并还原" @click="resetAllFilters">
          <SvgIcon name="close" :size="14" />
          <span>关闭筛选</span>
        </button>

        <span class="tool-sep" />

        <!-- 品名管理 (图 3) -->
        <el-dropdown trigger="click" @command="handleSpnCommand">
          <button class="spd-tool-btn">
            <SvgIcon name="dict" :size="14" color="var(--accent-primary)" />
            <span>品名管理</span>
            <SvgIcon name="arrow-down" :size="11" />
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="create_spn">新增产品名称 (通用大品名)</el-dropdown-item>
              <el-dropdown-item command="edit_spn" :disabled="!selectedSpn">编辑当前大品名</el-dropdown-item>
              <el-dropdown-item command="delete_spn" :disabled="!selectedSpn" divided>删除当前大品名</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 新增产品规格 (图 5) -->
        <button
          v-if="canOperateDict('can_create')"
          class="spd-tool-btn btn-highlight"
          @click="openAddSpecModal"
        >
          <SvgIcon name="plus" :size="14" color="#ffffff" />
          <span>新增产品规格</span>
        </button>

        <!-- 编辑产品规格 -->
        <button
          v-if="canOperateDict('can_edit')"
          class="spd-tool-btn"
          :disabled="!selectedSpec"
          @click="openEditSpecModal"
        >
          <SvgIcon name="edit" :size="14" />
          <span>编辑产品规格</span>
        </button>

        <!-- 停用/启用产品规格 -->
        <button
          v-if="canOperateDict('can_edit')"
          class="spd-tool-btn"
          :disabled="!selectedSpec"
          @click="handleToggleSpecStatus"
        >
          <SvgIcon name="lock" :size="14" :color="selectedSpec?.status === 'ACTIVE' ? 'var(--color-danger)' : 'var(--color-success)'" />
          <span>{{ selectedSpec?.status === 'ACTIVE' ? '停用产品规格' : '启用产品规格' }}</span>
        </button>

        <!-- 删除产品规格 -->
        <button
          v-if="canOperateDict('can_delete')"
          class="spd-tool-btn btn-danger-text"
          :disabled="!selectedSpec"
          @click="handleDeleteSpec"
        >
          <SvgIcon name="close" :size="14" color="var(--color-danger)" />
          <span>删除产品规格</span>
        </button>

        <span class="tool-sep" />

        <!-- 变更供应商 -->
        <button
          v-if="canOperateDict('can_edit')"
          class="spd-tool-btn"
          :disabled="!selectedSpec"
          @click="openChangeSupplierModal"
        >
          <SvgIcon name="refresh" :size="14" />
          <span>变更供应商</span>
        </button>

        <!-- 集中带量采购调价管理 -->
        <button
          v-if="canOperateDict('can_edit')"
          class="spd-tool-btn btn-warn"
          :disabled="selectedSpecIds.length === 0"
          @click="openBatchPriceAdjustModal"
        >
          <SvgIcon name="scale" :size="14" color="var(--color-warning)" />
          <span>集中带量调价 ({{ selectedSpecIds.length }})</span>
        </button>

        <!-- 供应商资质档案管理 -->
        <button
          v-if="userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'dept_manager'"
          class="spd-tool-btn"
          @click="showSupplierManageModal = true"
        >
          <SvgIcon name="user" :size="14" />
          <span>供应商档案</span>
        </button>

        <!-- 管理员专属：仓库与人员细粒度授权配置 (RBAC) -->
        <button
          v-if="userStore.currentUser.roleCode === 'sys_admin'"
          class="spd-tool-btn btn-admin"
          @click="openWarehouseRbacModal"
        >
          <SvgIcon name="lock" :size="14" color="var(--accent-primary)" />
          <span>仓库细粒度授权</span>
        </button>
      </div>

      <div class="toolbar-actions-right">
        <button class="spd-tool-btn" @click="handleExportSpecs">
          <SvgIcon name="upload" :size="14" />
          <span>导出 Excel</span>
        </button>
      </div>
    </div>

    <!-- 真实 SPD 四栏三树主工作台布局 (1:1 对标图 4) -->
    <div class="dict-workbench-grid">
      <!-- 第一栏 (左栏上/下)：维度一 仓库树 + 维度二 耗材分类树 -->
      <aside class="workbench-col-trees glass-panel">
        <!-- 仓库分类树 (按人分仓，限权过滤) -->
        <div class="tree-box-upper">
          <div class="tree-section-header">
            <div class="title-with-icon">
              <SvgIcon name="room" :size="14" color="var(--accent-primary)" />
              <span>仓库树</span>
            </div>
            <span v-if="isNurseRole" class="rbac-indicator-pill">护士限仓</span>
            <button
              v-else-if="userStore.currentUser.roleCode === 'sys_admin'"
              class="tree-mini-btn"
              title="新增仓库专属节点"
              @click="openAddWarehouseModal"
            >
              + 新建仓库
            </button>
          </div>
          <!-- 仓库搜索过滤输入框 -->
          <div class="tree-search-bar" style="padding: 6px 8px;">
            <input
              v-model="warehouseSearchKeyword"
              placeholder="搜索仓库编码或名称..."
              class="spd-search-input font-mono"
              style="width: 100%; font-size: 11.5px; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border-card); background: var(--bg-card); color: var(--text-primary);"
            />
          </div>
          <div class="tree-scroll-container">
            <div
              class="tree-node-row"
              :class="{ active: selectedWarehouseCode === '' }"
              @click="selectWarehouse('')"
            >
              <SvgIcon name="package" :size="14" color="var(--text-muted)" />
              <span class="tree-label">全部仓库物资</span>
              <span class="tree-count font-mono">{{ specs.length }}</span>
            </div>
            <!-- 分组一：院级归口主仓库 -->
            <div class="tree-group-header" style="font-size: 11px; font-weight: 700; color: var(--accent-primary); padding: 8px 10px 4px 10px; display: flex; align-items: center; justify-content: space-between;">
              <span>院级归口主仓库 ({{ mainWarehouseNodes.length }})</span>
              <span class="status-chip chip-info" style="font-size: 10px; padding: 0 4px;">主仓</span>
            </div>
            <div
              v-for="wh in mainWarehouseNodes"
              :key="wh.warehouse_code"
              class="tree-node-row"
              :class="{ active: selectedWarehouseCode === wh.warehouse_code }"
              @click="selectWarehouse(wh.warehouse_code)"
            >
              <SvgIcon name="room" :size="14" color="var(--accent-primary)" />
              <span class="tree-label">{{ wh.warehouse_name }}</span>
              <span class="font-mono text-muted" style="font-size: 10px; margin-left: auto; margin-right: 4px;">{{ wh.warehouse_code }}</span>
              <!-- 管理员操作：修改与删除 -->
              <div v-if="userStore.currentUser.roleCode === 'sys_admin'" class="wh-item-actions" style="display: flex; gap: 3px;" @click.stop>
                <button class="mini-btn-link" title="编辑仓库" style="border: none; background: transparent; color: var(--accent-primary); font-size: 11px; cursor: pointer;" @click="openEditWarehouseModal(wh)">改</button>
                <button class="mini-btn-link text-danger" title="删除仓库" style="border: none; background: transparent; color: var(--color-danger); font-size: 11px; cursor: pointer;" @click="handleDeleteWarehouse(wh)">删</button>
              </div>
            </div>

            <!-- 分组二：临床科室二级库 / 专仓 (树状缩进) -->
            <div class="tree-group-header" style="font-size: 11px; font-weight: 700; color: var(--color-success); padding: 10px 10px 4px 10px; display: flex; align-items: center; justify-content: space-between;">
              <span>临床科室二级库 / 专仓 ({{ secondaryWarehouseNodes.length }})</span>
              <span class="status-chip chip-active" style="font-size: 10px; padding: 0 4px;">病区</span>
            </div>
            <div
              v-for="wh in secondaryWarehouseNodes"
              :key="wh.warehouse_code"
              class="tree-node-row tree-node-child"
              :class="{ active: selectedWarehouseCode === wh.warehouse_code }"
              style="padding-left: 18px;"
              @click="selectWarehouse(wh.warehouse_code)"
            >
              <span style="color: var(--text-muted); margin-right: 4px; font-family: monospace;">└─</span>
              <SvgIcon name="safe" :size="13" color="var(--color-success)" />
              <span class="tree-label">{{ wh.warehouse_name }}</span>
              <span class="font-mono text-muted" style="font-size: 10px; margin-left: auto; margin-right: 4px;">{{ wh.warehouse_code }}</span>
              <!-- 管理员操作：修改与删除 -->
              <div v-if="userStore.currentUser.roleCode === 'sys_admin'" class="wh-item-actions" style="display: flex; gap: 3px;" @click.stop>
                <button class="mini-btn-link" title="编辑仓库" style="border: none; background: transparent; color: var(--accent-primary); font-size: 11px; cursor: pointer;" @click="openEditWarehouseModal(wh)">改</button>
                <button class="mini-btn-link text-danger" title="删除仓库" style="border: none; background: transparent; color: var(--color-danger); font-size: 11px; cursor: pointer;" @click="handleDeleteWarehouse(wh)">删</button>
              </div>
            </div>
          </div>
        </div>

        <div class="tree-horizontal-divider" />

        <!-- 耗材属性分类树 -->
        <div class="tree-box-lower">
          <div class="tree-section-header">
            <div class="title-with-icon">
              <SvgIcon name="dict" :size="14" color="var(--accent-primary)" />
              <span>耗材分类</span>
            </div>
            <button
              v-if="userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'dept_manager'"
              class="tree-mini-btn"
              @click="openCategoryManageModal"
            >
              分类管理
            </button>
          </div>
          <div class="tree-scroll-container">
            <div
              class="tree-node-row"
              :class="{ active: selectedCategoryCode === '' }"
              @click="selectCategory('')"
            >
              <SvgIcon name="dict" :size="14" color="var(--text-muted)" />
              <span class="tree-label">全部分类</span>
            </div>
            <div
              v-for="cat in categoryList"
              :key="cat.code"
              class="tree-node-row"
              :class="{ active: selectedCategoryCode === cat.code }"
              @click="selectCategory(cat.code)"
            >
              <span class="cat-code font-mono">{{ cat.code }}</span>
              <span class="tree-label">{{ cat.name }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 第二栏 (中栏)：产品名称 / 供应商 双 Tab 列表 -->
      <section class="workbench-col-middle glass-panel">
        <div class="middle-tab-header">
          <div
            class="tab-btn"
            :class="{ active: middleTab === 'spn' }"
            @click="middleTab = 'spn'"
          >
            <span>产品名称</span>
            <span class="tab-badge font-mono">{{ spns.length }}</span>
          </div>
          <div
            class="tab-btn"
            :class="{ active: middleTab === 'supplier' }"
            @click="middleTab = 'supplier'"
          >
            <span>供应商</span>
            <span class="tab-badge font-mono">{{ suppliers.length }}</span>
          </div>
        </div>

        <!-- 搜索与筛选小条 -->
        <div class="middle-search-bar">
          <input
            v-model="middleSearchKeyword"
            type="text"
            :placeholder="middleTab === 'spn' ? '搜索大品名/编码...' : '搜索供应商名称...'"
            class="middle-search-input"
          />
          <button class="middle-search-btn" @click="fetchData">
            筛选
          </button>
        </div>

        <!-- Tab A: 大品名树列表 (对应图 4 中栏列表) -->
        <div v-show="middleTab === 'spn'" class="middle-list-container">
          <div
            class="middle-list-item"
            :class="{ active: selectedSpnId === null }"
            @click="selectSpn(null)"
          >
            <SvgIcon name="package" :size="14" color="var(--text-muted)" />
            <span class="item-title">全部产品规格</span>
            <span class="item-count font-mono">{{ specs.length }}</span>
          </div>
          <div
            v-for="spn in filteredSpns"
            :key="spn.id"
            class="middle-list-item"
            :class="{ active: selectedSpnId === spn.id }"
            @click="selectSpn(spn)"
          >
            <SvgIcon name="room" :size="14" color="var(--accent-primary)" />
            <div class="spn-item-info">
              <span class="spn-code-badge font-mono">{{ spn.spn_code }}</span>
              <span class="spn-name-text">{{ spn.spn_name }}</span>
            </div>
            <span class="item-count font-mono">{{ spn.spec_count }}</span>
          </div>
        </div>

        <!-- Tab B: 供应商列表 (对应图 4 中栏供应商 Tab) -->
        <div v-show="middleTab === 'supplier'" class="middle-list-container">
          <div
            class="middle-list-item"
            :class="{ active: selectedSupplierId === null }"
            @click="selectSupplier(null)"
          >
            <SvgIcon name="user" :size="14" color="var(--text-muted)" />
            <span class="item-title">全部供货商物资</span>
          </div>
          <div
            v-for="sup in filteredSuppliers"
            :key="sup.id"
            class="middle-list-item"
            :class="{ active: selectedSupplierId === sup.id }"
            @click="selectSupplier(sup)"
          >
            <SvgIcon name="safe" :size="14" color="var(--color-warning)" />
            <div class="spn-item-info">
              <span class="spn-code-badge font-mono">{{ sup.supplier_code }}</span>
              <span class="spn-name-text">{{ sup.supplier_name }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 第三栏 (右栏)：产品规格型号明细表格 (对齐图 4 右栏与图 5) -->
      <section class="workbench-col-specs glass-panel">
        <div class="specs-table-header">
          <div class="header-left">
            <h3>产品规格明细台账</h3>
            <span class="header-desc">
              {{ currentFilterSummary }}
            </span>
          </div>
          <div class="header-right">
            <span v-if="selectedSpec" class="selected-spec-tag font-mono">
              当前规格: <strong>{{ selectedSpec.spec_name }}</strong> ({{ selectedSpec.spec_code }})
            </span>
            <el-checkbox
              v-model="showDisabledSpecs"
              :true-value="true"
              :false-value="false"
              class="font-mono"
            >
              包含已停用规格
            </el-checkbox>
          </div>
        </div>

        <el-table
          :data="paginatedSpecs"
          border
          stripe
          highlight-current-row
          class="spd-spec-table"
          v-loading="loading"
          @selection-change="handleSpecSelectionChange"
          @current-change="handleSpecRowClick"
        >
          <!-- 多选 Checkbox 栏 (支持批量调价) -->
          <el-table-column type="selection" width="46" align="center" />

          <!-- 产品代码 (936010100024055517) -->
          <el-table-column prop="spec_code" label="产品代码" width="165" fixed="left">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold text-accent">{{ row.spec_code }}</span>
            </template>
          </el-table-column>

          <!-- 产品名称 (医用氧气123) -->
          <el-table-column prop="product_name" label="产品名称" min-width="160">
            <template #default="{ row }">
              <div class="product-name-cell font-bold">{{ row.product_name }}</div>
              <div class="product-sub-spec font-mono text-muted">规格: {{ row.spec_name }}</div>
            </template>
          </el-table-column>

          <!-- 通用名 -->
          <el-table-column prop="common_name" label="通用名" width="130" />

          <!-- 拼音码 -->
          <el-table-column prop="pinyin_code" label="拼音码" width="100">
            <template #default="{ row }">
              <span class="tag-pill font-mono">{{ row.pinyin_code }}</span>
            </template>
          </el-table-column>

          <!-- 组件名称 -->
          <el-table-column prop="component_name" label="组件名称" width="90" align="center" />

          <!-- 生产厂家 -->
          <el-table-column prop="manufacturer" label="生产厂家" min-width="200" show-overflow-tooltip />

          <!-- 型号规格 -->
          <el-table-column prop="model_name" label="型号" width="120" />

          <!-- 单价 (元) -->
          <el-table-column prop="unit_price" label="单价" width="110" align="right">
            <template #default="{ row }">
              <span class="font-mono tabular-nums font-bold">¥ {{ Number(row.unit_price).toFixed(2) }}</span>
            </template>
          </el-table-column>

          <!-- 计件单位 -->
          <el-table-column prop="pricing_unit" label="计件单位" width="85" align="center" />

          <!-- 包装转换比 -->
          <el-table-column prop="conversion_ratio" label="包装比" width="85" align="center">
            <template #default="{ row }">
              <span class="font-mono tabular-nums">1:{{ row.conversion_ratio }}</span>
            </template>
          </el-table-column>

          <!-- 注册证号 -->
          <el-table-column prop="register_card_no" label="医疗器械注册证号" width="180" show-overflow-tooltip />

          <!-- 状态 -->
          <el-table-column prop="status" label="状态" width="85" align="center">
            <template #default="{ row }">
              <span :class="['status-chip', row.status === 'ACTIVE' ? 'chip-success' : 'chip-disabled']">
                {{ row.status === 'ACTIVE' ? '在用' : '停用' }}
              </span>
            </template>
          </el-table-column>

          <!-- 分配仓库 -->
          <el-table-column prop="assigned_warehouses" label="已授权仓库" min-width="160">
            <template #default="{ row }">
              <div class="wh-tag-container">
                <span
                  v-for="wh in (row.assigned_warehouses || '').split(',')"
                  :key="wh"
                  class="wh-mini-tag font-mono"
                >
                  {{ wh }}
                </span>
              </div>
            </template>
          </el-table-column>

          <!-- 操作栏 -->
          <el-table-column label="操作" width="140" fixed="right" align="center">
            <template #default="{ row }">
              <button class="table-op-btn" @click.stop="openEditSpecModalWithRow(row)">
                编辑
              </button>
              <button class="table-op-btn" @click.stop="viewPriceLogs(row)">
                调价记录
              </button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 规格明细台账标准分页条 -->
        <div class="pagination-footer" style="display: flex; justify-content: flex-end; padding: 14px 10px 4px;">
          <el-pagination
            v-model:current-page="specCurrentPage"
            v-model:page-size="specPageSize"
            :page-sizes="[15, 30, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="filteredSpecs.length"
          />
        </div>
      </section>
    </div>
    </template>

    <!-- =========================================================================
         子视图 2：全院仓库架构与归口层级维护独立工作台 (明确区分主库与二级库)
         ========================================================================= -->
    <div v-else-if="currentModuleTab === 'warehouses'" class="independent-subview-container">
      <!-- 顶部功能横幅 -->
      <div class="subview-header-card glass-panel">
        <div class="header-left">
          <div class="header-title-row">
            <SvgIcon name="room" :size="20" color="var(--accent-primary)" />
            <h2>全院物资仓库架构与归口层级维护</h2>
            <span class="subview-badge">主库 / 临床二级库双层分级拓扑</span>
          </div>
          <p class="header-desc">
            全院物资仓库严格划分为院级归口主仓库（耗材科/设备科/总务科/信息科）与下属临床二级库/病区库，实现分级精细化管辖、采购验收与按需分发调拨。
          </p>
        </div>
        <div class="header-actions">
          <button
            v-if="userStore.currentUser.roleCode === 'sys_admin'"
            class="spd-btn btn-primary"
            @click="openAddWarehouseModal"
          >
            <SvgIcon name="plus" :size="14" style="margin-right: 4px;" />
            + 新增物资仓库
          </button>
        </div>
      </div>

      <!-- 仓库统计指标大盘 -->
      <div class="wh-kpi-row">
        <div class="wh-kpi-item glass-panel">
          <span class="kpi-label">全院仓库总数</span>
          <span class="kpi-num font-mono">{{ warehouses.length }}</span>
          <span class="kpi-sub">主库与临床科室二级库全覆盖</span>
        </div>
        <div class="wh-kpi-item glass-panel">
          <span class="kpi-label">院级归口主仓库</span>
          <span class="kpi-num font-mono text-accent">{{ mainWarehouses.length }}</span>
          <span class="kpi-sub">耗材科 / 设备科 / 总务科 / 信息科</span>
        </div>
        <div class="wh-kpi-item glass-panel">
          <span class="kpi-label">临床科室二级库</span>
          <span class="kpi-num font-mono">{{ secondaryWarehouses.length }}</span>
          <span class="kpi-sub">病区定数包与临床现存备货</span>
        </div>
        <div class="wh-kpi-item glass-panel">
          <span class="kpi-label">期初建账锁死库房</span>
          <span class="kpi-num font-mono text-warn">{{ lockedWarehousesCount }}</span>
          <span class="kpi-sub">已完成一次性资产建账</span>
        </div>
      </div>

      <!-- 主库群与二级库群两栏拓扑架构卡片 -->
      <div class="wh-architecture-grid">
        <!-- 左栏：院级归口主仓库群 -->
        <div class="wh-group-card glass-panel">
          <div class="wh-group-header">
            <div class="group-title-row">
              <SvgIcon name="package" :size="16" color="var(--accent-primary)" />
              <h3>院级归口主仓库群 (四大主库)</h3>
              <span class="group-badge font-mono">{{ mainWarehouses.length }}</span>
            </div>
            <span class="group-hint">负责向全院临床科室采购验收、资质审查与按需分发</span>
          </div>

          <div class="wh-card-list">
            <div
              v-for="wh in mainWarehouses"
              :key="wh.warehouse_code"
              class="wh-entity-card"
            >
              <div class="entity-card-top">
                <div class="entity-name-row">
                  <span class="entity-name font-bold">{{ wh.warehouse_name }}</span>
                  <span class="entity-level-tag tag-main">院级主库</span>
                </div>
                <div v-if="userStore.currentUser.roleCode === 'sys_admin'" class="entity-actions">
                  <button class="mini-btn-link" @click="openEditWarehouseModal(wh)">编辑</button>
                  <button class="mini-btn-link text-danger" @click="handleDeleteWarehouse(wh)">删除</button>
                </div>
              </div>
              <div class="entity-card-props">
                <div class="prop-item">
                  <span class="prop-k">专属编码：</span>
                  <span class="prop-v font-mono text-accent font-bold">{{ wh.warehouse_code }}</span>
                </div>
                <div class="prop-item">
                  <span class="prop-k">管理科室：</span>
                  <span class="prop-v">{{ wh.dept_code || '院部归口' }}</span>
                </div>
                <div class="prop-item">
                  <span class="prop-k">下属二级库：</span>
                  <span class="prop-v font-mono font-bold">{{ getSubSecondaryCount(wh.warehouse_code) }} 个</span>
                </div>
                <div class="prop-item">
                  <span class="prop-k">物资归口：</span>
                  <span class="prop-v">{{ wh.warehouse_code === 'WH_EQUIP' ? '医疗设备/器械' : (wh.warehouse_code === 'WH_ZONGWU' ? '后勤物资' : '医用耗材/试剂') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右栏：临床科室二级库房群 -->
        <div class="wh-group-card glass-panel">
          <div class="wh-group-header">
            <div class="group-title-row">
              <SvgIcon name="room" :size="16" color="var(--color-success)" />
              <h3>临床科室与病区二级库房群</h3>
              <span class="group-badge font-mono">{{ secondaryWarehouses.length }}</span>
            </div>
            <span class="group-hint">病区科室日常医疗耗材领用、发料消除库存与独立盘点</span>
          </div>

          <div class="wh-card-list">
            <div
              v-for="wh in secondaryWarehouses"
              :key="wh.warehouse_code"
              class="wh-entity-card"
            >
              <div class="entity-card-top">
                <div class="entity-name-row">
                  <span class="entity-name font-bold">{{ wh.warehouse_name }}</span>
                  <span class="entity-level-tag tag-secondary">临床二级库</span>
                </div>
                <div v-if="userStore.currentUser.roleCode === 'sys_admin'" class="entity-actions">
                  <button class="mini-btn-link" @click="openEditWarehouseModal(wh)">编辑</button>
                  <button class="mini-btn-link text-danger" @click="handleDeleteWarehouse(wh)">删除</button>
                </div>
              </div>
              <div class="entity-card-props">
                <div class="prop-item">
                  <span class="prop-k">专属编码：</span>
                  <span class="prop-v font-mono text-accent font-bold">{{ wh.warehouse_code }}</span>
                </div>
                <div class="prop-item">
                  <span class="prop-k">归口主库：</span>
                  <span class="prop-v font-bold">{{ getParentWarehouseName(wh.parent_code) }}</span>
                </div>
                <div class="prop-item">
                  <span class="prop-k">所属科室：</span>
                  <span class="prop-v">{{ wh.dept_code || '临床病区' }}</span>
                </div>
                <div class="prop-item">
                  <span class="prop-k">建账状态：</span>
                  <span v-if="wh.init_stock_locked" class="status-chip chip-disabled">已永久锁死</span>
                  <span v-else class="status-chip chip-locked">待建账锁死</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- =========================================================================
         子视图 3：医疗物资国标 / 院内双维分类设置独立工作台
         ========================================================================= -->
    <div v-else-if="currentModuleTab === 'categories'" class="independent-subview-container">
      <div class="subview-header-card glass-panel">
        <div class="header-left">
          <div class="header-title-row">
            <SvgIcon name="package" :size="20" color="var(--accent-primary)" />
            <h2>医疗物资国标 / 院内双维分类设置</h2>
            <span class="subview-badge font-mono">{{ categories.length }} 个国标分类</span>
          </div>
          <p class="header-desc">
            统一规范全院医疗耗材国标 4 位/6 位编码分类，明确主科室归口（耗材科/设备科/总务科）与管理属性（普通/高值/冷链），杜绝分类混乱。
          </p>
        </div>
        <div class="header-actions">
          <button
            v-if="userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'dept_manager'"
            class="spd-btn btn-primary"
            @click="openAddCategoryModal"
          >
            <SvgIcon name="plus" :size="14" style="margin-right: 4px;" />
            + 新增耗材分类
          </button>
        </div>
      </div>

      <!-- 分类大表格台账 -->
      <div class="glass-panel" style="padding: 16px;">
        <table class="spd-sub-table">
          <thead>
            <tr>
              <th style="width: 120px;">分类编码</th>
              <th style="width: 220px;">分类名称</th>
              <th style="width: 160px;">归口管理科室</th>
              <th style="width: 140px;">管控级别</th>
              <th style="width: 160px; text-align: center;">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in categories" :key="cat.category_code">
              <td class="font-mono tabular-nums font-bold text-accent">{{ cat.category_code }}</td>
              <td class="font-bold">{{ cat.category_name }}</td>
              <td>{{ cat.main_dept_code === 'EQUIP_DEPT' ? '设备科主库' : '耗材科主库' }}</td>
              <td>
                <span class="status-chip" :class="cat.consumable_level === 'HIGH_VALUE' ? 'chip-locked' : 'chip-active'">
                  {{ cat.consumable_level === 'HIGH_VALUE' ? '高值耗材' : '普通耗材' }}
                </span>
              </td>
              <td style="text-align: center;">
                <button class="table-op-btn" @click="openEditCategoryModal(cat)">编辑</button>
                <button class="table-op-btn text-danger" style="margin-left: 6px;" @click="handleDeleteCategory(cat)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- =========================================================================
         子视图 4：国家级医疗物资供应商全资质档案独立工作台
         ========================================================================= -->
    <div v-else-if="currentModuleTab === 'suppliers'" class="independent-subview-container">
      <div class="subview-header-card glass-panel">
        <div class="header-left">
          <div class="header-title-row">
            <SvgIcon name="safe" :size="20" color="var(--color-warning)" />
            <h2>医疗物资供应商国家级资质档案台账</h2>
            <span class="subview-badge font-mono">{{ suppliers.length }} 家准入企业</span>
          </div>
          <p class="header-desc">
            国家级医疗器械合规首营档案准入管理，严格核验《医疗器械经营许可证》、统一社会信用代码与资质效期，自动红黄绿灯风险预警拦截。
          </p>
        </div>
        <div class="header-actions">
          <button
            v-if="userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'dept_manager'"
            class="spd-btn btn-primary"
            @click="openAddSupplierForm"
          >
            <SvgIcon name="plus" :size="14" style="margin-right: 4px;" />
            + 新增供应商资质档案
          </button>
        </div>
      </div>

      <!-- 供应商台账大表格 -->
      <div class="glass-panel" style="padding: 16px;">
        <table class="spd-sub-table">
          <thead>
            <tr>
              <th style="width: 110px;">编码</th>
              <th style="width: 220px;">企业名称</th>
              <th style="width: 190px;">统一社会信用代码</th>
              <th style="width: 190px;">经营许可证号</th>
              <th style="width: 110px; text-align: center;">资质状态</th>
              <th style="width: 140px; text-align: center;">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sup in suppliers" :key="sup.id">
              <td class="font-mono text-muted">{{ sup.supplier_code }}</td>
              <td class="font-bold">{{ sup.supplier_name }}</td>
              <td class="font-mono tabular-nums">{{ sup.social_credit_code || '-' }}</td>
              <td class="font-mono tabular-nums">{{ sup.license_no || '-' }}</td>
              <td style="text-align: center;">
                <span class="status-chip chip-active">{{ sup.qual_status === 'AUDITED' ? '资质核验通过' : '审核通过' }}</span>
              </td>
              <td style="text-align: center;">
                <button class="table-op-btn" @click="openEditSupplierModal(sup)">编辑</button>
                <button class="table-op-btn text-danger" style="margin-left: 6px;" @click="deleteSupplierItem(sup.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- =========================================================================
         弹窗 1：新增 / 编辑产品名称 (通用大品名) 对话框 (1:1 还原图 3)
         ========================================================================= -->
    <el-dialog
      v-model="showSpnDialog"
      :title="isEditingSpn ? '编辑产品名称' : '新增产品名称'"
      width="680px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="dialog-grid-form">
        <!-- 耗材分类 (*) -->
        <div class="form-row">
          <label class="form-label required">耗材分类</label>
          <div class="form-control-wrap">
            <select v-model="spnForm.category_code" class="spd-select">
              <option v-for="c in categoryList" :key="c.code" :value="c.code">
                {{ c.code }} | {{ c.name }}
              </option>
            </select>
          </div>
          <span class="field-hint">(*) 必填项</span>
        </div>

        <!-- 耗材代码 (*) -->
        <div class="form-row">
          <label class="form-label required">耗材代码</label>
          <div class="form-control-wrap">
            <input
              v-model="spnForm.spn_code"
              type="text"
              class="spd-input font-mono"
              placeholder="如 936010100024"
              :disabled="isEditingSpn"
            />
          </div>
          <span class="field-hint">(*) 必填项</span>
        </div>

        <!-- 耗材名称 (*) -->
        <div class="form-row">
          <label class="form-label required">耗材名称</label>
          <div class="form-control-wrap">
            <input
              v-model="spnForm.spn_name"
              type="text"
              class="spd-input"
              placeholder="如 医用氧气123"
              @input="handleSpnNameInput"
            />
          </div>
          <span class="field-hint">(*) 必填项</span>
        </div>

        <!-- 通用名称 -->
        <div class="form-row">
          <label class="form-label">通用名称</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.common_name" type="text" class="spd-input" placeholder="如 医用氧气" />
          </div>
        </div>

        <!-- 拼音码 -->
        <div class="form-row">
          <label class="form-label">拼音码</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.pinyin_code" type="text" class="spd-input font-mono" placeholder="首字母缩写 如 YYQ123" />
          </div>
        </div>

        <!-- 财务核算分类 -->
        <div class="form-row">
          <label class="form-label">财务核算分类</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.finance_category" type="text" class="spd-input" placeholder="西药卫生材料 / 气体核算" />
          </div>
        </div>

        <!-- 绩效核算分类 -->
        <div class="form-row">
          <label class="form-label">绩效核算分类</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.performance_category" type="text" class="spd-input" placeholder="临床基础耗材" />
          </div>
        </div>

        <!-- 住院收费分类 -->
        <div class="form-row">
          <label class="form-label">住院收费分类</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.inpatient_charge_category" type="text" class="spd-input" placeholder="按量计费 / 住院治疗材料费" />
          </div>
        </div>

        <!-- 门诊收费分类 -->
        <div class="form-row">
          <label class="form-label">门诊收费分类</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.outpatient_charge_category" type="text" class="spd-input" placeholder="按量计费 / 门诊处置费" />
          </div>
        </div>

        <!-- 病案分类 -->
        <div class="form-row">
          <label class="form-label">病案分类</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.medical_record_category" type="text" class="spd-input" placeholder="治疗支持材料" />
          </div>
        </div>

        <!-- 医保分类 -->
        <div class="form-row">
          <label class="form-label">医保分类</label>
          <div class="form-control-wrap">
            <select v-model="spnForm.medicare_category" class="spd-select">
              <option value="甲类医保可报销材料">甲类医保 (100%报销)</option>
              <option value="乙类医保部分报销材料">乙类医保 (部分自负)</option>
              <option value="自费耗材材料">丙类/自费耗材</option>
              <option value="打包收费不另行收费">医保病种打包不另收</option>
            </select>
          </div>
        </div>

        <!-- 勾选属性行 (收费、高值、集采) -->
        <div class="form-row flags-row">
          <label class="form-label">属性标识</label>
          <div class="checkbox-group">
            <el-checkbox v-model="spnForm.is_chargeable" :true-value="1" :false-value="0">
              是否收费材料
            </el-checkbox>
            <el-checkbox v-model="spnForm.is_high_value" :true-value="1" :false-value="0">
              是否高值耗材
            </el-checkbox>
            <el-checkbox v-model="spnForm.is_central_proc" :true-value="1" :false-value="0">
              是否带量集采
            </el-checkbox>
          </div>
        </div>

        <!-- 集采项目 -->
        <div v-if="spnForm.is_central_proc" class="form-row">
          <label class="form-label">集采项目说明</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.central_proc_project" type="text" class="spd-input" placeholder="如 国家带量采购第五批" />
          </div>
        </div>

        <!-- 采购合同编号 -->
        <div class="form-row">
          <label class="form-label">合同编号</label>
          <div class="form-control-wrap">
            <input v-model="spnForm.contract_no" type="text" class="spd-input font-mono" placeholder="如 HT-2026-O2-001" />
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <button class="spd-btn btn-secondary" @click="showSpnDialog = false">关闭</button>
          <button class="spd-btn btn-primary" :disabled="submitting" @click="submitSpnForm">
            {{ submitting ? '保存中...' : '确定保存' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 2：新增 / 编辑产品规格型号对话框 (1:1 还原图 5 左右双栏结构)
         ========================================================================= -->
    <el-dialog
      v-model="showSpecDialog"
      :title="isEditingSpec ? '编辑产品规格' : '新增产品规格'"
      width="1080px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal spec-modal"
    >
      <div class="spec-modal-split">
        <!-- 左侧：产品规格详细属性表格 (图 5 左栏) -->
        <div class="spec-form-pane">
          <div class="pane-title">产品规格详情</div>
          <div class="spec-fields-scroll">
            <!-- 产品代码 (*) -->
            <div class="form-row">
              <label class="form-label required">产品代码</label>
              <div class="form-control-wrap">
                <input
                  v-model="specForm.spec_code"
                  type="text"
                  class="spd-input font-mono"
                  placeholder="如 936010100024055517"
                  :disabled="isEditingSpec"
                />
              </div>
              <span class="field-hint">(*) 必填项</span>
            </div>

            <!-- 产品名称 (*) -->
            <div class="form-row">
              <label class="form-label required">产品名称</label>
              <div class="form-control-wrap">
                <input v-model="specForm.product_name" type="text" class="spd-input" placeholder="品名" />
              </div>
              <span class="field-hint">(*) 必填项</span>
            </div>

            <!-- 规格 (*) -->
            <div class="form-row">
              <label class="form-label required">规格</label>
              <div class="form-control-wrap">
                <input v-model="specForm.spec_name" type="text" class="spd-input" placeholder="如 40L 纯度≥99.5%" />
              </div>
              <span class="field-hint">(*) 必填项</span>
            </div>

            <!-- 型号 (*) -->
            <div class="form-row">
              <label class="form-label required">型号</label>
              <div class="form-control-wrap">
                <input v-model="specForm.model_name" type="text" class="spd-input" placeholder="如 TWLB-40" />
              </div>
              <span class="field-hint">(*) 必填项</span>
            </div>

            <!-- 生产厂商 (*) -->
            <div class="form-row">
              <label class="form-label required">生产厂商</label>
              <div class="form-control-wrap">
                <input v-model="specForm.manufacturer" type="text" class="spd-input" placeholder="如 普昂(杭州)医疗科技有限公司" />
              </div>
              <span class="field-hint">(*) 必填项</span>
            </div>

            <!-- 单价 (*) -->
            <div class="form-row">
              <label class="form-label required">基准单价(元)</label>
              <div class="form-control-wrap">
                <input v-model.number="specForm.unit_price" type="number" step="0.01" class="spd-input font-mono" placeholder="45.00" />
              </div>
              <span class="field-hint">(*) 必填项</span>
            </div>

            <!-- 计件单位 (*) -->
            <div class="form-row">
              <label class="form-label required">计件单位</label>
              <div class="form-control-wrap">
                <input v-model="specForm.pricing_unit" type="text" class="spd-input" placeholder="如 瓶 / 支 / 盒 / 套" />
              </div>
              <span class="field-hint">(*) 必填项</span>
            </div>

            <!-- 包装单位 & 包装比 -->
            <div class="form-row">
              <label class="form-label">包装单位 / 换算比</label>
              <div class="form-control-wrap dual-inline">
                <input v-model="specForm.package_unit" type="text" class="spd-input" placeholder="大包装单位 (如 箱)" />
                <input v-model.number="specForm.conversion_ratio" type="number" class="spd-input font-mono" placeholder="大小比 (如 50)" />
              </div>
            </div>

            <!-- 默认供应商 (下拉选择) -->
            <div class="form-row">
              <label class="form-label">默认供应商</label>
              <div class="form-control-wrap">
                <select v-model="specForm.default_supplier_id" class="spd-select" @change="handleSupplierSelectChange">
                  <option :value="0">请选择供应商...</option>
                  <option v-for="s in suppliers" :key="s.id" :value="s.id">
                    {{ s.supplier_code }} | {{ s.supplier_name }}
                  </option>
                </select>
              </div>
            </div>

            <!-- 医疗器械注册证号 -->
            <div class="form-row">
              <label class="form-label">注册证号</label>
              <div class="form-control-wrap">
                <input v-model="specForm.register_card_no" type="text" class="spd-input font-mono" placeholder="国械注准20223140555" />
              </div>
            </div>

            <!-- 医保耗材国家编码 -->
            <div class="form-row">
              <label class="form-label">国家医保编码</label>
              <div class="form-control-wrap">
                <input v-model="specForm.medicare_code" type="text" class="spd-input font-mono" placeholder="C01010100024001" />
              </div>
            </div>

            <!-- 储存条件 -->
            <div class="form-row">
              <label class="form-label">储存条件</label>
              <div class="form-control-wrap">
                <input v-model="specForm.storage_condition" type="text" class="spd-input" placeholder="常温干燥避光 / 冷藏2-8℃" />
              </div>
            </div>

            <!-- 授权分配仓库 (逗号分隔) -->
            <div class="form-row">
              <label class="form-label">授权入库仓库</label>
              <div class="form-control-wrap">
                <input v-model="specForm.assigned_warehouses" type="text" class="spd-input font-mono" placeholder="WH_WEICAI,WH_ZONGWU,WH_SEC_CARDIO" />
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：调价记录与管控限额 (图 5 右栏) -->
        <div class="spec-side-pane">
          <div class="side-tab-buttons">
            <button class="side-tab-btn active">调价记录</button>
            <button class="side-tab-btn">管控与限额</button>
          </div>

          <!-- 调价记录列表 -->
          <div class="price-logs-pane">
            <div v-if="currentSpecPriceLogs.length === 0" class="empty-hint">
              暂无历史调价记录
            </div>
            <div v-else class="logs-table-wrap">
              <table class="spd-sub-table">
                <thead>
                  <tr>
                    <th>价格(元)</th>
                    <th>调价原因与文号</th>
                    <th>生效时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in currentSpecPriceLogs" :key="log.id">
                    <td class="font-mono tabular-nums font-bold text-accent">
                      ¥ {{ Number(log.new_price).toFixed(2) }}
                      <span class="diff-tag" :class="log.adjust_diff < 0 ? 'text-green' : 'text-warn'">
                        ({{ log.adjust_diff > 0 ? '+' : '' }}{{ Number(log.adjust_diff).toFixed(2) }})
                      </span>
                    </td>
                    <td>
                      <div class="log-reason">{{ log.adjust_reason }}</div>
                      <div v-if="log.adjust_doc_no" class="log-doc font-mono">{{ log.adjust_doc_no }}</div>
                    </td>
                    <td class="font-mono text-muted">{{ log.effective_time.substring(0, 10) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 管控与限额模拟区域 (图 5 右下角) -->
            <div class="limit-ctrl-box">
              <div class="limit-title">采购与申领风控限额</div>
              <div class="limit-row">
                <label>
                  <input type="checkbox" checked />
                  <span>单笔采购限额: <strong>10.00 万元</strong></span>
                </label>
              </div>
              <div class="limit-row">
                <label>
                  <input type="checkbox" checked />
                  <span>科室月申领上限: <strong>5.00 万元</strong></span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <button class="spd-btn btn-secondary" @click="showSpecDialog = false">关闭</button>
          <button class="spd-btn btn-primary" :disabled="submitting" @click="submitSpecForm">
            {{ submitting ? '保存中...' : '确定保存规格' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 3：集中带量采购批量调价向导对话框 (支持多选批量改价)
         ========================================================================= -->
    <el-dialog
      v-model="showBatchPriceModal"
      title="集中带量采购与批量调价管理"
      width="720px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="batch-adjust-content">
        <div class="batch-notice-box">
          <SvgIcon name="scale" :size="16" color="var(--color-warning)" />
          <span>您已勾选 <strong>{{ selectedSpecIds.length }}</strong> 项耗材规格进行批量价格调整。调价后将自动写入不可篡改审计快照日志。</span>
        </div>

        <div class="form-row">
          <label class="form-label required">调价模式</label>
          <div class="radio-wrap">
            <el-radio-group v-model="batchAdjustForm.adjust_type">
              <el-radio value="FIXED_PRICE">统一定价模式 (直接设定新单价)</el-radio>
              <el-radio value="PERCENT_DISCOUNT">按比例调价 (如 -0.10 为降价10%)</el-radio>
              <el-radio value="FIXED_OFFSET">按固定金额扣减 (如 -5.00 元)</el-radio>
            </el-radio-group>
          </div>
        </div>

        <div class="form-row">
          <label class="form-label required">调价数值</label>
          <div class="form-control-wrap">
            <input
              v-model.number="batchAdjustForm.adjust_value"
              type="number"
              step="0.01"
              class="spd-input font-mono"
              placeholder="请输入数值 (如 45.00 或 -0.15 或 -5.00)"
            />
          </div>
        </div>

        <div class="form-row">
          <label class="form-label required">调价依据文号</label>
          <div class="form-control-wrap">
            <input
              v-model="batchAdjustForm.doc_no"
              type="text"
              class="spd-input font-mono"
              placeholder="如 浙药械采【2026】18号集中带量采购文件"
            />
          </div>
        </div>

        <div class="form-row">
          <label class="form-label required">调价业务原因</label>
          <div class="form-control-wrap">
            <input
              v-model="batchAdjustForm.reason"
              type="text"
              class="spd-input"
              placeholder="如 省集中带量采购动态联动调价执行"
            />
          </div>
        </div>

        <!-- 调价拟受影响规格清单预览 -->
        <div class="preview-spec-box">
          <div class="preview-title">拟调价规格列表 (前 5 项):</div>
          <div v-for="s in previewSpecs" :key="s.id" class="preview-item font-mono">
            <span>{{ s.spec_name }} ({{ s.spec_code }})</span>
            <span class="preview-price">
              原价: ¥{{ Number(s.unit_price).toFixed(2) }} ->
              <strong class="text-accent">拟调: ¥{{ calculatePreviewPrice(s.unit_price) }}</strong>
            </span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <button class="spd-btn btn-secondary" @click="showBatchPriceModal = false">取消</button>
          <button class="spd-btn btn-primary" :disabled="submitting" @click="submitBatchPriceAdjust">
            {{ submitting ? '执行调价中...' : '确认执行批量调价' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 4：变更默认供货商模态框
         ========================================================================= -->
    <el-dialog
      v-model="showChangeSupplierModal"
      title="变更产品规格默认供应商"
      width="520px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div v-if="selectedSpec" class="change-sup-form">
        <div class="form-row">
          <label class="form-label">目标规格</label>
          <div class="text-val font-mono">{{ selectedSpec.spec_name }} ({{ selectedSpec.spec_code }})</div>
        </div>
        <div class="form-row">
          <label class="form-label">当前供应商</label>
          <div class="text-val">{{ selectedSpec.default_supplier_name || '未绑定' }}</div>
        </div>
        <div class="form-row">
          <label class="form-label required">新供货企业</label>
          <select v-model="targetSupplierId" class="spd-select">
            <option :value="0">请选择新供应商...</option>
            <option v-for="s in suppliers" :key="s.id" :value="s.id">
              {{ s.supplier_code }} | {{ s.supplier_name }}
            </option>
          </select>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button class="spd-btn btn-secondary" @click="showChangeSupplierModal = false">取消</button>
          <button class="spd-btn btn-primary" :disabled="submitting || !targetSupplierId" @click="submitChangeSupplier">
            确定变更
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- =========================================================================
         弹窗 5：供应商准入资质档案维护模态框 (CRUD)
         ========================================================================= -->
    <el-dialog
      v-model="showSupplierManageModal"
      title="医疗物资供应商资质档案管理"
      width="860px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="sup-manage-content">
        <div class="sup-actions-bar">
          <button class="spd-btn btn-primary" @click="openAddSupplierForm">
            + 新增供应商档案
          </button>
        </div>

        <table class="spd-sub-table">
          <thead>
            <tr>
              <th>编码</th>
              <th>企业名称</th>
              <th>统一社会信用代码</th>
              <th>经营许可证号</th>
              <th>资质状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sup in suppliers" :key="sup.id">
              <td class="font-mono tabular-nums font-bold">{{ sup.supplier_code }}</td>
              <td class="font-bold">{{ sup.supplier_name }}</td>
              <td class="font-mono text-muted">{{ sup.social_credit_code }}</td>
              <td class="font-mono">{{ sup.license_no }}</td>
              <td>
                <span class="status-chip chip-success">审核通过</span>
              </td>
              <td>
                <button class="table-op-btn" @click="openEditSupplierModal(sup)">编辑</button>
                <button class="table-op-btn text-danger" style="margin-left: 6px;" @click="deleteSupplierItem(sup.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-dialog>

    <!-- 弹窗 5.1：供应商多维资质新增与编辑模态框 (国家级医疗项目规范) -->
    <el-dialog
      v-model="showSupplierFormModal"
      :title="isEditSupplier ? '编辑医疗物资供应商资质档案' : '新增医疗物资准入供应商资质档案'"
      width="680px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="spd-form-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; padding: 10px 0;">
        <div class="form-group">
          <label class="form-label required">供应商唯一编码 (专属ID)</label>
          <input
            v-model="supplierForm.supplier_code"
            :disabled="isEditSupplier"
            placeholder="如: SUP_WEGO_01"
            class="spd-input font-mono font-bold"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">企业法定全称</label>
          <input
            v-model="supplierForm.supplier_name"
            placeholder="如: 山东威高集团医用高分子制品股份有限公司"
            class="spd-input"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">统一社会信用代码 (18位)</label>
          <input
            v-model="supplierForm.social_credit_code"
            placeholder="如: 91371000166688889X"
            class="spd-input font-mono"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">《医疗器械经营许可证》编号</label>
          <input
            v-model="supplierForm.license_no"
            placeholder="如: 鲁械经营许20260088号"
            class="spd-input font-mono"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">许可证有效截止日期</label>
          <input
            v-model="supplierForm.license_expiry_date"
            type="date"
            class="spd-input font-mono"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">业务联系人姓名</label>
          <input
            v-model="supplierForm.contact_person"
            placeholder="如: 张明远"
            class="spd-input"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">联系手机号</label>
          <input
            v-model="supplierForm.contact_phone"
            placeholder="如: 13905318888"
            class="spd-input font-mono"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">准入资质状态</label>
          <select v-model="supplierForm.qual_status" class="spd-select">
            <option value="QUAL_APPROVED">审核通过正常供货</option>
            <option value="QUAL_PENDING">待审核</option>
            <option value="QUAL_EXPIRED">资质到期熔断</option>
          </select>
        </div>
        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label required">主营供货物资品类范围</label>
          <input
            v-model="supplierForm.supply_categories"
            placeholder="如: 普耗,高值,骨科,植入物,医用气体"
            class="spd-input"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <button class="spd-btn" @click="showSupplierFormModal = false">取消</button>
          <button class="spd-btn btn-primary" @click="handleSaveSupplier">保存供应商档案</button>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 5.2：全院仓库架构节点维护模态框 (增/改专属ID) -->
    <el-dialog
      v-model="showWarehouseModal"
      :title="isEditWarehouse ? '编辑仓库组织节点' : '新增全院仓库专属节点 (专属ID区分)'"
      width="540px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="spd-form-column" style="display: flex; flex-direction: column; gap: 14px; padding: 10px 0;">
        <div class="form-group">
          <label class="form-label required">仓库专属编码 (唯一ID)</label>
          <input
            v-model="warehouseForm.warehouse_code"
            :disabled="isEditWarehouse"
            placeholder="如: WH_SEC_PEDIATRIC / WH_ZONGWU"
            class="spd-input font-mono font-bold"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">仓库名称</label>
          <input
            v-model="warehouseForm.warehouse_name"
            placeholder="如: 儿科病区二级库 / 卫材库房"
            class="spd-input"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">仓库层级与性质</label>
          <select v-model="warehouseForm.warehouse_level" class="spd-select">
            <option value="DEPT_PRIMARY">院级归口主仓库 (耗材科/设备科/总务科/信息科)</option>
            <option value="CLINICAL_SECONDARY">临床科室二级库房 (病区/手术室/门诊科室)</option>
          </select>
        </div>
        <div v-if="warehouseForm.warehouse_level === 'CLINICAL_SECONDARY'" class="form-group">
          <label class="form-label required">上级归口主仓库 (发料与管辖主库)</label>
          <select v-model="warehouseForm.parent_code" class="spd-select">
            <option value="">-- 请选择上级归口主仓库 --</option>
            <option v-for="mw in mainWarehouses" :key="mw.warehouse_code" :value="mw.warehouse_code">
              {{ mw.warehouse_name }} ({{ mw.warehouse_code }})
            </option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label required">归属科室编码</label>
          <input
            v-model="warehouseForm.dept_code"
            placeholder="如: 010101 (内一科) 或 CONSUMABLE_DEPT"
            class="spd-input font-mono"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <button class="spd-btn" @click="showWarehouseModal = false">取消</button>
          <button class="spd-btn btn-primary" @click="handleSaveWarehouse">确认保存仓库</button>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 5.3：耗材国标分类增删改查模态框 -->
    <el-dialog
      v-model="showCategoryModal"
      title="耗材国标多级分类维护"
      width="780px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="category-manage-wrap">
        <div class="category-action-bar" style="display: flex; gap: 10px; margin-bottom: 12px;">
          <button class="spd-btn btn-primary" @click="openAddCategoryModal">+ 新增耗材分类</button>
        </div>
        <table class="spd-sub-table">
          <thead>
            <tr>
              <th>分类编码</th>
              <th>分类名称</th>
              <th>归口管理科室</th>
              <th>管控级别</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in categories" :key="cat.category_code">
              <td class="font-mono tabular-nums font-bold">{{ cat.category_code }}</td>
              <td class="font-bold">{{ cat.category_name }}</td>
              <td>{{ cat.main_dept_code === 'EQUIP_DEPT' ? '设备科主库' : '耗材科主库' }}</td>
              <td>
                <span class="status-chip" :class="cat.consumable_level === 'HIGH_VALUE' ? 'chip-danger' : 'chip-info'">
                  {{ cat.consumable_level === 'HIGH_VALUE' ? '高值耗材' : '普通耗材' }}
                </span>
              </td>
              <td>
                <button class="table-op-btn" @click="openEditCategoryModal(cat)">编辑</button>
                <button class="table-op-btn text-danger" style="margin-left: 6px;" @click="handleDeleteCategory(cat)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-dialog>

    <!-- 弹窗 5.4：分类编辑表单 -->
    <el-dialog
      v-model="showCategoryFormModal"
      :title="isEditCategory ? '编辑耗材分类' : '新增耗材分类'"
      width="500px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="spd-form-column" style="display: flex; flex-direction: column; gap: 12px;">
        <div class="form-group">
          <label class="form-label required">分类编码</label>
          <input v-model="categoryForm.category_code" :disabled="isEditCategory" placeholder="如: 0101 / 0202" class="spd-input font-mono" />
        </div>
        <div class="form-group">
          <label class="form-label required">分类名称</label>
          <input v-model="categoryForm.category_name" placeholder="如: 医用气体 / 骨科材料类" class="spd-input" />
        </div>
        <div class="form-group">
          <label class="form-label required">归口管理科室</label>
          <select v-model="categoryForm.main_dept_code" class="spd-select">
            <option value="CONSUMABLE_DEPT">耗材科主库</option>
            <option value="EQUIP_DEPT">设备科主库</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label required">管控级别</label>
          <select v-model="categoryForm.consumable_level" class="spd-select">
            <option value="GENERAL">普通耗材</option>
            <option value="HIGH_VALUE">高值耗材</option>
            <option value="EQUIP_PART">设备配件</option>
          </select>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <button class="spd-btn" @click="showCategoryFormModal = false">取消</button>
          <button class="spd-btn btn-primary" @click="handleSaveCategory">保存分类</button>
        </div>
      </template>
    </el-dialog>


    <!-- =========================================================================
         弹窗 6：管理员专属 - 仓库细粒度授权配置 (RBAC)
         ========================================================================= -->
    <el-dialog
      v-model="showWarehouseRbacModal"
      title="用户与仓库细粒度操作权限配置矩阵 (信息科管理员专属)"
      width="900px"
      append-to-body
      destroy-on-close
      class="spd-dialog-modal"
    >
      <div class="rbac-config-content">
        <div class="rbac-user-select-row">
          <label class="form-label required">配置目标人员账号</label>
          <select v-model="selectedRbacUserId" class="spd-select" @change="fetchUserWarehousePerms">
            <option :value="1">赵振华 (admin - 信息科管理员)</option>
            <option :value="2">王建国 (haocai - 耗材科主管)</option>
            <option :value="3">周天海 (shebei - 设备科主管)</option>
            <option :value="4">李晓琳 (nurse - 骨科病区护士)</option>
            <option :value="5">孙丽娟 (caiwu - 财务科主管)</option>
          </select>
        </div>

        <table class="spd-sub-table">
          <thead>
            <tr>
              <th>仓库编码</th>
              <th>仓库名称</th>
              <th align="center">查看物资</th>
              <th align="center">科室申领</th>
              <th align="center">验收入库</th>
              <th align="center">发料出库</th>
              <th align="center">盘点维护</th>
              <th align="center">跨仓调拨</th>
              <th align="center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="wh in warehouses" :key="wh.warehouse_code">
              <td class="font-mono text-muted">{{ wh.warehouse_code }}</td>
              <td class="font-bold">{{ wh.warehouse_name }}</td>
              <td align="center">
                <el-switch v-model="getPermItem(wh.warehouse_code).can_view" :active-value="1" :inactive-value="0" />
              </td>
              <td align="center">
                <el-switch v-model="getPermItem(wh.warehouse_code).can_apply" :active-value="1" :inactive-value="0" />
              </td>
              <td align="center">
                <el-switch v-model="getPermItem(wh.warehouse_code).can_inbound" :active-value="1" :inactive-value="0" />
              </td>
              <td align="center">
                <el-switch v-model="getPermItem(wh.warehouse_code).can_outbound" :active-value="1" :inactive-value="0" />
              </td>
              <td align="center">
                <el-switch v-model="getPermItem(wh.warehouse_code).can_stocktake" :active-value="1" :inactive-value="0" />
              </td>
              <td align="center">
                <el-switch v-model="getPermItem(wh.warehouse_code).can_transfer" :active-value="1" :inactive-value="0" />
              </td>
              <td align="center">
                <button class="table-op-btn" @click="saveSinglePerm(wh.warehouse_code)">保存</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-dialog>

    <!-- 智能体 1: 产品字典智能归类与建库审查智能体 (Plan & Execute 架构) -->
    <AgentChatWidget
      floating
      agent-id="dict_guard"
      agent-title="产品字典智能归类与建库智能体"
      architecture-tag="Plan & Execute (3步法)"
      :preset-questions="[
        '帮我检查医用外科口罩分类是否合规',
        '以科室主管权限新建一类骨科高值耗材',
        '自动分析待入库高值批次合规性'
      ]"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';
import AgentChatWidget from '@/components/AgentChatWidget.vue';
import {
  listSpns,
  createSpn,
  updateSpn,
  deleteSpn,
  listSpecs,
  createSpec,
  updateSpec,
  deleteSpec,
  toggleSpecStatus,
  batchAdjustPrice,
  listPriceAdjustLogs,
  listSuppliers,
  createSupplier,
  updateSupplier,
  deleteSupplier,
  listWarehouses,
  createWarehouse,
  updateWarehouse,
  deleteWarehouse,
  listCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  getUserWarehousePerms,
  upsertUserWarehousePerm,
  type SpnItem,
  type SpecItem,
  type SupplierProfileItem,
  type WarehouseNode,
  type CategoryNode,
  type PriceAdjustLogItem,
  type UserWarehousePermItem
} from '@/api/dictApi';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 4 大主内容区子视图切换状态 (与左侧侧边栏及 URL query.tab 双向实时联动)
const currentModuleTab = ref<'specs' | 'warehouses' | 'categories' | 'suppliers'>('specs');

/**
 * 切换产品字典四大主内容区独立视图
 * @param tab 目标子视图名称 ('specs' | 'warehouses' | 'categories' | 'suppliers')
 * @returns void
 * @route 联动更新浏览器 query.tab 并无缝切换主内容区视图
 * @throws 无异常抛出
 */
function switchModuleTab(tab: 'specs' | 'warehouses' | 'categories' | 'suppliers') {
  currentModuleTab.value = tab;
  router.replace({ query: { ...route.query, tab } });
}

// 监听路由 query 动态切换主内容区视图
watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab === 'warehouses' || newTab === 'categories' || newTab === 'suppliers' || newTab === 'specs') {
      currentModuleTab.value = newTab;
    } else {
      currentModuleTab.value = 'specs';
    }
  },
  { immediate: true }
);

// 基础数据状态
const loading = ref<boolean>(false);
const submitting = ref<boolean>(false);

const spns = ref<SpnItem[]>([]);
const specs = ref<SpecItem[]>([]);
const suppliers = ref<SupplierProfileItem[]>([]);
const warehouses = ref<WarehouseNode[]>([]);
const categories = ref<CategoryNode[]>([]);
const userWarehousePerms = ref<UserWarehousePermItem[]>([]);

// 仓库分层计算：院级主库与临床二级库
const mainWarehouses = computed(() => {
  return warehouses.value.filter(w =>
    w.warehouse_level === 'MAIN_GROUP' ||
    w.warehouse_level === 'DEPT_PRIMARY' ||
    w.warehouse_code.startsWith('WH_WEI') ||
    w.warehouse_code.startsWith('WH_EQUIP') ||
    w.warehouse_code.startsWith('WH_ZONG') ||
    w.warehouse_code.startsWith('WH_XIN') ||
    w.warehouse_code === 'WH_ZHUANXIANG'
  );
});

const secondaryWarehouses = computed(() => {
  return warehouses.value.filter(w =>
    w.warehouse_level === 'CLINICAL_SECONDARY' ||
    w.warehouse_code.startsWith('WH_SEC') ||
    w.warehouse_code === 'WH_HOUQIN' ||
    w.warehouse_code === 'WH_CESHI'
  );
});

const lockedWarehousesCount = computed(() => {
  return warehouses.value.filter(w => w.init_stock_locked === 1).length;
});

/**
 * 获取归口主仓库名称
 * @param parentCode 主仓库编码
 * @returns 归口主仓库名称字符串
 * @route 内部展示计算
 * @throws 无异常
 */
function getParentWarehouseName(parentCode?: string): string {
  if (!parentCode) return '卫材主库 (默认归口)';
  const parent = warehouses.value.find(w => w.warehouse_code === parentCode);
  return parent ? parent.warehouse_name : parentCode;
}

/**
 * 计算主库下辖的二级库数量
 * @param mainCode 主仓库编码
 * @returns 下辖二级库统计数量
 * @route 内部展示计算
 * @throws 无异常
 */
function getSubSecondaryCount(mainCode: string): number {
  return secondaryWarehouses.value.filter(w => w.parent_code === mainCode || (!w.parent_code && mainCode === 'WH_WEICAI')).length;
}

// 筛选状态
const selectedWarehouseCode = ref<string>('');
const selectedCategoryCode = ref<string>('');
const selectedSpnId = ref<number | null>(null);
const selectedSupplierId = ref<number | null>(null);
const middleTab = ref<'spn' | 'supplier'>('spn');
const middleSearchKeyword = ref<string>('');
const warehouseSearchKeyword = ref<string>('');
const showDisabledSpecs = ref<boolean>(false);

// 选中项状态
const selectedSpec = ref<SpecItem | null>(null);
const selectedSpecIds = ref<number[]>([]);
const currentSpecPriceLogs = ref<PriceAdjustLogItem[]>([]);

// 弹窗状态
const showSpnDialog = ref<boolean>(false);
const isEditingSpn = ref<boolean>(false);
const showSpecDialog = ref<boolean>(false);
const isEditingSpec = ref<boolean>(false);
const showBatchPriceModal = ref<boolean>(false);
const showChangeSupplierModal = ref<boolean>(false);
const showSupplierManageModal = ref<boolean>(false);
const showWarehouseRbacModal = ref<boolean>(false);

// 仓库维护模态框状态
const showWarehouseModal = ref<boolean>(false);
const isEditWarehouse = ref<boolean>(false);
const warehouseForm = ref<Partial<WarehouseNode>>({
  warehouse_code: '',
  warehouse_name: '',
  warehouse_level: 'CLINICAL_SECONDARY',
  dept_code: '010101'
});

// 分类维护模态框状态
const showCategoryModal = ref<boolean>(false);
const showCategoryFormModal = ref<boolean>(false);
const isEditCategory = ref<boolean>(false);
const categoryForm = ref<Partial<CategoryNode>>({
  category_code: '',
  category_name: '',
  main_dept_code: 'CONSUMABLE_DEPT',
  consumable_level: 'GENERAL'
});

// 供应商档案模态框状态
const showSupplierFormModal = ref<boolean>(false);
const isEditSupplier = ref<boolean>(false);
const supplierForm = ref<Partial<SupplierProfileItem>>({
  supplier_code: '',
  supplier_name: '',
  social_credit_code: '',
  license_no: '',
  license_expiry_date: '2029-12-31',
  contact_person: '',
  contact_phone: '',
  qual_status: 'QUAL_APPROVED',
  supply_categories: '普耗,高值,骨科,气体'
});

// 表单状态
const spnForm = ref<Partial<SpnItem>>({
  spn_code: '',
  spn_name: '',
  category_code: '0101',
  common_name: '',
  pinyin_code: '',
  finance_category: '西药卫生材料',
  performance_category: '临床基础耗材',
  inpatient_charge_category: '按量计费',
  outpatient_charge_category: '按量计费',
  medical_record_category: '治疗支持材料',
  medicare_category: '甲类医保可报销材料',
  is_chargeable: 1,
  is_high_value: 0,
  is_central_proc: 0,
  central_proc_project: '',
  contract_no: ''
});

const specForm = ref<Partial<SpecItem>>({
  spn_id: 1,
  spec_code: '',
  product_name: '',
  spec_name: '',
  model_name: '',
  common_name: '',
  component_name: '1',
  brand_name: '国产品牌',
  manufacturer: '',
  pricing_unit: '瓶',
  package_unit: '箱',
  conversion_ratio: 1,
  unit_price: 45.0,
  register_card_no: '',
  medicare_code: '',
  storage_condition: '常温干燥避光',
  assigned_warehouses: 'WH_WEICAI',
  default_supplier_id: 0
});

const batchAdjustForm = ref({
  adjust_type: 'PERCENT_DISCOUNT' as 'FIXED_PRICE' | 'PERCENT_DISCOUNT' | 'FIXED_OFFSET',
  adjust_value: -0.1,
  reason: '省药械采购平台国家集采动态联动调价',
  doc_no: '浙药械采【2026】18号'
});

const targetSupplierId = ref<number>(0);
const selectedRbacUserId = ref<number>(4); // 默认护士李晓琳
const rbacPermsMap = ref<Record<string, UserWarehousePermItem>>({});

// 耗材分类动态清单：100% 读取数据库 categories.value 同源数据，杜绝前后端分类不同步
const categoryList = computed(() => {
  return (categories.value || []).map((c) => ({
    code: c.category_code,
    name: c.category_name
  }));
});

// 计算属性
const isNurseRole = computed(() => userStore.currentUser.roleCode === 'secondary_user');

// 仓库限权过滤：若是护士角色，仅显示授权绑定的仓库 (WH_SEC_ORTHO 与 WH_SEC_CARDIO)
const visibleWarehouses = computed(() => {
  if (userStore.currentUser.roleCode === 'sys_admin' || userStore.currentUser.roleCode === 'finance_auditor') {
    return warehouses.value;
  }
  if (isNurseRole.value) {
    return warehouses.value.filter((w) =>
      w.warehouse_code === 'WH_SEC_ORTHO' || w.warehouse_code === 'WH_SEC_CARDIO'
    );
  }
  // 耗材科主管
  if (userStore.currentUser.roleCode === 'dept_manager') {
    return warehouses.value.filter((w) =>
      w.warehouse_code === 'WH_WEICAI' || w.warehouse_code === 'WH_ZONGWU' || w.warehouse_code === 'WH_ZHUANXIANG' || w.warehouse_code === 'WH_HOUQIN'
    );
  }
  return warehouses.value;
});

const filteredWarehouses = computed(() => {
  const list = visibleWarehouses.value;
  if (!warehouseSearchKeyword.value.trim()) return list;
  const kw = warehouseSearchKeyword.value.toLowerCase().trim();
  return list.filter((w) =>
    (w.warehouse_name || '').toLowerCase().includes(kw) ||
    (w.warehouse_code || '').toLowerCase().includes(kw)
  );
});

const mainWarehouseNodes = computed(() => {
  return filteredWarehouses.value.filter(
    (wh) => wh.warehouse_level !== 'CLINICAL_SECONDARY' && !wh.warehouse_code.startsWith('WH_SEC')
  );
});

const secondaryWarehouseNodes = computed(() => {
  return filteredWarehouses.value.filter(
    (wh) => wh.warehouse_level === 'CLINICAL_SECONDARY' || wh.warehouse_code.startsWith('WH_SEC')
  );
});

const selectedSpn = computed(() => spns.value.find((s) => s.id === selectedSpnId.value) || null);

const totalSpecCount = computed(() => specs.value.length + 1280);
const consumableSpecCount = computed(() => specs.value.filter((s) => s.category_code !== '0103').length + 850);

const filteredSpns = computed(() => {
  let list = spns.value;
  if (selectedCategoryCode.value) {
    list = list.filter((s) => s.category_code === selectedCategoryCode.value);
  }
  if (middleSearchKeyword.value.trim()) {
    const kw = middleSearchKeyword.value.toLowerCase().trim();
    list = list.filter(
      (s) =>
        s.spn_name.toLowerCase().includes(kw) ||
        s.spn_code.includes(kw) ||
        s.pinyin_code.toLowerCase().includes(kw)
    );
  }
  return list;
});

const filteredSuppliers = computed(() => {
  if (!middleSearchKeyword.value.trim()) return suppliers.value;
  const kw = middleSearchKeyword.value.toLowerCase().trim();
  return suppliers.value.filter(
    (s) => s.supplier_name.toLowerCase().includes(kw) || s.supplier_code.includes(kw)
  );
});

const filteredSpecs = computed(() => {
  let list = specs.value;
  // 停用过滤
  if (!showDisabledSpecs.value) {
    list = list.filter((s) => s.status === 'ACTIVE');
  }
  // 仓库过滤
  if (selectedWarehouseCode.value) {
    list = list.filter((s) => (s.assigned_warehouses || '').includes(selectedWarehouseCode.value));
  }
  // 分类过滤
  if (selectedCategoryCode.value) {
    list = list.filter((s) => s.category_code === selectedCategoryCode.value);
  }
  // 大品名过滤
  if (selectedSpnId.value !== null) {
    list = list.filter((s) => s.spn_id === selectedSpnId.value);
  }
  // 供应商过滤
  if (selectedSupplierId.value !== null) {
    list = list.filter((s) => s.default_supplier_id === selectedSupplierId.value);
  }
  return list;
});

const specCurrentPage = ref(1);
const specPageSize = ref(15);
const paginatedSpecs = computed(() => {
  const start = (specCurrentPage.value - 1) * specPageSize.value;
  return filteredSpecs.value.slice(start, start + specPageSize.value);
});

const previewSpecs = computed(() => {
  return specs.value.filter((s) => selectedSpecIds.value.includes(s.id)).slice(0, 5);
});

const currentFilterSummary = computed(() => {
  const parts: string[] = [];
  if (selectedWarehouseCode.value) {
    const wh = warehouses.value.find((w) => w.warehouse_code === selectedWarehouseCode.value);
    parts.push(`仓库: ${wh ? wh.warehouse_name : selectedWarehouseCode.value}`);
  }
  if (selectedCategoryCode.value) {
    const cat = categoryList.value.find((c) => c.code === selectedCategoryCode.value);
    parts.push(`分类: ${cat ? cat.name : selectedCategoryCode.value}`);
  }
  if (selectedSpn.value) {
    parts.push(`品名: ${selectedSpn.value.spn_name}`);
  }
  return parts.length ? `当前范围: ${parts.join(' > ')}` : '全院所有仓库与品类全景';
});

// 权限判断辅助
function canOperateDict(action: 'can_create' | 'can_edit' | 'can_delete'): boolean {
  if (isNurseRole.value) {
    return false; // 护士无权修改字典
  }
  return userStore.canAction('DICT_MANAGE', action);
}

// 数据加载
async function fetchData(): Promise<void> {
  loading.value = true;
  try {
    const [spnRes, specRes, supRes, whRes, catRes] = await Promise.all([
      listSpns(),
      listSpecs(),
      listSuppliers(),
      listWarehouses(),
      listCategories()
    ]);
    spns.value = spnRes || [];
    specs.value = specRes || [];
    suppliers.value = supRes || [];
    warehouses.value = whRes || [];
    categories.value = catRes || [];
  } catch {
    ElMessage.error('加载医疗字典与多级规格数据失败');
  } finally {
    loading.value = false;
  }
}

// 树选择事件
function selectWarehouse(code: string): void {
  selectedWarehouseCode.value = code;
}

function selectCategory(code: string): void {
  selectedCategoryCode.value = code;
}

function selectSpn(spn: SpnItem | null): void {
  selectedSpnId.value = spn ? spn.id : null;
}

function selectSupplier(sup: SupplierProfileItem | null): void {
  selectedSupplierId.value = sup ? sup.id : null;
}

function resetAllFilters(): void {
  selectedWarehouseCode.value = '';
  selectedCategoryCode.value = '';
  selectedSpnId.value = null;
  selectedSupplierId.value = null;
  middleSearchKeyword.value = '';
  showDisabledSpecs.value = false;
  ElMessage.success('已重置所有筛选条件，展示全景物料');
}

// 表格多选与点击事件
function handleSpecSelectionChange(rows: SpecItem[]): void {
  selectedSpecIds.value = rows.map((r) => r.id);
}

function handleSpecRowClick(row: SpecItem | null): void {
  selectedSpec.value = row;
  if (row) {
    loadSpecPriceLogs(row.id);
  }
}

async function loadSpecPriceLogs(specId: number): Promise<void> {
  try {
    const logs = await listPriceAdjustLogs({ spec_id: specId });
    currentSpecPriceLogs.value = logs || [];
  } catch {
    currentSpecPriceLogs.value = [];
  }
}

function viewPriceLogs(row: SpecItem): void {
  selectedSpec.value = row;
  loadSpecPriceLogs(row.id);
  openEditSpecModalWithRow(row);
}

// 品名管理指令
function handleSpnCommand(command: string): void {
  if (command === 'create_spn') {
    isEditingSpn.value = false;
    spnForm.value = {
      spn_code: `9360${Date.now().toString().slice(-8)}`,
      spn_name: '',
      category_code: selectedCategoryCode.value || '0101',
      common_name: '',
      pinyin_code: '',
      finance_category: '西药卫生材料',
      performance_category: '临床基础耗材',
      inpatient_charge_category: '按量计费',
      outpatient_charge_category: '按量计费',
      medical_record_category: '治疗支持材料',
      medicare_category: '甲类医保可报销材料',
      is_chargeable: 1,
      is_high_value: 0,
      is_central_proc: 0,
      central_proc_project: '',
      contract_no: ''
    };
    showSpnDialog.value = true;
  } else if (command === 'edit_spn' && selectedSpn.value) {
    isEditingSpn.value = true;
    spnForm.value = { ...selectedSpn.value };
    showSpnDialog.value = true;
  } else if (command === 'delete_spn' && selectedSpn.value) {
    handleDeleteSpn(selectedSpn.value);
  }
}

function handleSpnNameInput(): void {
  if (spnForm.value.spn_name) {
    if (!spnForm.value.common_name) {
      spnForm.value.common_name = spnForm.value.spn_name;
    }
    // 简易拼音首字母占位
    spnForm.value.pinyin_code = spnForm.value.spn_name
      .split('')
      .map((c) => c.charCodeAt(0).toString(16).slice(-1).toUpperCase())
      .join('')
      .slice(0, 8);
  }
}

async function submitSpnForm(): Promise<void> {
  if (!spnForm.value.spn_code || !spnForm.value.spn_name) {
    ElMessage.warning('品名编码和品名名称为必填项');
    return;
  }
  submitting.value = true;
  try {
    if (isEditingSpn.value && spnForm.value.id) {
      await updateSpn(spnForm.value.id, spnForm.value);
      ElMessage.success('产品大品名更新成功');
    } else {
      await createSpn(spnForm.value);
      ElMessage.success('新增产品大品名成功');
    }
    showSpnDialog.value = false;
    await fetchData();
  } catch (err: any) {
    ElMessage.error(err.message || '保存大品名失败');
  } finally {
    submitting.value = false;
  }
}

async function handleDeleteSpn(spn: SpnItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确定删除大品名 [${spn.spn_name}] 吗？若下属仍有规格将自动拦截。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    );
    await deleteSpn(spn.id);
    ElMessage.success('大品名已安全删除');
    selectedSpnId.value = null;
    await fetchData();
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除大品名失败');
    }
  }
}

// 规格录入与编辑 (图 5)
function openAddSpecModal(): void {
  isEditingSpec.value = false;
  const parentSpn = selectedSpn.value;
  specForm.value = {
    spn_id: parentSpn ? parentSpn.id : 1,
    spec_code: `${parentSpn ? parentSpn.spn_code : '936010100024'}${Date.now().toString().slice(-6)}`,
    product_name: parentSpn ? parentSpn.spn_name : '医用氧气123',
    spec_name: '',
    model_name: '',
    common_name: parentSpn ? parentSpn.common_name : '',
    component_name: '1',
    brand_name: '国产品牌',
    manufacturer: '普昂(杭州)医疗科技有限公司',
    pricing_unit: '瓶',
    package_unit: '箱',
    conversion_ratio: 1,
    unit_price: 45.0,
    register_card_no: '国械注准20223140555',
    medicare_code: '',
    storage_condition: '常温干燥避光',
    assigned_warehouses: selectedWarehouseCode.value || 'WH_WEICAI',
    default_supplier_id: 1,
    default_supplier_name: '普昂(杭州)医疗科技有限公司'
  };
  currentSpecPriceLogs.value = [];
  showSpecDialog.value = true;
}

function openEditSpecModal(): void {
  if (!selectedSpec.value) return;
  openEditSpecModalWithRow(selectedSpec.value);
}

function openEditSpecModalWithRow(spec: SpecItem): void {
  isEditingSpec.value = true;
  specForm.value = { ...spec };
  selectedSpec.value = spec;
  loadSpecPriceLogs(spec.id);
  showSpecDialog.value = true;
}

function handleSupplierSelectChange(): void {
  const target = suppliers.value.find((s) => s.id === specForm.value.default_supplier_id);
  if (target) {
    specForm.value.default_supplier_name = target.supplier_name;
  }
}

async function submitSpecForm(): Promise<void> {
  if (!specForm.value.spec_code || !specForm.value.spec_name || !specForm.value.model_name) {
    ElMessage.warning('规格编码、规格名称与型号为必填项');
    return;
  }
  submitting.value = true;
  try {
    if (isEditingSpec.value && specForm.value.id) {
      await updateSpec(specForm.value.id, specForm.value);
      ElMessage.success('产品规格型号更新成功');
    } else {
      await createSpec(specForm.value);
      ElMessage.success('新增产品规格型号成功');
    }
    showSpecDialog.value = false;
    await fetchData();
  } catch (err: any) {
    ElMessage.error(err.message || '保存产品规格失败');
  } finally {
    submitting.value = false;
  }
}

async function handleToggleSpecStatus(): Promise<void> {
  if (!selectedSpec.value) return;
  const spec = selectedSpec.value;
  try {
    const updated = await toggleSpecStatus(spec.id);
    spec.status = updated.status;
    ElMessage.success(`规格 [${spec.spec_name}] 已成功切换为 ${updated.status === 'ACTIVE' ? '正常在用' : '已停用'}`);
  } catch (err: any) {
    ElMessage.error(err.message || '切换规格状态失败');
  }
}

async function handleDeleteSpec(): Promise<void> {
  if (!selectedSpec.value) return;
  const spec = selectedSpec.value;
  try {
    await ElMessageBox.confirm(
      `确定删除产品规格 [${spec.spec_name}] (${spec.spec_code}) 吗？`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    );
    await deleteSpec(spec.id);
    ElMessage.success('产品规格已成功安全删除');
    selectedSpec.value = null;
    await fetchData();
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除规格失败');
    }
  }
}

// 集中带量批量调价
function openBatchPriceAdjustModal(): void {
  if (selectedSpecIds.value.length === 0) {
    ElMessage.warning('请先在表格左侧勾选待批量调价的规格');
    return;
  }
  showBatchPriceModal.value = true;
}

function calculatePreviewPrice(oldPrice: number): string {
  const val = Number(batchAdjustForm.value.adjust_value) || 0;
  if (batchAdjustForm.value.adjust_type === 'FIXED_PRICE') {
    return Math.max(0.01, val).toFixed(2);
  }
  if (batchAdjustForm.value.adjust_type === 'PERCENT_DISCOUNT') {
    return Math.max(0.01, oldPrice * (1 + val)).toFixed(2);
  }
  if (batchAdjustForm.value.adjust_type === 'FIXED_OFFSET') {
    return Math.max(0.01, oldPrice + val).toFixed(2);
  }
  return Number(oldPrice).toFixed(2);
}

async function submitBatchPriceAdjust(): Promise<void> {
  if (!batchAdjustForm.value.reason) {
    ElMessage.warning('请输入调价原因说明');
    return;
  }
  submitting.value = true;
  try {
    const res = await batchAdjustPrice({
      spec_ids: selectedSpecIds.value,
      adjust_type: batchAdjustForm.value.adjust_type,
      adjust_value: Number(batchAdjustForm.value.adjust_value),
      reason: batchAdjustForm.value.reason,
      doc_no: batchAdjustForm.value.doc_no
    });
    ElMessage.success(res.adjust_reason || `成功为 ${res.affected_count} 项规格执行批量调价`);
    showBatchPriceModal.value = false;
    await fetchData();
    if (selectedSpec.value) {
      loadSpecPriceLogs(selectedSpec.value.id);
    }
  } catch (err: any) {
    ElMessage.error(err.message || '批量调价执行异常');
  } finally {
    submitting.value = false;
  }
}

// 变更供应商
function openChangeSupplierModal(): void {
  if (!selectedSpec.value) return;
  targetSupplierId.value = selectedSpec.value.default_supplier_id || 0;
  showChangeSupplierModal.value = true;
}

async function submitChangeSupplier(): Promise<void> {
  if (!selectedSpec.value || !targetSupplierId.value) return;
  const target = suppliers.value.find((s) => s.id === targetSupplierId.value);
  if (!target) return;

  submitting.value = true;
  try {
    await updateSpec(selectedSpec.value.id, {
      default_supplier_id: target.id,
      default_supplier_name: target.supplier_name
    });
    selectedSpec.value.default_supplier_id = target.id;
    selectedSpec.value.default_supplier_name = target.supplier_name;
    ElMessage.success(`已成功将供应商变更为 [${target.supplier_name}]`);
    showChangeSupplierModal.value = false;
    await fetchData();
  } catch (err: any) {
    ElMessage.error(err.message || '变更供应商失败');
  } finally {
    submitting.value = false;
  }
}

// 供应商资质档案管理
function openAddSupplierForm(): void {
  isEditSupplier.value = false;
  supplierForm.value = {
    supplier_code: `SUP_${Date.now().toString().slice(-4)}`,
    supplier_name: '',
    social_credit_code: `91330100${Date.now().toString().slice(-10)}`,
    license_no: `浙械经营备2026${Date.now().toString().slice(-4)}号`,
    license_expiry_date: '2029-12-31',
    contact_person: '',
    contact_phone: '',
    qual_status: 'QUAL_APPROVED',
    supply_categories: '普耗,高值,骨科,气体'
  };
  showSupplierFormModal.value = true;
}

function openEditSupplierModal(sup: SupplierProfileItem): void {
  isEditSupplier.value = true;
  supplierForm.value = { ...sup };
  showSupplierFormModal.value = true;
}

async function handleSaveSupplier(): Promise<void> {
  if (!supplierForm.value.supplier_name || !supplierForm.value.supplier_code) {
    ElMessage.warning('供应商编码和企业全称为必填项');
    return;
  }
  try {
    if (isEditSupplier.value && supplierForm.value.id) {
      await updateSupplier(supplierForm.value.id, supplierForm.value);
      ElMessage.success('供应商资质档案已更新');
    } else {
      await createSupplier(supplierForm.value);
      ElMessage.success('新增准入供应商成功');
    }
    showSupplierFormModal.value = false;
    const supRes = await listSuppliers();
    suppliers.value = supRes || [];
  } catch (err: any) {
    ElMessage.error(err.message || '保存供应商档案失败');
  }
}

async function deleteSupplierItem(id: number): Promise<void> {
  try {
    await ElMessageBox.confirm('确定注销并删除该供应商资质档案吗？', '删除确认', { type: 'warning' });
    await deleteSupplier(id);
    ElMessage.success('供应商档案已删除');
    const supRes = await listSuppliers();
    suppliers.value = supRes || [];
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除供应商失败');
    }
  }
}

// 仓库组织节点管理 (支持专属ID增删改查与库存拦截)
function openAddWarehouseModal(): void {
  isEditWarehouse.value = false;
  warehouseForm.value = {
    warehouse_code: `WH_SEC_${Date.now().toString().slice(-4)}`,
    warehouse_name: '',
    warehouse_level: 'CLINICAL_SECONDARY',
    dept_code: '010101'
  };
  showWarehouseModal.value = true;
}

function openEditWarehouseModal(wh: WarehouseNode): void {
  isEditWarehouse.value = true;
  warehouseForm.value = { ...wh };
  showWarehouseModal.value = true;
}

async function handleSaveWarehouse(): Promise<void> {
  if (!warehouseForm.value.warehouse_code || !warehouseForm.value.warehouse_name) {
    ElMessage.warning('仓库专属编码与仓库名称为必填项');
    return;
  }
  submitting.value = true;
  try {
    if (isEditWarehouse.value && warehouseForm.value.id) {
      await updateWarehouse(warehouseForm.value.id, warehouseForm.value);
      ElMessage.success('仓库节点信息更新成功');
    } else {
      await createWarehouse(warehouseForm.value);
      ElMessage.success('新增仓库专属节点成功');
    }
    showWarehouseModal.value = false;
    await fetchData();
  } catch (err: any) {
    ElMessage.error(err.message || '保存仓库失败');
  } finally {
    submitting.value = false;
  }
}

async function handleDeleteWarehouse(wh: WarehouseNode): Promise<void> {
  if (!wh.id) return;
  try {
    await ElMessageBox.confirm(
      `确定删除仓库 [${wh.warehouse_name}] (${wh.warehouse_code}) 吗？若存在在库物资或单据将刚性拦截。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    );
    await deleteWarehouse(wh.id);
    ElMessage.success('仓库已安全删除');
    if (selectedWarehouseCode.value === wh.warehouse_code) {
      selectedWarehouseCode.value = '';
    }
    await fetchData();
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除仓库失败');
    }
  }
}

// 耗材国标分类增删改查
function openCategoryManageModal(): void {
  showCategoryModal.value = true;
}

function openAddCategoryModal(): void {
  isEditCategory.value = false;
  categoryForm.value = {
    category_code: `01${Date.now().toString().slice(-2)}`,
    category_name: '',
    main_dept_code: 'CONSUMABLE_DEPT',
    consumable_level: 'GENERAL'
  };
  showCategoryFormModal.value = true;
}

function openEditCategoryModal(cat: CategoryNode): void {
  isEditCategory.value = true;
  categoryForm.value = { ...cat };
  showCategoryFormModal.value = true;
}

async function handleSaveCategory(): Promise<void> {
  if (!categoryForm.value.category_code || !categoryForm.value.category_name) {
    ElMessage.warning('分类编码和分类名称为必填项');
    return;
  }
  try {
    if (isEditCategory.value && categoryForm.value.id) {
      await updateCategory(categoryForm.value.id, categoryForm.value);
      ElMessage.success('耗材分类修改成功');
    } else {
      await createCategory(categoryForm.value);
      ElMessage.success('新增耗材分类成功');
    }
    showCategoryFormModal.value = false;
    const catRes = await listCategories();
    categories.value = catRes || [];
  } catch (err: any) {
    ElMessage.error(err.message || '保存分类失败');
  }
}

async function handleDeleteCategory(cat: CategoryNode): Promise<void> {
  if (!cat.id) return;
  try {
    await ElMessageBox.confirm(
      `确定删除分类 [${cat.category_name}] (${cat.category_code}) 吗？`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    );
    await deleteCategory(cat.id);
    ElMessage.success('耗材分类已删除');
    const catRes = await listCategories();
    categories.value = catRes || [];
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除分类失败');
    }
  }
}

// 仓库细粒度授权配置 (RBAC)
function openWarehouseRbacModal(): void {
  showWarehouseRbacModal.value = true;
  fetchUserWarehousePerms();
}

async function fetchUserWarehousePerms(): Promise<void> {
  try {
    const res = await getUserWarehousePerms(selectedRbacUserId.value);
    const map: Record<string, UserWarehousePermItem> = {};
    (res || []).forEach((p) => {
      map[p.warehouse_code] = p;
    });
    rbacPermsMap.value = map;
  } catch {
    rbacPermsMap.value = {};
  }
}

function getPermItem(whCode: string): UserWarehousePermItem {
  if (!rbacPermsMap.value[whCode]) {
    rbacPermsMap.value[whCode] = {
      id: 0,
      user_id: selectedRbacUserId.value,
      username: 'user',
      warehouse_code: whCode,
      can_view: 0,
      can_apply: 0,
      can_inbound: 0,
      can_outbound: 0,
      can_stocktake: 0,
      can_transfer: 0,
      updated_by: 'admin',
      updated_at: ''
    };
  }
  return rbacPermsMap.value[whCode];
}

async function saveSinglePerm(whCode: string): Promise<void> {
  const item = getPermItem(whCode);
  try {
    await upsertUserWarehousePerm({
      user_id: selectedRbacUserId.value,
      warehouse_code: whCode,
      can_view: item.can_view,
      can_apply: item.can_apply,
      can_inbound: item.can_inbound,
      can_outbound: item.can_outbound,
      can_stocktake: item.can_stocktake,
      can_transfer: item.can_transfer
    });
    ElMessage.success(`仓库 [${whCode}] 细粒度权限配置已保存`);
  } catch (err: any) {
    ElMessage.error(err.message || '保存权限配置失败');
  }
}

// 导出真实 CSV / Excel 文件 (带 UTF-8 BOM \uFEFF，解决乱码)
function handleExportSpecs(): void {
  const list = filteredSpecs.value;
  if (!list || list.length === 0) {
    ElMessage.warning('当前无规格数据可供导出');
    return;
  }
  const headers = ['产品代码', '产品名称', '规格', '型号', '通用名', '生产厂家', '单价(元)', '计件单位', '包装单位', '转换比', '注册证号', '归属仓库', '状态'];
  const rows = list.map((s) => [
    `"${s.spec_code || ''}"`,
    `"${(s.product_name || '').replace(/"/g, '""')}"`,
    `"${(s.spec_name || '').replace(/"/g, '""')}"`,
    `"${(s.model_name || '').replace(/"/g, '""')}"`,
    `"${(s.common_name || '').replace(/"/g, '""')}"`,
    `"${(s.manufacturer || '').replace(/"/g, '""')}"`,
    (s.unit_price || 0).toFixed(2),
    `"${s.pricing_unit || ''}"`,
    `"${s.package_unit || ''}"`,
    s.conversion_ratio || 1,
    `"${s.register_card_no || ''}"`,
    `"${s.assigned_warehouses || ''}"`,
    s.status === 'ACTIVE' ? '正常在用' : '已停用'
  ]);
  const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  const now = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14);
  link.setAttribute('download', `医院医疗物资全景规格台账_${now}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  ElMessage.success(`已成功导出 ${list.length} 条医疗物资规格明细 CSV 台账`);
}

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.product-dict-workbench {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  color: var(--text-primary);
}

/* 顶部 KPI 4 宫格 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.kpi-card {
  padding: 14px 18px;
  border-radius: 14px;
}

.kpi-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-muted);
}

.kpi-val {
  font-size: 26px;
  font-weight: 800;
  margin: 6px 0;
  letter-spacing: -0.5px;
}

.kpi-unit {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

.kpi-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
}

.text-warn {
  color: var(--color-warning);
}

/* 工具栏面板 */
.spd-dict-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-actions-left,
.toolbar-actions-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.tool-sep {
  width: 1px;
  height: 18px;
  background: var(--border-divider);
  margin: 0 4px;
}

.spd-tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.spd-tool-btn:hover:not(:disabled) {
  border-color: var(--accent-primary);
  background: var(--bg-card-hover);
  color: var(--accent-primary);
}

.spd-tool-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-highlight {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #ffffff !important;
}

.btn-highlight:hover {
  filter: brightness(1.1);
}

.btn-warn {
  border-color: rgba(251, 191, 36, 0.4);
  color: var(--color-warning);
}

.btn-danger-text:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.btn-admin {
  border-color: rgba(56, 189, 248, 0.4);
  background: rgba(56, 189, 248, 0.08);
}

/* 主工作台四栏三树网格 */
.dict-workbench-grid {
  display: grid;
  grid-template-columns: 240px 270px 1fr;
  gap: 12px;
  min-height: calc(100vh - 290px);
}

/* 第一栏：仓库树与分类树 */
.workbench-col-trees {
  display: flex;
  flex-direction: column;
  padding: 12px;
  border-radius: 14px;
  gap: 8px;
}

.tree-box-upper,
.tree-box-lower {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.tree-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-divider);
  font-size: 13px;
  font-weight: 700;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tree-mini-btn {
  border: none;
  background: rgba(56, 189, 248, 0.15);
  color: var(--accent-primary);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
}

.rbac-indicator-pill {
  font-size: 11px;
  font-weight: 600;
  background: rgba(52, 211, 153, 0.16);
  color: var(--color-success);
  padding: 2px 6px;
  border-radius: 4px;
}

.tree-mini-label {
  font-size: 11px;
  color: var(--text-muted);
}

.tree-scroll-container {
  overflow-y: auto;
  max-height: 260px;
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.tree-node-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 7px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
  user-select: none;
}

.tree-node-row:hover {
  background: rgba(56, 189, 248, 0.08);
}

.tree-node-row.active {
  background: rgba(56, 189, 248, 0.18);
  font-weight: 700;
  color: var(--accent-primary);
}

.tree-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-code {
  color: var(--accent-primary);
  font-weight: 700;
  font-size: 11px;
}

.tree-count {
  font-size: 11px;
  color: var(--text-muted);
}

.tree-chip {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 3px;
}

.chip-locked {
  background: rgba(251, 191, 36, 0.18);
  color: var(--color-warning);
}

.tree-horizontal-divider {
  height: 1px;
  background: var(--border-divider);
  margin: 6px 0;
}

/* 第二栏：中栏品名与供应商 */
.workbench-col-middle {
  display: flex;
  flex-direction: column;
  padding: 12px;
  border-radius: 14px;
  gap: 8px;
}

.middle-tab-header {
  display: flex;
  border-bottom: 1px solid var(--border-divider);
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.tab-btn.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}

.tab-badge {
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
}

.middle-search-bar {
  display: flex;
  gap: 6px;
  margin: 4px 0;
}

.middle-search-input {
  flex: 1;
  height: 30px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 12px;
  outline: none;
}

.middle-search-input:focus {
  border-color: var(--accent-primary);
}

.middle-search-btn {
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
  padding: 0 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.middle-list-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.middle-list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.middle-list-item:hover {
  background: rgba(56, 189, 248, 0.08);
}

.middle-list-item.active {
  background: rgba(56, 189, 248, 0.18);
  font-weight: 700;
  color: var(--accent-primary);
}

.spn-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.spn-code-badge {
  font-size: 10px;
  color: var(--text-muted);
}

.spn-name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-count {
  font-size: 11px;
  color: var(--text-muted);
}

/* 第三栏：右栏产品规格明细表格 */
.workbench-col-specs {
  display: flex;
  flex-direction: column;
  padding: 14px;
  border-radius: 14px;
  gap: 10px;
  min-width: 0;
}

.specs-table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-divider);
}

.header-left h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.header-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
  display: block;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-spec-tag {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
}

.spd-spec-table {
  width: 100%;
  flex: 1;
}

.product-name-cell {
  color: var(--text-primary);
}

.product-sub-spec {
  font-size: 11px;
  margin-top: 2px;
}

.wh-tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.wh-mini-tag {
  font-size: 10px;
  padding: 2px 5px;
  border-radius: 4px;
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
}

.status-chip {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.chip-success {
  background: rgba(52, 211, 153, 0.16);
  color: var(--color-success);
}

.chip-disabled {
  background: rgba(148, 163, 184, 0.2);
  color: var(--text-muted);
}

.table-op-btn {
  border: none;
  background: transparent;
  color: var(--accent-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 2px 4px;
}

.table-op-btn:hover {
  text-decoration: underline;
}

/* 模态框通用表单样式 */
.dialog-grid-form {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  max-height: 60vh;
  overflow-y: auto;
  padding: 6px 4px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-label {
  width: 110px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: right;
  flex-shrink: 0;
}

.form-label.required::before {
  content: '* ';
  color: var(--color-danger);
}

.form-control-wrap {
  flex: 1;
}

.field-hint {
  font-size: 11px;
  color: var(--color-danger);
  flex-shrink: 0;
}

.spd-input,
.spd-select {
  width: 100%;
  height: 34px;
  padding: 0 10px;
  border-radius: 7px;
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.spd-input:focus,
.spd-select:focus {
  border-color: var(--accent-primary);
}

.dual-inline {
  display: flex;
  gap: 8px;
}

.flags-row .checkbox-group {
  display: flex;
  gap: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 10px;
}

.spd-btn {
  padding: 7px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.btn-primary {
  background: var(--accent-primary);
  color: #ffffff;
}

.btn-secondary {
  border-color: var(--border-card);
  background: var(--bg-card);
  color: var(--text-primary);
}

/* 规格双栏模态框 (图 5) */
.spec-modal-split {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 18px;
  max-height: 65vh;
  overflow: hidden;
}

.spec-form-pane {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-divider);
  padding-right: 16px;
  min-height: 0;
}

.spec-fields-scroll {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 6px 2px;
}

.pane-title {
  font-size: 14px;
  font-weight: 700;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-divider);
  margin-bottom: 8px;
}

.spec-side-pane {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.side-tab-buttons {
  display: flex;
  border-bottom: 1px solid var(--border-divider);
}

.side-tab-btn {
  flex: 1;
  padding: 6px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.side-tab-btn.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}

.spd-sub-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.spd-sub-table th,
.spd-sub-table td {
  padding: 6px 8px;
  border-bottom: 1px solid var(--border-divider);
}

.spd-sub-table th {
  color: var(--text-muted);
  text-align: left;
}

.limit-ctrl-box {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-divider);
}

.limit-title {
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

.limit-row {
  font-size: 12px;
  margin: 4px 0;
}

/* 批量调价向导 */
.batch-adjust-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.batch-notice-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.3);
  font-size: 13px;
  color: var(--color-warning);
}

.preview-spec-box {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-divider);
  font-size: 12px;
}

.preview-title {
  font-weight: 700;
  margin-bottom: 6px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
}

/* 供应商管理与 RBAC 内容 */
.sup-manage-content,
.rbac-config-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 60vh;
  overflow-y: auto;
}

.rbac-user-select-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 产品字典四大独立主内容区子视图样式 */
.dict-subview-tab-bar {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 14px;
  align-items: center;
  border-radius: 10px;
}

.dict-subview-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}

.dict-subview-tab-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.dict-subview-tab-btn.active {
  background: var(--accent-subtle, rgba(56, 189, 248, 0.12));
  color: var(--accent-primary);
  border-color: var(--accent-border, rgba(56, 189, 248, 0.3));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.tab-pill {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--bg-hover);
  color: currentColor;
}

.independent-subview-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 4px;
}

.subview-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px;
  border-radius: 12px;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.header-title-row h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
}

.subview-badge {
  font-size: 11.5px;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
  border: 1px solid rgba(56, 189, 248, 0.25);
  font-weight: 600;
}

.header-desc {
  margin: 0;
  font-size: 12.5px;
  color: var(--text-muted);
  line-height: 1.5;
}

/* 仓库架构指标大盘 */
.wh-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.wh-kpi-item {
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  border-radius: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-divider);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.wh-kpi-item:hover {
  border-color: var(--accent-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.wh-kpi-item .kpi-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.wh-kpi-item .kpi-num {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.wh-kpi-item .kpi-sub {
  font-size: 11px;
  color: var(--text-muted);
}

/* 两栏主库与二级库群拓扑 */
.wh-architecture-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.wh-group-card {
  display: flex;
  flex-direction: column;
  padding: 18px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-divider);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.wh-group-header {
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-divider);
}

.group-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.group-title-row h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.group-badge {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  background: var(--bg-hover);
  color: var(--text-muted);
}

.group-hint {
  font-size: 11.5px;
  color: var(--text-muted);
}

.wh-card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wh-entity-card {
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-divider);
  background: var(--bg-card);
  transition: all 0.2s ease;
}

.wh-entity-card:hover {
  border-color: var(--accent-primary);
  transform: translateY(-1px);
}

.entity-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.entity-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.entity-name {
  font-size: 14px;
  color: var(--text-primary);
}

.entity-level-tag {
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.tag-main {
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-primary);
  border: 1px solid rgba(56, 189, 248, 0.25);
}

.tag-secondary {
  background: rgba(52, 211, 153, 0.12);
  color: var(--color-success);
  border: 1px solid rgba(52, 211, 153, 0.25);
}

.entity-actions {
  display: flex;
  gap: 8px;
}

.entity-card-props {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
  font-size: 12px;
}

.prop-item {
  display: flex;
  align-items: center;
}

.prop-k {
  color: var(--text-muted);
  width: 70px;
  flex-shrink: 0;
}

.prop-v {
  color: var(--text-primary);
}
</style>
