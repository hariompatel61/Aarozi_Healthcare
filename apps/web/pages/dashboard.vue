<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const api = useApi()
const loading = ref(true)

// Top KPI Metrics
const kpiCards = ref<any[]>([
  {
    title: 'Patients Today',
    value: '0',
    change: '+ 12%',
    icon: 'users',
    iconColor: 'text-blue-600 bg-blue-50',
    changeColor: 'text-emerald-600',
  },
  {
    title: 'Samples Collected',
    value: '0',
    change: '+ 18%',
    icon: 'beaker',
    iconColor: 'text-emerald-600 bg-emerald-50',
    changeColor: 'text-emerald-600',
  },
  {
    title: 'Reports Released',
    value: '0',
    change: '+ 16%',
    icon: 'document',
    iconColor: 'text-blue-600 bg-blue-50',
    changeColor: 'text-emerald-600',
  },
  {
    title: "Today's Collections",
    value: '₹ 0',
    change: '+ 16%',
    icon: 'currency',
    iconColor: 'text-emerald-600 bg-emerald-50',
    changeColor: 'text-emerald-600',
  },
])

// Test Status Breakdown
const testStatusBreakdown = ref<any[]>([
  { label: 'Received', count: 0, color: '#3b82f6', pill: 'bg-blue-500' },
  { label: 'Processing', count: 0, color: '#06b6d4', pill: 'bg-cyan-500' },
  { label: 'Completed', count: 0, color: '#10b981', pill: 'bg-emerald-500' },
  { label: 'Pending', count: 0, color: '#f59e0b', pill: 'bg-amber-500' },
  { label: 'Rejected', count: 0, color: '#ef4444', pill: 'bg-red-500' },
])

const totalSamples = computed(() => {
  return testStatusBreakdown.value.reduce((acc, curr) => acc + (curr.count || 0), 0)
})

// Reports Awaiting Approval
const reportsAwaitingApproval = ref<any[]>([])

// Recent Patients with Sample Collection and Report Generation times
const recentPatients = ref<any[]>([])
const isSeeAll = ref(false)
const patientSearch = ref('')

const displayedPatients = computed(() => {
  if (!patientSearch.value.trim()) return recentPatients.value
  const q = patientSearch.value.trim().toLowerCase()
  return recentPatients.value.filter(
    p =>
      p.patient_id.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      p.test.toLowerCase().includes(q)
  )
})

function toggleSeeAll() {
  isSeeAll.value = !isSeeAll.value
  loadDashboard()
}

// Blood Stock Alert
const bloodStockAlerts = ref<any[]>([])

async function loadDashboard() {
  loading.value = true
  try {
    const url = isSeeAll.value ? '/pathology/dashboard/summary?see_all=true' : '/pathology/dashboard/summary'
    const res: any = await api.get(url)
    if (res) {
      if (res.kpi_cards) kpiCards.value = res.kpi_cards
      if (res.test_status_breakdown) testStatusBreakdown.value = res.test_status_breakdown
      if (res.reports_awaiting_approval) reportsAwaitingApproval.value = res.reports_awaiting_approval
      if (res.recent_patients) recentPatients.value = res.recent_patients
      if (res.blood_stock_alerts) bloodStockAlerts.value = res.blood_stock_alerts
    }
  } catch (err) {
    console.error('Failed to load dashboard data from database:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Header Banner matching Screen 1 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">
          Dashboard &mdash; Operational Overview
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Daily lab operations, pending work, collections and blood stock status
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <NuxtLink
          to="/patients/register"
          class="btn-primary"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>New Patient</span>
        </NuxtLink>
      </div>
    </div>

    <!-- KPI Metric Cards matching Screen 1 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <div
        v-for="card in kpiCards"
        :key="card.title"
        class="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs flex items-center justify-between"
      >
        <div>
          <p class="text-xs font-medium text-slate-500">{{ card.title }}</p>
          <p class="text-2xl font-bold font-mono text-slate-900 mt-1 tracking-tight">{{ card.value }}</p>
          <p class="text-[11px] font-semibold flex items-center mt-1" :class="card.changeColor">
            <span>{{ card.change }}</span>
          </p>
        </div>

        <div class="h-10 w-10 rounded-lg flex items-center justify-center shrink-0" :class="card.iconColor">
          <!-- Users Icon -->
          <svg v-if="card.icon === 'users'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <!-- Beaker Icon -->
          <svg v-else-if="card.icon === 'beaker'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <!-- Document Icon -->
          <svg v-else-if="card.icon === 'document'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <!-- Currency Rupee Icon -->
          <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 8h6m-5 0a3 3 0 110 6H9l3 3m-3-9h6m-6 3h4" />
          </svg>
        </div>
      </div>
    </div>

    <!-- Middle Split Row matching Screen 1: Test Status Donut Chart (Left) + Reports Awaiting Approval (Right) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-3">
      <!-- Test Status Today (8 cols) -->
      <div class="lg:col-span-8 bg-white p-4 rounded-lg border border-slate-200 shadow-2xs flex flex-col justify-between">
        <div class="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
          <h2 class="text-xs font-bold text-slate-900 tracking-tight">Test Status (Today)</h2>
          <span class="text-[11px] text-slate-400">Real-time Lab Feed</span>
        </div>

        <div class="flex flex-col sm:flex-row items-center justify-around gap-4 py-2">
          <!-- Donut Graphic Representation matching Screen 1 -->
          <div class="relative flex items-center justify-center shrink-0">
            <!-- Simulated Donut Ring with SVG -->
            <svg class="h-32 w-32 -rotate-90 transform" viewBox="0 0 36 36">
              <path
                class="text-slate-100"
                stroke-width="3.8"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="text-blue-500"
                stroke-dasharray="21, 100"
                stroke-width="3.8"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="text-cyan-500"
                stroke-dasharray="37, 100"
                stroke-dashoffset="-21"
                stroke-width="3.8"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="text-emerald-500"
                stroke-dasharray="29, 100"
                stroke-dashoffset="-58"
                stroke-width="3.8"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="text-amber-500"
                stroke-dasharray="9, 100"
                stroke-dashoffset="-87"
                stroke-width="3.8"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="text-red-500"
                stroke-dasharray="3, 100"
                stroke-dashoffset="-96"
                stroke-width="3.8"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div class="absolute flex flex-col items-center justify-center">
              <span class="text-xl font-bold font-mono text-slate-900">{{ totalSamples }}</span>
              <span class="text-[9px] text-slate-500 font-medium tracking-tight">Total Samples</span>
            </div>
          </div>

          <!-- Breakdown Legend matching Screen 1 -->
          <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-xs w-full sm:w-auto">
            <div
              v-for="st in testStatusBreakdown"
              :key="st.label"
              class="flex items-center justify-between space-x-3"
            >
              <div class="flex items-center space-x-2">
                <span class="h-2 w-2 rounded-full shrink-0" :class="st.pill" />
                <span class="text-slate-600 font-medium">{{ st.label }}</span>
              </div>
              <span class="font-mono font-bold text-slate-900">{{ st.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Reports Awaiting Approval (4 cols) matching Screen 1 -->
      <div class="lg:col-span-4 bg-white p-4 rounded-lg border border-slate-200 shadow-2xs flex flex-col justify-between">
        <div class="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
          <div class="flex items-center space-x-1.5">
            <h2 class="text-xs font-bold text-slate-900 tracking-tight">Reports Awaiting Approval</h2>
            <span class="text-[10px] bg-red-100 text-red-700 font-bold px-1.5 py-0.2 rounded-full font-mono">12</span>
          </div>
          <NuxtLink to="/pathology/results" class="text-[11px] text-blue-600 hover:underline font-medium">
            View All &gt;
          </NuxtLink>
        </div>

        <div class="space-y-2 my-auto">
          <div
            v-for="rep in reportsAwaitingApproval"
            :key="rep.test"
            class="flex items-center justify-between text-xs p-1.5 rounded hover:bg-slate-50 transition"
          >
            <div class="flex items-center space-x-2">
              <span class="h-1.5 w-1.5 rounded-full bg-blue-500" />
              <span class="font-medium text-slate-700">{{ rep.test }}</span>
            </div>
            <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-[11px]">
              {{ rep.count }}
            </span>
          </div>
        </div>

        <div class="pt-2 border-t border-slate-100 mt-2">
          <NuxtLink
            to="/pathology/results"
            class="w-full py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded flex items-center justify-center transition"
          >
            Open Verification Workstation &rarr;
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Bottom Split Row matching Screen 1: Recent Patients (Left 8 cols) + Blood Stock Alert (Right 4 cols) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-3">
      <!-- Recent Patients Table (8 cols) -->
      <div class="lg:col-span-8 bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-2 mb-3 gap-2">
          <div class="flex items-center space-x-2">
            <h2 class="text-xs font-bold text-slate-900 tracking-tight">Recent Patients</h2>
            <span class="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono">
              {{ displayedPatients.length }} {{ isSeeAll ? 'Total' : 'Latest' }}
            </span>
          </div>

          <div class="flex items-center space-x-2">
            <!-- Inline Filter -->
            <div class="relative">
              <input
                v-model="patientSearch"
                type="text"
                placeholder="Filter patients..."
                class="pl-7 pr-2 py-1 text-[11px] bg-slate-50 border border-slate-200 rounded text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:bg-white w-40 transition"
              />
              <span class="absolute inset-y-0 left-0 flex items-center pl-2 text-slate-400 pointer-events-none">
                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </span>
            </div>

            <!-- See All Toggle Button -->
            <button
              type="button"
              class="px-2.5 py-1 text-[11px] font-semibold rounded border transition cursor-pointer"
              :class="isSeeAll ? 'bg-sky-600 text-white border-sky-700' : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'"
              @click="toggleSeeAll"
            >
              {{ isSeeAll ? 'Show Top 10' : 'See All' }}
            </button>

            <NuxtLink to="/patients" class="text-[11px] text-blue-600 hover:underline font-medium">
              Directory &gt;
            </NuxtLink>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-100 text-xs">
            <thead class="bg-slate-50 text-slate-500 font-semibold">
              <tr>
                <th class="px-3 py-2 text-left">#</th>
                <th class="px-3 py-2 text-left">Patient ID</th>
                <th class="px-3 py-2 text-left">Name</th>
                <th class="px-3 py-2 text-left">Age / Sex</th>
                <th class="px-3 py-2 text-left">Test / Package</th>
                <th class="px-3 py-2 text-left">Status</th>
                <th class="px-3 py-2 text-left">Sample Collection Time</th>
                <th class="px-3 py-2 text-left">Report Generation Time</th>
                <th class="px-3 py-2 text-right">Amount</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-if="loading">
                <td colspan="9" class="text-center py-6 text-slate-400 font-medium">
                  Loading clinical data from database...
                </td>
              </tr>
              <tr v-else-if="displayedPatients.length === 0">
                <td colspan="9" class="text-center py-6 text-slate-400 font-medium">
                  No patient records found in database
                </td>
              </tr>
              <tr
                v-for="p in displayedPatients"
                v-else
                :key="p.id"
                class="hover:bg-slate-50/80 transition-colors"
              >
                <td class="px-3 py-2 text-slate-400 font-mono">{{ p.id }}</td>
                <td class="px-3 py-2 font-mono font-semibold text-blue-700">{{ p.patient_id }}</td>
                <td class="px-3 py-2 font-medium text-slate-900">{{ p.name }}</td>
                <td class="px-3 py-2 text-slate-500 font-mono">{{ p.age_sex }}</td>
                <td class="px-3 py-2 text-slate-700">
                  <span class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-medium">
                    {{ p.test }}
                  </span>
                </td>
                <td class="px-3 py-2">
                  <span
                    :class="[
                      'inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-semibold border',
                      p.status.toLowerCase() === 'completed' || p.status.toLowerCase() === 'released' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : '',
                      p.status.toLowerCase() === 'processing' ? 'bg-cyan-50 text-cyan-700 border-cyan-200' : '',
                      p.status.toLowerCase() === 'collected' ? 'bg-blue-50 text-blue-700 border-blue-200' : '',
                      p.status.toLowerCase() === 'pending' || p.status.toLowerCase() === 'ordered' ? 'bg-amber-50 text-amber-700 border-amber-200' : ''
                    ]"
                  >
                    {{ p.status }}
                  </span>
                </td>
                <td class="px-3 py-2 font-mono text-slate-700">
                  <span class="inline-flex items-center space-x-1 text-[11px] font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                    <svg class="h-3 w-3 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{{ p.sample_collection_time || '-' }}</span>
                  </span>
                </td>
                <td class="px-3 py-2 font-mono text-slate-700">
                  <span
                    :class="[
                      'inline-flex items-center space-x-1 text-[11px] font-medium px-2 py-0.5 rounded border',
                      p.report_generation_time && p.report_generation_time !== 'Pending'
                        ? 'text-emerald-700 bg-emerald-50 border-emerald-100'
                        : 'text-amber-700 bg-amber-50 border-amber-100'
                    ]"
                  >
                    <svg class="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>{{ p.report_generation_time || 'Pending' }}</span>
                  </span>
                </td>
                <td class="px-3 py-2 text-right font-mono font-semibold text-slate-800">{{ p.amount }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Blood Stock Alert (4 cols) matching Screen 1 -->
      <div class="lg:col-span-4 bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
        <div class="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
          <div class="flex items-center space-x-1.5">
            <h2 class="text-xs font-bold text-slate-900 tracking-tight">Blood Stock Alert</h2>
          </div>
          <NuxtLink to="/blood_bank/inventory" class="text-[11px] text-blue-600 hover:underline font-medium">
            View All &gt;
          </NuxtLink>
        </div>

        <div class="space-y-1.5">
          <div
            v-for="b in bloodStockAlerts"
            :key="b.group"
            class="flex items-center justify-between text-xs py-1 px-2 rounded hover:bg-slate-50 transition"
          >
            <span class="font-bold font-mono text-slate-900 w-8">{{ b.group }}</span>
            <span class="font-mono text-slate-600 text-[11px]">{{ b.units }}</span>
            <span
              :class="[
                'px-1.5 py-0.2 rounded text-[10px] font-semibold border',
                b.badge
              ]"
            >
              {{ b.status }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
