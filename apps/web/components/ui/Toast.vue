<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Icon from './Icon.vue'
import IconButton from './IconButton.vue'
import type { ToastMessage } from '~/composables/useToast'

interface Props {
  toast: ToastMessage
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'dismiss', id: string): void
}>()

const isPaused = ref(false)
const progress = ref(100)
let startTime = Date.now()
let remainingTime = props.toast.durationMs ?? 4000
let intervalId: any = null

function updateProgress() {
  if (isPaused.value || (props.toast.durationMs ?? 4000) <= 0) return
  const elapsed = Date.now() - startTime
  const pct = Math.max(0, 100 - (elapsed / (props.toast.durationMs ?? 4000)) * 100)
  progress.value = pct
  if (pct <= 0) {
    emit('dismiss', props.toast.id)
  }
}

function onMouseEnter() {
  isPaused.value = true
}

function onMouseLeave() {
  isPaused.value = false
  startTime = Date.now() - ((100 - progress.value) / 100) * (props.toast.durationMs ?? 4000)
}

onMounted(() => {
  intervalId = setInterval(updateProgress, 50)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<template>
  <div
    :class="[
      'pointer-events-auto w-full max-w-sm rounded-xl shadow-lg border p-3.5 text-left transition-all duration-200 relative overflow-hidden',
      'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800',
      toast.type === 'success' ? 'border-l-4 border-l-emerald-500' : '',
      toast.type === 'error' ? 'border-l-4 border-l-red-500' : '',
      toast.type === 'warning' ? 'border-l-4 border-l-amber-500' : '',
      toast.type === 'info' ? 'border-l-4 border-l-teal-500' : ''
    ]"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <div class="flex items-start gap-3">
      <!-- Icon -->
      <div class="mt-0.5 shrink-0">
        <Icon
          v-if="toast.type === 'success'"
          name="check"
          size="sm"
          className="text-emerald-500"
        />
        <Icon
          v-else-if="toast.type === 'error'"
          name="alert-triangle"
          size="sm"
          className="text-red-500"
        />
        <Icon
          v-else-if="toast.type === 'warning'"
          name="alert-circle"
          size="sm"
          className="text-amber-500"
        />
        <Icon
          v-else
          name="shield-check"
          size="sm"
          className="text-teal-500"
        />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <h4 class="text-xs font-bold text-slate-900 dark:text-slate-100 leading-tight">
          {{ toast.title }}
        </h4>
        <p v-if="toast.description" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-normal">
          {{ toast.description }}
        </p>
      </div>

      <!-- Close Button -->
      <IconButton
        icon="x"
        label="Dismiss notification"
        size="sm"
        @click="emit('dismiss', toast.id)"
      />
    </div>

    <!-- Progress Bar (Auto-dismiss countdown) -->
    <div
      v-if="(toast.durationMs ?? 4000) > 0"
      class="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-100 dark:bg-slate-800"
    >
      <div
        :class="[
          'h-full transition-all duration-75 ease-linear',
          toast.type === 'success' ? 'bg-emerald-500' : '',
          toast.type === 'error' ? 'bg-red-500' : '',
          toast.type === 'warning' ? 'bg-amber-500' : '',
          toast.type === 'info' ? 'bg-teal-500' : ''
        ]"
        :style="{ width: `${progress}%` }"
      />
    </div>
  </div>
</template>

