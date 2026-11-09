<script setup lang="ts">
import { computed } from 'vue'

export interface SegmentOption {
  label: string
  value: any
  badge?: string | number
}

interface Props {
  modelValue: any
  options: (SegmentOption | string)[]
  size?: 'sm' | 'md'
  disabled?: boolean
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  disabled: false,
  fullWidth: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: any): void
  (e: 'change', val: any): void
}>()

const normalizedOptions = computed<SegmentOption[]>(() => {
  return props.options.map((opt) => {
    if (typeof opt === 'string') {
      return { label: opt, value: opt }
    }
    return opt
  })
})

function select(val: any) {
  if (props.disabled) return
  emit('update:modelValue', val)
  emit('change', val)
}
</script>

<template>
  <div
    role="tablist"
    :class="[
      'inline-flex p-1 bg-slate-100 dark:bg-slate-800 rounded-lg select-none transition-colors border border-slate-200 dark:border-slate-700/60',
      fullWidth ? 'w-full' : '',
      size === 'sm' ? 'h-7' : 'h-9',
      disabled ? 'opacity-50 pointer-events-none' : ''
    ]"
  >
    <button
      v-for="opt in normalizedOptions"
      :key="String(opt.value)"
      type="button"
      role="tab"
      :aria-selected="modelValue === opt.value"
      :class="[
        'relative inline-flex items-center justify-center font-semibold rounded-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-teal-500 cursor-pointer',
        fullWidth ? 'flex-1' : '',
        size === 'sm' ? 'px-2.5 text-[11px]' : 'px-3.5 text-xs',
        modelValue === opt.value
          ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
          : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
      ]"
      @click="select(opt.value)"
    >
      <span>{{ opt.label }}</span>
      <span
        v-if="opt.badge !== undefined"
        :class="[
          'ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] font-bold',
          modelValue === opt.value
            ? 'bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300'
            : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
        ]"
      >
        {{ opt.badge }}
      </span>
    </button>
  </div>
</template>

