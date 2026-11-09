<script setup lang="ts">
import { computed } from 'vue'
import Icon, { type IconName } from './Icon.vue'

interface Props {
  modelValue?: string | number | null
  id?: string
  name?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel'
  label?: string
  placeholder?: string
  size?: 'sm' | 'md'
  error?: string
  helperText?: string
  required?: boolean
  disabled?: boolean
  readonly?: boolean
  monospace?: boolean
  clearable?: boolean
  prefixIcon?: IconName
  suffixIcon?: IconName
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  size: 'md',
  required: false,
  disabled: false,
  readonly: false,
  monospace: false,
  clearable: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'blur', evt: FocusEvent): void
  (e: 'focus', evt: FocusEvent): void
  (e: 'clear'): void
}>()

const inputId = computed(() => props.id || `input_${Math.random().toString(36).substring(2, 9)}`)

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function handleClear() {
  emit('update:modelValue', '')
  emit('clear')
}
</script>

<template>
  <div class="flex flex-col space-y-1 w-full text-left">
    <!-- Form Label -->
    <label
      v-if="label"
      :for="inputId"
      class="text-xs font-semibold text-slate-700 dark:text-slate-300 select-none flex items-center justify-between"
    >
      <span>
        {{ label }}
        <span v-if="required" class="text-red-500 font-bold ml-0.5">*</span>
      </span>
      <slot name="label-right" />
    </label>

    <!-- Input Box Wrapper -->
    <div class="relative rounded-md shadow-2xs flex items-center">
      <!-- Prefix Slot or Icon -->
      <div v-if="$slots.prefix || prefixIcon" class="absolute left-2.5 flex items-center pointer-events-none text-slate-400">
        <slot name="prefix">
          <Icon v-if="prefixIcon" :name="prefixIcon" size="sm" />
        </slot>
      </div>

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
          'w-full font-sans transition-colors border rounded-md focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-slate-900',
          size === 'sm' ? 'h-7 text-xs px-2.5' : 'h-9 text-sm px-3',
          $slots.prefix || prefixIcon ? 'pl-8' : '',
          $slots.suffix || suffixIcon || (clearable && modelValue) ? 'pr-8' : '',
          monospace ? 'font-mono tabular-nums' : '',
          error
            ? 'border-red-400 text-red-900 dark:text-red-300 dark:border-red-600 bg-red-50/20 focus:ring-red-400 focus:border-red-500 placeholder-red-300'
            : 'border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-900 focus:ring-teal-500 focus:border-teal-500 placeholder-slate-400',
          disabled ? 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-500 cursor-not-allowed border-slate-200 dark:border-slate-800' : '',
          readonly ? 'bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300' : ''
        ]"
        @input="onInput"
        @blur="(e) => emit('blur', e)"
        @focus="(e) => emit('focus', e)"
      />

      <!-- Clear Button (when clearable and has value) -->
      <button
        v-if="clearable && modelValue && !disabled && !readonly"
        type="button"
        class="absolute right-2 p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
        aria-label="Clear input"
        @click="handleClear"
      >
        <Icon name="x" size="xs" />
      </button>

      <!-- Suffix Slot or Icon -->
      <div v-else-if="$slots.suffix || suffixIcon" class="absolute right-2.5 flex items-center pointer-events-none text-slate-400">
        <slot name="suffix">
          <Icon v-if="suffixIcon" :name="suffixIcon" size="sm" />
        </slot>
      </div>
    </div>

    <!-- Error or Helper Text -->
    <p v-if="error" class="text-xs text-red-600 dark:text-red-400 font-medium mt-0.5 flex items-center">
      <Icon name="alert-circle" size="xs" className="mr-1 inline-block shrink-0" />
      {{ error }}
    </p>
    <p v-else-if="helperText" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
      {{ helperText }}
    </p>
  </div>
</template>
