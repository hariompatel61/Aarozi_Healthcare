<script setup lang="ts">
interface Props {
  size?: 'xs' | 'sm' | 'md'
}

withDefaults(defineProps<Props>(), {
  size: 'xs',
})
</script>

<template>
  <kbd
    :class="[
      'inline-flex items-center justify-center font-mono font-medium rounded border select-none transition-colors',
      'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700 shadow-2xs',
      size === 'xs' ? 'px-1.5 py-0.5 text-[11px] min-w-[1.25rem] leading-none' : '',
      size === 'sm' ? 'px-2 py-0.5 text-xs min-w-[1.5rem]' : '',
      size === 'md' ? 'px-2.5 py-1 text-sm min-w-[1.75rem]' : ''
    ]"
  >
    <slot />
  </kbd>
</template>

