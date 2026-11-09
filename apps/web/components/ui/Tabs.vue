<script setup lang="ts">
import { computed } from 'vue'

export interface TabItem {
  id: string
  label: string
  count?: number | string
  icon?: string
  disabled?: boolean
}

interface Props {
  modelValue: string
  tabs: (TabItem | string)[]
  variant?: 'underline' | 'pill'
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'underline',
  size: 'md',
})

const emit = defineEmits<{
  (e: 'update:modelValue', id: string): void
  (e: 'change', id: string): void
}>()

const normalizedTabs = computed<TabItem[]>(() => {
  return props.tabs.map((t) => {
    if (typeof t === 'string') {
      return { id: t, label: t }
    }
    return t
  })
})

function selectTab(id: string) {
  emit('update:modelValue', id)
  emit('change', id)
}
</script>

<template>
  <div
    role="tablist"
    :class="[
      'flex items-center select-none overflow-x-auto no-scrollbar',
      variant === 'underline'
        ? 'border-b border-slate-200 dark:border-slate-800 space-x-6'
        : 'p-1 bg-slate-100 dark:bg-slate-800 rounded-lg space-x-1 border border-slate-200 dark:border-slate-700/60'
    ]"
  >
    <button
      v-for="tab in normalizedTabs"
      :key="tab.id"
      type="button"
      role="tab"
      :aria-selected="modelValue === tab.id"
      :disabled="tab.disabled"
      :class="[
        'font-semibold inline-flex items-center gap-2 whitespace-nowrap transition-all duration-150 focus:outline-none cursor-pointer',
        size === 'sm' ? 'text-xs' : 'text-sm',
        variant === 'underline'
          ? [
              'py-2.5 border-b-2 -mb-px',
              modelValue === tab.id
                ? 'border-teal-600 text-teal-700 dark:border-teal-400 dark:text-teal-300'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:border-slate-300'
            ]
          : [
              'px-3 py-1.5 rounded-md',
              modelValue === tab.id
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
            ],
        tab.disabled ? 'opacity-40 pointer-events-none' : ''
      ]"
      @click="selectTab(tab.id)"
    >
      <span>{{ tab.label }}</span>
      <span
        v-if="tab.count !== undefined"
        :class="[
          'px-1.5 py-0.2 rounded-full text-[10px] font-bold',
          modelValue === tab.id
            ? 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200'
            : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
        ]"
      >
        {{ tab.count }}
      </span>
    </button>
  </div>
</template>

