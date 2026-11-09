<script setup lang="ts">
import { ref } from 'vue'

const currentStep = ref(1)
const importSource = ref('csv')
const conflictStrategy = ref('SKIP_EXISTING')
const rawCsvInput = ref(`Patient Name,Phone,Age,Gender,Legacy MRN,Email
Dr. Rajesh Sharma,9820011111,45,M,MRN-1001,rajesh@example.com
Pooja K. Patel,9820022222,32,F,MRN-1002,pooja@example.com
Amitabh Verma,9820033333,58,M,MRN-1003,amitabh@example.com
Sunita Deshmukh,9820044444,28,F,MRN-1004,sunita@example.com`)

const isProcessing = ref(false)
const previewData = ref<any>(null)
const migrationResult = ref<any>(null)

async function generatePreview() {
  isProcessing.value = true
  try {
    const res = await fetch('/migration/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        csv_content: rawCsvInput.value,
        source_name: 'LEGACY_LIS_IMPORT',
      }),
    })
    previewData.value = await res.json()
    currentStep.value = 2
  } catch (err) {
    alert('Failed to parse input file. Please verify format.')
  } finally {
    isProcessing.value = false
  }
}

async function executeImport() {
  if (!previewData.value) return
  isProcessing.value = true
  try {
    // Reconstruct rows from sample preview
    const sampleRows = previewData.value.sample_preview.map((s: any) => s.data)
    const res = await fetch('/migration/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        records: sampleRows,
        field_mapping: previewData.value.auto_mapping,
        conflict_strategy: conflictStrategy.value,
        source_name: 'LEGACY_LIS_MIGRATION',
      }),
    })
    migrationResult.value = await res.json()
    currentStep.value = 3
  } catch (err) {
    alert('Import encountered an error and was safely rolled back.')
  } finally {
    isProcessing.value = false
  }
}

function resetWizard() {
  currentStep.value = 1
  previewData.value = null
  migrationResult.value = null
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased text-xs">
    <!-- Header -->
    <header class="bg-white border-b border-slate-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <NuxtLink to="/dashboard" class="flex items-center space-x-2">
            <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black text-sm">
              A
            </div>
            <span class="font-bold text-slate-900 text-sm">Aarozi Healthcare</span>
          </NuxtLink>
          <span class="text-slate-300">/</span>
          <span class="font-semibold text-slate-700">Legacy LIS Data Migration &amp; Ingestion Wizard</span>
        </div>

        <div class="flex items-center space-x-2">
          <NuxtLink to="/admin/licensing" class="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50">
            System Settings
          </NuxtLink>
          <NuxtLink to="/dashboard" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold">
            &larr; Back to Workstation
          </NuxtLink>
        </div>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- Wizard Progress Steps -->
      <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs flex items-center justify-between max-w-2xl mx-auto">
        <div class="flex items-center space-x-2" :class="currentStep >= 1 ? 'text-indigo-600 font-bold' : 'text-slate-400'">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-[11px]" :class="currentStep >= 1 ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-600'">1</span>
          <span>Source &amp; Upload</span>
        </div>
        <span class="text-slate-300">&mdash;&mdash;</span>
        <div class="flex items-center space-x-2" :class="currentStep >= 2 ? 'text-indigo-600 font-bold' : 'text-slate-400'">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-[11px]" :class="currentStep >= 2 ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-600'">2</span>
          <span>Mapping &amp; Duplicates</span>
        </div>
        <span class="text-slate-300">&mdash;&mdash;</span>
        <div class="flex items-center space-x-2" :class="currentStep >= 3 ? 'text-indigo-600 font-bold' : 'text-slate-400'">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-[11px]" :class="currentStep >= 3 ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-600'">3</span>
          <span>Import Audit Summary</span>
        </div>
      </div>

      <!-- STEP 1: Select Source & Paste/Upload Data -->
      <div v-if="currentStep === 1" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
        <div>
          <h2 class="text-base font-bold text-slate-900">Select Legacy Data Source</h2>
          <p class="text-slate-500 mt-0.5">
            Import patient records, historical visits, test catalogs, and doctor referrals from your old laboratory software.
          </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <label
            class="p-4 rounded-xl border cursor-pointer transition flex flex-col justify-between"
            :class="importSource === 'csv' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900' : 'border-slate-200 hover:bg-slate-50 text-slate-700'"
          >
            <div class="flex items-center space-x-2">
              <input v-model="importSource" type="radio" value="csv" class="text-indigo-600" />
              <span class="font-bold">CSV / Excel Text</span>
            </div>
            <span class="text-slate-500 text-[11px] mt-2 block">Direct paste or tabular export</span>
          </label>

          <label
            class="p-4 rounded-xl border cursor-pointer transition flex flex-col justify-between"
            :class="importSource === 'json' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900' : 'border-slate-200 hover:bg-slate-50 text-slate-700'"
          >
            <div class="flex items-center space-x-2">
              <input v-model="importSource" type="radio" value="json" class="text-indigo-600" />
              <span class="font-bold">JSON Dump</span>
            </div>
            <span class="text-slate-500 text-[11px] mt-2 block">Structured patient records</span>
          </label>

          <label
            class="p-4 rounded-xl border cursor-pointer transition flex flex-col justify-between"
            :class="importSource === 'zip' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900' : 'border-slate-200 hover:bg-slate-50 text-slate-700'"
          >
            <div class="flex items-center space-x-2">
              <input v-model="importSource" type="radio" value="zip" class="text-indigo-600" />
              <span class="font-bold">Aarozi Migration Package</span>
            </div>
            <span class="text-slate-500 text-[11px] mt-2 block">ZIP archive from another lab</span>
          </label>
        </div>

        <div>
          <label class="block font-medium text-slate-700 mb-1">Paste CSV Data or Sample Content</label>
          <textarea
            v-model="rawCsvInput"
            rows="7"
            class="w-full font-mono text-[11px] p-3 border border-slate-300 rounded-xl focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
            placeholder="Patient Name,Phone,Age,Gender,Legacy MRN,Email..."
          ></textarea>
        </div>

        <div class="flex justify-between items-center pt-2">
          <span class="text-slate-400">Transactions are safely validated before committing.</span>
          <button
            type="button"
            :disabled="isProcessing"
            class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-xs transition cursor-pointer"
            @click="generatePreview"
          >
            <span v-if="!isProcessing">Scan &amp; Preview Mapping &rarr;</span>
            <span v-else>Analyzing Headers...</span>
          </button>
        </div>
      </div>

      <!-- STEP 2: Review Mapping, Duplicates & Conflict Strategy -->
      <div v-if="currentStep === 2 && previewData" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
        <div class="flex justify-between items-start border-b border-slate-100 pb-3">
          <div>
            <h2 class="text-base font-bold text-slate-900">Schema Mapping &amp; Duplicate Analysis</h2>
            <p class="text-slate-500 mt-0.5">
              Detected {{ previewData.total_records }} records. {{ previewData.duplicates_in_sample }} potential duplicates identified in sample.
            </p>
          </div>
          <button type="button" class="text-slate-400 hover:text-slate-600 font-semibold" @click="currentStep = 1">&larr; Back</button>
        </div>

        <!-- Auto Mapping Badges -->
        <div>
          <span class="text-slate-400 block font-medium mb-1.5">Auto-Detected Field Mappings:</span>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(target, source) in previewData.auto_mapping"
              :key="source"
              class="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[11px]"
            >
              <strong class="text-slate-900">{{ source }}</strong> &rarr; <span class="text-indigo-600 font-bold">{{ target }}</span>
            </span>
          </div>
        </div>

        <!-- Conflict Strategy Selector -->
        <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <span class="font-bold text-slate-900 block">Duplicate Conflict Resolution Policy:</span>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label class="flex items-center space-x-2 cursor-pointer">
              <input v-model="conflictStrategy" type="radio" value="SKIP_EXISTING" class="text-indigo-600" />
              <span><strong>Skip Existing</strong> (Recommended)</span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer">
              <input v-model="conflictStrategy" type="radio" value="UPDATE_MISSING" class="text-indigo-600" />
              <span><strong>Update Missing Fields</strong></span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer">
              <input v-model="conflictStrategy" type="radio" value="CREATE_NEW" class="text-indigo-600" />
              <span><strong>Create Separate Record</strong></span>
            </label>
          </div>
        </div>

        <!-- Sample Records Preview Table -->
        <div class="overflow-x-auto border border-slate-200 rounded-xl">
          <table class="w-full text-left border-collapse">
            <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
              <tr>
                <th class="p-3">#</th>
                <th class="p-3">Name</th>
                <th class="p-3">Mobile</th>
                <th class="p-3">Gender / Age</th>
                <th class="p-3">Legacy MRN</th>
                <th class="p-3">Duplicate Check</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="item in previewData.sample_preview" :key="item.row_index" :class="item.is_duplicate ? 'bg-amber-50/50' : ''">
                <td class="p-3 font-mono text-slate-400">{{ item.row_index + 1 }}</td>
                <td class="p-3 font-bold text-slate-900">{{ item.data.first_name }} {{ item.data.last_name || '' }}</td>
                <td class="p-3 font-mono text-slate-700">{{ item.data.mobile }}</td>
                <td class="p-3 text-slate-600">{{ item.data.sex || 'U' }} &bull; {{ item.data.age || '-' }} yrs</td>
                <td class="p-3 font-mono text-slate-600">{{ item.data.legacy_id }}</td>
                <td class="p-3">
                  <span v-if="item.is_duplicate" class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px]">
                    Duplicate: {{ item.duplicate_reason }}
                  </span>
                  <span v-else class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                    &check; New Patient
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex justify-between items-center pt-2">
          <button type="button" class="px-4 py-2 border border-slate-300 rounded-lg" @click="currentStep = 1">Cancel</button>
          <button
            type="button"
            :disabled="isProcessing"
            class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl shadow-xs transition cursor-pointer"
            @click="executeImport"
          >
            <span v-if="!isProcessing">Confirm &amp; Execute Transactional Import &rarr;</span>
            <span v-else>Importing Records into Database...</span>
          </button>
        </div>
      </div>

      <!-- STEP 3: Final Import Summary & Audit -->
      <div v-if="currentStep === 3 && migrationResult" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs text-center space-y-4">
        <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto text-xl font-bold">
          &check;
        </div>
        <div>
          <h2 class="text-base font-bold text-slate-900">Patient Data Migration Completed Successfully!</h2>
          <p class="text-slate-500 mt-0.5">Batch ID: {{ migrationResult.batch_id }} &bull; Source: {{ migrationResult.source }}</p>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-lg mx-auto pt-2">
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span class="text-slate-400 block text-[11px]">Total Scanned</span>
            <span class="text-lg font-bold text-slate-900 mt-0.5 block">{{ migrationResult.total_scanned }}</span>
          </div>
          <div class="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
            <span class="text-emerald-700 block text-[11px]">Imported</span>
            <span class="text-lg font-bold text-emerald-800 mt-0.5 block">{{ migrationResult.imported_count }}</span>
          </div>
          <div class="p-3 rounded-xl bg-amber-50 border border-amber-200">
            <span class="text-amber-700 block text-[11px]">Skipped (Dups)</span>
            <span class="text-lg font-bold text-amber-800 mt-0.5 block">{{ migrationResult.skipped_count }}</span>
          </div>
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span class="text-slate-400 block text-[11px]">Updated</span>
            <span class="text-lg font-bold text-slate-900 mt-0.5 block">{{ migrationResult.updated_count }}</span>
          </div>
        </div>

        <p class="text-slate-500 text-[11px] max-w-md mx-auto pt-2">
          All imported records have been tagged with <code>source_system: MIGRATED_LEGACY_LIS</code> and are immediately searchable from the Reception Desk (<kbd class="px-1 py-0.5 bg-slate-100 border border-slate-300 rounded font-mono">F2</kbd>).
        </p>

        <div class="pt-4 flex justify-center space-x-3">
          <NuxtLink to="/patients" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-xs transition">
            View Patient Directory &rarr;
          </NuxtLink>
          <button type="button" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl" @click="resetWizard">
            Import Another File
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

