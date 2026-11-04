import { httpGet, httpPost } from './request';

/**
 * 供应商与多级采购协同单据模型契约
 */
export interface SupplierPurchaseOrder {
  order_no: string;
  supplier_code: string;
  supplier_name: string;
  license_no: string;
  qual_audit_status: 'QUAL_PENDING' | 'QUAL_APPROVED' | 'QUAL_REJECTED';
  apply_dept_code: string;
  audit_main_dept_code: string;
  product_code: string;
  product_name: string;
  purchase_qty: number;
  picked_batch_no: string | null;
  purchase_flow_status: string;
  auto_inbound_order_no: string | null;
}

/**
 * 查询全院多级采购计划单、供应商经营资质准入状态及发货单列表
 * @returns Promise<SupplierPurchaseOrder[]> 采供单据列表
 * @route GET /ext/supplier-purchase/list
 * @throws Error 当请求异常时抛出
 */
export function listSupplierPurchaseOrders(): Promise<SupplierPurchaseOrder[]> {
  return httpGet('/ext/supplier-purchase/list');
}

/**
 * 供应商上传《医疗器械经营许可证》或医院耗材/设备科审核准入资质
 * @param data 资质审核请求载荷
 * @returns Promise 审核结果
 * @route POST /ext/supplier-purchase/qual-audit
 * @throws Error 当写入异常时抛出
 */
export function auditSupplierQualification(data: {
  supplier_code: string;
  supplier_name: string;
  license_no: string;
  license_expiry_date: string;
  audit_action: 'QUAL_PENDING' | 'QUAL_APPROVED' | 'QUAL_REJECTED';
}): Promise<{ supplier_code: string; license_no: string; qual_audit_status: string; affected_orders: number }> {
  return httpPost('/ext/supplier-purchase/qual-audit', data);
}

/**
 * 执行临床采购计划提报、主科审批、供应商接单拣货与二次确认发货（发货后自动生成医院待验收入库单）
 * @param data 采供流转动作载荷
 * @returns Promise 流转更新后的单据对象
 * @route POST /ext/supplier-purchase/flow
 * @throws Error 当供应商资质未过审尝试接单发货时抛出 403 拦截异常
 */
export function flowSupplierPurchaseAction(data: {
  order_no?: string;
  flow_action: 'CREATE_PLAN' | 'DEPT_APPROVE' | 'SUPPLIER_PICK_AND_SHIP';
  supplier_code?: string;
  apply_dept_code?: string;
  product_id?: number;
  purchase_qty?: number;
  picked_batch_no?: string;
  picked_expiry_date?: string;
  operator_name: string;
}): Promise<{ order_no: string; supplier_code: string; qual_audit_status: string; purchase_flow_status: string; auto_inbound_order_no: string | null }> {
  return httpPost('/ext/supplier-purchase/flow', data);
}

/**
 * 主库管理员对供应商送货单实施实物查验与批号核验并正式验收入库
 * @param data 验收入库载荷
 * @returns Promise 验收入库结果
 * @route POST /ext/orders/supplier-delivery/accept
 * @throws Error 当验收失败时抛出
 */
export function acceptSupplierDeliveryInbound(data: {
  order_no: string;
  warehouse_code?: string;
  operator_name: string;
  accept_remark?: string;
}): Promise<{ order_no: string; warehouse_code: string; quantity: number; status: string }> {
  return httpPost('/ext/orders/supplier-delivery/accept', data);
}

