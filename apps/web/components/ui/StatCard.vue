<script setup lang="ts">
import Icon, { type IconName } from './Icon.vue'
import Skeleton from './Skeleton.vue'

interface Props {
  label: string
  value?: string | number
  trend?: number | string
  trendDirection?: 'up' | 'down' | 'neutral'
  trendLabel?: string
  icon?: IconName
  iconColor?: 'teal' | 'emerald' | 'amber' | 'red' | 'sky' | 'slate'
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  trendDirection: 'neutral',
  iconColor: 'teal',
  loading: false,
})
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-xl p-4 shadow-2xs text-left relative overflow-hidden">
    <div v-if="loading" class="space-y-2.5">
      <Skeleton height="14px" width="40%" />
      <Skeleton height="28px" width="60%" />
      <Skeleton height="12px" width="30%" />
    </div>

    <div v-else>
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          {{ label }}
        </span>
        <div
          v-if="icon"
          :class="[
            'w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
            iconColor === 'teal' ? 'bg-teal-50 text-teal-600 dark:bg-teal-950/60 dark:text-teal-400' : '',
            iconColor === 'emerald' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400' : '',
            iconColor === 'amber' ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400' : '',
            iconColor === 'red' ? 'bg-red-50 text-red-600 dark:bg-red-950/60 dark:text-red-400' : '',
            iconColor === 'sky' ? 'bg-sky-50 text-sky-600 dark:bg-sky-950/60 dark:text-sky-400' : '',
            iconColor === 'slate' ? 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400' : ''
          ]"
        >
          <Icon :name="icon" size="sm" />
        </div>
      </div>

      <div class="mt-2 flex items-baseline gap-2">
        <span class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight font-sans">
          {{ value }}
        </span>

        <span
          v-if="trend !== undefined"
          :class="[
            'inline-flex items-center text-xs font-semibold px-1.5 py-0.2 rounded',
            trendDirection === 'up' ? 'text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/60' : '',
            trendDirection === 'down' ? 'text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-950/60' : '',
            trendDirection === 'neutral' ? 'text-slate-600 bg-slate-100 dark:text-slate-300 dark:bg-slate-800' : ''
          ]"
        >
          {{ typeof trend === 'number' && trend > 0 ? `+${trend}%` : `${trend}%` }}
        </span>
      </div>

      <p v-if="trendLabel" class="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
        {{ trendLabel }}
      </p>
    </div>
  </div>
</template>

