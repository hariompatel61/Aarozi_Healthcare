<script setup lang="ts">
import { computed } from 'vue'

export type BadgeVariant =
  | 'emerald'
  | 'blue'
  | 'amber'
  | 'red'
  | 'purple'
  | 'slate'
  | 'teal'

interface Props {
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  pulse?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'slate',
  size: 'md',
  pulse: false,
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'emerald':
      return 'bg-emerald-50 text-emerald-800 border-emerald-200'
    case 'blue':
      return 'bg-blue-50 text-blue-800 border-blue-200'
    case 'amber':
      return 'bg-amber-50 text-amber-800 border-amber-200'
    case 'red':
      return 'bg-red-50 text-red-800 border-red-200 font-bold'
    case 'purple':
      return 'bg-purple-50 text-purple-800 border-purple-200'
    case 'teal':
      return 'bg-teal-50 text-teal-800 border-teal-200'
    case 'slate':
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200'
  }
})

const sizeClasses = computed(() => {
  return props.size === 'sm'
    ? 'px-1.5 py-0.2 text-[10px] leading-tight font-medium rounded'
    : 'px-2 py-0.5 text-xs font-semibold rounded-full'
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center justify-center border select-none transition-colors tracking-wide',
      variantClasses,
      sizeClasses,
      pulse ? 'animate-pulse' : ''
    ]"
  >
    <span
      v-if="pulse"
      class="h-1.5 w-1.5 rounded-full mr-1.5 shrink-0 bg-current"
    />
    <slot />
  </span>
</template>
