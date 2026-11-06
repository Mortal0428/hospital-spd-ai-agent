import { httpGet, httpPost } from './request';

/**
 * 高值耗材全生命周期扩展单据模型契约
 */
export interface HighValueLifecycleOrder {
  order_no: string;
  hv_biz_type: string;
  dept_code: string;
  product_code: string;
  product_name: string;
  udi_sn: string;
  qr_code_payload: string;
  is_qr_verified: number;
  patient_inpatient_no: string | null;
  patient_name_masked: string | null;
  confirm_stage: 'PENDING_CONFIRM' | 'SUBMITTED';
  is_irreversible_locked: number;
  operator_name: string;
  remark: string | null;
}

/**
 * 查询高值耗材备货申请、科室接收、退货出库或报损单列表
 * @param params 可选业务类型过滤参数 (hv_biz_type)
 * @returns Promise<HighValueLifecycleOrder[]> 单据列表
 * @route GET /ext/high-value/lifecycle
 * @throws Error 当请求异常时抛出
 */
export function listHighValueLifecycleOrders(params?: { hv_biz_type?: string }): Promise<HighValueLifecycleOrder[]> {
  return httpGet('/ext/high-value/lifecycle', params);
}

/**
 * 创建高值耗材备货、科室接收、退货出库或报损单（自动生成专属二维码载荷）
 * @param data 制单请求载荷
 * @returns Promise 创建的高值记录
 * @route POST /ext/high-value/lifecycle
 * @throws Error 当产品不存在时抛出
 */
export function createHighValueLifecycleOrder(data: {
  hv_biz_type: string;
  dept_code: string;
  product_id: number;
  udi_sn: string;
  operator_name: string;
  remark?: string;
}): Promise<{ order_no: string; udi_sn: string; qr_code_payload: string; confirm_stage: string; is_irreversible_locked: number }> {
  return httpPost('/ext/high-value/lifecycle', data);
}

/**
 * 执行高值单据外层二次确认或取消提交（高值科室退货出库单二次确认后永久锁死）
 * @param data 动作请求载荷
 * @returns Promise 更新后的单据摘要
 * @route POST /ext/high-value/two-step-action
 * @throws Error 当对已二次确认的高值退货单取消提交时抛出不可逆拦截异常
 */
export function executeHighValueTwoStepAction(data: {
  order_no: string;
  action: 'SECOND_CONFIRM' | 'CANCEL_SUBMIT' | 'EDIT_REMARK' | 'DELETE_ORDER';
  operator_name: string;
  new_remark?: string;
}): Promise<any> {
  return httpPost('/ext/high-value/two-step-action', data);
}

/**
 * 扫描高值耗材一物一码专属二维码完成患者核销绑定
 * @param data 包含 udi_sn, patient_inpatient_no, patient_name, operator_name 的核销请求
 * @returns Promise 绑定脱敏患者后的核销详情
 * @route POST /ext/high-value/qr-verify
 * @throws Error 当未找到单品时抛出 404
 */
export function verifyHighValueQrScan(data: {
  udi_sn: string;
  patient_inpatient_no: string;
  patient_name: string;
  operator_name: string;
}): Promise<{ order_no: string; udi_sn: string; is_qr_verified: number; patient_inpatient_no: string; patient_name_masked: string }> {
  return httpPost('/ext/high-value/qr-verify', data);
}

/**
 * 【高值核销查询】专用接口：仅查询已扫码核销绑定患者的高值单品
 * @returns Promise<HighValueLifecycleOrder[]> 列表
 * @route GET /ext/high-value/verified-list
 * @throws Error 当查询异常时抛出
 */
export function listVerifiedHighValueItems(): Promise<HighValueLifecycleOrder[]> {
  return httpGet('/ext/high-value/verified-list');
}

/**
 * 不良事件紧急召回批次汇总契约
 */
export interface RecallBatchSummary {
  batch_no: string;
  product_name: string;
  product_code: string;
  spec_model: string;
  unit_price: number;
  expiry_date: string;
  total_items_in_batch: number;
  in_stock_frozen_count: number;
  implanted_patients_count: number;
}

/**
 * 不良事件已植入患者紧急追查清册项契约
 */
export interface RecallPatientItem {
  udi_sn: string;
  batch_no: string;
  product_code: string;
  product_name: string;
  spec_model: string;
  patient_inpatient_no: string;
  patient_name_masked: string;
  surgery_name: string;
  attending_doctor: string;
  verify_nurse_name: string;
  verified_at: string;
  current_dept_name: string;
  follow_up_status: 'PENDING_CONTACT' | 'CONTACTED_NORMAL' | 'ADVERSE_OBSERVED' | 'COMPENSATED';
  follow_up_doctor: string;
  follow_up_remark: string;
  updated_at: string;
}

/**
 * 不良事件穿透返回结构
 */
export interface RecallTraceResult {
  batch_list?: Array<{
    batch_no: string;
    product_name: string;
    product_code: string;
    spec_model: string;
    total_items: number;
    implanted_count: number;
    in_stock_count: number;
  }>;
  batch_summary: RecallBatchSummary | null;
  patient_list: RecallPatientItem[];
}

/**
 * 穿透查询不良事件召回批次对应的在库锁定件数与已植入患者紧急追访清册
 * @param batch_no 可选生产批号，为空时返回全院批次追查汇总
 * @returns Promise<RecallTraceResult> 穿透追查清册
 * @route GET /api/v1/extended-spd/recall/trace-patients
 * @throws Error 当请求异常时抛出
 */
export function traceRecallPatients(batch_no?: string): Promise<RecallTraceResult> {
  return httpGet('/ext/recall/trace-patients', batch_no ? { batch_no } : undefined);
}

/**
 * 更新不良事件已植入患者的医学随访状态与处置记录（触发 6W 审计日志）
 * @param data 随访状态流转载荷
 * @returns Promise<any> 更新回执
 * @route POST /api/v1/ext/recall/update-follow-up
 * @throws Error 异常抛出
 */
export function updateRecallFollowUp(data: {
  udi_sn: string;
  batch_no?: string;
  follow_up_status: string;
  follow_up_doctor?: string;
  follow_up_remark?: string;
  operator_name?: string;
}): Promise<any> {
  return httpPost('/ext/recall/update-follow-up', data);
}

