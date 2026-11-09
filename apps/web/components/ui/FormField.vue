<script setup lang="ts">
import { computed } from 'vue'
import Icon from './Icon.vue'

interface Props {
  label?: string
  required?: boolean
  error?: string
  hint?: string
  id?: string
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
})

const fieldId = computed(() => props.id || `field_${Math.random().toString(36).substring(2, 9)}`)
</script>

<template>
  <div class="flex flex-col space-y-1.5 w-full text-left">
    <div v-if="label || $slots.label || $slots['label-right']" class="flex items-center justify-between">
      <label :for="fieldId" class="text-xs font-semibold text-slate-700 dark:text-slate-300 select-none">
        <slot name="label">
          {{ label }}
          <span v-if="required" class="text-red-500 font-bold ml-0.5">*</span>
        </slot>
      </label>
      <div v-if="$slots['label-right']" class="text-[11px] text-slate-400">
        <slot name="label-right" />
      </div>
    </div>

    <!-- Field Control Slot -->
    <slot :id="fieldId" :error="error" />

    <!-- Hint or Error Message -->
    <p v-if="error" class="text-xs text-red-600 dark:text-red-400 font-medium flex items-center">
      <Icon name="alert-circle" size="xs" className="mr-1 inline-block shrink-0" />
      {{ error }}
    </p>
    <p v-else-if="hint" class="text-[11px] text-slate-500 dark:text-slate-400">
      {{ hint }}
    </p>
  </div>
</template>

