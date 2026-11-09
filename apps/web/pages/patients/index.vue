<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const searchQuery = ref('')
const selectedGender = ref('All')
const selectedStatus = ref('All')

const api = useApi()
const loading = ref(true)
const patients = ref<PatientRecord[]>([])

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
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Top Action Bar matching Reference Design -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Patient Directory</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Universal patient identity lookup across clinical orders, results and billing ledgers
        </p>
      </div>

      <div>
        <NuxtLink
          to="/patients/register"
          class="btn-primary"
          title="Register new patient or walk-in (F2)"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>New Patient</span>
          <kbd class="ml-1 px-1.5 py-0.2 text-[9px] font-mono text-teal-100 bg-teal-800/60 rounded">F2</kbd>
        </NuxtLink>
      </div>
    </div>

    <!-- KPI Summary Pills with live data -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Total Patients</p>
        <p class="text-lg font-bold font-mono text-slate-900 mt-0.5">{{ patients.length }}</p>
      </div>
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Today's Intake</p>
        <p class="text-lg font-bold font-mono text-teal-600 mt-0.5">{{ patients.length }}</p>
      </div>
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Active In-Progress</p>
        <p class="text-lg font-bold font-mono text-amber-600 mt-0.5">{{ patients.filter(p => ['Processing', 'Collected', 'Pending'].includes(p.status)).length }}</p>
      </div>
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Completed Cases</p>
        <p class="text-lg font-bold font-mono text-emerald-600 mt-0.5">{{ patients.filter(p => p.status === 'Completed').length }}</p>
      </div>
    </div>

    <!-- Search & Filters Header -->
    <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center space-x-2 flex-1 min-w-[260px] max-w-lg">
        <div class="relative flex-1">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search by UHID, Patient Name, Mobile..."
            class="input-faang w-full pl-9 pr-8"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="absolute inset-y-0 right-0 flex items-center pr-2.5 text-slate-400 hover:text-slate-600 cursor-pointer"
            title="Clear search"
            @click="searchQuery = ''"
          >
            <span class="text-sm leading-none">&times;</span>
          </button>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <!-- Gender Filter -->
        <select
          v-model="selectedGender"
          class="select-faang input-faang text-slate-700 cursor-pointer text-xs"
        >
          <option value="All">All Genders</option>
          <option value="M">Male (M)</option>
          <option value="F">Female (F)</option>
        </select>

        <!-- Status Filter -->
        <select
          v-model="selectedStatus"
          class="select-faang input-faang text-slate-700 cursor-pointer text-xs"
        >
          <option value="All">All Statuses</option>
          <option value="Collected">Collected</option>
          <option value="Processing">Processing</option>
          <option value="Completed">Completed</option>
          <option value="Pending">Pending</option>
        </select>

        <!-- See All / Reset Filter Button -->
        <button
          type="button"
          class="btn-secondary"
          title="Reset all filters"
          @click="searchQuery = ''; selectedGender = 'All'; selectedStatus = 'All'"
        >
          Reset Filters
        </button>
      </div>
    </div>

    <!-- Patients Data Table matching Reference Design -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="w-12 px-3 py-2.5 text-center">#</th>
              <th class="px-4 py-2.5 text-left">Patient ID (UHID)</th>
              <th class="px-4 py-2.5 text-left">Name</th>
              <th class="px-4 py-2.5 text-left">Age / Sex</th>
              <th class="px-4 py-2.5 text-left">Mobile Number</th>
              <th class="px-4 py-2.5 text-left">Prescribed By</th>
              <th class="px-4 py-2.5 text-left">Ordered Tests</th>
              <th class="px-4 py-2.5 text-left">Status</th>
              <th class="px-4 py-2.5 text-right">Invoice &amp; Bill</th>
              <th class="px-4 py-2.5 text-right">Time</th>
              <th class="px-4 py-2.5 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="11" class="text-center py-8 text-slate-400 font-medium">
                Loading patients from database...
              </td>
            </tr>
            <tr v-else-if="filteredPatients.length === 0">
              <td colspan="11" class="text-center py-8 text-slate-400 font-medium">
                No patients found in directory
              </td>
            </tr>
            <tr
              v-for="(p, idx) in paginatedPatients"
              v-else
              :key="p.id"
              class="hover:bg-blue-50/40 transition-colors"
            >
              <td class="px-3 py-2.5 text-center font-mono font-bold text-slate-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>
              <td class="px-4 py-2.5 font-mono font-semibold text-blue-700">
                <NuxtLink :to="'/billing/invoices?search=' + encodeURIComponent(p.uhid)" class="hover:underline" title="View Patient Invoices">
                  {{ p.uhid }}
                </NuxtLink>
              </td>
              <td class="px-4 py-2.5 font-medium text-slate-900">
                {{ p.name }}
              </td>
              <td class="px-4 py-2.5 text-slate-600 font-mono">
                {{ p.age }} / {{ p.gender }}
              </td>
              <td class="px-4 py-2.5 text-slate-600 font-mono">
                {{ p.mobile }}
              </td>
              <td class="px-4 py-2.5 text-slate-700">
                <NuxtLink
                  v-if="p.referral_doctor && p.referral_doctor !== 'Direct Walk-in'"
                  :to="'/billing/referrals?search=' + encodeURIComponent(p.referral_doctor)"
                  class="text-blue-700 font-medium hover:underline inline-flex items-center space-x-1"
                  title="View Referring Doctor Details"
                >
                  <span>{{ p.referral_doctor }}</span>
                </NuxtLink>
                <span v-else class="text-slate-400 italic">Direct Walk-in</span>
              </td>
              <td class="px-4 py-2.5 text-slate-700">
                <span class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-800 font-medium">
                  {{ p.tests }}
                </span>
              </td>
              <td class="px-4 py-2.5">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border',
                    p.status === 'Completed' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : '',
                    p.status === 'Processing' ? 'bg-blue-50 text-blue-700 border-blue-200' : '',
                    p.status === 'Collected' ? 'bg-teal-50 text-teal-700 border-teal-200' : '',
                    p.status === 'Pending' ? 'bg-amber-50 text-amber-700 border-amber-200' : ''
                  ]"
                >
                  {{ p.status }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-right font-mono">
                <NuxtLink
                  v-if="p.invoice_no"
                  :to="'/billing/invoices?search=' + encodeURIComponent(p.invoice_no)"
                  class="text-blue-700 font-semibold hover:underline block"
                  title="View Invoice"
                >
                  ₹{{ p.amount.toLocaleString('en-IN') }}
                  <span class="block text-[10px] text-slate-400 font-normal">{{ p.invoice_no }}</span>
                </NuxtLink>
                <span v-else class="text-slate-400 font-semibold">₹{{ p.amount }}</span>
              </td>
              <td class="px-4 py-2.5 text-right text-slate-500 font-mono">
                {{ p.time }}
              </td>
              <td class="px-4 py-2.5 text-center space-x-2 whitespace-nowrap">
                <NuxtLink
                  :to="'/billing/invoices?search=' + encodeURIComponent(p.uhid)"
                  class="text-emerald-700 hover:text-emerald-900 font-semibold hover:underline text-[11px]"
                >
                  View Bill
                </NuxtLink>
                <NuxtLink
                  :to="{ path: '/patients/register', query: { patient_id: p.id, uhid: p.uhid } }"
                  class="text-blue-600 hover:text-blue-800 font-bold hover:underline text-[11px]"
                >
                  New Order
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
        :total-items="filteredPatients.length"
      />
    </div>
  </div>
</template>
