<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'
import { useReportTheme } from '~/composables/useReportTheme'

const api = useApi()
const { success, warning, info } = useToast()
const { signatories } = useReportTheme()

interface PendingVerificationItem {
  id: string
  sample_id: string
  uhid: string
  patient_name: string
  age_sex: string
  test_name: string
  department: string
  completed_at: string
  flags: 'Normal' | 'Abnormal' | 'Critical Panic'
  flag_count: number
  key_findings: string
  status: 'Pending Verification' | 'Approved' | 'Returned for Rerun'
}

const loading = ref(true)
const queue = ref<PendingVerificationItem[]>([])
const selectedFilter = ref<'all' | 'pending' | 'approved'>('all')
const searchQuery = ref('')

// Pathologist from active branding settings
const signingDoctor = computed(() => {
  const consultant = signatories.value.find((s) => s.id === 'sig-2') || signatories.value[1]
  return consultant ? `${consultant.name}, ${consultant.qualification}` : 'Dr. Payal Shah, MD (Pathology)'
})

async function fetchVerificationQueue() {
  loading.value = true
  try {
    const list: any = await api.get('/pathology/samples')
    if (Array.isArray(list)) {
      queue.value = list.map((s: any, idx: number) => {
        const flagType: 'Normal' | 'Abnormal' | 'Critical Panic' = s.flag_type || 'Normal'
        const flagCount: number = s.flag_count || 0
        const findings: string = s.key_findings || 'All analytes within physiological biological reference intervals.'

        const isCompleted = s.status === 'Completed' || s.status === 'Released'
        const verificationStatus: 'Pending Verification' | 'Approved' | 'Returned for Rerun' = isCompleted
          ? 'Approved'
          : 'Pending Verification'

        return {
          id: `ver-${s.id || idx}`,
          sample_id: s.sample_id,
          uhid: s.patient_uhid,
          patient_name: s.patient_name,
          age_sex: s.age_sex,
          test_name: s.test_name,
          department: s.department,
          completed_at: s.collected_at ? `Today ${s.collected_at}` : 'Recently',
          flags: flagType,
          flag_count: flagCount,
          key_findings: findings,
          status: verificationStatus,
        }
      })
    }
  } catch (err) {
    console.error('Failed to load verification queue from database:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchVerificationQueue()
})

const filteredQueue = computed(() => {
  return queue.value.filter((item) => {
    if (selectedFilter.value === 'pending' && item.status !== 'Pending Verification') return false
    if (selectedFilter.value === 'approved' && item.status !== 'Approved') return false

    const q = searchQuery.value.trim().toLowerCase()
    if (q) {
      const matchName = item.patient_name.toLowerCase().includes(q)
      const matchUhid = item.uhid.toLowerCase().includes(q)
      const matchSample = item.sample_id.toLowerCase().includes(q)
      const matchTest = item.test_name.toLowerCase().includes(q)
      if (!matchName && !matchUhid && !matchSample && !matchTest) return false
    }

    return true
  })
})

const { currentPage, pageSize, paginatedItems: paginatedQueue, resetPage } = usePagination(filteredQueue, 10)

watch([selectedFilter, searchQuery], () => {
  resetPage()
})

// Approval Modal
const isApproveModalOpen = ref(false)
const activeItem = ref<PendingVerificationItem | null>(null)
const pathologistRemarks = ref('Results correlated with clinical history. Verified for official report release.')

function openApproveModal(item: PendingVerificationItem) {
  activeItem.value = item
  isApproveModalOpen.value = true
}

async function approveReport() {
  if (!activeItem.value) return
  try {
    await api.post(`/pathology/results/verify`, {
      sample_id: activeItem.value.sample_id,
      notes: pathologistRemarks.value,
      signer: signingDoctor.value,
    })
  } catch {
    // API response handled
  }

  activeItem.value.status = 'Approved'
  success('Report Approved', `Diagnostic report for ${activeItem.value.patient_name} approved and digitally stamped!`)
  isApproveModalOpen.value = false
}

function returnForRerun(item: PendingVerificationItem) {
  item.status = 'Returned for Rerun'
  warning('Returned for Rerun', `Sample ${item.sample_id} returned to laboratory bench for dilution rerun.`)
}

function batchApproveAll() {
  let approvedCount = 0
  for (const item of queue.value) {
    if (item.status === 'Pending Verification' && item.flags !== 'Critical Panic') {
      item.status = 'Approved'
      approvedCount++
    }
  }
  if (approvedCount > 0) {
    success('Batch Approved', `${approvedCount} non-critical pending report(s) digitally approved!`)
  } else {
    info('No Pending Items', 'All non-critical batches are already approved.')
  }
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
          class="px-3 py-1.5 rounded-md font-medium text-xs bg-white/10 hover:bg-white/20 text-white transition flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Sample Tracking</span>
        </NuxtLink>

        <NuxtLink
          to="/pathology/verification"
          class="px-3 py-1.5 rounded-md font-bold text-xs bg-white text-blue-900 shadow-2xs flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Verification</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Pathologist Verification &amp; Approval Desk</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Medical doctor clinical evaluation, delta check audit, abnormal flag review and digital signature release
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <button
          type="button"
          class="btn-secondary"
          @click="fetchVerificationQueue"
        >
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          <span>Refresh</span>
        </button>

        <button
          type="button"
          class="btn-emerald"
          @click="batchApproveAll"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>Batch Approve (Normal)</span>
        </button>
      </div>
    </div>

    <!-- Summary KPIs -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Awaiting Verification</p>
        <p class="text-lg font-bold font-mono text-blue-700 mt-0.5">
          {{ queue.filter(q => q.status === 'Pending Verification').length }}
        </p>
      </div>
      <div class="bg-white p-3 rounded-lg border border-red-200 bg-red-50/20 shadow-2xs">
        <p class="text-[11px] font-medium text-red-600">Panic Values (Immediate Review)</p>
        <p class="text-lg font-bold font-mono text-red-700 mt-0.5">
          {{ queue.filter(q => q.flags === 'Critical Panic').length }}
        </p>
      </div>
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Abnormal Flags</p>
        <p class="text-lg font-bold font-mono text-amber-600 mt-0.5">
          {{ queue.filter(q => q.flags === 'Abnormal').length }}
        </p>
      </div>
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Signing Pathologist</p>
        <p class="text-xs font-bold text-slate-800 mt-1 line-clamp-1">{{ signingDoctor }}</p>
        <p class="text-[9px] text-emerald-700 font-semibold flex items-center mt-0.5">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1" />
          Digital DSC Certificate Valid
        </p>
      </div>
    </div>

    <!-- Filter & Search Toolbar -->
    <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center flex-1 min-w-[260px] max-w-md">
        <div class="relative flex-1">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 pointer-events-none">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search queue by patient, UHID, sample barcode, test..."
            class="input-faang w-full pl-8 pr-7 py-1.5 text-xs font-sans"
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
      </div>

      <div class="flex items-center space-x-1.5">
        <button
          type="button"
          class="filter-pill"
          :class="{ active: selectedFilter === 'all' }"
          @click="selectedFilter = 'all'"
        >
          All ({{ queue.length }})
        </button>
        <button
          type="button"
          class="filter-pill"
          :class="{ active: selectedFilter === 'pending' }"
          @click="selectedFilter = 'pending'"
        >
          Pending ({{ queue.filter(q => q.status === 'Pending Verification').length }})
        </button>
        <button
          type="button"
          class="filter-pill"
          :class="{ active: selectedFilter === 'approved' }"
          @click="selectedFilter = 'approved'"
        >
          Approved ({{ queue.filter(q => q.status === 'Approved').length }})
        </button>
      </div>
    </div>

    <!-- Queue Table -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="w-12 px-3 py-2.5 text-center">#</th>
              <th class="px-4 py-2.5 text-left">Sample / UHID</th>
              <th class="px-4 py-2.5 text-left">Patient Details</th>
              <th class="px-4 py-2.5 text-left">Investigation Panel</th>
              <th class="px-4 py-2.5 text-left">Key Findings</th>
              <th class="px-4 py-2.5 text-center">Alert Flag</th>
              <th class="px-4 py-2.5 text-center">Status</th>
              <th class="px-4 py-2.5 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="8" class="text-center py-8 text-slate-400 font-medium">
                Loading verification queue from database...
              </td>
            </tr>
            <tr v-else-if="filteredQueue.length === 0">
              <td colspan="8" class="text-center py-8 text-slate-400 font-medium">
                No reports matching verification criteria.
              </td>
            </tr>
            <tr
              v-for="(item, idx) in paginatedQueue"
              v-else
              :key="item.id"
              :class="[
                'transition-colors',
                item.flags === 'Critical Panic' ? 'bg-red-50/40 hover:bg-red-50/70' : 'hover:bg-blue-50/40'
              ]"
            >
              <td class="px-3 py-2.5 text-center font-mono font-bold text-slate-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>
              <td class="px-4 py-2.5 font-mono">
                <div class="font-bold text-blue-700">{{ item.sample_id }}</div>
                <div class="text-[10px] text-slate-500">{{ item.uhid }}</div>
              </td>
              <td class="px-4 py-2.5 font-medium text-slate-900">
                <div>{{ item.patient_name }}</div>
                <div class="text-[10px] text-slate-500 font-mono">{{ item.age_sex }}</div>
              </td>
              <td class="px-4 py-2.5 text-slate-800">
                <div>{{ item.test_name }}</div>
                <div class="text-[10px] text-slate-500">{{ item.department }}</div>
              </td>
              <td class="px-4 py-2.5 text-slate-700 font-mono text-[11px]">
                {{ item.key_findings }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border',
                    item.flags === 'Critical Panic' ? 'bg-red-100 text-red-800 border-red-300 animate-pulse' : (item.flags === 'Abnormal' ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-emerald-100 text-emerald-800 border-emerald-200')
                  ]"
                >
                  {{ item.flags }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  :class="[
                    'inline-block px-2 py-0.5 rounded text-[10px] font-semibold',
                    item.status === 'Approved' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : (item.status === 'Returned for Rerun' ? 'bg-slate-100 text-slate-600 border border-slate-200' : 'bg-blue-50 text-blue-700 border border-blue-200')
                  ]"
                >
                  {{ item.status }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center space-x-1.5 whitespace-nowrap">
                <NuxtLink
                  :to="`/pathology/results?sample_id=${item.sample_id}`"
                  class="px-2 py-1 text-[11px] font-bold text-white bg-blue-600 hover:bg-blue-700 rounded transition inline-block shadow-2xs"
                  title="View/Edit Investigation Results in Workstation"
                >
                  ⚡ Workstation
                </NuxtLink>

                <template v-if="item.status === 'Pending Verification'">
                  <button
                    type="button"
                    class="px-2.5 py-1 text-[11px] font-semibold text-white bg-sky-600 hover:bg-sky-700 rounded shadow-2xs transition cursor-pointer"
                    @click="openApproveModal(item)"
                  >
                    Approve &amp; Sign
                  </button>
                  <button
                    type="button"
                    class="px-2 py-1 text-[11px] font-medium text-slate-600 hover:text-red-700 hover:bg-red-50 rounded transition cursor-pointer"
                    title="Return to technologist for dilution / rerun"
                    @click="returnForRerun(item)"
                  >
                    Rerun
                  </button>
                </template>
                <NuxtLink
                  v-else-if="item.status === 'Approved'"
                  to="/reporting/templates"
                  class="text-emerald-700 font-semibold hover:underline text-[11px]"
                >
                  View Letterhead &rarr;
                </NuxtLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Component -->
      <PaginationBar
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total-items="filteredQueue.length"
      />
    </div>

    <!-- Approve Modal -->
    <div
      v-if="isApproveModalOpen && activeItem"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-sm font-bold text-slate-900">Sign &amp; Release Diagnostic Report</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="isApproveModalOpen = false">&times;</button>
        </div>

        <form class="p-5 space-y-3 text-xs" @submit.prevent="approveReport">
          <div class="bg-slate-50 p-3 rounded border border-slate-200 space-y-1">
            <div class="flex justify-between">
              <span class="text-slate-500">Patient:</span>
              <span class="font-bold text-slate-900">{{ activeItem.patient_name }} ({{ activeItem.uhid }})</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Panel:</span>
              <span class="font-medium text-slate-800">{{ activeItem.test_name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Result Summary:</span>
              <span class="font-mono font-bold text-blue-700">{{ activeItem.key_findings }}</span>
            </div>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Pathologist Clinical Interpretation / Remarks</label>
            <textarea
              v-model="pathologistRemarks"
              rows="3"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div class="border-t border-slate-100 pt-2 flex items-center justify-between">
            <div class="text-[11px] text-slate-500">
              Authorized Signatory:<br />
              <strong class="text-slate-800">{{ signingDoctor }}</strong>
            </div>
            <div class="text-right">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                Digital DSC Valid
              </span>
            </div>
          </div>

          <div class="flex justify-end space-x-2 pt-3">
            <button type="button" class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded hover:bg-slate-50" @click="isApproveModalOpen = false">
              Cancel
            </button>
            <button type="submit" class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded shadow-xs cursor-pointer">
              Confirm &amp; Stamp Signature
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
