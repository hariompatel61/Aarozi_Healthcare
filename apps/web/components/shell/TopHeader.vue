<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useBranch } from '~/composables/useBranch'
import { useToast } from '~/composables/useToast'
import Modal from '~/components/ui/Modal.vue'

interface Props {
  collapsed?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'toggle-mobile'): void
  (e: 'open-command-palette'): void
}>()

const router = useRouter()
const { branches, selectedBranch, switchBranch, currentBranch } = useBranch()
const { success, info } = useToast()
const api = useApi()

function onBranchChange(event: Event) {
  const target = event.target as HTMLSelectElement
  if (target && target.value) {
    switchBranch(target.value)
  }
}

// -------------------------------------------------------------
// Clinical Alerts & Notification Bell State
// -------------------------------------------------------------
const isAlertsOpen = ref(false)
const alertsContainerRef = ref<HTMLElement | null>(null)

export interface ClinicalAlert {
  id: string
  title: string
  patient_name: string
  uhid: string
  sample_id: string
  phone: string
  test: string
  detail: string
  badge: string
  badgeClass: string
  time: string
  read: boolean
  canWhatsApp: boolean
}

const alerts = ref<ClinicalAlert[]>([])

async function loadClinicalAlerts() {
  try {
    const res: any = await api.get('/pathology/samples?limit=20')
    if (Array.isArray(res)) {
      const flagged = res.filter((s: any) => s.flag_type === 'Critical Panic' || s.flag_type === 'Abnormal')
      alerts.value = flagged.map((s: any, idx: number) => ({
        id: s.id || `alt-${idx}`,
        title: s.flag_type === 'Critical Panic' ? 'Panic Critical Value Alert' : 'Abnormal Result Flag',
        patient_name: s.patient_name || 'Patient',
        uhid: s.patient_uhid || 'N/A',
        sample_id: s.sample_id || 'N/A',
        phone: s.mobile || '+91 98765 00000',
        test: s.test_name || 'Investigation',
        detail: s.key_findings || 'Abnormal findings flagged by laboratory analyzer.',
        badge: s.flag_type === 'Critical Panic' ? 'CRITICAL' : 'ABNORMAL',
        badgeClass: s.flag_type === 'Critical Panic' ? 'bg-red-100 text-red-700 border-red-200' : 'bg-amber-100 text-amber-700 border-amber-200',
        time: s.collected_at ? `${s.collected_at}` : 'Recently',
        read: false,
        canWhatsApp: true,
      }))
    }
  } catch (err) {
    console.warn('Failed to load clinical alerts from database:', err)
  }
}

const unreadCount = computed(() => alerts.value.filter((a) => !a.read).length)

function markAllRead() {
  alerts.value.forEach((a) => {
    a.read = true
  })
  info('Alerts Cleared', 'All clinical alerts acknowledged.')
}

// -------------------------------------------------------------
// WhatsApp Report Dispatch Modal State
// -------------------------------------------------------------
const isWhatsAppModalOpen = ref(false)
const activeDispatchAlert = ref<ClinicalAlert | null>(null)
const recipientPhone = ref('+91 98765 43210')
const recipientName = ref('Aarav Sharma')
const reportSummary = ref('HbA1c (HPLC) - Sample #SMP250001')
const isSending = ref(false)

function openQuickWhatsAppDispatch(alert?: ClinicalAlert) {
  if (alert) {
    activeDispatchAlert.value = alert
    recipientName.value = alert.patient_name
    recipientPhone.value = alert.phone
    reportSummary.value = `${alert.test} (Sample #${alert.sample_id})`
  } else {
    activeDispatchAlert.value = null
    recipientName.value = 'Aarav Sharma'
    recipientPhone.value = '+91 98765 43210'
    reportSummary.value = 'HbA1c (HPLC) - Sample #SMP250001'
  }
  isAlertsOpen.value = false
  isWhatsAppModalOpen.value = true
}

const whatsappMessagePreview = computed(() => {
  const sample = activeDispatchAlert.value?.sample_id || 'SMP250001'
  return `🏥 *Aarozi Healthcare Central Diagnostic Lab*\n\nDear *${recipientName.value}*,\nYour verified lab report for *${reportSummary.value}* is ready.\n\n📄 *Official PDF Report:* https://aarozi.health/reports/verify/${sample}-QR\n\n_NABL Accredited & ISO 15189:2022 Certified._`
})

function sendViaWhatsAppWeb() {
  const cleanPhone = recipientPhone.value.replace(/[^0-9]/g, '')
  const text = encodeURIComponent(whatsappMessagePreview.value)
  window.open(`https://wa.me/${cleanPhone}?text=${text}`, '_blank')
  if (activeDispatchAlert.value) {
    activeDispatchAlert.value.read = true
  }
  success('WhatsApp Web Opened', `Direct chat initiated for ${recipientPhone.value}`)
  isWhatsAppModalOpen.value = false
}

async function sendViaWhatsAppApi() {
  isSending.value = true
  try {
    const reportId = activeDispatchAlert.value?.id || 'rep-default'
    await api.post(`/reports/${reportId}/deliver`, {
      channel: 'whatsapp',
      recipient: recipientPhone.value,
      metadata: { patient_name: recipientName.value, summary: reportSummary.value },
    })
    if (activeDispatchAlert.value) {
      activeDispatchAlert.value.read = true
    }
    success(
      'WhatsApp Report Dispatched!',
      `Diagnostic report notification dispatched to ${recipientPhone.value}.`
    )
    isWhatsAppModalOpen.value = false
  } catch (err: any) {
    // If backend direct dispatch fails, fall back gracefully to direct WhatsApp Web
    sendViaWhatsAppWeb()
  } finally {
    isSending.value = false
  }
}

function navigateToAlert(alert: ClinicalAlert) {
  alert.read = true
  isAlertsOpen.value = false
  router.push(`/pathology/results?sample_id=${alert.sample_id}`)
}

function handleClickOutside(e: MouseEvent) {
  if (alertsContainerRef.value && !alertsContainerRef.value.contains(e.target as Node)) {
    isAlertsOpen.value = false
  }
}

onMounted(() => {
  if (typeof document !== 'undefined') {
    document.addEventListener('click', handleClickOutside)
  }
  loadClinicalAlerts()
})

onUnmounted(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('click', handleClickOutside)
  }
})
</script>

<template>
  <header class="h-14 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between z-30 sticky top-0 shadow-2xs">
    <!-- Left: Mobile Toggle & Clinical Status -->
    <div class="flex items-center space-x-3">
      <!-- Mobile Hamburger -->
      <button
        type="button"
        class="lg:hidden p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-md cursor-pointer"
        aria-label="Toggle navigation drawer"
        @click="emit('toggle-mobile')"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Clean Clinical Breadcrumb / Workspace Indicator -->
      <div class="hidden sm:flex items-center space-x-2 text-xs">
        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
          NABL Accredited LIS
        </span>
        <span class="text-slate-300">&bull;</span>
        <span class="text-slate-600 font-semibold text-[11px]">{{ currentBranch?.name }}</span>
        <span class="text-slate-400 text-[10px]">({{ currentBranch?.badge }})</span>
      </div>
    </div>

    <!-- Center: Global Quick Command Search Bar (Ctrl+K) -->
    <div class="hidden md:flex items-center">
      <button
        type="button"
        @click="emit('open-command-palette')"
        class="flex items-center justify-between w-64 lg:w-80 px-3 py-1.5 text-xs text-slate-500 bg-slate-50/80 hover:bg-white border border-slate-200 hover:border-slate-300 rounded-lg cursor-pointer transition shadow-2xs group"
        title="Search patients, invoices, tests, instruments (Ctrl+K)"
      >
        <div class="flex items-center gap-2">
          <svg class="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span class="text-slate-500 group-hover:text-slate-800 font-normal">Search patients, tests...</span>
        </div>
        <kbd class="px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-white border border-slate-200 rounded shadow-2xs">Ctrl K</kbd>
      </button>
    </div>

    <!-- Right Controls: Branch Selector, Notification Bell, User Avatar -->
    <div class="flex items-center space-x-2.5 sm:space-x-3">
      <!-- Branch Selector Pill (Mapped to useBranch Composable) -->
      <div
        class="flex items-center text-xs text-slate-700 bg-white hover:bg-slate-50 transition rounded-lg border border-slate-200 shadow-2xs overflow-hidden"
        title="Select Active Operating Laboratory / Collection Center"
      >
        <span class="pl-2.5 pr-1 text-teal-600 shrink-0">
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </span>
        <select
          :value="selectedBranch"
          class="select-faang bg-transparent font-semibold text-slate-800 focus:outline-none cursor-pointer py-1.5 pl-1 text-xs"
          @change="onBranchChange"
        >
          <option v-for="b in branches" :key="b.id" :value="b.name">
            {{ b.name }} ({{ b.badge }})
          </option>
        </select>
      </div>

      <!-- Notification Bell with Alerts Dropdown & WhatsApp Dispatch Trigger -->
      <div ref="alertsContainerRef" class="relative">
        <button
          type="button"
          class="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition cursor-pointer"
          :class="{ 'bg-slate-100 text-slate-900': isAlertsOpen }"
          title="Clinical Alerts &amp; Notifications"
          aria-label="Clinical Alerts"
          @click="isAlertsOpen = !isAlertsOpen"
        >
          <svg class="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>

          <!-- Red badge with unread count -->
          <span
            v-if="unreadCount > 0"
            class="absolute top-1 right-1 h-3.5 min-w-3.5 px-0.5 rounded-full bg-red-500 text-[8px] font-bold text-white flex items-center justify-center animate-pulse"
          >
            {{ unreadCount }}
          </span>
        </button>

        <!-- Dropdown Popover Panel -->
        <div
          v-if="isAlertsOpen"
          class="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden text-left"
        >
          <!-- Popover Header -->
          <div class="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-slate-900">Clinical Alerts &amp; Notifications</span>
              <span
                v-if="unreadCount > 0"
                class="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-red-100 text-red-700"
              >
                {{ unreadCount }} new
              </span>
            </div>
            <button
              v-if="unreadCount > 0"
              type="button"
              class="btn-ghost text-[11px] font-semibold text-teal-600 hover:text-teal-800"
              @click="markAllRead"
            >
              Mark all read
            </button>
          </div>

          <!-- Quick WhatsApp Dispatch Bar -->
          <div class="p-2.5 bg-emerald-50/70 border-b border-emerald-100 flex items-center justify-between text-xs">
            <div class="flex items-center space-x-1.5 text-emerald-900 font-semibold text-[11px]">
              <svg class="w-4 h-4 text-emerald-600" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.031 2C6.495 2 2 6.495 2 12.031c0 1.97.57 3.81 1.56 5.37L2.43 22l4.78-1.1c1.48.83 3.17 1.3 4.82 1.3 5.54 0 10.03-4.49 10.03-10.03S17.57 2 12.03 2z" />
              </svg>
              <span>Instant WhatsApp Dispatch</span>
            </div>
            <button
              type="button"
              class="btn-emerald text-[11px] py-1 px-2.5"
              @click="openQuickWhatsAppDispatch()"
            >
              Send Report
            </button>
          </div>

          <!-- Alert Items List -->
          <div class="max-h-72 overflow-y-auto divide-y divide-slate-100">
            <div
              v-for="alt in alerts"
              :key="alt.id"
              class="p-3 hover:bg-slate-50 transition cursor-pointer group"
              :class="{ 'bg-blue-50/20': !alt.read }"
              @click="navigateToAlert(alt)"
            >
              <div class="flex items-start justify-between gap-2">
                <span
                  class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase border"
                  :class="alt.badgeClass"
                >
                  {{ alt.badge }}
                </span>
                <span class="text-[10px] text-slate-400 font-mono">{{ alt.time }}</span>
              </div>

              <div class="mt-1">
                <h4 class="text-xs font-bold text-slate-900 leading-tight group-hover:text-teal-700 transition-colors">
                  {{ alt.title }}
                </h4>
                <p class="text-[11px] text-slate-600 font-medium mt-0.5">
                  {{ alt.patient_name }} ({{ alt.uhid }}) &bull;
                  <span class="font-mono text-teal-700 font-semibold">{{ alt.sample_id }}</span>
                </p>
                <p class="text-[11px] text-slate-500 mt-0.5 line-clamp-2">
                  {{ alt.detail }}
                </p>
              </div>

              <!-- Item Actions: Clean single dispatch with phone, no redundant View button -->
              <div class="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between">
                <span class="text-[10px] text-slate-400 font-mono">{{ alt.phone }}</span>
                <div class="flex items-center space-x-1.5">
                  <button
                    v-if="alt.canWhatsApp"
                    type="button"
                    class="px-2 py-0.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 rounded text-[10px] font-semibold flex items-center space-x-1 transition cursor-pointer"
                    title="Dispatch report to patient on WhatsApp"
                    @click.stop="openQuickWhatsAppDispatch(alt)"
                  >
                    <span>WhatsApp</span>
                  </button>
                  <span class="text-[10px] text-slate-400 group-hover:text-teal-600 font-medium flex items-center">
                    <span>Inspect</span> &rarr;
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Popover Footer -->
          <div class="p-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px]">
            <NuxtLink
              to="/pathology/results"
              class="text-teal-700 hover:text-teal-900 hover:underline font-semibold"
              @click="isAlertsOpen = false"
            >
              Result Workstation &rarr;
            </NuxtLink>
            <NuxtLink
              to="/reporting/release"
              class="text-slate-600 hover:text-slate-900 font-medium"
              @click="isAlertsOpen = false"
            >
              Report Release Desk
            </NuxtLink>
          </div>
        </div>
      </div>

      <!-- User Profile (Hariom Patel - Lab Admin) -->
      <div class="flex items-center space-x-2 pl-2 border-l border-slate-200 text-left">
        <div class="h-8 w-8 rounded-full bg-teal-600 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-xs">
          HP
        </div>
        <div class="hidden sm:block">
          <p class="text-xs font-semibold text-slate-900 leading-tight">Hariom Patel</p>
          <p class="text-[10px] text-slate-500 leading-tight">Lab Admin</p>
        </div>
      </div>
    </div>

    <!-- Quick WhatsApp Report Dispatch Modal -->
    <Modal
      v-model="isWhatsAppModalOpen"
      title="WhatsApp Diagnostic Report Dispatch"
      description="Send verified PDF link directly to patient WhatsApp"
      max-width="md"
    >
      <div class="space-y-4 text-xs">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Patient Name</label>
          <input
            v-model="recipientName"
            type="text"
            class="input-faang w-full bg-slate-50 font-medium"
            readonly
          />
        </div>

        <div>
          <label class="block font-semibold text-slate-700 mb-1">
            Recipient WhatsApp Mobile Number <span class="text-red-500">*</span>
          </label>
          <input
            v-model="recipientPhone"
            type="tel"
            placeholder="+91 98765 43210"
            class="input-faang w-full font-mono font-semibold"
          />
          <p class="text-[10px] text-slate-400 mt-1">Direct international format with country code (+91 for India)</p>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 mb-1">Message Preview</label>
          <div class="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg text-emerald-950 font-sans whitespace-pre-line text-[11px] leading-relaxed shadow-2xs">
            {{ whatsappMessagePreview }}
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <button
            type="button"
            class="btn-secondary"
            @click="close"
          >
            Cancel
          </button>

          <div class="flex items-center space-x-2">
            <button
              type="button"
              class="btn-secondary"
              title="Open chat in WhatsApp Web browser tab"
              @click="sendViaWhatsAppWeb"
            >
              <span>WhatsApp Web</span>
              <svg class="w-3 h-3 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
            </button>

            <button
              type="button"
              :disabled="isSending"
              class="btn-emerald disabled:opacity-50"
              @click="sendViaWhatsAppApi"
            >
              <svg v-if="isSending" class="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Instant Dispatch API</span>
            </button>
          </div>
        </div>
      </template>
    </Modal>
  </header>
</template>
