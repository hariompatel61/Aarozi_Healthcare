<script setup lang="ts">
interface Props {
  width?: string
  height?: string
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full'
  className?: string
}

withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '1rem',
  rounded: 'md',
  className: '',
})
</script>

<template>
  <div
    :class="[
      'animate-pulse bg-slate-200 dark:bg-slate-800 transition-colors',
      rounded === 'none' ? 'rounded-none' : '',
      rounded === 'sm' ? 'rounded-sm' : '',
      rounded === 'md' ? 'rounded-md' : '',
      rounded === 'lg' ? 'rounded-lg' : '',
      rounded === 'full' ? 'rounded-full' : '',
      className
    ]"
    :style="{ width, height }"
    aria-hidden="true"
  />
</template>

