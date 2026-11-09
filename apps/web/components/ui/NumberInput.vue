<script setup lang="ts">
import { computed } from 'vue'
import Icon from './Icon.vue'

interface Props {
  modelValue?: number | null
  label?: string
  placeholder?: string
  min?: number
  max?: number
  step?: number
  precision?: number
  prefix?: string
  suffix?: string
  size?: 'sm' | 'md'
  disabled?: boolean
  readonly?: boolean
  error?: string
  helperText?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 0,
  min: 0,
  max: 9999999,
  step: 1,
  precision: 0,
  size: 'md',
  disabled: false,
  readonly: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: number): void
  (e: 'change', val: number): void
}>()

function clamp(val: number): number {
  let bounded = Math.max(props.min, Math.min(props.max, val))
  if (props.precision > 0) {
    bounded = parseFloat(bounded.toFixed(props.precision))
  }
  return bounded
}

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  const num = parseFloat(target.value)
  if (!isNaN(num)) {
    const clamped = clamp(num)
    emit('update:modelValue', clamped)
    emit('change', clamped)
  }
}

function increment() {
  if (props.disabled || props.readonly) return
  const current = props.modelValue ?? props.min
  const next = clamp(current + props.step)
  emit('update:modelValue', next)
  emit('change', next)
}

function decrement() {
  if (props.disabled || props.readonly) return
  const current = props.modelValue ?? props.min
  const next = clamp(current - props.step)
  emit('update:modelValue', next)
  emit('change', next)
}
</script>

<template>
  <div class="flex flex-col space-y-1 w-full text-left">
    <label v-if="label" class="text-xs font-semibold text-slate-700 dark:text-slate-300 select-none">
      {{ label }}
    </label>

    <div class="relative flex items-center rounded-md shadow-2xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus-within:ring-2 focus-within:ring-teal-500 focus-within:border-teal-500 overflow-hidden">
      <!-- Decrement Step Button -->
      <button
        type="button"
        :disabled="disabled || readonly || (modelValue !== null && modelValue !== undefined && modelValue <= min)"
        class="px-2.5 py-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none cursor-pointer border-r border-slate-200 dark:border-slate-800 h-full flex items-center justify-center transition-colors select-none"
        aria-label="Decrement"
        @click="decrement"
      >
        <Icon name="minus" size="xs" />
      </button>

      <!-- Currency Prefix (e.g. ₹) -->
      <span v-if="prefix" class="pl-2.5 pr-1 text-slate-400 font-medium text-xs select-none">
        {{ prefix }}
      </span>

      <!-- Main Numeric Input -->
      <input
        type="number"
        :value="modelValue"
        :min="min"
        :max="max"
        :step="step"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :class="[
          'w-full font-mono tabular-nums text-slate-900 dark:text-slate-100 bg-transparent text-center focus:outline-none appearance-none',
          size === 'sm' ? 'h-7 text-xs px-2' : 'h-9 text-sm px-2'
        ]"
        @input="handleInput"
      />

      <!-- Unit Suffix (e.g. mg/dL, units) -->
      <span v-if="suffix" class="pr-2.5 pl-1 text-slate-400 font-medium text-xs select-none">
        {{ suffix }}
      </span>

      <!-- Increment Step Button -->
      <button
        type="button"
        :disabled="disabled || readonly || (modelValue !== null && modelValue !== undefined && modelValue >= max)"
        class="px-2.5 py-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none cursor-pointer border-l border-slate-200 dark:border-slate-800 h-full flex items-center justify-center transition-colors select-none"
        aria-label="Increment"
        @click="increment"
      >
        <Icon name="plus" size="xs" />
      </button>
    </div>

    <p v-if="error" class="text-xs text-red-600 font-medium mt-0.5">
      {{ error }}
    </p>
    <p v-else-if="helperText" class="text-xs text-slate-500 mt-0.5">
      {{ helperText }}
    </p>
  </div>
</template>

