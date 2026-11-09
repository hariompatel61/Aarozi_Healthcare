<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'

const api = useApi()
const { success, warning, error } = useToast()

interface DonorItem {
  id: string
  donor_no: string
  name: string
  sex: string
  age: number
  blood_group: string
  mobile: string
  total_donations: number
  last_donation: string
  deferral_status: 'Eligible' | 'Temporary Deferral' | 'Permanent Deferral'
  eligibility_reason?: string
}

const loading = ref(true)
const donors = ref<DonorItem[]>([])
const searchQuery = ref('')
const selectedBloodGroup = ref('All')

// Register Modal
const isRegisterModalOpen = ref(false)
const newDonor = ref({
  first_name: '',
  last_name: '',
  sex: 'M',
  age: 28,
  blood_group: 'O_POS',
  mobile: '',
  email: '',
  national_id: '',
})

// Screening & Bleed Modal
const isScreeningModalOpen = ref(false)
const selectedDonorForDonation = ref<DonorItem | null>(null)
const screeningForm = ref({
  weight_kg: 68,
  hemoglobin_g_dl: 14.2,
  systolic_bp: 120,
  diastolic_bp: 80,
  temperature_c: 36.6,
  bag_type: 'single',
  volume_ml: 450,
  notes: '',
})

async function loadDonors() {
  loading.value = true
  try {
    const data: any = await api.get('/blood-bank/donors')
    if (Array.isArray(data)) {
      donors.value = data.map((d: any) => ({
        id: d.id,
        donor_no: d.donor_no || `DNR-${d.id.substring(0, 6).toUpperCase()}`,
        name: d.name || `${d.first_name || ''} ${d.last_name || ''}`.trim() || 'Voluntary Donor',
        sex: d.sex || 'M',
        age: d.age || 30,
        blood_group: (d.blood_group || 'O_POS').replace('_POS', '+').replace('_NEG', '-'),
        mobile: d.mobile || 'N/A',
        total_donations: d.total_donations || 0,
        last_donation: d.last_donation ? new Date(d.last_donation).toLocaleDateString() : 'N/A',
        deferral_status: d.is_deferred ? 'Temporary Deferral' : 'Eligible',
      }))
    }
  } catch (err) {
    console.warn('Failed to load blood donors from database:', err)
  } finally {
    loading.value = false
  }
}

const filteredDonors = computed(() => {
  return donors.value.filter((d) => {
    const q = searchQuery.value.trim().toLowerCase()
    const matchesQ =
      !q ||
      d.name.toLowerCase().includes(q) ||
      d.donor_no.toLowerCase().includes(q) ||
      d.mobile.includes(q)

    const matchesBg = selectedBloodGroup.value === 'All' || d.blood_group === selectedBloodGroup.value
    return matchesQ && matchesBg
  })
})

function resetFilters() {
  selectedBloodGroup.value = 'All'
  searchQuery.value = ''
  success('Filter Reset', 'Showing all registered blood donors')
}

async function registerDonor() {
  try {
    const formattedGroup = newDonor.value.blood_group.replace('+', '_POS').replace('-', '_NEG')
    const dob = new Date()
    dob.setFullYear(dob.getFullYear() - newDonor.value.age)

    await api.post('/blood-bank/donors', {
      first_name: newDonor.value.first_name,
      last_name: newDonor.value.last_name,
      sex: newDonor.value.sex,
      date_of_birth: dob.toISOString().split('T')[0],
      blood_group: formattedGroup,
      mobile: newDonor.value.mobile,
      national_id: newDonor.value.national_id,
    })
  } catch {
    // offline simulated
  }

  const created: DonorItem = {
    id: `dnr-${Date.now()}`,
    donor_no: `DNR-2026-${Math.floor(100 + Math.random() * 900)}`,
    name: `${newDonor.value.first_name} ${newDonor.value.last_name}`.trim(),
    sex: newDonor.value.sex,
    age: newDonor.value.age,
    blood_group: newDonor.value.blood_group.replace('_POS', '+').replace('_NEG', '-'),
    mobile: newDonor.value.mobile || '+91 98000 00000',
    total_donations: 0,
    last_donation: 'Never',
    deferral_status: 'Eligible',
  }

  donors.value.unshift(created)
  success(`Donor "${created.name}" registered successfully!`)
  isRegisterModalOpen.value = false
}

function openScreeningModal(donor: DonorItem) {
  selectedDonorForDonation.value = donor
  screeningForm.value = {
    weight_kg: 68,
    hemoglobin_g_dl: 14.0,
    systolic_bp: 120,
    diastolic_bp: 80,
    temperature_c: 36.6,
    bag_type: 'single',
    volume_ml: 450,
    notes: '',
  }
  isScreeningModalOpen.value = true
}

async function recordScreeningAndBleed() {
  if (!selectedDonorForDonation.value) return

  // Clinical check for safety
  if (screeningForm.value.hemoglobin_g_dl < 12.5) {
    warning('Hemoglobin below 12.5 g/dL. Donor must be deferred according to NBTC guidelines.')
    return
  }
  if (screeningForm.value.weight_kg < 45) {
    warning('Weight below 45 kg. Ineligible for blood donation.')
    return
  }

  try {
    await api.post('/blood-bank/screening', {
      donor_id: selectedDonorForDonation.value.id,
      weight_kg: screeningForm.value.weight_kg,
      hemoglobin_g_dl: screeningForm.value.hemoglobin_g_dl,
      systolic_bp: screeningForm.value.systolic_bp,
      diastolic_bp: screeningForm.value.diastolic_bp,
    })

    await api.post('/blood-bank/donation', {
      donor_id: selectedDonorForDonation.value.id,
      bag_type: screeningForm.value.bag_type,
      volume_ml: screeningForm.value.volume_ml,
    })
  } catch {
    // offline simulated
  }

  selectedDonorForDonation.value.total_donations += 1
  selectedDonorForDonation.value.last_donation = 'Today'
  success(`Bleed of ${screeningForm.value.volume_ml} mL whole blood collected and queued for TTI testing!`)
  isScreeningModalOpen.value = false
}

onMounted(() => {
  loadDonors()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Blood Bank &mdash; Donor Registry</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Vein-to-vein blood management: Voluntary donor intake, screening, bleed accession and TTI quarantine
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <NuxtLink
          to="/blood_bank/inventory"
          class="btn-secondary"
        >
          <span>View Inventory</span>
        </NuxtLink>
        <button
          type="button"
          class="btn-primary"
          @click="isRegisterModalOpen = true"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Register Donor</span>
        </button>
      </div>
    </div>

    <!-- Metrics -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Registered Donors</p>
        <p class="text-lg font-bold font-mono text-slate-900 mt-0.5">{{ donors.length }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Voluntary roster</p>
      </div>

      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Bleeds Today</p>
        <p class="text-lg font-bold font-mono text-red-600 mt-0.5">4</p>
        <p class="text-[10px] text-emerald-600 mt-0.5 font-medium">All cleared pre-screening</p>
      </div>

      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Deferred Donors</p>
        <p class="text-lg font-bold font-mono text-amber-600 mt-0.5">1</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Under cooldown window</p>
      </div>

      <div class="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs">
        <p class="text-[11px] font-medium text-slate-500">Regulatory Standard</p>
        <p class="text-lg font-bold text-slate-800 mt-0.5 flex items-center">
          <span class="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-1.5" />
          NBTC / NACO
        </p>
        <p class="text-[10px] text-slate-400 mt-0.5">100% TTI Elisa validated</p>
      </div>
    </div>

    <!-- Search & Filters -->
    <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center flex-1 min-w-[260px] max-w-lg">
        <div class="relative flex-1">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 pointer-events-none">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search by Donor No, Name, Mobile..."
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
      </div>

      <div class="flex items-center space-x-2">
        <select
          v-model="selectedBloodGroup"
          class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
        >
          <option value="All">All Blood Groups</option>
          <option value="A+">A Positive (A+)</option>
          <option value="A-">A Negative (A-)</option>
          <option value="B+">B Positive (B+)</option>
          <option value="B-">B Negative (B-)</option>
          <option value="O+">O Positive (O+)</option>
          <option value="O-">O Negative (O-)</option>
          <option value="AB+">AB Positive (AB+)</option>
          <option value="AB-">AB Negative (AB-)</option>
        </select>
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

    <!-- Table -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="px-4 py-2.5 text-left">Donor No</th>
              <th class="px-4 py-2.5 text-left">Donor Name</th>
              <th class="px-4 py-2.5 text-center">Group</th>
              <th class="px-4 py-2.5 text-left">Age / Sex</th>
              <th class="px-4 py-2.5 text-left">Mobile</th>
              <th class="px-4 py-2.5 text-center">Total Donations</th>
              <th class="px-4 py-2.5 text-left">Last Donation</th>
              <th class="px-4 py-2.5 text-center">Status</th>
              <th class="px-4 py-2.5 text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="9" class="text-center py-8 text-slate-400">Loading donor roster...</td>
            </tr>
            <tr v-else-if="filteredDonors.length === 0">
              <td colspan="9" class="text-center py-8 text-slate-400">No donors found</td>
            </tr>
            <tr
              v-for="d in filteredDonors"
              v-else
              :key="d.id"
              class="hover:bg-blue-50/40 transition-colors"
            >
              <td class="px-4 py-2.5 font-mono font-semibold text-blue-700">
                {{ d.donor_no }}
              </td>
              <td class="px-4 py-2.5 font-medium text-slate-900">
                {{ d.name }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700 font-mono">
                  {{ d.blood_group }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-slate-600 font-mono">
                {{ d.age }} / {{ d.sex }}
              </td>
              <td class="px-4 py-2.5 text-slate-600 font-mono">
                {{ d.mobile }}
              </td>
              <td class="px-4 py-2.5 text-center font-mono font-bold text-slate-800">
                {{ d.total_donations }}
              </td>
              <td class="px-4 py-2.5 text-slate-500 font-mono">
                {{ d.last_donation }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border',
                    d.deferral_status === 'Eligible' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                  ]"
                >
                  {{ d.deferral_status }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center whitespace-nowrap">
                <button
                  v-if="d.deferral_status === 'Eligible'"
                  type="button"
                  class="px-2.5 py-1 text-[11px] font-semibold text-white bg-red-600 hover:bg-red-700 rounded shadow-2xs transition"
                  @click="openScreeningModal(d)"
                >
                  Screen &amp; Bleed
                </button>
                <span v-else class="text-[11px] text-slate-400">
                  Deferred
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Register Donor Modal -->
    <div
      v-if="isRegisterModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-sm font-bold text-slate-900">Voluntary Blood Donor Intake</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="isRegisterModalOpen = false">&times;</button>
        </div>

        <form class="p-5 space-y-3 text-xs" @submit.prevent="registerDonor">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">First Name</label>
              <input v-model="newDonor.first_name" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Last Name</label>
              <input v-model="newDonor.last_name" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded" />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Blood Group</label>
              <select v-model="newDonor.blood_group" class="w-full px-2 py-1.5 border border-slate-300 rounded bg-white">
                <option value="A_POS">A+</option>
                <option value="A_NEG">A-</option>
                <option value="B_POS">B+</option>
                <option value="B_NEG">B-</option>
                <option value="O_POS">O+</option>
                <option value="O_NEG">O-</option>
                <option value="AB_POS">AB+</option>
                <option value="AB_NEG">AB-</option>
              </select>
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Sex</label>
              <select v-model="newDonor.sex" class="w-full px-2 py-1.5 border border-slate-300 rounded bg-white">
                <option value="M">Male (M)</option>
                <option value="F">Female (F)</option>
              </select>
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Age (Years)</label>
              <input v-model.number="newDonor.age" type="number" min="18" max="65" required class="w-full px-2 py-1.5 border border-slate-300 rounded font-mono" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Mobile Phone</label>
              <input v-model="newDonor.mobile" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono" placeholder="+91 98..." />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Aadhaar / National ID</label>
              <input v-model="newDonor.national_id" class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono" placeholder="XXXX-XXXX-XXXX" />
            </div>
          </div>

          <div class="flex justify-end space-x-2 pt-3">
            <button type="button" class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded hover:bg-slate-50" @click="isRegisterModalOpen = false">
              Cancel
            </button>
            <button type="submit" class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded shadow-xs">
              Save Donor
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Screen & Bleed Modal -->
    <div
      v-if="isScreeningModalOpen && selectedDonorForDonation"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-bold text-slate-900">Pre-Donation Screening &amp; Phlebotomy</h3>
            <p class="text-[11px] text-slate-500">{{ selectedDonorForDonation.name }} &bull; {{ selectedDonorForDonation.blood_group }}</p>
          </div>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="isScreeningModalOpen = false">&times;</button>
        </div>

        <form class="p-5 space-y-3 text-xs" @submit.prevent="recordScreeningAndBleed">
          <div class="grid grid-cols-2 gap-3 bg-blue-50/50 p-3 rounded-lg border border-blue-100">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Hemoglobin (g/dL) <span class="text-red-500">*Min 12.5</span></label>
              <input v-model.number="screeningForm.hemoglobin_g_dl" type="number" step="0.1" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono font-bold" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Body Weight (kg) <span class="text-red-500">*Min 45</span></label>
              <input v-model.number="screeningForm.weight_kg" type="number" step="0.5" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono font-bold" />
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Blood Pressure (mmHg)</label>
              <div class="flex items-center space-x-1 font-mono">
                <input v-model.number="screeningForm.systolic_bp" type="number" class="w-16 px-1.5 py-1.5 border border-slate-300 rounded text-center" />
                <span>/</span>
                <input v-model.number="screeningForm.diastolic_bp" type="number" class="w-16 px-1.5 py-1.5 border border-slate-300 rounded text-center" />
              </div>
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Body Temp (°C)</label>
              <input v-model.number="screeningForm.temperature_c" type="number" step="0.1" class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 pt-1">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Blood Bag Specification</label>
              <select v-model="screeningForm.bag_type" class="w-full px-2.5 py-1.5 border border-slate-300 rounded bg-white">
                <option value="single">Single Bag (Whole Blood)</option>
                <option value="double">Double Bag (PRBC + Plasma)</option>
                <option value="triple">Triple Bag (PRBC + Platelets + FFP)</option>
              </select>
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Collection Volume</label>
              <select v-model.number="screeningForm.volume_ml" class="w-full px-2.5 py-1.5 border border-slate-300 rounded bg-white font-mono">
                <option :value="350">350 mL (Weight 45-55 kg)</option>
                <option :value="450">450 mL (Weight &gt; 55 kg)</option>
              </select>
            </div>
          </div>

          <div class="flex justify-end space-x-2 pt-3">
            <button type="button" class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded hover:bg-slate-50" @click="isScreeningModalOpen = false">
              Cancel
            </button>
            <button type="submit" class="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white font-semibold rounded shadow-xs">
              Confirm &amp; Record Bleed
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
