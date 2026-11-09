<script setup lang="ts">
import { computed } from 'vue'
import Icon, { type IconName } from './Icon.vue'

/**
 * Aarozi Healthcare Design System Button Component
 * Strictly complies with 3-tier tokens, accessibility and keyboard navigation.
 */
interface Props {
  variant?: 'primary' | 'secondary' | 'tertiary' | 'danger' | 'success' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  iconLeft?: IconName
  iconRight?: IconName
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false,
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white font-semibold shadow-xs border border-transparent focus:ring-teal-500'
    case 'secondary':
      return 'bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 font-semibold border border-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700 shadow-2xs focus:ring-slate-400'
    case 'tertiary':
      return 'bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-700 font-semibold border border-transparent dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 focus:ring-slate-400'
    case 'success':
      return 'bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-semibold shadow-xs border border-transparent focus:ring-emerald-500'
    case 'danger':
      return 'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-semibold shadow-xs border border-transparent focus:ring-red-500'
    case 'ghost':
      return 'bg-transparent hover:bg-slate-100 active:bg-slate-200 text-slate-600 dark:text-slate-300 dark:hover:bg-slate-800 font-medium border border-transparent focus:ring-slate-400'
    default:
      return 'bg-teal-600 text-white'
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-7 px-2.5 text-xs gap-1.5 rounded-md'
    case 'lg':
      return 'h-11 px-5 text-base gap-2.5 rounded-lg'
    case 'md':
    default:
      return 'h-9 px-3.5 text-sm gap-2 rounded-md'
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
    :class="[
      'inline-flex items-center justify-center font-sans select-none transition-all duration-150',
      'focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-slate-900',
      'active:scale-[0.98]',
      variantClasses,
      sizeClasses,
      fullWidth ? 'w-full' : '',
      disabled || loading ? 'opacity-50 cursor-not-allowed pointer-events-none active:scale-100' : 'cursor-pointer'
    ]"
  >
    <!-- Loading Spinner -->
    <svg
      v-if="loading"
      class="animate-spin -ml-0.5 h-3.5 w-3.5 text-current shrink-0"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>

    <!-- Icon Left Slot or Prop -->
    <slot v-else name="icon-left">
      <Icon v-if="iconLeft" :name="iconLeft" :size="iconSize" />
    </slot>

    <!-- Button Text Content -->
    <span class="truncate">
      <slot />
    </span>

    <!-- Icon Right Slot or Prop -->
    <slot name="icon-right">
      <Icon v-if="iconRight" :name="iconRight" :size="iconSize" />
    </slot>
  </button>
</template>
