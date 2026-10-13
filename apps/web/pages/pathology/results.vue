<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between border-b border-gray-200 pb-4">
      <div>
        <div class="flex items-center space-x-2 text-xs text-gray-500 mb-1">
          <NuxtLink to="/dashboard" class="hover:underline">Dashboard</NuxtLink>
          <span>/</span>
          <NuxtLink to="/pathology" class="hover:underline">Pathology</NuxtLink>
          <span>/</span>
          <span class="text-gray-900 font-medium">Result Entry</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Rapid Result Entry</h1>
        <p class="text-sm text-gray-500">Keyboard-first rapid result bench (Alt+S submit, Alt+D draft, Enter next row, Esc reset)</p>
      </div>

      <div class="flex items-center space-x-3">
        <span v-if="autosaveStatus === 'saving'" class="text-xs text-blue-600 font-medium flex items-center space-x-1">
          <span class="inline-block w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
          <span>Saving draft...</span>
        </span>
        <span v-else-if="autosaveStatus === 'saved'" class="text-xs text-green-600 font-medium">
          Draft autosaved {{ lastSavedTime }}
        </span>

        <button
          type="button"
          class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          @click="resetForm"
        >
          Clear (Esc)
        </button>
        <button
          type="button"
          class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          :disabled="uiState === 'loading'"
          @click="saveDraft"
        >
          Save Draft (Alt+D)
        </button>
        <button
          type="button"
          class="px-5 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm"
          :disabled="uiState === 'loading'"
          @click="submitResults"
        >
          Submit &amp; Enter (Alt+S)
        </button>
      </div>
    </div>

    <div v-if="uiState === 'error'" class="p-4 rounded-md bg-red-50 border border-red-200">
      <h3 class="text-sm font-medium text-red-800">Result Entry Error</h3>
      <p class="mt-1 text-sm text-red-700">{{ errorMessage }}</p>
    </div>

    <div v-if="uiState === 'permission_denied'" class="p-8 text-center bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 class="text-base font-semibold text-gray-900">Permission Denied</h3>
      <p class="mt-1 text-sm text-gray-500">You do not have permission ('result.enter') to enter laboratory test results.</p>
    </div>

    <div v-else-if="uiState === 'empty'" class="p-8 text-center bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 class="text-base font-semibold text-gray-900">No Specimen Selected</h3>
      <p class="mt-1 text-sm text-gray-500">Select an accessioned order item from the bench worklist to begin result entry.</p>
    </div>

    <div v-else-if="uiState === 'loading'" class="p-12 text-center bg-white rounded-lg border border-gray-200 shadow-sm">
      <div class="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-2 text-sm text-gray-500">Loading test analytes and reference ranges...</p>
    </div>
    <div
      v-else
      class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden"
      @keydown.alt.s.prevent="submitResults"
      @keydown.alt.d.prevent="saveDraft"
      @keydown.esc="resetForm"
    >
      <div class="bg-gray-50 px-6 py-4 border-b border-gray-200 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-600">
        <div>
          <span class="font-semibold text-gray-800 block">Patient</span>
          <span>{{ patientInfo.name }} ({{ patientInfo.patient_no }})</span>
        </div>
        <div>
          <span class="font-semibold text-gray-800 block">Demographics</span>
          <span>{{ patientInfo.sex }}, {{ patientInfo.age }} yrs</span>
        </div>
        <div>
          <span class="font-semibold text-gray-800 block">Order</span>
          <span>{{ specimenInfo.order_no }}</span>
        </div>
        <div>
          <span class="font-semibold text-gray-800 block">Context</span>
          <span>{{ specimenInfo.context || 'General' }}</span>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 text-sm">
          <thead class="bg-gray-50 text-gray-600 text-xs font-semibold uppercase">
            <tr>
              <th scope="col" class="px-6 py-3 text-left">Analyte / Test</th>
              <th scope="col" class="px-6 py-3 text-left">Result Value</th>
              <th scope="col" class="px-6 py-3 text-left">Unit</th>
              <th scope="col" class="px-6 py-3 text-left">Reference Range</th>
              <th scope="col" class="px-6 py-3 text-left">Flag</th>
              <th scope="col" class="px-6 py-3 text-left">Notes</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="(analyte, idx) in analytes" :key="analyte.code" class="hover:bg-gray-50">
              <td class="px-6 py-3 font-medium text-gray-900 whitespace-nowrap">
                <div>{{ analyte.name }}</div>
                <div class="text-xs text-gray-400 font-mono">{{ analyte.code }}</div>
              </td>
              <td class="px-6 py-3 whitespace-nowrap">
                <input
                  :id="'analyte-input-' + idx"
                  :ref="el => { if (el) inputRefs[idx] = el as any }"
                  v-model="analyte.raw_value"
                  type="text"
                  class="w-36 h-9 px-3 rounded border text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :class="getInputHighlightClass(analyte)"
                  placeholder="Enter value"
                  @input="handleValueChange"
                  @keydown.enter.prevent="focusNextRow(idx)"
                />
              </td>
              <td class="px-6 py-3 text-gray-500 whitespace-nowrap">{{ analyte.unit || '-' }}</td>
              <td class="px-6 py-3 text-gray-600 text-xs whitespace-nowrap font-mono">{{ analyte.reference_text || 'Standard' }}</td>
              <td class="px-6 py-3 whitespace-nowrap">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full uppercase" :class="getFlagBadgeClass(analyte)">
                  {{ analyte.flag || 'NORMAL' }}
                </span>
              </td>
              <td class="px-6 py-3 whitespace-nowrap">
                <input
                  v-model="analyte.notes"
                  type="text"
                  class="w-48 h-8 px-2 rounded border border-gray-200 text-xs text-gray-600"
                  placeholder="Clinical note"
                  @input="handleValueChange"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>


<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'

interface AnalyteItem {
  code: string
  name: string
  raw_value: string
  unit?: string
  reference_text?: string
  low_value?: number
  high_value?: number
  critical_low?: number
  critical_high?: number
  flag?: string
  notes?: string
}

type UIState = 'idle' | 'loading' | 'empty' | 'error' | 'permission_denied'
type AutosaveStatus = 'idle' | 'saving' | 'saved'

const uiState = ref<UIState>('idle')
const autosaveStatus = ref<AutosaveStatus>('idle')
const errorMessage = ref('')
const lastSavedTime = ref('just now')
const inputRefs = reactive<{ [key: number]: HTMLInputElement }>({})

const patientInfo = reactive({
  name: 'John Doe',
  patient_no: 'PAT-1002',
  sex: 'Male',
  age: '45',
})

const specimenInfo = reactive({
  order_no: 'ORD-20261013-0001',
  barcode: 'SMP-883920',
  context: 'Fasting',
})

const analytes = ref<AnalyteItem[]>([
  {
    code: 'GLU',
    name: 'Fasting Blood Glucose',
    raw_value: '95',
    unit: 'mg/dL',
    reference_text: '70 - 99 mg/dL',
    low_value: 70,
    high_value: 99,
    critical_low: 45,
    critical_high: 400,
    flag: 'NORMAL',
    notes: '',
  },
  {
    code: 'CHOL',
    name: 'Total Cholesterol',
    raw_value: '',
    unit: 'mg/dL',
    reference_text: '125 - 200 mg/dL',
    low_value: 125,
    high_value: 200,
    flag: 'NORMAL',
    notes: '',
  },
  {
    code: 'TRIG',
    name: 'Triglycerides',
    raw_value: '',
    unit: 'mg/dL',
    reference_text: '< 150 mg/dL',
    high_value: 150,
    flag: 'NORMAL',
    notes: '',
  },
])

let autosaveTimer: any = null

function handleValueChange() {
  evaluateFlags()
  triggerAutosave()
}

function evaluateFlags() {
  for (const a of analytes.value) {
    if (!a.raw_value) {
      a.flag = 'NORMAL'
      continue
    }
    const num = parseFloat(a.raw_value)
    if (isNaN(num)) {
      a.flag = 'NORMAL'
      continue
    }
    if (a.critical_low !== undefined && num < a.critical_low) {
      a.flag = 'CRITICAL_LOW'
    } else if (a.critical_high !== undefined && num > a.critical_high) {
      a.flag = 'CRITICAL_HIGH'
    } else if (a.low_value !== undefined && num < a.low_value) {
      a.flag = 'LOW'
    } else if (a.high_value !== undefined && num > a.high_value) {
      a.flag = 'HIGH'
    } else {
      a.flag = 'NORMAL'
    }
  }
}

function triggerAutosave() {
  autosaveStatus.value = 'saving'
  clearTimeout(autosaveTimer)
  autosaveTimer = setTimeout(() => {
    // Save draft to localStorage as durable offline fallback
    try {
      localStorage.setItem('aarozi_draft_' + specimenInfo.order_no, JSON.stringify(analytes.value))
    } catch {}
    autosaveStatus.value = 'saved'
    lastSavedTime.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }, 1000)
}

function focusNextRow(currentIdx: number) {
  const nextIdx = currentIdx + 1
  if (inputRefs[nextIdx]) {
    inputRefs[nextIdx].focus()
    inputRefs[nextIdx].select()
  }
}

function getFlagBadgeClass(a: AnalyteItem) {
  switch (a.flag) {
    case 'CRITICAL_LOW':
    case 'CRITICAL_HIGH':
      return 'bg-red-100 text-red-800 border border-red-300 font-bold animate-pulse'
    case 'HIGH':
    case 'LOW':
      return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
    default:
      return 'bg-green-100 text-green-800 border border-green-200'
  }
}

function getInputHighlightClass(a: AnalyteItem) {
  switch (a.flag) {
    case 'CRITICAL_LOW':
    case 'CRITICAL_HIGH':
      return 'border-red-500 bg-red-50 text-red-900 ring-1 ring-red-500'
    case 'HIGH':
    case 'LOW':
      return 'border-yellow-500 bg-yellow-50 text-yellow-900'
    default:
      return 'border-gray-300 bg-white text-gray-900'
  }
}

function resetForm() {
  for (const a of analytes.value) {
    a.raw_value = ''
    a.notes = ''
    a.flag = 'NORMAL'
  }
  autosaveStatus.value = 'idle'
}

function saveDraft() {
  triggerAutosave()
}

function submitResults() {
  uiState.value = 'loading'
  setTimeout(() => {
    uiState.value = 'idle'
    autosaveStatus.value = 'saved'
  }, 500)
}

onMounted(() => {
  // Restore draft if saved
  try {
    const cached = localStorage.getItem('aarozi_draft_' + specimenInfo.order_no)
    if (cached) {
      const parsed = JSON.parse(cached)
      if (Array.isArray(parsed) && parsed.length > 0) {
        analytes.value = parsed
        evaluateFlags()
      }
    }
  } catch {}

  // Auto-focus first row
  if (inputRefs[0]) {
    inputRefs[0].focus()
  }
})

onUnmounted(() => {
  clearTimeout(autosaveTimer)
})
</script>

