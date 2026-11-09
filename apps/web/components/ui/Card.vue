<script setup lang="ts">
interface Props {
  title?: string
  subtitle?: string
  dense?: boolean
}

withDefaults(defineProps<Props>(), {
  dense: false,
})
</script>

<template>
  <div class="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col text-left">
    <div
      v-if="title || $slots.header || $slots['header-actions']"
      :class="[
        'border-b border-slate-100 flex items-center justify-between',
        dense ? 'px-4 py-2.5' : 'px-5 py-3.5'
      ]"
    >
      <div>
        <h3 v-if="title" class="text-sm font-semibold text-slate-900 tracking-tight">
          {{ title }}
        </h3>
        <p v-if="subtitle" class="text-xs text-slate-500 mt-0.5">
          {{ subtitle }}
        </p>
        <slot name="header" />
      </div>
      <div v-if="$slots['header-actions']" class="flex items-center space-x-2">
        <slot name="header-actions" />
      </div>
    </div>

    <div :class="dense ? 'p-3' : 'p-5'">
      <slot />
    </div>

    <div
      v-if="$slots.footer"
      :class="[
        'bg-slate-50 border-t border-slate-100 flex items-center justify-between',
        dense ? 'px-4 py-2 text-xs' : 'px-5 py-3 text-sm'
      ]"
    >
      <slot name="footer" />
    </div>
  </div>
</template>
