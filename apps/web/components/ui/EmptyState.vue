<script setup lang="ts">
import Icon, { type IconName } from './Icon.vue'
import Button from './Button.vue'

interface Props {
  icon?: IconName
  title: string
  description?: string
  primaryActionLabel?: string
  secondaryActionLabel?: string
}

withDefaults(defineProps<Props>(), {
  icon: 'search',
})

const emit = defineEmits<{
  (e: 'primary-action'): void
  (e: 'secondary-action'): void
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-10 px-4 text-center max-w-sm mx-auto select-none">
    <div class="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 flex items-center justify-center mb-3.5 shadow-2xs">
      <slot name="icon">
        <Icon :name="icon" size="xl" />
      </slot>
    </div>

    <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200 tracking-tight">
      {{ title }}
    </h4>

    <p v-if="description" class="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
      {{ description }}
    </p>

    <div v-if="primaryActionLabel || secondaryActionLabel || $slots.actions" class="mt-4 flex items-center gap-2.5">
      <slot name="actions">
        <Button
          v-if="primaryActionLabel"
          variant="primary"
          size="sm"
          @click="emit('primary-action')"
        >
          {{ primaryActionLabel }}
        </Button>
        <Button
          v-if="secondaryActionLabel"
          variant="secondary"
          size="sm"
          @click="emit('secondary-action')"
        >
          {{ secondaryActionLabel }}
        </Button>
      </slot>
    </div>
  </div>
</template>

