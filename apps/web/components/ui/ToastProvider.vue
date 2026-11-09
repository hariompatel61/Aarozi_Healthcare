<script setup lang="ts">
import { useToast } from '~/composables/useToast'
import Toast from './Toast.vue'

const { toasts, dismiss } = useToast()
</script>

<template>
  <Teleport to="body">
    <div
      aria-live="assertive"
      class="pointer-events-none fixed inset-0 z-50 flex items-start px-4 py-6 sm:p-6 justify-end"
    >
      <div class="flex w-full flex-col items-center space-y-2 sm:items-end">
        <TransitionGroup
          enter-active-class="transform ease-out duration-250 transition"
          enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-4"
          enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <Toast
            v-for="t in toasts"
            :key="t.id"
            :toast="t"
            @dismiss="dismiss"
          />
        </TransitionGroup>
      </div>
    </div>
  </Teleport>
</template>
