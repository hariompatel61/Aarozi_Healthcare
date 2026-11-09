<script setup lang="ts">
import Icon from './Icon.vue'
import Button from './Button.vue'
import SearchField from './SearchField.vue'

interface Props {
  searchQuery?: string
  searchPlaceholder?: string
  hasActiveFilters?: boolean
}

withDefaults(defineProps<Props>(), {
  searchQuery: '',
  searchPlaceholder: 'Search...',
  hasActiveFilters: false,
})

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'search', val: string): void
  (e: 'reset'): void
}>()
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-2.5 sm:p-3 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-2.5">
    <!-- Left: Search Box -->
    <div class="w-full md:w-72 lg:w-80">
      <SearchField
        :model-value="searchQuery"
        :placeholder="searchPlaceholder"
        size="sm"
        @update:model-value="(val) => emit('update:searchQuery', val)"
        @search="(val) => emit('search', val)"
        @clear="emit('reset')"
      />
    </div>

    <!-- Center/Right: Quick Filter Pills & Custom Filters -->
    <div class="flex flex-wrap items-center gap-2 overflow-x-auto py-0.5">
      <slot />

      <!-- Reset Filters Button -->
      <Button
        v-if="hasActiveFilters"
        variant="ghost"
        size="sm"
        @click="emit('reset')"
      >
        <template #icon-left>
          <Icon name="x" size="xs" />
        </template>
        Reset
      </Button>

      <slot name="actions" />
    </div>
  </div>
</template>

