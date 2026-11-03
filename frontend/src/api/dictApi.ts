import { httpGet, httpPost, httpPut, httpDelete } from './request';

/**
 * 仓库树节点模型契约
 */
export interface WarehouseNode {
  id?: number;
  warehouse_code: string;
  warehouse_name: string;
  warehouse_level: string;
  parent_code?: string;
  dept_code: string;
  init_stock_locked: number;
  init_stock_order_no: string | null;
  init_locked_at?: string | null;
  status?: number;
}

/**
 * 产品分类树节点模型契约
 */
export interface CategoryNode {
  id?: number;
  category_code: string;
  category_name: string;
  main_dept_code: string;
  consumable_level: string;
  parent_id?: number;
  storage_condition?: string;
  sort_order?: number;
}

/**
 * 通用大品名 (Generic SPN) 契约 (对应图 3 新增品名)
 */
export interface SpnItem {
  id: number;
  spn_code: string;
  spn_name: string;
  category_code: string;
  common_name: string;
  pinyin_code: string;
  finance_category: string;
  performance_category: string;
  inpatient_charge_category: string;
  outpatient_charge_category: string;
  medical_record_category: string;
  medicare_category: string;
  is_chargeable: number;
  is_high_value: number;
  is_central_proc: number;
  central_proc_project: string;
  contract_no: string;
  contract_signed_date?: string | null;
  contract_start_date?: string | null;
  contract_end_date?: string | null;
  status: string;
  created_at: string;
  spec_count: number;
}

/**
 * 型号规格单品 (Spec SKU) 契约 (对应图 4 右栏与图 5 规格录入)
 */
export interface SpecItem {
  id: number;
  spn_id: number;
  spec_code: string;
  product_name: string;
  spec_name: string;
  model_name: string;
  common_name: string;
  component_name: string;
  pinyin_code: string;
  brand_name: string;
  manufacturer: string;
  description: string;
  pricing_unit: string;
  package_unit: string;
  conversion_ratio: number;
  unit_price: number;
  register_card_no: string;
  register_expiry_date?: string | null;
  medicare_code: string;
  medicare_category_code: string;
  production_license_no: string;
  production_license_expiry?: string | null;
  default_supplier_id: number;
  default_supplier_name: string;
  original_code: string;
  provincial_code: string;
  storage_condition: string;
  is_central_proc: number;
  central_proc_code: string;
  origin_place: string;
  category_code: string;
  status: string; // 'ACTIVE' | 'DISABLED'
  assigned_warehouses: string;
  created_at: string;
}

/**
 * 供应商资质档案模型契约 (对应图 4 中栏供应商 Tab)
 */
export interface SupplierProfileItem {
  id: number;
  supplier_code: string;
  supplier_name: string;
  social_credit_code: string;
  license_no: string;
  license_expiry_date: string;
  contact_person: string;
  contact_phone: string;
  supply_categories: string;
  qual_status: string;
  status: string;
  created_at: string;
}

/**
 * 调价历史记录快照契约 (对应图 5 调价记录 Tab)
 */
export interface PriceAdjustLogItem {
  id: number;
  spec_id: number;
  spec_code: string;
  spec_name: string;
  old_price: number;
  new_price: number;
  adjust_diff: number;
  adjust_reason: string;
  adjust_doc_no: string;
  operator_name: string;
  effective_time: string;
}

/**
 * 用户-仓库细粒度授权矩阵契约
 */
export interface UserWarehousePermItem {
  id: number;
  user_id: number;
  username: string;
  warehouse_code: string;
  can_view: number;
  can_apply: number;
  can_inbound: number;
  can_outbound: number;
  can_stocktake: number;
  can_transfer: number;
  updated_by: string;
  updated_at: string;
}

/**
 * 存量兼容产品字典条目
 */
export interface ProductDictItem {
  product_id: number;
  product_code: string;
  product_name: string;
  common_name: string;
  pinyin_code: string;
  component_name: string;
  brand_name: string;
  spec_model: string;
  unit: string;
  main_dept_code: string;
  consumable_level: string;
  assigned_warehouses: string[];
  supplier_code: string;
  previous_price: number;
  current_price: number;
  price_updated_reason: string;
  is_disabled: number;
}

// =========================================================================
// 1. 大品名 (SPN) API
// =========================================================================

export function listSpns(params?: { category_code?: string; keyword?: string }): Promise<SpnItem[]> {
  return httpGet('/dict/spns', params);
}

export function createSpn(data: Partial<SpnItem>): Promise<SpnItem> {
  return httpPost('/dict/spns', data);
}

export function updateSpn(spnId: number, data: Partial<SpnItem>): Promise<SpnItem> {
  return httpPut(`/dict/spns/${spnId}`, data);
}

export function deleteSpn(spnId: number): Promise<{ spn_id: number }> {
  return httpDelete(`/dict/spns/${spnId}`);
}

// =========================================================================
// 2. 规格型号单品 (Spec SKU) API
// =========================================================================

export function listSpecs(params?: {
  spn_id?: number;
  category_code?: string;
  warehouse_code?: string;
  keyword?: string;
  status_filter?: string;
}): Promise<SpecItem[]> {
  return httpGet('/dict/specs', params);
}

export function createSpec(data: Partial<SpecItem>): Promise<SpecItem> {
  return httpPost('/dict/specs', data);
}

export function updateSpec(specId: number, data: Partial<SpecItem>): Promise<SpecItem> {
  return httpPut(`/dict/specs/${specId}`, data);
}

export function deleteSpec(specId: number): Promise<{ spec_id: number }> {
  return httpDelete(`/dict/specs/${specId}`);
}

export function toggleSpecStatus(specId: number): Promise<SpecItem> {
  return httpPost(`/dict/specs/${specId}/toggle-status`);
}

// =========================================================================
// 3. 集中带量采购批量调价 API
// =========================================================================

export function batchAdjustPrice(data: {
  spec_ids: number[];
  adjust_type: 'FIXED_PRICE' | 'PERCENT_DISCOUNT' | 'FIXED_OFFSET';
  adjust_value: number;
  reason: string;
  doc_no?: string;
}): Promise<{ affected_count: number; adjust_type: string; adjust_reason: string }> {
  return httpPost('/dict/batch-adjust-price', data);
}

export function listPriceAdjustLogs(params?: { spec_id?: number; spec_code?: string }): Promise<PriceAdjustLogItem[]> {
  return httpGet('/dict/price-adjust-logs', params);
}

// =========================================================================
// 4. 供应商资质档案管理 API
// =========================================================================

export function listSuppliers(params?: { keyword?: string }): Promise<SupplierProfileItem[]> {
  return httpGet('/dict/suppliers', params);
}

export function createSupplier(data: Partial<SupplierProfileItem>): Promise<SupplierProfileItem> {
  return httpPost('/dict/suppliers', data);
}

export function updateSupplier(id: number, data: Partial<SupplierProfileItem>): Promise<SupplierProfileItem> {
  return httpPut(`/dict/suppliers/${id}`, data);
}

export function deleteSupplier(id: number): Promise<{ supplier_id: number }> {
  return httpDelete(`/dict/suppliers/${id}`);
}

// =========================================================================
// 5. 仓库树与用户细粒度授权 API
// =========================================================================

export function listWarehouses(): Promise<WarehouseNode[]> {
  return httpGet('/dict/warehouses');
}

export function createWarehouse(data: Partial<WarehouseNode>): Promise<WarehouseNode> {
  return httpPost('/dict/warehouses', data);
}

export function updateWarehouse(id: number, data: Partial<WarehouseNode>): Promise<WarehouseNode> {
  return httpPut(`/dict/warehouses/${id}`, data);
}

export function deleteWarehouse(id: number): Promise<{ warehouse_id: number }> {
  return httpDelete(`/dict/warehouses/${id}`);
}

export function listCategories(): Promise<CategoryNode[]> {
  return httpGet('/dict/categories');
}

export function createCategory(data: Partial<CategoryNode>): Promise<CategoryNode> {
  return httpPost('/dict/categories', data);
}

export function updateCategory(id: number, data: Partial<CategoryNode>): Promise<CategoryNode> {
  return httpPut(`/dict/categories/${id}`, data);
}

export function deleteCategory(id: number): Promise<{ category_id: number }> {
  return httpDelete(`/dict/categories/${id}`);
}

export function getUserWarehousePerms(userId?: number): Promise<UserWarehousePermItem[]> {
  return httpGet('/dict/user-warehouse-perms', userId ? { user_id: userId } : undefined);
}

export function upsertUserWarehousePerm(data: {
  user_id: number;
  warehouse_code: string;
  can_view: number;
  can_apply: number;
  can_inbound: number;
  can_outbound: number;
  can_stocktake: number;
  can_transfer: number;
}): Promise<UserWarehousePermItem> {
  return httpPost('/dict/user-warehouse-perms', data);
}

// =========================================================================
// 存量兼容 API
// =========================================================================

export function getDictOverview(params?: {
  warehouse_code?: string;
  show_disabled?: number;
  keyword?: string;
}): Promise<{
  warehouse_tree: WarehouseNode[];
  category_tree: CategoryNode[];
  products: ProductDictItem[];
}> {
  return httpGet('/ext/dict/overview', params);
}

export function copyProductToWarehouse(data: {
  product_id: number;
  target_warehouse_code: string;
}): Promise<{ product_id: number; product_code: string; assigned_warehouses: string[] }> {
  return httpPost('/ext/dict/copy-warehouse', data);
}

export function adjustProductPrice(data: {
  product_id: number;
  new_price: number;
  reason: string;
}): Promise<{ product_id: number; previous_price: number; current_price: number; reason: string }> {
  return httpPost('/ext/dict/adjust-price', data);
}

