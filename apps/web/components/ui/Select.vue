<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import Icon from './Icon.vue'

export interface SelectOption {
  label: string
  value: any
  description?: string
  badge?: string
}

interface Props {
  modelValue?: any
  options: (SelectOption | string)[]
  label?: string
  placeholder?: string
  size?: 'sm' | 'md'
  searchable?: boolean
  clearable?: boolean
  disabled?: boolean
  error?: string
  helperText?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Select an option...',
  size: 'md',
  searchable: true,
  clearable: false,
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: any): void
  (e: 'change', val: any): void
}>()

const isOpen = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(-1)
const containerRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)

// Normalize options to SelectOption[]
const normalizedOptions = computed<SelectOption[]>(() => {
  return props.options.map((opt) => {
    if (typeof opt === 'string') {
      return { label: opt, value: opt }
    }
    return opt
  })
})

const filteredOptions = computed(() => {
  if (!props.searchable || !searchQuery.value.trim()) {
    return normalizedOptions.value
  }
  const q = searchQuery.value.toLowerCase().trim()
  return normalizedOptions.value.filter((opt) =>
    opt.label.toLowerCase().includes(q) || (opt.description && opt.description.toLowerCase().includes(q))
  )
})

const selectedOption = computed(() => {
  return normalizedOptions.value.find((opt) => opt.value === props.modelValue)
})

function toggleDropdown() {
  if (props.disabled) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    searchQuery.value = ''
    highlightedIndex.value = filteredOptions.value.findIndex((o) => o.value === props.modelValue)
    setTimeout(() => searchInputRef.value?.focus(), 50)
  }
}

function selectOption(option: SelectOption) {
  emit('update:modelValue', option.value)
  emit('change', option.value)
  isOpen.value = false
  searchQuery.value = ''
}

function clearSelection(e: MouseEvent) {
  e.stopPropagation()
  emit('update:modelValue', null)
  emit('change', null)
}

function onKeyDown(e: KeyboardEvent) {
  if (!isOpen.value) {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
      e.preventDefault()
      toggleDropdown()
    }
    return
  }

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      if (highlightedIndex.value < filteredOptions.value.length - 1) {
        highlightedIndex.value++
      } else {
        highlightedIndex.value = 0
      }
      break
    case 'ArrowUp':
      e.preventDefault()
      if (highlightedIndex.value > 0) {
        highlightedIndex.value--
      } else {
        highlightedIndex.value = filteredOptions.value.length - 1
      }
      break
    case 'Enter':
      e.preventDefault()
      if (highlightedIndex.value >= 0 && highlightedIndex.value < filteredOptions.value.length) {
        const opt = filteredOptions.value[highlightedIndex.value]
        if (opt) {
          selectOption(opt)
        }
      }
      break
    case 'Escape':
      e.preventDefault()
      isOpen.value = false
      break
  }
}

function handleClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  if (typeof document !== 'undefined') {
    document.addEventListener('click', handleClickOutside)
  }
})

onUnmounted(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('click', handleClickOutside)
  }
})
</script>

<template>
  <div ref="containerRef" class="relative flex flex-col space-y-1 w-full text-left" @keydown="onKeyDown">
    <label v-if="label" class="text-xs font-semibold text-slate-700 dark:text-slate-300 select-none">
      {{ label }}
    </label>

    <!-- Trigger Button -->
    <button
      type="button"
      :disabled="disabled"
      class="w-full flex items-center justify-between font-sans border rounded-md shadow-2xs transition-all text-left bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-1 dark:focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
      :class="[
        size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-9 px-3 text-sm',
        error ? 'border-red-400 focus:ring-red-400' : ''
      ]"
      @click="toggleDropdown"
    >
      <span class="truncate" :class="!selectedOption ? 'text-slate-400' : ''">
        {{ selectedOption ? selectedOption.label : placeholder }}
      </span>

      <div class="flex items-center space-x-1 ml-2 shrink-0">
        <button
          v-if="clearable && selectedOption && !disabled"
          type="button"
          class="p-0.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100"
          aria-label="Clear selection"
          @click="clearSelection"
        >
          <Icon name="x" size="xs" />
        </button>
        <Icon name="chevron-down" size="xs" :className="isOpen ? 'rotate-180 transition-transform' : 'transition-transform'" />
      </div>
    </button>

    <!-- Dropdown Menu -->
    <div
      v-if="isOpen"
      class="absolute left-0 right-0 z-50 mt-1 top-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-lg overflow-hidden py-1"
    >
      <!-- Search Input in Dropdown -->
      <div v-if="searchable" class="px-2 pb-1 pt-1 border-b border-slate-100 dark:border-slate-800">
        <div class="relative flex items-center">
          <Icon name="search" size="xs" className="absolute left-2 text-slate-400" />
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            class="w-full pl-7 pr-2 py-1 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-teal-500"
            placeholder="Type to filter..."
          />
        </div>
      </div>

      <!-- Option List -->
      <div class="max-h-60 overflow-y-auto py-1">
        <div
          v-for="(opt, idx) in filteredOptions"
          :key="String(opt.value)"
          :class="[
            'px-3 py-2 text-xs flex items-center justify-between cursor-pointer select-none transition-colors',
            highlightedIndex === idx || opt.value === modelValue
              ? 'bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-200 font-medium'
              : 'text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800'
          ]"
          @click="selectOption(opt)"
          @mouseenter="highlightedIndex = idx"
        >
          <div>
            <div class="font-medium">{{ opt.label }}</div>
            <div v-if="opt.description" class="text-[11px] text-slate-400">{{ opt.description }}</div>
          </div>
          <div class="flex items-center space-x-1.5">
            <span v-if="opt.badge" class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {{ opt.badge }}
            </span>
            <Icon v-if="opt.value === modelValue" name="check" size="xs" className="text-teal-600 dark:text-teal-400" />
          </div>
        </div>

        <!-- Empty Results State -->
        <div v-if="filteredOptions.length === 0" class="px-3 py-4 text-center text-xs text-slate-400">
          No matching options found
        </div>
      </div>
    </div>

    <!-- Error or Helper Text -->
    <p v-if="error" class="text-xs text-red-600 font-medium mt-0.5">
      {{ error }}
    </p>
    <p v-else-if="helperText" class="text-xs text-slate-500 mt-0.5">
      {{ helperText }}
    </p>
  </div>
</template>
