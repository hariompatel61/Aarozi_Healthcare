<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto p-4 sm:p-6 md:p-20">
    <!-- Backdrop Blur -->
    <div
      class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
      @click="close"
    ></div>

    <!-- Command Dialog -->
    <div
      class="relative mx-auto max-w-xl transform divide-y divide-slate-100 overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 transition-all"
    >
      <!-- Search Input Header -->
      <div class="relative flex items-center px-4">
        <svg class="h-5 w-5 text-teal-600 pointer-events-none shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          ref="searchInputRef"
          type="text"
          v-model="query"
          placeholder="Search navigation, patient actions, instruments, or integrations... (Press Esc to close)"
          class="h-12 w-full border-0 bg-transparent pl-3 pr-4 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-0"
          @keydown.down.prevent="navigateDown"
          @keydown.up.prevent="navigateUp"
          @keydown.enter.prevent="selectActive"
          @keydown.esc="close"
        />
        <kbd class="px-2 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-100 rounded border border-slate-200">ESC</kbd>
      </div>

      <!-- Results List -->
      <div class="max-h-80 overflow-y-auto p-2 text-sm text-slate-700 space-y-1">
        <template v-if="filteredItems.length > 0">
          <div
            v-for="(item, index) in filteredItems"
            :key="item.id"
            @click="executeItem(item)"
            @mouseenter="activeIndex = index"
            class="flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer transition-colors"
            :class="activeIndex === index ? 'bg-teal-50 text-teal-900 font-medium' : 'text-slate-700 hover:bg-slate-50'"
          >
            <div class="flex items-center gap-3">
              <span class="text-base">{{ item.icon }}</span>
              <div>
                <div class="text-xs font-semibold text-slate-900">{{ item.title }}</div>
                <div class="text-[11px] text-slate-400">{{ item.subtitle }}</div>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <span v-if="item.badge" class="px-2 py-0.5 text-[10px] rounded-full font-semibold" :class="item.badgeClass || 'bg-slate-100 text-slate-600'">
                {{ item.badge }}
              </span>
              <kbd v-if="activeIndex === index" class="text-[10px] font-mono text-teal-700 bg-teal-100/60 px-1.5 py-0.5 rounded">↵ Go</kbd>
            </div>
          </div>
        </template>

        <!-- Empty State -->
        <div v-else class="py-8 text-center text-xs text-slate-500">
          <p>No matching commands found for <span class="font-semibold text-slate-700">"{{ query }}"</span></p>
          <p class="text-[11px] text-slate-400 mt-1">Try searching "WhatsApp", "Mindray", "Patient", or "CBC"</p>
        </div>
      </div>

      <!-- Footer Quick Tips -->
      <div class="px-4 py-2.5 bg-slate-50 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
        <div class="flex items-center gap-3">
          <span>Navigate <kbd class="font-mono bg-white px-1 rounded border border-slate-200">↑</kbd> <kbd class="font-mono bg-white px-1 rounded border border-slate-200">↓</kbd></span>
          <span>Select <kbd class="font-mono bg-white px-1 rounded border border-slate-200">↵</kbd></span>
          <span>Close <kbd class="font-mono bg-white px-1 rounded border border-slate-200">esc</kbd></span>
        </div>
        <span class="font-semibold text-teal-700">Aarozi SaaS Command Bar</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isOpen = ref(false)
const query = ref('')
const activeIndex = ref(0)
const searchInputRef = ref<HTMLInputElement | null>(null)

interface CommandItem {
  id: string
  title: string
  subtitle: string
  to: string
  icon: string
  badge?: string
  badgeClass?: string
  keywords: string[]
}

const commands: CommandItem[] = [
  // Fast Actions
  {
    id: 'register-patient',
    title: 'Register New Patient',
    subtitle: 'Intake demographic, insurance, and assign UHID',
    to: '/patients',
    icon: '👤',
    badge: 'Intake',
    badgeClass: 'bg-emerald-100 text-emerald-800',
    keywords: ['patient', 'intake', 'register', 'uhid', 'new', 'admit'],
  },
  {
    id: 'cash-billing',
    title: 'New Cashier Invoice',
    subtitle: 'Generate diagnostic bill, collect cash/UPI payment',
    to: '/billing/invoices',
    icon: '💳',
    badge: 'POS',
    badgeClass: 'bg-blue-100 text-blue-800',
    keywords: ['billing', 'invoice', 'payment', 'cashier', 'receipt', 'pos'],
  },
  {
    id: 'analyzer-config',
    title: 'Analyzer Interfacing & Instruments',
    subtitle: 'Configure Mindray, Erba, Cobas, ASTM/HL7 and serial/TCP ports',
    to: '/pathology/instruments',
    icon: '🔬',
    badge: 'ASTM / HL7',
    badgeClass: 'bg-indigo-100 text-indigo-800',
    keywords: ['analyzer', 'instruments', 'machine', 'astm', 'hl7', 'mindray', 'erba', 'cobas', 'serial', 'tcp'],
  },
  {
    id: 'integrations-whatsapp',
    title: 'Integrations & WhatsApp Dispatch',
    subtitle: 'Configure automated WhatsApp report dispatch & Google Drive sync',
    to: '/admin/integrations',
    icon: '💬',
    badge: 'WhatsApp/Drive',
    badgeClass: 'bg-teal-100 text-teal-800',
    keywords: ['whatsapp', 'drive', 'google drive', 'integration', 'cloud', 'sms', 'meta', 'api'],
  },
  {
    id: 'offline-cloud-sync',
    title: 'Offline & Cloud Sync Engine',
    subtitle: 'Transactional outbox replication, conflict desk & air-gap bundle',
    to: '/admin/sync',
    icon: '☁️',
    badge: 'Hybrid Sync',
    badgeClass: 'bg-teal-100 text-teal-800',
    keywords: ['sync', 'offline', 'cloud', 'outbox', 'conflict', 'replication', 'hybrid'],
  },
  {
    id: 'result-entry',
    title: 'Result Entry & Analyte Values',
    subtitle: 'Enter numeric and qualitative test findings',
    to: '/pathology/results',
    icon: '🧪',
    badge: 'LIS',
    badgeClass: 'bg-amber-100 text-amber-800',
    keywords: ['result', 'entry', 'test', 'analyte', 'lab', 'values'],
  },
  {
    id: 'pathologist-verification',
    title: 'Pathologist Verification Desk',
    subtitle: 'Review abnormal and panic values for clinical sign-off',
    to: '/pathology/verification',
    icon: '🩺',
    badge: 'Sign-off',
    badgeClass: 'bg-rose-100 text-rose-800',
    keywords: ['verification', 'pathologist', 'authorize', 'panic', 'sign', 'approval'],
  },
  {
    id: 'report-release',
    title: 'Report Release & Dispatch Queue',
    subtitle: 'View finalized PDF reports with QR codes and delivery logs',
    to: '/reporting/release',
    icon: '📄',
    badge: 'Release',
    badgeClass: 'bg-emerald-100 text-emerald-800',
    keywords: ['report', 'release', 'pdf', 'qr', 'download', 'print', 'dispatch'],
  },
  {
    id: 'test-catalog',
    title: 'Test Catalog Master (1000+ Tests)',
    subtitle: 'Manage 3-layer test packages, profiles, parameters, and LOINC codes',
    to: '/pathology/catalog',
    icon: '📚',
    badge: 'Master',
    badgeClass: 'bg-purple-100 text-purple-800',
    keywords: ['catalog', 'tests', 'loinc', 'packages', 'profiles', 'parameters', 'prices'],
  },
  {
    id: 'blood-bank-donors',
    title: 'Blood Bank Donor Registry',
    subtitle: 'Screen voluntary donors, assess deferrals, and log donations',
    to: '/blood_bank/donors',
    icon: '🩸',
    badge: 'Blood Bank',
    badgeClass: 'bg-rose-100 text-rose-800',
    keywords: ['blood', 'donor', 'donation', 'deferral', 'screening'],
  },
  {
    id: 'blood-inventory',
    title: 'Blood Component Inventory',
    subtitle: 'Track PRBC, FFP, Platelets with cold-chain monitoring',
    to: '/blood_bank/inventory',
    icon: '🧊',
    badge: 'Blood Bank',
    badgeClass: 'bg-rose-100 text-rose-800',
    keywords: ['inventory', 'blood', 'prbc', 'ffp', 'platelets', 'storage'],
  },
  {
    id: 'crossmatch',
    title: 'Compatibility & Cross-Match Desk',
    subtitle: 'Major/minor cross-match and compatibility testing',
    to: '/blood_bank/crossmatch',
    icon: '❤️',
    badge: 'Blood Bank',
    badgeClass: 'bg-rose-100 text-rose-800',
    keywords: ['crossmatch', 'compatibility', 'transfusion', 'patient blood'],
  },
  {
    id: 'licensing',
    title: 'System Licensing & Offline Cryptography',
    subtitle: 'Ed25519 offline license verification and feature entitlements',
    to: '/admin/licensing',
    icon: '🔐',
    badge: 'License',
    badgeClass: 'bg-slate-100 text-slate-800',
    keywords: ['license', 'offline', 'activation', 'ed25519', 'subscription', 'renewal'],
  },
]

const filteredItems = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return commands
  return commands.filter((cmd) => {
    return (
      cmd.title.toLowerCase().includes(q) ||
      cmd.subtitle.toLowerCase().includes(q) ||
      cmd.keywords.some((k) => k.includes(q))
    )
  })
})

watch(query, () => {
  activeIndex.value = 0
})

function open() {
  isOpen.value = true
  query.value = ''
  activeIndex.value = 0
  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

function close() {
  isOpen.value = false
}

function navigateDown() {
  if (activeIndex.value < filteredItems.value.length - 1) {
    activeIndex.value++
  } else {
    activeIndex.value = 0
  }
}

function navigateUp() {
  if (activeIndex.value > 0) {
    activeIndex.value--
  } else {
    activeIndex.value = filteredItems.value.length - 1
  }
}

function selectActive() {
  const item = filteredItems.value[activeIndex.value]
  if (item) {
    executeItem(item)
  }
}

function executeItem(item: CommandItem) {
  close()
  router.push(item.to)
}

function onGlobalKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    if (isOpen.value) {
      close()
    } else {
      open()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
})

defineExpose({
  open,
  close,
})
</script>

