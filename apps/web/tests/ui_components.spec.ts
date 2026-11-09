import { describe, it, expect } from 'vitest'
import { useToast } from '../composables/useToast'
import Button from '../components/ui/Button.vue'
import Input from '../components/ui/Input.vue'
import Select from '../components/ui/Select.vue'
import Badge from '../components/ui/Badge.vue'
import Card from '../components/ui/Card.vue'
import DataTable from '../components/ui/DataTable.vue'
import Modal from '../components/ui/Modal.vue'
import ToastProvider from '../components/ui/ToastProvider.vue'

describe('UI Primitives and Design System Primitives', () => {
  it('exports all required clinical UI components', () => {
    expect(Button).toBeDefined()
    expect(Input).toBeDefined()
    expect(Select).toBeDefined()
    expect(Badge).toBeDefined()
    expect(Card).toBeDefined()
    expect(DataTable).toBeDefined()
    expect(Modal).toBeDefined()
    expect(ToastProvider).toBeDefined()
  })

  it('manages reactive toasts with useToast composable', () => {
    const { toasts, success, error, warning, info, dismiss, clearAll } = useToast()
    clearAll()
    expect(toasts.value.length).toBe(0)

    const id1 = success('Patient Registered', 'UHID: 2026-0001')
    expect(toasts.value.length).toBe(1)
    expect(toasts.value[0]?.type).toBe('success')
    expect(toasts.value[0]?.title).toBe('Patient Registered')

    error('Critical Value', 'Potassium: 2.4 mEq/L')
    expect(toasts.value.length).toBe(2)
    expect(toasts.value[1]?.type).toBe('error')

    warning('Re-test recommended')
    info('Sample received')
    expect(toasts.value.length).toBe(4)

    dismiss(id1)
    expect(toasts.value.length).toBe(3)
    expect(toasts.value.some((t) => t.id === id1)).toBe(false)

    clearAll()
    expect(toasts.value.length).toBe(0)
  })
})
