<script setup lang="ts">
import { ref, computed } from 'vue'
import Icon from './Icon.vue'
import Checkbox from './Checkbox.vue'
import Skeleton from './Skeleton.vue'
import EmptyState from './EmptyState.vue'

export interface ColumnDef {
  key: string
  label: string
  sortable?: boolean
  align?: 'left' | 'center' | 'right'
  width?: string
}

interface Props {
  columns: ColumnDef[]
  data: any[]
  rowKey?: string
  loading?: boolean
  dense?: boolean
  zebra?: boolean
  selectable?: boolean
  selectedKeys?: any[]
  emptyTitle?: string
  emptyDescription?: string
}

const props = withDefaults(defineProps<Props>(), {
  rowKey: 'id',
  loading: false,
  dense: true,
  zebra: false,
  selectable: false,
  selectedKeys: () => [],
  emptyTitle: 'No records found',
  emptyDescription: 'There are no items to display in this list.',
})

const emit = defineEmits<{
  (e: 'update:selectedKeys', keys: any[]): void
  (e: 'row-click', row: any, index: number): void
  (e: 'sort', key: string, order: 'asc' | 'desc'): void
}>()

const sortKey = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const activeRowIndex = ref<number>(-1)

function handleSort(col: ColumnDef) {
  if (!col.sortable) return
  if (sortKey.value === col.key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = col.key
    sortOrder.value = 'asc'
  }
  emit('sort', sortKey.value, sortOrder.value)
}

const isAllSelected = computed(() => {
  if (!props.data.length) return false
  return props.data.every((r) => props.selectedKeys.includes(r[props.rowKey]))
})

const isIndeterminate = computed(() => {
  if (!props.data.length || isAllSelected.value) return false
  return props.data.some((r) => props.selectedKeys.includes(r[props.rowKey]))
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    emit('update:selectedKeys', [])
  } else {
    emit('update:selectedKeys', props.data.map((r) => r[props.rowKey]))
  }
}

function toggleRowSelect(row: any, e?: Event) {
  if (e) e.stopPropagation()
  const key = row[props.rowKey]
  const idx = props.selectedKeys.indexOf(key)
  const next = [...props.selectedKeys]
  if (idx >= 0) {
    next.splice(idx, 1)
  } else {
    next.push(key)
  }
  emit('update:selectedKeys', next)
}

function onRowClick(row: any, idx: number) {
  activeRowIndex.value = idx
  emit('row-click', row, idx)
}
</script>

<template>
  <div class="w-full overflow-hidden border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 shadow-2xs">
    <div class="overflow-x-auto max-h-[70vh]">
      <table class="w-full text-left border-collapse select-none">
        <!-- Sticky Table Header -->
        <thead class="sticky top-0 z-10 bg-slate-50 dark:bg-slate-800/90 backdrop-blur-xs border-b border-slate-200 dark:border-slate-800">
          <tr>
            <!-- Selection Checkbox Header -->
            <th v-if="selectable" class="w-10 px-3 py-2 text-center">
              <Checkbox
                :model-value="isAllSelected"
                :indeterminate="isIndeterminate"
                @change="toggleSelectAll"
              />
            </th>

            <!-- Data Column Headers -->
            <th
              v-for="col in columns"
              :key="col.key"
              :style="{ width: col.width }"
              :class="[
                'px-3.5 py-2 font-semibold text-xs text-slate-600 dark:text-slate-300 tracking-wider whitespace-nowrap',
                col.sortable ? 'cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors' : '',
                col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left'
              ]"
              @click="handleSort(col)"
            >
              <div
                class="inline-flex items-center gap-1.5"
                :class="col.align === 'right' ? 'flex-row-reverse' : ''"
              >
                <span>{{ col.label }}</span>
                <span v-if="col.sortable" class="text-slate-400">
                  <Icon
                    v-if="sortKey === col.key && sortOrder === 'asc'"
                    name="chevron-up"
                    size="xs"
                    className="text-teal-600"
                  />
                  <Icon
                    v-else-if="sortKey === col.key && sortOrder === 'desc'"
                    name="chevron-down"
                    size="xs"
                    className="text-teal-600"
                  />
                  <Icon
                    v-else
                    name="chevron-down"
                    size="xs"
                    className="opacity-40"
                  />
                </span>
              </div>
            </th>
          </tr>
        </thead>

        <!-- Loading Skeletons -->
        <tbody v-if="loading" class="divide-y divide-slate-100 dark:divide-slate-800">
          <tr v-for="n in 5" :key="n" :class="dense ? 'h-9' : 'h-11'">
            <td v-if="selectable" class="px-3 text-center">
              <Skeleton width="16px" height="16px" rounded="sm" />
            </td>
            <td v-for="col in columns" :key="col.key" class="px-3.5">
              <Skeleton height="14px" :width="col.width || '70%'" />
            </td>
          </tr>
        </tbody>

        <!-- Data Rows -->
        <tbody v-else-if="data.length > 0" class="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
          <tr
            v-for="(row, idx) in data"
            :key="row[rowKey] || idx"
            :class="[
              'transition-colors cursor-pointer',
              dense ? 'h-9' : 'h-11',
              zebra && idx % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-800/20' : '',
              selectedKeys.includes(row[rowKey])
                ? 'bg-teal-50/70 dark:bg-teal-950/40'
                : activeRowIndex === idx
                ? 'bg-slate-100 dark:bg-slate-800'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/60'
            ]"
            @click="onRowClick(row, idx)"
          >
            <!-- Row Checkbox -->
            <td v-if="selectable" class="w-10 px-3 text-center" @click.stop>
              <Checkbox
                :model-value="selectedKeys.includes(row[rowKey])"
                @change="toggleRowSelect(row)"
              />
            </td>

            <!-- Cells -->
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-3.5 text-slate-800 dark:text-slate-200 whitespace-nowrap',
                col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left'
              ]"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]" :index="idx">
                {{ row[col.key] !== undefined && row[col.key] !== null ? row[col.key] : '—' }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty State -->
      <div v-if="!loading && data.length === 0" class="p-6">
        <slot name="empty">
          <EmptyState
            icon="search"
            :title="emptyTitle"
            :description="emptyDescription"
          />
        </slot>
      </div>
    </div>

    <!-- Table Footer / Pagination Slot -->
    <div
      v-if="$slots.footer"
      class="border-t border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 px-4 py-2.5"
    >
      <slot name="footer" />
    </div>
  </div>
</template>
