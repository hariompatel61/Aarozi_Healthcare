<script setup lang="ts">
import { computed } from 'vue'

export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
}

interface Props {
  modelValue: string | number | null | undefined
  options: SelectOption[]
  id?: string
  name?: string
  label?: string
  placeholder?: string
  error?: string
  required?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: string | number): void
  (e: 'change', val: string | number): void
}>()

const selectId = computed(() => props.id || `select_${Math.random().toString(36).substring(2, 9)}`)

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
  emit('change', target.value)
}
</script>

<template>
  <div class="flex flex-col space-y-1 w-full text-left">
    <label
      v-if="label"
      :for="selectId"
      class="text-xs font-semibold text-slate-700 select-none"
    >
      {{ label }}
      <span v-if="required" class="text-red-500 font-bold ml-0.5">*</span>
    </label>

    <div class="relative rounded-md shadow-sm">
      <select
        :id="selectId"
        :name="name"
        :value="modelValue"
        :disabled="disabled"
        :required="required"
        :class="[
          'w-full px-3 py-2 text-sm rounded-md transition-colors border bg-white focus:outline-none focus:ring-2 focus:ring-offset-1 appearance-none pr-8',
          error
            ? 'border-red-400 text-red-900 focus:ring-red-400 focus:border-red-500'
            : 'border-slate-300 text-slate-900 focus:ring-teal-500 focus:border-teal-500',
          disabled ? 'bg-slate-100 text-slate-500 cursor-not-allowed border-slate-200' : 'cursor-pointer'
        ]"
        @change="onChange"
      >
        <option v-if="placeholder" value="" disabled :selected="!modelValue">
          {{ placeholder }}
        </option>
        <option
          v-for="opt in options"
          :key="opt.value"
          :value="opt.value"
          :disabled="opt.disabled"
        >
          {{ opt.label }}
        </option>
      </select>

      <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>

    <p v-if="error" class="text-xs text-red-600 font-medium mt-0.5">
      {{ error }}
    </p>
  </div>
</template>
