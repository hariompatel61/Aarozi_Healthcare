<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'
import IconButton from './IconButton.vue'

interface Props {
  modelValue: boolean
  title?: string
  description?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'close'): void
}>()

function close() {
  emit('update:modelValue', false)
  emit('close')
}

defineExpose({
  close,
})

function onKeydown(evt: KeyboardEvent) {
  if (evt.key === 'Escape' && props.modelValue) {
    close()
  }
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('keydown', onKeydown)
    if (typeof document !== 'undefined') {
      document.body.classList.remove('overflow-hidden')
    }
  }
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
      role="dialog"
      aria-modal="true"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-2xs transition-opacity duration-200"
        aria-hidden="true"
        @click="close"
      />

      <!-- Dialog Panel -->
      <div
        :class="[
          'relative bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden w-full text-left transition-all z-10',
          size === 'sm' || maxWidth === 'sm' ? 'max-w-sm' : '',
          size === 'md' || maxWidth === 'md' ? 'max-w-md' : '',
          size === 'lg' || maxWidth === 'lg' ? 'max-w-lg' : '',
          size === 'xl' || maxWidth === 'xl' ? 'max-w-xl' : '',
          size === '2xl' || maxWidth === '2xl' || maxWidth === '3xl' ? 'max-w-3xl' : '',
          size === 'full' ? 'max-w-[95vw] h-[90vh]' : ''
        ]"
      >
        <!-- Modal Header -->
        <div
          v-if="title || description || $slots.header"
          class="px-5 py-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between"
        >
          <slot name="header" :close="close">
            <div>
              <h3 v-if="title" class="text-base font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                {{ title }}
              </h3>
              <p v-if="description" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {{ description }}
              </p>
            </div>
          </slot>
          <IconButton
            icon="x"
            label="Close dialog (Esc)"
            size="sm"
            @click="close"
          />
        </div>

        <!-- Modal Body -->
        <div class="p-5 max-h-[75vh] overflow-y-auto">
          <slot :close="close" />
        </div>

        <!-- Modal Footer -->
        <div
          v-if="$slots.footer"
          class="px-5 py-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/70 flex items-center justify-end gap-2.5"
        >
          <slot name="footer" :close="close" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
