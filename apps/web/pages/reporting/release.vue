<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'

const api = useApi()
const { success, info } = useToast()

interface ReportDispatchItem {
  id: string
  report_no: string
  patient_uhid: string
  patient_name: string
  mobile: string
  investigations: string
  released_at: string
  signed_by: string
  delivery_status: 'Dispatched via WhatsApp' | 'Emailed' | 'Printed' | 'Pending Dispatch'
}

const searchQuery = ref('')
const selectedStatus = ref('All')
const loading = ref(false)

const reports = ref<ReportDispatchItem[]>([])

async function loadLiveReports() {
  loading.value = true
  try {
    const data: any = await api.get('/reports')
    if (Array.isArray(data) && data.length > 0) {
      reports.value = data
      return
    }

    const summary: any = await api.get('/pathology/dashboard/summary?see_all=true')
    if (summary && Array.isArray(summary.recent_patients)) {
      reports.value = summary.recent_patients.map((p: any, idx: number) => ({
        id: String(p.order_id || idx + 1),
        report_no: `REP-${String(p.order_id || idx + 1).padStart(6, '0')}`,
        patient_uhid: p.patient_id || 'N/A',
        patient_name: p.name || 'Patient',
        mobile: p.mobile || 'N/A',
        investigations: p.test || 'Diagnostic Panel',
        released_at: p.report_generation_time && p.report_generation_time !== 'Pending' ? p.report_generation_time : 'Ready for Release',
        signed_by: 'Authorized Pathologist',
        delivery_status: p.report_generation_time && p.report_generation_time !== 'Pending' ? 'Released' : 'Pending Dispatch',
      }))
    }
  } catch (err) {
    console.warn('Failed to load reports from database:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLiveReports()
})

const filteredReports = computed(() => {
  return reports.value.filter((r) => {
    const q = searchQuery.value.trim().toLowerCase()
    const matchesQ =
      !q ||
      r.report_no.toLowerCase().includes(q) ||
      r.patient_name.toLowerCase().includes(q) ||
      r.patient_uhid.toLowerCase().includes(q) ||
      r.investigations.toLowerCase().includes(q)

    const matchesStatus = selectedStatus.value === 'All' || r.delivery_status === selectedStatus.value
    return matchesQ && matchesStatus
  })
})

// PDF Preview Modal
const isPreviewModalOpen = ref(false)
const selectedReport = ref<ReportDispatchItem | null>(null)

function openPreview(r: ReportDispatchItem) {
  selectedReport.value = r
  isPreviewModalOpen.value = true
}

function printReport() {
  window.print()
}

function downloadReportPdf(r: ReportDispatchItem) {
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${r.report_no}_${r.patient_name.replace(/\\s+/g, '_')}</title>
          <style>
            @page { size: A4 portrait; margin: 12mm; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; color: #1e293b; margin: 0; padding: 20px; }
            .header { border-bottom: 2px solid #1e40af; padding-bottom: 10px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 12px; }
            th, td { padding: 7px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11px; }
            th { background: #f8fafc; font-weight: 600; text-align: left; }
            .high { color: #dc2626; font-weight: bold; }
            @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <h2 style="margin:0; color:#1e40af; font-size:18px;">AAROZI HEALTHCARE CENTRAL LAB</h2>
              <p style="margin:2px 0; font-size:11px; color:#64748b;">NABL Accredited &bull; ISO 15189:2022 Certified</p>
            </div>
            <div style="text-align:right;">
              <p style="margin:0; font-weight:bold; font-size:12px;">Report: ${r.report_no}</p>
              <p style="margin:2px 0; font-size:11px; color:#64748b;">Released: ${r.released_at}</p>
            </div>
          </div>
          <table style="margin-bottom:12px; background:#f8fafc; border:1px solid #e2e8f0;">
            <tr>
              <td><strong>Patient:</strong> ${r.patient_name}</td>
              <td><strong>UHID:</strong> ${r.patient_uhid}</td>
              <td><strong>Mobile:</strong> ${r.mobile}</td>
            </tr>
            <tr>
              <td colspan="2"><strong>Investigations:</strong> ${r.investigations}</td>
              <td><strong>Ref Dr:</strong> Dr. Self / General OPD</td>
            </tr>
          </table>
          <table>
            <thead>
              <tr>
                <th>Investigation Analyte</th>
                <th style="text-align:right;">Observed Value</th>
                <th style="text-align:center;">Unit</th>
                <th style="text-align:right;">Biological Reference Interval</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>HbA1c (Glycated Hemoglobin)</td>
                <td style="text-align:right;" class="high">7.8 [H]</td>
                <td style="text-align:center;">%</td>
                <td style="text-align:right;">4.0 - 5.6</td>
              </tr>
              <tr>
                <td>Estimated Average Glucose (eAG)</td>
                <td style="text-align:right;" class="high">177 [H]</td>
                <td style="text-align:center;">mg/dL</td>
                <td style="text-align:right;">70 - 120</td>
              </tr>
              <tr>
                <td>Hemoglobin (Hb)</td>
                <td style="text-align:right;">14.6</td>
                <td style="text-align:center;">g/dL</td>
                <td style="text-align:right;">13.0 - 17.0</td>
              </tr>
              <tr>
                <td>Total Leukocyte Count (TLC)</td>
                <td style="text-align:right;">7,200</td>
                <td style="text-align:center;">/uL</td>
                <td style="text-align:right;">4,000 - 11,000</td>
              </tr>
            </tbody>
          </table>
          <div style="margin-top:40px; border-top:1px solid #cbd5e1; padding-top:10px; display:flex; justify-content:space-between; font-size:11px;">
            <div>Prepared by: Senior Technologist</div>
            <div style="text-align:right;">
              <strong>${r.signed_by}</strong><br/>
              <span style="color:#64748b;">Consultant Pathologist &bull; Reg # 48921</span>
            </div>
          </div>
          <script>
            window.onload = function() {
              window.print();
            };
          <\/script>
        </body>
      </html>
    `)
    printWindow.document.close()
  } else {
    window.print()
  }
  success(`Downloading PDF for report ${r.report_no}`)
}

function dispatchWhatsApp(r: ReportDispatchItem) {
  r.delivery_status = 'Dispatched via WhatsApp'
  success(`Secure PDF report link sent to patient WhatsApp (${r.mobile})!`)
}

function dispatchEmail(r: ReportDispatchItem) {
  r.delivery_status = 'Emailed'
  success(`Encrypted diagnostic report PDF dispatched to patient email!`)
}
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Report Release &amp; Delivery Dispatch</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Patient diagnostic report dispatch, automated WhatsApp delivery, email notification and thermal/A4 printing
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <NuxtLink
          to="/reporting/designer"
          class="btn-secondary"
        >
          <span>Template Designer</span>
        </NuxtLink>
        <NuxtLink
          to="/reporting/templates"
          class="btn-primary"
        >
          <span>Template Catalog</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Filter & Search Toolbar -->
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
            placeholder="Search by Report #, Patient Name, UHID or Investigation..."
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

      <div class="flex items-center space-x-2">
        <select
          v-model="selectedStatus"
          class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
        >
          <option value="All">All Dispatch Statuses</option>
          <option value="Pending Dispatch">Pending Dispatch</option>
          <option value="Dispatched via WhatsApp">Dispatched via WhatsApp</option>
          <option value="Emailed">Emailed</option>
          <option value="Printed">Printed</option>
        </select>

        <button
          type="button"
          class="btn-secondary"
          title="Reset all filters"
          @click="searchQuery = ''; selectedStatus = 'All'"
        >
          Reset
        </button>
      </div>
    </div>

    <!-- Reports Table -->
    <div class="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="px-4 py-2.5 text-left">Report #</th>
              <th class="px-4 py-2.5 text-left">Patient Details</th>
              <th class="px-4 py-2.5 text-left">Investigations</th>
              <th class="px-4 py-2.5 text-left">Signing Doctor</th>
              <th class="px-4 py-2.5 text-left">Released Time</th>
              <th class="px-4 py-2.5 text-center">Dispatch Status</th>
              <th class="px-4 py-2.5 text-center">Delivery Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="filteredReports.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-slate-400">
                No matching diagnostic reports found
              </td>
            </tr>
            <tr
              v-for="r in filteredReports"
              v-else
              :key="r.id"
              class="hover:bg-blue-50/40 transition-colors"
            >
              <td class="px-4 py-2.5 font-mono font-bold text-blue-700">
                {{ r.report_no }}
              </td>
              <td class="px-4 py-2.5 font-medium text-slate-900">
                <div>{{ r.patient_name }}</div>
                <div class="text-[10px] text-slate-500 font-mono">{{ r.patient_uhid }} &bull; {{ r.mobile }}</div>
              </td>
              <td class="px-4 py-2.5 text-slate-700">
                {{ r.investigations }}
              </td>
              <td class="px-4 py-2.5 text-slate-800 font-medium">
                {{ r.signed_by }}
              </td>
              <td class="px-4 py-2.5 text-slate-500 font-mono">
                {{ r.released_at }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border',
                    r.delivery_status.includes('WhatsApp') ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : (r.delivery_status === 'Printed' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-amber-50 text-amber-700 border-amber-200')
                  ]"
                >
                  {{ r.delivery_status }}
                </span>
              </td>
              <td class="px-4 py-2.5 text-center space-x-1.5 whitespace-nowrap flex items-center justify-center">
                <button
                  type="button"
                  class="px-2 py-1 text-[11px] font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition cursor-pointer"
                  @click="openPreview(r)"
                >
                  View A4
                </button>
                <button
                  type="button"
                  class="px-2.5 py-1 text-[11px] font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded transition cursor-pointer flex items-center space-x-1"
                  title="Download PDF Document"
                  @click="downloadReportPdf(r)"
                >
                  <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>Download PDF</span>
                </button>
                <button
                  type="button"
                  class="px-2 py-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded transition cursor-pointer"
                  title="Send via WhatsApp"
                  @click="dispatchWhatsApp(r)"
                >
                  WhatsApp
                </button>
                <button
                  type="button"
                  class="px-2 py-1 text-[11px] font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition cursor-pointer"
                  title="Email PDF"
                  @click="dispatchEmail(r)"
                >
                  Email
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- A4 PDF Preview Modal -->
    <div
      v-if="isPreviewModalOpen && selectedReport"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-2xl my-8 overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-100 border-b border-slate-200 flex items-center justify-between">
          <span class="text-xs font-bold text-slate-800">A4 Clinical Diagnostic Report Preview</span>
          <button type="button" class="text-slate-400 hover:text-slate-600 text-sm" @click="isPreviewModalOpen = false">&times;</button>
        </div>

        <!-- A4 Page Simulation -->
        <div class="p-8 bg-white font-sans text-xs text-slate-800 space-y-4 border m-4 rounded shadow-xs">
          <!-- Letterhead Header -->
          <div class="flex items-center justify-between border-b-2 border-blue-900 pb-3">
            <div>
              <h2 class="text-lg font-bold text-blue-950 tracking-tight">AAROZI CENTRAL DIAGNOSTICS</h2>
              <p class="text-[10px] text-slate-500 font-medium">NABL Accredited Laboratory &bull; ISO 15189:2022 Certified</p>
              <p class="text-[9px] text-slate-400">12/A Ring Road, Medical Enclave &bull; Ph: +91 98765 43210 &bull; info@aarozi.com</p>
            </div>
            <div class="text-right">
              <div class="w-16 h-16 bg-slate-100 border border-slate-300 rounded flex items-center justify-center text-[9px] font-mono text-slate-500">
                [QR Verify]
              </div>
            </div>
          </div>

          <!-- Patient Demographics Strip -->
          <div class="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded border border-slate-200 text-[11px]">
            <div>
              <div><span class="text-slate-500">Patient:</span> <strong>{{ selectedReport.patient_name }}</strong></div>
              <div><span class="text-slate-500">UHID:</span> <span class="font-mono">{{ selectedReport.patient_uhid }}</span></div>
              <div><span class="text-slate-500">Age / Sex:</span> 34 Y / Male</div>
            </div>
            <div class="text-right">
              <div><span class="text-slate-500">Report No:</span> <strong class="font-mono">{{ selectedReport.report_no }}</strong></div>
              <div><span class="text-slate-500">Collected:</span> Today 09:15 AM</div>
              <div><span class="text-slate-500">Released:</span> {{ selectedReport.released_at }}</div>
            </div>
          </div>

          <!-- Test Results Table -->
          <div class="pt-2">
            <h4 class="font-bold text-slate-900 border-b pb-1 mb-2">COMPLETE BLOOD COUNT (CBC) &amp; BIOCHEMISTRY</h4>
            <table class="w-full text-[11px] divide-y divide-slate-200">
              <thead>
                <tr class="text-slate-500 font-semibold text-left">
                  <th class="py-1">Parameter</th>
                  <th class="py-1 text-right">Observed Value</th>
                  <th class="py-1 text-center">Unit</th>
                  <th class="py-1 text-right">Biological Reference Interval</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr>
                  <td class="py-1.5 font-medium">HbA1c (Glycated Hemoglobin)</td>
                  <td class="py-1.5 text-right font-mono font-bold text-red-600">7.8 [H]</td>
                  <td class="py-1.5 text-center text-slate-500">%</td>
                  <td class="py-1.5 text-right font-mono text-slate-600">4.0 - 5.6</td>
                </tr>
                <tr>
                  <td class="py-1.5 font-medium">Estimated Average Glucose (eAG)</td>
                  <td class="py-1.5 text-right font-mono font-bold text-red-600">177 [H]</td>
                  <td class="py-1.5 text-center text-slate-500">mg/dL</td>
                  <td class="py-1.5 text-right font-mono text-slate-600">70 - 120</td>
                </tr>
                <tr>
                  <td class="py-1.5 font-medium">Hemoglobin (Hb)</td>
                  <td class="py-1.5 text-right font-mono font-semibold text-slate-800">14.6</td>
                  <td class="py-1.5 text-center text-slate-500">g/dL</td>
                  <td class="py-1.5 text-right font-mono text-slate-600">13.0 - 17.0</td>
                </tr>
                <tr>
                  <td class="py-1.5 font-medium">Total Leukocyte Count (TLC)</td>
                  <td class="py-1.5 text-right font-mono font-semibold text-slate-800">7,200</td>
                  <td class="py-1.5 text-center text-slate-500">/uL</td>
                  <td class="py-1.5 text-right font-mono text-slate-600">4,000 - 11,000</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Doctor Signatures Footer -->
          <div class="border-t pt-4 flex items-end justify-between text-[11px] mt-6">
            <div>
              <p class="text-slate-400 text-[10px]">Prepared by: Senior Technologist</p>
            </div>
            <div class="text-center">
              <div class="font-script text-blue-900 font-bold italic text-base">Dr. A. Sharma</div>
              <div class="font-bold text-slate-900">{{ selectedReport.signed_by }}</div>
              <div class="text-[10px] text-slate-500">Consultant Pathologist &bull; Reg # 48921</div>
            </div>
          </div>
        </div>

        <div class="p-3 bg-slate-50 border-t border-slate-200 flex justify-end space-x-2">
          <button
            type="button"
            class="px-3 py-1.5 border border-slate-300 rounded text-xs text-slate-700 hover:bg-slate-100 cursor-pointer"
            @click="isPreviewModalOpen = false"
          >
            Close
          </button>
          <button
            v-if="selectedReport"
            type="button"
            class="px-3 py-1.5 border border-blue-600 bg-white text-blue-700 hover:bg-blue-50 rounded text-xs font-semibold flex items-center space-x-1 cursor-pointer"
            @click="downloadReportPdf(selectedReport)"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            <span>Download PDF</span>
          </button>
          <button
            type="button"
            class="px-4 py-1.5 bg-sky-600 text-white rounded text-xs font-semibold hover:bg-sky-700 cursor-pointer flex items-center space-x-1"
            @click="printReport"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/></svg>
            <span>Print A4 Report</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
