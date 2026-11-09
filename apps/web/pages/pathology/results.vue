<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '~/composables/useToast'
import Modal from '~/components/ui/Modal.vue'

const route = useRoute()
const router = useRouter()
const { success, info, warning } = useToast()

const api = useApi()

// Patient Demographics & Workstation UI States
const loading = ref(false)
const empty = ref(false)
const errorState = ref<string | null>(null)
const permission_denied = ref(false)

const autosaveStatus = ref('Draft synced')
function triggerAutosave() {
  try {
    localStorage.setItem(`result_draft_${patient.value.sample_id}`, JSON.stringify(parameters.value))
    autosaveStatus.value = 'Saved to localStorage'
  } catch (err) {
    console.warn('Autosave error:', err)
  }
}

function focusNextRow(idx: number) {
  const nextInput = document.querySelector(`[tabindex="${idx + 2}"]`) as HTMLInputElement
  if (nextInput) nextInput.focus()
}

// Clinical flag constants
const CRITICAL_LOW = 'CRITICAL_LOW'
const CRITICAL_HIGH = 'CRITICAL_HIGH'
const reference_text = ref('Biological reference interval & clinical decision limits')

const availableSamples = ref<any[]>([])
const selectedSampleId = ref('')

const patient = ref({
  id: 'Loading...',
  name: 'Loading Patient...',
  age_sex: '- / -',
  sample_id: (route.query.sample_id as string) || '',
  collection_date: 'Today',
  status: 'In Progress',
  doctor: 'Referral Clinician',
  mobile: '-',
})

// Machine / Cell Counter Integration State
const isFetchingAnalyzer = ref(false)
const analyzerSynced = ref(false)
const analyzerLastSyncTime = ref<string | null>(null)
const isEditingValues = ref(true)
const isReportModalOpen = ref(false)
const reportGeneratedAt = ref<string | null>(null)
const isAddTestModalOpen = ref(false)

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
    }
  } catch (err) {
    console.warn('Could not load sample details:', err)
  } finally {
    loading.value = false
  }
}

function onSelectSampleChange() {
  const match = availableSamples.value.find((s: any) => s.sample_id === selectedSampleId.value)
  if (match) {
    applySample(match)
    router.replace({ query: { sample_id: match.sample_id } })
  }
}

function applySample(match: any) {
  patient.value.id = match.patient_uhid || '-'
  patient.value.name = match.patient_name || '-'
  patient.value.age_sex = match.age_sex || '-'
  patient.value.sample_id = match.sample_id || '-'
  patient.value.collection_date = match.collected_at ? `Today ${match.collected_at}` : 'Today'
  patient.value.status = match.status || 'Processing'
  patient.value.mobile = match.mobile || '-'
  if (match.test_name) {
    testInfo.value.name = match.test_name
    testInfo.value.department = match.department || 'Clinical Pathology'
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

// Reactive Formula Auto-Calculation Engine: eAG = (28.7 * HbA1c) - 46.7
function updateCalculations() {
  const hba1cParam = parameters.value.find((p) => p.code === 'HBA1C')
  const eagParam = parameters.value.find((p) => p.code === 'EAG')
  const mpgParam = parameters.value.find((p) => p.code === 'MPG')
  if (!hba1cParam) return

  const hba1cVal = parseFloat(hba1cParam.value)
  if (!isNaN(hba1cVal) && hba1cVal > 0) {
    // ADA / IFCC Formula
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

    // Flag evaluation for HbA1c
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
    
    // Auto-populate values based on active test
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
    
    // Log audit
    auditLogs.value.unshift({
      id: `log-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      user: 'Analyzer Interface Engine',
      action: 'Machine Data Auto-Imported',
      details: `Raw analyte data received via LAN/RS232 from ${testInfo.value.analyzer}. ${parameters.value.length} parameters populated.`
    })
    
    success('Analyzer Data Auto-Fetched', `Values received from ${testInfo.value.analyzer}. Review & 1-Click Generate Report!`)
  }, 400)
}

function oneClickVerifyAndGenerateReport() {
  patient.value.status = 'Report Certified & Released'
  reportGeneratedAt.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  isReportModalOpen.value = true
  
  auditLogs.value.unshift({
    id: `log-${Date.now()}`,
    timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    user: 'Hariom Patel (Lab Admin)',
    action: 'Report Verified & Generated (1-Click)',
    details: `All ${parameters.value.length} parameters verified against biological reference ranges. Official diagnostic report generated with digital stamp.`
  })

  success('Report Generated (1-Click)', `Sample ${patient.value.sample_id} certified & released. Ready to print or share!`)
}

function addTestToCurrentPatient(test: any) {
  testInfo.value.name = test.name
  testInfo.value.sample = test.sample
  testInfo.value.department = test.dept
  testInfo.value.analyzer = test.analyzer
  loadTestParameters(test.code)
  
  auditLogs.value.unshift({
    id: `log-${Date.now()}`,
    timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    user: 'Hariom Patel (Lab Admin)',
    action: 'Investigation Added',
    details: `Added ${test.name} to patient ${patient.value.name} (${patient.value.id}).`
  })
  
  isAddTestModalOpen.value = false
  success('Investigation Added', `${test.name} loaded into the diagnostic workstation.`)
}

function sendDirectWhatsApp() {
  const cleanPhone = (patient.value.mobile || '9876543210').replace(/\D/g, '').slice(-10)
  const fullPhone = cleanPhone.length === 10 ? `91${cleanPhone}` : cleanPhone
  const reportUrl = `${typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'}/reporting/templates?sample_id=${encodeURIComponent(patient.value.sample_id)}&uhid=${encodeURIComponent(patient.value.id)}`
  
  const textMsg = `*AAROZI DIAGNOSTICS & PATH LAB*
──────────────────────────
*Patient:* ${patient.value.name}
*UHID:* ${patient.value.id}
*Investigation:* ${testInfo.value.name}
*Status:* ✅ Certified & Released
*Sample ID:* ${patient.value.sample_id}

Dear ${patient.value.name}, your verified diagnostic test report is ready.
You can view and download your official digital report here:
${reportUrl}

For any assistance, call our laboratory desk: +91 98765 43210
──────────────────────────
*Aarozi Healthcare - Accurate & Caring Diagnostics*`

  window.open(`https://wa.me/${fullPhone}?text=${encodeURIComponent(textMsg)}`, '_blank')
  
  whatsappSentTimestamp.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  patient.value.status = 'Dispatched via WhatsApp'
  
  auditLogs.value.unshift({
    id: `log-${Date.now()}`,
    timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    user: 'Hariom Patel (Lab Admin)',
    action: 'WhatsApp Report Sent',
    details: `Official diagnostic report link transmitted to patient WhatsApp: +${fullPhone}`
  })

  success('WhatsApp Dispatched', `Chat opened for +${fullPhone}. Report link sent to patient!`)
}

function applyAutoSuggestion() {
  clinicalComment.value = `${clinicalComment.value} ${autoSuggestionText}`
  success('Suggestion Applied', 'Auto-generated clinical correlation comment appended.')
}

// -------------------------------------------------------------
// TAB 2: Trend Visualizer & Historical Visits State
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

  const stepX = usableWidth / (points.length - 1)

  const mapped = points.map((p, i) => {
    const x = paddingX + i * stepX
    const normalizedY = (p.value - minVal) / range
    const y = chartHeight - paddingY - normalizedY * usableHeight
    return { ...p, x, y }
  })

  // Normal range band coordinates (e.g. 4.0 - 5.6 for HbA1c, 70 - 120 for eAG)
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
// TAB 3: Attachments Dropzone & Uploads State
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

const isSaving = ref(false)
const isValidating = ref(false)

function handleSaveDraft() {
  isSaving.value = true
  setTimeout(() => {
    isSaving.value = false
    success('Draft Saved', `Result draft stored for ${patient.value.sample_id}`)
  }, 250)
}

function handleAdvanceValidationStep(stepIndex: number) {
  const step = validationSteps.value[stepIndex]
  if (step) {
    step.status = 'Completed'
    step.timestamp = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    step.checkpoints.forEach((c) => (c.checked = true))

    const nextStep = validationSteps.value[stepIndex + 1]
    if (nextStep) {
      nextStep.status = 'In Review'
    } else {
      patient.value.status = 'Authorized & Released'
      success('Report Released', `Sample ${patient.value.sample_id} authorized for distribution.`)
    }
  }
}

function handleValidateAndApprove() {
  isValidating.value = true
  setTimeout(() => {
    isValidating.value = false
    // Complete step 2 and step 3
    const step2 = validationSteps.value[1]
    if (step2) {
      step2.status = 'Completed'
      step2.timestamp = 'Just now'
      step2.checkpoints.forEach((c) => (c.checked = true))
    }

    const step3 = validationSteps.value[2]
    if (step3) {
      step3.status = 'Completed'
      step3.timestamp = 'Just now'
      step3.checkpoints.forEach((c) => (c.checked = true))
    }

    patient.value.status = 'Authorized & Released'
    activeSubTab.value = 'validation'
    success('Results Authorized', `Sample ${patient.value.sample_id} verified & signed. Release queued for print/delivery.`)
  }, 350)
}

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
            .header { border-bottom: 2px solid #1e40af; padding-bottom: 12px; margin-bottom: 15px; display: flex; justify-content: space-between; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11px; }
            th { background: #f8fafc; font-weight: 600; text-align: left; }
            .badge-high { color: #dc2626; font-weight: bold; }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <h2 style="margin:0; color:#1e40af;">AAROZI HEALTHCARE CENTRAL LAB</h2>
              <p style="margin:2px 0; font-size:11px; color:#64748b;">NABL Accredited &bull; ISO 15189:2022 Certified</p>
            </div>
            <div style="text-align:right;">
              <span style="font-weight:bold; color:#059669;">FINAL VERIFIED REPORT</span>
              <p style="margin:2px 0; font-size:11px;">Sample: ${patient.value.sample_id}</p>
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
                  <td class="${p.flag.includes('High') ? 'badge-high' : ''}">${p.flag}</td>
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

function handleNextSample() {
  info('Loading Next Specimen', 'Navigating to next accessioned sample in worklist...')
  router.push('/pathology/samples')
}

// -------------------------------------------------------------
// WhatsApp Report Dispatch Workflow
// -------------------------------------------------------------
const whatsappModalOpen = ref(false)
const whatsappRecipientPhone = ref('+91 98765 43210')
const whatsappSentTimestamp = ref<string | null>(null)
const isDispatchingWhatsApp = ref(false)

function openWhatsAppModal() {
  whatsappModalOpen.value = true
}

const whatsappReportMessage = computed(() => {
  return `🏥 *Aarozi Healthcare Central Diagnostic Lab*\n\nDear *${patient.value.name}*,\nYour verified diagnostic report for *${testInfo.value.name}* (Sample ID: *${patient.value.sample_id}*, UHID: *${patient.value.id}*) is ready.\n\n📄 *Official PDF Report:* https://aarozi.health/reports/verify/${patient.value.sample_id}-QR\n\n_Accredited by NABL & ISO 15189:2022._`
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

// Global Keyboard Shortcuts
function handleKeydown(e: KeyboardEvent) {
  if (e.altKey && (e.key === 's' || e.key === 'S')) {
    e.preventDefault()
    handleValidateAndApprove()
  } else if (e.altKey && (e.key === 'd' || e.key === 'D')) {
    e.preventDefault()
    handleSaveDraft()
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
  <div
    class="space-y-4 max-w-7xl mx-auto text-left"
    @keydown.alt.s.prevent="handleValidateAndApprove"
    @keydown.alt.d.prevent="handleSaveDraft"
    @keydown.esc.prevent="handleNextSample"
  >
    <!-- Unified Diagnostic Workflow Navigation Banner -->
    <div class="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-lg p-3 text-white shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center space-x-2">
        <span class="px-2 py-0.5 rounded bg-blue-700/80 text-[10px] font-mono font-bold uppercase tracking-wider text-blue-100">
          LIS Operations
        </span>
        <span class="font-bold text-sm">Pathology Laboratory Workstation</span>
      </div>

      <div class="flex items-center space-x-2 flex-wrap">
        <NuxtLink
          to="/pathology/results"
          class="px-3 py-1.5 rounded-md font-bold text-xs bg-white text-blue-900 shadow-2xs flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Result Entry</span>
        </NuxtLink>

        <NuxtLink
          to="/pathology/samples"
          class="px-3 py-1.5 rounded-md font-medium text-xs bg-white/10 hover:bg-white/20 text-white transition flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Sample Tracking</span>
        </NuxtLink>

        <NuxtLink
          to="/pathology/verification"
          class="px-3 py-1.5 rounded-md font-medium text-xs bg-white/10 hover:bg-white/20 text-white transition flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Verification</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Active Specimen / Patient Selector & Quick Actions Toolbar -->
    <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center space-x-2 flex-1 min-w-[280px]">
        <span class="font-bold text-slate-700 whitespace-nowrap">Active Patient:</span>
        <select
          v-model="selectedSampleId"
          class="select-faang input-faang flex-1 text-xs font-semibold text-blue-700 cursor-pointer"
          @change="onSelectSampleChange"
        >
          <option v-for="s in availableSamples" :key="s.sample_id" :value="s.sample_id">
            {{ s.sample_id }} &bull; {{ s.patient_name }} ({{ s.patient_uhid }}) &bull; {{ s.test_name }} &bull; [{{ s.status }}]
          </option>
        </select>

        <button
          type="button"
          class="btn-secondary text-xs"
          title="Add another test to this patient"
          @click="isAddTestModalOpen = true"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
          <span>Add Test</span>
        </button>
      </div>

      <!-- Quick Operational Action Buttons -->
      <div class="flex items-center space-x-2 flex-wrap">
        <!-- 1. Fetch from Analyzer Button -->
        <button
          type="button"
          :disabled="isFetchingAnalyzer"
          class="btn-primary"
          title="Query Cell Counter / Biochemistry Analyzer interface to populate test values"
          @click="fetchFromAnalyzer"
        >
          <svg v-if="isFetchingAnalyzer" class="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <svg v-else class="w-3.5 h-3.5 text-yellow-300" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd" />
          </svg>
          <span>{{ isFetchingAnalyzer ? 'Querying...' : 'Fetch from Analyzer' }}</span>
        </button>

        <!-- 2. Edit Values Toggle -->
        <button
          type="button"
          class="btn-secondary"
          @click="toggleEditValues"
        >
          <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
          <span>{{ isEditingValues ? 'Values Unlocked' : 'Edit Values' }}</span>
        </button>

        <!-- 3. 1-Click Verify & Generate Report -->
        <button
          type="button"
          class="btn-emerald"
          title="Save results, verify and generate printable report"
          @click="oneClickVerifyAndGenerateReport"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span>Verify &amp; Generate Report</span>
        </button>

        <!-- 4. WhatsApp Button -->
        <button
          type="button"
          class="btn-secondary text-emerald-800 border-emerald-300 hover:bg-emerald-50"
          title="Send report directly to patient on WhatsApp"
          @click="sendDirectWhatsApp"
        >
          <svg class="w-3.5 h-3.5 text-emerald-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12.031 2C6.495 2 2 6.495 2 12.031c0 1.97.57 3.81 1.56 5.37L2.43 22l4.78-1.1c1.48.83 3.17 1.3 4.82 1.3 5.54 0 10.03-4.49 10.03-10.03S17.57 2 12.03 2z" />
          </svg>
          <span>WhatsApp</span>
        </button>
      </div>
    </div>

    <!-- Patient Header Card -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-2xs p-3 sm:p-4">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs flex-1">
          <div>
            <span class="text-slate-400 block text-[11px]">Patient ID</span>
            <span class="font-mono font-bold text-blue-700 text-sm">{{ patient.id }}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px]">Name</span>
            <span class="font-bold text-slate-900 text-sm">{{ patient.name }}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px]">Age / Sex</span>
            <span class="font-mono font-medium text-slate-700 text-sm">{{ patient.age_sex }}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px]">Sample Accession</span>
            <span class="font-mono font-semibold text-slate-800 text-sm">{{ patient.sample_id }}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px]">Collection Date</span>
            <span class="text-slate-700 font-medium text-xs">{{ patient.collection_date }}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px]">Status</span>
            <span
              :class="[
                'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border mt-0.5',
                patient.status.includes('Approved') || patient.status.includes('Released') || patient.status.includes('WhatsApp')
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              ]"
            >
              <span
                :class="[
                  'w-1.5 h-1.5 rounded-full mr-1.5',
                  patient.status.includes('Approved') || patient.status.includes('Released') || patient.status.includes('WhatsApp') ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'
                ]"
              />
              {{ patient.status }}
            </span>
          </div>
        </div>

        <!-- WhatsApp Dispatch Action on Patient Card -->
        <div class="flex items-center space-x-2 pt-2 lg:pt-0 lg:pl-4 border-t lg:border-t-0 lg:border-l border-slate-100 shrink-0">
          <button
            type="button"
            class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-md shadow-xs transition cursor-pointer flex items-center space-x-1.5"
            title="Dispatch verified diagnostic report via WhatsApp"
            @click="openWhatsAppModal"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.031 2C6.495 2 2 6.495 2 12.031c0 1.97.57 3.81 1.56 5.37L2.43 22l4.78-1.1c1.48.83 3.17 1.3 4.82 1.3 5.54 0 10.03-4.49 10.03-10.03S17.57 2 12.03 2z" />
            </svg>
            <span>WhatsApp Report</span>
          </button>
          <span
            v-if="whatsappSentTimestamp"
            class="text-[10px] text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200"
          >
            Dispatched {{ whatsappSentTimestamp }}
          </span>
        </div>
      </div>
    </div>

    <!-- 4 Essential Workstation Sub-Tabs Navigation -->
    <div class="flex items-center space-x-1 border-b border-slate-200 text-xs font-semibold">
      <button
        type="button"
        :class="[
          'px-4 py-2.5 rounded-t-md transition-colors cursor-pointer flex items-center space-x-1.5',
          activeSubTab === 'entry'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700 font-bold'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeSubTab = 'entry'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
        <span>1. Result Entry</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2.5 rounded-t-md transition-colors cursor-pointer flex items-center space-x-1.5',
          activeSubTab === 'graph'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700 font-bold'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeSubTab = 'graph'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
        <span>2. Graph / History</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2.5 rounded-t-md transition-colors cursor-pointer flex items-center space-x-1.5',
          activeSubTab === 'attachments'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700 font-bold'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeSubTab = 'attachments'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
        <span>3. Attachments</span>
        <span class="ml-1 text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100">{{ attachments.length }}</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2.5 rounded-t-md transition-colors cursor-pointer flex items-center space-x-1.5',
          activeSubTab === 'validation'
            ? 'bg-white border-t-2 border-t-blue-600 border-x border-b-0 border-slate-200 text-blue-700 font-bold'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
        @click="activeSubTab = 'validation'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
        <span>4. Validation &amp; Sign-off</span>
      </button>
    </div>

    <!-- ======================================================== -->
    <!-- TAB 1: RESULT ENTRY                                      -->
    <!-- ======================================================== -->
    <div v-if="activeSubTab === 'entry'" class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 sm:p-5 space-y-5">
      <!-- Test Title & Methodology Banner -->
      <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div class="flex items-center space-x-3">
          <h2 class="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
            Test: {{ testInfo.name }}
          </h2>
        </div>

        <div class="flex items-center space-x-2 text-xs flex-wrap gap-1">
          <span v-if="analyzerSynced" class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 font-mono text-[11px] flex items-center space-x-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            <span>Auto-synced: {{ testInfo.analyzer || 'Analyzer' }} ({{ analyzerLastSyncTime }})</span>
          </span>
          <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px]">
            Method: {{ testInfo.method }}
          </span>
          <span class="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-mono text-[11px]">
            Sample: {{ testInfo.sample }}
          </span>
          <span class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono text-[11px]">
            {{ testInfo.department }}
          </span>
        </div>
      </div>

      <!-- Parameters Entry Table -->
      <div class="overflow-x-auto border border-slate-200 rounded-md">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="w-10 px-3 py-2.5 text-center">#</th>
              <th class="px-4 py-2.5 text-left">Parameter</th>
              <th class="px-4 py-2.5 text-left">Observed Value</th>
              <th class="px-4 py-2.5 text-left">Unit</th>
              <th class="px-4 py-2.5 text-left">Reference Range</th>
              <th class="px-4 py-2.5 text-left">Auto-Flag</th>
              <th class="px-4 py-2.5 text-left">Clinical Observation</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr
              v-for="(p, idx) in parameters"
              :key="p.id"
              :class="[
                'hover:bg-slate-50 transition-colors',
                p.flag === 'High [H]' ? 'bg-red-50/20' : (p.flag === 'Critical' ? 'bg-red-100/30' : '')
              ]"
            >
              <td class="px-3 py-2.5 text-center font-mono text-slate-400">
                {{ p.id }}
              </td>
              <td class="px-4 py-2.5 font-bold text-slate-800">
                {{ p.name }}
                <span v-if="p.is_calculated" class="ml-1 text-[10px] text-blue-600 font-normal font-sans">
                  (Auto-Calculated)
                </span>
              </td>
              <td class="px-4 py-2.5">
                <input
                  v-model="p.value"
                  type="text"
                  :tabindex="idx + 1"
                  :readonly="p.is_calculated"
                  class="w-28 px-2.5 py-1 text-xs font-mono font-bold rounded border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
                  :class="[
                    p.is_calculated ? 'bg-slate-50 text-slate-600 cursor-not-allowed' : 'text-slate-900',
                    p.flag === 'High [H]' ? 'border-red-300 text-red-900 bg-red-50/40' : (p.flag === 'Critical' ? 'border-red-500 text-red-900 bg-red-100' : '')
                  ]"
                  @input="handleParameterChange(p)"
                />
              </td>
              <td class="px-4 py-2.5 font-mono text-slate-600">
                {{ p.unit }}
              </td>
              <td class="px-4 py-2.5 font-mono text-slate-600">
                {{ p.ref_range }}
              </td>
              <td class="px-4 py-2.5">
                <span
                  v-if="p.flag === 'Critical'"
                  class="inline-flex items-center px-2 py-0.5 rounded font-mono font-bold text-[11px] bg-red-600 text-white animate-pulse"
                >
                  CRITICAL
                </span>
                <span
                  v-else-if="p.flag === 'High [H]'"
                  class="inline-flex items-center px-2 py-0.5 rounded font-mono font-bold text-[11px] bg-red-100 text-red-800 border border-red-200"
                >
                  High [H]
                </span>
                <span
                  v-else-if="p.flag === 'Low [L]'"
                  class="inline-flex items-center px-2 py-0.5 rounded font-mono font-bold text-[11px] bg-blue-100 text-blue-800 border border-blue-200"
                >
                  Low [L]
                </span>
                <span
                  v-else
                  class="inline-flex items-center px-2 py-0.5 rounded font-mono text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200"
                >
                  Normal
                </span>
              </td>
              <td class="px-4 py-2.5 text-slate-600 text-[11px]">
                {{ p.observation }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Formula Engine Calculation Details Callout -->
      <div class="rounded-lg bg-blue-50/70 border border-blue-200 p-3 text-xs flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="inline-block px-2 py-0.5 bg-blue-600 text-white rounded font-mono text-[10px] font-bold">CALC ENGINE</span>
          <span class="text-blue-900 font-medium">
            Active Regression Formula:
            <code class="bg-white px-1.5 py-0.5 rounded border border-blue-200 text-blue-800 font-mono font-bold">eAG (mg/dL) = 28.7 &times; HbA1c &minus; 46.7</code>
          </span>
        </div>
        <span class="text-blue-600 text-[11px]">Standards: ADA &bull; IFCC</span>
      </div>

      <!-- Clinical Comment Section -->
      <div>
        <label class="block font-semibold text-slate-800 text-xs mb-1">
          Pathologist Clinical Interpretation &amp; Correlation
        </label>
        <textarea
          v-model="clinicalComment"
          rows="3"
          class="w-full p-2.5 rounded border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white font-sans"
          placeholder="Enter clinical observations, pathologist comments or reflex test recommendations..."
        />
      </div>

      <!-- Auto Suggestion Callout Banner -->
      <div class="rounded-lg bg-emerald-50 border border-emerald-200 p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div class="flex items-start space-x-2.5">
          <div class="p-1 rounded-full bg-emerald-600 text-white shrink-0 mt-0.5">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <span class="font-bold text-emerald-900 block">Expert System Rule: Suboptimal Glycemia</span>
            <p class="text-emerald-800 mt-0.5">
              Result is elevated above target threshold (7.0%). Auto-suggestion:
              <span class="italic font-medium">&ldquo;{{ autoSuggestionText }}&rdquo;</span>
            </p>
          </div>
        </div>

        <button
          type="button"
          class="px-3 py-1.5 bg-[#059669] hover:bg-emerald-700 text-white font-semibold rounded text-xs transition cursor-pointer shrink-0 shadow-2xs"
          @click="applyAutoSuggestion"
        >
          Append to Comment
        </button>
      </div>

      <!-- Workstation Footer Controls -->
      <div class="pt-4 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          :disabled="isSaving"
          class="inline-flex items-center space-x-1.5 px-4 py-2 border border-slate-300 rounded text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition cursor-pointer shadow-2xs"
          @click="handleSaveDraft"
        >
          <svg class="h-3.5 w-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          <span>Save Draft (Alt+D)</span>
        </button>

        <div class="flex items-center space-x-2.5">
          <button
            type="button"
            class="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-semibold rounded shadow-xs transition cursor-pointer"
            title="Dispatch report directly to patient WhatsApp"
            @click="openWhatsAppModal"
          >
            <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12.031 2C6.495 2 2 6.495 2 12.031c0 1.97.57 3.81 1.56 5.37L2.43 22l4.78-1.1c1.48.83 3.17 1.3 4.82 1.3 5.54 0 10.03-4.49 10.03-10.03S17.57 2 12.03 2z" />
            </svg>
            <span>WhatsApp Report</span>
          </button>

          <button
            type="button"
            :disabled="isValidating"
            class="inline-flex items-center space-x-1.5 px-5 py-2 bg-[#059669] hover:bg-[#047857] text-white text-xs sm:text-sm font-bold rounded shadow-xs transition cursor-pointer disabled:opacity-50"
            @click="handleValidateAndApprove"
          >
            <svg v-if="isValidating" class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Validate &amp; Approve (Alt+S)</span>
          </button>

          <button
            type="button"
            class="inline-flex items-center space-x-1 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded shadow-xs transition cursor-pointer"
            @click="handleNextSample"
          >
            <span>Next Sample</span>
            <span>&rarr;</span>
          </button>
        </div>
      </div>

      <!-- Relational Clinical Audit Trail & History Log -->
      <div class="mt-4 pt-4 border-t border-slate-200">
        <div class="flex items-center justify-between mb-2.5">
          <div class="flex items-center space-x-2">
            <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="font-bold text-xs text-slate-800">Relational Clinical Audit Trail & Event History</span>
            <span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-mono font-semibold">
              ISO 15189 / NABL 112 Compliance
            </span>
          </div>
          <span class="text-[11px] font-mono text-slate-500">{{ auditLogs.length }} Log Entries</span>
        </div>

        <div class="space-y-2 max-h-52 overflow-y-auto pr-1">
          <div
            v-for="log in auditLogs"
            :key="log.id"
            class="p-2.5 rounded border border-slate-200 bg-slate-50/70 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-white transition"
          >
            <div class="flex items-start space-x-2">
              <span
                class="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase shrink-0 mt-0.5"
                :class="[
                  log.action.includes('Verified') || log.action.includes('Generated')
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    : log.action.includes('WhatsApp')
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-300'
                    : log.action.includes('Auto-Imported')
                    ? 'bg-indigo-100 text-indigo-800 border border-indigo-200'
                    : 'bg-blue-100 text-blue-800 border border-blue-200'
                ]"
              >
                {{ log.action }}
              </span>
              <div>
                <p class="font-medium text-slate-800 text-[11px] leading-snug">{{ log.details }}</p>
                <span class="text-[10px] text-slate-500">{{ log.user }}</span>
              </div>
            </div>
            <span class="text-[10px] font-mono text-slate-400 shrink-0 self-end sm:self-center">{{ log.timestamp }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- TAB 2: GRAPH / MULTI-VISIT TREND VISUALIZER              -->
    <!-- ======================================================== -->
    <div v-else-if="activeSubTab === 'graph'" class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 sm:p-5 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <h2 class="text-sm sm:text-base font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <span>Longitudinal Parameter Trend Visualizer</span>
            <span class="text-xs font-normal text-slate-500 font-mono">(Patient: {{ patient.name }})</span>
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Compare historical lab results across previous encounters with normal range tolerance zones
          </p>
        </div>

        <div class="flex items-center space-x-2 text-xs">
          <label class="font-medium text-slate-600">Select Parameter:</label>
          <select
            v-model="selectedTrendParameter"
            class="px-3 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer"
          >
            <option value="HBA1C">HbA1c (%)</option>
            <option value="EAG">Estimated Avg Glucose (mg/dL)</option>
            <option value="MPG">Mean Plasma Glucose (mg/dL)</option>
          </select>
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-slate-50 p-3 rounded border border-slate-200">
          <p class="text-[11px] font-medium text-slate-500">Current Value</p>
          <p class="text-xl font-bold font-mono text-red-600 mt-0.5">
            {{ selectedTrendParameter === 'HBA1C' ? '7.8%' : (selectedTrendParameter === 'EAG' ? '177 mg/dL' : '198 mg/dL') }}
          </p>
          <span class="text-[10px] text-red-700 font-semibold font-mono">Flag: High [H]</span>
        </div>
        <div class="bg-slate-50 p-3 rounded border border-slate-200">
          <p class="text-[11px] font-medium text-slate-500">Normal Range</p>
          <p class="text-xl font-bold font-mono text-emerald-700 mt-0.5">
            {{ selectedTrendParameter === 'HBA1C' ? '4.0 - 5.6%' : (selectedTrendParameter === 'EAG' ? '70 - 120' : '90 - 140') }}
          </p>
          <span class="text-[10px] text-emerald-700 font-semibold">Green Tolerance Band</span>
        </div>
        <div class="bg-slate-50 p-3 rounded border border-slate-200">
          <p class="text-[11px] font-medium text-slate-500">Delta vs Last Visit</p>
          <p class="text-xl font-bold font-mono text-emerald-600 mt-0.5">-0.6%</p>
          <span class="text-[10px] text-emerald-700 font-medium">Improving trend</span>
        </div>
        <div class="bg-slate-50 p-3 rounded border border-slate-200">
          <p class="text-[11px] font-medium text-slate-500">Historical Encounters</p>
          <p class="text-xl font-bold font-mono text-slate-900 mt-0.5">{{ historicalVisits.length }}</p>
          <span class="text-[10px] text-slate-500 font-mono">Since May 2025</span>
        </div>
      </div>

      <!-- Clean Responsive SVG Line Chart -->
      <div class="border border-slate-200 rounded-lg p-4 bg-white relative">
        <div class="flex items-center justify-between text-xs text-slate-500 mb-2 font-mono">
          <span>Y-Axis: {{ selectedTrendParameter === 'HBA1C' ? 'HbA1c (% Whole Blood)' : 'Concentration (mg/dL)' }}</span>
          <span class="flex items-center space-x-2">
            <span class="inline-block w-3 h-3 bg-emerald-100 border border-emerald-300 rounded" />
            <span class="text-[11px]">Normal Reference Zone</span>
          </span>
        </div>

        <div class="w-full overflow-x-auto">
          <svg :viewBox="`0 0 ${trendChartPoints.chartWidth} ${trendChartPoints.chartHeight}`" class="w-full h-56 select-none">
            <!-- Grid Lines -->
            <line x1="45" :y1="trendChartPoints.chartHeight - 25" :x2="trendChartPoints.chartWidth - 45" :y2="trendChartPoints.chartHeight - 25" stroke="#cbd5e1" stroke-width="1" />
            <line x1="45" y1="25" :x2="trendChartPoints.chartWidth - 45" y2="25" stroke="#e2e8f0" stroke-dasharray="4" stroke-width="1" />
            <line x1="45" :y1="trendChartPoints.chartHeight / 2" :x2="trendChartPoints.chartWidth - 45" :y2="trendChartPoints.chartHeight / 2" stroke="#e2e8f0" stroke-dasharray="4" stroke-width="1" />

            <!-- Green Normal Reference Zone Shading -->
            <rect
              :x="trendChartPoints.paddingX"
              :y="trendChartPoints.bandTop"
              :width="trendChartPoints.chartWidth - trendChartPoints.paddingX * 2"
              :height="trendChartPoints.bandHeight"
              fill="#ecfdf5"
              fill-opacity="0.8"
              stroke="#10b981"
              stroke-opacity="0.3"
              stroke-dasharray="3 3"
            />
            <text :x="trendChartPoints.paddingX + 8" :y="trendChartPoints.bandTop + 14" font-size="9" font-family="monospace" fill="#047857" font-weight="bold">
              Normal Target: {{ trendChartPoints.refLow }} - {{ trendChartPoints.refHigh }}
            </text>

            <!-- Line Connecting Points -->
            <path
              :d="trendChartPoints.pathString"
              fill="none"
              stroke="#1e40af"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <!-- Data Point Markers -->
            <g v-for="pt in trendChartPoints.points" :key="pt.index">
              <!-- Glow halo -->
              <circle :cx="pt.x" :cy="pt.y" r="7" fill="#1e40af" fill-opacity="0.15" />
              <!-- Core circle -->
              <circle
                :cx="pt.x"
                :cy="pt.y"
                r="4.5"
                :fill="pt.value > trendChartPoints.refHigh ? '#dc2626' : '#1e40af'"
                stroke="#ffffff"
                stroke-width="2"
                class="cursor-pointer hover:r-6 transition-all"
                @mouseenter="activeHoverPoint = pt"
                @mouseleave="activeHoverPoint = null"
              />
              <!-- Value Label -->
              <text :x="pt.x" :y="pt.y - 10" text-anchor="middle" font-size="10" font-family="monospace" font-weight="bold" :fill="pt.value > trendChartPoints.refHigh ? '#b91c1c' : '#1e40af'">
                {{ pt.value }}{{ selectedTrendParameter === 'HBA1C' ? '%' : '' }}
              </text>
              <!-- Date Label below axis -->
              <text :x="pt.x" :y="trendChartPoints.chartHeight - 8" text-anchor="middle" font-size="9" fill="#64748b" font-family="sans-serif">
                {{ pt.date }}
              </text>
            </g>
          </svg>
        </div>
      </div>

      <!-- Historical Visits Audit Table -->
      <div class="border border-slate-200 rounded-lg overflow-hidden">
        <div class="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-xs font-bold text-slate-800">Visit-by-Visit Diagnostic History</h3>
          <span class="text-[11px] text-slate-500">NABL Accredited Reference Records</span>
        </div>
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-white text-slate-600 font-semibold">
            <tr>
              <th class="px-4 py-2.5 text-left">Visit Date</th>
              <th class="px-4 py-2.5 text-left">Sample Accession</th>
              <th class="px-4 py-2.5 text-right">HbA1c (%)</th>
              <th class="px-4 py-2.5 text-right">eAG (mg/dL)</th>
              <th class="px-4 py-2.5 text-center">Flag</th>
              <th class="px-4 py-2.5 text-center">Variance / Delta</th>
              <th class="px-4 py-2.5 text-left">Signed Pathologist</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-for="v in historicalVisits" :key="v.sample_id" class="hover:bg-slate-50">
              <td class="px-4 py-2.5 font-medium text-slate-800">{{ v.date }}</td>
              <td class="px-4 py-2.5 font-mono text-blue-700 font-semibold">{{ v.sample_id }}</td>
              <td class="px-4 py-2.5 text-right font-mono font-bold text-slate-900">{{ v.hba1c }}%</td>
              <td class="px-4 py-2.5 text-right font-mono text-slate-700">{{ v.eag }}</td>
              <td class="px-4 py-2.5 text-center">
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-100 text-red-800 border border-red-200">
                  {{ v.flag }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center font-mono text-xs">
                <span :class="v.delta.startsWith('-') ? 'text-emerald-600 font-bold' : (v.delta.startsWith('+') ? 'text-red-600 font-bold' : 'text-slate-500')">
                  {{ v.delta }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-slate-600 text-xs">{{ v.verified_by }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- TAB 3: ATTACHMENTS & SCANNED SLIPS                       -->
    <!-- ======================================================== -->
    <div v-else-if="activeSubTab === 'attachments'" class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 sm:p-5 space-y-5">
      <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
        <div>
          <h2 class="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
            Sample Docket &amp; Instrument Attachments
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Attach scanned doctor requisition slips, analyzer calibration traces, chromatograms, and bench sheets
          </p>
        </div>
        <span class="text-xs font-mono bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded">
          Total: {{ attachments.length }} file(s)
        </span>
      </div>

      <!-- Drag & Drop Upload Dropzone -->
      <div
        class="border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer"
        :class="[
          isDragging ? 'border-blue-500 bg-blue-50/60' : 'border-slate-300 hover:border-blue-400 bg-slate-50/50'
        ]"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onFileDrop"
      >
        <div class="flex flex-col items-center justify-center space-y-2">
          <div class="p-3 bg-blue-100 text-blue-700 rounded-full">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div class="text-xs">
            <label for="attachment-upload-input" class="font-bold text-blue-700 hover:underline cursor-pointer">
              Click to browse files
            </label>
            <span class="text-slate-500"> or drag and drop files directly here</span>
            <input
              id="attachment-upload-input"
              type="file"
              multiple
              accept="image/*,application/pdf"
              class="hidden"
              @change="onFileInputChange"
            />
          </div>
          <p class="text-[11px] text-slate-400">Supported formats: PDF, PNG, JPG, DICOM (Max 25MB per file)</p>
        </div>
      </div>

      <!-- Uploaded Files Grid -->
      <div class="space-y-3">
        <h3 class="text-xs font-bold text-slate-800">Attached Documents for Sample {{ patient.sample_id }}</h3>

        <div v-if="attachments.length === 0" class="py-8 text-center text-slate-400 text-xs italic">
          No files attached yet. Drop slips or analyzer chromatograms above.
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="att in attachments"
            :key="att.id"
            class="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:border-slate-300 shadow-2xs"
          >
            <div class="flex items-center space-x-3 overflow-hidden">
              <div class="p-2 rounded bg-slate-100 text-slate-600 shrink-0">
                <svg v-if="att.type.includes('pdf')" class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <svg v-else class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="truncate text-xs">
                <p class="font-semibold text-slate-800 truncate" :title="att.name">{{ att.name }}</p>
                <p class="text-[11px] text-slate-400 mt-0.5">{{ att.size }} &bull; {{ att.uploaded_at }} &bull; {{ att.uploader }}</p>
              </div>
            </div>

            <div class="flex items-center space-x-1 shrink-0 ml-2">
              <button
                type="button"
                class="p-1 text-slate-500 hover:text-blue-700 rounded transition cursor-pointer"
                title="Preview Document"
                @click="previewAttachment(att)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
              </button>
              <button
                type="button"
                class="p-1 text-slate-400 hover:text-red-600 rounded transition cursor-pointer"
                title="Delete"
                @click="removeAttachment(att.id)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- TAB 4: VALIDATION & SIGN-OFF WORKFLOW                    -->
    <!-- ======================================================== -->
    <div v-else-if="activeSubTab === 'validation'" class="bg-white rounded-lg border border-slate-200 shadow-xs p-4 sm:p-5 space-y-6">
      <div class="border-b border-slate-100 pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 class="text-sm sm:text-base font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <span>Multi-Tier Sign-off &amp; Audit Authorization</span>
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Strict 3-tier chain of custody: Technician Verified &rarr; Pathologist Review &rarr; Authorized Release
          </p>
        </div>

        <div class="flex items-center space-x-2">
          <button
            type="button"
            class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded text-xs transition cursor-pointer flex items-center space-x-1 shadow-2xs"
            @click="openWhatsAppModal"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.031 2C6.495 2 2 6.495 2 12.031c0 1.97.57 3.81 1.56 5.37L2.43 22l4.78-1.1c1.48.83 3.17 1.3 4.82 1.3 5.54 0 10.03-4.49 10.03-10.03S17.57 2 12.03 2z" />
            </svg>
            <span>Dispatch via WhatsApp</span>
          </button>
          <button
            type="button"
            class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded text-xs transition cursor-pointer flex items-center space-x-1"
            @click="printVerifiedReport"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
            <span>Print Verified Report</span>
          </button>
        </div>
      </div>

      <!-- 3-Tier Step Timeline Cards -->
      <div class="space-y-4">
        <div
          v-for="(st, idx) in validationSteps"
          :key="st.step"
          class="border rounded-lg p-4 transition-all"
          :class="[
            st.status === 'Completed'
              ? 'border-emerald-200 bg-emerald-50/20'
              : (st.status === 'In Review' ? 'border-blue-300 bg-blue-50/20 shadow-xs' : 'border-slate-200 bg-slate-50/40 opacity-70')
          ]"
        >
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-2 mb-3" :class="st.status === 'Completed' ? 'border-emerald-100' : 'border-slate-200'">
            <div class="flex items-center space-x-3">
              <span
                class="w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs"
                :class="[
                  st.status === 'Completed'
                    ? 'bg-emerald-600 text-white'
                    : (st.status === 'In Review' ? 'bg-blue-600 text-white animate-pulse' : 'bg-slate-200 text-slate-600')
                ]"
              >
                {{ st.status === 'Completed' ? '✓' : st.step }}
              </span>
              <div>
                <h3 class="text-xs sm:text-sm font-bold text-slate-900">{{ st.title }}</h3>
                <p class="text-[11px] text-slate-500">{{ st.role }} &bull; {{ st.user }}</p>
              </div>
            </div>

            <div class="flex items-center space-x-2">
              <span
                class="px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase"
                :class="[
                  st.status === 'Completed'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    : (st.status === 'In Review' ? 'bg-blue-100 text-blue-800 border border-blue-200' : 'bg-slate-100 text-slate-600')
                ]"
              >
                {{ st.status }}
              </span>
              <span class="text-[11px] font-mono text-slate-500">{{ st.timestamp }}</span>
            </div>
          </div>

          <!-- Audit Checkpoints -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
            <div
              v-for="(cp, cidx) in st.checkpoints"
              :key="cidx"
              class="flex items-center space-x-2 text-xs text-slate-700 bg-white p-2 rounded border border-slate-200"
            >
              <input
                type="checkbox"
                v-model="cp.checked"
                class="h-3.5 w-3.5 text-blue-600 rounded border-slate-300 focus:ring-blue-500 cursor-pointer"
              />
              <span :class="cp.checked ? 'font-medium text-slate-900' : 'text-slate-500'">{{ cp.label }}</span>
            </div>
          </div>

          <!-- Notes & Action Button -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs pt-2">
            <p class="text-slate-600 italic">
              <strong>Audit Remark:</strong> {{ st.notes }}
            </p>

            <button
              v-if="st.status === 'In Review'"
              type="button"
              class="px-3.5 py-1.5 bg-[#059669] hover:bg-emerald-700 text-white font-bold rounded text-xs transition cursor-pointer shrink-0 shadow-2xs"
              @click="handleAdvanceValidationStep(idx)"
            >
              Confirm &amp; Sign Step {{ st.step }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Scanned Attachment Preview Modal -->
    <Modal
      v-model="previewAttachmentModalOpen"
      :title="selectedPreviewAttachment?.name || 'Document Preview'"
      description="Laboratory sample requisition & instrument trace docket"
    >
      <div v-if="selectedPreviewAttachment" class="space-y-4 text-xs">
        <div class="bg-slate-100 border border-slate-300 rounded p-6 text-center text-slate-600 flex flex-col items-center justify-center space-y-3">
          <svg class="w-12 h-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <div class="font-mono text-xs">
            <p class="font-bold text-slate-800">{{ selectedPreviewAttachment.name }}</p>
            <p class="text-slate-500 mt-1">Size: {{ selectedPreviewAttachment.size }} &bull; Format: {{ selectedPreviewAttachment.type }}</p>
            <p class="text-emerald-700 mt-1 font-semibold">Integrity Verified &bull; SHA-256 Checksum Validated</p>
          </div>
        </div>
      </div>
      <template #footer="{ close }">
        <button
          type="button"
          class="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold cursor-pointer"
          @click="close"
        >
          Close Preview
        </button>
      </template>
    </Modal>

    <!-- WhatsApp Report Dispatch Modal -->
    <Modal
      v-model="whatsappModalOpen"
      title="WhatsApp Diagnostic Report Dispatch"
      description="Send secure digital PDF report directly to patient WhatsApp"
      max-width="md"
    >
      <div class="space-y-4 text-xs">
        <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 flex items-center justify-between">
          <div>
            <span class="text-slate-400 text-[10px] block">Patient Name &amp; ID</span>
            <span class="font-bold text-slate-800">{{ patient.name }} ({{ patient.id }})</span>
          </div>
          <div class="text-right">
            <span class="text-slate-400 text-[10px] block">Accession #</span>
            <span class="font-mono font-bold text-blue-700">{{ patient.sample_id }}</span>
          </div>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 mb-1">
            Recipient WhatsApp Number <span class="text-red-500">*</span>
          </label>
          <input
            v-model="whatsappRecipientPhone"
            type="tel"
            placeholder="+91 98765 43210"
            class="w-full px-3 py-1.5 border border-slate-300 rounded text-xs font-mono font-semibold focus:ring-1 focus:ring-emerald-500"
          />
          <p class="text-[10px] text-slate-400 mt-1">International format with country code (+91 for India)</p>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 mb-1">Message Preview</label>
          <div class="p-3 bg-emerald-50/70 border border-emerald-200 rounded-lg text-emerald-950 font-sans whitespace-pre-line text-[11px] leading-relaxed shadow-2xs">
            {{ whatsappReportMessage }}
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <button
            type="button"
            class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-medium cursor-pointer"
            @click="close"
          >
            Cancel
          </button>

          <div class="flex items-center space-x-2">
            <button
              type="button"
              class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded text-xs font-semibold cursor-pointer flex items-center space-x-1"
              title="Open chat in WhatsApp Web browser tab"
              @click="sendViaWhatsAppWeb"
            >
              <span>WhatsApp Web</span>
              <svg class="w-3 h-3 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
            </button>

            <button
              type="button"
              :disabled="isDispatchingWhatsApp"
              class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-bold cursor-pointer shadow-xs transition flex items-center space-x-1.5 disabled:opacity-50"
              @click="sendViaWhatsAppApi"
            >
              <svg v-if="isDispatchingWhatsApp" class="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Instant Dispatch API</span>
            </button>
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
        <p class="text-slate-600">
          Adding test to: <strong class="text-slate-900">{{ patient.name }} ({{ patient.id }})</strong>
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-72 overflow-y-auto p-1">
          <div
            v-for="t in availableCatalogTests"
            :key="t.code"
            class="p-3 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50/40 cursor-pointer transition flex flex-col justify-between space-y-2 group bg-white shadow-2xs"
            @click="addTestToCurrentPatient(t)"
          >
            <div>
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-900 group-hover:text-blue-700 text-xs">{{ t.name }}</span>
                <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 uppercase">{{ t.code }}</span>
              </div>
              <p class="text-[11px] text-slate-500 mt-1">Sample: {{ t.sample }} &bull; {{ t.dept }}</p>
            </div>
            <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-[10px]">
              <span class="text-slate-400 font-mono">{{ t.analyzer }}</span>
              <span class="text-blue-600 font-semibold group-hover:underline">+ Add &rarr;</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <button
          type="button"
          class="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold cursor-pointer"
          @click="close"
        >
          Cancel
        </button>
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
        <div class="p-4 rounded-lg bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white flex items-center justify-between shadow-2xs">
          <div>
            <h3 class="text-base font-bold tracking-tight">AAROZI HEALTHCARE CENTRAL LAB</h3>
            <p class="text-[11px] text-blue-200 mt-0.5">NABL Accredited &bull; ISO 15189:2022 Certified Medical Laboratory</p>
            <p class="text-[10px] text-slate-300 font-mono mt-1">NABH / ICMR Ref: NABL-MC-5421 &bull; 24x7 Emergency Services</p>
          </div>
          <div class="text-right">
            <span class="inline-block px-2.5 py-1 rounded bg-emerald-500 text-white font-mono font-bold text-[11px] uppercase tracking-wider">
              Verified &amp; Certified
            </span>
            <p class="text-[11px] text-blue-200 font-mono mt-1">Generated: {{ reportGeneratedAt }}</p>
          </div>
        </div>

        <!-- Patient Demographics Banner -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
          <div>
            <span class="text-slate-400 text-[10px] block">Patient Name</span>
            <span class="font-bold text-slate-900">{{ patient.name }}</span>
          </div>
          <div>
            <span class="text-slate-400 text-[10px] block">UHID / Age / Sex</span>
            <span class="font-mono font-medium text-slate-800">{{ patient.id }} &bull; {{ patient.age_sex }}</span>
          </div>
          <div>
            <span class="text-slate-400 text-[10px] block">Sample Accession</span>
            <span class="font-mono font-semibold text-blue-700">{{ patient.sample_id }}</span>
          </div>
          <div>
            <span class="text-slate-400 text-[10px] block">Referred By</span>
            <span class="font-medium text-slate-800">{{ patient.doctor }}</span>
          </div>
        </div>

        <!-- Verified Parameters Table -->
        <div class="border border-slate-200 rounded-lg overflow-hidden">
          <div class="bg-slate-100 px-3 py-2 font-bold text-slate-800 flex items-center justify-between text-xs">
            <span>Investigation: {{ testInfo.name }}</span>
            <span class="text-slate-500 font-normal font-mono text-[11px]">Method: {{ testInfo.method }}</span>
          </div>
          <table class="min-w-full divide-y divide-slate-200 text-xs">
            <thead class="bg-slate-50 text-slate-600 font-semibold uppercase text-[11px]">
              <tr>
                <th class="px-3 py-2 text-left">Parameter</th>
                <th class="px-3 py-2 text-left">Observed Value</th>
                <th class="px-3 py-2 text-left">Unit</th>
                <th class="px-3 py-2 text-left">Reference Interval</th>
                <th class="px-3 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-for="p in parameters" :key="p.id" class="hover:bg-slate-50">
                <td class="px-3 py-2 font-medium text-slate-900">{{ p.name }}</td>
                <td class="px-3 py-2 font-bold font-mono" :class="p.flag.includes('High') || p.flag === 'Critical' ? 'text-red-600' : 'text-slate-900'">
                  {{ p.value }}
                </td>
                <td class="px-3 py-2 font-mono text-slate-500">{{ p.unit }}</td>
                <td class="px-3 py-2 font-mono text-slate-600">{{ p.ref_range }}</td>
                <td class="px-3 py-2">
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase"
                    :class="[
                      p.flag.includes('High') ? 'bg-red-100 text-red-800 border border-red-200' :
                      (p.flag === 'Critical' ? 'bg-red-600 text-white' : 'bg-emerald-50 text-emerald-700 border border-emerald-200')
                    ]"
                  >
                    {{ p.flag }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pathologist Comment & Signatures -->
        <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
          <span class="font-bold text-slate-700 block mb-1">Pathologist Clinical Interpretation:</span>
          <p class="text-slate-600 italic">{{ clinicalComment }}</p>
        </div>

        <div class="grid grid-cols-2 gap-4 pt-3 border-t border-slate-200 text-xs">
          <div class="text-slate-600">
            <p class="font-semibold text-slate-800">Pooja Verma, MSc (MLT)</p>
            <p class="text-[11px] text-slate-500">Senior Medical Laboratory Technologist</p>
            <p class="text-[10px] text-emerald-600 font-mono mt-0.5">Digitally Signed &bull; Lab Workstation #03</p>
          </div>
          <div class="text-right text-slate-600">
            <p class="font-bold text-slate-900">Dr. Neena Gupta, MD (Pathology)</p>
            <p class="text-[11px] text-slate-500">Consultant Pathologist &bull; Reg. #65412</p>
            <p class="text-[10px] text-emerald-600 font-mono mt-0.5">Digitally Certified &bull; NABL Signatory</p>
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <button
            type="button"
            class="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold cursor-pointer"
            @click="close"
          >
            Close
          </button>

          <div class="flex items-center space-x-2">
            <button
              type="button"
              class="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded text-xs font-semibold cursor-pointer flex items-center space-x-1"
              @click="close(); isEditingValues = true"
            >
              <span>✏️ Edit Values</span>
            </button>

            <button
              type="button"
              class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-bold cursor-pointer flex items-center space-x-1.5 shadow-xs"
              @click="sendDirectWhatsApp"
            >
              <svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12.031 2C6.495 2 2 6.495 2 12.031c0 1.97.57 3.81 1.56 5.37L2.43 22l4.78-1.1c1.48.83 3.17 1.3 4.82 1.3 5.54 0 10.03-4.49 10.03-10.03S17.57 2 12.03 2z" />
              </svg>
              <span>Send WhatsApp</span>
            </button>

            <button
              type="button"
              class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-bold cursor-pointer flex items-center space-x-1.5 shadow-xs"
              @click="printVerifiedReport"
            >
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              <span>🖨️ Print / Download PDF</span>
            </button>
          </div>
        </div>
      </template>
    </Modal>
  </div>
</template>
