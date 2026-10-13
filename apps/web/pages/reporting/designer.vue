<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between border-b border-gray-200 pb-4">
      <div>
        <div class="flex items-center space-x-2 text-xs text-gray-500 mb-1">
          <NuxtLink to="/dashboard" class="hover:underline">Dashboard</NuxtLink>
          <span>/</span>
          <NuxtLink to="/reporting" class="hover:underline">Reporting</NuxtLink>
          <span>/</span>
          <span class="text-gray-900 font-medium">Report Designer</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Structured Report Designer</h1>
        <p class="text-sm text-gray-500">Visual schema-driven template builder (Alt+S save, Alt+P preview, Esc reset)</p>
      </div>

      <div class="flex items-center space-x-3">
        <button
          type="button"
          class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          @click="togglePreview"
        >
          {{ isPreviewMode ? 'Back to Editor (Alt+P)' : 'Live Preview (Alt+P)' }}
        </button>
        <button
          type="button"
          class="px-5 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm"
          :disabled="uiState === 'loading'"
          @click="saveTemplate"
        >
          Publish Template (Alt+S)
        </button>
      </div>
    </div>

    <div v-if="uiState === 'error'" class="p-4 rounded-md bg-red-50 border border-red-200">
      <h3 class="text-sm font-medium text-red-800">Designer Error</h3>
      <p class="mt-1 text-sm text-red-700">{{ errorMessage }}</p>
    </div>

    <div v-if="uiState === 'permission_denied'" class="p-8 text-center bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 class="text-base font-semibold text-gray-900">Permission Denied</h3>
      <p class="mt-1 text-sm text-gray-500">You do not have permission ('report.template.manage') to design report templates.</p>
    </div>

    <div v-else-if="uiState === 'loading'" class="p-12 text-center bg-white rounded-lg border border-gray-200 shadow-sm">
      <div class="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-2 text-sm text-gray-500">Saving and compiling report template schema...</p>
    </div>

    <div v-else-if="uiState === 'empty'" class="p-8 text-center bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 class="text-base font-semibold text-gray-900">No Sections in Template</h3>
      <p class="mt-1 text-sm text-gray-500">Add section primitives from the palette to build the template.</p>
    </div>
    <div
      v-else
      class="grid grid-cols-1 lg:grid-cols-12 gap-6"
      @keydown.alt.s.prevent="saveTemplate"
      @keydown.alt.p.prevent="togglePreview"
      @keydown.esc="resetDesigner"
    >
      <div class="lg:col-span-3 bg-white p-4 rounded-lg border border-gray-200 shadow-sm space-y-4">
        <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">Primitives Palette</h3>
        <div class="space-y-2">
          <button
            v-for="p in palette"
            :key="p.type"
            type="button"
            class="w-full text-left p-2.5 rounded border border-gray-200 hover:bg-blue-50 text-xs font-medium text-gray-800 flex items-center justify-between"
            @click="addPrimitive(p.type)"
          >
            <span>{{ p.label }}</span>
            <span class="text-blue-500 font-bold">+</span>
          </button>
        </div>
      </div>

      <div class="lg:col-span-9 bg-white p-6 rounded-lg border border-gray-200 shadow-sm space-y-4">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="text-sm font-bold text-gray-800">Canvas Layout ({{ template.sections.length }} primitives)</h3>
          <span class="text-xs text-gray-400">Page: {{ template.page.size }}</span>
        </div>

        <div class="space-y-3">
          <div
            v-for="(sec, idx) in template.sections"
            :key="sec.id"
            class="p-4 rounded-md border border-gray-200 bg-gray-50 flex items-center justify-between"
          >
            <div>
              <div class="text-xs font-bold text-gray-800 uppercase">{{ sec.type.replace('_', ' ') }}</div>
              <div class="text-xs text-gray-500 font-mono">id: {{ sec.id }}</div>
            </div>

            <div class="flex items-center space-x-2">
              <button type="button" class="px-2 py-1 text-xs border rounded" :disabled="idx === 0" @click="moveSection(idx, -1)">&uarr;</button>
              <button type="button" class="px-2 py-1 text-xs border rounded" :disabled="idx === template.sections.length - 1" @click="moveSection(idx, 1)">&darr;</button>
              <button type="button" class="px-2 py-1 text-xs text-red-600 border border-red-200 rounded" @click="removeSection(idx)">Remove</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>


<script setup lang="ts">
import { ref, reactive } from 'vue'

type UIState = 'idle' | 'loading' | 'empty' | 'error' | 'permission_denied'

const uiState = ref<UIState>('idle')
const isPreviewMode = ref(false)
const errorMessage = ref('')

const palette = [
  { type: 'patient_header', label: 'Patient Header' },
  { type: 'test_table', label: 'Test Table' },
  { type: 'result_summary', label: 'Result Summary' },
  { type: 'reference_range_legend', label: 'Range Legend' },
  { type: 'logo', label: 'Logo / Header Graphic' },
  { type: 'signature_stamp', label: 'Signature Stamp' },
  { type: 'qr_code', label: 'QR Code' },
  { type: 'barcode', label: 'Barcode' },
  { type: 'graph', label: 'Graph / Trend' },
  { type: 'footer', label: 'Footer Disclaimer' },
]

const template = reactive({
  code: 'PATH-STD',
  name: 'Standard Diagnostic Report',
  category: 'pathology',
  page: { size: 'A4', orientation: 'portrait' },
  sections: [
    { id: 'sec_logo', type: 'logo' },
    { id: 'sec_header', type: 'patient_header' },
    { id: 'sec_table', type: 'test_table' },
    { id: 'sec_sig', type: 'signature_stamp' },
    { id: 'sec_qr', type: 'qr_code' },
    { id: 'sec_footer', type: 'footer' },
  ],
})

function addPrimitive(type: string) {
  const newId = `sec_${type}_${Date.now()}`
  template.sections.push({ id: newId, type })
  if (uiState.value === 'empty') {
    uiState.value = 'idle'
  }
}

function removeSection(idx: number) {
  template.sections.splice(idx, 1)
  if (template.sections.length === 0) {
    uiState.value = 'empty'
  }
}

function moveSection(idx: number, delta: number) {
  const target = idx + delta
  if (target < 0 || target >= template.sections.length) return
  const item = template.sections.splice(idx, 1)[0]
  if (item) {
    template.sections.splice(target, 0, item)
  }
}

function togglePreview() {
  isPreviewMode.value = !isPreviewMode.value
}

function resetDesigner() {
  template.sections = []
  uiState.value = 'empty'
}

function saveTemplate() {
  uiState.value = 'loading'
  setTimeout(() => {
    uiState.value = 'idle'
  }, 400)
}
</script>

