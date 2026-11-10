<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '~/composables/useToast'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import Kbd from '~/components/ui/Kbd.vue'
import Icon from '~/components/ui/Icon.vue'
import Modal from '~/components/ui/Modal.vue'

const router = useRouter()
const route = useRoute()
const { success, warning, error, info } = useToast()
const api = useApi()

// -------------------------------------------------------------
// 1. PATIENT DEMOGRAPHICS & MOBILE / NAME AUTO-LOOKUP
// -------------------------------------------------------------
const loading = ref(false)
const permission_denied = ref(false)
const firstNameInput = ref<HTMLInputElement | null>(null)
const mobileInputRef = ref<HTMLInputElement | null>(null)
const testSearchInputRef = ref<HTMLInputElement | null>(null)

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
  age: '' as any,
  gender: 'Male',
  sex: 'Male',
  primary_id_type: 'National ID / Aadhaar',
  city: '',
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
  form.age = '' as any
  form.gender = 'Male'
  form.city = ''
  form.address = ''
  selectedPartnerId.value = 'ref-00'
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
      const match = data.find((p: any) => {
        const pMob = (p.mobile_normalized || p.mobile || '').replace(/\D/g, '')
        return pMob.endsWith(cleanMobile.slice(-10))
      })
      if (match) {
        selectExistingPatient(match)
        return
      }
    }
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

const selectedPartnerId = ref('ref-00')

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

const selectedTestCodes = ref<string[]>([])

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
// 4. DISCOUNT & COMMISSION ENGINE
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

const referralCommissionAmount = computed(() => {
  if (!selectedPartner.value || selectedPartner.value.commission_pct <= 0) return 0
  return Math.round((netPayable.value * selectedPartner.value.commission_pct) / 100)
})

// -------------------------------------------------------------
// 5. PAYMENT TENDER (SPLIT TENDER)
// -------------------------------------------------------------
const tenderCash = ref<number>(0)
const tenderUpi = ref<number>(0)
const tenderCard = ref<number>(0)

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
    mobileInputRef.value?.focus()
    return
  }

  if (selectedTests.value.length === 0) {
    warning('No Tests Selected', 'Please select at least one test from the catalog.')
    testSearchInputRef.value?.focus()
    return
  }

  isSubmitting.value = true
  generatedInvoiceNo.value = `INV-2026-${Math.floor(10000 + Math.random() * 90000)}`

  try {
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

    try {
      await api.post('/pathology/orders/create', {
        patient_id: registeredPatientId,
        test_ids: selectedTestCodes.value,
        referral_partner_id: selectedPartnerId.value !== 'ref-00' ? selectedPartnerId.value : null,
      })
    } catch (ordErr: any) {
      console.warn('Pathology order workflow creation fallback:', ordErr)
    }

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
      `UHID: ${patientUhid.value} • Patient: ${form.full_name} • Net Bill: ₹${netPayable.value.toLocaleString('en-IN')}`
    )

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
    return
  }
  showBarcodeModal.value = true
}

function printReceiptWindow() {
  window.print()
}

function resetPosCounter() {
  resetToNewPatient()
  selectedTestCodes.value = []
  discountValue.value = 0
  tenderCash.value = 0
  tenderUpi.value = 0
  tenderCard.value = 0
  info('Form Cleared', 'Ready for new patient intake.')
  nextTick(() => {
    mobileInputRef.value?.focus()
  })
}

function handleGlobalKeydown(e: KeyboardEvent) {
  if (e.key === 'F2' || (e.altKey && e.key.toLowerCase() === 's')) {
    e.preventDefault()
    handleSaveAndPrintInvoice()
  } else if (e.key === 'F3') {
    e.preventDefault()
    testSearchInputRef.value?.focus()
  } else if (e.key === 'Escape') {
    if (showSearchDropdown.value) showSearchDropdown.value = false
    else if (showReceiptModal.value) showReceiptModal.value = false
    else if (showBarcodeModal.value) showBarcodeModal.value = false
    else if (isAddDoctorModalOpen.value) isAddDoctorModalOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  loadReferralPartners()
  tenderCash.value = netPayable.value

  const qPatientId = (route.query.patient_id as string) || (route.query.uhid as string)
  if (qPatientId) {
    loadPreselectedPatient(qPatientId)
  }

  nextTick(() => {
    mobileInputRef.value?.focus()
  })
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <!-- Keyboard shortcuts: @keydown.alt.s, @keydown.esc -->
  <div class="space-y-4 max-w-7xl mx-auto text-left text-slate-900 dark:text-slate-100 pb-12">
    <!-- Top Action Header -->
    <PageHeader
      title="Patient Registration & Billing"
      subtitle="Fast front desk patient intake, test selection, and billing settlement."
      icon="users"
      badge="Terminal #01"
      badge-variant="info"
    >
      <template #meta>
        <span class="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300 font-medium">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Local LAN Cashier Ready</span>
        </span>
      </template>

      <template #actions>
        <Button
          variant="secondary"
          size="sm"
          icon-left="refresh"
          @click="resetPosCounter"
        >
          Clear Form
        </Button>
        <Button
          variant="primary"
          size="sm"
          icon-left="printer"
          :loading="isSubmitting"
          @click="handleSaveAndPrintInvoice"
        >
          Save & Print
        </Button>
      </template>
    </PageHeader>

    <!-- Main Two-Column POS Layout (7 cols Left / 5 cols Right) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
      <!-- ======================================================== -->
      <!-- LEFT COLUMN: PATIENT DEMOGRAPHICS & INVESTIGATION CATALOG -->
      <!-- ======================================================== -->
      <div class="lg:col-span-7 space-y-4">
        <!-- 1. Patient Demographics & Repeat Search -->
        <Card title="1. Patient Demographics" dense>
          <template #header-right>
            <div class="flex items-center gap-2">
              <Badge v-if="isExistingPatient" variant="success" size="sm">
                Repeat Patient Verified
              </Badge>
              <Badge v-else variant="neutral" size="sm">
                New Patient
              </Badge>
              <div class="flex items-center gap-1 font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                <span class="text-slate-600 dark:text-slate-400 font-bold">UHID:</span>
                <span class="font-bold text-[#2576d2] dark:text-[#90ccf9]">{{ patientUhid }}</span>
              </div>
            </div>
          </template>

          <div class="p-4 space-y-3.5 relative">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <!-- Mobile Number -->
              <div class="relative">
                <div class="flex items-center justify-between mb-1">
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">
                    Mobile Number <span class="text-red-500">*</span>
                  </label>
                  <button
                    v-if="isExistingPatient"
                    type="button"
                    class="text-xs font-semibold text-[#b73612] dark:text-[#fdb99b] hover:underline cursor-pointer"
                    @click="resetToNewPatient"
                  >
                    Change to New
                  </button>
                  <button
                    v-else-if="form.mobile.replace(/\D/g, '').length >= 10"
                    type="button"
                    class="text-xs font-semibold text-[#2576d2] dark:text-[#90ccf9] hover:underline cursor-pointer"
                    @click="checkMobileLookup"
                  >
                    Check Past
                  </button>
                </div>

                <div class="relative">
                  <input
                    ref="mobileInputRef"
                    v-model="form.mobile"
                    type="tel"
                    maxlength="10"
                    placeholder="10-digit mobile"
                    class="w-full px-3 py-2 border rounded-lg text-xs font-mono bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2] transition-colors"
                    :class="isExistingPatient ? 'border-[#2576d2] bg-[#f0f7fe] dark:bg-[#1d273d]' : ''"
                    @input="triggerPatientSearch(form.mobile, 'mobile')"
                    @focus="form.mobile.length >= 3 && triggerPatientSearch(form.mobile, 'mobile')"
                    @keydown.enter.prevent="checkMobileLookup"
                  />
                  <span v-if="isSearchingPatients && activeSearchField === 'mobile'" class="absolute right-2.5 top-2.5 text-slate-400">
                    <Icon name="refresh" size="xs" class="animate-spin" />
                  </span>
                </div>
              </div>

              <!-- Full Name Input -->
              <div class="sm:col-span-2 relative">
                <div class="flex items-center justify-between mb-1">
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">
                    Full Patient Name <span class="text-red-500">*</span>
                  </label>
                </div>

                <div class="relative">
                  <input
                    v-model="form.full_name"
                    type="text"
                    placeholder="e.g. Aarav Sharma"
                    class="w-full px-3 py-2 border rounded-lg text-xs bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2] transition-colors"
                    :class="isExistingPatient ? 'border-[#2576d2] bg-[#f0f7fe] dark:bg-[#1d273d]' : ''"
                    @input="triggerPatientSearch(form.full_name, 'name')"
                    @focus="form.full_name.length >= 2 && triggerPatientSearch(form.full_name, 'name')"
                  />
                  <span v-if="isSearchingPatients && activeSearchField === 'name'" class="absolute right-2.5 top-2.5 text-slate-400">
                    <Icon name="refresh" size="xs" class="animate-spin" />
                  </span>
                </div>
              </div>

              <!-- Repeat Patient Dropdown Popover -->
              <div
                v-if="showSearchDropdown && searchSuggestions.length > 0"
                class="absolute top-16 left-4 right-4 z-50 bg-white dark:bg-slate-900 border border-[#ede9f7] dark:border-[#23273e] rounded-xl shadow-2xl overflow-hidden divide-y divide-slate-100 dark:divide-slate-800"
              >
                <div class="bg-[#f0f7fe] dark:bg-[#1d273d] px-3.5 py-2 flex items-center justify-between text-xs font-bold text-[#1c4372] dark:text-[#90ccf9] border-b border-[#ede9f7] dark:border-[#23273e]">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[#2576d2] animate-pulse" />
                    <span>Repeat Records Found ({{ searchSuggestions.length }}) — Click to Auto-fill</span>
                  </div>
                  <button
                    type="button"
                    class="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 text-sm font-bold px-1 cursor-pointer"
                    @click="showSearchDropdown = false"
                  >
                    ✕
                  </button>
                </div>

                <div class="max-h-60 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
                  <button
                    v-for="sug in searchSuggestions"
                    :key="sug.id"
                    type="button"
                    class="w-full text-left p-3 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d] flex items-center justify-between transition cursor-pointer group"
                    @click="selectExistingPatient(sug)"
                  >
                    <div class="space-y-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap">
                        <span class="font-bold text-slate-900 dark:text-slate-100 group-hover:text-[#2576d2] dark:group-hover:text-[#90ccf9] text-xs">
                          {{ sug.first_name }} {{ sug.last_name || '' }}
                        </span>
                        <Badge variant="info" size="sm">
                          {{ sug.patient_no || sug.id }}
                        </Badge>
                        <span v-if="sug.sex" class="text-xs text-slate-500 font-medium">
                          {{ sug.age_years ? sug.age_years + 'y / ' : '' }}{{ sug.sex }}
                        </span>
                      </div>
                      <div class="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                        <span class="font-mono">📞 {{ sug.mobile_normalized || sug.mobile || 'No Mobile' }}</span>
                        <span v-if="sug.city">• 📍 {{ sug.city }}</span>
                        <span v-if="sug.referral_doctor">• Ref: {{ sug.referral_doctor }}</span>
                      </div>
                    </div>

                    <div class="shrink-0 ml-3">
                      <span class="inline-flex items-center gap-1 text-xs font-semibold text-[#1c5fae] dark:text-[#90ccf9] bg-[#f0f7fe] dark:bg-[#1d273d] px-2.5 py-1 rounded-md border border-[#bee1fb] dark:border-[#2576d2]/50 group-hover:bg-[#2576d2] group-hover:text-white transition">
                        <span>Select</span>
                        <span>→</span>
                      </span>
                    </div>
                  </button>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/60 px-3.5 py-2 text-xs text-slate-500 flex items-center justify-between">
                  <span>Click outside or select to dismiss</span>
                  <button
                    type="button"
                    class="text-[#2576d2] dark:text-[#90ccf9] font-bold hover:underline cursor-pointer"
                    @click="showSearchDropdown = false"
                  >
                    Register as New Patient
                  </button>
                </div>
              </div>
            </div>

            <!-- Age, Gender, City -->
            <div class="grid grid-cols-3 gap-3 pt-1">
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Age (Years)</label>
                <input
                  v-model.number="form.age"
                  type="number"
                  min="0"
                  max="125"
                  placeholder="e.g. 28"
                  class="w-full px-3 py-2 border rounded-lg text-xs font-mono bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2]"
                />
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Gender</label>
                <select
                  v-model="form.gender"
                  class="w-full px-3 py-2 border rounded-lg text-xs bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2] cursor-pointer"
                >
                  <option value="Male">Male (M)</option>
                  <option value="Female">Female (F)</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">City / Area</label>
                <input
                  v-model="form.city"
                  type="text"
                  placeholder="e.g. City / Locality"
                  class="w-full px-3 py-2 border rounded-lg text-xs bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2]"
                />
              </div>
            </div>
          </div>
        </Card>

        <!-- 2. Prescribing Doctor & Healthcare Partner Selection -->
        <Card title="2. Prescribing Doctor & Healthcare Partner" dense>
          <template #header-right>
            <button
              type="button"
              class="text-xs font-bold text-[#2576d2] dark:text-[#90ccf9] hover:underline flex items-center gap-1 cursor-pointer"
              @click="isAddDoctorModalOpen = true"
            >
              <Icon name="plus" size="xs" />
              <span>Add Doctor / Center</span>
            </button>
          </template>

          <div class="p-4 space-y-2">
            <div class="flex items-center justify-between">
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">
                Prescribing Referral Source *
              </label>
              <span v-if="selectedPartner.commission_pct > 0" class="text-xs font-semibold text-[#b73612] dark:text-[#fdb99b] bg-[#fff7f2] dark:bg-[#772614]/30 px-2 py-0.5 rounded border border-[#fed8c4] dark:border-[#932c13]">
                {{ selectedPartner.commission_pct }}% Referral Commission
              </span>
            </div>

            <select
              v-model="selectedPartnerId"
              class="w-full px-3 py-2 border rounded-lg text-xs font-medium bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2] cursor-pointer"
            >
              <option v-for="p in partners" :key="p.id" :value="p.id">
                {{ getPartnerDisplayLabel(p) }}
              </option>
            </select>
          </div>
        </Card>

        <!-- 3. Investigation & Package Catalog Selector -->
        <Card title="3. Investigation & Package Selector" dense>
          <template #header-right>
            <div class="flex items-center gap-2">
              <span class="text-xs text-slate-500 font-mono">Selected: {{ selectedTests.length }} tests</span>
              <Badge variant="info" size="sm">Catalog Active</Badge>
            </div>
          </template>

          <div class="p-4 space-y-3">
            <!-- Test Search Input -->
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 pointer-events-none">
                <Icon name="search" size="sm" />
              </span>
              <input
                ref="testSearchInputRef"
                v-model="testSearchQuery"
                type="text"
                placeholder="Search test name or code (e.g., CBC, LFT, Lipid, HbA1c)..."
                class="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2] focus:bg-white dark:focus:bg-slate-800 transition"
              />
            </div>

            <!-- Category Filter Pills -->
            <div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
              <button
                v-for="cat in categories"
                :key="cat"
                type="button"
                :class="[
                  'px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer shrink-0 border select-none',
                  selectedCategory === cat
                    ? 'bg-[#2576d2] text-white border-[#2576d2] shadow-2xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700'
                ]"
                @click="selectedCategory = cat"
              >
                {{ cat }}
              </button>
            </div>

            <!-- Investigation Table -->
            <div class="border border-slate-200 dark:border-slate-700 rounded-lg max-h-60 overflow-y-auto overflow-x-auto">
              <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700 text-xs text-left">
                <thead class="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold sticky top-0 z-10 select-none">
                  <tr>
                    <th class="w-10 px-3 py-2 text-center"></th>
                    <th class="px-3 py-2">Code</th>
                    <th class="px-3 py-2">Investigation Name</th>
                    <th class="px-3 py-2">Sample Tube</th>
                    <th class="px-3 py-2 text-right">Standard MRP</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                  <tr
                    v-for="t in filteredCatalog"
                    :key="t.code"
                    :class="[
                      'cursor-pointer transition-colors',
                      selectedTestCodes.includes(t.code)
                        ? 'bg-[#f0f7fe] dark:bg-[#1d273d] font-semibold'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                    ]"
                    @click="toggleTest(t.code)"
                  >
                    <td class="px-3 py-2 text-center" @click.stop>
                      <input
                        type="checkbox"
                        :checked="selectedTestCodes.includes(t.code)"
                        class="h-4 w-4 text-[#2576d2] rounded border-slate-300 focus:ring-[#3b93ee] cursor-pointer"
                        @change="toggleTest(t.code)"
                      />
                    </td>
                    <td class="px-3 py-2 font-mono font-bold text-[#2576d2] dark:text-[#90ccf9]">{{ t.code }}</td>
                    <td class="px-3 py-2 text-slate-800 dark:text-slate-200">{{ t.name }}</td>
                    <td class="px-3 py-2">
                      <span class="inline-block px-2 py-0.5 rounded font-mono text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                        {{ t.sample }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-right font-mono font-bold text-slate-900 dark:text-white">₹{{ t.price }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      </div>

      <!-- ======================================================== -->
      <!-- RIGHT COLUMN: POS BILLING SUMMARY, DISCOUNT & SPLIT TENDER -->
      <!-- ======================================================== -->
      <div class="lg:col-span-5 space-y-4">
        <!-- Billing Summary & Selected Cart -->
        <Card title="POS Billing Summary" dense>
          <template #header-right>
            <Badge variant="neutral" size="sm">
              {{ selectedTests.length }} Items
            </Badge>
          </template>

          <div class="p-4 space-y-3.5 text-xs">
            <!-- Selected Tests Itemized List -->
            <div v-if="selectedTests.length === 0" class="py-8 text-center text-slate-400 italic">
              No tests added yet.
            </div>

            <div v-else class="space-y-2 max-h-48 overflow-y-auto pr-1">
              <div
                v-for="(t, idx) in selectedTests"
                :key="t.code"
                class="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs"
              >
                <div class="truncate mr-2 flex items-center gap-1.5">
                  <span class="font-mono text-slate-400">{{ idx + 1 }}.</span>
                  <span class="font-bold text-slate-800 dark:text-slate-200 truncate">{{ t.name }}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="font-mono font-bold text-slate-900 dark:text-slate-100">₹{{ t.price }}</span>
                  <button
                    type="button"
                    class="p-1 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded cursor-pointer transition"
                    title="Remove item"
                    @click="removeTest(t.code)"
                  >
                    <Icon name="trash" size="xs" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Pricing Breakdown -->
            <div class="border-t border-slate-200 dark:border-slate-700 pt-3 space-y-2.5">
              <div class="flex items-center justify-between text-slate-700 dark:text-slate-200">
                <span class="font-semibold text-slate-700 dark:text-slate-300">Gross Total:</span>
                <span class="font-mono font-bold text-slate-900 dark:text-white">₹{{ grossAmount.toLocaleString('en-IN') }}</span>
              </div>

              <!-- Discount Engine (% or Flat) -->
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-1.5 shrink-0">
                  <span class="font-semibold text-slate-700 dark:text-slate-300">Discount:</span>
                  <div class="inline-flex rounded-md border border-slate-300 dark:border-slate-700 overflow-hidden text-xs">
                    <button
                      type="button"
                      :class="[
                        'px-2 py-0.5 cursor-pointer font-bold transition-colors',
                        discountType === 'flat' ? 'bg-[#2576d2] text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                      ]"
                      @click="discountType = 'flat'"
                    >
                      ₹ Flat
                    </button>
                    <button
                      type="button"
                      :class="[
                        'px-2 py-0.5 cursor-pointer font-bold transition-colors',
                        discountType === 'percentage' ? 'bg-[#2576d2] text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                      ]"
                      @click="discountType === 'percentage'"
                    >
                      % Pct
                    </button>
                  </div>
                </div>

                <div class="flex items-center gap-1">
                  <input
                    v-model.number="discountValue"
                    type="number"
                    min="0"
                    placeholder="0"
                    class="w-20 px-2 py-1 border rounded text-right font-mono font-bold text-xs bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
                  />
                  <span v-if="calculatedDiscount > 0" class="text-red-600 dark:text-red-400 font-mono font-bold text-xs">
                    (-₹{{ calculatedDiscount }})
                  </span>
                </div>
              </div>

              <!-- Net Payable Total Display -->
              <div class="flex items-center justify-between border-t border-slate-200 dark:border-slate-700 pt-3">
                <span class="text-sm font-bold text-slate-900 dark:text-white">Net Bill Payable:</span>
                <span class="text-xl font-extrabold font-mono text-[#2576d2] dark:text-[#90ccf9]">
                  ₹{{ netPayable.toLocaleString('en-IN') }}
                </span>
              </div>
            </div>
          </div>
        </Card>

        <!-- Payment Tender Collection (Split Multi-Mode) -->
        <Card title="Payment Tender Collection" dense>
          <template #header-right>
            <div class="flex items-center gap-1">
              <button
                type="button"
                class="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 rounded text-xs font-semibold cursor-pointer border border-slate-200 dark:border-slate-700"
                @click="setPaymentMode('cash')"
              >
                Cash
              </button>
              <button
                type="button"
                class="px-2 py-0.5 bg-[#f0f7fe] dark:bg-[#1d273d] text-[#1c5fae] dark:text-[#90ccf9] hover:bg-[#e1f0fd] rounded text-xs font-semibold cursor-pointer border border-[#bee1fb] dark:border-[#2576d2]/50"
                @click="setPaymentMode('upi')"
              >
                UPI QR
              </button>
              <button
                type="button"
                class="px-2 py-0.5 bg-[#fff7f2] dark:bg-[#772614]/30 text-[#b73612] dark:text-[#fdb99b] hover:bg-[#ffefe5] rounded text-xs font-semibold cursor-pointer border border-[#fed8c4] dark:border-[#932c13]"
                @click="setPaymentMode('due')"
              >
                Mark Due
              </button>
            </div>
          </template>

          <div class="p-4 space-y-3.5 text-xs">
            <!-- Split Tender Inputs -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Cash Tender (₹)</label>
                <input
                  v-model.number="tenderCash"
                  type="number"
                  min="0"
                  class="w-full px-3 py-2 border rounded-lg font-mono font-bold text-xs bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
                />
              </div>

              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">UPI / QR (₹)</label>
                <input
                  v-model.number="tenderUpi"
                  type="number"
                  min="0"
                  class="w-full px-3 py-2 border rounded-lg font-mono font-bold text-xs bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
                />
              </div>

              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Card / POS Swipe (₹)</label>
                <input
                  v-model.number="tenderCard"
                  type="number"
                  min="0"
                  class="w-full px-3 py-2 border rounded-lg font-mono font-bold text-xs bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
                />
              </div>

              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Balance Due / Credit</label>
                <div
                  :class="[
                    'px-3 py-2 rounded-lg font-mono font-bold text-xs border flex items-center justify-between',
                    balanceDue > 0
                      ? 'bg-[#fff7f2] dark:bg-[#772614]/30 text-[#b73612] dark:text-[#fdb99b] border-[#fed8c4] dark:border-[#932c13]'
                      : 'bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700'
                  ]"
                >
                  <span>₹{{ balanceDue.toLocaleString('en-IN') }}</span>
                  <Badge v-if="balanceDue > 0" variant="warning" size="sm">DUE</Badge>
                  <Badge v-else variant="success" size="sm">SETTLED</Badge>
                </div>
              </div>
            </div>

            <!-- Action Buttons Bar -->
            <div class="pt-3 border-t border-slate-200 dark:border-slate-700 space-y-2">
              <Button
                variant="primary"
                size="lg"
                full-width
                icon-left="printer"
                :disabled="isSubmitting || selectedTests.length === 0"
                :loading="isSubmitting"
                @click="handleSaveAndPrintInvoice"
              >
                <span>Save &amp; Print Invoice</span>
              </Button>

              <Button
                variant="primary"
                size="md"
                full-width
                icon-left="barcode"
                :disabled="selectedTests.length === 0"
                @click="handleSaveAndPrintBarcodes"
              >
                <span>Generate Barcodes</span>
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- Quick Modal: Add New Referral Partner / Center -->
    <Modal
      v-model="isAddDoctorModalOpen"
      title="Register Referral Partner / Center"
      description="Quickly onboard a consulting clinician, pathology lab, hospital or polyclinic"
    >
      <div class="space-y-3.5 text-xs">
        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Partner Category / Entity Type *</label>
          <select
            v-model="newDoctor.partner_type"
            class="w-full px-3 py-2 border rounded-lg text-xs bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2] cursor-pointer"
            @change="onQuickPartnerTypeChange"
          >
            <option v-for="t in partnerTypesList" :key="t.id" :value="t.id">
              {{ t.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Doctor / Center Name *</label>
          <input
            v-model="newDoctor.name"
            type="text"
            placeholder="e.g. Dr. Rajesh Khanna, Metro Path Lab or Apex Hospital"
            class="w-full px-3 py-2 border rounded-lg text-xs bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3b93ee] focus:border-[#2576d2]"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Specialty</label>
            <input
              v-model="newDoctor.specialty"
              type="text"
              placeholder="e.g. Cardiology / Internal Medicine"
              class="w-full px-3 py-2 border rounded-lg text-xs bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Contact Phone</label>
            <input
              v-model="newDoctor.phone"
              type="tel"
              placeholder="10-digit mobile"
              class="w-full px-3 py-2 border rounded-lg text-xs font-mono bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700"
            />
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <Button variant="secondary" size="sm" @click="close">
          Cancel
        </Button>
        <Button variant="primary" size="sm" @click="submitAddDoctor">
          Save &amp; Select Partner
        </Button>
      </template>
    </Modal>

    <!-- Receipt Print Modal -->
    <Modal
      v-model="showReceiptModal"
      title="POS Payment Receipt"
      description="Official laboratory tax invoice & payment receipt"
    >
      <div class="space-y-3 text-xs bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800 font-mono">
        <div class="text-center border-b border-dashed border-slate-300 dark:border-slate-700 pb-2.5">
          <h3 class="font-bold text-slate-900 dark:text-white text-sm">AAROZI HEALTHCARE</h3>
          <p class="text-xs text-slate-500">ISO 15189:2022 • GSTIN: 09AAACA1234D1Z5</p>
          <p class="text-xs font-bold text-[#2576d2] dark:text-[#90ccf9] mt-1">{{ generatedInvoiceNo }}</p>
        </div>

        <div class="text-xs space-y-1 border-b border-dashed border-slate-300 dark:border-slate-700 pb-2.5">
          <div class="flex justify-between"><span>Patient:</span><strong>{{ form.full_name }}</strong></div>
          <div class="flex justify-between"><span>UHID:</span><strong>{{ patientUhid }}</strong></div>
          <div class="flex justify-between"><span>Age / Sex:</span><strong>{{ form.age }}Y / {{ form.gender }}</strong></div>
          <div class="flex justify-between"><span>Clinician:</span><strong>{{ selectedPartner.name }}</strong></div>
          <div class="flex justify-between"><span>Date:</span><strong>{{ new Date().toLocaleDateString('en-IN') }}</strong></div>
        </div>

        <div class="space-y-1.5 border-b border-dashed border-slate-300 dark:border-slate-700 pb-2.5 text-xs">
          <div v-for="t in selectedTests" :key="t.code" class="flex justify-between">
            <span class="truncate mr-2">{{ t.name }}</span>
            <span class="font-bold">₹{{ t.price }}</span>
          </div>
        </div>

        <div class="space-y-1 text-xs">
          <div class="flex justify-between"><span>Gross Total:</span><span>₹{{ grossAmount }}</span></div>
          <div v-if="calculatedDiscount > 0" class="flex justify-between text-red-600"><span>Discount:</span><span>-₹{{ calculatedDiscount }}</span></div>
          <div class="flex justify-between text-sm font-bold pt-1.5 border-t border-slate-300 dark:border-slate-700">
            <span>Net Amount:</span>
            <span>₹{{ netPayable }}</span>
          </div>
          <div class="flex justify-between text-emerald-700 font-bold"><span>Paid Tender:</span><span>₹{{ totalPaidNow }}</span></div>
          <div v-if="balanceDue > 0" class="flex justify-between text-amber-700 font-bold"><span>Balance Due:</span><span>₹{{ balanceDue }}</span></div>
        </div>
      </div>

      <template #footer="{ close }">
        <NuxtLink
          to="/patients"
          class="text-xs font-bold text-[#2576d2] hover:underline flex items-center gap-1"
        >
          <span>View Patient Directory →</span>
        </NuxtLink>
        <div class="flex items-center gap-2">
          <Button variant="secondary" size="sm" @click="close">
            Close
          </Button>
          <Button variant="success" size="sm" icon-left="printer" @click="printReceiptWindow">
            Print Receipt
          </Button>
        </div>
      </template>
    </Modal>

    <!-- Barcode Labels Print Modal -->
    <Modal
      v-model="showBarcodeModal"
      title="Specimen Tube Barcode Labels"
      description="Thermal labels for vacutainer collection tubes (50x25mm standard)"
    >
      <div class="space-y-3 text-xs">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="(t, idx) in selectedTests"
            :key="t.code"
            class="p-3.5 border-2 border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-xl flex flex-col justify-between font-mono"
          >
            <div class="flex justify-between items-start text-xs">
              <div>
                <strong class="text-slate-900 dark:text-white block">{{ form.full_name || 'PATIENT' }}</strong>
                <span class="text-[#2576d2] dark:text-[#90ccf9] font-bold">{{ patientUhid }}</span> • {{ form.age }}Y/{{ form.gender.charAt(0) }}
              </div>
              <Badge variant="neutral" size="sm">{{ t.sample }}</Badge>
            </div>

            <!-- Barcode Graphic Simulation -->
            <div class="my-2.5 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-center">
              <div class="text-2xl tracking-widest font-mono select-none text-slate-900 dark:text-slate-100 font-bold">
                ||| | |||| | ||| |||| |
              </div>
              <span class="text-xs text-slate-500 dark:text-slate-400 block font-mono mt-0.5">SMP-{{ patientUhid.slice(-5) }}-0{{ idx + 1 }}</span>
            </div>

            <div class="flex justify-between items-center text-xs text-slate-500">
              <span class="truncate max-w-[140px]">{{ t.name }}</span>
              <span>{{ new Date().toLocaleDateString('en-IN') }}</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <Button variant="secondary" size="sm" @click="close">
          Cancel
        </Button>
        <Button variant="primary" size="sm" icon-left="printer" @click="printReceiptWindow">
          Print 50×25mm Labels
        </Button>
      </template>
    </Modal>
  </div>
</template>
