<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue?: boolean
  label?: string
  description?: string
  disabled?: boolean
  size?: 'sm' | 'md'
  id?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  disabled: false,
  size: 'md',
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'change', val: boolean): void
}>()

const inputId = computed(() => props.id || `switch_${Math.random().toString(36).substring(2, 9)}`)

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
      'inline-flex items-center gap-3 select-none transition-opacity cursor-pointer group',
      disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''
    ]"
  >
    <div class="relative flex items-center">
      <input
        :id="inputId"
        type="checkbox"
        role="switch"
        :checked="modelValue"
        :aria-checked="modelValue"
        :disabled="disabled"
        class="sr-only peer"
        @change="toggle"
      />
      <!-- Track -->
      <div
        :class="[
          'rounded-full transition-colors duration-200 border',
          'peer-focus:ring-2 peer-focus:ring-teal-500 peer-focus:ring-offset-1 dark:peer-focus:ring-offset-slate-900',
          size === 'sm' ? 'w-8 h-4.5 p-0.5' : 'w-10 h-6 p-0.5',
          modelValue
            ? 'bg-teal-600 border-teal-600'
            : 'bg-slate-200 dark:bg-slate-700 border-slate-300 dark:border-slate-600'
        ]"
      >
        <!-- Knob -->
        <div
          :class="[
            'bg-white rounded-full shadow-xs transform transition-transform duration-200',
            size === 'sm' ? 'w-3.5 h-3.5' : 'w-5 h-5',
            modelValue
              ? size === 'sm' ? 'translate-x-3.5' : 'translate-x-4'
              : 'translate-x-0'
          ]"
        />
      </div>
    </div>

    <div v-if="label || $slots.default" class="text-xs">
      <span class="font-medium text-slate-800 dark:text-slate-200">
        <slot>{{ label }}</slot>
      </span>
      <p v-if="description" class="text-[11px] text-slate-500 dark:text-slate-400">
        {{ description }}
      </p>
    </div>
  </label>
</template>

