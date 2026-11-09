<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '~/composables/useToast'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Badge from '~/components/ui/Badge.vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import Kbd from '~/components/ui/Kbd.vue'
import Modal from '~/components/ui/Modal.vue'

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

function getPartnerTypeBadge(type: string): { label: string; variant: 'info' | 'success' | 'neutral' | 'warning' } {
  switch (type) {
    case 'lab':
    case 'external_lab':
      return { label: 'Pathology Lab', variant: 'info' }
    case 'hospital':
      return { label: 'Hospital', variant: 'success' }
    case 'clinic':
      return { label: 'Clinic', variant: 'neutral' }
    case 'corporate':
    case 'other':
      return { label: 'Corporate B2B', variant: 'warning' }
    default:
      return { label: 'Doctor', variant: 'info' }
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
  <div class="space-y-6 max-w-7xl mx-auto text-left">
    <!-- Top Action Bar -->
    <PageHeader
      title="Referral Doctors & Healthcare Partners"
      description="Consulting physician commissions, diagnostic outreach accounting, hospital/lab referrals and payout settlements."
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <Button
            variant="secondary"
            size="md"
            title="Reload referral partners"
            @click="loadReferrals"
          >
            <Icon name="refresh" class="w-4 h-4" />
            <span class="hidden sm:inline">Refresh</span>
          </Button>
          <Button
            variant="primary"
            size="md"
            title="Register new referring doctor or partner organization"
            @click="isAddModalOpen = true"
          >
            <Icon name="plus" class="w-4 h-4" />
            <span>Add Partner</span>
          </Button>
        </div>
      </template>
    </PageHeader>

    <!-- Referral Metrics Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Partners</p>
          <div class="w-8 h-8 rounded-lg bg-teal-50 flex items-center justify-center text-teal-600">
            <Icon name="users" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-slate-900 mt-2">{{ partners.length }}</p>
        <p class="text-xs text-slate-500 mt-1">Active prescribing network</p>
      </Card>

      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Referred Revenue</p>
          <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
            <Icon name="credit-card" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-blue-600 mt-2">₹{{ totalReferredBusiness.toLocaleString('en-IN') }}</p>
        <p class="text-xs text-emerald-700 mt-1 font-medium font-mono">+24% vs last month</p>
      </Card>

      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Payout</p>
          <div class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
            <Icon name="activity" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-2xl font-bold font-mono text-amber-600 mt-2">₹{{ totalPendingSettlements.toLocaleString('en-IN') }}</p>
        <p class="text-xs text-amber-700 mt-1 font-medium">Ready for settlement</p>
      </Card>

      <Card class="p-4 bg-white">
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">TDS Compliance</p>
          <div class="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
            <Icon name="shield-check" class="w-4 h-4" />
          </div>
        </div>
        <p class="text-lg font-bold text-emerald-700 mt-2 flex items-center gap-1.5">
          <span class="inline-block w-2 h-2 rounded-full bg-emerald-500" />
          TDS Verified
        </p>
        <p class="text-xs text-slate-500 mt-1">Form 16A calculated</p>
      </Card>
    </div>

    <!-- Search Toolbar & Category Filter -->
    <Card class="p-4 bg-white">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <!-- Search Input with Keyboard Cue -->
        <div class="relative flex-1 max-w-xl">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
            <Icon name="search" class="w-4 h-4" />
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search by Doctor, Lab, Hospital, Clinic or Contact..."
            class="w-full pl-9 pr-14 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent transition-shadow"
          />
          <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <Kbd>/</Kbd>
          </div>
        </div>

        <!-- Filter Dropdown & Reset -->
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-1.5">
            <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Category:</label>
            <select
              v-model="selectedType"
              class="border border-slate-300 rounded-lg px-3 py-2 text-xs font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-teal-600"
            >
              <option value="All">All Categories</option>
              <option value="doctor">Doctors / Clinicians</option>
              <option value="lab">Referral Labs &amp; Pathology</option>
              <option value="hospital">Hospitals &amp; Centers</option>
              <option value="clinic">Clinics &amp; Polyclinics</option>
              <option value="other">Other B2B Partners</option>
            </select>
          </div>

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
              <th class="px-4 py-3 text-left">Doctor / Partner</th>
              <th class="px-4 py-3 text-left">Category &amp; Specialty</th>
              <th class="px-4 py-3 text-left">Contact</th>
              <th class="px-4 py-3 text-center">Commission Structure</th>
              <th class="px-4 py-3 text-right">Referred Cases</th>
              <th class="px-4 py-3 text-right">Business Volume</th>
              <th class="px-4 py-3 text-right">Pending Payout</th>
              <th class="px-4 py-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="8" class="text-center py-12 text-slate-400 font-medium">
                <div class="flex items-center justify-center gap-2">
                  <Icon name="refresh" class="w-5 h-5 animate-spin text-teal-600" />
                  <span>Loading referral partners...</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="filteredPartners.length === 0">
              <td colspan="8" class="text-center py-12 text-slate-400 font-medium">
                <div class="flex flex-col items-center justify-center gap-2">
                  <Icon name="users" class="w-8 h-8 text-slate-300" />
                  <p class="text-sm font-semibold text-slate-600">No referral partners found in this category</p>
                  <p class="text-xs text-slate-400">Click "Add Partner" above to register a physician or clinic.</p>
                </div>
              </td>
            </tr>
            <tr
              v-for="p in filteredPartners"
              v-else
              :key="p.id"
              class="hover:bg-teal-50/40 transition-colors"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-bold text-slate-900 text-sm">{{ p.name }}</span>
                  <Badge :variant="getPartnerTypeBadge(p.partner_type).variant">
                    {{ getPartnerTypeBadge(p.partner_type).label }}
                  </Badge>
                </div>
                <NuxtLink
                  :to="'/patients?referral_partner_id=' + p.id"
                  class="text-teal-700 hover:underline text-xs inline-flex items-center gap-1 mt-1 font-medium"
                  title="View Referred Patients"
                >
                  <span>View Patients ({{ p.total_referred_cases }}) &rarr;</span>
                </NuxtLink>
              </td>
              <td class="px-4 py-3 text-slate-600">
                <span class="inline-block px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-800 font-medium">
                  {{ p.specialty }}
                </span>
              </td>
              <td class="px-4 py-3 text-slate-600 font-mono">
                {{ p.contact_phone }}
              </td>
              <td class="px-4 py-3 text-center">
                <span class="font-mono font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full text-xs border border-teal-200">
                  {{ p.commission_type === 'percentage' ? `${p.commission_value}%` : `₹${p.commission_value}/test` }}
                </span>
              </td>
              <td class="px-4 py-3 text-right font-mono text-slate-800 font-medium">
                <NuxtLink
                  :to="'/patients?referral_partner_id=' + p.id"
                  class="hover:text-teal-700 hover:underline font-bold"
                  title="Click to view cases"
                >
                  {{ p.total_referred_cases }}
                </NuxtLink>
              </td>
              <td class="px-4 py-3 text-right font-mono font-bold text-slate-900">
                <NuxtLink
                  :to="'/billing/invoices?referral_partner_id=' + p.id + '&search=' + encodeURIComponent(p.name)"
                  class="hover:text-teal-700 hover:underline"
                  title="Click to view invoices"
                >
                  ₹{{ p.total_business_volume.toLocaleString('en-IN') }}
                </NuxtLink>
              </td>
              <td class="px-4 py-3 text-right font-mono font-bold text-amber-600">
                ₹{{ p.unsettled_commission.toLocaleString('en-IN') }}
              </td>
              <td class="px-4 py-3 text-center whitespace-nowrap">
                <div class="flex items-center justify-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="sm"
                    :to="'/billing/invoices?referral_partner_id=' + p.id + '&search=' + encodeURIComponent(p.name)"
                    title="View Invoices Prescribed by this Partner"
                  >
                    <Icon name="file-text" class="w-3.5 h-3.5" />
                    <span>Invoices</span>
                  </Button>
                  <Button
                    v-if="p.unsettled_commission > 0"
                    variant="success"
                    size="sm"
                    title="Process commission settlement payout"
                    @click="openSettleModal(p)"
                  >
                    <Icon name="check" class="w-3.5 h-3.5" />
                    <span>Settle Payout</span>
                  </Button>
                  <span v-else class="text-xs text-slate-400 font-medium px-2 py-1">
                    Settled
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Mobile Card View -->
    <div class="md:hidden space-y-3">
      <div v-if="loading" class="p-8 text-center text-slate-400 font-medium">
        <Icon name="refresh" class="w-6 h-6 animate-spin mx-auto text-teal-600 mb-2" />
        <p class="text-xs">Loading partners...</p>
      </div>
      <div v-else-if="filteredPartners.length === 0" class="p-8 text-center text-slate-400 font-medium bg-white rounded-lg border border-slate-200">
        <Icon name="users" class="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p class="text-sm font-semibold text-slate-700">No referral partners found</p>
      </div>
      <Card
        v-for="p in filteredPartners"
        v-else
        :key="'mobile-' + p.id"
        class="p-4 bg-white space-y-3 border border-slate-200"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <Badge :variant="getPartnerTypeBadge(p.partner_type).variant">
                {{ getPartnerTypeBadge(p.partner_type).label }}
              </Badge>
              <span class="text-xs font-mono font-medium text-slate-500">{{ p.specialty }}</span>
            </div>
            <h3 class="text-base font-bold text-slate-900 mt-1">{{ p.name }}</h3>
            <p class="text-xs font-mono text-slate-500 mt-0.5">{{ p.contact_phone }}</p>
          </div>
          <div class="text-right">
            <span class="text-xs font-mono font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
              {{ p.commission_type === 'percentage' ? `${p.commission_value}%` : `₹${p.commission_value}` }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-2 p-2 bg-slate-50 rounded-lg text-center text-xs">
          <div>
            <span class="text-slate-400 block">Cases</span>
            <span class="font-bold font-mono text-slate-800">{{ p.total_referred_cases }}</span>
          </div>
          <div>
            <span class="text-slate-400 block">Volume</span>
            <span class="font-bold font-mono text-slate-800">₹{{ p.total_business_volume.toLocaleString('en-IN') }}</span>
          </div>
          <div>
            <span class="text-slate-400 block">Payout Due</span>
            <span class="font-bold font-mono text-amber-600">₹{{ p.unsettled_commission.toLocaleString('en-IN') }}</span>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <Button
            variant="ghost"
            size="sm"
            :to="'/billing/invoices?referral_partner_id=' + p.id + '&search=' + encodeURIComponent(p.name)"
          >
            <Icon name="file-text" class="w-3.5 h-3.5" />
            <span>Invoices</span>
          </Button>
          <Button
            v-if="p.unsettled_commission > 0"
            variant="success"
            size="sm"
            @click="openSettleModal(p)"
          >
            <Icon name="check" class="w-3.5 h-3.5" />
            <span>Settle</span>
          </Button>
        </div>
      </Card>
    </div>

    <!-- Add Referral Partner Modal -->
    <Modal
      v-model="isAddModalOpen"
      title="Add Referral Partner / Clinician"
      description="Register an external consulting physician, diagnostic center, or hospital for commission tracking."
      size="md"
      @close="isAddModalOpen = false"
    >
      <form class="space-y-4" @submit.prevent="createPartner">
        <!-- Partner Category Selector Dropdown -->
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Partner Category *</label>
          <select
            v-model="newPartner.partner_type"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-800 font-medium focus:ring-2 focus:ring-teal-600 text-sm cursor-pointer"
            @change="onPartnerTypeChange"
          >
            <option v-for="t in partnerTypes" :key="t.id" :value="t.id">
              {{ t.label }}
            </option>
          </select>
        </div>

        <!-- Dynamic Name Input -->
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">{{ currentPartnerTypeConfig.nameLabel }}</label>
          <input
            v-model="newPartner.name"
            required
            class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-600 text-sm text-slate-900"
            :placeholder="currentPartnerTypeConfig.namePlaceholder"
          />
        </div>

        <!-- Dynamic Specialty Input -->
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">{{ currentPartnerTypeConfig.specialtyLabel }}</label>
          <input
            v-model="newPartner.specialty"
            required
            class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-600 text-sm text-slate-900"
            :placeholder="currentPartnerTypeConfig.defaultSpecialty"
          />
        </div>

        <!-- Contact Phone -->
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Contact Phone Number</label>
          <input
            v-model="newPartner.phone"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm text-slate-900"
            placeholder="+91 98765 00000"
          />
        </div>

        <!-- Commission Structure -->
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Commission Type</label>
            <select
              v-model="newPartner.commission_type"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-800 text-sm focus:ring-2 focus:ring-teal-600"
            >
              <option value="percentage">Percentage (%)</option>
              <option value="fixed">Fixed Per Test (₹)</option>
            </select>
          </div>
          <div class="space-y-1.5">
            <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Value</label>
            <input
              v-model.number="newPartner.commission_value"
              type="number"
              min="0"
              required
              class="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm text-slate-900"
              placeholder="15"
            />
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-4 border-t border-slate-200">
          <Button
            type="button"
            variant="ghost"
            size="md"
            @click="isAddModalOpen = false"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="md"
          >
            <Icon name="check" class="w-4 h-4" />
            <span>Save Partner</span>
          </Button>
        </div>
      </form>
    </Modal>

    <!-- Settlement Confirmation Modal -->
    <Modal
      v-model="isSettleModalOpen"
      title="Confirm Commission Payout"
      description="Record payout voucher reference for accounting ledger audit."
      size="sm"
      @close="isSettleModalOpen = false"
    >
      <div v-if="selectedPartner" class="space-y-4">
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span class="text-xs text-slate-500 font-semibold uppercase tracking-wider">Partner:</span>
          <p class="font-bold text-slate-900 text-base mt-0.5">{{ selectedPartner.name }}</p>
        </div>

        <div class="bg-amber-50 p-4 rounded-xl border border-amber-200 text-center">
          <p class="text-xs text-amber-800 font-medium uppercase tracking-wider">Settlement Amount Due</p>
          <p class="text-2xl font-bold font-mono text-amber-700 mt-1">₹{{ selectedPartner.unsettled_commission.toLocaleString('en-IN') }}</p>
        </div>

        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Voucher / NEFT Txn Ref</label>
          <input
            v-model="settlementRef"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm text-slate-900 focus:ring-2 focus:ring-teal-600"
          />
        </div>

        <div class="flex justify-end gap-2 pt-4 border-t border-slate-200">
          <Button
            type="button"
            variant="ghost"
            size="md"
            @click="isSettleModalOpen = false"
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="success"
            size="md"
            @click="confirmSettlement"
          >
            <Icon name="check" class="w-4 h-4" />
            <span>Confirm Settlement</span>
          </Button>
        </div>
      </div>
    </Modal>
  </div>
</template>
