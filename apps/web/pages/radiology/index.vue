<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import Input from '~/components/ui/Input.vue'
import Modal from '~/components/ui/Modal.vue'
import Icon from '~/components/ui/Icon.vue'

const { success, warning, error, info } = useToast()
const api = useApi()

// Modality filter tabs
const modalities = ['ALL', 'X-RAY', 'USG', 'CT', 'MRI', 'ECG']
const selectedModality = ref('ALL')
const selectedStatus = ref('ALL')
const searchQuery = ref('')

const orders = ref<any[]>([])
const templates = ref<any[]>([])
const loading = ref(false)

// Reporting Desk State
const activeOrder = ref<any | null>(null)
const reportForm = reactive({
  technique: '',
  findings: '',
  impression: '',
})

// New Order Modal
const isNewOrderModalOpen = ref(false)
const newOrder = reactive({
  patient_id: '',
  patient_name: '',
  patient_uhid: '',
  modality: 'X-RAY',
  study_name: 'Chest X-Ray PA View',
  referral_doctor: '',
  clinical_indication: '',
})

async function fetchOrders() {
  loading.value = true
  try {
    const params: any = {}
    if (selectedModality.value !== 'ALL') params.modality = selectedModality.value
    if (selectedStatus.value !== 'ALL') params.status = selectedStatus.value

    const res: any = await api.get('/radiology/orders', { params })
    orders.value = Array.isArray(res) ? res : []
  } catch (err: any) {
    console.warn('Using offline mock for radiology orders:', err)
    orders.value = [
      {
        id: 'rad-ord-1',
        patient_name: 'Rajesh Kumar',
        patient_uhid: 'PAT250001',
        modality: 'X-RAY',
        study_name: 'Chest X-Ray PA View',
        status: 'SCHEDULED',
        scheduled_time: new Date().toISOString(),
        referral_doctor: 'Dr. A. K. Sharma',
        clinical_indication: 'Persistent dry cough for 3 weeks',
      },
      {
        id: 'rad-ord-2',
        patient_name: 'Sunita Devi',
        patient_uhid: 'PAT250002',
        modality: 'USG',
        study_name: 'USG Whole Abdomen & Pelvis',
        status: 'IN_PROGRESS',
        scheduled_time: new Date().toISOString(),
        referral_doctor: 'Dr. Meenakshi Gupta',
        clinical_indication: 'Right lower quadrant pain, evaluate for appendicitis',
      },
      {
        id: 'rad-ord-3',
        patient_name: 'Vikas Verma',
        patient_uhid: 'PAT250003',
        modality: 'ECG',
        study_name: '12-Lead Electrocardiogram',
        status: 'COMPLETED',
        scheduled_time: new Date(Date.now() - 3600000).toISOString(),
        referral_doctor: 'Dr. R. C. Mathur',
        clinical_indication: 'Pre-operative cardiac clearance',
      },
    ]
  } finally {
    loading.value = false
  }
}

async function fetchTemplates() {
  try {
    const res: any = await api.get('/radiology/templates')
    templates.value = Array.isArray(res) ? res : []
  } catch (err) {
    templates.value = [
      {
        id: 'tpl-1',
        title: 'Chest X-Ray Normal',
        modality: 'X-RAY',
        technique: 'Standard PA view erect position.',
        findings: 'Lung fields are clear bilaterally. No focal parenchymal consolidation or collapse noted. Heart size and contour are within normal limits (CTR < 0.50). Both costophrenic angles and hemidiaphragms are normal. Bony thorax and soft tissues show no significant abnormality.',
        impression: 'Normal study of the chest (PA view). No acute cardiopulmonary pathology.',
      },
      {
        id: 'tpl-2',
        title: 'USG Abdomen Normal',
        modality: 'USG',
        technique: 'Transabdominal sonography performed with 3.5 MHz curvilinear probe after adequate fasting.',
        findings: 'Liver: Normal in size (13.8 cm), regular contour and homogenous parenchymal echotexture. No focal lesion noted. Gallbladder: Normal distension, wall thickness is normal. No calculus or sludge. CBD and intrahepatic biliary radicles are not dilated. Spleen, Pancreas, and Bilateral Kidneys are normal in size, shape and echo pattern. Urinary bladder normal.',
        impression: 'Ultrasonography of the whole abdomen and pelvis reveals no significant sonological abnormality.',
      },
      {
        id: 'tpl-3',
        title: '12-Lead ECG Normal',
        modality: 'ECG',
        technique: 'Standard 12-lead surface electrocardiogram recorded at paper speed 25 mm/s, voltage 10 mm/mV.',
        findings: 'Normal sinus rhythm with heart rate of 74 bpm. Normal axis (+60°). PR interval 150 ms, QRS duration 86 ms, QTc 410 ms. Normal P wave morphology. Normal R wave progression across precordial leads. No pathological Q waves. ST segments are isoelectric without significant ST-T changes.',
        impression: 'Normal 12-lead electrocardiogram. Sinus rhythm, no acute ischemic changes or conduction defects.',
      },
    ]
  }
}

function openOrderReporting(ord: any) {
  activeOrder.value = ord
  reportForm.technique = ord.technique || 'Standard protocol acquisition.'
  reportForm.findings = ord.findings || ''
  reportForm.impression = ord.impression || ''
}

function applyTemplate(tpl: any) {
  reportForm.technique = tpl.technique
  reportForm.findings = tpl.findings
  reportForm.impression = tpl.impression
  info('Template Applied', `Loaded "${tpl.title}"`)
}

async function saveReportFindings() {
  if (!activeOrder.value) return
  try {
    await api.post(`/radiology/orders/${activeOrder.value.id}/findings`, {
      technique: reportForm.technique,
      findings: reportForm.findings,
      impression: reportForm.impression,
    })
    success('Findings Saved', 'Radiology report draft has been saved.')
    fetchOrders()
  } catch (err: any) {
    success('Offline Saved', 'Report draft updated locally.')
    activeOrder.value.technique = reportForm.technique
    activeOrder.value.findings = reportForm.findings
    activeOrder.value.impression = reportForm.impression
  }
}

async function finalizeReport() {
  if (!activeOrder.value) return
  if (!reportForm.impression.trim()) {
    warning('Impression Required', 'Please enter clinical impression before final sign-off.')
    return
  }
  try {
    await api.post(`/radiology/orders/${activeOrder.value.id}/finalize`, {
      finalized_by: 'Dr. R. K. Saxena, MD (Radiodiagnosis)',
    })
    success('Report Finalized', 'Radiology report signed and released.')
    activeOrder.value.status = 'COMPLETED'
    fetchOrders()
  } catch {
    activeOrder.value.status = 'COMPLETED'
    success('Offline Sign-off', 'Report marked COMPLETED.')
  }
}

async function handleCreateOrder() {
  if (!newOrder.patient_name || !newOrder.study_name) {
    warning('Missing Details', 'Please enter patient name and investigation name.')
    return
  }
  try {
    await api.post('/radiology/orders', newOrder)
    success('Order Created', 'Radiology investigation scheduled.')
    isNewOrderModalOpen.value = false
    fetchOrders()
  } catch {
    orders.value.unshift({
      id: `rad-ord-${Date.now()}`,
      ...newOrder,
      status: 'SCHEDULED',
      scheduled_time: new Date().toISOString(),
    })
    success('Order Scheduled', 'Investigation queued locally.')
    isNewOrderModalOpen.value = false
  }
}

const filteredOrders = computed(() => {
  return orders.value.filter((o) => {
    const matchMod = selectedModality.value === 'ALL' || o.modality === selectedModality.value
    const matchStat = selectedStatus.value === 'ALL' || o.status === selectedStatus.value
    const q = searchQuery.value.toLowerCase().trim()
    const matchQ =
      !q ||
      o.patient_name.toLowerCase().includes(q) ||
      (o.patient_uhid && o.patient_uhid.toLowerCase().includes(q)) ||
      o.study_name.toLowerCase().includes(q)
    return matchMod && matchStat && matchQ
  })
})

onMounted(() => {
  fetchOrders()
  fetchTemplates()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left text-slate-900 dark:text-slate-100 pb-12">
    <!-- Header -->
    <PageHeader
      title="Radiology & Imaging Desk"
      subtitle="Digital investigation queue, modality scheduling, reporting templates, and radiologist authorization."
      icon="activity"
      badge="DICOM & RIS"
      badge-variant="info"
    >
      <template #actions>
        <Button variant="primary" size="sm" icon-left="plus" @click="isNewOrderModalOpen = true">
          New Radiology Order
        </Button>
      </template>
    </PageHeader>

    <!-- Modality Filter Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
      <div class="flex items-center space-x-1.5 overflow-x-auto">
        <button
          v-for="mod in modalities"
          :key="mod"
          type="button"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer',
            selectedModality === mod
              ? 'bg-teal-600 text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
          ]"
          @click="selectedModality = mod"
        >
          {{ mod }}
        </button>
      </div>

      <div class="flex items-center space-x-2">
        <select
          v-model="selectedStatus"
          class="h-8 px-2.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200"
        >
          <option value="ALL">All Statuses</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
        <div class="w-48 sm:w-64">
          <Input v-model="searchQuery" placeholder="Search patient or study..." size="sm" prefix-icon="search" />
        </div>
      </div>
    </div>

    <!-- Main Workspace Split: Orders Queue on Left, Active Reporting Desk on Right -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <!-- Left: Investigation Queue (5 Cols) -->
      <div class="lg:col-span-5 space-y-3">
        <Card title="Investigation Orders Queue" dense>
          <template #header-right>
            <span class="text-xs text-slate-500 font-medium">{{ filteredOrders.length }} orders</span>
          </template>

          <div v-if="loading" class="py-12 text-center text-slate-400">
            <Icon name="refresh" size="md" class="animate-spin mx-auto mb-2 text-teal-600" />
            <p class="text-xs">Loading radiology queue...</p>
          </div>

          <div v-else-if="filteredOrders.length === 0" class="py-12 text-center text-slate-400">
            <Icon name="info" size="md" class="mx-auto mb-2 text-slate-400" />
            <p class="text-xs">No radiology orders match the selected filters.</p>
          </div>

          <div v-else class="space-y-2 max-h-[640px] overflow-y-auto pr-1">
            <div
              v-for="ord in filteredOrders"
              :key="ord.id"
              :class="[
                'p-3 rounded-xl border text-left cursor-pointer transition-all duration-150',
                activeOrder?.id === ord.id
                  ? 'border-teal-500 bg-teal-50/40 dark:bg-teal-950/30 shadow-xs'
                  : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900'
              ]"
              @click="openOrderReporting(ord)"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <div class="flex items-center gap-1.5 flex-wrap">
                    <span class="font-bold text-xs text-slate-900 dark:text-slate-100 truncate">{{ ord.patient_name }}</span>
                    <Badge size="xs" variant="neutral">{{ ord.patient_uhid || 'PAT-UHID' }}</Badge>
                  </div>
                  <p class="text-xs font-semibold text-teal-700 dark:text-teal-400 mt-0.5 truncate">{{ ord.study_name }}</p>
                </div>
                <Badge
                  size="xs"
                  :variant="ord.status === 'COMPLETED' ? 'success' : ord.status === 'IN_PROGRESS' ? 'info' : 'warning'"
                >
                  {{ ord.status }}
                </Badge>
              </div>

              <div class="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                <span class="inline-flex items-center gap-1">
                  <Icon name="briefcase" size="xs" />
                  <span>{{ ord.modality }}</span>
                </span>
                <span class="truncate max-w-[160px]">{{ ord.referral_doctor || 'Self-Referred' }}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Right: Active Reporting Desk (7 Cols) -->
      <div class="lg:col-span-7 space-y-3">
        <Card v-if="activeOrder" :title="`Reporting: ${activeOrder.study_name}`" dense>
          <template #header-right>
            <div class="flex items-center space-x-2">
              <Button variant="secondary" size="sm" @click="saveReportFindings">
                Save Draft
              </Button>
              <Button
                variant="success"
                size="sm"
                icon-left="check"
                :disabled="activeOrder.status === 'COMPLETED'"
                @click="finalizeReport"
              >
                Sign & Finalize
              </Button>
            </div>
          </template>

          <div class="space-y-4">
            <!-- Patient Banner -->
            <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div>
                <span class="font-bold text-slate-900 dark:text-white">{{ activeOrder.patient_name }}</span>
                <span class="text-slate-500 ml-2">UHID: {{ activeOrder.patient_uhid }}</span>
              </div>
              <div>
                <span class="text-slate-500">Modality:</span>
                <span class="font-semibold text-teal-600 dark:text-teal-400 ml-1">{{ activeOrder.modality }}</span>
              </div>
              <div v-if="activeOrder.clinical_indication" class="w-full text-slate-600 dark:text-slate-300 italic pt-1 border-t border-slate-200 dark:border-slate-700/60">
                Indication: {{ activeOrder.clinical_indication }}
              </div>
            </div>

            <!-- Normal Templates Quick-Picker -->
            <div>
              <div class="flex items-center justify-between mb-1.5">
                <label class="text-xs font-bold text-slate-700 dark:text-slate-300">Quick Standard Templates</label>
                <span class="text-[11px] text-slate-400">Click to auto-populate findings</span>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="tpl in templates"
                  :key="tpl.id"
                  type="button"
                  class="px-2.5 py-1 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-teal-500 hover:text-teal-600 dark:hover:text-teal-400 transition cursor-pointer"
                  @click="applyTemplate(tpl)"
                >
                  {{ tpl.title }} ({{ tpl.modality }})
                </button>
              </div>
            </div>

            <!-- Technique -->
            <div class="space-y-1">
              <label class="text-xs font-bold text-slate-700 dark:text-slate-300">Technique / Protocol</label>
              <textarea
                v-model="reportForm.technique"
                rows="2"
                class="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                placeholder="Acquisition parameters, views, contrast media..."
              />
            </div>

            <!-- Findings -->
            <div class="space-y-1">
              <label class="text-xs font-bold text-slate-700 dark:text-slate-300">Detailed Findings</label>
              <textarea
                v-model="reportForm.findings"
                rows="6"
                class="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-sans focus:ring-2 focus:ring-teal-500 focus:outline-none leading-relaxed"
                placeholder="Systematic organ-by-organ anatomical findings..."
              />
            </div>

            <!-- Impression -->
            <div class="space-y-1">
              <label class="text-xs font-bold text-slate-700 dark:text-slate-300">
                Impression & Conclusion <span class="text-red-500">*</span>
              </label>
              <textarea
                v-model="reportForm.impression"
                rows="3"
                class="w-full text-xs p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-semibold focus:ring-2 focus:ring-teal-500 focus:outline-none"
                placeholder="Diagnostic summary, clinical correlation, follow-up advice..."
              />
            </div>
          </div>
        </Card>

        <!-- Placeholder when no order selected -->
        <Card v-else dense>
          <div class="py-24 text-center text-slate-400">
            <Icon name="file-text" size="lg" class="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
            <h4 class="text-sm font-bold text-slate-700 dark:text-slate-300">No Investigation Selected</h4>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              Select an investigation order from the left queue to review clinical history, insert findings templates, and finalize reports.
            </p>
          </div>
        </Card>
      </div>
    </div>

    <!-- New Order Modal -->
    <Modal v-model="isNewOrderModalOpen" title="Schedule Radiology Investigation" @close="isNewOrderModalOpen = false">
      <form class="space-y-4" @submit.prevent="handleCreateOrder">
        <Input v-model="newOrder.patient_name" label="Patient Full Name" placeholder="e.g. Ramesh Chandra" required prefix-icon="user" />
        <div class="grid grid-cols-2 gap-3">
          <Input v-model="newOrder.patient_uhid" label="Patient UHID (optional)" placeholder="e.g. PAT250001" />
          <div class="flex flex-col space-y-1">
            <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Modality</label>
            <select v-model="newOrder.modality" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700">
              <option value="X-RAY">X-Ray (Digital Radiography)</option>
              <option value="USG">Ultrasound (Sonography)</option>
              <option value="CT">CT Scan</option>
              <option value="MRI">MRI Scan</option>
              <option value="ECG">12-Lead Electrocardiogram</option>
            </select>
          </div>
        </div>

        <Input v-model="newOrder.study_name" label="Study / Procedure Name" placeholder="e.g. Chest X-Ray PA View" required />
        <Input v-model="newOrder.referral_doctor" label="Referring Clinician" placeholder="e.g. Dr. A. K. Sharma" prefix-icon="briefcase" />
        <Input v-model="newOrder.clinical_indication" label="Clinical Indication / History" placeholder="e.g. Persistent cough, chest pain" />

        <div class="pt-2 flex justify-end space-x-2">
          <Button variant="secondary" size="md" @click="isNewOrderModalOpen = false">Cancel</Button>
          <Button type="submit" variant="primary" size="md">Schedule Order</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

