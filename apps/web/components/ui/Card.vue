<script setup lang="ts">
interface Props {
  title?: string
  subtitle?: string
  hoverable?: boolean
  dense?: boolean
  noPadding?: boolean
}

withDefaults(defineProps<Props>(), {
  hoverable: false,
  dense: false,
  noPadding: false,
})
</script>

<template>
  <div
    :class="[
      'bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl shadow-2xs transition-all duration-150 overflow-hidden text-left',
      hoverable ? 'hover:shadow-sm hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer' : ''
    ]"
  >
    <!-- Card Header -->
    <div
      v-if="title || subtitle || $slots.header || $slots['header-right']"
      :class="[
        'border-b border-slate-100 dark:border-slate-800 flex items-center justify-between',
        dense ? 'px-4 py-2.5' : 'px-5 py-3.5'
      ]"
    >
      <slot name="header">
        <div>
          <h3 v-if="title" class="text-sm font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            {{ title }}
          </h3>
          <p v-if="subtitle" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {{ subtitle }}
          </p>
        </div>
      </slot>
      <div v-if="$slots['header-right']" class="shrink-0 ml-4">
        <slot name="header-right" />
      </div>
    </div>

    <!-- Card Body -->
    <div
      :class="[
        noPadding ? 'p-0' : dense ? 'p-4' : 'p-5'
      ]"
    >
      <slot />
    </div>

    <!-- Card Footer -->
    <div
      v-if="$slots.footer"
      :class="[
        'border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50',
        dense ? 'px-4 py-2' : 'px-5 py-3'
      ]"
    >
      <slot name="footer" />
    </div>
  </div>
</template>
