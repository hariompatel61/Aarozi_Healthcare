<script setup lang="ts">
export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  align?: 'left' | 'center' | 'right'
  width?: string
  monospace?: boolean
}

interface Props {
  columns: TableColumn[]
  items: Array<Record<string, any>>
  loading?: boolean
  emptyText?: string
  totalItems?: number
  pageSize?: number
  currentPage?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  emptyText: 'No records found',
  totalItems: 0,
  pageSize: 20,
  currentPage: 1,
})

const emit = defineEmits<{
  (e: 'update:currentPage', page: number): void
  (e: 'row-click', item: Record<string, any>): void
  (e: 'sort', key: string): void
}>()
</script>

<template>
  <div class="w-full bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col text-left">
    <div class="overflow-x-auto w-full">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 sticky top-0 z-10">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              scope="col"
              :style="col.width ? { width: col.width } : undefined"
              :class="[
                'px-3 py-2.5 text-xs font-semibold text-slate-600 uppercase tracking-wider select-none',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
                col.sortable ? 'cursor-pointer hover:bg-slate-100' : ''
              ]"
              @click="col.sortable ? emit('sort', col.key) : undefined"
            >
              <div
                class="inline-flex items-center space-x-1"
                :class="col.align === 'right' ? 'justify-end' : col.align === 'center' ? 'justify-center' : 'justify-start'"
              >
                <span>{{ col.label }}</span>
                <span v-if="col.sortable" class="text-slate-400 text-xs">↕</span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 bg-white">
          <tr v-if="loading">
            <td :colspan="columns.length" class="py-8 text-center text-slate-500">
              <div class="inline-flex items-center space-x-2 text-teal-600">
                <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span class="text-xs font-medium text-slate-600">Loading clinical records...</span>
              </div>
            </td>
          </tr>
          <tr v-else-if="items.length === 0">
            <td :colspan="columns.length" class="py-8 text-center text-slate-400 text-xs italic">
              {{ emptyText }}
            </td>
          </tr>
          <tr
            v-for="(item, idx) in items"
            v-else
            :key="item.id || idx"
            class="hover:bg-teal-50/40 cursor-pointer transition-colors"
            @click="emit('row-click', item)"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-3 py-2.5 whitespace-nowrap text-slate-700',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
                col.monospace ? 'font-mono tabular-nums text-xs' : ''
              ]"
            >
              <slot :name="`cell(${col.key})`" :item="item" :value="item[col.key]">
                {{ item[col.key] !== null && item[col.key] !== undefined ? item[col.key] : '—' }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Footer -->
    <div
      v-if="totalItems > pageSize"
      class="bg-slate-50 px-4 py-2.5 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500"
    >
      <div>
        Showing
        <span class="font-semibold text-slate-700 font-mono">{{ (currentPage - 1) * pageSize + 1 }}</span>
        to
        <span class="font-semibold text-slate-700 font-mono">
          {{ Math.min(currentPage * pageSize, totalItems) }}
        </span>
        of
        <span class="font-semibold text-slate-700 font-mono">{{ totalItems }}</span>
        entries
      </div>

      <div class="flex items-center space-x-1">
        <button
          type="button"
          :disabled="currentPage <= 1"
          class="px-2.5 py-1 border border-slate-300 rounded bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          @click="emit('update:currentPage', currentPage - 1)"
        >
          Previous
        </button>
        <button
          type="button"
          :disabled="currentPage * pageSize >= totalItems"
          class="px-2.5 py-1 border border-slate-300 rounded bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          @click="emit('update:currentPage', currentPage + 1)"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>
