<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  currentPage: number
  pageSize: number
  totalItems: number
  pageSizeOptions?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  pageSizeOptions: () => [10, 25, 50, 100],
})

const emit = defineEmits<{
  (e: 'update:currentPage', page: number): void
  (e: 'update:pageSize', size: number): void
}>()

const totalPages = computed(() => {
  if (props.totalItems <= 0) return 1
  return Math.ceil(props.totalItems / props.pageSize)
})

const fromItem = computed(() => {
  if (props.totalItems === 0) return 0
  return (props.currentPage - 1) * props.pageSize + 1
})

const toItem = computed(() => {
  return Math.min(props.currentPage * props.pageSize, props.totalItems)
})

function changePage(page: number) {
  if (page < 1 || page > totalPages.value || page === props.currentPage) return
  emit('update:currentPage', page)
}

function onPageSizeChange(e: Event) {
  const val = Number((e.target as HTMLSelectElement).value)
  emit('update:pageSize', val)
  emit('update:currentPage', 1)
}

// Generate visible page numbers with ellipsis
const visiblePages = computed(() => {
  const total = totalPages.value
  const current = props.currentPage
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const pages: (number | string)[] = []
  if (current <= 4) {
    pages.push(1, 2, 3, 4, 5, '...', total)
  } else if (current >= total - 3) {
    pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
  } else {
    pages.push(1, '...', current - 1, current, current + 1, '...', total)
  }
  return pages
})
</script>

<template>
  <div class="bg-slate-50 px-4 py-2.5 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
    <!-- Left: Showing Records Info & Page Size Selector -->
    <div class="flex items-center space-x-3">
      <div>
        Showing
        <span class="font-bold text-slate-800 font-mono">{{ fromItem }}</span>
        to
        <span class="font-bold text-slate-800 font-mono">{{ toItem }}</span>
        of
        <span class="font-bold text-slate-900 font-mono">{{ totalItems }}</span>
        records
      </div>

      <div class="flex items-center space-x-1.5 pl-2 border-l border-slate-200">
        <label class="text-[11px] text-slate-500">Per page:</label>
        <select
          :value="pageSize"
          class="px-2 py-0.5 bg-white border border-slate-300 rounded text-xs font-semibold text-slate-700 cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500"
          @change="onPageSizeChange"
        >
          <option v-for="opt in pageSizeOptions" :key="opt" :value="opt">
            {{ opt }}
          </option>
        </select>
      </div>
    </div>

    <!-- Right: Page Controls -->
    <div class="flex items-center space-x-1">
      <!-- First Page -->
      <button
        type="button"
        :disabled="currentPage <= 1"
        class="px-2 py-1 border border-slate-300 rounded bg-white text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition text-xs font-mono"
        title="First Page"
        @click="changePage(1)"
      >
        &laquo;
      </button>

      <!-- Previous Page -->
      <button
        type="button"
        :disabled="currentPage <= 1"
        class="px-2.5 py-1 border border-slate-300 rounded bg-white text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition text-xs font-medium"
        @click="changePage(currentPage - 1)"
      >
        Previous
      </button>

      <!-- Page Numbers -->
      <div class="flex items-center space-x-1">
        <template v-for="(p, idx) in visiblePages" :key="idx">
          <span v-if="p === '...'" class="px-1.5 text-slate-400 select-none">...</span>
          <button
            v-else
            type="button"
            :class="[
              'w-7 h-7 rounded text-xs font-mono font-semibold transition cursor-pointer flex items-center justify-center',
              p === currentPage
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100'
            ]"
            @click="changePage(Number(p))"
          >
            {{ p }}
          </button>
        </template>
      </div>

      <!-- Next Page -->
      <button
        type="button"
        :disabled="currentPage >= totalPages"
        class="px-2.5 py-1 border border-slate-300 rounded bg-white text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition text-xs font-medium"
        @click="changePage(currentPage + 1)"
      >
        Next
      </button>

      <!-- Last Page -->
      <button
        type="button"
        :disabled="currentPage >= totalPages"
        class="px-2 py-1 border border-slate-300 rounded bg-white text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition text-xs font-mono"
        title="Last Page"
        @click="changePage(totalPages)"
      >
        &raquo;
      </button>
    </div>
  </div>
</template>
