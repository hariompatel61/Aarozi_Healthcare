<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: string | number | null | undefined
  id?: string
  name?: string
  type?: string
  label?: string
  placeholder?: string
  error?: string
  helperText?: string
  required?: boolean
  disabled?: boolean
  readonly?: boolean
  monospace?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  required: false,
  disabled: false,
  readonly: false,
  monospace: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: string | number): void
  (e: 'blur', evt: FocusEvent): void
  (e: 'focus', evt: FocusEvent): void
}>()

const inputId = computed(() => props.id || `input_${Math.random().toString(36).substring(2, 9)}`)

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="flex flex-col space-y-1 w-full text-left">
    <label
      v-if="label"
      :for="inputId"
      class="text-xs font-semibold text-slate-700 select-none flex items-center justify-between"
    >
      <span>
        {{ label }}
        <span v-if="required" class="text-red-500 font-bold ml-0.5">*</span>
      </span>
      <slot name="label-right" />
    </label>

    <div class="relative rounded-md shadow-sm">
      <input
        :id="inputId"
        :name="name"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :class="[
          'w-full px-3 py-2 text-sm rounded-md transition-colors border bg-white focus:outline-none focus:ring-2 focus:ring-offset-1',
          monospace ? 'font-mono tabular-nums' : '',
          error
            ? 'border-red-400 text-red-900 focus:ring-red-400 focus:border-red-500 placeholder-red-300'
            : 'border-slate-300 text-slate-900 focus:ring-teal-500 focus:border-teal-500 placeholder-slate-400',
          disabled ? 'bg-slate-100 text-slate-500 cursor-not-allowed border-slate-200' : '',
          readonly ? 'bg-slate-50 text-slate-700' : ''
        ]"
        @input="onInput"
        @blur="(e) => emit('blur', e)"
        @focus="(e) => emit('focus', e)"
      />
    </div>

    <p v-if="error" class="text-xs text-red-600 font-medium mt-0.5 flex items-center">
      <svg class="h-3 w-3 mr-1 inline-block shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path
          fill-rule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clip-rule="evenodd"
        />
      </svg>
      {{ error }}
    </p>
    <p v-else-if="helperText" class="text-xs text-slate-500 mt-0.5">
      {{ helperText }}
    </p>
  </div>
</template>
