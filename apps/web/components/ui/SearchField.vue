<script setup lang="ts">
import { ref, watch } from 'vue'
import Icon from './Icon.vue'
import Kbd from './Kbd.vue'

interface Props {
  modelValue?: string
  placeholder?: string
  shortcut?: string
  debounce?: number
  size?: 'sm' | 'md'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: 'Search...',
  shortcut: 'Ctrl+K',
  debounce: 250,
  size: 'md',
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'search', val: string): void
  (e: 'clear'): void
}>()

const localQuery = ref(props.modelValue)
let timer: ReturnType<typeof setTimeout> | null = null

watch(() => props.modelValue, (newVal) => {
  localQuery.value = newVal
})

function onInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  localQuery.value = val
  emit('update:modelValue', val)

  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    emit('search', val)
  }, props.debounce)
}

function handleClear() {
  localQuery.value = ''
  emit('update:modelValue', '')
  emit('search', '')
  emit('clear')
}
</script>

<template>
  <div class="relative flex items-center w-full">
    <Icon
      name="search"
      size="sm"
      className="absolute left-2.5 text-slate-400 pointer-events-none"
    />

    <input
      type="search"
      :value="localQuery"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="[
        'w-full pl-8 pr-16 font-sans border rounded-md shadow-2xs transition-colors bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500',
        size === 'sm' ? 'h-7 text-xs' : 'h-9 text-sm',
        disabled ? 'opacity-50 cursor-not-allowed bg-slate-100' : ''
      ]"
      @input="onInput"
    />

    <div class="absolute right-2 flex items-center space-x-1">
      <button
        v-if="localQuery && !disabled"
        type="button"
        class="p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
        aria-label="Clear search"
        @click="handleClear"
      >
        <Icon name="x" size="xs" />
      </button>

      <Kbd v-else-if="shortcut" size="xs">
        {{ shortcut }}
      </Kbd>
    </div>
  </div>
</template>

