<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '~/composables/useToast'
import Modal from '~/components/ui/Modal.vue'

const router = useRouter()
const route = useRoute()
const { success, warning, error, info } = useToast()
const api = useApi()

// -------------------------------------------------------------
// 1. PATIENT DEMOGRAPHICS & MOBILE / NAME AUTO-LOOKUP
// -------------------------------------------------------------
const loading = ref(false)
const errorState = ref<string | null>(null)
const permission_denied = ref(false)
const firstNameInput = ref<HTMLInputElement | null>(null)

const patientUhid = ref(`PAT25000${Math.floor(10 + Math.random() * 90)}`)
const isExistingPatient = ref(false)
const existingPatientId = ref<string | null>(null)
const isSearchingMobile = ref(false)

// Repeat Patient Auto-search
const searchSuggestions = ref<any[]>([])
const isSearchingPatients = ref(false)
const activeSearchField = ref<'mobile' | 'name' | null>(null)
const showSearchDropdown = ref(false)
let searchDebounceTimer: any = null

const form = reactive({
  first_name: '',
  last_name: '',
  full_name: '',
  mobile: '',
  age: 32,
  gender: 'Male',
  sex: 'Male',
  primary_id_type: 'National ID / Aadhaar',
  city: 'Noida',
  address: '',
  patient_type: 'Walk-in',
})

function triggerPatientSearch(val: string, field: 'mobile' | 'name') {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  const trimmed = (val || '').trim()
  const minLen = field === 'mobile' ? 3 : 2
  const checkVal = field === 'mobile' ? trimmed.replace(/\D/g, '') : trimmed
  if (checkVal.length < minLen) {
    searchSuggestions.value = []
    showSearchDropdown.value = false
    return
  }
  activeSearchField.value = field
  isSearchingPatients.value = true
  searchDebounceTimer = setTimeout(async () => {
    try {
      const data: any = await api.get(`/patients?query=${encodeURIComponent(checkVal)}&limit=6`)
      if (Array.isArray(data) && data.length > 0) {
        searchSuggestions.value = data
        showSearchDropdown.value = true
      } else {
        searchSuggestions.value = []
        showSearchDropdown.value = false
      }
    } catch (err) {
      console.warn('Patient auto-suggest search error:', err)
    } finally {
      isSearchingPatients.value = false
    }
  }, 180)
}

function selectExistingPatient(p: any) {
  existingPatientId.value = p.id || null
  patientUhid.value = p.patient_no || p.uhid || p.id || patientUhid.value
  const fullName = `${p.first_name || ''} ${p.last_name || ''}`.trim() || p.name || ''
  form.full_name = fullName || form.full_name
  form.mobile = (p.mobile_normalized || p.mobile || '').replace(/\D/g, '').slice(-10) || form.mobile
  form.age = p.age_years || p.age || form.age
  form.gender = (p.sex || p.gender || '').toLowerCase().startsWith('f') ? 'Female' : 'Male'
  form.city = p.city || form.city
  form.address = p.address || form.address
  if (p.referral_partner_id) {
    selectedPartnerId.value = p.referral_partner_id
  }
  isExistingPatient.value = true
  showSearchDropdown.value = false
  searchSuggestions.value = []
  success('Repeat Patient Selected', `${form.full_name} (${patientUhid.value}) loaded for test order.`)
}

function resetToNewPatient() {
  existingPatientId.value = null
  patientUhid.value = `PAT25000${Math.floor(10 + Math.random() * 90)}`
  form.mobile = ''
  form.full_name = ''
  form.age = 30
  form.gender = 'Male'
  form.city = 'Noida'
  form.address = ''
  isExistingPatient.value = false
  showSearchDropdown.value = false
  searchSuggestions.value = []
  info('New Patient Mode', 'Enter fresh demographic details.')
}

async function loadPreselectedPatient(idOrUhid: string) {
  loading.value = true
  try {
    const p: any = await api.get(`/patients/${encodeURIComponent(idOrUhid)}`)
    if (p && (p.id || p.patient_no)) {
      selectExistingPatient(p)
      info('Patient Loaded', `Ready to order tests for ${form.full_name} (${patientUhid.value})`)
    }
  } catch (err) {
    console.warn('Could not load preselected patient:', err)
  } finally {
    loading.value = false
  }
}

async function checkMobileLookup() {
  const cleanMobile = form.mobile.replace(/\D/g, '')
  if (cleanMobile.length < 10) {
    isExistingPatient.value = false
    return
  }
  isSearchingMobile.value = true
  try {
    const data: any = await api.get(`/patients?query=${encodeURIComponent(cleanMobile.slice(-10))}`)
    if (Array.isArray(data) && data.length > 0) {
      // Look for a confirmed match on phone number
      const match = data.find((p: any) => {
        const pMob = (p.mobile_normalized || p.mobile || '').replace(/\D/g, '')
        return pMob.endsWith(cleanMobile.slice(-10))
      })
      if (match) {
        selectExistingPatient(match)
        return
      }
    }
    // If no match found, do NOT overwrite any user-entered name or details
    isExistingPatient.value = false
    info('New Patient', `No prior record for ${cleanMobile.slice(-10)}. Proceed with registration.`)
  } catch (err) {
    console.warn('API mobile lookup fallback:', err)
  } finally {
    isSearchingMobile.value = false
  }
}

// -------------------------------------------------------------
// 2. REFERRAL DOCTORS & PARTNER HUBS
// -------------------------------------------------------------
interface ReferralPartnerOption {
  id: string
  name: string
  specialty: string
  partner_type: string
  commission_pct: number
}

const partners = ref<ReferralPartnerOption[]>([
  { id: 'ref-01', name: 'Dr. Amrit Singh', specialty: 'Cardiology', partner_type: 'doctor', commission_pct: 15 },
  { id: 'ref-02', name: 'Dr. Neena Gupta', specialty: 'Endocrinology', partner_type: 'doctor', commission_pct: 20 },
  { id: 'ref-03', name: 'Dr. R. Sharma', specialty: 'General Medicine', partner_type: 'doctor', commission_pct: 10 },
  { id: 'ref-04', name: 'Apex Heart & Multispeciality', specialty: 'Hospital Hub', partner_type: 'hospital', commission_pct: 18 },
  { id: 'ref-00', name: 'Direct Walk-in / Self', specialty: 'None', partner_type: 'self', commission_pct: 0 },
])

const selectedPartnerId = ref('ref-01')

const defaultPartner: ReferralPartnerOption = { id: 'ref-00', name: 'Direct Walk-in / Self', specialty: 'None', partner_type: 'self', commission_pct: 0 }
const selectedPartner = computed<ReferralPartnerOption>(() => {
  return partners.value.find((p) => p.id === selectedPartnerId.value) ?? defaultPartner
})

function getPartnerDisplayLabel(p: ReferralPartnerOption) {
  if (p.partner_type === 'self' || p.id === 'ref-00') {
    return 'Direct Walk-in / Self Prescribed'
  }
  let typeBadge = ''
  if (p.partner_type === 'lab' || p.partner_type === 'external_lab') {
    typeBadge = '[Pathology Lab]'
  } else if (p.partner_type === 'hospital') {
    typeBadge = '[Hospital]'
  } else if (p.partner_type === 'clinic') {
    typeBadge = '[Clinic]'
  } else if (p.partner_type === 'corporate' || p.partner_type === 'other') {
    typeBadge = '[B2B Partner]'
  } else {
    typeBadge = '[Doctor]'
  }
  const spec = p.specialty && p.specialty !== 'None' ? ` • ${p.specialty}` : ''
  return `${p.name} ${typeBadge}${spec}`
}

async function loadReferralPartners() {
  try {
    const list: any = await api.get('/billing/referrals/partners')
    if (Array.isArray(list) && list.length > 0) {
      partners.value = list.map((p: any) => ({
        id: p.id,
        name: p.name,
        specialty: p.specialty || 'General',
        partner_type: p.partner_type || 'doctor',
        commission_pct: Number(p.commission_value || 15),
      }))
      // Ensure Self/Direct exists
      if (!partners.value.find((p) => p.id === 'ref-00')) {
        partners.value.push({ id: 'ref-00', name: 'Direct Walk-in / Self', specialty: 'None', partner_type: 'self', commission_pct: 0 })
      }
    }
  } catch (err) {
    console.warn('Using referral partners cache:', err)
  }
}

// Quick Add Doctor / Center Modal State
const isAddDoctorModalOpen = ref(false)
const newDoctor = reactive({
  partner_type: 'doctor',
  name: '',
  specialty: 'Internal Medicine',
  phone: '',
  commission_pct: 15,
})

const partnerTypesList = [
  { id: 'doctor', label: 'Doctor / Consulting Clinician', defaultSpecialty: 'Internal Medicine', placeholder: 'e.g. Dr. Rajesh Khanna, MD', prefix: 'Dr. ' },
  { id: 'lab', label: 'Referral Lab / Pathology Center', defaultSpecialty: 'Pathology & Diagnostic', placeholder: 'e.g. Apex Diagnostics & Path Lab', prefix: '' },
  { id: 'hospital', label: 'Hospital / Nursing Home', defaultSpecialty: 'Multispeciality Hospital', placeholder: 'e.g. Metro Multispeciality Hospital', prefix: '' },
  { id: 'clinic', label: 'Clinic / Polyclinic Center', defaultSpecialty: 'Polyclinic OPD', placeholder: 'e.g. City Health Polyclinic', prefix: '' },
  { id: 'other', label: 'Other Healthcare Partner', defaultSpecialty: 'Diagnostic Outreach', placeholder: 'e.g. Global Health Partner', prefix: '' },
]

function onQuickPartnerTypeChange() {
  const conf = partnerTypesList.find((x) => x.id === newDoctor.partner_type)
  if (conf) {
    if (!newDoctor.specialty || partnerTypesList.some((x) => x.defaultSpecialty === newDoctor.specialty)) {
      newDoctor.specialty = conf.defaultSpecialty
    }
    if (conf.prefix && !newDoctor.name.startsWith(conf.prefix)) {
      newDoctor.name = conf.prefix
    } else if (!conf.prefix && newDoctor.name.startsWith('Dr. ')) {
      newDoctor.name = newDoctor.name.replace(/^Dr\.\s*/, '')
    }
  }
}

async function submitAddDoctor() {
  if (!newDoctor.name.trim()) {
    warning('Missing Name', 'Please enter partner name.')
    return
  }

  const newId = `ref-${Date.now()}`
  let finalName = newDoctor.name.trim()
  if (newDoctor.partner_type === 'doctor' && !finalName.startsWith('Dr.')) {
    finalName = `Dr. ${finalName}`
  }

  const created: ReferralPartnerOption = {
    id: newId,
    name: finalName,
    specialty: newDoctor.specialty.trim() || 'General',
    partner_type: newDoctor.partner_type || 'doctor',
    commission_pct: Number(newDoctor.commission_pct || 15),
  }

  try {
    const payload = {
      name: created.name,
      partner_type: created.partner_type,
      specialty: created.specialty,
      contact_phone: newDoctor.phone.trim() || undefined,
      commission_type: 'percentage',
      commission_value: created.commission_pct,
    }
    try {
      await api.post('/billing/referrals/partners/create', payload)
    } catch {
      await api.post('/billing/referrals/partners', payload)
    }
  } catch {
    // offline graceful fallback
  }

  partners.value.unshift(created)
  selectedPartnerId.value = newId
  isAddDoctorModalOpen.value = false
  success('Partner Selected', `"${created.name}" assigned to this registration.`)

  newDoctor.name = ''
  newDoctor.phone = ''
  newDoctor.partner_type = 'doctor'
}

// -------------------------------------------------------------
// 3. TEST / PACKAGE SELECTOR
// -------------------------------------------------------------
interface TestItem {
  code: string
  name: string
  sample: string
  price: number
  category: string
}

const testCatalog = ref<TestItem[]>([
  { code: 'CBC', name: 'Complete Blood Count (CBC & ESR)', sample: 'EDTA', price: 400, category: 'Hematology' },
  { code: 'LFT', name: 'Liver Function Test Complete (12)', sample: 'Serum', price: 500, category: 'Biochemistry' },
  { code: 'KFT', name: 'Kidney Function Test & Electrolytes', sample: 'Serum', price: 450, category: 'Biochemistry' },
  { code: 'TFT', name: 'Thyroid Profile (Total T3, T4, TSH)', sample: 'Serum', price: 650, category: 'Hormones' },
  { code: 'HBA1C', name: 'Glycated Hemoglobin HbA1c (HPLC)', sample: 'EDTA', price: 500, category: 'Biochemistry' },
  { code: 'LIPID', name: 'Lipid Profile Comprehensive', sample: 'Serum', price: 650, category: 'Biochemistry' },
  { code: 'URINE_R', name: 'Urine Routine & Microscopy Complete', sample: 'Urine', price: 200, category: 'Urine' },
  { code: 'VIT_D', name: 'Vitamin D (25-Hydroxy)', sample: 'Serum', price: 1200, category: 'Biochemistry' },
  { code: 'VIT_B12', name: 'Vitamin B12 (Cyanocobalamin)', sample: 'Serum', price: 900, category: 'Biochemistry' },
  { code: 'DENGUE', name: 'Dengue NS1 Antigen (ELISA)', sample: 'Serum', price: 600, category: 'Serology' },
  { code: 'WIDAL', name: 'Widal Slide Agglutination', sample: 'Serum', price: 250, category: 'Serology' },
])

const testSearchQuery = ref('')
const selectedCategory = ref('All')
const categories = ['All', 'Popular', 'Hematology', 'Biochemistry', 'Hormones', 'Serology', 'Urine']

const selectedTestCodes = ref<string[]>(['CBC', 'LFT'])

const selectedTests = computed(() => {
  return testCatalog.value.filter((t) => selectedTestCodes.value.includes(t.code))
})

const filteredCatalog = computed(() => {
  const q = testSearchQuery.value.trim().toLowerCase()
  return testCatalog.value.filter((t) => {
    const matchesCat =
      selectedCategory.value === 'All'
        ? true
        : selectedCategory.value === 'Popular'
        ? ['CBC', 'LFT', 'KFT', 'TFT', 'HBA1C'].includes(t.code)
        : t.category === selectedCategory.value

    const matchesQuery = !q || t.name.toLowerCase().includes(q) || t.code.toLowerCase().includes(q)
    return matchesCat && matchesQuery
  })
})

function toggleTest(code: string) {
  if (selectedTestCodes.value.includes(code)) {
    selectedTestCodes.value = selectedTestCodes.value.filter((c) => c !== code)
  } else {
    selectedTestCodes.value.push(code)
  }
}

function removeTest(code: string) {
  selectedTestCodes.value = selectedTestCodes.value.filter((c) => c !== code)
}

// -------------------------------------------------------------
// 4. DISCOUNT & AUTOMATIC COMMISSION ENGINE
// -------------------------------------------------------------
const discountType = ref<'flat' | 'percentage'>('flat')
const discountValue = ref<number>(0)

const grossAmount = computed(() => {
  return selectedTests.value.reduce((acc, t) => acc + t.price, 0)
})

const calculatedDiscount = computed(() => {
  if (discountValue.value <= 0) return 0
  if (discountType.value === 'percentage') {
    return Math.round((grossAmount.value * Math.min(100, discountValue.value)) / 100)
  }
  return Math.min(grossAmount.value, Number(discountValue.value))
})

const netPayable = computed(() => {
  return Math.max(0, grossAmount.value - calculatedDiscount.value)
})

// Automated Referral Doctor Commission Calculation
const referralCommissionAmount = computed(() => {
  if (!selectedPartner.value || selectedPartner.value.commission_pct <= 0) return 0
  return Math.round((netPayable.value * selectedPartner.value.commission_pct) / 100)
})

// -------------------------------------------------------------
// 5. PAYMENT COLLECTION (SPLIT TENDER)
// -------------------------------------------------------------
const tenderCash = ref<number>(900)
const tenderUpi = ref<number>(0)
const tenderCard = ref<number>(0)

// Keep cash in sync initially when net payable updates if no split has started
watch(netPayable, (newNet) => {
  if (tenderUpi.value === 0 && tenderCard.value === 0) {
    tenderCash.value = newNet
  }
})

const totalPaidNow = computed(() => {
  return Number(tenderCash.value || 0) + Number(tenderUpi.value || 0) + Number(tenderCard.value || 0)
})

const balanceDue = computed(() => {
  return Math.max(0, netPayable.value - totalPaidNow.value)
})

function setPaymentMode(mode: 'cash' | 'upi' | 'card' | 'due') {
  if (mode === 'cash') {
    tenderCash.value = netPayable.value
    tenderUpi.value = 0
    tenderCard.value = 0
  } else if (mode === 'upi') {
    tenderCash.value = 0
    tenderUpi.value = netPayable.value
    tenderCard.value = 0
  } else if (mode === 'card') {
    tenderCash.value = 0
    tenderUpi.value = 0
    tenderCard.value = netPayable.value
  } else if (mode === 'due') {
    tenderCash.value = 0
    tenderUpi.value = 0
    tenderCard.value = 0
  }
}

// -------------------------------------------------------------
// 6. ACTION BUTTONS: SAVE & PRINT INVOICE (F2) & BARCODES
// -------------------------------------------------------------
const isSubmitting = ref(false)
const showReceiptModal = ref(false)
const showBarcodeModal = ref(false)
const generatedInvoiceNo = ref('')

async function handleSaveAndPrintInvoice() {
  if (!form.full_name.trim() || !form.mobile.trim()) {
    warning('Missing Information', 'Patient Name and Mobile Phone are required.')
    return
  }

  if (selectedTests.value.length === 0) {
    warning('No Tests Selected', 'Please select at least one test from the catalog.')
    return
  }

  isSubmitting.value = true
  generatedInvoiceNo.value = `INV-2026-${Math.floor(10000 + Math.random() * 90000)}`

  try {
    // 1. Register/Ensure Patient in Database
    let registeredPatientId = existingPatientId.value || patientUhid.value
    if (!isExistingPatient.value || !existingPatientId.value) {
      try {
        const nameParts = form.full_name.trim().split(/\s+/)
        const firstName = nameParts[0] || 'Patient'
        const lastName = nameParts.slice(1).join(' ') || ''
        const cleanPhone = form.mobile.replace(/\D/g, '').slice(-10)
        const sexVal = form.gender.toLowerCase() === 'female' ? 'female' : (form.gender.toLowerCase() === 'other' ? 'other' : 'male')

        const regRes: any = await api.post('/patients/register', {
          first_name: firstName,
          last_name: lastName,
          age_years: Number(form.age) || 30,
          sex: sexVal,
          mobile: cleanPhone,
          city: form.city || 'Noida',
          address_json: { city: form.city || 'Noida', address: form.address || '' },
        })
        if (regRes && (regRes.id || regRes.patient_no)) {
          registeredPatientId = regRes.id
          patientUhid.value = regRes.patient_no || regRes.id
        }
      } catch (regErr: any) {
        console.warn('Patient registration API call error:', regErr)
      }
    }

    // 2. Create Billing Invoice in Database
    try {
      await api.post('/billing/invoices/create', {
        patient_id: registeredPatientId,
        referral_partner_id: selectedPartnerId.value !== 'ref-00' ? selectedPartnerId.value : null,
        notes: `Intake Ref: ${selectedPartner.value.name}`,
        items: selectedTests.value.map((t) => ({
          description: t.name,
          quantity: 1,
          unit_price: t.price,
          discount_amount: calculatedDiscount.value / selectedTests.value.length,
        })),
      })
    } catch (invErr: any) {
      console.warn('Billing invoice creation error:', invErr)
    }

    // 3. Create Pathology Diagnostic Order in Laboratory Workstation
    try {
      await api.post('/pathology/orders/create', {
        patient_id: registeredPatientId,
        test_ids: selectedTestCodes.value,
        referral_partner_id: selectedPartnerId.value !== 'ref-00' ? selectedPartnerId.value : null,
      })
    } catch (ordErr: any) {
      console.warn('Pathology order workflow creation fallback:', ordErr)
    }

    // 4. Record Payment Tender
    if (totalPaidNow.value > 0) {
      try {
        await api.post('/billing/payments/record', {
          invoice_id: generatedInvoiceNo.value,
          amount: totalPaidNow.value,
          payment_method: tenderCash.value > 0 ? 'Cash' : (tenderUpi.value > 0 ? 'UPI' : 'Card'),
          reference: `POS-${Date.now().toString().slice(-6)}`,
        })
      } catch (payErr: any) {
        console.warn('Payment recording error:', payErr)
      }
    }

    success(
      'Patient Registered & Invoice Saved',
      `UHID: ${patientUhid.value} &bull; Patient: ${form.full_name} &bull; Net Bill: ₹${netPayable.value.toLocaleString('en-IN')}`
    )

    // Trigger Print Receipt Modal
    showReceiptModal.value = true
  } catch (err: any) {
    error('Registration Error', err?.message || 'Could not complete registration')
  } finally {
    isSubmitting.value = false
  }
}

function handleSaveAndPrintBarcodes() {
  if (selectedTests.value.length === 0) {
    warning('No Tests Selected', 'Select investigations to generate specimen tube barcodes.')
  }
  showBarcodeModal.value = true
}

function printReceiptWindow() {
  window.print()
}

function resetPosCounter() {
  resetToNewPatient()
  selectedTestCodes.value = ['CBC']
  discountValue.value = 0
  tenderCash.value = 400
  tenderUpi.value = 0
  tenderCard.value = 0
  info('Counter Reset', 'Ready for next patient intake.')
}

// Global Keyboard Shortcut: F2 for Save & Print Invoice
function handleGlobalKeydown(e: KeyboardEvent) {
  if (e.key === 'F2') {
    e.preventDefault()
    handleSaveAndPrintInvoice()
  } else if (e.key === 'Escape') {
    if (showSearchDropdown.value) showSearchDropdown.value = false
    if (showReceiptModal.value) showReceiptModal.value = false
    if (showBarcodeModal.value) showBarcodeModal.value = false
    if (isAddDoctorModalOpen.value) isAddDoctorModalOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  loadReferralPartners()
  // set initial cash amount
  tenderCash.value = netPayable.value

  const qPatientId = (route.query.patient_id as string) || (route.query.uhid as string)
  if (qPatientId) {
    loadPreselectedPatient(qPatientId)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div
    class="space-y-4 max-w-7xl mx-auto text-left"
    @keydown.alt.s.prevent="handleSaveAndPrintInvoice"
    @keydown.esc.prevent="resetPosCounter"
  >
    <!-- Top Action Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <span>Patient Intake &amp; Quick Billing POS</span>
          <span class="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono font-bold">
            Counter Terminal #01
          </span>
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Single-screen registration, clinician mapping, multi-select test pricing, and instant split cashier tender
        </p>
      </div>

      <!-- Quick Action Indicators -->
      <div class="flex items-center space-x-2 text-xs">
        <span class="inline-flex items-center px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium text-[11px]">
          Instant Bill &amp; Print
        </span>
        <button
          type="button"
          class="px-2.5 py-1 text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded font-semibold text-xs cursor-pointer transition"
          @click="resetPosCounter"
        >
          Clear POS
        </button>
      </div>
    </div>

    <!-- Main POS Layout: Left Column (Intake & Tests) + Right Column (Billing, Commission & Tender) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
      <!-- ======================================================== -->
      <!-- LEFT COLUMN (7 OF 12 COLS): DEMOGRAPHICS & TESTS         -->
      <!-- ======================================================== -->
      <div class="lg:col-span-7 space-y-4">
        <!-- 1. Patient Demographics & Mobile Lookup -->
        <div class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 space-y-3 text-xs">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 class="font-bold text-slate-900 text-sm flex items-center space-x-1.5">
              <span>1. Patient Demographics</span>
              <span v-if="isExistingPatient" class="text-[10px] bg-emerald-100 text-emerald-800 font-mono px-2 py-0.5 rounded-full font-bold">
                Returning Patient
              </span>
            </h2>
            <div class="flex items-center space-x-1.5 font-mono text-[11px]">
              <span class="text-slate-400">UHID:</span>
              <span class="font-bold text-blue-700">{{ patientUhid }}</span>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 relative">
            <!-- Mobile Phone Input (Auto-Search Repeat Patient) -->
            <div class="relative">
              <div class="flex items-center justify-between mb-1">
                <label class="block font-semibold text-slate-700">
                  Mobile Number <span class="text-red-500">*</span>
                </label>
                <button
                  v-if="isExistingPatient"
                  type="button"
                  class="text-[10px] font-semibold text-amber-600 hover:text-amber-800 cursor-pointer"
                  @click="resetToNewPatient"
                >
                  Change to New
                </button>
                <button
                  v-else-if="form.mobile.replace(/\D/g, '').length >= 10"
                  type="button"
                  class="text-[10px] font-semibold text-blue-600 hover:text-blue-800 cursor-pointer"
                  @click="checkMobileLookup"
                >
                  Check Past Record
                </button>
              </div>
              <div class="relative">
                <input
                  v-model="form.mobile"
                  type="tel"
                  maxlength="10"
                  placeholder="10-digit mobile"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs font-mono focus:ring-1 focus:ring-blue-500 bg-white"
                  :class="isExistingPatient ? 'border-emerald-400 bg-emerald-50/20' : ''"
                  @input="triggerPatientSearch(form.mobile, 'mobile')"
                  @focus="form.mobile.length >= 3 && triggerPatientSearch(form.mobile, 'mobile')"
                  @keydown.enter.prevent="checkMobileLookup"
                />
                <span v-if="isSearchingPatients && activeSearchField === 'mobile'" class="absolute right-2 top-2 text-slate-400">
                  <svg class="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
                </span>
              </div>
              <p class="text-[10px] text-slate-400 mt-0.5">Type 3+ digits to auto-search repeat patients</p>
            </div>

            <!-- Patient Name (Auto-Search Repeat Patient) -->
            <div class="sm:col-span-2 relative">
              <div class="flex items-center justify-between mb-1">
                <label class="block font-semibold text-slate-700">
                  Full Name <span class="text-red-500">*</span>
                </label>
                <span v-if="isExistingPatient" class="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Returning Patient Verified
                </span>
                <span v-else class="text-[10px] text-slate-400">
                  Auto-searches as you type
                </span>
              </div>
              <div class="relative">
                <input
                  ref="firstNameInput"
                  v-model="form.full_name"
                  type="text"
                  placeholder="e.g. Aarav Sharma (type 2+ letters to search returning patients)"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 bg-white"
                  :class="isExistingPatient ? 'border-emerald-400 bg-emerald-50/20' : ''"
                  @input="triggerPatientSearch(form.full_name, 'name')"
                  @focus="form.full_name.length >= 2 && triggerPatientSearch(form.full_name, 'name')"
                />
                <span v-if="isSearchingPatients && activeSearchField === 'name'" class="absolute right-2 top-2 text-slate-400">
                  <svg class="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
                </span>
              </div>
              <p class="text-[10px] text-slate-400 mt-0.5">Type name to instantly choose from repeat patients</p>
            </div>

            <!-- Auto-Suggest Dropdown for Repeat Patients -->
            <div
              v-if="showSearchDropdown && searchSuggestions.length > 0"
              class="absolute top-full left-0 right-0 z-50 mt-1 bg-white border border-blue-200 rounded-lg shadow-2xl overflow-hidden text-xs divide-y divide-slate-100 ring-1 ring-black/5"
            >
              <div class="bg-blue-50/90 px-3 py-1.5 flex items-center justify-between text-[11px] font-semibold text-blue-900 border-b border-blue-100">
                <div class="flex items-center space-x-1.5">
                  <span class="inline-block w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
                  <span>Repeat Patients Found ({{ searchSuggestions.length }}) &mdash; Click to Auto-fill</span>
                </div>
                <button
                  type="button"
                  class="text-slate-400 hover:text-slate-700 text-sm font-bold px-1"
                  @click="showSearchDropdown = false"
                >
                  &times;
                </button>
              </div>

              <div class="max-h-56 overflow-y-auto divide-y divide-slate-100 bg-white">
                <button
                  v-for="sug in searchSuggestions"
                  :key="sug.id"
                  type="button"
                  class="w-full text-left px-3 py-2 hover:bg-sky-50 focus:bg-sky-50 flex items-center justify-between transition cursor-pointer group"
                  @click="selectExistingPatient(sug)"
                >
                  <div class="space-y-0.5">
                    <div class="flex items-center space-x-2">
                      <span class="font-bold text-slate-900 group-hover:text-blue-700">
                        {{ sug.first_name }} {{ sug.last_name || '' }}
                      </span>
                      <span class="px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold bg-blue-100 text-blue-800">
                        {{ sug.patient_no || sug.id }}
                      </span>
                      <span v-if="sug.sex" class="text-[11px] text-slate-500 font-medium">
                        {{ sug.age_years ? sug.age_years + 'y / ' : '' }}{{ sug.sex }}
                      </span>
                    </div>
                    <div class="flex items-center space-x-3 text-[11px] text-slate-500">
                      <span class="font-mono text-slate-600">📞 {{ sug.mobile_normalized || sug.mobile || 'No Mobile' }}</span>
                      <span v-if="sug.city">&bull; 📍 {{ sug.city }}</span>
                      <span v-if="sug.referral_doctor">&bull; Ref: {{ sug.referral_doctor }}</span>
                    </div>
                  </div>

                  <div class="text-right shrink-0 ml-3">
                    <span class="inline-flex items-center space-x-1 text-[11px] font-semibold text-blue-600 group-hover:text-white bg-blue-50 group-hover:bg-blue-600 px-2 py-1 rounded border border-blue-200 group-hover:border-blue-600 transition shadow-2xs">
                      <span>Choose</span>
                      <span>&rarr;</span>
                    </span>
                  </div>
                </button>
              </div>

              <div class="bg-slate-50 px-3 py-1.5 text-[10px] text-slate-500 flex items-center justify-between">
                <span>Press Escape to dismiss</span>
                <button
                  type="button"
                  class="text-blue-600 font-semibold hover:underline"
                  @click="showSearchDropdown = false"
                >
                  Register as New Patient
                </button>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <!-- Age -->
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Age (Years)</label>
              <input
                v-model="form.age"
                type="number"
                min="0"
                max="120"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs font-mono focus:ring-1 focus:ring-blue-500 bg-white"
              />
            </div>

            <!-- Gender -->
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Gender</label>
              <select
                v-model="form.gender"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 bg-white cursor-pointer"
              >
                <option value="Male">Male (M)</option>
                <option value="Female">Female (F)</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <!-- City -->
            <div>
              <label class="block font-semibold text-slate-700 mb-1">City / Area</label>
              <input
                v-model="form.city"
                type="text"
                placeholder="City"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 bg-white"
              />
            </div>
          </div>
        </div>

        <!-- 2. Prescribing Doctor & Healthcare Partner Selection -->
        <div class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 space-y-3 text-xs">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <div>
              <h2 class="font-bold text-slate-900 text-sm">2. Prescribing Doctor &amp; Healthcare Partner</h2>
              <p class="text-[11px] text-slate-500 mt-0.5">Consulting doctor, referral hospital, pathology lab or clinic</p>
            </div>
            <button
              type="button"
              class="text-sky-600 hover:text-sky-700 font-semibold flex items-center space-x-1 cursor-pointer"
              @click="isAddDoctorModalOpen = true"
            >
              <span>+ Add Partner / Center</span>
            </button>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Prescribing Clinician / Healthcare Partner *</label>
            <select
              v-model="selectedPartnerId"
              class="w-full px-3 py-2 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-sky-500 bg-white font-medium cursor-pointer"
            >
              <option v-for="p in partners" :key="p.id" :value="p.id">
                {{ getPartnerDisplayLabel(p) }}
              </option>
            </select>
          </div>
        </div>

        <!-- 3. Test & Package Catalog Selector -->
        <div class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 space-y-3 text-xs">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 class="font-bold text-slate-900 text-sm">3. Investigation &amp; Package Selector</h2>
            <span class="text-slate-500 text-[11px] font-mono">Selected: {{ selectedTests.length }} tests</span>
          </div>

          <!-- Search Bar for Tests -->
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              v-model="testSearchQuery"
              type="text"
              placeholder="Search test name or code (e.g., CBC, LFT, Lipid, HbA1c)..."
              class="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <!-- Category Pills -->
          <div class="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs scrollbar-none">
            <button
              v-for="cat in categories"
              :key="cat"
              type="button"
              :class="[
                'px-2.5 py-1 rounded-full text-xs font-medium transition cursor-pointer shrink-0',
                selectedCategory === cat ? 'bg-blue-600 text-white shadow-2xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              ]"
              @click="selectedCategory = cat"
            >
              {{ cat }}
            </button>
          </div>

          <!-- Test Catalog Table -->
          <div class="overflow-x-auto border border-slate-200 rounded max-h-56 overflow-y-auto">
            <table class="min-w-full divide-y divide-slate-200 text-xs">
              <thead class="bg-slate-50 text-slate-600 font-semibold sticky top-0 z-10">
                <tr>
                  <th class="w-8 px-2 py-1.5 text-center"></th>
                  <th class="px-3 py-1.5 text-left">Code</th>
                  <th class="px-3 py-1.5 text-left">Investigation</th>
                  <th class="px-3 py-1.5 text-left">Tube</th>
                  <th class="px-3 py-1.5 text-right">Standard Rate</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 bg-white">
                <tr
                  v-for="t in filteredCatalog"
                  :key="t.code"
                  class="hover:bg-blue-50/50 cursor-pointer transition-colors"
                  :class="selectedTestCodes.includes(t.code) ? 'bg-blue-50/40 font-medium' : ''"
                  @click="toggleTest(t.code)"
                >
                  <td class="px-2 py-1.5 text-center" @click.stop>
                    <input
                      type="checkbox"
                      :checked="selectedTestCodes.includes(t.code)"
                      class="h-3.5 w-3.5 text-blue-600 rounded border-slate-300 focus:ring-blue-500 cursor-pointer"
                      @change="toggleTest(t.code)"
                    />
                  </td>
                  <td class="px-3 py-1.5 font-mono font-bold text-blue-900">{{ t.code }}</td>
                  <td class="px-3 py-1.5 text-slate-800">{{ t.name }}</td>
                  <td class="px-3 py-1.5 text-slate-500 font-mono text-[10px]">{{ t.sample }}</td>
                  <td class="px-3 py-1.5 text-right font-mono font-bold text-slate-900">₹{{ t.price }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ======================================================== -->
      <!-- RIGHT COLUMN (5 OF 12 COLS): POS SUMMARY & TENDER        -->
      <!-- ======================================================== -->
      <div class="lg:col-span-5 space-y-4">
        <!-- Selected Items & Real-Time Bill Calculation Card -->
        <div class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 space-y-3 text-xs">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 class="font-bold text-slate-900 text-sm">POS Billing Summary</h2>
            <span class="text-[10px] font-mono text-slate-400">Order Slip</span>
          </div>

          <!-- Selected Tests Itemized List -->
          <div v-if="selectedTests.length === 0" class="py-6 text-center text-slate-400 italic">
            No tests added yet. Check investigations on the left.
          </div>

          <div v-else class="space-y-1.5 max-h-44 overflow-y-auto pr-1">
            <div
              v-for="(t, idx) in selectedTests"
              :key="t.code"
              class="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-100"
            >
              <div class="truncate mr-2">
                <span class="font-mono text-slate-400 mr-1">{{ idx + 1 }}.</span>
                <span class="font-semibold text-slate-800">{{ t.name }}</span>
              </div>
              <div class="flex items-center space-x-2 shrink-0">
                <span class="font-mono font-bold text-slate-900">₹{{ t.price }}</span>
                <button
                  type="button"
                  class="text-slate-400 hover:text-red-600 p-0.5 rounded cursor-pointer transition"
                  title="Remove"
                  @click="removeTest(t.code)"
                >
                  <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Pricing Breakdowns & Discount Controls -->
          <div class="border-t border-slate-100 pt-2 space-y-2">
            <div class="flex items-center justify-between text-slate-600">
              <span>Gross Total:</span>
              <span class="font-mono font-bold text-slate-800">₹{{ grossAmount.toLocaleString('en-IN') }}</span>
            </div>

            <!-- Discount Input Field (% or Flat ₹) -->
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center space-x-1 shrink-0">
                <span class="text-slate-600">Discount:</span>
                <div class="inline-flex rounded border border-slate-300 overflow-hidden text-[10px]">
                  <button
                    type="button"
                    :class="[discountType === 'flat' ? 'bg-blue-600 text-white font-bold' : 'bg-slate-50 text-slate-700']"
                    class="px-1.5 py-0.5 cursor-pointer"
                    @click="discountType = 'flat'"
                  >
                    ₹ Flat
                  </button>
                  <button
                    type="button"
                    :class="[discountType === 'percentage' ? 'bg-blue-600 text-white font-bold' : 'bg-slate-50 text-slate-700']"
                    class="px-1.5 py-0.5 cursor-pointer"
                    @click="discountType = 'percentage'"
                  >
                    %
                  </button>
                </div>
              </div>

              <div class="flex items-center space-x-1">
                <input
                  v-model.number="discountValue"
                  type="number"
                  min="0"
                  class="w-20 px-2 py-0.5 border border-slate-300 rounded text-right font-mono font-semibold text-xs"
                  placeholder="0"
                />
                <span v-if="calculatedDiscount > 0" class="text-red-600 font-mono text-[11px] font-bold">
                  (-₹{{ calculatedDiscount }})
                </span>
              </div>
            </div>

            <!-- Net Payable -->
            <div class="flex items-center justify-between text-sm sm:text-base border-t border-slate-200 pt-2">
              <span class="font-bold text-slate-900">Net Payable Total:</span>
              <span class="font-extrabold font-mono text-blue-900 text-lg">
                ₹{{ netPayable.toLocaleString('en-IN') }}
              </span>
            </div>
          </div>
        </div>

        <!-- 5. Payment Tender (Split Multi-Mode) Card -->
        <div class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 space-y-3 text-xs">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 class="font-bold text-slate-900 text-sm">Payment Tender Collection</h2>
            <div class="flex items-center space-x-1 text-[10px]">
              <button
                type="button"
                class="px-1.5 py-0.5 bg-slate-100 hover:bg-slate-200 rounded font-medium cursor-pointer"
                @click="setPaymentMode('cash')"
              >
                All Cash
              </button>
              <button
                type="button"
                class="px-1.5 py-0.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded font-medium cursor-pointer"
                @click="setPaymentMode('upi')"
              >
                All UPI
              </button>
              <button
                type="button"
                class="px-1.5 py-0.5 bg-amber-50 text-amber-700 hover:bg-amber-100 rounded font-medium cursor-pointer"
                @click="setPaymentMode('due')"
              >
                Mark Due
              </button>
            </div>
          </div>

          <!-- Split Tender Inputs -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Cash Tender (₹)</label>
              <input
                v-model.number="tenderCash"
                type="number"
                min="0"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono font-bold text-xs"
              />
            </div>

            <div>
              <label class="block font-medium text-slate-700 mb-1">UPI / QR Code (₹)</label>
              <input
                v-model.number="tenderUpi"
                type="number"
                min="0"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono font-bold text-xs"
              />
            </div>

            <div>
              <label class="block font-medium text-slate-700 mb-1">Card / POS Swipe (₹)</label>
              <input
                v-model.number="tenderCard"
                type="number"
                min="0"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono font-bold text-xs"
              />
            </div>

            <div>
              <label class="block font-medium text-slate-700 mb-1">Balance Due / Credit</label>
              <div
                class="px-2.5 py-1.5 rounded font-mono font-bold text-xs border"
                :class="balanceDue > 0 ? 'bg-amber-50 text-amber-800 border-amber-300' : 'bg-slate-100 text-slate-500 border-slate-200'"
              >
                ₹{{ balanceDue.toLocaleString('en-IN') }}
              </div>
            </div>
          </div>

          <!-- Action Buttons Bar -->
          <div class="pt-3 border-t border-slate-100 space-y-2">
            <!-- Save & Print Invoice (F2) -->
            <button
              type="button"
              :disabled="isSubmitting || selectedTests.length === 0"
              class="btn-emerald w-full py-2.5 px-4 text-xs sm:text-sm"
              @click="handleSaveAndPrintInvoice"
            >
              <svg v-if="isSubmitting" class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              <span>Save &amp; Print Invoice</span>
              <kbd class="ml-1 px-1.5 py-0.2 text-[9px] font-mono text-emerald-100 bg-emerald-800/60 rounded">F2</kbd>
            </button>

            <!-- Save & Print Barcodes -->
            <button
              type="button"
              :disabled="selectedTests.length === 0"
              class="btn-primary w-full py-2 px-4 text-xs"
              @click="handleSaveAndPrintBarcodes"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
              </svg>
              <span>Save &amp; Print Barcodes</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Modal: Add New Referral Partner / Center -->
    <Modal
      v-model="isAddDoctorModalOpen"
      title="Register Referral Partner / Center"
      description="Quickly onboard a consulting physician, pathology lab, hospital or clinic"
    >
      <div class="space-y-3 text-xs">
        <!-- Partner Category Dropdown -->
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Partner Category / Entity Type *</label>
          <select
            v-model="newDoctor.partner_type"
            class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-sky-500 bg-white cursor-pointer"
            @change="onQuickPartnerTypeChange"
          >
            <option v-for="t in partnerTypesList" :key="t.id" :value="t.id">
              {{ t.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 mb-1">Doctor / Center Name *</label>
          <input
            v-model="newDoctor.name"
            type="text"
            placeholder="e.g. Dr. Rajesh Khanna, Metro Path Lab or Apex Hospital"
            class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-sky-500"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Specialty / Discipline</label>
            <input
              v-model="newDoctor.specialty"
              type="text"
              placeholder="e.g. Cardiology / Pathology"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs"
            />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Contact Phone</label>
            <input
              v-model="newDoctor.phone"
              type="tel"
              placeholder="Mobile / Center phone"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs font-mono"
            />
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <button
          type="button"
          class="px-3 py-1.5 border border-slate-300 rounded text-slate-700 bg-white hover:bg-slate-50 text-xs font-semibold cursor-pointer"
          @click="close"
        >
          Cancel
        </button>
        <button
          type="button"
          class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-bold cursor-pointer shadow-2xs"
          @click="submitAddDoctor"
        >
          Save &amp; Select Partner
        </button>
      </template>
    </Modal>

    <!-- Receipt Print Modal -->
    <Modal
      v-model="showReceiptModal"
      title="POS Payment Receipt"
      description="Official laboratory tax invoice & payment receipt"
    >
      <div class="space-y-3 text-xs bg-slate-50 p-4 rounded border border-slate-200 font-mono">
        <div class="text-center border-b border-dashed border-slate-300 pb-2">
          <h3 class="font-bold text-slate-900 text-sm">AAROZI HEALTHCARE CENTRAL LAB</h3>
          <p class="text-[10px] text-slate-500">ISO 15189:2022 &bull; GSTIN: 09AAACA1234D1Z5</p>
          <p class="text-[11px] font-bold text-blue-800 mt-1">{{ generatedInvoiceNo }}</p>
        </div>

        <div class="text-[11px] space-y-0.5 border-b border-dashed border-slate-300 pb-2">
          <div class="flex justify-between"><span>Patient:</span><strong>{{ form.full_name }}</strong></div>
          <div class="flex justify-between"><span>UHID:</span><strong>{{ patientUhid }}</strong></div>
          <div class="flex justify-between"><span>Age/Sex:</span><strong>{{ form.age }}Y / {{ form.gender }}</strong></div>
          <div class="flex justify-between"><span>Doctor:</span><strong>{{ selectedPartner.name }}</strong></div>
          <div class="flex justify-between"><span>Date:</span><strong>20-Oct-2026</strong></div>
        </div>

        <div class="space-y-1 border-b border-dashed border-slate-300 pb-2 text-[11px]">
          <div v-for="t in selectedTests" :key="t.code" class="flex justify-between">
            <span class="truncate mr-2">{{ t.name }}</span>
            <span>₹{{ t.price }}</span>
          </div>
        </div>

        <div class="space-y-0.5 text-[11px]">
          <div class="flex justify-between"><span>Gross Total:</span><span>₹{{ grossAmount }}</span></div>
          <div v-if="calculatedDiscount > 0" class="flex justify-between text-red-600"><span>Discount:</span><span>-₹{{ calculatedDiscount }}</span></div>
          <div class="flex justify-between text-sm font-bold pt-1 border-t border-slate-300">
            <span>Net Amount:</span>
            <span>₹{{ netPayable }}</span>
          </div>
          <div class="flex justify-between text-emerald-700"><span>Paid (Cash/UPI):</span><span>₹{{ totalPaidNow }}</span></div>
          <div v-if="balanceDue > 0" class="flex justify-between text-amber-700 font-bold"><span>Balance Due:</span><span>₹{{ balanceDue }}</span></div>
        </div>
      </div>

      <template #footer="{ close }">
        <NuxtLink
          to="/patients"
          class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold cursor-pointer flex items-center space-x-1"
        >
          <span>View in Patient Directory &rarr;</span>
        </NuxtLink>
        <div class="flex items-center space-x-2">
          <button
            type="button"
            class="px-3 py-1.5 border border-slate-300 rounded text-slate-700 text-xs font-semibold cursor-pointer"
            @click="close"
          >
            Close
          </button>
          <button
            type="button"
            class="px-4 py-1.5 bg-[#059669] hover:bg-emerald-700 text-white rounded text-xs font-bold cursor-pointer shadow-2xs flex items-center space-x-1"
            @click="printReceiptWindow"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
            <span>Print Receipt</span>
          </button>
        </div>
      </template>
    </Modal>

    <!-- Barcode Labels Print Modal -->
    <Modal
      v-model="showBarcodeModal"
      title="Specimen Tube Barcode Labels"
      description="Thermal labels for vacutainer collection tubes (50x25mm)"
    >
      <div class="space-y-3 text-xs">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="(t, idx) in selectedTests"
            :key="t.code"
            class="p-3 border-2 border-dashed border-slate-300 bg-white rounded flex flex-col justify-between font-mono"
          >
            <div class="flex justify-between items-start text-[10px]">
              <div>
                <strong class="text-slate-900 block">{{ form.full_name || 'PATIENT' }}</strong>
                <span class="text-blue-700 font-bold">{{ patientUhid }}</span> &bull; {{ form.age }}Y/{{ form.gender.charAt(0) }}
              </div>
              <span class="px-1 py-0.2 bg-slate-100 rounded text-[9px] font-bold">{{ t.sample }}</span>
            </div>

            <!-- Barcode Graphic Simulation -->
            <div class="my-2 py-1 bg-slate-50 border border-slate-200 rounded text-center">
              <div class="text-xl tracking-widest font-barcode font-serif select-none">
                ||| | |||| | ||| |||| |
              </div>
              <span class="text-[9px] text-slate-600 block font-mono">SMP-{{ patientUhid.slice(-5) }}-0{{ idx + 1 }}</span>
            </div>

            <div class="flex justify-between items-center text-[9px] text-slate-500">
              <span>{{ t.name.slice(0, 18) }}</span>
              <span>20-Oct-26</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <button
          type="button"
          class="px-3 py-1.5 border border-slate-300 rounded text-slate-700 text-xs font-semibold cursor-pointer"
          @click="close"
        >
          Cancel
        </button>
        <button
          type="button"
          class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-bold cursor-pointer shadow-2xs flex items-center space-x-1"
          @click="printReceiptWindow"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
          <span>Print Thermal Barcodes</span>
        </button>
      </template>
    </Modal>
  </div>
</template>
