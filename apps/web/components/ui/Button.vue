<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-teal-600 hover:bg-teal-700 text-white font-medium shadow-sm focus:ring-teal-500 border border-transparent'
    case 'secondary':
      return 'bg-white hover:bg-slate-50 text-slate-700 font-medium border border-slate-300 shadow-sm focus:ring-slate-400'
    case 'danger':
      return 'bg-red-600 hover:bg-red-700 text-white font-medium shadow-sm focus:ring-red-500 border border-transparent'
    case 'ghost':
      return 'bg-transparent hover:bg-slate-100 text-slate-600 font-medium focus:ring-slate-400 border border-transparent'
    default:
      return 'bg-teal-600 text-white'
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-2.5 py-1 text-xs rounded'
    case 'lg':
      return 'px-4 py-2.5 text-base rounded-md'
    case 'md':
    default:
      return 'px-3.5 py-2 text-sm rounded-md'
  }
})
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 select-none',
      variantClasses,
      sizeClasses,
      disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
    ]"
  >
    <svg
      v-if="loading"
      class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8H4z"
      />
    </svg>
    <slot />
  </button>
</template>
