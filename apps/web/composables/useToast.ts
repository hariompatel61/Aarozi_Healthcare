import { ref } from 'vue'

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  description?: string
  durationMs?: number
}

const toasts = ref<ToastMessage[]>([])

export function useToast() {
  function show(toast: Omit<ToastMessage, 'id'>) {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`
    const duration = toast.durationMs ?? 4000
    const newToast: ToastMessage = { ...toast, id }
    
    toasts.value.push(newToast)

    if (duration > 0) {
      setTimeout(() => {
        dismiss(id)
      }, duration)
    }

    return id
  }

  function success(title: string, description?: string) {
    return show({ type: 'success', title, description })
  }

  function error(title: string, description?: string) {
    return show({ type: 'error', title, description, durationMs: 6000 })
  }

  function warning(title: string, description?: string) {
    return show({ type: 'warning', title, description })
  }

  function info(title: string, description?: string) {
    return show({ type: 'info', title, description })
  }

  function dismiss(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function clearAll() {
    toasts.value = []
  }

  return {
    toasts,
    show,
    success,
    error,
    warning,
    info,
    dismiss,
    clearAll,
  }
}
