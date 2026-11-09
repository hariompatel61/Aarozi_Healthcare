<script setup lang="ts">
import Modal from './Modal.vue'
import Button from './Button.vue'
import Icon from './Icon.vue'

interface Props {
  modelValue: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  severity?: 'danger' | 'warning' | 'info'
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  severity: 'danger',
  loading: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function onConfirm() {
  emit('confirm')
}

function onCancel() {
  emit('update:modelValue', false)
  emit('cancel')
}
</script>

<template>
  <Modal
    :model-value="modelValue"
    size="sm"
    @update:model-value="(val) => emit('update:modelValue', val)"
    @close="onCancel"
  >
    <div class="flex items-start gap-3.5">
      <!-- Severity Icon Badge -->
      <div
        :class="[
          'w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-2xs',
          severity === 'danger' ? 'bg-red-50 text-red-600 dark:bg-red-950/60 dark:text-red-400' : '',
          severity === 'warning' ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400' : '',
          severity === 'info' ? 'bg-teal-50 text-teal-600 dark:bg-teal-950/60 dark:text-teal-400' : ''
        ]"
      >
        <Icon
          :name="severity === 'danger' ? 'alert-triangle' : severity === 'warning' ? 'alert-circle' : 'shield-check'"
          size="md"
        />
      </div>

      <!-- Text Content -->
      <div>
        <h4 class="text-sm font-bold text-slate-900 dark:text-slate-100">
          {{ title }}
        </h4>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
          {{ message }}
        </p>
      </div>
    </div>

    <template #footer>
      <Button
        variant="secondary"
        size="sm"
        :disabled="loading"
        @click="onCancel"
      >
        {{ cancelText }}
      </Button>
      <Button
        :variant="severity === 'danger' ? 'danger' : severity === 'warning' ? 'primary' : 'success'"
        size="sm"
        :loading="loading"
        @click="onConfirm"
      >
        {{ confirmText }}
      </Button>
    </template>
  </Modal>
</template>

