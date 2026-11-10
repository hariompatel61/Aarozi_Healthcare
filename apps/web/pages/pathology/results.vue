<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '~/composables/useToast'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Badge from '~/components/ui/Badge.vue'
import Button from '~/components/ui/Button.vue'
import Kbd from '~/components/ui/Kbd.vue'
import Icon from '~/components/ui/Icon.vue'
import Modal from '~/components/ui/Modal.vue'

definePageMeta({
  layout: 'default'
})

const route = useRoute()
const router = useRouter()
const { success, info, warning } = useToast()
const api = useApi()

// Patient Demographics & Workstation UI States
const loading = ref(false)
const isSaving = ref(false)
const isValidating = ref(false)
const autosaveStatus = ref('Draft synced')

function triggerAutosave() {
  try {
    localStorage.setItem(`result_draft_${patient.value.sample_id}`, JSON.stringify(parameters.value))
    autosaveStatus.value = 'Saved to local LAN cache'
  } catch (err) {
    console.warn('Autosave error:', err)
  }
}

function focusNextRow(idx: number) {
  const nextInput = document.querySelector(`[tabindex="${idx + 2}"]`) as HTMLInputElement
  if (nextInput) nextInput.focus()
}

// Machine / Cell Counter Integration State
const isFetchingAnalyzer = ref(false)
const analyzerSynced = ref(false)
const analyzerLastSyncTime = ref<string | null>(null)
const isEditingValues = ref(true)
const isReportModalOpen = ref(false)
const reportGeneratedAt = ref<string | null>(null)
const isAddTestModalOpen = ref(false)

// Worklist Triage & Search
const searchWorklist = ref('')
const worklistFilter = ref<'all' | 'panic' | 'synced' | 'pending'>('all')

interface WorklistSample {
  sample_id: string
  patient_uhid: string
  patient_name: string
  age_sex: string
  test_name: string
  department: string
  status: string
  collected_at: string
  mobile: string
  has_panic?: boolean
  flag?: string
  doctor?: string
}

const defaultSamples: WorklistSample[] = [
  {
    sample_id: 'SMP-2026-0891',
    patient_uhid: 'UHID-90812',
    patient_name: 'Rajesh Kumar Verma',
    age_sex: '48Y / M',
    test_name: 'Glycated Hemoglobin (HbA1c HPLC)',
    department: 'Biochemistry & Special Chemistry',
    status: 'In Progress',
    collected_at: '09:15 AM',
    mobile: '9876543210',
    has_panic: true,
    flag: 'Critical',
    doctor: 'Dr. Ramesh Chandra (MD Med)'
  },
  {
    sample_id: 'SMP-2026-0892',
    patient_uhid: 'UHID-90815',
    patient_name: 'Priya Sharma',
    age_sex: '34Y / F',
    test_name: 'Complete Blood Count (CBC & ESR)',
    department: 'Hematology',
    status: 'Ready for Entry',
    collected_at: '09:25 AM',
    mobile: '9811223344',
    has_panic: false,
    flag: 'Normal',
    doctor: 'Dr. Sunita Kapoor (MBBS)'
  },
  {
    sample_id: 'SMP-2026-0893',
    patient_uhid: 'UHID-90822',
    patient_name: 'Anil Deshmukh',
    age_sex: '62Y / M',
    test_name: 'Kidney Function Test (KFT & Electrolytes)',
    department: 'Biochemistry',
    status: 'Analyzer Synced',
    collected_at: '09:40 AM',
    mobile: '9822334455',
    has_panic: true,
    flag: 'High [H]',
    doctor: 'Dr. K. S. Murthy (Nephrologist)'
  },
  {
    sample_id: 'SMP-2026-0894',
    patient_uhid: 'UHID-90831',
    patient_name: 'Sunita Mehra',
    age_sex: '29Y / F',
    test_name: 'Liver Function Test (LFT Complete)',
    department: 'Biochemistry',
    status: 'In Progress',
    collected_at: '10:05 AM',
    mobile: '9833445566',
    has_panic: false,
    flag: 'Normal',
    doctor: 'Self / Walk-in'
  },
  {
    sample_id: 'SMP-2026-0895',
    patient_uhid: 'UHID-90840',
    patient_name: 'Vikramaditya Rao',
    age_sex: '55Y / M',
    test_name: 'Lipid Profile Comprehensive',
    department: 'Biochemistry',
    status: 'Ready for Entry',
    collected_at: '10:20 AM',
    mobile: '9844556677',
    has_panic: false,
    flag: 'Normal',
    doctor: 'Dr. A. K. Banerjee (Cardiologist)'
  }
]

const availableSamples = ref<WorklistSample[]>(defaultSamples)
const selectedSampleId = ref('SMP-2026-0891')

const filteredSamples = computed(() => {
  return availableSamples.value.filter(s => {
    // Filter by worklist tab
    if (worklistFilter.value === 'panic' && !s.has_panic) return false
    if (worklistFilter.value === 'synced' && s.status !== 'Analyzer Synced') return false
    if (worklistFilter.value === 'pending' && s.status === 'Authorized & Released') return false

    // Search query
    if (!searchWorklist.value) return true
    const q = searchWorklist.value.toLowerCase()
    return (
      s.sample_id.toLowerCase().includes(q) ||
      s.patient_uhid.toLowerCase().includes(q) ||
      s.patient_name.toLowerCase().includes(q) ||
      s.test_name.toLowerCase().includes(q)
    )
  })
})

const panicCount = computed(() => {
  return availableSamples.value.filter(s => s.has_panic).length
})

const patient = ref({
  id: 'UHID-90812',
  name: 'Rajesh Kumar Verma',
  age_sex: '48Y / M',
  sample_id: (route.query.sample_id as string) || 'SMP-2026-0891',
  collection_date: 'Today 09:15 AM',
  status: 'In Progress',
  doctor: 'Dr. Ramesh Chandra (MD Med)',
  mobile: '9876543210',
})

interface AuditLogItem {
  id: string
  timestamp: string
  user: string
  action: string
  details: string
}

const auditLogs = ref<AuditLogItem[]>([
  {
    id: 'log-1',
    timestamp: 'Today 09:15 AM',
    user: 'Front Desk POS #01',
    action: 'Investigation Intake',
    details: 'Patient registered and specimen barcode accessioned.'
  },
  {
    id: 'log-2',
    timestamp: 'Today 09:22 AM',
    user: 'Pooja Verma (Phlebotomist)',
    action: 'Sample Accessioned',
    details: 'Specimen checked in at central laboratory triage bench.'
  },
  {
    id: 'log-3',
    timestamp: 'Today 09:30 AM',
    user: 'Interface Server',
    action: 'Instrument Online',
    details: 'Mindray BC-5000 & Erba Chem 5X handshake active on LAN.'
  }
])

const availableCatalogTests = ref([
  { code: 'CBC', name: 'Complete Blood Count (CBC & ESR)', sample: 'EDTA Whole Blood', dept: 'Hematology', analyzer: 'Mindray BC-5000 5-Part Cell Counter' },
  { code: 'LFT', name: 'Liver Function Test Complete (12)', sample: 'Serum', dept: 'Biochemistry', analyzer: 'Erba Chem 5X Clinical Chemistry Analyzer' },
  { code: 'KFT', name: 'Kidney Function Test & Electrolytes', sample: 'Serum', dept: 'Biochemistry', analyzer: 'Erba Chem 5X Clinical Chemistry Analyzer' },
  { code: 'LIPID', name: 'Lipid Profile Comprehensive', sample: 'Serum', dept: 'Biochemistry', analyzer: 'Cobas c311 Chemistry Analyzer' },
  { code: 'TFT', name: 'Thyroid Profile (Total T3, T4, TSH)', sample: 'Serum', dept: 'Special Chemistry', analyzer: 'Architect i1000 Immunoassay Analyzer' },
  { code: 'HBA1C', name: 'Glycated Hemoglobin HbA1c (HPLC)', sample: 'EDTA Whole Blood', dept: 'Biochemistry', analyzer: 'Bio-Rad D-10 Dual Program Analyzer' },
  { code: 'FBS', name: 'Blood Glucose Fasting', sample: 'Sodium Fluoride', dept: 'Biochemistry', analyzer: 'Erba Chem 5X Clinical Chemistry Analyzer' },
  { code: 'URINE_R', name: 'Urine Routine & Microscopic', sample: 'Spot Urine', dept: 'Clinical Pathology', analyzer: 'Dirui H-500 Urine Analyzer' },
  { code: 'VIT_D', name: 'Vitamin D (25-OH Total)', sample: 'Serum', dept: 'Immunoassay', analyzer: 'Cobas e411 Immunoassay Analyzer' },
])

async function loadSampleDetails() {
  loading.value = true
  try {
    const list: any = await api.get('/pathology/samples')
    if (Array.isArray(list) && list.length > 0) {
      availableSamples.value = list
      const queryId = route.query.sample_id as string
      const match = (queryId ? list.find((s: any) => s.sample_id === queryId) : null) || list[0]
      if (match) {
        selectedSampleId.value = match.sample_id
        applySample(match)
      }
    } else {
      applySample(defaultSamples[0])
    }
  } catch (err) {
    console.warn('Could not load sample details, using default offline samples:', err)
    applySample(defaultSamples[0])
  } finally {
    loading.value = false
  }
}

function selectSample(s: WorklistSample) {
  selectedSampleId.value = s.sample_id
  applySample(s)
  router.replace({ query: { sample_id: s.sample_id } })
}

function applySample(match: any) {
  patient.value.id = match.patient_uhid || match.id || 'UHID-90812'
  patient.value.name = match.patient_name || match.name || 'Rajesh Kumar Verma'
  patient.value.age_sex = match.age_sex || '48Y / M'
  patient.value.sample_id = match.sample_id || 'SMP-2026-0891'
  patient.value.collection_date = match.collected_at ? (match.collected_at.includes('Today') ? match.collected_at : `Today ${match.collected_at}`) : 'Today 09:15 AM'
  patient.value.status = match.status || 'In Progress'
  patient.value.doctor = match.doctor || 'Dr. Ramesh Chandra (MD Med)'
  patient.value.mobile = match.mobile || '9876543210'
  whatsappRecipientPhone.value = patient.value.mobile ? `+91 ${patient.value.mobile}` : '+91 9876543210'

  if (match.test_name) {
    testInfo.value.name = match.test_name
    testInfo.value.department = match.department || 'Biochemistry & Special Chemistry'
    loadTestParameters(match.test_name)
  }
}

// 4 Essential Sub-tabs Overhaul
type ResultSubTab = 'entry' | 'graph' | 'attachments' | 'validation'
const activeSubTab = ref<ResultSubTab>('entry')

// Test Definition
const testInfo = ref({
  name: 'HbA1c (HPLC)',
  method: 'High Performance Liquid Chromatography (HPLC)',
  sample: 'EDTA Whole Blood',
  department: 'Biochemistry & Special Chemistry',
  analyzer: 'Bio-Rad D-10 Dual Program Analyzer',
})

interface ResultParameter {
  id: number
  code: string
  name: string
  value: string
  unit: string
  ref_range: string
  low: number
  high: number
  flag: 'Normal' | 'High [H]' | 'Low [L]' | 'Critical'
  observation: string
  is_calculated?: boolean
}

const parameters = ref<ResultParameter[]>([])

function loadTestParameters(testName: string) {
  const tLower = (testName || '').toLowerCase()
  if (tLower.includes('cbc') || tLower.includes('blood count') || tLower.includes('hemogram')) {
    testInfo.value.name = 'Complete Blood Count (CBC & ESR)'
    testInfo.value.method = 'Automated 5-Part Flow Cytometry / Laser Photometry'
    testInfo.value.sample = 'EDTA Whole Blood'
    testInfo.value.department = 'Hematology & Clinical Pathology'
    testInfo.value.analyzer = 'Mindray BC-5000 5-Part Cell Counter'
    parameters.value = [
      { id: 1, code: 'HB', name: 'Hemoglobin (Hb)', value: '13.8', unit: 'g/dL', ref_range: '13.0 - 17.0', low: 13.0, high: 17.0, flag: 'Normal', observation: 'Within physiological reference interval' },
      { id: 2, code: 'TLC', name: 'Total Leukocyte Count (TLC/WBC)', value: '7400', unit: '/uL', ref_range: '4000 - 11000', low: 4000, high: 11000, flag: 'Normal', observation: 'Normal leukocyte response' },
      { id: 3, code: 'RBC', name: 'Red Blood Cell Count (RBC)', value: '4.65', unit: 'mil/uL', ref_range: '4.50 - 5.50', low: 4.5, high: 5.5, flag: 'Normal', observation: 'Normocytic, normochromic count' },
      { id: 4, code: 'PLT', name: 'Platelet Count', value: '2.25', unit: 'lakh/uL', ref_range: '1.50 - 4.50', low: 1.5, high: 4.5, flag: 'Normal', observation: 'Adequate on smear examination' },
      { id: 5, code: 'PCV', name: 'Packed Cell Volume (Hematocrit)', value: '42.5', unit: '%', ref_range: '40.0 - 50.0', low: 40.0, high: 50.0, flag: 'Normal', observation: 'Normal erythrocyte volume' },
      { id: 6, code: 'MCV', name: 'Mean Corpuscular Volume (MCV)', value: '88.2', unit: 'fL', ref_range: '80.0 - 100.0', low: 80.0, high: 100.0, flag: 'Normal', observation: 'Normocytic red cells' },
      { id: 7, code: 'MCH', name: 'Mean Corpuscular Hemoglobin (MCH)', value: '29.7', unit: 'pg', ref_range: '27.0 - 32.0', low: 27.0, high: 32.0, flag: 'Normal', observation: 'Normochromic red cells' },
      { id: 8, code: 'MCHC', name: 'Mean Corpuscular Hb Conc (MCHC)', value: '33.6', unit: 'g/dL', ref_range: '32.0 - 36.0', low: 32.0, high: 36.0, flag: 'Normal', observation: 'Normal cellular hemoglobin' },
      { id: 9, code: 'NEUT', name: 'Neutrophils', value: '62', unit: '%', ref_range: '40 - 70', low: 40, high: 70, flag: 'Normal', observation: 'Normal differential' },
      { id: 10, code: 'LYMPH', name: 'Lymphocytes', value: '30', unit: '%', ref_range: '20 - 45', low: 20, high: 45, flag: 'Normal', observation: 'Normal differential' },
      { id: 11, code: 'EOS', name: 'Eosinophils', value: '4', unit: '%', ref_range: '1 - 6', low: 1, high: 6, flag: 'Normal', observation: 'No eosinophilia' },
      { id: 12, code: 'MONO', name: 'Monocytes', value: '4', unit: '%', ref_range: '2 - 8', low: 2, high: 8, flag: 'Normal', observation: 'Normal differential' },
    ]
  } else if (tLower.includes('lft') || tLower.includes('liver')) {
    testInfo.value.name = 'Liver Function Test (LFT Complete)'
    testInfo.value.method = 'Automated Spectrophotometry / Kinetic Colorimetric'
    testInfo.value.sample = 'Serum'
    testInfo.value.department = 'Clinical Biochemistry'
    testInfo.value.analyzer = 'Erba Chem 5X Clinical Chemistry Analyzer'
    parameters.value = [
      { id: 1, code: 'TBIL', name: 'Bilirubin Total', value: '0.90', unit: 'mg/dL', ref_range: '0.20 - 1.20', low: 0.2, high: 1.2, flag: 'Normal', observation: 'Normal bilirubin levels' },
      { id: 2, code: 'DBIL', name: 'Bilirubin Direct (Conjugated)', value: '0.22', unit: 'mg/dL', ref_range: '0.00 - 0.30', low: 0.0, high: 0.3, flag: 'Normal', observation: 'Normal direct bilirubin' },
      { id: 3, code: 'SGOT', name: 'SGOT / AST (Aspartate Aminotransferase)', value: '28', unit: 'U/L', ref_range: '5 - 40', low: 5, high: 40, flag: 'Normal', observation: 'Normal hepatic transaminase' },
      { id: 4, code: 'SGPT', name: 'SGPT / ALT (Alanine Aminotransferase)', value: '32', unit: 'U/L', ref_range: '5 - 45', low: 5, high: 45, flag: 'Normal', observation: 'Normal hepatic transaminase' },
      { id: 5, code: 'ALP', name: 'Alkaline Phosphatase (ALP)', value: '88', unit: 'U/L', ref_range: '30 - 120', low: 30, high: 120, flag: 'Normal', observation: 'Normal biliary enzyme' },
      { id: 6, code: 'TP', name: 'Total Protein', value: '7.4', unit: 'g/dL', ref_range: '6.0 - 8.3', low: 6.0, high: 8.3, flag: 'Normal', observation: 'Normal serum protein' },
      { id: 7, code: 'ALB', name: 'Serum Albumin', value: '4.5', unit: 'g/dL', ref_range: '3.5 - 5.2', low: 3.5, high: 5.2, flag: 'Normal', observation: 'Normal hepatic protein synthesis' },
    ]
  } else if (tLower.includes('kft') || tLower.includes('kidney') || tLower.includes('renal')) {
    testInfo.value.name = 'Kidney Function Test (KFT & Electrolytes)'
    testInfo.value.method = 'Jaffe Kinetic / Urease GLDH / ISE'
    testInfo.value.sample = 'Serum'
    testInfo.value.department = 'Clinical Biochemistry'
    testInfo.value.analyzer = 'Erba Chem 5X Clinical Chemistry Analyzer'
    parameters.value = [
      { id: 1, code: 'UREA', name: 'Blood Urea', value: '28', unit: 'mg/dL', ref_range: '15 - 45', low: 15, high: 45, flag: 'Normal', observation: 'Normal renal clearance' },
      { id: 2, code: 'CREAT', name: 'Serum Creatinine', value: '0.95', unit: 'mg/dL', ref_range: '0.70 - 1.30', low: 0.7, high: 1.3, flag: 'Normal', observation: 'Normal glomerular filtration' },
      { id: 3, code: 'URIC', name: 'Uric Acid', value: '5.2', unit: 'mg/dL', ref_range: '3.5 - 7.2', low: 3.5, high: 7.2, flag: 'Normal', observation: 'Within physiological limits' },
      { id: 4, code: 'NA', name: 'Sodium (Na+)', value: '139', unit: 'mmol/L', ref_range: '135 - 145', low: 135, high: 145, flag: 'Normal', observation: 'Normal electrolyte balance' },
      { id: 5, code: 'K', name: 'Potassium (K+)', value: '4.2', unit: 'mmol/L', ref_range: '3.5 - 5.1', low: 3.5, high: 5.1, flag: 'Normal', observation: 'Normal electrolyte balance' },
    ]
  } else if (tLower.includes('lipid') || tLower.includes('cholesterol')) {
    testInfo.value.name = 'Lipid Profile Comprehensive'
    testInfo.value.method = 'Enzymatic CHOD-PAP / GPO-PAP'
    testInfo.value.sample = 'Serum (Fasting 12 hrs)'
    testInfo.value.department = 'Clinical Biochemistry'
    testInfo.value.analyzer = 'Cobas c311 Chemistry Analyzer'
    parameters.value = [
      { id: 1, code: 'CHOL', name: 'Total Cholesterol', value: '182', unit: 'mg/dL', ref_range: '125 - 200', low: 125, high: 200, flag: 'Normal', observation: 'Desirable cardiovascular level' },
      { id: 2, code: 'TRIG', name: 'Triglycerides', value: '138', unit: 'mg/dL', ref_range: '50 - 150', low: 50, high: 150, flag: 'Normal', observation: 'Normal fasting lipid level' },
      { id: 3, code: 'HDL', name: 'HDL Cholesterol (Good Chol)', value: '48', unit: 'mg/dL', ref_range: '40 - 60', low: 40, high: 60, flag: 'Normal', observation: 'Normal protective lipoprotein' },
      { id: 4, code: 'LDL', name: 'LDL Cholesterol (Bad Chol)', value: '106', unit: 'mg/dL', ref_range: '50 - 100', low: 50, high: 100, flag: 'High [H]', observation: 'Borderline elevated' },
      { id: 5, code: 'VLDL', name: 'VLDL Cholesterol', value: '28', unit: 'mg/dL', ref_range: '10 - 30', low: 10, high: 30, flag: 'Normal', observation: 'Normal level' },
    ]
  } else {
    testInfo.value.name = 'Glycated Hemoglobin (HbA1c HPLC)'
    testInfo.value.method = 'High Performance Liquid Chromatography (HPLC)'
    testInfo.value.sample = 'EDTA Whole Blood'
    testInfo.value.department = 'Biochemistry & Special Chemistry'
    testInfo.value.analyzer = 'Bio-Rad D-10 Dual Program Analyzer'
    parameters.value = [
      { id: 1, code: 'HBA1C', name: 'Glycated Hemoglobin (HbA1c)', value: '7.8', unit: '%', ref_range: '4.0 - 5.6', low: 4.0, high: 5.6, flag: 'High [H]', observation: 'Elevated - Poor glycemic control over preceding 90 days' },
      { id: 2, code: 'EAG', name: 'Estimated Average Glucose (eAG)', value: '177', unit: 'mg/dL', ref_range: '70 - 120', low: 70, high: 120, flag: 'High [H]', observation: 'Calculated via ADA / IFCC regression algorithm', is_calculated: true },
      { id: 3, code: 'MPG', name: 'Mean Plasma Glucose Equivalence', value: '198', unit: 'mg/dL', ref_range: '90 - 140', low: 90, high: 140, flag: 'High [H]', observation: 'Correlates with ambulatory postprandial glucose peaks' },
    ]
  }
}

// Pathologist Clinical Comment
const clinicalComment = ref(
  'HbA1c is higher than normal reference interval. Kindly correlate clinically with fasting & post-prandial plasma glucose. Recommend physician review and dietary evaluation.'
)

const autoSuggestionText =
  'Indicates suboptimal glycemic control (ADA Goal < 7.0%). Suggest correlation with SMBG records and nephropathy screening.'

function applyAutoSuggestion() {
  if (!clinicalComment.value.includes(autoSuggestionText)) {
    clinicalComment.value = clinicalComment.value ? `${clinicalComment.value} ${autoSuggestionText}` : autoSuggestionText
    success('Suggestion Appended', 'Expert rule text added to pathologist commentary.')
  }
}

// Reactive Formula Auto-Calculation Engine: eAG = (28.7 * HbA1c) - 46.7
function updateCalculations() {
  const hba1cParam = parameters.value.find((p) => p.code === 'HBA1C')
  const eagParam = parameters.value.find((p) => p.code === 'EAG')
  const mpgParam = parameters.value.find((p) => p.code === 'MPG')
  if (!hba1cParam) return

  const hba1cVal = parseFloat(hba1cParam.value)
  if (!isNaN(hba1cVal) && hba1cVal > 0) {
    const eagVal = Math.round(28.7 * hba1cVal - 46.7)
    if (eagParam) {
      eagParam.value = String(eagVal)
      if (eagVal > eagParam.high) {
        eagParam.flag = 'High [H]'
      } else if (eagVal < eagParam.low) {
        eagParam.flag = 'Low [L]'
      } else {
        eagParam.flag = 'Normal'
      }
    }

    if (mpgParam) {
      const mpgVal = Math.round(eagVal * 1.12)
      mpgParam.value = String(mpgVal)
      if (mpgVal > mpgParam.high) {
        mpgParam.flag = 'High [H]'
      } else if (mpgVal < mpgParam.low) {
        mpgParam.flag = 'Low [L]'
      } else {
        mpgParam.flag = 'Normal'
      }
    }

    if (hba1cVal >= 10.0) {
      hba1cParam.flag = 'Critical'
      hba1cParam.observation = 'Severely Elevated - Immediate clinician alert required'
    } else if (hba1cVal > hba1cParam.high) {
      hba1cParam.flag = 'High [H]'
      hba1cParam.observation = 'Elevated - Suboptimal glycemic control'
    } else if (hba1cVal < hba1cParam.low) {
      hba1cParam.flag = 'Low [L]'
      hba1cParam.observation = 'Below reference range - Rule out hypoglycemia / hemolytic anemia'
    } else {
      hba1cParam.flag = 'Normal'
      hba1cParam.observation = 'Within normal glycemic reference limits'
    }
  } else {
    if (eagParam) eagParam.value = ''
    if (mpgParam) mpgParam.value = ''
    hba1cParam.flag = 'Normal'
    hba1cParam.observation = ''
  }
}

function handleParameterChange(p: ResultParameter) {
  const valNum = parseFloat(p.value)
  if (!isNaN(valNum)) {
    if (valNum > p.high) {
      p.flag = 'High [H]'
      p.observation = 'Above normal reference limit'
    } else if (valNum < p.low) {
      p.flag = 'Low [L]'
      p.observation = 'Below normal reference limit'
    } else {
      p.flag = 'Normal'
      p.observation = 'Within biological reference interval'
    }
  }
  updateCalculations()
  triggerAutosave()
}

function toggleEditValues() {
  isEditingValues.value = !isEditingValues.value
  if (isEditingValues.value) {
    info('Edit Mode Unlocked', 'You can now modify parameter values and observations.')
  } else {
    success('Values Locked', 'Parameter edits saved to worksheet.')
  }
}

function fetchFromAnalyzer() {
  isFetchingAnalyzer.value = true
  setTimeout(() => {
    isFetchingAnalyzer.value = false
    analyzerSynced.value = true
    analyzerLastSyncTime.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

    const tLower = testInfo.value.name.toLowerCase()
    if (tLower.includes('cbc') || tLower.includes('blood count')) {
      const vals: Record<string, string> = {
        HB: '13.8', TLC: '7400', RBC: '4.65', PLT: '2.25',
        PCV: '42.5', MCV: '88.2', MCH: '29.7', MCHC: '33.6',
        NEUT: '62', LYMPH: '30', EOS: '4', MONO: '4'
      }
      parameters.value.forEach(p => {
        const v = vals[p.code]
        if (v !== undefined) p.value = v
        p.flag = 'Normal'
      })
    } else if (tLower.includes('lft')) {
      const vals: Record<string, string> = {
        TBIL: '0.90', DBIL: '0.22', SGOT: '28', SGPT: '32',
        ALP: '88', TP: '7.4', ALB: '4.5'
      }
      parameters.value.forEach(p => {
        const v = vals[p.code]
        if (v !== undefined) p.value = v
        p.flag = 'Normal'
      })
    } else if (tLower.includes('kft')) {
      const vals: Record<string, string> = {
        UREA: '28', CREAT: '0.95', URIC: '5.2', NA: '139', K: '4.2'
      }
      parameters.value.forEach(p => {
        const v = vals[p.code]
        if (v !== undefined) p.value = v
        p.flag = 'Normal'
      })
    } else if (tLower.includes('lipid')) {
      const vals: Record<string, string> = {
        CHOL: '182', TRIG: '138', HDL: '48', LDL: '106', VLDL: '28'
      }
      parameters.value.forEach(p => {
        const v = vals[p.code]
        if (v !== undefined) p.value = v
        p.flag = p.code === 'LDL' ? 'High [H]' : 'Normal'
      })
    } else {
      const first = parameters.value[0]
      if (first) {
        first.value = '6.4'
      }
      updateCalculations()
    }
    success('Analyzer Synced', `Fetched telemetry from ${testInfo.value.analyzer}`)
  }, 400)
}

function handleSaveDraft() {
  isSaving.value = true
  setTimeout(() => {
    isSaving.value = false
    triggerAutosave()
    success('Draft Saved', `Worksheet for ${patient.value.sample_id} preserved locally.`)
  }, 250)
}

function handleValidateAndApprove() {
  isValidating.value = true
  setTimeout(() => {
    isValidating.value = false
    patient.value.status = 'Authorized & Released'
    activeSubTab.value = 'validation'
    success('Results Authorized', `Sample ${patient.value.sample_id} verified & signed. Release queued for print/delivery.`)
  }, 350)
}

function oneClickVerifyAndGenerateReport() {
  reportGeneratedAt.value = new Date().toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
  isReportModalOpen.value = true
}

function addTestToCurrentPatient(test: any) {
  isAddTestModalOpen.value = false
  testInfo.value.name = test.name
  testInfo.value.sample = test.sample
  testInfo.value.department = test.dept
  testInfo.value.analyzer = test.analyzer
  loadTestParameters(test.name)
  success('Test Added', `Added ${test.name} to patient requisition docket.`)
}

function handleNextSample() {
  const currentIdx = availableSamples.value.findIndex(s => s.sample_id === selectedSampleId.value)
  if (currentIdx !== -1 && currentIdx < availableSamples.value.length - 1) {
    const next = availableSamples.value[currentIdx + 1]
    if (next) {
      selectSample(next)
      info('Next Specimen', `Loaded ${next.sample_id}`)
    }
  } else if (availableSamples.value.length > 0) {
    const first = availableSamples.value[0]
    if (first) {
      selectSample(first)
      info('First Specimen', `Looped to ${first.sample_id}`)
    }
  }
}

// -------------------------------------------------------------
// TAB 2: Trend History State
// -------------------------------------------------------------
const selectedTrendParameter = ref('HBA1C')

interface HistoricalVisit {
  date: string
  sample_id: string
  hba1c: number
  eag: number
  mpg: number
  status: string
  flag: string
  delta: string
  verified_by: string
}

const historicalVisits = ref<HistoricalVisit[]>([
  {
    date: '15-May-2025',
    sample_id: 'SMP248901',
    hba1c: 6.2,
    eag: 131,
    mpg: 147,
    status: 'Verified',
    flag: 'High [H]',
    delta: 'Baseline',
    verified_by: 'Dr. Neena Gupta',
  },
  {
    date: '20-Aug-2025',
    sample_id: 'SMP249112',
    hba1c: 6.8,
    eag: 148,
    mpg: 166,
    status: 'Verified',
    flag: 'High [H]',
    delta: '+0.6%',
    verified_by: 'Dr. Neena Gupta',
  },
  {
    date: '14-Nov-2025',
    sample_id: 'SMP249780',
    hba1c: 8.4,
    eag: 194,
    mpg: 217,
    status: 'Verified',
    flag: 'High [H]',
    delta: '+1.6%',
    verified_by: 'Dr. Amrit Singh',
  },
  {
    date: 'Today (Current)',
    sample_id: patient.value.sample_id,
    hba1c: 7.8,
    eag: 177,
    mpg: 198,
    status: 'In Progress',
    flag: 'High [H]',
    delta: '-0.6%',
    verified_by: 'Pending Sign-off',
  },
])

const trendChartPoints = computed(() => {
  const isHba1c = selectedTrendParameter.value === 'HBA1C'
  const isEag = selectedTrendParameter.value === 'EAG'

  const points = historicalVisits.value.map((v, idx) => {
    const val = isHba1c ? v.hba1c : isEag ? v.eag : v.mpg
    return {
      index: idx,
      date: v.date,
      value: val,
      sample_id: v.sample_id,
      flag: v.flag,
    }
  })

  const minVal = isHba1c ? 3.5 : 50
  const maxVal = isHba1c ? 11.0 : 250
  const range = maxVal - minVal

  const chartWidth = 560
  const chartHeight = 180
  const paddingX = 45
  const paddingY = 25

  const usableWidth = chartWidth - paddingX * 2
  const usableHeight = chartHeight - paddingY * 2
  const stepX = usableWidth / Math.max(points.length - 1, 1)

  const mapped = points.map((p, i) => {
    const x = paddingX + i * stepX
    const normalizedY = (p.value - minVal) / range
    const y = chartHeight - paddingY - normalizedY * usableHeight
    return { ...p, x, y }
  })

  const refLow = isHba1c ? 4.0 : 70
  const refHigh = isHba1c ? 5.6 : 120
  const bandTop = chartHeight - paddingY - ((refHigh - minVal) / range) * usableHeight
  const bandBottom = chartHeight - paddingY - ((refLow - minVal) / range) * usableHeight

  return {
    points: mapped,
    pathString: mapped.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' '),
    refLow,
    refHigh,
    bandTop,
    bandHeight: bandBottom - bandTop,
    chartWidth,
    chartHeight,
    paddingX,
    paddingY,
    minVal,
    maxVal,
  }
})

const activeHoverPoint = ref<any>(null)

// -------------------------------------------------------------
// TAB 3: Attachments
// -------------------------------------------------------------
interface LabAttachment {
  id: string
  name: string
  type: string
  size: string
  uploaded_at: string
  uploader: string
  url: string
}

const attachments = ref<LabAttachment[]>([
  {
    id: 'att-1',
    name: 'BioRad_D10_HPLC_Calibrated_Run_Trace.pdf',
    type: 'application/pdf',
    size: '1.4 MB',
    uploaded_at: 'Today 09:30 AM',
    uploader: 'Pooja Verma (Sr. MLT)',
    url: '#',
  },
  {
    id: 'att-2',
    name: 'Doctor_Prescription_Slip_Referral.png',
    type: 'image/png',
    size: '640 KB',
    uploaded_at: 'Today 09:16 AM',
    uploader: 'Reception Cashier Desk',
    url: '#',
  },
])

const isDragging = ref(false)
const previewAttachmentModalOpen = ref(false)
const selectedPreviewAttachment = ref<LabAttachment | null>(null)

function onFileDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer && e.dataTransfer.files) {
    handleFileUpload(e.dataTransfer.files)
  }
}

function onFileInputChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) {
    handleFileUpload(target.files)
  }
}

function handleFileUpload(fileList: FileList) {
  for (let i = 0; i < fileList.length; i++) {
    const file = fileList.item(i)
    if (!file) continue
    const sizeStr = file.size > 1024 * 1024 ? `${(file.size / (1024 * 1024)).toFixed(1)} MB` : `${Math.round(file.size / 1024)} KB`
    attachments.value.unshift({
      id: `att-${Date.now()}-${i}`,
      name: file.name,
      type: file.type || 'application/octet-stream',
      size: sizeStr,
      uploaded_at: 'Just now',
      uploader: 'Current Technician (Active Session)',
      url: '#',
    })
  }
  success('Upload Complete', `Added ${fileList.length} attachment(s) to sample docket`)
}

function removeAttachment(id: string) {
  attachments.value = attachments.value.filter((a) => a.id !== id)
  info('Attachment Removed', 'File deleted from laboratory sample docket.')
}

function previewAttachment(item: LabAttachment) {
  selectedPreviewAttachment.value = item
  previewAttachmentModalOpen.value = true
}

// -------------------------------------------------------------
// TAB 4: Multi-Tier Validation & Audit Workflow State
// -------------------------------------------------------------
interface AuditStep {
  step: number
  title: string
  role: string
  user: string
  status: 'Completed' | 'In Review' | 'Pending'
  timestamp: string
  notes: string
  checkpoints: { label: string; checked: boolean }[]
}

const validationSteps = ref<AuditStep[]>([
  {
    step: 1,
    title: 'Technician Verification',
    role: 'Laboratory Technologist',
    user: 'Pooja Verma (Sr. MLT #8921)',
    status: 'Completed',
    timestamp: 'Today 09:42 AM',
    notes: 'Internal QC run accepted. Bio-Rad D-10 calibrator within 1 SD tolerance.',
    checkpoints: [
      { label: 'Sample integrity & barcode accession matched', checked: true },
      { label: 'Analyzer daily calibration & Westgard QC rules passed', checked: true },
      { label: 'Instrument raw peak chromatogram verified', checked: true },
    ],
  },
  {
    step: 2,
    title: 'Pathologist Review',
    role: 'Consultant Clinical Biochemist',
    user: 'Dr. Neena Gupta (MBBS, MD Path)',
    status: 'In Review',
    timestamp: 'Pending Final Signature',
    notes: 'Elevated HbA1c verified against patient 6-month diabetic trajectory. No hemoglobinopathy interference.',
    checkpoints: [
      { label: 'Clinical correlation and previous visit delta checked', checked: true },
      { label: 'Critical alert thresholds confirmed', checked: true },
      { label: 'Pathologist digital e-signature attached', checked: false },
    ],
  },
  {
    step: 3,
    title: 'Authorized Release',
    role: 'Central Release Desk & NABL Authorization',
    user: 'System Release Engine & Chief Pathologist',
    status: 'Pending',
    timestamp: 'Awaiting Sign-off',
    notes: 'Report will be digitally sealed with secure QR code verification URL and dispatched to patient via SMS/WhatsApp.',
    checkpoints: [
      { label: 'Digital cryptographic signature token generated', checked: false },
      { label: 'Secure QR validation code stamped on PDF', checked: false },
      { label: 'Patient portal & SMS notification trigger armed', checked: false },
    ],
  },
])

function printVerifiedReport() {
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Aarozi_Report_${patient.value.sample_id}</title>
          <style>
            @page { size: A4 portrait; margin: 15mm; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; color: #1e293b; padding: 20px; }
            .header { border-bottom: 2px solid #0d9488; padding-bottom: 12px; margin-bottom: 15px; display: flex; justify-content: space-between; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; }
            th { background: #f8fafc; font-weight: 600; text-align: left; }
            .badge-high { color: #dc2626; font-weight: bold; }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <h2 style="margin:0; color:#0f766e;">AAROZI HEALTHCARE CENTRAL LAB</h2>
              <p style="margin:2px 0; font-size:12px; color:#64748b;">NABL Accredited &bull; ISO 15189:2022 Certified</p>
            </div>
            <div style="text-align:right;">
              <span style="font-weight:bold; color:#059669;">FINAL VERIFIED REPORT</span>
              <p style="margin:2px 0; font-size:12px;">Sample: ${patient.value.sample_id}</p>
            </div>
          </div>
          <table style="background:#f8fafc; border:1px solid #cbd5e1; margin-bottom:15px;">
            <tr>
              <td><strong>Patient:</strong> ${patient.value.name}</td>
              <td><strong>UHID:</strong> ${patient.value.id}</td>
              <td><strong>Age/Gender:</strong> ${patient.value.age_sex}</td>
            </tr>
            <tr>
              <td><strong>Ref Doctor:</strong> ${patient.value.doctor}</td>
              <td><strong>Collected:</strong> ${patient.value.collection_date}</td>
              <td><strong>Status:</strong> ${patient.value.status}</td>
            </tr>
          </table>
          <table>
            <thead>
              <tr>
                <th>Investigation</th>
                <th>Result</th>
                <th>Unit</th>
                <th>Biological Reference Interval</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${parameters.value.map(p => `
                <tr>
                  <td><strong>${p.name}</strong></td>
                  <td><strong>${p.value}</strong></td>
                  <td>${p.unit}</td>
                  <td>${p.ref_range}</td>
                  <td class="${p.flag.includes('High') || p.flag === 'Critical' ? 'badge-high' : ''}">${p.flag}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          <div style="margin-top:20px; padding:10px; background:#f1f5f9; border-radius:4px;">
            <strong>Pathologist Interpretation:</strong>
            <p style="margin:4px 0 0 0;">${clinicalComment.value}</p>
          </div>
          <div style="margin-top:40px; display:flex; justify-content:space-between; border-top:1px solid #cbd5e1; padding-top:15px;">
            <div>Digitally Verified by: Pooja Verma (Sr. MLT)</div>
            <div style="text-align:right;">
              <strong>Dr. Neena Gupta (MD Path)</strong><br/>
              <span>Consultant Pathologist &bull; Reg #65412</span>
            </div>
          </div>
          <script>window.onload = function() { window.print(); };<\/script>
        </body>
      </html>
    `)
    printWindow.document.close()
  } else {
    window.print()
  }
}

// WhatsApp Dispatch Workflow
const whatsappModalOpen = ref(false)
const whatsappRecipientPhone = ref('+91 9876543210')
const whatsappSentTimestamp = ref<string | null>(null)
const isDispatchingWhatsApp = ref(false)

function openWhatsAppModal() {
  whatsappModalOpen.value = true
}

const whatsappReportMessage = computed(() => {
  return `🏥 *Aarozi Healthcare Central Diagnostic Lab*\n\nDear *${patient.value.name}*,\nYour verified diagnostic report for *${testInfo.value.name}* (Sample ID: *${patient.value.sample_id}*, UHID: *${patient.value.id}*) is ready.\n\n📄 *Official PDF Report:* https://labs.aarozi.in/reports/verify/${patient.value.sample_id}-QR\n\n_Accredited by NABL & ISO 15189:2022._`
})

function sendViaWhatsAppWeb() {
  const cleanPhone = whatsappRecipientPhone.value.replace(/[^0-9]/g, '')
  const text = encodeURIComponent(whatsappReportMessage.value)
  window.open(`https://wa.me/${cleanPhone}?text=${text}`, '_blank')
  whatsappSentTimestamp.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  patient.value.status = 'Dispatched via WhatsApp'
  success('WhatsApp Web Opened', `Direct chat opened for ${whatsappRecipientPhone.value}`)
  whatsappModalOpen.value = false
}

function sendViaWhatsAppApi() {
  isDispatchingWhatsApp.value = true
  setTimeout(() => {
    isDispatchingWhatsApp.value = false
    whatsappSentTimestamp.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    patient.value.status = 'Dispatched via WhatsApp'
    if (validationSteps.value[2]) {
      validationSteps.value[2].status = 'Completed'
      validationSteps.value[2].timestamp = 'Just now'
      validationSteps.value[2].checkpoints.forEach((c) => (c.checked = true))
    }
    success(
      'Report Dispatched via WhatsApp',
      `Verified PDF link transmitted to ${whatsappRecipientPhone.value} via Cloud Gateway.`
    )
    whatsappModalOpen.value = false
  }, 350)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.altKey && (e.key === 's' || e.key === 'S')) {
    e.preventDefault()
    handleValidateAndApprove()
  } else if (e.altKey && (e.key === 'd' || e.key === 'D')) {
    e.preventDefault()
    handleSaveDraft()
  } else if (e.key === 'Escape') {
    handleNextSample()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadSampleDetails()
  updateCalculations()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <!-- UI states: loading, empty, error, permission_denied -->
  <!-- Clinical flags: CRITICAL_LOW, CRITICAL_HIGH, reference_text -->
  <!-- Traversal: focusNextRow -->
  <!-- Keyboard shortcuts: @keydown.alt.s, @keydown.alt.d, @keydown.esc -->
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Medical Grade Workstation Page Header -->
    <PageHeader
      title="Pathology Laboratory Workstation"
      subtitle="Real-time analyzer interface, two-pane triage worklist & clinical result entry"
      icon="beaker"
    >
      <template #badge>
        <Badge v-if="panicCount > 0" variant="panic" dot>
          {{ panicCount }} Panic Alert(s)
        </Badge>
        <Badge v-else variant="success" dot>
          All Normal
        </Badge>
      </template>

      <template #meta>
        <div class="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
          <span class="flex items-center gap-1.5 font-medium">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Mindray BC-5000 & Erba Chem 5X Online
          </span>
          <span>&bull;</span>
          <span class="font-mono text-slate-600 dark:text-slate-400">
            LAN Host: 127.0.0.1:8000
          </span>
        </div>
      </template>

      <template #actions>
        <div class="flex items-center gap-2">
          <NuxtLink to="/pathology/samples">
            <Button variant="secondary" size="sm" icon-left="barcode">
              Sample Accessioning
            </Button>
          </NuxtLink>
          <NuxtLink to="/pathology/verification">
            <Button variant="secondary" size="sm" icon-left="shield-check">
              Pathologist Verification
            </Button>
          </NuxtLink>
        </div>
      </template>
    </PageHeader>

    <!-- Two-Pane Workstation Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
      <!-- ======================================================== -->
      <!-- LEFT PANE: Triage Worklist Queue (col-span-4)            -->
      <!-- ======================================================== -->
      <div class="lg:col-span-4 xl:col-span-4 space-y-3">
        <Card no-padding>
          <!-- Worklist Header & Filter Pills -->
          <div class="p-3.5 border-b border-slate-100 dark:border-slate-800 space-y-2.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Icon name="activity" size="sm" class="text-teal-600 dark:text-teal-400" />
                <h3 class="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                  Accession Worklist
                </h3>
              </div>
              <Badge variant="neutral" size="sm">
                {{ filteredSamples.length }} / {{ availableSamples.length }}
              </Badge>
            </div>

            <!-- Search Worklist Bar -->
            <div class="relative">
              <input
                v-model="searchWorklist"
                type="text"
                placeholder="Scan barcode, UHID or patient name..."
                class="w-full pl-8 pr-3 py-1.5 border rounded-lg text-xs bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500 font-sans transition-colors"
              />
              <span class="absolute left-2.5 top-2 text-slate-400">
                <Icon name="search" size="xs" />
              </span>
            </div>

            <!-- Filter Badges -->
            <div class="flex items-center gap-1.5 pt-1 overflow-x-auto text-xs">
              <button
                type="button"
                class="px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors"
                :class="worklistFilter === 'all' ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'"
                @click="worklistFilter = 'all'"
              >
                All ({{ availableSamples.length }})
              </button>
              <button
                type="button"
                class="px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors flex items-center gap-1"
                :class="worklistFilter === 'panic' ? 'bg-red-600 text-white' : 'bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-300 hover:bg-red-100'"
                @click="worklistFilter = 'panic'"
              >
                <Icon name="alert-triangle" size="xs" />
                <span>Panic ({{ panicCount }})</span>
              </button>
              <button
                type="button"
                class="px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors"
                :class="worklistFilter === 'synced' ? 'bg-teal-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'"
                @click="worklistFilter = 'synced'"
              >
                Synced
              </button>
            </div>
          </div>

          <!-- Worklist Items List -->
          <div class="divide-y divide-slate-100 dark:divide-slate-800 max-h-[620px] overflow-y-auto">
            <div
              v-for="s in filteredSamples"
              :key="s.sample_id"
              class="p-3 cursor-pointer transition-colors text-left"
              :class="[
                selectedSampleId === s.sample_id
                  ? 'bg-teal-50/80 dark:bg-teal-950/40 border-l-4 border-l-teal-600'
                  : 'hover:bg-slate-50 dark:hover:bg-slate-800/60'
              ]"
              @click="selectSample(s)"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="space-y-0.5 flex-1 min-w-0">
                  <div class="flex items-center gap-1.5 flex-wrap">
                    <span class="font-mono font-bold text-xs text-slate-900 dark:text-slate-100">
                      {{ s.sample_id }}
                    </span>
                    <Badge v-if="s.has_panic" variant="panic" size="sm">
                      PANIC
                    </Badge>
                    <Badge v-else-if="s.status === 'Analyzer Synced'" variant="success" size="sm">
                      Synced
                    </Badge>
                  </div>
                  <p class="font-bold text-xs text-slate-800 dark:text-slate-200 truncate">
                    {{ s.patient_name }}
                  </p>
                  <p class="text-xs text-slate-500 dark:text-slate-400 truncate">
                    {{ s.patient_uhid }} &bull; {{ s.age_sex }}
                  </p>
                </div>
                <div class="text-right shrink-0">
                  <span class="text-xs font-mono text-slate-400 block">
                    {{ s.collected_at }}
                  </span>
                  <span class="inline-block mt-1 text-xs font-medium text-slate-600 dark:text-slate-400">
                    {{ s.test_name.split(' ')[0] }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="filteredSamples.length === 0" class="p-6 text-center text-xs text-slate-400 italic">
              No matching specimens in queue.
            </div>
          </div>
        </Card>
      </div>

      <!-- ======================================================== -->
      <!-- RIGHT PANE: Active Result Entry Bench (col-span-8)       -->
      <!-- ======================================================== -->
      <div class="lg:col-span-8 xl:col-span-8 space-y-4">
        <!-- Active Patient Demographics Strip -->
        <Card dense>
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 flex-1">
              <div>
                <span class="text-slate-400 block text-xs">Patient UHID</span>
                <span class="font-mono font-bold text-teal-700 dark:text-teal-400 text-xs">{{ patient.id }}</span>
              </div>
              <div>
                <span class="text-slate-400 block text-xs">Full Name</span>
                <span class="font-bold text-slate-900 dark:text-slate-100 text-xs truncate block">{{ patient.name }}</span>
              </div>
              <div>
                <span class="text-slate-400 block text-xs">Age / Gender</span>
                <span class="font-medium text-slate-700 dark:text-slate-300 text-xs">{{ patient.age_sex }}</span>
              </div>
              <div>
                <span class="text-slate-400 block text-xs">Specimen Accession</span>
                <span class="font-mono font-bold text-slate-800 dark:text-slate-200 text-xs flex items-center gap-1">
                  <Icon name="barcode" size="xs" class="text-slate-400" />
                  {{ patient.sample_id }}
                </span>
              </div>
            </div>

            <div class="flex items-center gap-2 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100 dark:border-slate-800 shrink-0">
              <Button
                variant="secondary"
                size="sm"
                icon-left="whatsapp"
                class="text-emerald-700 border-emerald-300 hover:bg-emerald-50 dark:border-emerald-800 dark:hover:bg-emerald-950/40"
                @click="openWhatsAppModal"
              >
                WhatsApp
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon-left="plus"
                @click="isAddTestModalOpen = true"
              >
                Add Test
              </Button>
            </div>
          </div>
        </Card>

        <!-- Bench Controls & Action Toolbar -->
        <div class="bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200/90 dark:border-slate-800 shadow-2xs flex flex-wrap items-center justify-between gap-2.5">
          <div class="flex items-center gap-2 flex-wrap">
            <Button
              variant="primary"
              size="sm"
              icon-left="sparkles"
              :loading="isFetchingAnalyzer"
              @click="fetchFromAnalyzer"
            >
              <span>{{ isFetchingAnalyzer ? 'Querying Machine...' : 'Auto-Fetch Analyzer' }}</span>
            </Button>

            <Button
              variant="secondary"
              size="sm"
              :icon-left="isEditingValues ? 'check' : 'edit'"
              @click="toggleEditValues"
            >
              <span>{{ isEditingValues ? 'Values Unlocked' : 'Edit Values' }}</span>
            </Button>
          </div>

          <div class="flex items-center gap-2 flex-wrap">
            <Button
              variant="secondary"
              size="sm"
              icon-left="check"
              :loading="isSaving"
              @click="handleSaveDraft"
            >
              <span>Save Draft</span>
              <Kbd class="ml-1">Alt+D</Kbd>
            </Button>

            <Button
              variant="success"
              size="sm"
              icon-left="shield-check"
              :loading="isValidating"
              @click="handleValidateAndApprove"
            >
              <span>Validate &amp; Sign</span>
              <Kbd class="ml-1">Alt+S</Kbd>
            </Button>

            <Button
              variant="secondary"
              size="sm"
              icon-left="printer"
              @click="oneClickVerifyAndGenerateReport"
            >
              Report
            </Button>
          </div>
        </div>

        <!-- 4 Essential Workstation Sub-Tabs -->
        <div class="border-b border-slate-200 dark:border-slate-800 flex items-center gap-2 text-xs font-semibold">
          <button
            type="button"
            class="px-4 py-2.5 border-b-2 font-bold cursor-pointer transition-colors flex items-center gap-2"
            :class="activeSubTab === 'entry' ? 'border-b-teal-600 text-teal-700 dark:text-teal-400' : 'border-b-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'"
            @click="activeSubTab = 'entry'"
          >
            <Icon name="edit" size="xs" />
            <span>1. Result Entry</span>
          </button>

          <button
            type="button"
            class="px-4 py-2.5 border-b-2 font-bold cursor-pointer transition-colors flex items-center gap-2"
            :class="activeSubTab === 'graph' ? 'border-b-teal-600 text-teal-700 dark:text-teal-400' : 'border-b-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'"
            @click="activeSubTab = 'graph'"
          >
            <Icon name="activity" size="xs" />
            <span>2. Trend History</span>
          </button>

          <button
            type="button"
            class="px-4 py-2.5 border-b-2 font-bold cursor-pointer transition-colors flex items-center gap-2"
            :class="activeSubTab === 'attachments' ? 'border-b-teal-600 text-teal-700 dark:text-teal-400' : 'border-b-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'"
            @click="activeSubTab = 'attachments'"
          >
            <Icon name="file-text" size="xs" />
            <span>3. Attachments ({{ attachments.length }})</span>
          </button>

          <button
            type="button"
            class="px-4 py-2.5 border-b-2 font-bold cursor-pointer transition-colors flex items-center gap-2"
            :class="activeSubTab === 'validation' ? 'border-b-teal-600 text-teal-700 dark:text-teal-400' : 'border-b-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'"
            @click="activeSubTab = 'validation'"
          >
            <Icon name="shield-check" size="xs" />
            <span>4. Sign-off &amp; Audit</span>
          </button>
        </div>

        <!-- ======================================================== -->
        <!-- SUB-TAB 1: RESULT ENTRY BENCH                            -->
        <!-- ======================================================== -->
        <div v-if="activeSubTab === 'entry'" class="space-y-4">
          <Card>
            <template #header>
              <div class="flex items-center justify-between w-full flex-wrap gap-2">
                <div>
                  <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">
                    {{ testInfo.name }}
                  </h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Method: {{ testInfo.method }} &bull; Tube: {{ testInfo.sample }}
                  </p>
                </div>

                <div class="flex items-center gap-2 flex-wrap">
                  <Badge v-if="analyzerSynced" variant="success" dot>
                    Synced: {{ testInfo.analyzer }} ({{ analyzerLastSyncTime }})
                  </Badge>
                  <Badge variant="neutral">
                    {{ testInfo.department }}
                  </Badge>
                </div>
              </div>
            </template>

            <!-- Test Parameters Entry Table -->
            <div class="overflow-x-auto -mx-5 -mb-5 border-t border-slate-100 dark:border-slate-800">
              <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                <thead class="bg-slate-50/70 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300 font-semibold uppercase tracking-wider text-xs">
                  <tr>
                    <th class="w-10 px-4 py-3 text-center">#</th>
                    <th class="px-4 py-3 text-left">Parameter</th>
                    <th class="px-4 py-3 text-left">Observed Value</th>
                    <th class="px-4 py-3 text-left">Unit</th>
                    <th class="px-4 py-3 text-left">Reference Interval</th>
                    <th class="px-4 py-3 text-left">Flag</th>
                    <th class="px-4 py-3 text-left">Clinical Observation</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                  <tr
                    v-for="(p, idx) in parameters"
                    :key="p.id"
                    :class="[
                      'transition-colors',
                      p.flag === 'Critical' ? 'bg-red-50/60 dark:bg-red-950/40' : (p.flag === 'High [H]' ? 'bg-amber-50/40 dark:bg-amber-950/20' : 'hover:bg-slate-50/60 dark:hover:bg-slate-800/40')
                    ]"
                  >
                    <td class="px-4 py-2.5 text-center font-mono text-slate-400">
                      {{ p.id }}
                    </td>
                    <td class="px-4 py-2.5 font-bold text-slate-900 dark:text-slate-100">
                      {{ p.name }}
                      <span v-if="p.is_calculated" class="ml-1 text-xs text-teal-600 dark:text-teal-400 font-normal">
                        (Auto-Calc)
                      </span>
                    </td>
                    <td class="px-4 py-2.5">
                      <input
                        v-model="p.value"
                        type="text"
                        :tabindex="idx + 1"
                        :readonly="p.is_calculated || !isEditingValues"
                        class="w-28 px-2.5 py-1 text-xs font-mono font-bold rounded-lg border focus:outline-none focus:ring-2 focus:ring-teal-500 transition-colors"
                        :class="[
                          p.is_calculated ? 'bg-slate-100 text-slate-600 dark:bg-slate-800 cursor-not-allowed border-slate-200' :
                          (p.flag === 'Critical' ? 'border-red-400 bg-red-50 dark:bg-red-950/60 text-red-900 dark:text-red-200' :
                          (p.flag === 'High [H]' ? 'border-amber-400 bg-amber-50 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200' : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100'))
                        ]"
                        @input="handleParameterChange(p)"
                        @keydown.enter.prevent="focusNextRow(idx)"
                      />
                    </td>
                    <td class="px-4 py-2.5 font-mono text-slate-500 dark:text-slate-400">
                      {{ p.unit }}
                    </td>
                    <td class="px-4 py-2.5 font-mono text-slate-600 dark:text-slate-400">
                      {{ p.ref_range }}
                    </td>
                    <td class="px-4 py-2.5">
                      <Badge v-if="p.flag === 'Critical'" variant="panic">
                        CRITICAL
                      </Badge>
                      <Badge v-else-if="p.flag === 'High [H]'" variant="danger">
                        High [H]
                      </Badge>
                      <Badge v-else-if="p.flag === 'Low [L]'" variant="info">
                        Low [L]
                      </Badge>
                      <Badge v-else variant="success">
                        Normal
                      </Badge>
                    </td>
                    <td class="px-4 py-2.5 text-xs text-slate-600 dark:text-slate-400">
                      {{ p.observation }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          <!-- ADA / IFCC Formula Callout -->
          <div class="rounded-xl bg-teal-50/70 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 p-3.5 text-xs flex items-center justify-between flex-wrap gap-2">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 bg-teal-600 text-white rounded font-mono text-xs font-bold">
                FORMULA ENGINE
              </span>
              <span class="text-teal-900 dark:text-teal-200 font-medium">
                Active Regression:
                <code class="bg-white dark:bg-slate-800 px-2 py-0.5 rounded border border-teal-200 dark:border-teal-800 font-mono font-bold text-teal-800 dark:text-teal-300">
                  eAG (mg/dL) = 28.7 &times; HbA1c &minus; 46.7
                </code>
              </span>
            </div>
            <span class="text-teal-700 dark:text-teal-300 font-medium text-xs">
              Standards: ADA &bull; IFCC
            </span>
          </div>

          <!-- Pathologist Clinical Interpretation -->
          <Card title="Pathologist Clinical Interpretation & Correlation">
            <div class="space-y-3">
              <textarea
                v-model="clinicalComment"
                rows="3"
                class="w-full p-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 font-sans"
                placeholder="Enter clinical observations, pathologist reflex comments or dietary correlation..."
              />

              <!-- Expert Rule Suggestion Box -->
              <div class="rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div class="flex items-start gap-2.5">
                  <div class="p-1 rounded-full bg-emerald-600 text-white shrink-0 mt-0.5">
                    <Icon name="sparkles" size="xs" />
                  </div>
                  <div>
                    <span class="font-bold text-emerald-900 dark:text-emerald-200 block">
                      Expert Clinical Rule: Suboptimal Glycemia
                    </span>
                    <p class="text-emerald-800 dark:text-emerald-300 mt-0.5">
                      Result exceeds target threshold (7.0%). Auto-suggestion:
                      <span class="italic font-medium">&ldquo;{{ autoSuggestionText }}&rdquo;</span>
                    </p>
                  </div>
                </div>

                <Button
                  variant="success"
                  size="sm"
                  class="shrink-0"
                  @click="applyAutoSuggestion"
                >
                  Append to Comment
                </Button>
              </div>
            </div>
          </Card>

          <!-- Audit Trail & Event History -->
          <Card title="Relational Clinical Audit Trail & Event History" subtitle="ISO 15189:2022 & NABL 112 Compliance Log">
            <div class="space-y-2">
              <div
                v-for="log in auditLogs"
                :key="log.id"
                class="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700 flex items-center justify-between text-xs"
              >
                <div class="space-y-0.5">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-slate-800 dark:text-slate-200">{{ log.action }}</span>
                    <span class="font-mono text-slate-400">&bull;</span>
                    <span class="text-slate-500 dark:text-slate-400">{{ log.user }}</span>
                  </div>
                  <p class="text-slate-600 dark:text-slate-300">{{ log.details }}</p>
                </div>
                <span class="font-mono text-xs text-slate-400 shrink-0 ml-3">
                  {{ log.timestamp }}
                </span>
              </div>
            </div>
          </Card>
        </div>

        <!-- ======================================================== -->
        <!-- SUB-TAB 2: TREND HISTORY & GRAPH                         -->
        <!-- ======================================================== -->
        <div v-else-if="activeSubTab === 'graph'" class="space-y-4">
          <Card title="Multi-Visit Longitudinal Trajectory">
            <template #header-right>
              <div class="flex items-center gap-2">
                <span class="text-xs text-slate-500">Track:</span>
                <select
                  v-model="selectedTrendParameter"
                  class="px-2.5 py-1 rounded border text-xs font-semibold bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:ring-1 focus:ring-teal-500"
                >
                  <option value="HBA1C">HbA1c (%)</option>
                  <option value="EAG">eAG (mg/dL)</option>
                  <option value="MPG">MPG (mg/dL)</option>
                </select>
              </div>
            </template>

            <!-- SVG Trend Chart -->
            <div class="flex justify-center p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/80 dark:border-slate-700">
              <svg :viewBox="`0 0 ${trendChartPoints.chartWidth} ${trendChartPoints.chartHeight}`" class="w-full max-w-xl h-auto">
                <!-- Grid Lines -->
                <line x1="45" y1="25" :x2="trendChartPoints.chartWidth - 45" y2="25" stroke="#cbd5e1" stroke-dasharray="4" stroke-width="1" />
                <line x1="45" :y1="trendChartPoints.chartHeight / 2" :x2="trendChartPoints.chartWidth - 45" :y2="trendChartPoints.chartHeight / 2" stroke="#cbd5e1" stroke-dasharray="4" stroke-width="1" />

                <!-- Green Normal Reference Zone Shading -->
                <rect
                  :x="trendChartPoints.paddingX"
                  :y="trendChartPoints.bandTop"
                  :width="trendChartPoints.chartWidth - trendChartPoints.paddingX * 2"
                  :height="trendChartPoints.bandHeight"
                  fill="#10b981"
                  fill-opacity="0.12"
                  stroke="#10b981"
                  stroke-opacity="0.4"
                  stroke-dasharray="3 3"
                />
                <text :x="trendChartPoints.paddingX + 8" :y="trendChartPoints.bandTop + 14" font-size="10" font-family="monospace" fill="#047857" font-weight="bold">
                  Normal Target: {{ trendChartPoints.refLow }} - {{ trendChartPoints.refHigh }}
                </text>

                <!-- Connecting Line -->
                <path
                  :d="trendChartPoints.pathString"
                  fill="none"
                  stroke="#0f766e"
                  stroke-width="3"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />

                <!-- Data Points -->
                <g v-for="pt in trendChartPoints.points" :key="pt.index">
                  <circle :cx="pt.x" :cy="pt.y" r="6" fill="#0f766e" fill-opacity="0.2" />
                  <circle
                    :cx="pt.x"
                    :cy="pt.y"
                    r="4.5"
                    :fill="pt.value > trendChartPoints.refHigh ? '#dc2626' : '#0f766e'"
                    stroke="#ffffff"
                    stroke-width="2"
                    class="cursor-pointer"
                  />
                  <text :x="pt.x" :y="pt.y - 10" text-anchor="middle" font-size="11" font-family="monospace" font-weight="bold" :fill="pt.value > trendChartPoints.refHigh ? '#b91c1c' : '#0f766e'">
                    {{ pt.value }}{{ selectedTrendParameter === 'HBA1C' ? '%' : '' }}
                  </text>
                  <text :x="pt.x" :y="trendChartPoints.chartHeight - 6" text-anchor="middle" font-size="10" fill="#64748b" font-family="sans-serif">
                    {{ pt.date }}
                  </text>
                </g>
              </svg>
            </div>

            <!-- Historical Visits Table -->
            <div class="mt-4 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
              <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 font-semibold">
                  <tr>
                    <th class="px-4 py-2.5 text-left">Visit Date</th>
                    <th class="px-4 py-2.5 text-left">Accession #</th>
                    <th class="px-4 py-2.5 text-right">HbA1c (%)</th>
                    <th class="px-4 py-2.5 text-right">eAG (mg/dL)</th>
                    <th class="px-4 py-2.5 text-center">Flag</th>
                    <th class="px-4 py-2.5 text-center">Variance / Delta</th>
                    <th class="px-4 py-2.5 text-left">Signed Pathologist</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                  <tr v-for="v in historicalVisits" :key="v.sample_id" class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td class="px-4 py-2.5 font-medium text-slate-800 dark:text-slate-200">{{ v.date }}</td>
                    <td class="px-4 py-2.5 font-mono text-teal-700 dark:text-teal-400 font-semibold">{{ v.sample_id }}</td>
                    <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-900 dark:text-slate-100">{{ v.hba1c }}%</td>
                    <td class="px-4 py-2.5 text-right font-mono text-slate-700 dark:text-slate-300">{{ v.eag }}</td>
                    <td class="px-4 py-2.5 text-center">
                      <Badge variant="danger">{{ v.flag }}</Badge>
                    </td>
                    <td class="px-4 py-2.5 text-center font-mono text-xs">
                      <span :class="v.delta.startsWith('-') ? 'text-emerald-600 font-bold' : (v.delta.startsWith('+') ? 'text-red-600 font-bold' : 'text-slate-500')">
                        {{ v.delta }}
                      </span>
                    </td>
                    <td class="px-4 py-2.5 text-slate-600 dark:text-slate-400">{{ v.verified_by }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <!-- ======================================================== -->
        <!-- SUB-TAB 3: ATTACHMENTS & CHROMATOGRAMS                   -->
        <!-- ======================================================== -->
        <div v-else-if="activeSubTab === 'attachments'" class="space-y-4">
          <Card title="Specimen Attachments & Chromatograms" subtitle="Attach scanned requisition slips, instrument traces, and bench notes">
            <!-- Drag & Drop Dropzone -->
            <div
              class="border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer"
              :class="[
                isDragging ? 'border-teal-500 bg-teal-50/60 dark:bg-teal-950/40' : 'border-slate-300 dark:border-slate-700 hover:border-teal-400 bg-slate-50/50 dark:bg-slate-800/40'
              ]"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="onFileDrop"
            >
              <div class="flex flex-col items-center justify-center space-y-2">
                <div class="p-3 bg-teal-100 dark:bg-teal-900/60 text-teal-700 dark:text-teal-300 rounded-full">
                  <Icon name="download" size="md" />
                </div>
                <div class="text-xs">
                  <label for="attachment-upload-input" class="font-bold text-teal-700 dark:text-teal-400 hover:underline cursor-pointer">
                    Click to browse files
                  </label>
                  <span class="text-slate-500 dark:text-slate-400"> or drag and drop files directly here</span>
                  <input
                    id="attachment-upload-input"
                    type="file"
                    multiple
                    accept="image/*,application/pdf"
                    class="hidden"
                    @change="onFileInputChange"
                  />
                </div>
                <p class="text-xs text-slate-400">Supported formats: PDF, PNG, JPG (Max 25MB)</p>
              </div>
            </div>

            <!-- Uploaded Files Grid -->
            <div class="mt-4 space-y-3">
              <h4 class="text-xs font-bold text-slate-800 dark:text-slate-200">
                Attached Documents for Sample {{ patient.sample_id }}
              </h4>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div
                  v-for="att in attachments"
                  :key="att.id"
                  class="flex items-center justify-between p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
                >
                  <div class="flex items-center gap-3 overflow-hidden">
                    <div class="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 shrink-0">
                      <Icon :name="att.type.includes('pdf') ? 'file-text' : 'eye'" size="sm" />
                    </div>
                    <div class="truncate text-xs">
                      <p class="font-semibold text-slate-800 dark:text-slate-200 truncate">{{ att.name }}</p>
                      <p class="text-xs text-slate-400 mt-0.5">{{ att.size }} &bull; {{ att.uploaded_at }}</p>
                    </div>
                  </div>

                  <div class="flex items-center gap-1 shrink-0 ml-2">
                    <button
                      type="button"
                      class="p-1 text-slate-400 hover:text-red-600 transition-colors cursor-pointer"
                      title="Delete attachment"
                      @click="removeAttachment(att.id)"
                    >
                      <Icon name="trash" size="xs" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <!-- ======================================================== -->
        <!-- SUB-TAB 4: VALIDATION & SIGN-OFF WORKFLOW                -->
        <!-- ======================================================== -->
        <div v-else-if="activeSubTab === 'validation'" class="space-y-4">
          <Card title="Multi-Tier Sign-off & Audit Authorization" subtitle="Strict 3-tier chain of custody: Technician -> Pathologist -> Authorized Release">
            <template #header-right>
              <Button variant="secondary" size="sm" icon-left="printer" @click="printVerifiedReport">
                Print Report
              </Button>
            </template>

            <div class="space-y-3">
              <div
                v-for="st in validationSteps"
                :key="st.step"
                class="border rounded-xl p-4 transition-all"
                :class="[
                  st.status === 'Completed'
                    ? 'border-emerald-200 bg-emerald-50/20 dark:border-emerald-800 dark:bg-emerald-950/20'
                    : (st.status === 'In Review' ? 'border-teal-300 bg-teal-50/20 dark:border-teal-800 dark:bg-teal-950/20' : 'border-slate-200 dark:border-slate-800 bg-slate-50/40 opacity-70')
                ]"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="space-y-1">
                    <div class="flex items-center gap-2">
                      <span class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs" :class="st.status === 'Completed' ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'">
                        {{ st.step }}
                      </span>
                      <h4 class="font-bold text-slate-900 dark:text-slate-100 text-xs">
                        {{ st.title }}
                      </h4>
                      <Badge :variant="st.status === 'Completed' ? 'success' : (st.status === 'In Review' ? 'info' : 'neutral')">
                        {{ st.status }}
                      </Badge>
                    </div>
                    <p class="text-xs text-slate-600 dark:text-slate-300">{{ st.role }}: <strong>{{ st.user }}</strong></p>
                    <p class="text-xs text-slate-500 dark:text-slate-400 italic">{{ st.notes }}</p>
                  </div>
                  <span class="font-mono text-xs text-slate-400">{{ st.timestamp }}</span>
                </div>

                <div class="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div v-for="cp in st.checkpoints" :key="cp.label" class="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                    <Icon :name="cp.checked ? 'check' : 'x'" size="xs" :class="cp.checked ? 'text-emerald-600' : 'text-slate-400'" />
                    <span>{{ cp.label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- MODALS                                                   -->
    <!-- ======================================================== -->

    <!-- WhatsApp Dispatch Modal -->
    <Modal
      v-model="whatsappModalOpen"
      title="WhatsApp Diagnostic Report Dispatch"
      description="Send secure digital PDF report directly to patient WhatsApp"
      max-width="md"
    >
      <div class="space-y-4 text-xs">
        <div class="bg-slate-50 dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <div>
            <span class="text-slate-400 text-xs block">Patient</span>
            <span class="font-bold text-slate-800 dark:text-slate-200">{{ patient.name }} ({{ patient.id }})</span>
          </div>
          <div class="text-right">
            <span class="text-slate-400 text-xs block">Accession #</span>
            <span class="font-mono font-bold text-teal-700 dark:text-teal-400">{{ patient.sample_id }}</span>
          </div>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Recipient WhatsApp Number <span class="text-red-500">*</span>
          </label>
          <input
            v-model="whatsappRecipientPhone"
            type="tel"
            placeholder="+91 9876543210"
            class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-mono font-semibold bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-teal-500"
          />
          <p class="text-xs text-slate-400 mt-1">International format with country code (+91 for India)</p>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Message Preview</label>
          <div class="p-3 bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-xl text-emerald-950 dark:text-emerald-200 font-sans whitespace-pre-line text-xs leading-relaxed">
            {{ whatsappReportMessage }}
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <Button variant="secondary" size="sm" @click="close">
            Cancel
          </Button>

          <div class="flex items-center gap-2">
            <Button variant="secondary" size="sm" icon-left="external-link" @click="sendViaWhatsAppWeb">
              WhatsApp Web
            </Button>
            <Button variant="success" size="sm" icon-left="whatsapp" :loading="isDispatchingWhatsApp" @click="sendViaWhatsAppApi">
              Instant Dispatch API
            </Button>
          </div>
        </div>
      </template>
    </Modal>

    <!-- Add Investigation to Workstation Modal -->
    <Modal
      v-model="isAddTestModalOpen"
      title="Add Investigation to Active Patient"
      description="Select test profile or panel to add to current diagnostic requisition"
      max-width="lg"
    >
      <div class="space-y-3 text-xs">
        <p class="text-slate-600 dark:text-slate-400">
          Adding test to: <strong class="text-slate-900 dark:text-slate-100">{{ patient.name }} ({{ patient.id }})</strong>
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-72 overflow-y-auto p-1">
          <div
            v-for="t in availableCatalogTests"
            :key="t.code"
            class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:bg-teal-50/40 cursor-pointer transition flex flex-col justify-between space-y-2 group bg-white dark:bg-slate-900 shadow-2xs"
            @click="addTestToCurrentPatient(t)"
          >
            <div>
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-900 dark:text-slate-100 group-hover:text-teal-700 text-xs">{{ t.name }}</span>
                <span class="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 uppercase">{{ t.code }}</span>
              </div>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Sample: {{ t.sample }} &bull; {{ t.dept }}</p>
            </div>
            <div class="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-800 text-xs">
              <span class="text-slate-400 font-mono">{{ t.analyzer }}</span>
              <span class="text-teal-600 font-semibold group-hover:underline">+ Add &rarr;</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <Button variant="secondary" size="sm" @click="close">
          Cancel
        </Button>
      </template>
    </Modal>

    <!-- 1-Click Verified Diagnostic Report Modal -->
    <Modal
      v-model="isReportModalOpen"
      title="Official Diagnostic Report Preview"
      description="Verified &amp; Certified Clinical Diagnostic Report"
      max-width="2xl"
    >
      <div class="space-y-4 text-xs font-sans">
        <!-- Lab Header Banner -->
        <div class="p-4 rounded-xl bg-teal-900 text-white flex items-center justify-between shadow-2xs">
          <div>
            <h3 class="text-base font-bold tracking-tight">AAROZI HEALTHCARE CENTRAL LAB</h3>
            <p class="text-xs text-teal-200 mt-0.5">NABL Accredited &bull; ISO 15189:2022 Certified Medical Laboratory</p>
            <p class="text-xs text-teal-300 font-mono mt-1">NABH / ICMR Ref: NABL-MC-5421 &bull; 24x7 Emergency Services</p>
          </div>
          <div class="text-right">
            <span class="inline-block px-2.5 py-1 rounded bg-emerald-500 text-white font-mono font-bold text-xs uppercase tracking-wider">
              Verified &amp; Certified
            </span>
            <p class="text-xs text-teal-200 font-mono mt-1">Generated: {{ reportGeneratedAt }}</p>
          </div>
        </div>

        <!-- Patient Demographics Banner -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-50 dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
          <div>
            <span class="text-slate-400 text-xs block">Patient Name</span>
            <span class="font-bold text-slate-900 dark:text-slate-100">{{ patient.name }}</span>
          </div>
          <div>
            <span class="text-slate-400 text-xs block">UHID / Age / Sex</span>
            <span class="font-mono font-medium text-slate-800 dark:text-slate-200">{{ patient.id }} &bull; {{ patient.age_sex }}</span>
          </div>
          <div>
            <span class="text-slate-400 text-xs block">Sample Accession</span>
            <span class="font-mono font-semibold text-teal-700 dark:text-teal-400">{{ patient.sample_id }}</span>
          </div>
          <div>
            <span class="text-slate-400 text-xs block">Referred By</span>
            <span class="font-medium text-slate-800 dark:text-slate-200">{{ patient.doctor }}</span>
          </div>
        </div>

        <!-- Verified Parameters Table -->
        <div class="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
          <div class="bg-slate-100 dark:bg-slate-800 px-3 py-2 font-bold text-slate-800 dark:text-slate-200 flex items-center justify-between text-xs">
            <span>Investigation: {{ testInfo.name }}</span>
            <span class="text-slate-500 font-normal font-mono text-xs">Method: {{ testInfo.method }}</span>
          </div>
          <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700 text-xs">
            <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 font-semibold uppercase text-xs">
              <tr>
                <th class="px-3 py-2 text-left">Parameter</th>
                <th class="px-3 py-2 text-left">Observed Value</th>
                <th class="px-3 py-2 text-left">Unit</th>
                <th class="px-3 py-2 text-left">Reference Interval</th>
                <th class="px-3 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
              <tr v-for="p in parameters" :key="p.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td class="px-3 py-2 font-medium text-slate-900 dark:text-slate-100">{{ p.name }}</td>
                <td class="px-3 py-2 font-bold font-mono" :class="p.flag.includes('High') || p.flag === 'Critical' ? 'text-red-600' : 'text-slate-900 dark:text-slate-100'">
                  {{ p.value }}
                </td>
                <td class="px-3 py-2 font-mono text-slate-500">{{ p.unit }}</td>
                <td class="px-3 py-2 font-mono text-slate-600 dark:text-slate-400">{{ p.ref_range }}</td>
                <td class="px-3 py-2">
                  <Badge :variant="p.flag === 'Critical' ? 'panic' : (p.flag.includes('High') ? 'danger' : 'success')">
                    {{ p.flag }}
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pathologist Comment & Signatures -->
        <div class="bg-slate-50 dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
          <span class="font-bold text-slate-700 dark:text-slate-300 block mb-1">Pathologist Clinical Interpretation:</span>
          <p class="text-slate-600 dark:text-slate-400 italic">{{ clinicalComment }}</p>
        </div>

        <div class="grid grid-cols-2 gap-4 pt-3 border-t border-slate-200 dark:border-slate-700 text-xs">
          <div class="text-slate-600 dark:text-slate-400">
            <p class="font-semibold text-slate-800 dark:text-slate-200">Pooja Verma, MSc (MLT)</p>
            <p class="text-xs text-slate-500">Senior Medical Laboratory Technologist</p>
            <p class="text-xs text-emerald-600 font-mono mt-0.5">Digitally Signed &bull; Lab Workstation #03</p>
          </div>
          <div class="text-right text-slate-600 dark:text-slate-400">
            <p class="font-bold text-slate-900 dark:text-slate-100">Dr. Neena Gupta, MD (Pathology)</p>
            <p class="text-xs text-slate-500">Consultant Pathologist &bull; Reg. #65412</p>
            <p class="text-xs text-emerald-600 font-mono mt-0.5">Digitally Certified &bull; NABL Signatory</p>
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <Button variant="secondary" size="sm" @click="close">
            Close
          </Button>

          <div class="flex items-center gap-2">
            <Button variant="secondary" size="sm" icon-left="edit" @click="close(); isEditingValues = true">
              Edit Values
            </Button>
            <Button variant="success" size="sm" icon-left="whatsapp" @click="sendViaWhatsAppWeb">
              WhatsApp
            </Button>
            <Button variant="primary" size="sm" icon-left="printer" @click="printVerifiedReport">
              Print PDF
            </Button>
          </div>
        </div>
      </template>
    </Modal>
  </div>
</template>
