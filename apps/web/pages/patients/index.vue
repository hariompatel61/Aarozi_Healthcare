<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Badge from '~/components/ui/Badge.vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import Kbd from '~/components/ui/Kbd.vue'
import Modal from '~/components/ui/Modal.vue'

const router = useRouter()
const route = useRoute()
const searchQuery = ref('')
const selectedGender = ref('All')
const selectedStatus = ref('All')

const api = useApi()
const loading = ref(true)
const patients = ref<PatientRecord[]>([])
const selectedPatient = ref<PatientRecord | null>(null)
const isDetailsModalOpen = ref(false)

interface PatientRecord {
  id: string
  uhid: string
  name: string
  age: number
  gender: string
  mobile: string
  tests: string
  status: string
  amount: number
  time: string
  invoice_id?: string
  invoice_no?: string
  referral_doctor?: string
  referral_partner_id?: string
}

async function loadPatients() {
  loading.value = true
  try {
    if (route.query.query) {
      searchQuery.value = String(route.query.query)
    } else if (route.query.search) {
      searchQuery.value = String(route.query.search)
    }

    const refPartnerParam = route.query.referral_partner_id
      ? `?referral_partner_id=${encodeURIComponent(String(route.query.referral_partner_id))}`
      : ''

    const data: any = await api.get(`/patients${refPartnerParam}`)
    if (Array.isArray(data)) {
      patients.value = data.map((p: any, idx: number) => ({
        id: p.id || String(idx + 1),
        uhid: p.patient_no || 'N/A',
        name: `${p.first_name || ''} ${p.last_name || ''}`.trim() || 'Patient',
        age: p.age_years || p.age || 0,
        gender: (p.sex || '-').charAt(0).toUpperCase(),
        mobile: p.mobile_normalized || p.mobile || '-',
        tests: p.tests || '-',
        status: p.status || 'Registered',
        amount: Number(p.amount || 0),
        time: p.time || '-',
        invoice_id: p.invoice_id,
        invoice_no: p.invoice_no,
        referral_doctor: p.referral_doctor || 'Direct Walk-in',
        referral_partner_id: p.referral_partner_id,
      }))
    }
  } catch (err) {
    console.error('Failed to load patients from database:', err)
  } finally {
    loading.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'F2') {
    e.preventDefault()
    router.push('/patients/register')
  } else if (e.key === '/' && (e.target as HTMLElement)?.tagName !== 'INPUT') {
    e.preventDefault()
    const searchInput = document.getElementById('patient-search-input')
    searchInput?.focus()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadPatients()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const filteredPatients = computed(() => {
  return patients.value.filter((p) => {
    const q = searchQuery.value.trim().toLowerCase()
    const matchesQ =
      !q ||
      p.uhid.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      p.mobile.includes(q) ||
      p.tests.toLowerCase().includes(q) ||
      (p.referral_doctor && p.referral_doctor.toLowerCase().includes(q)) ||
      (p.invoice_no && p.invoice_no.toLowerCase().includes(q))

    const matchesGender = selectedGender.value === 'All' || p.gender === selectedGender.value
    const matchesStatus = selectedStatus.value === 'All' || p.status === selectedStatus.value

    return matchesQ && matchesGender && matchesStatus
  })
})

const { currentPage, pageSize, paginatedItems: paginatedPatients, resetPage } = usePagination(filteredPatients, 10)

watch([searchQuery, selectedGender, selectedStatus], () => {
  resetPage()
})

function getStatusBadgeVariant(status: string): 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'panic' {
  switch (status) {
    case 'Completed':
      return 'success'
    case 'Processing':
      return 'info'
    case 'Collected':
      return 'neutral'
    case 'Pending':
      return 'warning'
    default:
      return 'neutral'
  }
}

function openPatientDetails(p: PatientRecord) {
  selectedPatient.value = p
  isDetailsModalOpen.value = true
}

function resetFilters() {
  searchQuery.value = ''
  selectedGender.value = 'All'
  selectedStatus.value = 'All'
}
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto text-left">
    <!-- Page Header -->
    <PageHeader
      title="Patient Master Directory"
      description="Universal patient identity lookup across clinical orders, laboratory results, and billing ledgers."
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <Button
            variant="secondary"
            size="md"
            title="Reload patients"
            @click="loadPatients"
          >
            <Icon name="refresh" class="w-4 h-4" />
            <span class="hidden sm:inline">Refresh</span>
          </Button>
          <Button
            variant="primary"
            size="md"
            title="Register new patient or walk-in (F2)"
            to="/patients/register"
          >
            <Icon name="plus" class="w-4 h-4" />
            <span>New Patient</span>
            <Kbd>F2</Kbd>
          </Button>
        </div>
      </template>
    </PageHeader>

    <!-- Operational KPI Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Patients</p>
          <div class="w-8 h-8 rounded-lg bg-teal-50 flex items-center justify-center text-teal-600">
            <Icon name="users" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-slate-900 mt-2">{{ patients.length }}</p>
        <p class="text-xs text-slate-500 mt-1">Master lifetime directory</p>
      </Card>

      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Today's Intake</p>
          <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
            <Icon name="calendar" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-blue-600 mt-2">{{ patients.length }}</p>
        <p class="text-xs text-blue-700 mt-1 font-medium">New registrations</p>
      </Card>

      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active In-Progress</p>
          <div class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
            <Icon name="activity" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-amber-600 mt-2">
          {{ patients.filter(p => ['Processing', 'Collected', 'Pending', 'Registered'].includes(p.status)).length }}
        </p>
        <p class="text-xs text-amber-700 mt-1 font-medium">In lab processing queue</p>
      </Card>

      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Completed Cases</p>
          <div class="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
            <Icon name="check" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-emerald-600 mt-2">
          {{ patients.filter(p => p.status === 'Completed').length }}
        </p>
        <p class="text-xs text-emerald-700 mt-1 font-medium">Validated &amp; released</p>
      </Card>
    </div>

    <!-- Filter & Search Toolbar -->
    <Card class="p-4 bg-white">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <!-- Search Input with Keyboard Cue -->
        <div class="relative flex-1 max-w-xl">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
            <Icon name="search" class="w-4 h-4" />
          </span>
          <input
            id="patient-search-input"
            v-model="searchQuery"
            type="search"
            placeholder="Search by UHID, Patient Name, Mobile, Test, Doctor..."
            class="w-full pl-9 pr-14 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent transition-shadow"
          />
          <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <Kbd>/</Kbd>
          </div>
        </div>

        <!-- Filter Dropdowns & Reset -->
        <div class="flex flex-wrap items-center gap-3">
          <!-- Gender Filter -->
          <div class="flex items-center gap-1.5">
            <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sex:</label>
            <select
              v-model="selectedGender"
              class="border border-slate-300 rounded-lg px-3 py-2 text-xs font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-teal-600"
            >
              <option value="All">All Genders</option>
              <option value="M">Male (M)</option>
              <option value="F">Female (F)</option>
              <option value="O">Other (O)</option>
            </select>
          </div>

          <!-- Status Filter -->
          <div class="flex items-center gap-1.5">
            <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Status:</label>
            <select
              v-model="selectedStatus"
              class="border border-slate-300 rounded-lg px-3 py-2 text-xs font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-teal-600"
            >
              <option value="All">All Statuses</option>
              <option value="Registered">Registered</option>
              <option value="Collected">Collected</option>
              <option value="Processing">Processing</option>
              <option value="Completed">Completed</option>
              <option value="Pending">Pending</option>
            </select>
          </div>

          <!-- Reset Filter Button -->
          <Button
            variant="ghost"
            size="sm"
            title="Reset all filters"
            @click="resetFilters"
          >
            <Icon name="x" class="w-3.5 h-3.5" />
            <span>Reset</span>
          </Button>
        </div>
      </div>
    </Card>

    <!-- Desktop Table View -->
    <Card class="overflow-hidden bg-white hidden md:block">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="w-12 px-3 py-3 text-center">#</th>
              <th class="px-4 py-3 text-left">Patient ID (UHID)</th>
              <th class="px-4 py-3 text-left">Name</th>
              <th class="px-4 py-3 text-left">Age / Sex</th>
              <th class="px-4 py-3 text-left">Mobile Number</th>
              <th class="px-4 py-3 text-left">Prescribed By</th>
              <th class="px-4 py-3 text-left">Ordered Tests</th>
              <th class="px-4 py-3 text-left">Status</th>
              <th class="px-4 py-3 text-right">Invoice &amp; Bill</th>
              <th class="px-4 py-3 text-right">Time</th>
              <th class="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="11" class="text-center py-12 text-slate-400 font-medium">
                <div class="flex items-center justify-center gap-2">
                  <Icon name="refresh" class="w-5 h-5 animate-spin text-teal-600" />
                  <span>Loading patient directory from local database...</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="filteredPatients.length === 0">
              <td colspan="11" class="text-center py-12 text-slate-400 font-medium">
                <div class="flex flex-col items-center justify-center gap-2">
                  <Icon name="users" class="w-8 h-8 text-slate-300" />
                  <p class="text-sm font-semibold text-slate-600">No matching patient records found</p>
                  <p class="text-xs text-slate-400">Try adjusting your search criteria or register a new patient.</p>
                </div>
              </td>
            </tr>
            <tr
              v-for="(p, idx) in paginatedPatients"
              v-else
              :key="p.id"
              class="hover:bg-teal-50/40 transition-colors"
            >
              <td class="px-3 py-3 text-center font-mono font-bold text-slate-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>
              <td class="px-4 py-3 font-mono font-semibold text-teal-700">
                <button
                  type="button"
                  class="hover:underline font-mono text-left font-bold"
                  title="Click to view complete patient details"
                  @click="openPatientDetails(p)"
                >
                  {{ p.uhid }}
                </button>
              </td>
              <td class="px-4 py-3 font-semibold text-slate-900">
                <button
                  type="button"
                  class="hover:text-teal-700 text-left cursor-pointer"
                  @click="openPatientDetails(p)"
                >
                  {{ p.name }}
                </button>
              </td>
              <td class="px-4 py-3 text-slate-600 font-mono">
                {{ p.age }} Y / {{ p.gender }}
              </td>
              <td class="px-4 py-3 text-slate-600 font-mono">
                {{ p.mobile }}
              </td>
              <td class="px-4 py-3 text-slate-700">
                <NuxtLink
                  v-if="p.referral_doctor && p.referral_doctor !== 'Direct Walk-in'"
                  :to="'/billing/referrals?search=' + encodeURIComponent(p.referral_doctor)"
                  class="text-teal-700 font-medium hover:underline inline-flex items-center gap-1"
                  title="View Referring Doctor Details"
                >
                  <Icon name="user" class="w-3.5 h-3.5 text-slate-400" />
                  <span>{{ p.referral_doctor }}</span>
                </NuxtLink>
                <span v-else class="text-slate-400 italic">Direct Walk-in</span>
              </td>
              <td class="px-4 py-3 text-slate-700 max-w-xs truncate" :title="p.tests">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-800 font-medium">
                  {{ p.tests }}
                </span>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="getStatusBadgeVariant(p.status)">
                  {{ p.status }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right font-mono">
                <NuxtLink
                  v-if="p.invoice_no"
                  :to="'/billing/invoices?search=' + encodeURIComponent(p.invoice_no)"
                  class="text-teal-700 font-bold hover:underline block"
                  title="View Invoice"
                >
                  ₹{{ p.amount.toLocaleString('en-IN') }}
                  <span class="block text-xs text-slate-400 font-normal font-mono">{{ p.invoice_no }}</span>
                </NuxtLink>
                <span v-else class="text-slate-500 font-semibold font-mono">₹{{ p.amount }}</span>
              </td>
              <td class="px-4 py-3 text-right text-slate-500 font-mono whitespace-nowrap">
                {{ p.time }}
              </td>
              <td class="px-4 py-3 text-center whitespace-nowrap">
                <div class="flex items-center justify-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="sm"
                    title="View Patient Record"
                    @click="openPatientDetails(p)"
                  >
                    <Icon name="eye" class="w-3.5 h-3.5" />
                    <span>View</span>
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    title="Book New Lab Order"
                    :to="{ path: '/patients/register', query: { patient_id: p.id, uhid: p.uhid } }"
                  >
                    <Icon name="plus" class="w-3.5 h-3.5" />
                    <span>Order</span>
                  </Button>
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
        :total-items="filteredPatients.length"
      />
    </Card>

    <!-- Mobile Card View (for screens under 768px) -->
    <div class="md:hidden space-y-3">
      <div v-if="loading" class="p-8 text-center text-slate-400 font-medium">
        <Icon name="refresh" class="w-6 h-6 animate-spin mx-auto text-teal-600 mb-2" />
        <p class="text-xs">Loading patient records...</p>
      </div>
      <div v-else-if="filteredPatients.length === 0" class="p-8 text-center text-slate-400 font-medium bg-white rounded-lg border border-slate-200">
        <Icon name="users" class="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p class="text-sm font-semibold text-slate-700">No patients found</p>
      </div>
      <Card
        v-for="p in paginatedPatients"
        v-else
        :key="'mobile-' + p.id"
        class="p-4 bg-white space-y-3 border border-slate-200"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                {{ p.uhid }}
              </span>
              <Badge :variant="getStatusBadgeVariant(p.status)">
                {{ p.status }}
              </Badge>
            </div>
            <h3 class="text-sm font-bold text-slate-900 mt-1">{{ p.name }}</h3>
            <p class="text-xs text-slate-500 font-mono mt-0.5">
              {{ p.age }} Y / {{ p.gender }} • {{ p.mobile }}
            </p>
          </div>
          <div class="text-right">
            <span class="text-sm font-bold font-mono text-slate-900">₹{{ p.amount.toLocaleString('en-IN') }}</span>
            <span v-if="p.invoice_no" class="block text-xs font-mono text-slate-400">{{ p.invoice_no }}</span>
          </div>
        </div>

        <div class="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-medium text-slate-500">Doctor:</span>
            <span class="font-semibold text-slate-800">{{ p.referral_doctor }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="font-medium text-slate-500">Tests:</span>
            <span class="font-semibold text-slate-800 truncate max-w-[200px]">{{ p.tests }}</span>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <Button
            variant="ghost"
            size="sm"
            @click="openPatientDetails(p)"
          >
            <Icon name="eye" class="w-3.5 h-3.5" />
            <span>Details</span>
          </Button>
          <Button
            variant="secondary"
            size="sm"
            :to="'/billing/invoices?search=' + encodeURIComponent(p.uhid)"
          >
            <Icon name="credit-card" class="w-3.5 h-3.5" />
            <span>Bill</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            :to="{ path: '/patients/register', query: { patient_id: p.id, uhid: p.uhid } }"
          >
            <Icon name="plus" class="w-3.5 h-3.5" />
            <span>Order</span>
          </Button>
        </div>
      </Card>

      <PaginationBar
        v-if="filteredPatients.length > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total-items="filteredPatients.length"
      />
    </div>

    <!-- Patient Details Modal -->
    <Modal
      v-model="isDetailsModalOpen"
      title="Patient Identity & Clinical Summary"
      size="lg"
      @close="isDetailsModalOpen = false"
    >
      <div v-if="selectedPatient" class="space-y-6">
        <!-- Demographics Header Banner -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-teal-100 flex items-center justify-center text-teal-800 font-bold text-lg">
              {{ selectedPatient.name.charAt(0) }}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-base font-bold text-slate-900">{{ selectedPatient.name }}</h3>
                <Badge :variant="getStatusBadgeVariant(selectedPatient.status)">
                  {{ selectedPatient.status }}
                </Badge>
              </div>
              <p class="text-xs text-slate-500 font-mono mt-0.5">
                UHID: <span class="text-teal-700 font-bold">{{ selectedPatient.uhid }}</span> • Age: {{ selectedPatient.age }} Years • Sex: {{ selectedPatient.gender }}
              </p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Registered</p>
            <p class="text-xs font-mono font-medium text-slate-700 mt-0.5">{{ selectedPatient.time }}</p>
          </div>
        </div>

        <!-- Detailed Attributes Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1 p-3 bg-white border border-slate-200 rounded-lg">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Mobile Number</span>
            <div class="flex items-center gap-2">
              <Icon name="phone" class="w-4 h-4 text-teal-600" />
              <span class="text-sm font-mono font-semibold text-slate-800">{{ selectedPatient.mobile }}</span>
            </div>
          </div>

          <div class="space-y-1 p-3 bg-white border border-slate-200 rounded-lg">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Prescribing Physician</span>
            <div class="flex items-center gap-2">
              <Icon name="user" class="w-4 h-4 text-teal-600" />
              <span class="text-sm font-semibold text-slate-800">{{ selectedPatient.referral_doctor }}</span>
            </div>
          </div>

          <div class="space-y-1 p-3 bg-white border border-slate-200 rounded-lg">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Ordered Lab Tests</span>
            <div class="flex items-center gap-2">
              <Icon name="beaker" class="w-4 h-4 text-teal-600" />
              <span class="text-sm font-medium text-slate-800">{{ selectedPatient.tests }}</span>
            </div>
          </div>

          <div class="space-y-1 p-3 bg-white border border-slate-200 rounded-lg">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Invoice &amp; Amount</span>
            <div class="flex items-center justify-between">
              <span class="text-sm font-mono font-bold text-slate-900">₹{{ selectedPatient.amount.toLocaleString('en-IN') }}</span>
              <span v-if="selectedPatient.invoice_no" class="text-xs font-mono text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                {{ selectedPatient.invoice_no }}
              </span>
            </div>
          </div>
        </div>

        <!-- Quick Action Navigations -->
        <div class="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-slate-200">
          <Button
            variant="ghost"
            size="md"
            @click="isDetailsModalOpen = false"
          >
            Close
          </Button>
          <Button
            v-if="selectedPatient.invoice_no"
            variant="secondary"
            size="md"
            :to="'/billing/invoices?search=' + encodeURIComponent(selectedPatient.invoice_no)"
          >
            <Icon name="credit-card" class="w-4 h-4" />
            <span>Open Invoice</span>
          </Button>
          <Button
            variant="primary"
            size="md"
            :to="{ path: '/patients/register', query: { patient_id: selectedPatient.id, uhid: selectedPatient.uhid } }"
          >
            <Icon name="plus" class="w-4 h-4" />
            <span>Book New Test Order</span>
          </Button>
        </div>
      </div>
    </Modal>
  </div>
</template>
