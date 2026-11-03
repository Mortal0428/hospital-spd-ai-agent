import { ref, watch, onMounted, type Ref } from 'vue';

/**
 * 草稿配置选项
 */
export interface FormDraftOptions<T> {
  formKey: string;
  formData: Ref<T>;
  debounceMs?: number;
  autoSave?: boolean;
}

/**
 * 复杂单据本地草稿自动暂存与一键恢复 Hook
 * 针对医院业务中科室请领、验收入库等复杂多行填单场景，自动将未提交数据防抖持久化至 LocalStorage，
 * 彻底防止护士突发紧急抢救、网络波动或误触刷新导致的数据丢失。
 *
 * @param {FormDraftOptions<T>} options 草稿配置项
 * @returns {object} { hasDraft, draftTime, restoreDraft, clearDraft }
 * @route internal://src/composables/useFormDraft
 * @throws 无异常抛出
 */
export function useFormDraft<T extends Record<string, any>>(options: FormDraftOptions<T>) {
  const {
    formKey,
    formData,
    debounceMs = 1000,
    autoSave = true
  } = options;

  const storageKey = `spd_form_draft_${formKey}`;
  const hasDraft = ref<boolean>(false);
  const draftTime = ref<string>('');
  let timer: any = null;

  /**
   * 检查本地是否已有历史暂存草稿
   */
  function checkExistingDraft(): void {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.data) {
          hasDraft.value = true;
          draftTime.value = parsed.savedAt || '未知时间';
        }
      } catch {
        hasDraft.value = false;
      }
    } else {
      hasDraft.value = false;
    }
  }

  /**
   * 将当前表单数据保存至草稿
   */
  function saveDraftNow(): void {
    try {
      const payload = {
        savedAt: new Date().toLocaleTimeString(),
        data: formData.value
      };
      localStorage.setItem(storageKey, JSON.stringify(payload));
      hasDraft.value = true;
      draftTime.value = payload.savedAt;
    } catch (err) {
      console.warn(`[Draft] 草稿保存失败: ${formKey}`, err);
    }
  }

  /**
   * 一键恢复暂存草稿内容至当前表单
   * @returns {boolean} 恢复是否成功
   */
  function restoreDraft(): boolean {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return false;
    try {
      const parsed = JSON.parse(raw);
      if (parsed && parsed.data) {
        Object.assign(formData.value, parsed.data);
        return true;
      }
    } catch (err) {
      console.error(`[Draft] 草稿解析异常: ${formKey}`, err);
    }
    return false;
  }

  /**
   * 提交成功后或用户主动放弃时清空本地草稿
   */
  function clearDraft(): void {
    localStorage.removeItem(storageKey);
    hasDraft.value = false;
    draftTime.value = '';
  }

  onMounted(() => {
    checkExistingDraft();
  });

  if (autoSave) {
    watch(
      formData,
      () => {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
          saveDraftNow();
        }, debounceMs);
      },
      { deep: true }
    );
  }

  return {
    hasDraft,
    draftTime,
    restoreDraft,
    clearDraft,
    saveDraftNow
  };
}
