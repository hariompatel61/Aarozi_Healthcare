<script setup lang="ts">
import { computed } from 'vue'
import Icon from './Icon.vue'

interface Props {
  modelValue?: boolean
  label?: string
  description?: string
  disabled?: boolean
  indeterminate?: boolean
  id?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  disabled: false,
  indeterminate: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'change', val: boolean): void
}>()

const inputId = computed(() => props.id || `chk_${Math.random().toString(36).substring(2, 9)}`)

function toggle() {
  if (props.disabled) return
  const next = !props.modelValue
  emit('update:modelValue', next)
  emit('change', next)
}
</script>

<template>
  <label
    :for="inputId"
    :class="[
      'inline-flex items-start gap-2.5 select-none transition-opacity cursor-pointer group',
      disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''
    ]"
  >
    <div class="relative flex items-center justify-center mt-0.5">
      <input
        :id="inputId"
        type="checkbox"
        :checked="modelValue"
        :disabled="disabled"
        class="sr-only peer"
        @change="toggle"
      />
      <div
        :class="[
          'w-4 h-4 rounded border transition-all duration-150 flex items-center justify-center',
          'peer-focus:ring-2 peer-focus:ring-teal-500 peer-focus:ring-offset-1 dark:peer-focus:ring-offset-slate-900',
          modelValue || indeterminate
            ? 'bg-teal-600 border-teal-600 text-white'
            : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 group-hover:border-slate-400'
        ]"
      >
        <Icon v-if="indeterminate" name="minus" size="xs" className="w-2.5 h-2.5 stroke-[3]" />
        <Icon v-else-if="modelValue" name="check" size="xs" className="w-2.5 h-2.5 stroke-[3]" />
      </div>
    </div>

    <div v-if="label || $slots.default" class="text-xs">
      <span class="font-medium text-slate-800 dark:text-slate-200">
        <slot>{{ label }}</slot>
      </span>
      <p v-if="description" class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
        {{ description }}
      </p>
    </div>
  </label>
</template>

