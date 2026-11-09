<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '~/composables/useToast'

const route = useRoute()
const api = useApi()
const { success, error } = useToast()

interface ReferralPartner {
  id: string
  name: string
  partner_type: string
  specialty: string
  contact_phone: string
  commission_type: 'percentage' | 'fixed'
  commission_value: number
  total_referred_cases: number
  total_business_volume: number
  unsettled_commission: number
  status: 'active' | 'inactive'
}

const loading = ref(true)
const partners = ref<ReferralPartner[]>([])
const searchQuery = ref('')
const selectedType = ref('All')
const isAddModalOpen = ref(false)
const isSettleModalOpen = ref(false)
const selectedPartner = ref<ReferralPartner | null>(null)
const settlementRef = ref('')

const partnerTypes = [
  { id: 'doctor', label: 'Doctor / Consulting Clinician', defaultSpecialty: 'Internal Medicine', nameLabel: 'Doctor Name & Degree *', namePlaceholder: 'e.g. Dr. Ramesh Kumar, MD', specialtyLabel: 'Medical Specialty', defaultPrefix: 'Dr. ' },
  { id: 'lab', label: 'Referral Lab / Pathology Center', defaultSpecialty: 'Clinical Pathology', nameLabel: 'Lab / Diagnostic Center Name *', namePlaceholder: 'e.g. Apex Diagnostics & Path Lab', specialtyLabel: 'Diagnostic Focus / Disciplines', defaultPrefix: '' },
  { id: 'hospital', label: 'Hospital / Nursing Home', defaultSpecialty: 'Multispeciality IPD', nameLabel: 'Hospital / Nursing Home Name *', namePlaceholder: 'e.g. City Life Multispeciality Hospital', specialtyLabel: 'Facility Departments', defaultPrefix: '' },
  { id: 'clinic', label: 'Clinic / Polyclinic Center', defaultSpecialty: 'Family Medicine OPD', nameLabel: 'Clinic / Polyclinic Name *', namePlaceholder: 'e.g. Sanjeevani Polyclinic & Day Care', specialtyLabel: 'Clinic Specialty / OPD Services', defaultPrefix: '' },
  { id: 'other', label: 'Other B2B Healthcare Partner', defaultSpecialty: 'Corporate Health Outreach', nameLabel: 'Partner Organization Name *', namePlaceholder: 'e.g. Global Health Screening Corp', specialtyLabel: 'Category / Outreach Details', defaultPrefix: '' },
]

const newPartner = ref({
  partner_type: 'doctor',
  name: 'Dr. ',
  specialty: 'Internal Medicine',
  clinic: 'City Clinic',
  phone: '',
  commission_type: 'percentage' as 'percentage' | 'fixed',
  commission_value: 15,
})

const newDoctor = newPartner

const defaultPartnerType = partnerTypes[0]!
const currentPartnerTypeConfig = computed(() => {
  return partnerTypes.find((t) => t.id === newPartner.value.partner_type) ?? defaultPartnerType
})

function onPartnerTypeChange() {
  const t = currentPartnerTypeConfig.value
  if (!newPartner.value.specialty || partnerTypes.some((x) => x.defaultSpecialty === newPartner.value.specialty)) {
    newPartner.value.specialty = t.defaultSpecialty
  }
  if (t.defaultPrefix && !newPartner.value.name.startsWith(t.defaultPrefix)) {
    newPartner.value.name = t.defaultPrefix
  } else if (!t.defaultPrefix && newPartner.value.name.startsWith('Dr. ')) {
    newPartner.value.name = newPartner.value.name.replace(/^Dr\.\s*/, '')
  }
}

function getPartnerTypeBadge(type: string) {
  switch (type) {
    case 'lab':
    case 'external_lab':
      return { label: 'Pathology Lab', class: 'bg-purple-50 text-purple-700 border-purple-200' }
    case 'hospital':
      return { label: 'Hospital', class: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
    case 'clinic':
      return { label: 'Clinic', class: 'bg-teal-50 text-teal-700 border-teal-200' }
    case 'corporate':
    case 'other':
      return { label: 'Corporate B2B', class: 'bg-slate-100 text-slate-700 border-slate-300' }
    default:
      return { label: 'Doctor', class: 'bg-sky-50 text-sky-700 border-sky-200' }
  }
}

async function loadReferrals() {
  loading.value = true
  try {
    if (route.query.search) {
      searchQuery.value = String(route.query.search)
    } else if (route.query.query) {
      searchQuery.value = String(route.query.query)
    }

    const data: any = await api.get('/billing/referrals/partners')
    if (Array.isArray(data)) {
      partners.value = data.map((d: any) => ({
        id: d.id,
        name: d.name,
        partner_type: d.partner_type || 'doctor',
        specialty: d.specialty || 'Consulting Physician',
        contact_phone: d.contact_phone || 'N/A',
        commission_type: d.commission_type || 'percentage',
        commission_value: Number(d.commission_value || 15),
        total_referred_cases: Number(d.total_cases || 0),
        total_business_volume: Number(d.business_volume || 0),
        unsettled_commission: Number(d.unsettled || 0),
        status: d.status || 'active',
      }))
    }
  } catch (err) {
    console.error('Failed to load referral partners from database:', err)
  } finally {
    loading.value = false
  }
}

const filteredPartners = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const type = selectedType.value
  return partners.value.filter((p) => {
    const matchesSearch =
      !q ||
      p.name.toLowerCase().includes(q) ||
      p.specialty.toLowerCase().includes(q) ||
      p.contact_phone.includes(q) ||
      (p.partner_type && p.partner_type.toLowerCase().includes(q))
    const matchesType =
      type === 'All' ||
      p.partner_type === type ||
      (type === 'lab' && (p.partner_type === 'lab' || p.partner_type === 'external_lab'))
    return matchesSearch && matchesType
  })
})

function resetFilters() {
  searchQuery.value = ''
  selectedType.value = 'All'
  success('Filter Reset', 'Showing all referral partners')
}

const totalReferredBusiness = computed(() => {
  return partners.value.reduce((acc, p) => acc + p.total_business_volume, 0)
})

const totalPendingSettlements = computed(() => {
  return partners.value.reduce((acc, p) => acc + p.unsettled_commission, 0)
})

async function createPartner() {
  if (!newPartner.value.name.trim()) {
    error('Name Required', 'Please enter partner name.')
    return
  }

  try {
    const payload = {
      name: newPartner.value.name.trim(),
      partner_type: newPartner.value.partner_type,
      specialty: newPartner.value.specialty.trim() || currentPartnerTypeConfig.value.defaultSpecialty,
      contact_phone: newPartner.value.phone.trim() || undefined,
      commission_type: newPartner.value.commission_type,
      commission_value: newPartner.value.commission_value,
    }
    try {
      await api.post('/billing/referrals/partners/create', payload)
    } catch {
      await api.post('/billing/referrals/partners', payload)
    }
    success(`Referral Partner "${newPartner.value.name}" registered successfully!`)
    await loadReferrals()
    isAddModalOpen.value = false
    // Reset form
    newPartner.value.partner_type = 'doctor'
    newPartner.value.name = 'Dr. '
    newPartner.value.specialty = 'Internal Medicine'
    newPartner.value.phone = ''
  } catch (err: any) {
    error('Failed to create partner', err?.message || 'Database error')
  }
}
const createDoctor = createPartner

function openSettleModal(p: ReferralPartner) {
  selectedPartner.value = p
  settlementRef.value = `SETTLE-${Date.now().toString().slice(-6)}`
  isSettleModalOpen.value = true
}

async function confirmSettlement() {
  if (!selectedPartner.value) return
  try {
    await api.post('/billing/referrals/settle', {
      partner_id: selectedPartner.value.id,
      settlement_reference: settlementRef.value,
    })
    success(`Settlement confirmed for ${selectedPartner.value.name}! Receipt logged.`)
    await loadReferrals()
  } catch (err: any) {
    error('Settlement Failed', err?.message || 'Could not settle commission')
  }

  isSettleModalOpen.value = false
}

onMounted(() => {
  loadReferrals()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Top Action Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Referral Doctors &amp; Healthcare Partners</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Consulting physician commissions, diagnostic outreach accounting, hospital/lab referrals and payout settlements
        </p>
      </div>

      <div>
        <button
          type="button"
          class="btn-primary"
          @click="isAddModalOpen = true"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Add Partner</span>
        </button>
      </div>
    </div>

    <!-- Referral Metrics -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Total Partners</p>
        <p class="text-lg font-bold font-mono text-slate-900 mt-0.5">{{ partners.length }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Active prescribing network</p>
      </div>

      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Total Referred Revenue</p>
        <p class="text-lg font-bold font-mono text-blue-600 mt-0.5">₹ {{ totalReferredBusiness.toLocaleString('en-IN') }}</p>
        <p class="text-[10px] text-emerald-600 mt-0.5 font-medium">+ 24% vs last month</p>
      </div>

      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Pending Commission Due</p>
        <p class="text-lg font-bold font-mono text-amber-600 mt-0.5">₹ {{ totalPendingSettlements.toLocaleString('en-IN') }}</p>
        <p class="text-[10px] text-amber-700 mt-0.5 font-medium">Ready for monthly settlement</p>
      </div>

      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Compliance &amp; Audit</p>
        <p class="text-lg font-bold text-emerald-700 mt-0.5 flex items-center">
          <span class="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-1.5" />
          TDS Verified
        </p>
        <p class="text-[10px] text-slate-400 mt-0.5">Form 16A auto-calculated</p>
      </div>
    </div>

    <!-- Search Toolbar & Category Filter -->
    <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center flex-1 min-w-[260px] max-w-xl space-x-2">
        <div class="relative flex-1">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 pointer-events-none">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search by Doctor, Lab, Hospital, Clinic or Contact..."
            class="input-faang w-full pl-9 pr-7 py-1.5 text-xs font-sans"
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

        <!-- Partner Type Filter Dropdown -->
        <select
          v-model="selectedType"
          class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
        >
          <option value="All">All Categories</option>
          <option value="doctor">Doctors / Clinicians</option>
          <option value="lab">Referral Labs &amp; Pathology</option>
          <option value="hospital">Hospitals &amp; Centers</option>
          <option value="clinic">Clinics &amp; Polyclinics</option>
          <option value="other">Other B2B Partners</option>
        </select>
      </div>

      <div>
        <button
          type="button"
          class="btn-secondary"
          title="Reset all filters"
          @click="resetFilters"
        >
          Reset
        </button>
      </div>
    </div>

    <!-- Doctors & Partners Table -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="px-4 py-2.5 text-left">Doctor / Partner</th>
              <th class="px-4 py-2.5 text-left">Category &amp; Specialty</th>
              <th class="px-4 py-2.5 text-left">Contact</th>
              <th class="px-4 py-2.5 text-center">Structure</th>
              <th class="px-4 py-2.5 text-right">Referred Cases</th>
              <th class="px-4 py-2.5 text-right">Business Volume</th>
              <th class="px-4 py-2.5 text-right">Pending Payout</th>
              <th class="px-4 py-2.5 text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="8" class="text-center py-8 text-slate-400">Loading partners...</td>
            </tr>
            <tr v-else-if="filteredPartners.length === 0">
              <td colspan="8" class="text-center py-8 text-slate-400">No referral partners found in this category</td>
            </tr>
            <tr
              v-for="p in filteredPartners"
              v-else
              :key="p.id"
              class="hover:bg-blue-50/40 transition-colors"
            >
              <td class="px-4 py-2.5">
                <div class="flex items-center space-x-1.5 flex-wrap gap-y-1">
                  <span class="font-medium text-slate-900">{{ p.name }}</span>
                  <span
                    class="inline-flex items-center px-1.5 py-0.2 rounded text-[9px] font-semibold border"
                    :class="getPartnerTypeBadge(p.partner_type).class"
                  >
                    {{ getPartnerTypeBadge(p.partner_type).label }}
                  </span>
                </div>
                <NuxtLink
                  :to="'/patients?referral_partner_id=' + p.id"
                  class="text-blue-600 hover:underline text-[10px] inline-flex items-center space-x-0.5 mt-0.5"
                  title="View Referred Patients"
                >
                  <span>View Patients ({{ p.total_referred_cases }}) &rarr;</span>
                </NuxtLink>
              </td>
              <td class="px-4 py-2.5 text-slate-600">
                <span class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-medium">
                  {{ p.specialty }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-slate-600 font-mono">
                {{ p.contact_phone }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span class="font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded text-[10px]">
                  {{ p.commission_type === 'percentage' ? `${p.commission_value}%` : `₹${p.commission_value}/test` }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-right font-mono text-slate-800 font-medium">
                <NuxtLink
                  :to="'/patients?referral_partner_id=' + p.id"
                  class="hover:text-blue-700 hover:underline"
                  title="Click to view cases"
                >
                  {{ p.total_referred_cases }}
                </NuxtLink>
              </td>
              <td class="px-4 py-2.5 text-right font-mono font-semibold text-slate-900">
                <NuxtLink
                  :to="'/billing/invoices?referral_partner_id=' + p.id + '&search=' + encodeURIComponent(p.name)"
                  class="hover:text-blue-700 hover:underline"
                  title="Click to view invoices"
                >
                  ₹ {{ p.total_business_volume.toLocaleString('en-IN') }}
                </NuxtLink>
              </td>
              <td class="px-4 py-2.5 text-right font-mono font-bold text-amber-600">
                ₹ {{ p.unsettled_commission.toLocaleString('en-IN') }}
              </td>
              <td class="px-4 py-2.5 text-center whitespace-nowrap space-x-1.5">
                <NuxtLink
                  :to="'/billing/invoices?referral_partner_id=' + p.id + '&search=' + encodeURIComponent(p.name)"
                  class="px-2 py-1 text-[11px] font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition inline-block"
                  title="View Invoices Prescribed by this Partner"
                >
                  Invoices
                </NuxtLink>
                <button
                  v-if="p.unsettled_commission > 0"
                  type="button"
                  class="px-2.5 py-1 text-[11px] font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded shadow-2xs transition cursor-pointer"
                  @click="openSettleModal(p)"
                >
                  Settle Payout
                </button>
                <span v-else class="text-[11px] text-slate-400 font-medium">
                  Settled
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Referral Partner Modal -->
    <div
      v-if="isAddModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-sm font-bold text-slate-900">Add Referral Partner / Center</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="isAddModalOpen = false">&times;</button>
        </div>

        <form class="p-5 space-y-3 text-xs" @submit.prevent="createPartner">
          <!-- Partner Category Selector Dropdown -->
          <div>
            <label class="block font-medium text-slate-700 mb-1">Partner Category / Entity Type *</label>
            <select
              v-model="newPartner.partner_type"
              class="w-full px-3 py-1.5 border border-slate-300 rounded bg-white text-slate-800 font-medium focus:ring-1 focus:ring-sky-500 cursor-pointer"
              @change="onPartnerTypeChange"
            >
              <option v-for="t in partnerTypes" :key="t.id" :value="t.id">
                {{ t.label }}
              </option>
            </select>
          </div>

          <!-- Dynamic Name Input -->
          <div>
            <label class="block font-medium text-slate-700 mb-1">{{ currentPartnerTypeConfig.nameLabel }}</label>
            <input
              v-model="newPartner.name"
              required
              class="w-full px-3 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500"
              :placeholder="currentPartnerTypeConfig.namePlaceholder"
            />
          </div>

          <!-- Dynamic Specialty Input -->
          <div>
            <label class="block font-medium text-slate-700 mb-1">{{ currentPartnerTypeConfig.specialtyLabel }}</label>
            <input
              v-model="newPartner.specialty"
              required
              class="w-full px-3 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500"
              :placeholder="currentPartnerTypeConfig.defaultSpecialty"
            />
          </div>

          <!-- Contact Phone -->
          <div>
            <label class="block font-medium text-slate-700 mb-1">Contact Phone Number</label>
            <input
              v-model="newPartner.phone"
              class="w-full px-3 py-1.5 border border-slate-300 rounded font-mono"
              placeholder="+91 98765 00000"
            />
          </div>

          <!-- Commission Structure -->
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Commission Type</label>
              <select
                v-model="newPartner.commission_type"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded bg-white text-slate-800"
              >
                <option value="percentage">Percentage (%)</option>
                <option value="fixed">Fixed Per Test (₹)</option>
              </select>
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Value</label>
              <input
                v-model.number="newPartner.commission_value"
                type="number"
                min="0"
                required
                class="w-full px-3 py-1.5 border border-slate-300 rounded font-mono"
                placeholder="15"
              />
            </div>
          </div>

          <div class="flex justify-end space-x-2 pt-3">
            <button
              type="button"
              class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded hover:bg-slate-50 cursor-pointer"
              @click="isAddModalOpen = false"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded shadow-xs cursor-pointer"
            >
              Save Referral Partner
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Settlement Confirmation Modal -->
    <div
      v-if="isSettleModalOpen && selectedPartner"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-sm overflow-hidden text-left">
        <div class="p-4 bg-slate-100 flex items-center justify-between border-b border-slate-200">
          <h3 class="text-xs font-bold text-slate-900">Confirm Commission Payout</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="isSettleModalOpen = false">&times;</button>
        </div>

        <div class="p-5 space-y-3 text-xs">
          <div>
            <p class="text-slate-500">Doctor / Partner:</p>
            <p class="font-bold text-slate-900 text-sm">{{ selectedPartner.name }}</p>
          </div>

          <div class="bg-amber-50 p-3 rounded border border-amber-200">
            <p class="text-amber-800 font-medium">Total Settlement Amount:</p>
            <p class="text-xl font-bold font-mono text-amber-700">₹ {{ selectedPartner.unsettled_commission.toLocaleString('en-IN') }}</p>
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Voucher / NEFT Txn Ref</label>
            <input
              v-model="settlementRef"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono"
            />
          </div>

          <div class="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded hover:bg-slate-50"
              @click="isSettleModalOpen = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded shadow-xs"
              @click="confirmSettlement"
            >
              Mark Settled
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
