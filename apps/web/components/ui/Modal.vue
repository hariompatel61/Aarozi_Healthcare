<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'

interface Props {
  modelValue: boolean
  title?: string
  description?: string
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl'
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: 'md',
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'close'): void
}>()

function close() {
  emit('update:modelValue', false)
  emit('close')
}

function onKeydown(evt: KeyboardEvent) {
  if (evt.key === 'Escape' && props.modelValue) {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})

watch(
  () => props.modelValue,
  (open) => {
    if (typeof document !== 'undefined') {
      if (open) {
        document.body.classList.add('overflow-hidden')
      } else {
        document.body.classList.remove('overflow-hidden')
      }
    }
  }
)
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4 sm:p-6"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity"
        @click="close"
      />

      <!-- Dialog Panel -->
      <div
        :class="[
          'relative bg-white rounded-lg shadow-xl border border-slate-200 overflow-hidden w-full text-left transition-all z-10',
          maxWidth === 'sm' ? 'max-w-sm' : '',
          maxWidth === 'md' ? 'max-w-md' : '',
          maxWidth === 'lg' ? 'max-w-lg' : '',
          maxWidth === 'xl' ? 'max-w-xl' : '',
          maxWidth === '2xl' ? 'max-w-2xl' : '',
          maxWidth === '3xl' ? 'max-w-3xl' : ''
        ]"
      >
        <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 v-if="title" class="text-base font-semibold text-slate-900">
              {{ title }}
            </h3>
            <p v-if="description" class="text-xs text-slate-500 mt-0.5">
              {{ description }}
            </p>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-slate-600 rounded-md p-1 hover:bg-slate-100 transition-colors cursor-pointer"
            @click="close"
          >
            <span class="sr-only">Close</span>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-5">
          <slot />
        </div>

        <div
          v-if="$slots.footer"
          class="bg-slate-50 px-5 py-3 border-t border-slate-100 flex items-center justify-end space-x-2"
        >
          <slot name="footer" :close="close" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
