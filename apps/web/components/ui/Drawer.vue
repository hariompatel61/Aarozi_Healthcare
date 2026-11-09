<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'
import Icon from './Icon.vue'
import IconButton from './IconButton.vue'

interface Props {
  modelValue: boolean
  title?: string
  subtitle?: string
  width?: 'sm' | 'md' | 'lg' | 'xl'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  width: 'md',
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'close'): void
}>()

function close() {
  emit('update:modelValue', false)
  emit('close')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.modelValue) {
    close()
  }
}

watch(() => props.modelValue, (isOpen) => {
  if (typeof document !== 'undefined') {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
})

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', handleKeydown)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('keydown', handleKeydown)
    if (typeof document !== 'undefined') {
      document.body.style.overflow = ''
    }
  }
})
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-50 flex justify-end">
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-2xs transition-opacity duration-300"
        aria-hidden="true"
        @click="close"
      />

      <!-- Slide-in Panel -->
      <div
        :class="[
          'relative w-full bg-white dark:bg-slate-900 shadow-2xl flex flex-col h-full z-10 transition-transform duration-300 border-l border-slate-200 dark:border-slate-800 text-left',
          width === 'sm' ? 'max-w-sm' : '',
          width === 'md' ? 'max-w-md' : '',
          width === 'lg' ? 'max-w-xl' : '',
          width === 'xl' ? 'max-w-2xl' : ''
        ]"
        role="dialog"
        aria-modal="true"
      >
        <!-- Drawer Header -->
        <div class="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h3 v-if="title" class="text-base font-bold text-slate-900 dark:text-slate-100">
              {{ title }}
            </h3>
            <p v-if="subtitle" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {{ subtitle }}
            </p>
          </div>
          <IconButton
            icon="x"
            label="Close panel (Esc)"
            size="sm"
            @click="close"
          />
        </div>

        <!-- Drawer Body -->
        <div class="flex-1 overflow-y-auto p-5">
          <slot />
        </div>

        <!-- Drawer Footer -->
        <div
          v-if="$slots.footer"
          class="px-5 py-3.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/70 flex items-center justify-end gap-2.5"
        >
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

