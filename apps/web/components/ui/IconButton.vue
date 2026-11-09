<script setup lang="ts">
import { computed } from 'vue'
import Icon, { type IconName } from './Icon.vue'

interface Props {
  icon?: IconName
  label: string
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  shape?: 'square' | 'round'
  type?: 'button' | 'submit'
  disabled?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'ghost',
  size: 'md',
  shape: 'square',
  type: 'button',
  disabled: false,
  loading: false,
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-teal-600 hover:bg-teal-700 text-white shadow-xs focus:ring-teal-500'
    case 'secondary':
      return 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700 shadow-2xs focus:ring-slate-400'
    case 'danger':
      return 'bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-800 focus:ring-red-400'
    case 'ghost':
    default:
      return 'bg-transparent hover:bg-slate-100 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 focus:ring-slate-400'
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm': return 'w-7 h-7'
    case 'lg': return 'w-11 h-11'
    case 'md':
    default: return 'w-9 h-9'
  }
})

const iconSize = computed(() => {
  switch (props.size) {
    case 'sm': return 'xs'
    case 'lg': return 'md'
    case 'md':
    default: return 'sm'
  }
})
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :aria-label="label"
    :title="label"
    :class="[
      'inline-flex items-center justify-center shrink-0 transition-all select-none',
      'focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-slate-900',
      'active:scale-95',
      shape === 'round' ? 'rounded-full' : 'rounded-md',
      variantClasses,
      sizeClasses,
      disabled || loading ? 'opacity-50 cursor-not-allowed pointer-events-none' : 'cursor-pointer'
    ]"
  >
    <svg
      v-if="loading"
      class="animate-spin h-3.5 w-3.5 text-current"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
    <slot v-else>
      <Icon v-if="icon" :name="icon" :size="iconSize" />
    </slot>
  </button>
</template>

