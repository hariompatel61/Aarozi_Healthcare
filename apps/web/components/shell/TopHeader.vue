<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useBranch } from '~/composables/useBranch'
import { useToast } from '~/composables/useToast'
import { useTheme } from '~/composables/useTheme'
import Modal from '~/components/ui/Modal.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import Icon from '~/components/ui/Icon.vue'
import Kbd from '~/components/ui/Kbd.vue'

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
const { isDark, toggleTheme } = useTheme()
const api = useApi()

// Staff user state
const staffUser = ref<{ username?: string; station?: string; branch?: string }>({})

function handleLogout() {
  const authCookie = useCookie('auth_token', { path: '/' })
  const userCookie = useCookie('aarozi_user', { path: '/' })
  authCookie.value = null
  userCookie.value = null

  if (typeof window !== 'undefined') {
    localStorage.removeItem('token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('aarozi_user')
  }
  router.push('/login')
}

function onBranchChange(event: Event) {
  const target = event.target as HTMLSelectElement
  if (target && target.value) {
    switchBranch(target.value)
    success('Branch Switched', `Operating branch set to ${target.value}`)
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
  badgeVariant: 'panic' | 'warning' | 'info'
  time: string
  read: boolean
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
        badgeVariant: s.flag_type === 'Critical Panic' ? 'panic' : 'warning',
        time: s.collected_at ? `${s.collected_at}` : 'Recently',
        read: false,
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
// WhatsApp Quick Dispatch Modal State
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
    success('WhatsApp Dispatched', `Diagnostic report notification dispatched to ${recipientPhone.value}`)
    isWhatsAppModalOpen.value = false
  } catch (err: any) {
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
    try {
      const stored = localStorage.getItem('aarozi_user')
      if (stored) staffUser.value = JSON.parse(stored)
    } catch (e) {
      console.warn('Failed parsing aarozi_user', e)
    }
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
  <header class="h-14 bg-white/95 dark:bg-[#15182a] border-b border-[#ede9f7] dark:border-[#23273e] px-4 sm:px-6 flex items-center justify-between z-30 sticky top-0 shadow-2xs select-none">
    <!-- Left: Mobile Toggle & Operating Station Indicator -->
    <div class="flex items-center space-x-3">
      <!-- Mobile Hamburger Button -->
      <button
        type="button"
        class="lg:hidden p-1.5 text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 rounded-md cursor-pointer"
        aria-label="Toggle navigation drawer"
        @click="emit('toggle-mobile')"
      >
        <Icon name="menu" size="md" />
      </button>

      <!-- Clean Operating Station Status Badge (NO duplicate branch text, NO static NABL badge) -->
      <div class="hidden sm:flex items-center space-x-2 text-xs">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          {{ staffUser.station || 'Active Station' }}
        </span>
      </div>
    </div>

    <!-- Center: Global Command Palette Quick Search (Ctrl+K) -->
    <div class="hidden md:flex items-center">
      <button
        type="button"
        class="flex items-center justify-between w-64 lg:w-80 px-3 py-1.5 text-xs text-slate-500 dark:text-slate-400 bg-[#f9f8fe] dark:bg-[#1d2138] hover:bg-white dark:hover:bg-[#252b48] border border-[#ede9f7] dark:border-[#2a2f4c] rounded-lg cursor-pointer transition-all shadow-2xs group"
        title="Quick search patients, investigations, barcodes (Ctrl+K)"
        @click="emit('open-command-palette')"
      >
        <div class="flex items-center gap-2">
          <Icon name="search" size="xs" className="text-slate-400 group-hover:text-[#2576d2] transition-colors" />
          <span class="text-slate-500 dark:text-slate-300 font-normal">Search UHID, sample, test...</span>
        </div>
        <Kbd size="xs">Ctrl K</Kbd>
      </button>
    </div>

    <!-- Right Controls: Quick Action, Branch Dropdown, Alerts, Theme, User Profile -->
    <div class="flex items-center space-x-2 sm:space-x-2.5">
      <!-- Quick Action: Register Patient [F2] -->
      <NuxtLink to="/patients/register" class="hidden sm:inline-block">
        <Button variant="primary" size="sm">
          <template #icon-left><Icon name="plus" size="xs" /></template>
          <span>Register</span>
          <Kbd size="xs" class="bg-[#1c5fae] text-[#bee1fb] border-[#2576d2]">F2</Kbd>
        </Button>
      </NuxtLink>

      <!-- Interactive Operating Branch Selector -->
      <div class="flex items-center text-xs text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-2xs overflow-hidden">
        <span class="pl-2 pr-0.5 text-[#2576d2] shrink-0">
          <Icon name="briefcase" size="xs" />
        </span>
        <select
          :value="selectedBranch"
          class="bg-transparent font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer py-1.5 pl-1 pr-2 text-xs"
          title="Operating Branch Center"
          @change="onBranchChange"
        >
          <option v-for="b in branches" :key="b.id" :value="b.name" class="dark:bg-slate-900">
            {{ b.name }}
          </option>
        </select>
      </div>

      <!-- Notification Bell with Clinical Panic Alerts -->
      <div ref="alertsContainerRef" class="relative">
        <button
          type="button"
          :class="[
            'relative p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer',
            isAlertsOpen ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white' : ''
          ]"
          title="Clinical Alerts & Panic Values"
          aria-label="Clinical Alerts"
          @click="isAlertsOpen = !isAlertsOpen"
        >
          <Icon name="alert-circle" size="sm" />
          <!-- Panic counter badge -->
          <span
            v-if="unreadCount > 0"
            class="absolute top-1 right-1 h-3.5 min-w-3.5 px-0.5 rounded-full bg-red-600 text-[9px] font-bold text-white flex items-center justify-center animate-pulse"
          >
            {{ unreadCount }}
          </span>
        </button>

        <!-- Alerts Popover Dropdown -->
        <div
          v-if="isAlertsOpen"
          class="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 z-50 overflow-hidden text-left"
        >
          <div class="px-4 py-3 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-xs text-slate-900 dark:text-white">Clinical Alerts</span>
              <Badge v-if="unreadCount > 0" variant="panic" size="sm">{{ unreadCount }} Pending</Badge>
            </div>
            <button
              v-if="unreadCount > 0"
              type="button"
              class="text-xs text-teal-600 dark:text-teal-400 hover:underline font-semibold cursor-pointer"
              @click="markAllRead"
            >
              Acknowledge All
            </button>
          </div>

          <!-- Alert items list -->
          <div class="max-h-72 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
            <div
              v-for="al in alerts"
              :key="al.id"
              class="p-3 hover:bg-slate-50 dark:hover:bg-slate-800/60 cursor-pointer transition-colors"
              @click="navigateToAlert(al)"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="font-bold text-xs text-slate-800 dark:text-slate-200">{{ al.patient_name }}</span>
                <Badge :variant="al.badgeVariant" size="sm" :dot="al.badgeVariant === 'panic'">{{ al.badge }}</Badge>
              </div>
              <div class="text-xs text-slate-600 dark:text-slate-400 font-medium">{{ al.test }} &bull; {{ al.detail }}</div>
              <div class="mt-1 flex items-center justify-between text-[11px] text-slate-400">
                <span>Sample #{{ al.sample_id }}</span>
                <button
                  type="button"
                  class="text-emerald-600 dark:text-emerald-400 hover:underline font-semibold flex items-center gap-1"
                  @click.stop="openQuickWhatsAppDispatch(al)"
                >
                  <Icon name="whatsapp" size="xs" />
                  Dispatch
                </button>
              </div>
            </div>

            <div v-if="alerts.length === 0" class="py-8 text-center text-xs text-slate-400">
              Zero pending critical alerts. Laboratory normal.
            </div>
          </div>
        </div>
      </div>

      <!-- Theme Switcher Button -->
      <button
        type="button"
        class="p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
        :title="isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'"
        aria-label="Toggle theme"
        @click="toggleTheme"
      >
        <Icon :name="isDark ? 'sun' : 'moon'" size="sm" />
      </button>

      <!-- Logout / Lock Button -->
      <button
        type="button"
        class="p-2 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/40 transition cursor-pointer"
        title="Sign Out / Lock Station"
        @click="handleLogout"
      >
        <Icon name="lock" size="sm" />
      </button>
    </div>

    <!-- WhatsApp Quick Dispatch Modal -->
    <Modal
      v-model="isWhatsAppModalOpen"
      title="Rapid WhatsApp Report Dispatch"
      description="Direct delivery via official Cloud API or WhatsApp Web"
      size="md"
    >
      <div class="space-y-4 text-xs">
        <div class="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-lg text-emerald-950 dark:text-emerald-200 whitespace-pre-line font-mono text-[11px] leading-relaxed">
          {{ whatsappMessagePreview }}
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <Button variant="secondary" size="sm" @click="close">
            Cancel
          </Button>
          <div class="flex items-center space-x-2">
            <Button variant="secondary" size="sm" @click="sendViaWhatsAppWeb">
              Open WhatsApp Web
            </Button>
            <Button
              variant="success"
              size="sm"
              :loading="isSending"
              @click="sendViaWhatsAppApi"
            >
              <template #icon-left><Icon name="whatsapp" size="xs" /></template>
              Send via Cloud API
            </Button>
          </div>
        </div>
      </template>
    </Modal>
  </header>
</template>
