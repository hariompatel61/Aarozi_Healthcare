<script setup lang="ts">
import { useToast } from '~/composables/useToast'

const { toasts, dismiss } = useToast()
</script>

<template>
  <Teleport to="body">
    <div
      aria-live="assertive"
      class="pointer-events-none fixed inset-0 z-50 flex items-start px-4 py-6 sm:p-6"
    >
      <div class="flex w-full flex-col items-center space-y-3 sm:items-end">
        <TransitionGroup
          enter-active-class="transform ease-out duration-300 transition"
          enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
          enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
          leave-active-class="transition ease-in duration-100"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-for="t in toasts"
            :key="t.id"
            :class="[
              'pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg shadow-lg border p-4 text-left transition-all',
              t.type === 'success' ? 'bg-white border-emerald-300 text-slate-900' : '',
              t.type === 'error' ? 'bg-white border-red-300 text-slate-900' : '',
              t.type === 'warning' ? 'bg-white border-amber-300 text-slate-900' : '',
              t.type === 'info' ? 'bg-white border-blue-300 text-slate-900' : ''
            ]"
          >
            <div class="flex items-start">
              <!-- Icon -->
              <div class="shrink-0 mt-0.5">
                <svg
                  v-if="t.type === 'success'"
                  class="h-5 w-5 text-emerald-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <svg
                  v-else-if="t.type === 'error'"
                  class="h-5 w-5 text-red-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
                <svg
                  v-else-if="t.type === 'warning'"
                  class="h-5 w-5 text-amber-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <svg
                  v-else
                  class="h-5 w-5 text-blue-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <!-- Message Details -->
              <div class="ml-3 w-0 flex-1">
                <p class="text-sm font-semibold text-slate-900">
                  {{ t.title }}
                </p>
                <p v-if="t.description" class="mt-0.5 text-xs text-slate-500">
                  {{ t.description }}
                </p>
              </div>

              <!-- Close Button -->
              <div class="ml-4 flex shrink-0">
                <button
                  type="button"
                  class="inline-flex rounded-md text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
                  @click="dismiss(t.id)"
                >
                  <span class="sr-only">Close</span>
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>
  </Teleport>
</template>
