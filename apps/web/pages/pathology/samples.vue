<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '~/composables/useToast'
import Modal from '~/components/ui/Modal.vue'

const router = useRouter()
const { success, info, warning } = useToast()

// Top Navigation Tabs matching Screen 3
type SampleQueueTab = 'queue' | 'accessioning' | 'processing' | 'completed' | 'rejected'
const activeTab = ref<SampleQueueTab>('queue')

// Filters matching Screen 3
const filterDate = ref('2026-10-13')
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
      if (data.length > 0) {
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
  test_name: 'CBC',
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
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Unified Diagnostic Workflow Navigation Banner -->
    <div class="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-lg p-3 text-white shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center space-x-2">
        <span class="px-2 py-0.5 rounded bg-blue-700/80 text-[10px] font-mono font-bold uppercase tracking-wider text-blue-100">
          LIS Operations
        </span>
        <span class="font-bold text-sm">Pathology Laboratory Workstation</span>
      </div>

      <div class="flex items-center space-x-2 flex-wrap">
        <NuxtLink
          to="/pathology/results"
          class="px-3 py-1.5 rounded-md font-semibold text-xs bg-white/10 hover:bg-white/20 text-white transition flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Result Entry</span>
        </NuxtLink>

        <NuxtLink
          to="/pathology/samples"
          class="px-3 py-1.5 rounded-md font-bold text-xs bg-white text-blue-900 shadow-2xs flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Sample Tracking</span>
        </NuxtLink>

        <NuxtLink
          to="/pathology/verification"
          class="px-3 py-1.5 rounded-md font-medium text-xs bg-white/10 hover:bg-white/20 text-white transition flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Verification</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Top Header Banner matching Screen 3 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <span>Sample Tracking &mdash; Lab Workflow</span>
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Track samples from collection to result with barcode and status
        </p>
      </div>

      <!-- Quick Action Shortcuts -->
      <div class="flex items-center space-x-2 text-xs">
        <NuxtLink
          to="/pathology/results"
          class="btn-secondary"
          title="Open diagnostic result workstation"
        >
          <span>Result Workstation</span>
        </NuxtLink>
        <button
          type="button"
          class="btn-primary"
          @click="newSampleModalOpen = true"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>New Sample</span>
        </button>
      </div>
    </div>

    <!-- Top Workflow Tabs matching Screen 3 (Sample Queue, Accessioning, Processing, Completed, Rejected) -->
    <div class="flex items-center space-x-1 border-b border-slate-200 overflow-x-auto">
      <button
        type="button"
        :class="[
          'px-4 py-2 text-xs font-semibold rounded-t-md transition-colors cursor-pointer shrink-0',
          activeTab === 'queue'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeTab = 'queue'"
      >
        Sample Queue
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 text-xs font-semibold rounded-t-md transition-colors cursor-pointer shrink-0',
          activeTab === 'accessioning'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeTab = 'accessioning'"
      >
        Accessioning
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 text-xs font-semibold rounded-t-md transition-colors cursor-pointer shrink-0',
          activeTab === 'processing'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeTab = 'processing'"
      >
        Processing
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 text-xs font-semibold rounded-t-md transition-colors cursor-pointer shrink-0',
          activeTab === 'completed'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeTab = 'completed'"
      >
        Completed
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 text-xs font-semibold rounded-t-md transition-colors cursor-pointer shrink-0',
          activeTab === 'rejected'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeTab = 'rejected'"
      >
        Rejected
      </button>
    </div>

    <!-- Filter Control Bar matching Screen 3 -->
    <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Date Selector -->
        <div class="flex items-center space-x-1.5">
          <label class="text-slate-500 font-medium">Date</label>
          <input
            v-model="filterDate"
            type="date"
            class="input-faang px-2.5 py-1 text-xs text-slate-800"
          />
        </div>

        <!-- Department Dropdown -->
        <div class="flex items-center space-x-1.5">
          <label class="text-slate-500 font-medium">Department</label>
          <select
            v-model="filterDept"
            class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
          >
            <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>

        <!-- Status Dropdown -->
        <div class="flex items-center space-x-1.5">
          <label class="text-slate-500 font-medium">Status</label>
          <select
            v-model="filterStatus"
            class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
          >
            <option v-for="st in statuses" :key="st" :value="st">{{ st }}</option>
          </select>
        </div>
      </div>

      <!-- Search Input & Reset Button -->
      <div class="flex items-center space-x-2">
        <div class="relative w-64">
          <span class="absolute inset-y-0 left-0 flex items-center pl-2.5 text-slate-400 pointer-events-none">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search by sample ID, barcode, patient..."
            class="input-faang w-full pl-8 pr-7 py-1 text-xs"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="absolute inset-y-0 right-0 flex items-center pr-2 text-slate-400 hover:text-slate-600 cursor-pointer"
            title="Clear search"
            @click="searchQuery = ''"
          >
            <span class="text-sm leading-none">&times;</span>
          </button>
        </div>
        <button
          type="button"
          class="btn-secondary"
          title="Reset all filters"
          @click="resetAllFilters"
        >
          Reset
        </button>
      </div>
    </div>

    <!-- Main Laboratory Samples Table matching Screen 3 -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="w-10 px-3 py-2.5 text-center">#</th>
              <th class="px-4 py-2.5 text-left">Sample ID</th>
              <th class="px-4 py-2.5 text-left">Patient Name</th>
              <th class="px-4 py-2.5 text-left">Test / Package</th>
              <th class="px-4 py-2.5 text-left">Department</th>
              <th class="px-4 py-2.5 text-left">Status</th>
              <th class="px-4 py-2.5 text-left">Collected At</th>
              <th class="px-4 py-2.5 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="8" class="text-center py-8 text-slate-400 font-medium">
                Loading samples from database...
              </td>
            </tr>
            <tr v-else-if="filteredSamples.length === 0">
              <td colspan="8" class="text-center py-8 text-slate-400 font-medium">
                No samples matching your filter criteria
              </td>
            </tr>
            <tr
              v-for="(s, idx) in paginatedSamples"
              v-else
              :key="s.sample_id"
              :class="[
                'cursor-pointer transition-colors',
                selectedSample?.sample_id === s.sample_id
                  ? 'bg-blue-50/70 border-l-4 border-l-blue-600'
                  : 'hover:bg-slate-50'
              ]"
              @click="selectSample(s)"
            >
              <td class="px-3 py-2.5 text-center font-mono font-bold text-slate-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>
              <td class="px-4 py-2.5 font-mono font-semibold text-blue-700">
                <span class="flex items-center space-x-1.5">
                  <span
                    class="w-2 h-2 rounded-full inline-block shrink-0"
                    :style="{ backgroundColor: s.tube_color }"
                    title="Specimen Container Indicator"
                  />
                  <span>{{ s.sample_id }}</span>
                </span>
              </td>
              <td class="px-4 py-2.5 font-medium text-slate-900">
                {{ s.patient_name }}
              </td>
              <td class="px-4 py-2.5 text-slate-700 font-medium">
                {{ s.test_name }}
              </td>
              <td class="px-4 py-2.5 text-slate-500">
                {{ s.department }}
              </td>
              <td class="px-4 py-2.5">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border',
                    s.status === 'Collected' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : '',
                    s.status === 'Received' ? 'bg-teal-50 text-teal-700 border-teal-200' : '',
                    s.status === 'Processing' ? 'bg-blue-50 text-blue-700 border-blue-200' : '',
                    s.status === 'Completed' ? 'bg-green-50 text-green-700 border-green-200' : '',
                    s.status === 'Pending' ? 'bg-amber-50 text-amber-700 border-amber-200' : '',
                    s.status === 'Rejected' ? 'bg-red-50 text-red-700 border-red-200' : ''
                  ]"
                >
                  <span
                    :class="[
                      'w-1.5 h-1.5 rounded-full mr-1',
                      s.status === 'Collected' ? 'bg-emerald-500' : '',
                      s.status === 'Received' ? 'bg-teal-500' : '',
                      s.status === 'Processing' ? 'bg-blue-500 animate-pulse' : '',
                      s.status === 'Completed' ? 'bg-green-500' : '',
                      s.status === 'Pending' ? 'bg-amber-500' : '',
                      s.status === 'Rejected' ? 'bg-red-500' : ''
                    ]"
                  />
                  {{ s.status }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-slate-500 font-mono">
                {{ s.collected_at }}
              </td>
              <td class="px-4 py-2.5 text-center" @click.stop>
                <div class="flex items-center justify-center space-x-1.5">
                  <NuxtLink
                    :to="`/pathology/results?sample_id=${s.sample_id}`"
                    class="btn-primary py-0.5 px-2 text-[11px]"
                    title="Enter Results &amp; Generate Report"
                  >
                    Workstation
                  </NuxtLink>
                  <NuxtLink
                    :to="`/pathology/verification?sample_id=${s.sample_id}`"
                    class="btn-secondary py-0.5 px-2 text-[11px]"
                    title="Pathologist Approvals Desk"
                  >
                    Verify
                  </NuxtLink>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Component -->
      <PaginationBar
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total-items="filteredSamples.length"
      />
    </div>

    <!-- Bottom Split Section matching Screen 3: Sample Barcode Label (Left) + Quick Actions (Right) -->
    <div v-if="selectedSample" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Left Card: Sample Barcode Label matching Screen 3 -->
      <div class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
            <h3 class="text-xs font-bold text-slate-900 tracking-tight flex items-center space-x-1.5">
              <span>Sample Barcode Label</span>
            </h3>
            <span class="text-[11px] font-mono text-slate-500">
              Container: {{ selectedSample.specimen_type }}
            </span>
          </div>

          <!-- Barcode Graphic Container matching Screen 3 -->
          <div class="bg-slate-50 border border-slate-200 rounded p-4 flex flex-col items-center justify-center text-center">
            <!-- Authentic Barcode SVG Rendering -->
            <svg class="w-64 h-12" viewBox="0 0 200 40">
              <!-- Barcode Lines Pattern -->
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

            <!-- Barcode Number -->
            <p class="font-mono text-xs font-bold text-slate-800 tracking-wider mt-1">
              *{{ selectedSample.sample_id }}*
            </p>

            <!-- Patient Metadata matching Screen 3 -->
            <div class="mt-2 text-xs text-slate-700 font-medium">
              <span class="font-mono text-blue-700">{{ selectedSample.patient_uhid }}</span>
              <span class="mx-1.5 text-slate-300">|</span>
              <span>{{ selectedSample.age_sex }}</span>
              <span class="mx-1.5 text-slate-300">|</span>
              <span>{{ selectedSample.patient_name }}</span>
            </div>
            <p class="text-[11px] text-slate-500 mt-0.5">
              {{ selectedSample.test_name }} &bull; {{ selectedSample.department }}
            </p>
          </div>
        </div>

        <!-- Print Action Button matching Screen 3 -->
        <div class="mt-3 flex justify-end">
          <button
            type="button"
            class="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-300 rounded text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 transition cursor-pointer shadow-2xs"
            @click="printBarcodeLabel"
          >
            <svg class="h-3.5 w-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            <span>Print Label</span>
          </button>
        </div>
      </div>

      <!-- Right Card: Quick Actions matching Screen 3 -->
      <div class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
            <h3 class="text-xs font-bold text-slate-900 tracking-tight">
              Quick Actions for {{ selectedSample.sample_id }}
            </h3>
            <span class="text-[11px] text-slate-400">Workflow Transition</span>
          </div>

          <!-- Description -->
          <p class="text-xs text-slate-600 mb-4">
            Advance the specimen through laboratory reception, accessioning and automated analyzer processing benches.
          </p>

          <!-- Action Buttons in Colorful Semantics matching Screen 3 -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <!-- Receive Sample -->
            <button
              type="button"
              class="btn-emerald py-2.5 px-3 flex flex-col items-center justify-center space-y-1 text-xs"
              @click="markSampleReceived"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span>Receive Sample</span>
            </button>

            <!-- Mark Processing -->
            <button
              type="button"
              class="btn-primary py-2.5 px-3 flex flex-col items-center justify-center space-y-1 text-xs"
              @click="markSampleProcessing"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Mark Processing</span>
            </button>

            <!-- Mark Completed -->
            <button
              type="button"
              class="btn-secondary py-2.5 px-3 flex flex-col items-center justify-center space-y-1 text-xs text-purple-700 hover:text-purple-900 border-purple-200 hover:bg-purple-50"
              @click="markSampleCompleted"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Mark Completed</span>
            </button>
          </div>
        </div>

        <!-- Result Entry & Verification Direct Actions -->
        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span class="text-slate-500">
            Workstation actions for {{ selectedSample.sample_id }}:
          </span>
          <div class="flex items-center space-x-2">
            <button
              type="button"
              class="text-blue-700 font-semibold hover:underline flex items-center space-x-1 cursor-pointer"
              @click="navigateToResultEntry"
            >
              <span>Result Entry &rarr;</span>
            </button>
            <span class="text-slate-300">|</span>
            <NuxtLink
              :to="`/pathology/verification?sample_id=${selectedSample.sample_id}`"
              class="text-emerald-700 font-semibold hover:underline flex items-center space-x-1 cursor-pointer"
            >
              <span>Verification Desk &rarr;</span>
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <!-- New Sample Intake Modal -->
    <Modal
      v-model="newSampleModalOpen"
      title="Accession New Laboratory Specimen"
      description="Record accessioning for a newly received blood, serum or urine container."
    >
      <form class="space-y-3 text-xs" @submit.prevent="handleAddSample">
        <div>
          <label class="block font-medium text-slate-700 mb-1">Patient Name *</label>
          <input
            v-model="newSampleForm.patient_name"
            type="text"
            required
            placeholder="e.g. Rahul Verma"
            class="w-full px-3 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-medium text-slate-700 mb-1">Investigation</label>
            <input
              v-model="newSampleForm.test_name"
              type="text"
              required
              class="w-full px-3 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label class="block font-medium text-slate-700 mb-1">Department</label>
            <select
              v-model="newSampleForm.department"
              class="w-full px-3 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:outline-none"
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
          <label class="block font-medium text-slate-700 mb-1">Specimen Container Type</label>
          <select
            v-model="newSampleForm.specimen_type"
            class="w-full px-3 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:outline-none"
          >
            <option value="EDTA Whole Blood">EDTA Whole Blood (Lavender Top)</option>
            <option value="Serum">Serum / Clot Activator (Gold/Red Top)</option>
            <option value="Fluoride Plasma">Sodium Fluoride (Grey Top)</option>
            <option value="Urine">Sterile Urine Cup (Yellow)</option>
          </select>
        </div>

        <div class="pt-3 border-t border-slate-100 flex justify-end space-x-2">
          <button
            type="button"
            class="px-3 py-1.5 border border-slate-300 rounded text-slate-700 bg-white hover:bg-slate-50 text-xs font-medium cursor-pointer"
            @click="newSampleModalOpen = false"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded shadow-xs cursor-pointer"
          >
            Generate Barcode &amp; Accession
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>
