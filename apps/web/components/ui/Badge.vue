<script setup lang="ts">
import { computed } from 'vue'

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'panic'

interface Props {
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  dot?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'neutral',
  size: 'sm',
  dot: false,
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800'
    case 'warning':
      return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800'
    case 'danger':
      return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/60 dark:text-red-300 dark:border-red-800'
    case 'info':
      return 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/60 dark:text-sky-300 dark:border-sky-800'
    case 'panic':
      return 'bg-red-600 text-white border-red-700 animate-pulse font-bold'
    case 'neutral':
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700'
  }
})

const dotColor = computed(() => {
  switch (props.variant) {
    case 'success': return 'bg-emerald-500'
    case 'warning': return 'bg-amber-500'
    case 'danger': return 'bg-red-500'
    case 'info': return 'bg-sky-500'
    case 'panic': return 'bg-white'
    case 'neutral':
    default: return 'bg-slate-400'
  }
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-medium rounded-full border select-none transition-colors whitespace-nowrap',
      variantClasses,
      size === 'sm' ? 'px-2 py-0.5 text-[11px] leading-tight gap-1.5' : 'px-2.5 py-1 text-xs leading-none gap-2'
    ]"
  >
    <span
      v-if="dot"
      :class="['w-1.5 h-1.5 rounded-full shrink-0', dotColor, variant === 'panic' ? 'animate-ping' : '']"
    />
    <slot />
  </span>
</template>
