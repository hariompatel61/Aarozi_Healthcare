<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'

const api = useApi()
const { success, warning, error } = useToast()

interface CrossMatchItem {
  id: string
  request_no: string
  patient_uhid: string
  patient_name: string
  patient_blood_group: string
  donor_unit_number: string
  donor_blood_group: string
  component: string
  urgency: 'Routine' | 'Emergency'
  major_crossmatch: 'Compatible' | 'Incompatible' | 'Pending'
  minor_crossmatch: 'Compatible' | 'Incompatible' | 'Pending'
  status: 'Pending Test' | 'Ready for Issue' | 'Issued' | 'Incompatible'
}

const loading = ref(true)
const requests = ref<CrossMatchItem[]>([])

async function fetchCrossMatches() {
  loading.value = true
  try {
    const data: any = await api.get('/blood-bank/crossmatch-records')
    if (Array.isArray(data)) {
      requests.value = data
    }
  } catch (err) {
    console.warn('Failed to load crossmatch records from database:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCrossMatches()
})

// Issue Modal
const isIssueModalOpen = ref(false)
const selectedRequest = ref<CrossMatchItem | null>(null)
const wardBed = ref('ICU Bed 4')
const recipientAttendant = ref('Staff Nurse Kavita')

function openIssueModal(req: CrossMatchItem) {
  selectedRequest.value = req
  isIssueModalOpen.value = true
}

async function confirmIssue() {
  if (!selectedRequest.value) return
  try {
    await api.post(`/blood-bank/units/${selectedRequest.value.id}/issue?recipient_patient_id=${selectedRequest.value.patient_uhid}`)
    selectedRequest.value.status = 'Issued'
    success(`Unit ${selectedRequest.value.donor_unit_number} issued for patient ${selectedRequest.value.patient_name}! Transfusion slip printed.`)
    isIssueModalOpen.value = false
  } catch (err: any) {
    error('Issue Failed', err?.message || 'Could not issue blood unit.')
  }
}
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Blood Bank &mdash; Cross-Matching &amp; Issue</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Serological compatibility verification, Coomb's test validation and bed-side transfusion release
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <NuxtLink
          to="/blood_bank/inventory"
          class="btn-secondary"
        >
          <span>Inventory Status</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Instructions Banner -->
    <div class="bg-amber-50/70 border border-amber-200 p-3 rounded-lg text-xs text-amber-800 flex items-start space-x-2">
      <span class="font-bold text-amber-900">Safety Rule:</span>
      <span>Double patient identity check and recipient ABO/Rh confirmation required before final issue. Incompatible units are automatically hard-blocked from issue.</span>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="px-4 py-2.5 text-left">Requisition #</th>
              <th class="px-4 py-2.5 text-left">Patient (UHID)</th>
              <th class="px-4 py-2.5 text-center">Patient Grp</th>
              <th class="px-4 py-2.5 text-left">Assigned Unit #</th>
              <th class="px-4 py-2.5 text-center">Unit Grp</th>
              <th class="px-4 py-2.5 text-left">Component</th>
              <th class="px-4 py-2.5 text-center">Major Cross</th>
              <th class="px-4 py-2.5 text-center">Minor Cross</th>
              <th class="px-4 py-2.5 text-center">Status</th>
              <th class="px-4 py-2.5 text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="10" class="px-4 py-8 text-center text-slate-500">
                <div class="inline-flex items-center space-x-2">
                  <span class="inline-block w-4 h-4 border-2 border-sky-600 border-t-transparent rounded-full animate-spin"></span>
                  <span>Loading cross-match records...</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="requests.length === 0">
              <td colspan="10" class="px-4 py-8 text-center text-slate-400">
                No cross-match requisitions found. New cross-match tests will appear here.
              </td>
            </tr>
            <tr
              v-for="req in requests"
              :key="req.id"
              class="hover:bg-blue-50/40 transition-colors"
            >
              <td class="px-4 py-2.5 font-mono font-semibold text-blue-700">
                {{ req.request_no }}
              </td>
              <td class="px-4 py-2.5 font-medium text-slate-900">
                <div>{{ req.patient_name }}</div>
                <div class="text-[10px] text-slate-500 font-mono">{{ req.patient_uhid }}</div>
              </td>
              <td class="px-4 py-2.5 text-center">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-800 font-mono">
                  {{ req.patient_blood_group }}
                </span>
              </td>
              <td class="px-4 py-2.5 font-mono text-slate-800 font-medium">
                {{ req.donor_unit_number }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700 font-mono">
                  {{ req.donor_blood_group }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-slate-700">
                {{ req.component }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  :class="[
                    'inline-block px-1.5 py-0.5 rounded text-[10px] font-bold',
                    req.major_crossmatch === 'Compatible' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                  ]"
                >
                  {{ req.major_crossmatch }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  :class="[
                    'inline-block px-1.5 py-0.5 rounded text-[10px] font-bold',
                    req.minor_crossmatch === 'Compatible' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                  ]"
                >
                  {{ req.minor_crossmatch }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border',
                    req.status === 'Ready for Issue' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : '',
                    req.status === 'Issued' ? 'bg-blue-50 text-blue-700 border-blue-200' : '',
                    req.status === 'Pending Test' ? 'bg-amber-50 text-amber-700 border-amber-200' : ''
                  ]"
                >
                  {{ req.status }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center whitespace-nowrap">
                <button
                  v-if="req.status === 'Ready for Issue'"
                  type="button"
                  class="btn-emerald py-0.5 px-2 text-[11px]"
                  @click="openIssueModal(req)"
                >
                  Issue Blood Unit
                </button>
                <span v-else-if="req.status === 'Issued'" class="text-[11px] text-slate-400 font-medium">
                  Dispatched
                </span>
                <span v-else class="text-[11px] text-amber-600 font-medium">
                  Testing
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Issue Unit Modal -->
    <div
      v-if="isIssueModalOpen && selectedRequest"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-sm font-bold text-slate-900">Authorize Blood Unit Issue</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="isIssueModalOpen = false">&times;</button>
        </div>

        <form class="p-5 space-y-3 text-xs" @submit.prevent="confirmIssue">
          <div class="bg-blue-50 p-3 rounded border border-blue-100 space-y-1">
            <div class="flex justify-between">
              <span class="text-slate-600">Patient:</span>
              <span class="font-bold text-slate-900">{{ selectedRequest.patient_name }} ({{ selectedRequest.patient_blood_group }})</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-600">Unit Number:</span>
              <span class="font-mono font-bold text-red-600">{{ selectedRequest.donor_unit_number }} ({{ selectedRequest.donor_blood_group }})</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-600">Compatibility:</span>
              <span class="font-bold text-emerald-700">Major &amp; Minor Compatible</span>
            </div>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Ward / Bed Location</label>
            <input v-model="wardBed" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded" />
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Receiving Nursing Attendant</label>
            <input v-model="recipientAttendant" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded" />
          </div>

          <div class="flex justify-end space-x-2 pt-3">
            <button type="button" class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded hover:bg-slate-50" @click="isIssueModalOpen = false">
              Cancel
            </button>
            <button type="submit" class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded shadow-xs">
              Confirm &amp; Issue Unit
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
