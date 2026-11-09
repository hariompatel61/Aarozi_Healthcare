<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '~/composables/useToast'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Badge, { type BadgeVariant } from '~/components/ui/Badge.vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import Kbd from '~/components/ui/Kbd.vue'
import Modal from '~/components/ui/Modal.vue'
import PaginationBar from '~/components/ui/PaginationBar.vue'

const router = useRouter()
const { success, info, warning } = useToast()

// Top Navigation Tabs
type SampleQueueTab = 'queue' | 'accessioning' | 'processing' | 'completed' | 'rejected'
const activeTab = ref<SampleQueueTab>('queue')

// Filters
const filterDate = ref(new Date().toISOString().split('T')[0])
const filterDept = ref('All')
const filterStatus = ref('All')
const searchQuery = ref('')

const departments = [
  'All',
  'Hematology',
  'Biochemistry',
  'Hormones',
  'Microbiology',
  'Serology',
  'Clinical Pathology',
]

const statuses = ['All', 'Collected', 'Received', 'Processing', 'Completed', 'Pending', 'Rejected']

interface SampleItem {
  id: number
  sample_id: string
  patient_uhid: string
  patient_name: string
  age_sex: string
  test_name: string
  department: string
  specimen_type: string
  tube_color: string
  status: 'Collected' | 'Received' | 'Processing' | 'Completed' | 'Pending' | 'Rejected'
  collected_at: string
}

const api = useApi()
const loading = ref(true)
const samples = ref<SampleItem[]>([])
const selectedSample = ref<SampleItem | null>(null)

async function fetchSamples() {
  loading.value = true
  try {
    const data: any = await api.get('/pathology/samples')
    if (Array.isArray(data)) {
      samples.value = data
      if (data.length > 0 && !selectedSample.value) {
        selectedSample.value = data[0]
      }
    }
  } catch (err) {
    console.error('Failed to load samples from database:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSamples()
})

// New Sample Modal State
const newSampleModalOpen = ref(false)
const newSampleForm = ref({
  patient_name: '',
  test_name: 'CBC (Complete Blood Count)',
  department: 'Hematology',
  specimen_type: 'EDTA Whole Blood',
})

// Filtered Samples Computation
const filteredSamples = computed(() => {
  return samples.value.filter((s) => {
    // Tab filtering
    if (activeTab.value === 'accessioning' && s.status !== 'Collected' && s.status !== 'Received') return false
    if (activeTab.value === 'processing' && s.status !== 'Processing') return false
    if (activeTab.value === 'completed' && s.status !== 'Completed') return false
    if (activeTab.value === 'rejected' && s.status !== 'Rejected') return false

    // Department filter
    if (filterDept.value !== 'All' && s.department !== filterDept.value) return false

    // Status filter
    if (filterStatus.value !== 'All' && s.status !== filterStatus.value) return false

    // Search query
    const q = searchQuery.value.trim().toLowerCase()
    if (q) {
      const matchId = s.sample_id.toLowerCase().includes(q)
      const matchUhid = s.patient_uhid.toLowerCase().includes(q)
      const matchName = s.patient_name.toLowerCase().includes(q)
      const matchTest = s.test_name.toLowerCase().includes(q)
      if (!matchId && !matchUhid && !matchName && !matchTest) return false
    }

    return true
  })
})

const { currentPage, pageSize, paginatedItems: paginatedSamples, resetPage } = usePagination(filteredSamples, 10)

watch([activeTab, filterDept, filterStatus, searchQuery], () => {
  resetPage()
})

function selectSample(sample: SampleItem) {
  selectedSample.value = sample
}

// Quick Actions
function markSampleReceived() {
  if (!selectedSample.value) return
  selectedSample.value.status = 'Received'
  success('Sample Received', `Accessioned ${selectedSample.value.sample_id} into Central Lab`)
}

function markSampleProcessing() {
  if (!selectedSample.value) return
  selectedSample.value.status = 'Processing'
  info('Sample Processing', `${selectedSample.value.sample_id} routed to analyzer bench`)
}

function markSampleCompleted() {
  if (!selectedSample.value) return
  selectedSample.value.status = 'Completed'
  success('Sample Completed', `${selectedSample.value.sample_id} testing complete. Ready for approval.`)
}

function printBarcodeLabel() {
  if (!selectedSample.value) return
  info('Print Job Queued', `Printing thermal barcode label for ${selectedSample.value.sample_id}`)
}

function resetAllFilters() {
  activeTab.value = 'queue'
  filterDept.value = 'All'
  filterStatus.value = 'All'
  searchQuery.value = ''
  fetchSamples()
  success('Filters Reset', 'Displaying all accessioned laboratory samples')
}

function handleAddSample() {
  if (!newSampleForm.value.patient_name.trim()) {
    warning('Missing Name', 'Please enter patient name')
    return
  }
  const nextNum = samples.value.length + 1
  const idStr = String(nextNum).padStart(4, '0')
  const newSmp: SampleItem = {
    id: nextNum,
    sample_id: `SMP25${idStr}`,
    patient_uhid: `PAT25${idStr}`,
    patient_name: newSampleForm.value.patient_name,
    age_sex: '30 / M',
    test_name: newSampleForm.value.test_name,
    department: newSampleForm.value.department,
    specimen_type: newSampleForm.value.specimen_type,
    tube_color: newSampleForm.value.specimen_type.includes('EDTA') ? '#8b5cf6' : '#f59e0b',
    status: 'Collected',
    collected_at: 'Just Now',
  }
  samples.value.unshift(newSmp)
  selectedSample.value = newSmp
  newSampleModalOpen.value = false
  newSampleForm.value.patient_name = ''
  success('Sample Created', `Sample ${newSmp.sample_id} created in accessioning queue.`)
}

function navigateToResultEntry() {
  if (!selectedSample.value) return
  router.push(`/pathology/results?sample_id=${selectedSample.value.sample_id}`)
}

function getStatusBadgeVariant(status: string): BadgeVariant {
  switch (status) {
    case 'Completed': return 'success'
    case 'Received': return 'info'
    case 'Processing': return 'warning'
    case 'Rejected': return 'danger'
    case 'Collected': return 'info'
    default: return 'neutral'
  }
}

// Counts for tabs
const counts = computed(() => {
  const all = samples.value.length
  const accessioning = samples.value.filter(s => s.status === 'Collected' || s.status === 'Received').length
  const processing = samples.value.filter(s => s.status === 'Processing').length
  const completed = samples.value.filter(s => s.status === 'Completed').length
  const rejected = samples.value.filter(s => s.status === 'Rejected').length
  return { all, accessioning, processing, completed, rejected }
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Page Header with Workflow Breadcrumbs & Direct CTAs -->
    <PageHeader
      title="Specimen Accessioning & Sample Tracking"
      subtitle="Barcoding, specimen validation, analyzer bench routing, and tube tracking"
    >
      <template #actions>
        <div class="flex items-center gap-2 flex-wrap">
          <Button
            variant="secondary"
            size="sm"
            :loading="loading"
            @click="fetchSamples"
          >
            <template #icon-left>
              <Icon name="refresh" size="sm" :class="loading ? 'animate-spin' : ''" />
            </template>
            <span>Refresh</span>
          </Button>

          <NuxtLink to="/pathology/results">
            <Button variant="secondary" size="sm">
              <template #icon-left>
                <Icon name="beaker" size="sm" />
              </template>
              <span>Result Workstation</span>
            </Button>
          </NuxtLink>

          <NuxtLink to="/pathology/verification">
            <Button variant="secondary" size="sm">
              <template #icon-left>
                <Icon name="shield-check" size="sm" />
              </template>
              <span>Verification Desk</span>
            </Button>
          </NuxtLink>

          <Button
            variant="primary"
            size="sm"
            @click="newSampleModalOpen = true"
          >
            <template #icon-left>
              <Icon name="plus" size="sm" />
            </template>
            <span>New Specimen</span>
            <Kbd class="ml-1 hidden sm:inline-block">F3</Kbd>
          </Button>
        </div>
      </template>
    </PageHeader>

    <!-- Workflow Stage Tabs -->
    <div class="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800 overflow-x-auto pb-0.5">
      <button
        type="button"
        :class="[
          'px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer shrink-0 flex items-center gap-2 border-b-2',
          activeTab === 'queue'
            ? 'border-teal-600 text-teal-700 dark:text-teal-400 bg-white dark:bg-slate-900 border-x border-t border-slate-200 dark:border-slate-800'
            : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-800/40'
        ]"
        @click="activeTab = 'queue'"
      >
        <span>All Samples</span>
        <span class="px-1.5 py-0.2 rounded-full font-mono text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
          {{ counts.all }}
        </span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer shrink-0 flex items-center gap-2 border-b-2',
          activeTab === 'accessioning'
            ? 'border-teal-600 text-teal-700 dark:text-teal-400 bg-white dark:bg-slate-900 border-x border-t border-slate-200 dark:border-slate-800'
            : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-800/40'
        ]"
        @click="activeTab = 'accessioning'"
      >
        <span>Accessioning Desk</span>
        <span class="px-1.5 py-0.2 rounded-full font-mono text-[11px] bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300">
          {{ counts.accessioning }}
        </span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer shrink-0 flex items-center gap-2 border-b-2',
          activeTab === 'processing'
            ? 'border-teal-600 text-teal-700 dark:text-teal-400 bg-white dark:bg-slate-900 border-x border-t border-slate-200 dark:border-slate-800'
            : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-800/40'
        ]"
        @click="activeTab = 'processing'"
      >
        <span>Processing (Analyzers)</span>
        <span class="px-1.5 py-0.2 rounded-full font-mono text-[11px] bg-teal-100 dark:bg-teal-950 text-teal-700 dark:text-teal-300">
          {{ counts.processing }}
        </span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer shrink-0 flex items-center gap-2 border-b-2',
          activeTab === 'completed'
            ? 'border-teal-600 text-teal-700 dark:text-teal-400 bg-white dark:bg-slate-900 border-x border-t border-slate-200 dark:border-slate-800'
            : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-800/40'
        ]"
        @click="activeTab = 'completed'"
      >
        <span>Completed</span>
        <span class="px-1.5 py-0.2 rounded-full font-mono text-[11px] bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
          {{ counts.completed }}
        </span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer shrink-0 flex items-center gap-2 border-b-2',
          activeTab === 'rejected'
            ? 'border-teal-600 text-teal-700 dark:text-teal-400 bg-white dark:bg-slate-900 border-x border-t border-slate-200 dark:border-slate-800'
            : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-800/40'
        ]"
        @click="activeTab = 'rejected'"
      >
        <span>Rejected Specimen</span>
        <span class="px-1.5 py-0.2 rounded-full font-mono text-[11px] bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300">
          {{ counts.rejected }}
        </span>
      </button>
    </div>

    <!-- Filter Control Bar -->
    <div class="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200/90 dark:border-slate-800 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Date Selector -->
        <div class="flex items-center gap-1.5">
          <label class="text-slate-500 dark:text-slate-400 font-medium">Date</label>
          <input
            v-model="filterDate"
            type="date"
            class="px-2.5 py-1 text-xs text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:border-teal-500"
          />
        </div>

        <!-- Department Dropdown -->
        <div class="flex items-center gap-1.5">
          <label class="text-slate-500 dark:text-slate-400 font-medium">Department</label>
          <select
            v-model="filterDept"
            class="px-2.5 py-1 text-xs text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:border-teal-500 cursor-pointer"
          >
            <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>

        <!-- Status Dropdown -->
        <div class="flex items-center gap-1.5">
          <label class="text-slate-500 dark:text-slate-400 font-medium">Status</label>
          <select
            v-model="filterStatus"
            class="px-2.5 py-1 text-xs text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:border-teal-500 cursor-pointer"
          >
            <option v-for="st in statuses" :key="st" :value="st">{{ st }}</option>
          </select>
        </div>
      </div>

      <!-- Search Input & Reset Button -->
      <div class="flex items-center gap-2">
        <div class="relative w-64">
          <span class="absolute inset-y-0 left-0 flex items-center pl-2.5 text-slate-400 pointer-events-none">
            <Icon name="search" size="xs" />
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search sample ID, barcode, patient..."
            class="w-full pl-8 pr-7 py-1 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-teal-500"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="absolute inset-y-0 right-0 flex items-center pr-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
            title="Clear search"
            @click="searchQuery = ''"
          >
            <Icon name="x" size="xs" />
          </button>
        </div>

        <Button
          variant="secondary"
          size="sm"
          title="Reset all filters"
          @click="resetAllFilters"
        >
          Reset
        </Button>
      </div>
    </div>

    <!-- Main Laboratory Samples Table -->
    <Card no-padding>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-800 text-xs">
          <thead class="bg-slate-50/80 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              <th class="w-10 px-3 py-3 text-center">#</th>
              <th class="px-4 py-3 text-left">Specimen / Barcode</th>
              <th class="px-4 py-3 text-left">Patient Details</th>
              <th class="px-4 py-3 text-left">Investigation</th>
              <th class="px-4 py-3 text-left">Department</th>
              <th class="px-4 py-3 text-left">Workflow Status</th>
              <th class="px-4 py-3 text-left">Collected At</th>
              <th class="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
            <tr v-if="loading">
              <td colspan="8" class="text-center py-8 text-slate-400 font-medium">
                <div class="flex items-center justify-center gap-2">
                  <Icon name="refresh" size="sm" class="animate-spin text-teal-600" />
                  <span>Loading samples from database...</span>
                </div>
              </td>
            </tr>

            <tr v-else-if="filteredSamples.length === 0">
              <td colspan="8" class="text-center py-8 text-slate-400 font-medium">
                <Icon name="search" size="md" class="mx-auto text-slate-300 mb-1" />
                <span>No samples match your filter criteria.</span>
              </td>
            </tr>

            <tr
              v-for="(s, idx) in paginatedSamples"
              v-else
              :key="s.sample_id"
              :class="[
                'cursor-pointer transition-colors',
                selectedSample?.sample_id === s.sample_id
                  ? 'bg-teal-50/60 dark:bg-teal-950/40 border-l-4 border-l-teal-600'
                  : 'hover:bg-slate-50/80 dark:hover:bg-slate-800/40'
              ]"
              @click="selectSample(s)"
            >
              <td class="px-3 py-3 text-center font-mono font-bold text-slate-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span
                    class="w-3 h-3 rounded-full shrink-0 ring-1 ring-slate-300 dark:ring-slate-700"
                    :style="{ backgroundColor: s.tube_color }"
                    :title="s.specimen_type"
                  />
                  <div>
                    <span class="font-mono font-bold text-teal-700 dark:text-teal-400 text-xs">
                      {{ s.sample_id }}
                    </span>
                    <p class="text-[11px] text-slate-500 font-medium truncate max-w-[140px]">
                      {{ s.specimen_type }}
                    </p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3">
                <p class="font-semibold text-slate-900 dark:text-slate-100 text-xs">
                  {{ s.patient_name }}
                </p>
                <div class="flex items-center gap-1.5 text-[11px] text-slate-500 font-mono">
                  <span>{{ s.patient_uhid }}</span>
                  <span>&bull;</span>
                  <span>{{ s.age_sex }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-slate-800 dark:text-slate-200 font-medium">
                {{ s.test_name }}
              </td>
              <td class="px-4 py-3 text-slate-500 dark:text-slate-400">
                {{ s.department }}
              </td>
              <td class="px-4 py-3">
                <Badge :variant="getStatusBadgeVariant(s.status)" size="sm" :dot="true">
                  {{ s.status }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-400 font-mono whitespace-nowrap">
                {{ s.collected_at }}
              </td>
              <td class="px-4 py-3 text-center whitespace-nowrap" @click.stop>
                <div class="flex items-center justify-center gap-1.5">
                  <NuxtLink :to="`/pathology/results?sample_id=${s.sample_id}`">
                    <Button variant="primary" size="sm">
                      <span>Workstation</span>
                    </Button>
                  </NuxtLink>
                  <NuxtLink :to="`/pathology/verification?sample_id=${s.sample_id}`">
                    <Button variant="secondary" size="sm">
                      <span>Verify</span>
                    </Button>
                  </NuxtLink>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Component -->
      <div class="p-3 border-t border-slate-100 dark:border-slate-800">
        <PaginationBar
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total-items="filteredSamples.length"
        />
      </div>
    </Card>

    <!-- Bottom Split Section: Barcode Label (Left) + Quick Workflow Actions (Right) -->
    <div v-if="selectedSample" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Left Card: Sample Barcode Label -->
      <Card
        title="Thermal Barcode Specimen Label"
        :subtitle="`Container: ${selectedSample.specimen_type}`"
      >
        <template #header-right>
          <Button
            variant="secondary"
            size="sm"
            @click="printBarcodeLabel"
          >
            <template #icon-left>
              <Icon name="printer" size="sm" />
            </template>
            <span>Print Label</span>
          </Button>
        </template>

        <div class="space-y-3">
          <!-- Authentic Barcode Container -->
          <div class="bg-white dark:bg-slate-950 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-4 flex flex-col items-center justify-center text-center">
            <svg class="w-64 h-12" viewBox="0 0 200 40">
              <rect x="10" y="0" width="3" height="40" fill="#0f172a" />
              <rect x="16" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="22" y="0" width="4" height="40" fill="#0f172a" />
              <rect x="30" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="36" y="0" width="5" height="40" fill="#0f172a" />
              <rect x="44" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="50" y="0" width="4" height="40" fill="#0f172a" />
              <rect x="58" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="64" y="0" width="6" height="40" fill="#0f172a" />
              <rect x="74" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="80" y="0" width="3" height="40" fill="#0f172a" />
              <rect x="86" y="0" width="5" height="40" fill="#0f172a" />
              <rect x="94" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="100" y="0" width="4" height="40" fill="#0f172a" />
              <rect x="108" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="114" y="0" width="5" height="40" fill="#0f172a" />
              <rect x="122" y="0" width="3" height="40" fill="#0f172a" />
              <rect x="128" y="0" width="4" height="40" fill="#0f172a" />
              <rect x="136" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="142" y="0" width="5" height="40" fill="#0f172a" />
              <rect x="150" y="0" width="3" height="40" fill="#0f172a" />
              <rect x="156" y="0" width="4" height="40" fill="#0f172a" />
              <rect x="164" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="170" y="0" width="6" height="40" fill="#0f172a" />
              <rect x="180" y="0" width="2" height="40" fill="#0f172a" />
              <rect x="186" y="0" width="4" height="40" fill="#0f172a" />
            </svg>

            <p class="font-mono text-sm font-bold text-slate-900 dark:text-slate-100 tracking-wider mt-1.5">
              *{{ selectedSample.sample_id }}*
            </p>

            <div class="mt-2 text-xs text-slate-700 dark:text-slate-300 font-medium">
              <span class="font-mono font-bold text-teal-700 dark:text-teal-400">{{ selectedSample.patient_uhid }}</span>
              <span class="mx-1.5 text-slate-300 dark:text-slate-700">|</span>
              <span>{{ selectedSample.patient_name }}</span>
              <span class="mx-1.5 text-slate-300 dark:text-slate-700">|</span>
              <span>{{ selectedSample.age_sex }}</span>
            </div>

            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {{ selectedSample.test_name }} &bull; {{ selectedSample.department }}
            </p>
          </div>
        </div>
      </Card>

      <!-- Right Card: Quick Actions & Workflow Dispatch -->
      <Card
        title="Accessioning & Workflow Bench Actions"
        :subtitle="`Active Specimen: ${selectedSample.sample_id}`"
      >
        <div class="space-y-4">
          <p class="text-xs text-slate-600 dark:text-slate-400">
            Advance the specimen container through accessioning checks, analyzer benches, and pathology sign-off.
          </p>

          <!-- Action Buttons Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <Button
              variant="secondary"
              class="flex-col py-3 h-auto text-xs"
              @click="markSampleReceived"
            >
              <template #icon-left>
                <Icon name="check" size="md" class="text-teal-600 mb-1" />
              </template>
              <span>Receive Sample</span>
            </Button>

            <Button
              variant="secondary"
              class="flex-col py-3 h-auto text-xs"
              @click="markSampleProcessing"
            >
              <template #icon-left>
                <Icon name="beaker" size="md" class="text-sky-600 mb-1" />
              </template>
              <span>Route to Bench</span>
            </Button>

            <Button
              variant="secondary"
              class="flex-col py-3 h-auto text-xs"
              @click="markSampleCompleted"
            >
              <template #icon-left>
                <Icon name="shield-check" size="md" class="text-emerald-600 mb-1" />
              </template>
              <span>Mark Complete</span>
            </Button>
          </div>

          <!-- Direct Navigation Links -->
          <div class="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
            <span class="text-slate-500">
              Workstation shortcuts:
            </span>
            <div class="flex items-center gap-3">
              <button
                type="button"
                class="text-teal-700 dark:text-teal-400 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                @click="navigateToResultEntry"
              >
                <span>Result Entry &rarr;</span>
              </button>
              <span class="text-slate-300 dark:text-slate-700">|</span>
              <NuxtLink
                :to="`/pathology/verification?sample_id=${selectedSample.sample_id}`"
                class="text-sky-700 dark:text-sky-400 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
              >
                <span>Verification Desk &rarr;</span>
              </NuxtLink>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Accession New Specimen Modal -->
    <Modal
      v-model="newSampleModalOpen"
      title="Accession New Laboratory Specimen"
      description="Record accessioning for a newly received specimen container"
    >
      <form class="space-y-4 text-xs" @submit.prevent="handleAddSample">
        <div>
          <label class="block font-medium text-slate-700 dark:text-slate-300 mb-1">
            Patient Full Name *
          </label>
          <input
            v-model="newSampleForm.patient_name"
            type="text"
            required
            placeholder="e.g. Ramesh Kumar"
            class="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-teal-500"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Investigation Profile *
            </label>
            <input
              v-model="newSampleForm.test_name"
              type="text"
              required
              class="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-teal-500"
            />
          </div>
          <div>
            <label class="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Department
            </label>
            <select
              v-model="newSampleForm.department"
              class="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-teal-500 cursor-pointer"
            >
              <option value="Hematology">Hematology</option>
              <option value="Biochemistry">Biochemistry</option>
              <option value="Hormones">Hormones</option>
              <option value="Microbiology">Microbiology</option>
              <option value="Serology">Serology</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block font-medium text-slate-700 dark:text-slate-300 mb-1">
            Specimen Container Cap / Type
          </label>
          <select
            v-model="newSampleForm.specimen_type"
            class="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-xs bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-teal-500 cursor-pointer"
          >
            <option value="EDTA Whole Blood">EDTA Whole Blood (Lavender Top)</option>
            <option value="Serum">Serum / Clot Activator (Gold/Red Top)</option>
            <option value="Fluoride Plasma">Sodium Fluoride (Grey Top)</option>
            <option value="Urine">Sterile Urine Cup (Yellow)</option>
          </select>
        </div>

        <div class="pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            @click="newSampleModalOpen = false"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="sm"
          >
            <span>Generate Barcode &amp; Accession</span>
          </Button>
        </div>
      </form>
    </Modal>
  </div>
</template>
