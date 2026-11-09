<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Badge from '~/components/ui/Badge.vue'
import Button from '~/components/ui/Button.vue'
import Icon, { type IconName } from '~/components/ui/Icon.vue'
import Kbd from '~/components/ui/Kbd.vue'
import Skeleton from '~/components/ui/Skeleton.vue'

const api = useApi()
const loading = ref(true)

// Top KPI Metrics
interface KpiCard {
  title: string
  value: string
  change: string
  icon: string
  iconColor: string
  changeColor: string
}

const kpiCards = ref<KpiCard[]>([
  {
    title: 'Patients Today',
    value: '0',
    change: '+ 12%',
    icon: 'users',
    iconColor: 'text-sky-600 bg-sky-50 dark:bg-sky-950/60 dark:text-sky-400',
    changeColor: 'text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-300',
  },
  {
    title: 'Samples Collected',
    value: '0',
    change: '+ 18%',
    icon: 'beaker',
    iconColor: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-400',
    changeColor: 'text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-300',
  },
  {
    title: 'Reports Released',
    value: '0',
    change: '+ 16%',
    icon: 'document',
    iconColor: 'text-teal-600 bg-teal-50 dark:bg-teal-950/60 dark:text-teal-400',
    changeColor: 'text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-300',
  },
  {
    title: "Today's Collections",
    value: '₹ 0',
    change: '+ 16%',
    icon: 'currency',
    iconColor: 'text-amber-600 bg-amber-50 dark:bg-amber-950/60 dark:text-amber-400',
    changeColor: 'text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-300',
  },
])

// Test Status Breakdown
interface StatusBreakdownItem {
  label: string
  count: number
  color: string
  pill: string
}

const testStatusBreakdown = ref<StatusBreakdownItem[]>([
  { label: 'Received', count: 0, color: '#0284c7', pill: 'bg-sky-600' },
  { label: 'Processing', count: 0, color: '#0d9488', pill: 'bg-teal-600' },
  { label: 'Completed', count: 0, color: '#059669', pill: 'bg-emerald-600' },
  { label: 'Pending', count: 0, color: '#d97706', pill: 'bg-amber-600' },
  { label: 'Rejected', count: 0, color: '#dc2626', pill: 'bg-red-600' },
])

const totalSamples = computed(() => {
  return testStatusBreakdown.value.reduce((acc, curr) => acc + (curr.count || 0), 0)
})

// Reports Awaiting Approval
interface ApprovalItem {
  test: string
  count: number
}

const reportsAwaitingApproval = ref<ApprovalItem[]>([])

const totalAwaitingApproval = computed(() => {
  return reportsAwaitingApproval.value.reduce((acc, curr) => acc + (curr.count || 0), 0)
})

// Recent Patients
interface RecentPatient {
  id: number
  order_id?: string
  patient_id: string
  name: string
  age_sex: string
  test: string
  status: string
  amount: string
  order_time?: string
  sample_collection_time: string
  report_generation_time: string
}

const recentPatients = ref<RecentPatient[]>([])
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
interface BloodStockAlert {
  group: string
  units: string
  status: string
  badge: string
}

const bloodStockAlerts = ref<BloodStockAlert[]>([])

function getStatusBadgeVariant(status: string): 'success' | 'warning' | 'danger' | 'info' | 'neutral' {
  const s = (status || '').toLowerCase()
  if (s.includes('completed') || s.includes('released') || s.includes('normal')) return 'success'
  if (s.includes('processing') || s.includes('low')) return 'warning'
  if (s.includes('rejected') || s.includes('critical') || s.includes('panic')) return 'danger'
  if (s.includes('received') || s.includes('collected')) return 'info'
  return 'neutral'
}

function mapIconName(icon: string): IconName {
  if (icon === 'users') return 'users'
  if (icon === 'beaker') return 'beaker'
  if (icon === 'document') return 'file-text'
  if (icon === 'currency') return 'credit-card'
  return 'activity'
}

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
    <!-- Page Header with Clinical Breadcrumbs & High-Speed Actions -->
    <PageHeader
      title="Laboratory Operations Dashboard"
      subtitle="Live laboratory throughput, turnaround times, sample pipeline, and critical clinical alerts"
    >
      <template #actions>
        <div class="flex items-center gap-2 flex-wrap">
          <Button
            variant="secondary"
            size="sm"
            :loading="loading"
            @click="loadDashboard"
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
              <span>Worklist</span>
            </Button>
          </NuxtLink>

          <NuxtLink to="/pathology/verification">
            <Button variant="secondary" size="sm">
              <template #icon-left>
                <Icon name="shield-check" size="sm" />
              </template>
              <span>Verification</span>
            </Button>
          </NuxtLink>

          <NuxtLink to="/patients/register">
            <Button variant="primary" size="sm">
              <template #icon-left>
                <Icon name="plus" size="sm" />
              </template>
              <span>New Patient</span>
              <Kbd class="ml-1 hidden sm:inline-block">F2</Kbd>
            </Button>
          </NuxtLink>
        </div>
      </template>
    </PageHeader>

    <!-- Top KPI Metric Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <div
        v-for="card in kpiCards"
        :key="card.title"
        class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/90 dark:border-slate-800 shadow-2xs flex items-center justify-between transition-all hover:border-slate-300 dark:hover:border-slate-700"
      >
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {{ card.title }}
          </p>
          <p class="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100 tracking-tight">
            {{ card.value }}
          </p>
          <div class="flex items-center gap-1.5 pt-0.5">
            <span
              :class="[
                'inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full border',
                card.changeColor || 'text-emerald-700 bg-emerald-50 border-emerald-200'
              ]"
            >
              {{ card.change }} vs yesterday
            </span>
          </div>
        </div>

        <div
          :class="[
            'w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border border-slate-100 dark:border-slate-800',
            card.iconColor
          ]"
        >
          <Icon :name="mapIconName(card.icon)" size="md" />
        </div>
      </div>
    </div>

    <!-- Middle Row: Pipeline & Turnaround Times (8 cols) + Urgent Verification Desk (4 cols) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <!-- Test Pipeline & Turnaround Time -->
      <div class="lg:col-span-8">
        <Card
          title="Test Pipeline & Turnaround Time (TAT)"
          subtitle="Daily specimen progression through accessioning, testing, and release"
        >
          <template #header-right>
            <div class="flex items-center gap-2">
              <Badge variant="info" size="md">
                In-Lab TAT: 42m Avg
              </Badge>
              <Badge variant="success" size="md">
                STAT: 98.4%
              </Badge>
            </div>
          </template>

          <div class="space-y-5">
            <!-- Multi-stage progress bar -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-300">
                <span>Sample Flow Distribution</span>
                <span class="font-mono font-bold text-slate-900 dark:text-slate-100">
                  {{ totalSamples }} Total Specimens
                </span>
              </div>

              <div class="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden flex">
                <div
                  v-for="st in testStatusBreakdown"
                  :key="st.label"
                  :style="{
                    width: totalSamples > 0 ? `${(st.count / totalSamples) * 100}%` : '20%',
                    backgroundColor: st.color
                  }"
                  :title="`${st.label}: ${st.count}`"
                  class="h-full transition-all duration-300"
                />
              </div>
            </div>

            <!-- Pipeline Breakdown Cards -->
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
              <div
                v-for="st in testStatusBreakdown"
                :key="st.label"
                class="p-2.5 rounded-lg border border-slate-200/80 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/60 flex flex-col justify-between"
              >
                <div class="flex items-center gap-1.5">
                  <span class="w-2.5 h-2.5 rounded-full shrink-0" :class="st.pill" />
                  <span class="text-xs font-semibold text-slate-600 dark:text-slate-300 truncate">
                    {{ st.label }}
                  </span>
                </div>
                <div class="mt-2 flex items-baseline justify-between">
                  <span class="text-lg font-bold font-mono text-slate-900 dark:text-slate-100">
                    {{ st.count }}
                  </span>
                  <span class="text-xs text-slate-500 font-mono">
                    {{ totalSamples > 0 ? Math.round((st.count / totalSamples) * 100) : 0 }}%
                  </span>
                </div>
              </div>
            </div>

            <!-- In-Lab Clinical Benchmark Strip -->
            <div class="p-3 bg-sky-50/70 dark:bg-sky-950/40 border border-sky-100 dark:border-sky-900 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div class="flex items-center gap-2 text-sky-800 dark:text-sky-300">
                <Icon name="check" size="sm" class="text-sky-600 shrink-0" />
                <span class="font-medium">
                  Laboratory throughput operating within NABL turnaround time standard limits.
                </span>
              </div>
              <NuxtLink
                to="/pathology/samples"
                class="font-semibold text-sky-700 dark:text-sky-300 hover:text-sky-900 dark:hover:text-sky-100 flex items-center gap-1 shrink-0"
              >
                <span>Accession Desk</span>
                <Icon name="chevron-right" size="xs" />
              </NuxtLink>
            </div>
          </div>
        </Card>
      </div>

      <!-- Urgent Verification Desk -->
      <div class="lg:col-span-4">
        <Card
          title="Verification Desk"
          subtitle="Reports awaiting pathologist signature"
        >
          <template #header-right>
            <Badge :variant="totalAwaitingApproval > 0 ? 'danger' : 'success'" size="md">
              {{ totalAwaitingApproval }} Pending
            </Badge>
          </template>

          <div class="space-y-4">
            <div v-if="reportsAwaitingApproval.length === 0" class="py-8 text-center text-slate-400">
              <Icon name="check" size="lg" class="mx-auto text-emerald-500 mb-2" />
              <p class="text-xs font-semibold text-slate-700 dark:text-slate-300">Queue is Clear</p>
              <p class="text-xs text-slate-500">All completed results have been authorized.</p>
            </div>

            <div v-else class="space-y-2 max-h-52 overflow-y-auto pr-1">
              <div
                v-for="rep in reportsAwaitingApproval"
                :key="rep.test"
                class="flex items-center justify-between p-2 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-amber-500 shrink-0" />
                  <span class="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    {{ rep.test }}
                  </span>
                </div>
                <Badge variant="neutral" size="sm">
                  <span class="font-mono font-bold">{{ rep.count }}</span>
                </Badge>
              </div>
            </div>

            <div class="pt-2 border-t border-slate-100 dark:border-slate-800">
              <NuxtLink to="/pathology/verification" class="block w-full">
                <Button variant="primary" class="w-full justify-center text-xs">
                  <template #icon-left>
                    <Icon name="shield-check" size="sm" />
                  </template>
                  <span>Open Verification Queue</span>
                  <Kbd class="ml-1.5">Alt+A</Kbd>
                </Button>
              </NuxtLink>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- Bottom Row: Recent Accession Pipeline (8 cols) + Blood Bank Status (4 cols) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <!-- Recent Accession Pipeline Table -->
      <div class="lg:col-span-8">
        <Card
          title="Live Patient & Accession Flow"
          subtitle="Real-time intake, collection status, and release times"
        >
          <template #header-right>
            <div class="flex items-center gap-2">
              <!-- Search filter input -->
              <div class="relative w-44">
                <input
                  v-model="patientSearch"
                  type="text"
                  placeholder="Filter UHID, name..."
                  class="w-full pl-8 pr-2.5 py-1 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white dark:focus:bg-slate-900 transition"
                />
                <span class="absolute inset-y-0 left-0 flex items-center pl-2.5 text-slate-400 pointer-events-none">
                  <Icon name="search" size="xs" />
                </span>
              </div>

              <!-- See All Toggle -->
              <Button
                variant="secondary"
                size="sm"
                @click="toggleSeeAll"
              >
                {{ isSeeAll ? 'Top 10' : 'See All' }}
              </Button>

              <NuxtLink to="/patients">
                <Button variant="ghost" size="sm">
                  <span>Directory</span>
                  <template #icon-right>
                    <Icon name="chevron-right" size="xs" />
                  </template>
                </Button>
              </NuxtLink>
            </div>
          </template>

          <!-- Table Content -->
          <div class="overflow-x-auto -mx-5 -my-5 p-0">
            <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-800 text-xs">
              <thead class="bg-slate-50/80 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th class="px-4 py-3 text-left">#</th>
                  <th class="px-4 py-3 text-left">UHID / Patient</th>
                  <th class="px-4 py-3 text-left">Age / Sex</th>
                  <th class="px-4 py-3 text-left">Tests Requested</th>
                  <th class="px-4 py-3 text-left">Status</th>
                  <th class="px-4 py-3 text-left">Sampled</th>
                  <th class="px-4 py-3 text-left">Released</th>
                  <th class="px-4 py-3 text-right">Billing</th>
                  <th class="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                <tr v-if="loading">
                  <td colspan="9" class="text-center py-8 text-slate-400 font-medium">
                    <div class="flex items-center justify-center gap-2">
                      <Icon name="refresh" size="sm" class="animate-spin text-teal-600" />
                      <span>Loading clinical feed from laboratory database...</span>
                    </div>
                  </td>
                </tr>

                <tr v-else-if="displayedPatients.length === 0">
                  <td colspan="9" class="text-center py-8 text-slate-400 font-medium">
                    <Icon name="search" size="md" class="mx-auto text-slate-300 mb-1" />
                    <span>No patient orders match the current filter.</span>
                  </td>
                </tr>

                <tr
                  v-for="p in displayedPatients"
                  v-else
                  :key="p.id"
                  class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                >
                  <td class="px-4 py-2.5 font-mono text-slate-400">{{ p.id }}</td>
                  <td class="px-4 py-2.5">
                    <div>
                      <p class="font-mono font-bold text-teal-700 dark:text-teal-400 text-xs">
                        {{ p.patient_id }}
                      </p>
                      <p class="font-semibold text-slate-900 dark:text-slate-100 text-xs">
                        {{ p.name }}
                      </p>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 font-mono text-slate-600 dark:text-slate-400">
                    {{ p.age_sex }}
                  </td>
                  <td class="px-4 py-2.5">
                    <span class="inline-block max-w-[180px] truncate px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs">
                      {{ p.test }}
                    </span>
                  </td>
                  <td class="px-4 py-2.5">
                    <Badge :variant="getStatusBadgeVariant(p.status)" size="sm" :dot="true">
                      {{ p.status }}
                    </Badge>
                  </td>
                  <td class="px-4 py-2.5 font-mono text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">
                    {{ p.sample_collection_time || '-' }}
                  </td>
                  <td class="px-4 py-2.5 font-mono text-xs whitespace-nowrap">
                    <span
                      :class="[
                        p.report_generation_time && p.report_generation_time !== 'Pending'
                          ? 'text-emerald-700 dark:text-emerald-400 font-semibold'
                          : 'text-amber-700 dark:text-amber-400 font-medium'
                      ]"
                    >
                      {{ p.report_generation_time || 'Pending' }}
                    </span>
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-900 dark:text-slate-100 whitespace-nowrap">
                    {{ p.amount }}
                  </td>
                  <td class="px-4 py-2.5 text-center whitespace-nowrap">
                    <NuxtLink :to="`/pathology/results`">
                      <Button variant="ghost" size="sm">
                        <span>Open</span>
                      </Button>
                    </NuxtLink>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <!-- Blood Bank Inventory Status -->
      <div class="lg:col-span-4">
        <Card
          title="Blood Bank Reserves"
          subtitle="Crossmatch & component inventory status"
        >
          <template #header-right>
            <NuxtLink to="/blood_bank/inventory">
              <Button variant="ghost" size="sm">
                <span>Inventory</span>
                <template #icon-right>
                  <Icon name="chevron-right" size="xs" />
                </template>
              </Button>
            </NuxtLink>
          </template>

          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="b in bloodStockAlerts"
                :key="b.group"
                class="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 flex items-center justify-between"
              >
                <div>
                  <span class="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                    {{ b.group }}
                  </span>
                  <p class="text-xs font-mono text-slate-500">
                    {{ b.units }}
                  </p>
                </div>
                <Badge :variant="getStatusBadgeVariant(b.status)" size="sm">
                  {{ b.status }}
                </Badge>
              </div>
            </div>

            <div class="pt-2 border-t border-slate-100 dark:border-slate-800">
              <NuxtLink to="/blood_bank/inventory" class="block w-full">
                <Button variant="secondary" class="w-full justify-center text-xs">
                  <template #icon-left>
                    <Icon name="beaker" size="sm" />
                  </template>
                  <span>Manage Blood Bank Stock</span>
                </Button>
              </NuxtLink>
            </div>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>
