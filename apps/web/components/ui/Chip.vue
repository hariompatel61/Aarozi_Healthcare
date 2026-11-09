<script setup lang="ts">
import Icon from './Icon.vue'

interface Props {
  label?: string
  active?: boolean
  removable?: boolean
  size?: 'sm' | 'md'
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  active: false,
  removable: false,
  size: 'sm',
  disabled: false,
})

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'remove'): void
}>()
</script>

<template>
  <div
    :class="[
      'inline-flex items-center gap-1.5 rounded-full border transition-all duration-150 select-none cursor-pointer',
      size === 'sm' ? 'px-2.5 py-0.5 text-[11px] font-semibold' : 'px-3 py-1 text-xs font-semibold',
      active
        ? 'bg-teal-50 text-teal-800 border-teal-300 dark:bg-teal-950 dark:text-teal-200 dark:border-teal-700 shadow-2xs'
        : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60',
      disabled ? 'opacity-50 pointer-events-none' : ''
    ]"
    @click="emit('click')"
  >
    <slot>{{ label }}</slot>

    <button
      v-if="removable"
      type="button"
      class="p-0.5 -mr-1 rounded-full text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-700"
      aria-label="Remove filter"
      @click.stop="emit('remove')"
    >
      <Icon name="x" size="xs" />
    </button>
  </div>
</template>

