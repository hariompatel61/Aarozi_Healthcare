import { ref, computed, watch, type Ref } from 'vue'

export function usePagination<T>(items: Ref<T[]>, defaultPageSize: number = 10) {
  const currentPage = ref(1)
  const pageSize = ref(defaultPageSize)

  const totalPages = computed(() => {
    if (!items.value || items.value.length === 0) return 1
    return Math.ceil(items.value.length / pageSize.value)
  })

  const paginatedItems = computed(() => {
    if (!items.value) return []
    const start = (currentPage.value - 1) * pageSize.value
    return items.value.slice(start, start + pageSize.value)
  })

  function resetPage() {
    currentPage.value = 1
  }

  // Auto-adjust page if list length shrinks
  watch(
    () => items.value.length,
    () => {
      if (currentPage.value > totalPages.value) {
        currentPage.value = Math.max(1, totalPages.value)
      }
    }
  )

  return {
    currentPage,
    pageSize,
    totalPages,
    paginatedItems,
    resetPage,
  }
}
