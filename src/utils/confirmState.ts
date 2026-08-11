import { ref } from 'vue'

export interface ConfirmOptions {
  title?: string
  message: string
  detail?: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}

export const confirmState = ref({
  isOpen: false,
  title: '删除确认',
  message: '',
  detail: '',
  confirmText: '确认删除',
  cancelText: '取消',
  type: 'danger' as 'danger' | 'warning' | 'info',
  resolve: null as ((value: boolean) => void) | null
})

export function showConfirm(options: ConfirmOptions): Promise<boolean> {
  // If there's an existing unresolved confirm dialog, resolve it as false first
  if (confirmState.value.isOpen && confirmState.value.resolve) {
    confirmState.value.resolve(false)
  }

  return new Promise((resolve) => {
    confirmState.value = {
      isOpen: true,
      title: options.title || (options.type === 'warning' ? '操作确认' : '确认删除'),
      message: options.message,
      detail: options.detail || '',
      confirmText: options.confirmText || (options.type === 'warning' ? '确认' : '彻底删除'),
      cancelText: options.cancelText || '取消',
      type: options.type || 'danger',
      resolve
    }
  })
}

export function closeConfirm(result: boolean) {
  if (confirmState.value.resolve) {
    confirmState.value.resolve(result)
  }
  confirmState.value.isOpen = false
  confirmState.value.resolve = null
}
