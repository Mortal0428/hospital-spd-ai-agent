import { onMounted, onUnmounted, ref } from 'vue';

/**
 * 扫码解析产出结果
 */
export interface BarcodeScanResult {
  rawCode: string;
  diCode?: string;
  piBatch?: string;
  piSerial?: string;
  timestamp: number;
}

/**
 * 扫码枪监听配置项
 */
export interface BarcodeScannerOptions {
  maxIntervalMs?: number;
  minLength?: number;
  onScan?: (result: BarcodeScanResult) => void;
  enabled?: boolean;
}

/**
 * 全局工业条码与医疗器械 UDI 扫码枪无缝驱动 Composable Hook
 * 针对医院常见 USB/蓝牙扫码枪（高速敲击并以 Enter 键结尾）进行特征识别，
 * 精准区分普通人工键盘输入（按键间隔通常 > 80ms）与扫码枪输入（间隔通常 < 40ms）。
 *
 * @param {BarcodeScannerOptions} options 扫码配置项与成功回调
 * @returns {object} { lastScannedCode, isScanning }
 * @route internal://src/composables/useBarcodeScanner
 * @throws 无异常抛出，静默保护
 */
export function useBarcodeScanner(options: BarcodeScannerOptions = {}) {
  const {
    maxIntervalMs = 50,
    minLength = 4,
    onScan
  } = options;

  const lastScannedCode = ref<string>('');
  const isScanning = ref<boolean>(false);

  let buffer: string[] = [];
  let timestamps: number[] = [];

  /**
   * 解析 UDI GS1-128 结构化条码
   */
  function parseUdiBarcode(raw: string): { diCode?: string; piBatch?: string; piSerial?: string } {
    let diCode: string | undefined;
    let piBatch: string | undefined;
    let piSerial: string | undefined;

    // 常见 GS1-128 括号标识符解析: (01)DI(17)EXP(10)LOT(21)SN
    const diMatch = raw.match(/\(01\)(\d{14})/);
    if (diMatch) diCode = diMatch[1];

    const lotMatch = raw.match(/\(10\)([A-Za-z0-9]+)/);
    if (lotMatch) piBatch = lotMatch[1];

    const snMatch = raw.match(/\(21\)([A-Za-z0-9]+)/);
    if (snMatch) piSerial = snMatch[1];

    // 非括号标准前缀兼容
    if (!diCode && raw.length >= 14 && /^\d+$/.test(raw.substring(0, 14))) {
      diCode = raw.substring(0, 14);
    }

    return { diCode, piBatch, piSerial };
  }

  /**
   * 键盘按键事件统一拦截调度
   */
  function handleKeyDown(event: KeyboardEvent): void {
    // 忽略功能控制键与修饰键
    if (['Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab'].includes(event.key)) {
      return;
    }

    const now = performance.now();

    if (event.key === 'Enter') {
      if (buffer.length >= minLength) {
        // 计算相邻字符平均间隔时间
        let totalInterval = 0;
        for (let i = 1; i < timestamps.length; i++) {
          totalInterval += (timestamps[i] - timestamps[i - 1]);
        }
        const avgInterval = timestamps.length > 1 ? totalInterval / (timestamps.length - 1) : 0;

        // 若平均敲击间隔小于阈值，判定为扫码枪
        if (avgInterval <= maxIntervalMs) {
          const rawCode = buffer.join('').trim();
          if (rawCode) {
            event.preventDefault();
            event.stopPropagation();

            const parsed = parseUdiBarcode(rawCode);
            const scanResult: BarcodeScanResult = {
              rawCode,
              ...parsed,
              timestamp: Date.now()
            };

            lastScannedCode.value = rawCode;
            if (onScan) {
              onScan(scanResult);
            }
          }
        }
      }
      // 清空当前缓冲区
      buffer = [];
      timestamps = [];
      isScanning.value = false;
      return;
    }

    // 仅收集长度为 1 的可打印字符
    if (event.key.length === 1) {
      if (timestamps.length > 0) {
        const diff = now - timestamps[timestamps.length - 1];
        if (diff > maxIntervalMs * 2.5) {
          // 敲击超时，重置缓冲区
          buffer = [];
          timestamps = [];
        }
      }

      buffer.push(event.key);
      timestamps.push(now);
      isScanning.value = buffer.length > 2;
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown, true);
  });

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown, true);
  });

  return {
    lastScannedCode,
    isScanning
  };
}
