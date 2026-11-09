<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'

const api = useApi()
const { success, warning, error: toastError } = useToast()

interface ParameterMapping {
  instrument_code: string
  system_code: string
  conversion?: number
  unit?: string
}

interface InstrumentItem {
  id: string
  name: string
  model: string
  department: string
  protocol: 'ASTM' | 'HL7' | 'POCT1A' | 'FILE'
  connection_type: 'tcp' | 'serial'
  host?: string
  port?: number
  serial_port?: string
  baud_rate?: number
  is_bidirectional: boolean
  status: 'active' | 'idle' | 'offline'
  mappings_count: number
  mappings: ParameterMapping[]
  last_sync: string
  created_at?: string
}

const loading = ref(true)
const instruments = ref<InstrumentItem[]>([])
const searchQuery = ref('')
const selectedDepartment = ref('All')
const selectedProtocol = ref('All')

// Add / Edit Modal State
const isModalOpen = ref(false)
const modalMode = ref<'create' | 'edit'>('create')
const activeInstrumentId = ref<string | null>(null)
const isSubmitting = ref(false)

const form = ref({
  name: '',
  model: '',
  department: 'Hematology',
  protocol: 'ASTM',
  connection_type: 'tcp',
  host: '192.168.1.101',
  port: 5100,
  serial_port: 'COM1',
  baud_rate: 9600,
  is_bidirectional: true,
  status: 'active',
})

// Parameter Mapping Modal
const isMappingModalOpen = ref(false)
const activeMappingInstrument = ref<InstrumentItem | null>(null)
const currentMappings = ref<ParameterMapping[]>([])
const isSavingMappings = ref(false)

// Connection Test Modal / State
const isTesting = ref(false)
const testResult = ref<any | null>(null)
const isTestModalOpen = ref(false)

async function loadInstruments() {
  loading.value = true
  try {
    const data: any = await api.get('/pathology/instruments')
    if (Array.isArray(data)) {
      instruments.value = data
    }
  } catch (err: any) {
    console.error('Failed to load instruments:', err)
    toastError('Error', 'Could not load instrument configurations from database.')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadInstruments()
})

const filteredInstruments = computed(() => {
  return instruments.value.filter((inst) => {
    const q = searchQuery.value.trim().toLowerCase()
    if (q) {
      const matchName = inst.name.toLowerCase().includes(q)
      const matchModel = (inst.model || '').toLowerCase().includes(q)
      const matchDept = inst.department.toLowerCase().includes(q)
      if (!matchName && !matchModel && !matchDept) return false
    }
    const matchDeptFilter = selectedDepartment.value === 'All' || inst.department.toLowerCase() === selectedDepartment.value.toLowerCase()
    const matchProtoFilter = selectedProtocol.value === 'All' || inst.protocol.toUpperCase() === selectedProtocol.value.toUpperCase()
    return matchDeptFilter && matchProtoFilter
  })
})

const stats = computed(() => {
  const total = instruments.value.length
  const active = instruments.value.filter(i => i.status === 'active').length
  const totalMappings = instruments.value.reduce((acc, curr) => acc + (curr.mappings_count || 0), 0)
  return { total, active, totalMappings }
})

function openCreateModal() {
  modalMode.value = 'create'
  activeInstrumentId.value = null
  form.value = {
    name: '',
    model: '',
    department: 'Hematology',
    protocol: 'ASTM',
    connection_type: 'tcp',
    host: '192.168.1.101',
    port: 5100,
    serial_port: 'COM1',
    baud_rate: 9600,
    is_bidirectional: true,
    status: 'active',
  }
  isModalOpen.value = true
}

function openEditModal(inst: InstrumentItem) {
  modalMode.value = 'edit'
  activeInstrumentId.value = inst.id
  form.value = {
    name: inst.name,
    model: inst.model || inst.name,
    department: inst.department,
    protocol: inst.protocol,
    connection_type: inst.connection_type,
    host: inst.host || '127.0.0.1',
    port: inst.port || 5100,
    serial_port: inst.serial_port || 'COM1',
    baud_rate: inst.baud_rate || 9600,
    is_bidirectional: inst.is_bidirectional,
    status: inst.status,
  }
  isModalOpen.value = true
}

async function handleSaveInstrument() {
  if (!form.value.name.trim()) {
    warning('Validation', 'Please provide a name for the laboratory instrument.')
    return
  }

  isSubmitting.value = true
  try {
    if (modalMode.value === 'create') {
      await api.post('/pathology/instruments', form.value)
      success('Instrument Registered', `${form.value.name} is now registered in the LIS hub.`)
    } else if (activeInstrumentId.value) {
      await api.put(`/pathology/instruments/${activeInstrumentId.value}`, form.value)
      success('Configuration Updated', `${form.value.name} configuration saved.`)
    }
    isModalOpen.value = false
    await loadInstruments()
  } catch (err: any) {
    toastError('Save Failed', err?.message || 'Could not save instrument settings.')
  } finally {
    isSubmitting.value = false
  }
}

async function handleDeleteInstrument(inst: InstrumentItem) {
  if (!confirm(`Are you sure you want to decommission ${inst.name}? Existing past results will remain intact in the database.`)) {
    return
  }
  try {
    await api.delete(`/pathology/instruments/${inst.id}`)
    success('Instrument Removed', `${inst.name} decommissioned successfully.`)
    await loadInstruments()
  } catch (err: any) {
    toastError('Delete Failed', err?.message || 'Could not delete instrument.')
  }
}

// Parameter Mapping Management
function openMappingModal(inst: InstrumentItem) {
  activeMappingInstrument.value = inst
  currentMappings.value = inst.mappings && inst.mappings.length > 0
    ? JSON.parse(JSON.stringify(inst.mappings))
    : []
  isMappingModalOpen.value = true
}

function addMappingRow() {
  currentMappings.value.push({
    instrument_code: '',
    system_code: '',
    conversion: 1.0,
    unit: '',
  })
}

function removeMappingRow(index: number) {
  currentMappings.value.splice(index, 1)
}

function applyPreset(presetType: 'mindray' | 'erba' | 'cobas') {
  if (presetType === 'mindray') {
    currentMappings.value = [
      { instrument_code: 'WBC', system_code: 'TLC_WBC', conversion: 1.0, unit: '/cumm' },
      { instrument_code: 'RBC', system_code: 'RBC', conversion: 1.0, unit: '10^6/uL' },
      { instrument_code: 'HGB', system_code: 'HB', conversion: 1.0, unit: 'g/dL' },
      { instrument_code: 'PLT', system_code: 'PLT', conversion: 1.0, unit: '10^3/uL' },
      { instrument_code: 'HCT', system_code: 'PCV', conversion: 1.0, unit: '%' },
      { instrument_code: 'MCV', system_code: 'MCV', conversion: 1.0, unit: 'fL' },
      { instrument_code: 'MCH', system_code: 'MCH', conversion: 1.0, unit: 'pg' },
      { instrument_code: 'MCHC', system_code: 'MCHC', conversion: 1.0, unit: 'g/dL' },
      { instrument_code: 'NEU%', system_code: 'NEUT_PCT', conversion: 1.0, unit: '%' },
      { instrument_code: 'LYM%', system_code: 'LYMPH_PCT', conversion: 1.0, unit: '%' },
    ]
  } else if (presetType === 'erba') {
    currentMappings.value = [
      { instrument_code: 'GLU', system_code: 'GLU_FAST', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'UREA', system_code: 'UREA', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'CREAT', system_code: 'CREAT', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'BILI_T', system_code: 'BILI_TOT', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'BILI_D', system_code: 'BILI_DIR', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'SGPT', system_code: 'SGPT_ALT', conversion: 1.0, unit: 'U/L' },
      { instrument_code: 'SGOT', system_code: 'SGOT_AST', conversion: 1.0, unit: 'U/L' },
      { instrument_code: 'ALP', system_code: 'ALP', conversion: 1.0, unit: 'U/L' },
      { instrument_code: 'PROT', system_code: 'PROT_TOT', conversion: 1.0, unit: 'g/dL' },
      { instrument_code: 'ALB', system_code: 'ALB', conversion: 1.0, unit: 'g/dL' },
    ]
  } else if (presetType === 'cobas') {
    currentMappings.value = [
      { instrument_code: 'GLUC3', system_code: 'GLU_FAST', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'CREJ2', system_code: 'CREAT', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'ALTL', system_code: 'SGPT_ALT', conversion: 1.0, unit: 'U/L' },
      { instrument_code: 'ASTL', system_code: 'SGOT_AST', conversion: 1.0, unit: 'U/L' },
      { instrument_code: 'CHOL2', system_code: 'CHOL_TOT', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'TRIGL', system_code: 'TRIG', conversion: 1.0, unit: 'mg/dL' },
      { instrument_code: 'HDLC4', system_code: 'HDL', conversion: 1.0, unit: 'mg/dL' },
    ]
  }
  success('Preset Applied', `Populated ${currentMappings.value.length} standard analyte mappings.`)
}

async function saveMappings() {
  if (!activeMappingInstrument.value) return
  isSavingMappings.value = true
  try {
    await api.put(`/pathology/instruments/${activeMappingInstrument.value.id}`, {
      mapping_json: JSON.stringify(currentMappings.value),
    })
    success('Mappings Saved', `Updated ${currentMappings.value.length} parameter mappings for ${activeMappingInstrument.value.name}.`)
    isMappingModalOpen.value = false
    await loadInstruments()
  } catch (err: any) {
    toastError('Save Failed', err?.message || 'Could not save mappings.')
  } finally {
    isSavingMappings.value = false
  }
}

// Test Connection Ping
async function testConnection(inst: InstrumentItem) {
  isTesting.value = true
  activeInstrumentId.value = inst.id
  try {
    const res: any = await api.post(`/pathology/instruments/${inst.id}/test-connection`)
    testResult.value = res
    isTestModalOpen.value = true
    success('Handshake Verified', `Communication established with ${inst.name}.`)
    await loadInstruments()
  } catch (err: any) {
    toastError('Handshake Failed', err?.message || 'No response received from instrument socket.')
  } finally {
    isTesting.value = false
  }
}
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto text-left">
    <!-- Top Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
      <div>
        <div class="flex items-center space-x-2.5">
          <h1 class="text-2xl font-bold text-slate-900 tracking-tight">Lab Instrument &amp; Analyzer Interfacing</h1>
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            ASTM / HL7 Hub Active
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Configure bi-directional communication, serial RS-232 &amp; TCP/IP sockets, and analyte parameter code mappings.
        </p>
      </div>

      <div class="flex items-center space-x-3">
        <button
          type="button"
          class="btn-primary"
          @click="openCreateModal"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Connect New Analyzer</span>
        </button>
      </div>
    </div>

    <!-- Quick Metrics -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
        <div class="text-xs font-medium text-slate-500 uppercase tracking-wider">Configured Instruments</div>
        <div class="text-2xl font-bold text-slate-900 mt-1 font-mono">{{ stats.total }}</div>
        <div class="text-[11px] text-slate-500 mt-0.5">Cell counters, chemistry &amp; immunoassay</div>
      </div>
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
        <div class="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Online Links</div>
        <div class="text-2xl font-bold text-emerald-600 mt-1 font-mono">{{ stats.active }} <span class="text-xs text-slate-400 font-sans font-normal">/ {{ stats.total }}</span></div>
        <div class="text-[11px] text-emerald-700 mt-0.5 font-medium flex items-center space-x-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Zero packet loss detected</span>
        </div>
      </div>
      <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
        <div class="text-xs font-medium text-slate-500 uppercase tracking-wider">Mapped Parameters</div>
        <div class="text-2xl font-bold text-sky-600 mt-1 font-mono">{{ stats.totalMappings }}</div>
        <div class="text-[11px] text-slate-500 mt-0.5">Analyte code to LIS investigation rules</div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div class="flex items-center flex-1 min-w-[240px]">
        <div class="relative flex-1">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 pointer-events-none">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search by instrument name, model or department..."
            class="input-faang w-full pl-9 pr-7 py-1.5 text-xs"
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

      <div class="flex items-center space-x-2 text-xs">
        <select
          v-model="selectedDepartment"
          class="select-faang input-faang text-xs text-slate-700 cursor-pointer font-medium"
        >
          <option value="All">All Departments</option>
          <option value="Hematology">Hematology</option>
          <option value="Biochemistry">Biochemistry</option>
          <option value="Immunoassay">Immunoassay</option>
          <option value="Clinical Pathology">Clinical Pathology</option>
        </select>

        <select
          v-model="selectedProtocol"
          class="select-faang input-faang text-xs text-slate-700 cursor-pointer font-medium"
        >
          <option value="All">All Protocols</option>
          <option value="ASTM">ASTM E1394</option>
          <option value="HL7">HL7 v2.5</option>
          <option value="POCT1A">POCT1-A</option>
        </select>
      </div>
    </div>

    <!-- Instrument Cards Grid -->
    <div v-if="loading" class="py-12 text-center text-slate-500">
      <span class="inline-block w-6 h-6 border-2 border-sky-600 border-t-transparent rounded-full animate-spin"></span>
      <p class="text-xs mt-2">Loading configured laboratory analyzers...</p>
    </div>

    <div v-else-if="filteredInstruments.length === 0" class="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500 shadow-2xs">
      <svg class="w-10 h-10 mx-auto text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
      <h3 class="text-sm font-bold text-slate-800 mt-3">No Laboratory Analyzers Found</h3>
      <p class="text-xs text-slate-500 mt-1">Connect your cell counters, clinical chemistry or immunoassay analyzers.</p>
      <button
        type="button"
        class="mt-4 px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-lg shadow-xs transition cursor-pointer"
        @click="openCreateModal"
      >
        Connect First Analyzer
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="inst in filteredInstruments"
        :key="inst.id"
        class="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs hover:shadow-xs transition flex flex-col justify-between"
      >
        <div>
          <!-- Card Top: Name & Status -->
          <div class="flex items-start justify-between gap-2">
            <div>
              <h3 class="text-base font-bold text-slate-900">{{ inst.name }}</h3>
              <p class="text-xs text-slate-500">{{ inst.model }}</p>
            </div>
            <span
              :class="[
                'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider',
                inst.status === 'active' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                (inst.status === 'idle' ? 'bg-sky-100 text-sky-800 border border-sky-200' : 'bg-slate-100 text-slate-600')
              ]"
            >
              <span v-if="inst.status === 'active'" class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse"></span>
              {{ inst.status }}
            </span>
          </div>

          <!-- Connection Specs -->
          <div class="mt-4 space-y-1.5 text-xs">
            <div class="flex items-center justify-between py-1 border-b border-slate-100">
              <span class="text-slate-500">Department</span>
              <span class="font-medium text-slate-800">{{ inst.department }}</span>
            </div>
            <div class="flex items-center justify-between py-1 border-b border-slate-100">
              <span class="text-slate-500">Protocol</span>
              <span class="font-mono font-bold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded text-[11px]">{{ inst.protocol }}</span>
            </div>
            <div class="flex items-center justify-between py-1 border-b border-slate-100">
              <span class="text-slate-500">Interface Type</span>
              <span class="font-mono text-slate-800 text-[11px]">
                <template v-if="inst.connection_type === 'tcp'">
                  TCP/IP &mdash; {{ inst.host }}:{{ inst.port }}
                </template>
                <template v-else>
                  Serial &mdash; {{ inst.serial_port }} ({{ inst.baud_rate }} bps)
                </template>
              </span>
            </div>
            <div class="flex items-center justify-between py-1 border-b border-slate-100">
              <span class="text-slate-500">Direction</span>
              <span class="font-medium text-slate-800">
                {{ inst.is_bidirectional ? 'Bi-Directional (Host Query)' : 'Uni-Directional (Ingest Only)' }}
              </span>
            </div>
            <div class="flex items-center justify-between py-1">
              <span class="text-slate-500">Mapped Analytes</span>
              <span class="font-semibold text-sky-700">{{ inst.mappings_count }} parameters</span>
            </div>
          </div>
        </div>

        <!-- Card Footer Actions -->
        <div class="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
          <div class="flex items-center space-x-1.5">
            <button
              type="button"
              class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-medium transition cursor-pointer"
              title="Configure parameter code mapping"
              @click="openMappingModal(inst)"
            >
              Mappings
            </button>
            <button
              type="button"
              class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-medium transition cursor-pointer"
              title="Edit socket/serial parameters"
              @click="openEditModal(inst)"
            >
              Edit
            </button>
            <button
              type="button"
              class="px-2 py-1.5 text-red-600 hover:bg-red-50 rounded-md text-xs transition cursor-pointer"
              title="Delete analyzer"
              @click="handleDeleteInstrument(inst)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>

          <button
            type="button"
            class="inline-flex items-center space-x-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold shadow-2xs transition cursor-pointer"
            :disabled="isTesting"
            @click="testConnection(inst)"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Test Ping</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Add / Edit Modal -->
    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 overflow-y-auto">
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-6 text-left space-y-5 my-8">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-bold text-slate-900">
            {{ modalMode === 'create' ? 'Connect New Laboratory Analyzer' : 'Edit Analyzer Configuration' }}
          </h2>
          <button type="button" class="text-slate-400 hover:text-slate-600 cursor-pointer" @click="isModalOpen = false">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div class="space-y-4 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Instrument Display Name *</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="e.g. Sysmex XN-1000, Mindray BC-5000"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-medium focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Model / Vendor</label>
              <input
                v-model="form.model"
                type="text"
                placeholder="e.g. XN-1000 (Sysmex)"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Department</label>
              <select
                v-model="form.department"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-medium focus:ring-1 focus:ring-sky-500"
              >
                <option value="Hematology">Hematology</option>
                <option value="Biochemistry">Biochemistry</option>
                <option value="Immunoassay">Immunoassay</option>
                <option value="Coagulation">Coagulation</option>
                <option value="Clinical Pathology">Clinical Pathology</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Protocol Standard</label>
              <select
                v-model="form.protocol"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-medium focus:ring-1 focus:ring-sky-500"
              >
                <option value="ASTM">ASTM E1381 / E1394</option>
                <option value="HL7">HL7 v2.5 (MLLP)</option>
                <option value="POCT1A">POCT1-A Standard</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Interface Medium</label>
              <select
                v-model="form.connection_type"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-medium focus:ring-1 focus:ring-sky-500"
              >
                <option value="tcp">TCP/IP Network Socket</option>
                <option value="serial">RS-232 Serial COM Port</option>
              </select>
            </div>
          </div>

          <!-- Conditional TCP/IP settings -->
          <div v-if="form.connection_type === 'tcp'" class="grid grid-cols-3 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div class="col-span-2">
              <label class="block font-semibold text-slate-700 mb-1">IP Host / LAN Address</label>
              <input
                v-model="form.host"
                type="text"
                placeholder="192.168.1.101"
                class="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-mono text-slate-800"
              />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Socket Port</label>
              <input
                v-model.number="form.port"
                type="number"
                placeholder="5100"
                class="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-mono text-slate-800"
              />
            </div>
          </div>

          <!-- Conditional Serial COM settings -->
          <div v-else class="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Serial COM Port</label>
              <input
                v-model="form.serial_port"
                type="text"
                placeholder="COM1 or /dev/ttyUSB0"
                class="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-mono text-slate-800"
              />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Baud Rate (bps)</label>
              <select
                v-model.number="form.baud_rate"
                class="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-mono text-slate-800"
              >
                <option :value="4800">4800 bps</option>
                <option :value="9600">9600 bps (Standard)</option>
                <option :value="19200">19200 bps</option>
                <option :value="38400">38400 bps</option>
                <option :value="115200">115200 bps</option>
              </select>
            </div>
          </div>

          <div class="flex items-center space-x-2 pt-1">
            <input
              id="bidirectional"
              v-model="form.is_bidirectional"
              type="checkbox"
              class="w-4 h-4 text-sky-600 rounded border-slate-300 focus:ring-sky-500 cursor-pointer"
            />
            <label for="bidirectional" class="font-medium text-slate-700 cursor-pointer">
              Enable Bi-Directional Host Query (Analyzer automatically scans barcode &amp; fetches order)
            </label>
          </div>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-4 border-t border-slate-100">
          <button
            type="button"
            class="px-4 py-2 border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold rounded-lg transition cursor-pointer"
            @click="isModalOpen = false"
          >
            Cancel
          </button>
          <button
            type="button"
            class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-xs transition cursor-pointer"
            :disabled="isSubmitting"
            @click="handleSaveInstrument"
          >
            <span v-if="isSubmitting">Saving...</span>
            <span v-else>{{ modalMode === 'create' ? 'Save &amp; Connect' : 'Update Configuration' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Parameter Mapping Drawer / Modal -->
    <div v-if="isMappingModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 overflow-y-auto">
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-3xl w-full p-6 text-left space-y-4 my-8">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 class="text-base font-bold text-slate-900">
              Parameter Code Mapping &mdash; {{ activeMappingInstrument?.name }}
            </h2>
            <p class="text-xs text-slate-500">
              Translate machine-specific output codes to standardized LIS test investigations.
            </p>
          </div>
          <button type="button" class="text-slate-400 hover:text-slate-600 cursor-pointer" @click="isMappingModalOpen = false">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <!-- Presets Bar -->
        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
          <span class="font-semibold text-slate-700">Quick Populate Presets:</span>
          <div class="flex items-center space-x-2">
            <button
              type="button"
              class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 rounded font-medium shadow-2xs transition cursor-pointer"
              @click="applyPreset('mindray')"
            >
              Mindray BC Series (CBC)
            </button>
            <button
              type="button"
              class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 rounded font-medium shadow-2xs transition cursor-pointer"
              @click="applyPreset('erba')"
            >
              Erba Chem 5X (LFT/KFT)
            </button>
            <button
              type="button"
              class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 rounded font-medium shadow-2xs transition cursor-pointer"
              @click="applyPreset('cobas')"
            >
              Roche Cobas c311
            </button>
          </div>
        </div>

        <!-- Mapping Table -->
        <div class="max-h-[360px] overflow-y-auto border border-slate-200 rounded-xl">
          <table class="min-w-full divide-y divide-slate-200 text-xs">
            <thead class="bg-slate-50 text-slate-600 font-semibold uppercase">
              <tr>
                <th class="px-3 py-2 text-left">Machine Analyte Code</th>
                <th class="px-3 py-2 text-left">LIS Parameter Code</th>
                <th class="px-3 py-2 text-center w-24">Multiplier</th>
                <th class="px-3 py-2 text-left w-24">Unit</th>
                <th class="px-3 py-2 text-center w-12">Del</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-if="currentMappings.length === 0">
                <td colspan="5" class="px-4 py-8 text-center text-slate-400">
                  No parameters mapped yet. Click "Add Mapping Row" or choose a manufacturer preset above.
                </td>
              </tr>
              <tr v-for="(m, idx) in currentMappings" :key="idx" class="hover:bg-slate-50/60">
                <td class="px-3 py-1.5">
                  <input
                    v-model="m.instrument_code"
                    type="text"
                    placeholder="e.g. WBC, GLUC3"
                    class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded font-mono font-medium text-slate-900"
                  />
                </td>
                <td class="px-3 py-1.5">
                  <input
                    v-model="m.system_code"
                    type="text"
                    placeholder="e.g. TLC_WBC, GLU_FAST"
                    class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded font-mono font-semibold text-blue-700"
                  />
                </td>
                <td class="px-3 py-1.5 text-center">
                  <input
                    v-model.number="m.conversion"
                    type="number"
                    step="0.01"
                    class="w-20 px-2 py-1 bg-slate-50 border border-slate-200 rounded font-mono text-center text-slate-900"
                  />
                </td>
                <td class="px-3 py-1.5">
                  <input
                    v-model="m.unit"
                    type="text"
                    placeholder="mg/dL, g/dL"
                    class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded text-slate-700"
                  />
                </td>
                <td class="px-3 py-1.5 text-center">
                  <button
                    type="button"
                    class="p-1 text-slate-400 hover:text-red-600 transition cursor-pointer"
                    @click="removeMappingRow(idx)"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex items-center justify-between pt-2">
          <button
            type="button"
            class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-lg transition cursor-pointer"
            @click="addMappingRow"
          >
            + Add Mapping Row
          </button>

          <div class="flex items-center space-x-2">
            <button
              type="button"
              class="px-4 py-2 border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold rounded-lg transition cursor-pointer"
              @click="isMappingModalOpen = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-lg shadow-xs transition cursor-pointer"
              :disabled="isSavingMappings"
              @click="saveMappings"
            >
              <span v-if="isSavingMappings">Saving...</span>
              <span v-else>Save {{ currentMappings.length }} Mappings</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Handshake Test Diagnostic Modal -->
    <div v-if="isTestModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full p-6 text-left space-y-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
          </div>
          <div>
            <h3 class="text-sm font-bold text-slate-900">Analyzer Handshake Verified</h3>
            <p class="text-xs text-slate-500 font-mono">{{ testResult?.name }} ({{ testResult?.protocol }})</p>
          </div>
        </div>

        <div class="bg-slate-900 text-emerald-400 p-3.5 rounded-xl text-xs font-mono space-y-1">
          <div>&gt; CONNECT {{ testResult?.target }} ... SUCCESS</div>
          <div>&gt; PROTOCOL: {{ testResult?.protocol }} E1381 / E1394</div>
          <div>&gt; STATUS: {{ testResult?.handshake_status }}</div>
          <div>&gt; ROUND-TRIP LATENCY: {{ testResult?.latency_ms }} ms</div>
          <div>&gt; MONOTONIC TIMESTAMP: {{ testResult?.timestamp }}</div>
        </div>

        <div class="flex justify-end pt-2">
          <button
            type="button"
            class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-xs transition cursor-pointer"
            @click="isTestModalOpen = false"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

