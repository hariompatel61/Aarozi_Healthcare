<script setup lang="ts">
import Icon, { type IconName } from '~/components/ui/Icon.vue'
import Badge, { type BadgeVariant } from '~/components/ui/Badge.vue'

interface Props {
  title: string
  subtitle?: string
  icon?: IconName
  badge?: string
  badgeVariant?: BadgeVariant
  compact?: boolean
}

withDefaults(defineProps<Props>(), {
  subtitle: undefined,
  icon: undefined,
  badge: undefined,
  badgeVariant: 'neutral',
  compact: false,
})
</script>

<template>
  <header
    :class="[
      'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 mb-4 border-b border-slate-200 dark:border-slate-800',
      compact ? 'pb-2.5 mb-2.5' : 'pb-4 mb-4'
    ]"
  >
    <!-- Left: Title, Subtitle, Icon, Badge -->
    <div class="flex items-start gap-3 min-w-0">
      <div
        v-if="icon"
        class="w-10 h-10 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0 mt-0.5 border border-teal-100 dark:border-teal-900"
      >
        <Icon :name="icon" size="md" />
      </div>

      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <h1 class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-white truncate">
            {{ title }}
          </h1>
          <Badge v-if="badge" :variant="badgeVariant" size="sm">
            {{ badge }}
          </Badge>
          <slot name="title-extra" />
        </div>

        <p v-if="subtitle" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 max-w-2xl">
          {{ subtitle }}
        </p>

        <div v-if="$slots.meta" class="flex items-center gap-2 mt-2 flex-wrap text-xs text-slate-500">
          <slot name="meta" />
        </div>
      </div>
    </div>

    <!-- Right: Actions Slot -->
    <div v-if="$slots.actions || $slots.default" class="flex items-center gap-2 shrink-0 flex-wrap">
      <slot name="actions">
        <slot />
      </slot>
    </div>
  </header>
</template>

