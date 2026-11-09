<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'
import { useReportTheme, type ThemeId } from '~/composables/useReportTheme'

const { success, info, warning } = useToast()
const {
  themes,
  currentThemeId,
  currentTheme,
  labIdentity,
  signatories,
  themeOptions,
  selectTheme,
  saveAsDefault,
  resetToDefaults,
} = useReportTheme()

// Main Page Navigation Tabs: 'customizer' vs 'catalog'
type PageTab = 'customizer' | 'catalog'
const activePageTab = ref<PageTab>('customizer')

// Sidebar Customizer Tab: 'lab' | 'signatories' | 'print'
type DrawerTab = 'lab' | 'signatories' | 'print'
const activeDrawerTab = ref<DrawerTab>('lab')

// Color Palette Swatches
const colorPresets = [
  { name: 'Royal Blue', hex: '#0052cc' },
  { name: 'Navy Blue', hex: '#0f2942' },
  { name: 'Medical Green', hex: '#16a34a' },
  { name: 'Maroon Red', hex: '#881337' },
  { name: 'Gold / Yellow', hex: '#eab308' },
  { name: 'Dark Slate', hex: '#1e293b' },
]

// Sample Patient Demographics for Live A4 Interpolation
const samplePatient = reactive({
  name: 'Aarav Sharma',
  pid: 'PAT-2026-0842',
  ageGender: '34 Yrs / Male',
  barcode: 'SMP-98214',
  collectionCentre: 'Aarozi Central Lab, Hub #4, New Delhi',
  referredBy: 'Dr. Amrit Singh (MD, Medicine)',
  registeredAt: '20-Oct-2026 08:30 AM',
  collectedAt: '20-Oct-2026 09:15 AM',
  reportedAt: '20-Oct-2026 11:45 AM',
  sampleType: 'Whole Blood EDTA',
})

// Sample Test Parameters
const sampleParameters = [
  { name: 'Hemoglobin (Hb)', result: '14.2', unit: 'g/dL', range: '13.0 - 17.0', flag: 'NORMAL', isAbnormal: false },
  { name: 'Total Leukocyte Count (TLC)', result: '11,800', unit: '/cumm', range: '4,000 - 11,000', flag: 'HIGH [↑ H]', isAbnormal: true, high: true },
  { name: 'Platelet Count', result: '1,45,000', unit: '/cumm', range: '1,50,000 - 4,50,000', flag: 'LOW [↓ L]', isAbnormal: true, low: true },
  { name: 'Neutrophils', result: '78', unit: '%', range: '40 - 70', flag: 'HIGH [↑ H]', isAbnormal: true, high: true },
  { name: 'Lymphocytes', result: '18', unit: '%', range: '20 - 40', flag: 'LOW [↓ L]', isAbnormal: true, low: true },
  { name: 'Monocytes', result: '3', unit: '%', range: '2 - 8', flag: 'NORMAL', isAbnormal: false },
  { name: 'Eosinophils', result: '1', unit: '%', range: '1 - 6', flag: 'NORMAL', isAbnormal: false },
  { name: 'Basophils', result: '0', unit: '%', range: '0 - 1', flag: 'NORMAL', isAbnormal: false },
  { name: 'Packed Cell Volume (PCV)', result: '43.5', unit: '%', range: '40.0 - 50.0', flag: 'NORMAL', isAbnormal: false },
  { name: 'Mean Corpuscular Volume (MCV)', result: '86.4', unit: 'fL', range: '80.0 - 96.0', flag: 'NORMAL', isAbnormal: false },
]

// Logo Upload Handler
function handleLogoUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    if (file.size > 2 * 1024 * 1024) {
      warning('File Too Large', 'Please upload a logo image smaller than 2MB.')
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      labIdentity.logoUrl = e.target?.result as string
      success('Logo Updated', 'Custom lab logo updated in live A4 canvas.')
    }
    reader.readAsDataURL(file)
  }
}

function clearLogo() {
  labIdentity.logoUrl = ''
  info('Logo Cleared', 'Fallback medical shield icon restored.')
}

// Signature Upload Handler
function handleSignatureUpload(sigId: string, event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    if (file.size > 1 * 1024 * 1024) {
      warning('File Too Large', 'Signature file should be under 1MB (PNG transparent recommended).')
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      const sig = signatories.value.find((s) => s.id === sigId)
      if (sig) {
        sig.signatureImageUrl = e.target?.result as string
        success('Signature Saved', `Transparent signature attached to ${sig.name}.`)
      }
    }
    reader.readAsDataURL(file)
  }
}

function clearSignature(sigId: string) {
  const sig = signatories.value.find((s) => s.id === sigId)
  if (sig) {
    sig.signatureImageUrl = ''
    info('Signature Removed', `Default cursive signature restored for ${sig.name}.`)
  }
}

// Print Live A4 Trigger
function printA4() {
  window.print()
}

// -------------------------------------------------------------
// CATALOG TAB LOGIC (Ensures backward compatibility)
// -------------------------------------------------------------
const categories = [
  'All Categories',
  'Hematology',
  'Biochemistry',
  'Hormones',
  'Urinalysis',
  'Histopathology',
  'Serology',
  'General',
]
const catalogSearch = ref('')
const catalogCategory = ref('All Categories')

const catalogTemplates = ref([
  { id: 'TPL-HEM-CBC', code: 'CBC-01', title: 'Complete Blood Count (CBC & ESR)', category: 'Hematology', layout: 'drlogy', status: 'Published' },
  { id: 'TPL-BIO-LFT', code: 'LFT-01', title: 'Liver Function Test (LFT Complete)', category: 'Biochemistry', layout: 'healthplus', status: 'Published' },
  { id: 'TPL-BIO-KFT', code: 'KFT-01', title: 'Kidney Function Test (KFT & Electrolytes)', category: 'Biochemistry', layout: 'medicore', status: 'Published' },
  { id: 'TPL-HOR-THY', code: 'THY-01', title: 'Thyroid Profile (Total T3, T4, TSH)', category: 'Hormones', layout: 'guru', status: 'Published' },
  { id: 'TPL-BIO-LIP', code: 'LIP-01', title: 'Lipid Profile Comprehensive', category: 'Biochemistry', layout: 'varad', status: 'Published' },
  { id: 'TPL-URI-ROU', code: 'URI-01', title: 'Urine Routine & Microscopy Examination', category: 'Urinalysis', layout: 'dragon', status: 'Published' },
])

const filteredCatalog = computed(() => {
  return catalogTemplates.value.filter((t) => {
    if (catalogCategory.value !== 'All Categories' && t.category !== catalogCategory.value) return false
    const q = catalogSearch.value.trim().toLowerCase()
    if (q) {
      return t.title.toLowerCase().includes(q) || t.code.toLowerCase().includes(q) || t.category.toLowerCase().includes(q)
    }
    return true
  })
})

function applyTemplateTheme(layoutId: string) {
  if (themes.some((th) => th.id === layoutId)) {
    selectTheme(layoutId as ThemeId)
    activePageTab.value = 'customizer'
    success('Theme Activated', `Loaded layout "${layoutId.toUpperCase()}" into live customizer.`)
  }
}
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left pb-12">
    <!-- Top Action Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <div class="flex items-center space-x-2">
          <h1 class="text-xl font-bold text-slate-900 tracking-tight">
            Pathology Report Themes &amp; Branding Engine
          </h1>
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
            6 Real-World Themes
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-0.5">
          Customise lab branding, 3-tier signatory seals, watermark &amp; switch between Indian &amp; international diagnostic A4 formats
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <button
          type="button"
          :class="[
            'px-3.5 py-1.5 text-xs font-semibold rounded shadow-2xs transition cursor-pointer flex items-center space-x-1.5',
            activePageTab === 'customizer' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
          ]"
          @click="activePageTab = 'customizer'"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" /></svg>
          <span>Themes &amp; Branding</span>
        </button>

        <button
          type="button"
          :class="[
            'px-3.5 py-1.5 text-xs font-semibold rounded shadow-2xs transition cursor-pointer flex items-center space-x-1.5',
            activePageTab === 'catalog' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
          ]"
          @click="activePageTab = 'catalog'"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
          <span>Test Catalog Master</span>
        </button>

        <button
          type="button"
          class="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded shadow-2xs transition cursor-pointer flex items-center space-x-1"
          title="Reset theme and branding to default Drlogy configuration"
          @click="resetToDefaults"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          <span>Reset</span>
        </button>

        <button
          type="button"
          class="px-3.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold rounded shadow-2xs transition cursor-pointer flex items-center space-x-1"
          @click="printA4"
        >
          <svg class="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
          <span>Print / PDF</span>
        </button>

        <button
          type="button"
          class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded shadow-xs transition cursor-pointer flex items-center space-x-1.5"
          @click="saveAsDefault"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" /></svg>
          <span>Set as Default Lab Theme</span>
        </button>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- TAB 1: THEMES & BRANDING CUSTOMIZER                     -->
    <!-- ======================================================== -->
    <div v-if="activePageTab === 'customizer'" class="space-y-4">
      <!-- 6 Themes Carousel / Selector Bar -->
      <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs space-y-2">
        <div class="flex items-center justify-between text-xs font-semibold text-slate-600 px-1">
          <div class="flex items-center space-x-1.5">
            <span class="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
            <span class="font-bold text-slate-900 uppercase tracking-wider text-[11px]">Select A4 Report Layout Style</span>
          </div>
          <span class="text-slate-400 text-[11px]">Active: <strong class="text-blue-700 font-bold">{{ currentTheme?.name }}</strong></span>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          <button
            v-for="t in themes"
            :key="t.id"
            type="button"
            :class="[
              'p-2.5 rounded-lg border text-left transition-all cursor-pointer relative flex flex-col justify-between group overflow-hidden',
              currentThemeId === t.id
                ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/30 shadow-xs'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/70 shadow-2xs'
            ]"
            @click="selectTheme(t.id)"
          >
            <!-- Top Color Accent Bar -->
            <div class="w-full h-1 rounded-full mb-2" :style="{ backgroundColor: t.accentColor }" />

            <div>
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded" :style="{ color: t.accentColor, backgroundColor: `${t.accentColor}18` }">
                  {{ t.badge }}
                </span>
                <span v-if="currentThemeId === t.id" class="text-blue-600">
                  <svg class="w-4 h-4 fill-current" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                </span>
              </div>
              <h3 class="text-xs font-bold text-slate-900 group-hover:text-blue-700 leading-tight">
                {{ t.name }}
              </h3>
              <p class="text-[10px] text-slate-500 line-clamp-1 mt-0.5">
                {{ t.tagline }}
              </p>
            </div>

            <!-- Mini Layout Geometry Preview -->
            <div class="mt-2.5 pt-2 border-t border-slate-100 flex items-center space-x-1 opacity-70">
              <span class="w-3 h-1.5 rounded-xs" :style="{ backgroundColor: t.accentColor }" />
              <span class="h-1 bg-slate-200 rounded-full flex-1" />
              <span class="w-1.5 h-1.5 rounded-full bg-slate-300" />
            </div>
          </button>
        </div>
      </div>

      <!-- Main Customizer & A4 Preview Workspace -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        <!-- LEFT: Branding & Pathologist Customizer Drawer (5 cols) -->
        <div class="lg:col-span-5 space-y-3">
          <!-- Drawer Sub-Tabs -->
          <div class="bg-white p-1 rounded-lg border border-slate-200 flex items-center text-xs font-semibold shadow-2xs">
            <button
              type="button"
              :class="[
                'flex-1 py-1.5 rounded text-center transition cursor-pointer flex items-center justify-center space-x-1',
                activeDrawerTab === 'lab' ? 'bg-blue-600 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              ]"
              @click="activeDrawerTab = 'lab'"
            >
              <span>1. Lab Identity</span>
            </button>
            <button
              type="button"
              :class="[
                'flex-1 py-1.5 rounded text-center transition cursor-pointer flex items-center justify-center space-x-1',
                activeDrawerTab === 'signatories' ? 'bg-blue-600 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              ]"
              @click="activeDrawerTab = 'signatories'"
            >
              <span>2. Signatories</span>
            </button>
            <button
              type="button"
              :class="[
                'flex-1 py-1.5 rounded text-center transition cursor-pointer flex items-center justify-center space-x-1',
                activeDrawerTab === 'print' ? 'bg-blue-600 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              ]"
              @click="activeDrawerTab = 'print'"
            >
              <span>3. Theme &amp; Margins</span>
            </button>
          </div>

          <!-- DRAWER TAB 1: LAB IDENTITY -->
          <div v-show="activeDrawerTab === 'lab'" class="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3.5 text-xs">
            <div class="border-b border-slate-100 pb-2">
              <h2 class="font-bold text-slate-900 text-sm">Laboratory Branding &amp; Letterhead</h2>
              <p class="text-[11px] text-slate-500">Edit your clinic or laboratory identity visible across all headers.</p>
            </div>

            <!-- Lab Logo Upload -->
            <div>
              <label class="block font-semibold text-slate-700 mb-1.5">Lab Logo</label>
              <div class="flex items-center space-x-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <div class="w-14 h-14 bg-white rounded border border-slate-300 flex items-center justify-center overflow-hidden shrink-0 shadow-2xs">
                  <img
                    v-if="labIdentity.logoUrl"
                    :src="labIdentity.logoUrl"
                    alt="Lab Logo Preview"
                    class="w-full h-full object-contain p-1"
                  />
                  <div v-else class="text-blue-600 flex flex-col items-center">
                    <svg class="w-7 h-7" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5zm-1 6h2v3h3v2h-3v3h-2v-3H8v-2h3V8z" />
                    </svg>
                  </div>
                </div>

                <div class="flex-1 space-y-1">
                  <div class="flex items-center space-x-1.5">
                    <label class="px-2.5 py-1 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold rounded cursor-pointer text-[11px] shadow-2xs">
                      <span>Upload Logo</span>
                      <input type="file" accept="image/png,image/jpeg,image/svg+xml" class="hidden" @change="handleLogoUpload" />
                    </label>
                    <button
                      v-if="labIdentity.logoUrl"
                      type="button"
                      class="px-2 py-1 text-red-600 hover:text-red-800 text-[11px] font-semibold cursor-pointer"
                      @click="clearLogo"
                    >
                      Clear
                    </button>
                  </div>
                  <p class="text-[10px] text-slate-400">PNG or SVG recommended with transparent background (Max 2MB).</p>
                </div>
              </div>
            </div>

            <!-- Lab Name & Tagline -->
            <div class="grid grid-cols-1 gap-2.5">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Laboratory / Hospital Name</label>
                <input
                  v-model="labIdentity.labName"
                  type="text"
                  placeholder="e.g. Drlogy Pathology Lab"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 font-semibold text-slate-900"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">Lab Tagline / Mission</label>
                <input
                  v-model="labIdentity.tagline"
                  type="text"
                  placeholder="e.g. Accurate | Caring | Instant"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 text-slate-700"
                />
              </div>
            </div>

            <!-- Address & Contacts -->
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Facility Address</label>
              <textarea
                v-model="labIdentity.address"
                rows="2"
                placeholder="Plot 42, Knowledge Park III, Greater Noida, UP - 201310"
                class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 text-slate-700"
              />
            </div>

            <div class="grid grid-cols-2 gap-2.5">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Official Phones</label>
                <input
                  v-model="labIdentity.phoneNumbers"
                  type="text"
                  placeholder="+91 98765 43210"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs text-slate-700 font-mono"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">Official Email</label>
                <input
                  v-model="labIdentity.email"
                  type="email"
                  placeholder="reports@aarozi.health"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs text-slate-700"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2.5">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Website URL</label>
                <input
                  v-model="labIdentity.website"
                  type="text"
                  placeholder="www.aarozi.health"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs text-slate-700 font-mono"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">Home Collection WhatsApp</label>
                <input
                  v-model="labIdentity.homeCollectionPhone"
                  type="text"
                  placeholder="+91 98765 43210"
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs text-slate-700 font-mono"
                />
              </div>
            </div>

            <!-- Accreditation Badges Toggle -->
            <div class="pt-2 border-t border-slate-100 flex items-center justify-between">
              <div>
                <span class="font-semibold text-slate-800 block">Accreditation Badges</span>
                <span class="text-[10px] text-slate-500">Show NABL (ISO 15189) &amp; ISO 9001:2015 emblems</span>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input v-model="labIdentity.isoNablBadges" type="checkbox" class="sr-only peer" />
                <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
              </label>
            </div>
          </div>

          <!-- DRAWER TAB 2: SIGNATORIES -->
          <div v-show="activeDrawerTab === 'signatories'" class="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3.5 text-xs">
            <div class="border-b border-slate-100 pb-2 flex items-center justify-between">
              <div>
                <h2 class="font-bold text-slate-900 text-sm">Pathologists &amp; Signatories</h2>
                <p class="text-[11px] text-slate-500">Manage up to 3 authorized signatures in the report footer.</p>
              </div>
              <span class="text-[10px] font-mono bg-blue-50 text-blue-700 font-bold px-2 py-0.5 rounded border border-blue-200">
                3 POSITIONS
              </span>
            </div>

            <!-- Signatory Cards Accordion / List -->
            <div class="space-y-3">
              <div
                v-for="(sig, idx) in signatories"
                :key="sig.id"
                class="bg-slate-50 rounded-lg border border-slate-200 p-3 space-y-2.5"
              >
                <div class="flex items-center justify-between border-b border-slate-200 pb-1.5">
                  <div class="flex items-center space-x-1.5">
                    <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-800 font-bold text-[10px] flex items-center justify-center">
                      {{ idx + 1 }}
                    </span>
                    <span class="font-bold text-slate-800">
                      {{ idx === 0 ? 'Left (Lab Technician)' : idx === 1 ? 'Center (Consultant Pathologist)' : 'Right (Chief Pathologist)' }}
                    </span>
                  </div>
                  <label class="inline-flex items-center space-x-1 cursor-pointer">
                    <input v-model="sig.enabled" type="checkbox" class="rounded text-blue-600 h-3.5 w-3.5" />
                    <span class="text-[11px] text-slate-600 font-semibold">Active</span>
                  </label>
                </div>

                <div v-if="sig.enabled" class="space-y-2">
                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label class="block font-semibold text-slate-700 text-[11px] mb-0.5">Doctor / Staff Name</label>
                      <input
                        v-model="sig.name"
                        type="text"
                        class="w-full px-2 py-1 bg-white border border-slate-300 rounded text-xs text-slate-900 font-semibold"
                      />
                    </div>
                    <div>
                      <label class="block font-semibold text-slate-700 text-[11px] mb-0.5">Degree / Qualifications</label>
                      <input
                        v-model="sig.qualification"
                        type="text"
                        class="w-full px-2 py-1 bg-white border border-slate-300 rounded text-xs text-slate-700"
                      />
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label class="block font-semibold text-slate-700 text-[11px] mb-0.5">Designation</label>
                      <input
                        v-model="sig.designation"
                        type="text"
                        class="w-full px-2 py-1 bg-white border border-slate-300 rounded text-xs text-slate-700"
                      />
                    </div>
                    <div>
                      <label class="block font-semibold text-slate-700 text-[11px] mb-0.5">Registration / MCI No.</label>
                      <input
                        v-model="sig.regNo"
                        type="text"
                        class="w-full px-2 py-1 bg-white border border-slate-300 rounded text-xs text-slate-700 font-mono"
                      />
                    </div>
                  </div>

                  <!-- Signature Upload -->
                  <div class="pt-1.5 flex items-center justify-between bg-white p-2 rounded border border-slate-200">
                    <div class="flex items-center space-x-2">
                      <div class="h-8 w-20 border border-slate-300 rounded bg-slate-50 flex items-center justify-center overflow-hidden">
                        <img
                          v-if="sig.signatureImageUrl"
                          :src="sig.signatureImageUrl"
                          alt="Signature"
                          class="h-full w-full object-contain p-0.5"
                        />
                        <span v-else class="text-blue-900 font-serif italic text-xs font-bold">{{ sig.name.split(' ')[0] }}</span>
                      </div>
                      <span class="text-[10px] text-slate-500">
                        {{ sig.signatureImageUrl ? 'Custom PNG Attached' : 'Auto Cursive Stamp' }}
                      </span>
                    </div>

                    <div class="flex items-center space-x-1">
                      <label class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded cursor-pointer text-[10.5px]">
                        <span>Upload PNG</span>
                        <input type="file" accept="image/png,image/jpeg" class="hidden" @change="handleSignatureUpload(sig.id, $event)" />
                      </label>
                      <button
                        v-if="sig.signatureImageUrl"
                        type="button"
                        class="text-red-600 hover:text-red-800 text-[10.5px] font-semibold px-1 cursor-pointer"
                        @click="clearSignature(sig.id)"
                      >
                        Reset
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- DRAWER TAB 3: THEME & MARGINS -->
          <div v-show="activeDrawerTab === 'print'" class="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3.5 text-xs">
            <div class="border-b border-slate-100 pb-2">
              <h2 class="font-bold text-slate-900 text-sm">Theme Palettes &amp; Print Setup</h2>
              <p class="text-[11px] text-slate-500">Accent colors, watermark options &amp; pre-printed letterhead mode.</p>
            </div>

            <!-- Primary Accent Color Presets -->
            <div>
              <label class="block font-semibold text-slate-700 mb-1.5">Primary Accent Color</label>
              <div class="flex items-center space-x-2 flex-wrap gap-y-1.5">
                <button
                  v-for="color in colorPresets"
                  :key="color.hex"
                  type="button"
                  :class="[
                    'w-7 h-7 rounded-full border-2 transition-transform cursor-pointer relative shadow-2xs',
                    themeOptions.primaryColor.toLowerCase() === color.hex.toLowerCase()
                      ? 'scale-110 border-white ring-2 ring-blue-500'
                      : 'border-white hover:scale-105'
                  ]"
                  :style="{ backgroundColor: color.hex }"
                  :title="color.name"
                  @click="themeOptions.primaryColor = color.hex"
                />
                <div class="flex items-center space-x-1.5 pl-2">
                  <input
                    v-model="themeOptions.primaryColor"
                    type="color"
                    class="w-7 h-7 rounded cursor-pointer border border-slate-300"
                  />
                  <input
                    v-model="themeOptions.primaryColor"
                    type="text"
                    class="w-20 px-2 py-1 border border-slate-300 rounded font-mono text-[11px] text-slate-700 uppercase"
                  />
                </div>
              </div>
            </div>

            <!-- Watermark & Barcode Toggles -->
            <div class="space-y-2 pt-2 border-t border-slate-100">
              <div class="flex items-center justify-between">
                <div>
                  <span class="font-semibold text-slate-800 block">Center Background Watermark</span>
                  <span class="text-[10px] text-slate-500">Subtle translucent lab crest behind results table</span>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input v-model="themeOptions.showWatermark" type="checkbox" class="sr-only peer" />
                  <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
                </label>
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <span class="font-semibold text-slate-800 block">QR Code &amp; Sample Barcode</span>
                  <span class="text-[10px] text-slate-500">Show verification QR seal &amp; 1D sample barcode</span>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input v-model="themeOptions.showQrAndBarcode" type="checkbox" class="sr-only peer" />
                  <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
                </label>
              </div>
            </div>

            <!-- Blank vs Pre-printed Letterhead Mode -->
            <div class="pt-3 border-t border-slate-100 space-y-2">
              <label class="block font-semibold text-slate-800">Print Paper Type</label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  :class="[
                    'p-2.5 rounded-lg border text-left cursor-pointer transition',
                    themeOptions.letterheadMode === 'blank'
                      ? 'border-blue-600 bg-blue-50/60 ring-1 ring-blue-500'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  ]"
                  @click="themeOptions.letterheadMode = 'blank'"
                >
                  <strong class="block text-slate-900 text-[11px]">Blank A4 Paper</strong>
                  <span class="text-[10px] text-slate-500 block">Prints complete header, clinic logo &amp; footer banner</span>
                </button>

                <button
                  type="button"
                  :class="[
                    'p-2.5 rounded-lg border text-left cursor-pointer transition',
                    themeOptions.letterheadMode === 'preprinted'
                      ? 'border-amber-600 bg-amber-50/60 ring-1 ring-amber-500'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  ]"
                  @click="themeOptions.letterheadMode = 'preprinted'"
                >
                  <strong class="block text-slate-900 text-[11px]">Pre-printed Stationery</strong>
                  <span class="text-[10px] text-slate-500 block">Hides headers/footers and reserves margin space</span>
                </button>
              </div>

              <!-- Preprinted Margin Sliders -->
              <div v-if="themeOptions.letterheadMode === 'preprinted'" class="bg-amber-50/70 border border-amber-200 rounded p-2.5 space-y-2 text-[11px]">
                <div class="flex items-center justify-between">
                  <span class="text-amber-900 font-semibold">Top Header Reserve:</span>
                  <span class="font-mono font-bold text-amber-800">{{ themeOptions.preprintedTopMarginMm }} mm</span>
                </div>
                <input
                  v-model.number="themeOptions.preprintedTopMarginMm"
                  type="range"
                  min="20"
                  max="60"
                  step="2"
                  class="w-full accent-amber-600 cursor-pointer"
                />

                <div class="flex items-center justify-between pt-1">
                  <span class="text-amber-900 font-semibold">Bottom Footer Reserve:</span>
                  <span class="font-mono font-bold text-amber-800">{{ themeOptions.preprintedBottomMarginMm }} mm</span>
                </div>
                <input
                  v-model.number="themeOptions.preprintedBottomMarginMm"
                  type="range"
                  min="15"
                  max="45"
                  step="2"
                  class="w-full accent-amber-600 cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Live A4 Preview Canvas (7 cols) -->
        <div class="lg:col-span-7 flex flex-col items-center">
          <!-- Canvas Top Info Bar -->
          <div class="w-full flex items-center justify-between mb-2 px-1 text-xs text-slate-500">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-slate-800">A4 Live Letterhead Preview</span>
              <span class="text-[10px] font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                210mm &times; 297mm Standard
              </span>
            </div>
            <span class="text-emerald-700 font-semibold flex items-center text-[11px]">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-ping" />
              Live Binding Active
            </span>
          </div>

          <!-- A4 Paper Container with Shadow and Precise Proportions -->
          <div class="w-full bg-slate-200/80 p-3 sm:p-5 rounded-xl shadow-inner flex justify-center overflow-x-auto">
            <div
              id="a4-report-canvas"
              class="bg-white shadow-2xl border border-slate-300 w-full text-slate-900 relative transition-all flex flex-col justify-between overflow-hidden"
              :style="{
                maxWidth: '680px',
                minHeight: '940px',
                padding: '16px',
                fontFamily: currentThemeId === 'varad' ? 'Georgia, serif' : currentThemeId === 'dragon' ? 'ui-serif, Georgia, serif' : 'Inter, -apple-system, sans-serif',
              }"
            >
              <!-- Center Watermark Layer -->
              <div
                v-if="themeOptions.showWatermark"
                class="absolute inset-0 pointer-events-none flex items-center justify-center opacity-[0.045] select-none z-0"
              >
                <div class="text-center transform -rotate-25">
                  <svg class="w-60 h-60 mx-auto text-slate-900" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5zm0 4a3 3 0 110 6 3 3 0 010-6zm0 14.93c-3.86-1.1-6.9-4.88-6.99-9.13.88.37 1.83.6 2.82.68.27 1.77 1.48 3.25 3.17 3.78v4.67z" />
                  </svg>
                  <div class="text-2xl font-black uppercase tracking-widest text-slate-900 mt-2">
                    {{ labIdentity.labName }}
                  </div>
                  <div class="text-xs font-bold text-slate-700 tracking-wider">
                    CERTIFIED CLINICAL REPORT
                  </div>
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- PRE-PRINTED STATIONERY TOP MARGIN PLACEHOLDER        -->
              <!-- ==================================================== -->
              <div
                v-if="themeOptions.letterheadMode === 'preprinted'"
                class="border-2 border-dashed border-amber-300 bg-amber-50/60 rounded p-2 mb-3 text-center text-amber-800 text-[10.5px] font-mono flex items-center justify-center"
                :style="{ height: `${themeOptions.preprintedTopMarginMm * 2.8}px` }"
              >
                [ RESERVED TOP {{ themeOptions.preprintedTopMarginMm }}MM FOR PRE-PRINTED HOSPITAL STATIONERY ]
              </div>

              <!-- ==================================================== -->
              <!-- THEME 1: DRLOGY MODERN BLUE                          -->
              <!-- ==================================================== -->
              <div v-else-if="currentThemeId === 'drlogy'" class="space-y-3 z-10 relative">
                <!-- Drlogy Header -->
                <div class="border-b pb-2">
                  <div class="flex items-start justify-between">
                    <div class="flex items-center space-x-2.5">
                      <div class="w-12 h-12 rounded-full border-2 border-blue-600 p-1 flex items-center justify-center shadow-2xs shrink-0 overflow-hidden bg-white">
                        <img v-if="labIdentity.logoUrl" :src="labIdentity.logoUrl" class="w-full h-full object-contain" />
                        <svg v-else class="w-8 h-8 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5zm-1 6h2v3h3v2h-3v3h-2v-3H8v-2h3V8z" />
                        </svg>
                      </div>
                      <div>
                        <h1 class="text-base font-extrabold tracking-tight">
                          <span class="text-slate-900">{{ labIdentity.labName.split(' ')[0] }} </span>
                          <span class="text-blue-700">{{ labIdentity.labName.split(' ').slice(1).join(' ') || 'Diagnostics' }}</span>
                        </h1>
                        <p class="text-[10px] text-slate-500 font-medium">{{ labIdentity.tagline }}</p>
                        <p class="text-[9px] text-slate-400 mt-0.5">{{ labIdentity.address }}</p>
                      </div>
                    </div>

                    <div class="text-right text-[9.5px] space-y-0.5 shrink-0">
                      <div class="flex items-center justify-end space-x-1 text-slate-600">
                        <svg class="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
                        <span>{{ labIdentity.phoneNumbers.split('/')[0] }}</span>
                      </div>
                      <div class="flex items-center justify-end space-x-1 text-slate-600">
                        <svg class="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                        <span>{{ labIdentity.email }}</span>
                      </div>
                      <div v-if="labIdentity.isoNablBadges" class="flex items-center justify-end space-x-1 pt-0.5">
                        <span class="text-[8px] bg-emerald-50 text-emerald-800 font-bold px-1.5 py-0.2 rounded border border-emerald-200">
                          NABL ISO 15189
                        </span>
                        <span class="text-[8px] bg-blue-50 text-blue-800 font-bold px-1.5 py-0.2 rounded border border-blue-200">
                          ISO 9001:2015
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Blue Bar with Diagonal Stripes Center & Website Right -->
                  <div class="mt-2 h-5 bg-blue-600 rounded-sm flex items-center justify-between px-2 text-white text-[9px] overflow-hidden">
                    <span class="font-semibold tracking-wide uppercase text-[8.5px]">Pathology Laboratory Report</span>
                    <!-- Center Diagonal Stripes Pattern -->
                    <div class="flex items-center space-x-1 opacity-80">
                      <svg width="45" height="12" class="inline-block">
                        <defs>
                          <pattern id="drlogy-stripes" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                            <line x1="0" y1="0" x2="0" y2="6" stroke="#000" stroke-width="2" />
                          </pattern>
                        </defs>
                        <rect width="45" height="12" fill="url(#drlogy-stripes)" />
                      </svg>
                    </div>
                    <span class="font-mono text-[8.5px]">{{ labIdentity.website }}</span>
                  </div>
                </div>

                <!-- Drlogy 3-Column Patient Block -->
                <div class="bg-slate-50 border border-slate-200 rounded p-2.5 text-[9.5px]">
                  <div class="grid grid-cols-12 gap-2">
                    <!-- Left: Patient Details -->
                    <div class="col-span-5 space-y-0.5">
                      <div><span class="text-slate-400">Patient Name:</span> <strong class="text-slate-900">{{ samplePatient.name }}</strong></div>
                      <div><span class="text-slate-400">Age / Sex:</span> <strong>{{ samplePatient.ageGender }}</strong></div>
                      <div><span class="text-slate-400">Patient ID (PID):</span> <strong class="font-mono text-blue-800">{{ samplePatient.pid }}</strong></div>
                      <div><span class="text-slate-400">Primary Contact:</span> <span>+91 98100 23456</span></div>
                    </div>

                    <!-- Center: QR Code & Ref Doctor -->
                    <div class="col-span-4 border-x border-slate-200 px-2 flex flex-col justify-between">
                      <div class="space-y-0.5">
                        <div><span class="text-slate-400">Ref By:</span> <strong class="text-slate-800">{{ samplePatient.referredBy }}</strong></div>
                        <div class="line-clamp-1"><span class="text-slate-400">Collected At:</span> <span>{{ samplePatient.collectionCentre }}</span></div>
                      </div>
                      <div v-if="themeOptions.showQrAndBarcode" class="flex items-center space-x-2 pt-1">
                        <div class="w-8 h-8 bg-white border border-slate-300 rounded p-0.5 flex items-center justify-center shrink-0">
                          <svg class="w-7 h-7 text-slate-800" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2 2h8v8H2V2zm2 2v4h4V4H4zm10-2h8v8h-8V2zm2 2v4h4V4h-4zM2 14h8v8H2v-8zm2 2v4h4v-4H4zm10 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-2 2h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 0h2v2h-2v-2zm2-2h2v2h-2v-2zm-6-4h2v2h-2v-2zm4 4h2v2h-2v-2zM5 5h2v2H5V5zm12 0h2v2h-2V5zM5 17h2v2H5v-2z"/>
                          </svg>
                        </div>
                        <span class="text-[8px] text-slate-400 leading-tight">Digital Report Verification</span>
                      </div>
                    </div>

                    <!-- Right: Barcode & Dates -->
                    <div class="col-span-3 text-right space-y-0.5">
                      <div v-if="themeOptions.showQrAndBarcode" class="flex justify-end">
                        <div class="flex flex-col items-end">
                          <svg class="h-6 w-24" viewBox="0 0 100 24">
                            <rect x="0" y="0" width="2" height="24" fill="#0f172a"/><rect x="4" y="0" width="1" height="24" fill="#0f172a"/><rect x="7" y="0" width="3" height="24" fill="#0f172a"/><rect x="13" y="0" width="1" height="24" fill="#0f172a"/><rect x="16" y="0" width="4" height="24" fill="#0f172a"/><rect x="23" y="0" width="2" height="24" fill="#0f172a"/><rect x="27" y="0" width="1" height="24" fill="#0f172a"/><rect x="31" y="0" width="3" height="24" fill="#0f172a"/><rect x="37" y="0" width="2" height="24" fill="#0f172a"/><rect x="42" y="0" width="4" height="24" fill="#0f172a"/><rect x="49" y="0" width="1" height="24" fill="#0f172a"/><rect x="53" y="0" width="3" height="24" fill="#0f172a"/><rect x="59" y="0" width="2" height="24" fill="#0f172a"/><rect x="64" y="0" width="4" height="24" fill="#0f172a"/><rect x="71" y="0" width="2" height="24" fill="#0f172a"/><rect x="76" y="0" width="1" height="24" fill="#0f172a"/><rect x="80" y="0" width="3" height="24" fill="#0f172a"/><rect x="86" y="0" width="2" height="24" fill="#0f172a"/><rect x="91" y="0" width="3" height="24" fill="#0f172a"/>
                          </svg>
                          <span class="text-[7.5px] font-mono text-slate-500">{{ samplePatient.barcode }}</span>
                        </div>
                      </div>
                      <div><span class="text-slate-400">Reg:</span> <strong>{{ samplePatient.registeredAt.split(' ')[0] }}</strong></div>
                      <div><span class="text-slate-400">Coll:</span> <strong>{{ samplePatient.collectedAt.split(' ')[0] }}</strong></div>
                      <div><span class="text-slate-400">Rep:</span> <strong>{{ samplePatient.reportedAt.split(' ')[0] }}</strong></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- THEME 2: HEALTHPLUS CLINICAL NAVY                    -->
              <!-- ==================================================== -->
              <div v-else-if="currentThemeId === 'healthplus'" class="space-y-3 z-10 relative">
                <!-- Header with Navy Right Box -->
                <div class="flex items-start justify-between border-b pb-2">
                  <div class="flex items-center space-x-2.5">
                    <div class="w-12 h-12 rounded-full bg-[#0c3b5e] text-white flex items-center justify-center p-2 shrink-0 shadow-xs">
                      <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" /></svg>
                    </div>
                    <div>
                      <h1 class="text-base font-extrabold text-[#0c3b5e] tracking-tight uppercase">{{ labIdentity.labName }}</h1>
                      <p class="text-[9.5px] text-slate-500">{{ labIdentity.address }}</p>
                      <p class="text-[9px] text-slate-400 font-mono">Tel: {{ labIdentity.phoneNumbers }} &bull; {{ labIdentity.email }}</p>
                    </div>
                  </div>

                  <div class="bg-[#0c3b5e] text-white px-3 py-1.5 rounded text-right shrink-0">
                    <span class="block text-[8.5px] text-sky-200 font-semibold tracking-wider uppercase">Accredited Diagnostics</span>
                    <strong class="text-xs font-bold block">{{ labIdentity.tagline }}</strong>
                  </div>
                </div>

                <!-- Full-Width Navy Title Bar -->
                <div class="bg-[#0c3b5e] text-white text-center py-1 rounded text-xs font-bold tracking-wider uppercase">
                  CBC (COMPLETE BLOOD COUNT) &bull; AUTOMATED HEMATOLOGY
                </div>

                <!-- Rounded Card Grid for Patient Info -->
                <div class="bg-[#f8fafc] border border-slate-200 rounded-lg p-2.5 text-[9.5px]">
                  <div class="grid grid-cols-12 gap-2 items-center">
                    <div class="col-span-9 grid grid-cols-3 gap-2">
                      <div><span class="text-slate-400 block text-[8.5px]">PATIENT NAME</span><strong>{{ samplePatient.name }}</strong></div>
                      <div><span class="text-slate-400 block text-[8.5px]">AGE / GENDER</span><strong>{{ samplePatient.ageGender }}</strong></div>
                      <div><span class="text-slate-400 block text-[8.5px]">SAMPLE TYPE</span><strong>{{ samplePatient.sampleType }}</strong></div>
                      <div><span class="text-slate-400 block text-[8.5px]">COLLECTION DATE</span><strong>{{ samplePatient.collectedAt }}</strong></div>
                      <div><span class="text-slate-400 block text-[8.5px]">REPORTING DATE</span><strong>{{ samplePatient.reportedAt }}</strong></div>
                      <div><span class="text-slate-400 block text-[8.5px]">REFERRED BY</span><strong>{{ samplePatient.referredBy }}</strong></div>
                    </div>
                    <div v-if="themeOptions.showQrAndBarcode" class="col-span-3 border-l border-slate-200 pl-2 text-center">
                      <div class="w-10 h-10 mx-auto bg-white border border-slate-300 p-0.5 rounded flex items-center justify-center">
                        <svg class="w-9 h-9 text-slate-800" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M2 2h8v8H2V2zm2 2v4h4V4H4zm10-2h8v8h-8V2zm2 2v4h4V4h-4zM2 14h8v8H2v-8zm2 2v4h4v-4H4zm10 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-2 2h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 0h2v2h-2v-2zm2-2h2v2h-2v-2zm-6-4h2v2h-2v-2zm4 4h2v2h-2v-2zM5 5h2v2H5V5zm12 0h2v2h-2V5zM5 17h2v2H5v-2z"/>
                        </svg>
                      </div>
                      <span class="text-[7.5px] font-bold text-[#0c3b5e] uppercase mt-0.5 block">Scan to Verify</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- THEME 3: MEDICORE ECO GREEN                          -->
              <!-- ==================================================== -->
              <div v-else-if="currentThemeId === 'medicore'" class="space-y-3 z-10 relative">
                <!-- Eco Green Header -->
                <div class="border-b-2 border-emerald-600 pb-2">
                  <div class="flex items-start justify-between">
                    <div class="flex items-center space-x-2.5">
                      <div class="w-11 h-11 rounded-full bg-emerald-50 border border-emerald-400 text-emerald-600 flex items-center justify-center shrink-0">
                        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66l.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z"/>
                        </svg>
                      </div>
                      <div>
                        <h1 class="text-base font-extrabold text-emerald-800 tracking-tight">{{ labIdentity.labName }}</h1>
                        <p class="text-[9.5px] text-emerald-700 font-medium">{{ labIdentity.tagline }}</p>
                        <p class="text-[9px] text-slate-500">{{ labIdentity.address }}</p>
                      </div>
                    </div>

                    <div class="text-right shrink-0">
                      <div class="inline-flex items-center space-x-1.5 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded text-[8.5px] text-emerald-800 font-bold">
                        <span>ISO 15189:2022</span>
                        <span>&bull;</span>
                        <span>IAF ACCREDITED</span>
                      </div>
                      <p class="text-[8px] text-slate-400 mt-0.5">Govt. Reg No: NABL-MC-8821</p>
                    </div>
                  </div>

                  <!-- Thin Green Contact Strip -->
                  <div class="mt-1.5 bg-emerald-700 text-white px-2 py-0.5 rounded-xs flex items-center justify-between text-[8.5px] font-mono">
                    <span>Email: {{ labIdentity.email }}</span>
                    <span>Helpline: {{ labIdentity.phoneNumbers }}</span>
                    <span>Timings: 07:00 AM - 09:00 PM</span>
                  </div>
                </div>

                <!-- 2-Column Key-Value Patient Grid with Top/Bottom Borders -->
                <div class="border-y border-emerald-200 py-1.5 text-[9.5px]">
                  <div class="grid grid-cols-2 gap-x-6 gap-y-1">
                    <div class="flex justify-between border-b border-slate-100 pb-0.5"><span class="text-slate-500">Patient Name:</span> <strong>{{ samplePatient.name }}</strong></div>
                    <div class="flex justify-between border-b border-slate-100 pb-0.5"><span class="text-slate-500">UHID / Reg No:</span> <strong class="font-mono text-emerald-800">{{ samplePatient.pid }}</strong></div>
                    <div class="flex justify-between border-b border-slate-100 pb-0.5"><span class="text-slate-500">Age &amp; Gender:</span> <strong>{{ samplePatient.ageGender }}</strong></div>
                    <div class="flex justify-between border-b border-slate-100 pb-0.5"><span class="text-slate-500">Referred By:</span> <strong>{{ samplePatient.referredBy }}</strong></div>
                    <div class="flex justify-between"><span class="text-slate-500">Sample Collected:</span> <span>{{ samplePatient.collectedAt }}</span></div>
                    <div class="flex justify-between"><span class="text-slate-500">Report Released:</span> <span>{{ samplePatient.reportedAt }}</span></div>
                  </div>
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- THEME 4: GURU VERTICAL SIDEBAR                       -->
              <!-- ==================================================== -->
              <div v-else-if="currentThemeId === 'guru'" class="relative pl-7 space-y-3 z-10">
                <!-- Vertical Sidebar Dark Blue Strip -->
                <div class="absolute left-0 top-0 bottom-0 w-5 bg-[#0f2942] rounded-l flex items-center justify-center text-white select-none overflow-hidden">
                  <div
                    class="font-black text-[9px] tracking-widest uppercase whitespace-nowrap"
                    :style="{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }"
                  >
                    PATHOLOGY LAB REPORT &bull; DIAGNOSTIC RECORD
                  </div>
                </div>

                <!-- Guru Header -->
                <div class="border-b pb-2">
                  <div class="text-center">
                    <h1 class="text-base font-extrabold text-[#0f2942] uppercase tracking-wide">{{ labIdentity.labName }}</h1>
                    <p class="text-[9.5px] text-slate-500">{{ labIdentity.address }} &bull; Ph: {{ labIdentity.phoneNumbers }}</p>
                  </div>

                  <!-- Horizontal Navy Bar with Centered Pill -->
                  <div class="mt-2 bg-[#0f2942] h-4 rounded-sm relative flex items-center justify-center">
                    <span class="bg-white text-[#0f2942] border border-[#0f2942] text-[8.5px] font-bold px-3 py-0.2 rounded-full uppercase tracking-wider">
                      INVESTIGATION REPORT
                    </span>
                  </div>
                </div>

                <!-- Bordered Patient Box -->
                <div class="border border-slate-300 rounded p-2 text-[9.5px] bg-slate-50/50">
                  <div class="grid grid-cols-12 gap-2">
                    <div class="col-span-5 space-y-0.5">
                      <div><span class="text-slate-400">Name:</span> <strong class="text-slate-900">{{ samplePatient.name }}</strong></div>
                      <div><span class="text-slate-400">Age/Sex:</span> <strong>{{ samplePatient.ageGender }}</strong></div>
                      <div><span class="text-slate-400">PID:</span> <strong class="font-mono text-blue-900">{{ samplePatient.pid }}</strong></div>
                    </div>
                    <div v-if="themeOptions.showQrAndBarcode" class="col-span-3 flex items-center justify-center border-x border-slate-200">
                      <div class="w-9 h-9 bg-white border border-slate-300 p-0.5 rounded">
                        <svg class="w-full h-full text-slate-800" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M2 2h8v8H2V2zm2 2v4h4V4H4zm10-2h8v8h-8V2zm2 2v4h4V4h-4zM2 14h8v8H2v-8zm2 2v4h4v-4H4zm10 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-2 2h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 0h2v2h-2v-2zm2-2h2v2h-2v-2zm-6-4h2v2h-2v-2zm4 4h2v2h-2v-2zM5 5h2v2H5V5zm12 0h2v2h-2V5zM5 17h2v2H5v-2z"/>
                        </svg>
                      </div>
                    </div>
                    <div class="col-span-4 text-right space-y-0.5">
                      <div><span class="text-slate-400">Ref:</span> <strong>{{ samplePatient.referredBy }}</strong></div>
                      <div><span class="text-slate-400">Date:</span> <strong>{{ samplePatient.collectedAt.split(' ')[0] }}</strong></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- THEME 5: VARAD CLASSIC DOCTOR LETTERHEAD             -->
              <!-- ==================================================== -->
              <div v-else-if="currentThemeId === 'varad'" class="space-y-3 z-10 relative">
                <!-- Classic Doctor Letterhead Header -->
                <div class="border-b-2 border-red-900 pb-2">
                  <div class="flex items-start justify-between">
                    <div>
                      <h1 class="text-lg font-serif font-bold text-red-950 tracking-tight">{{ labIdentity.labName }}</h1>
                      <p class="text-[10px] text-slate-600 font-serif italic">{{ labIdentity.tagline }}</p>
                      <p class="text-[9px] text-slate-500 mt-0.5 font-serif">{{ labIdentity.address }}</p>
                    </div>

                    <div class="text-right font-serif text-[9.5px]">
                      <strong class="text-red-900 block font-bold text-xs">Dr. Payal Shah</strong>
                      <span class="text-slate-600 block">M.B.B.S., M.D. (Pathology)</span>
                      <span class="text-slate-500 block">Reg. No: MCI-48921</span>
                      <span class="text-slate-500 block">Mobile: {{ labIdentity.phoneNumbers.split('/')[0] }}</span>
                    </div>
                  </div>
                </div>

                <!-- Colon-Aligned Classic Patient Block -->
                <div class="border-y border-slate-300 py-1.5 text-[10px] font-serif uppercase tracking-wider">
                  <div class="grid grid-cols-2 gap-x-8 gap-y-0.5">
                    <div><span class="inline-block w-20 text-slate-500">NAME</span>: <strong>{{ samplePatient.name }}</strong></div>
                    <div><span class="inline-block w-20 text-slate-500">REF BY</span>: <strong>{{ samplePatient.referredBy }}</strong></div>
                    <div><span class="inline-block w-20 text-slate-500">AGE / SEX</span>: <strong>{{ samplePatient.ageGender }}</strong></div>
                    <div><span class="inline-block w-20 text-slate-500">DATE</span>: <strong>{{ samplePatient.collectedAt.split(' ')[0] }}</strong></div>
                  </div>
                </div>

                <!-- Centered Underlined Test Name -->
                <div class="text-center font-serif py-1">
                  <span class="text-xs font-bold uppercase tracking-widest border-b border-slate-900 pb-0.5">
                    COMPLETE BLOOD COUNT (CBC)
                  </span>
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- THEME 6: DRAGONHEALTH GOLD & CHARCOAL                -->
              <!-- ==================================================== -->
              <div v-else-if="currentThemeId === 'dragon'" class="space-y-3 z-10 relative">
                <!-- Split Charcoal / Gold Header -->
                <div class="rounded overflow-hidden shadow-xs">
                  <div class="bg-[#1e293b] text-white px-3 py-2 flex items-center justify-between">
                    <div class="flex items-center space-x-2.5">
                      <div class="w-10 h-10 rounded-full border-2 border-[#eab308] flex items-center justify-center font-black text-[#eab308] text-xs">
                        DH
                      </div>
                      <div>
                        <h1 class="text-sm font-black uppercase tracking-wider text-white">{{ labIdentity.labName }}</h1>
                        <p class="text-[9px] text-slate-300">{{ labIdentity.tagline }}</p>
                      </div>
                    </div>
                    <span class="text-[9px] font-mono text-[#eab308] border border-[#eab308] px-2 py-0.5 rounded">
                      DIAGNOSTIC REPORT
                    </span>
                  </div>
                  <!-- Bright Gold Ribbon -->
                  <div class="bg-[#eab308] text-[#1e293b] px-3 py-1 text-[9px] font-semibold flex items-center justify-between">
                    <span>{{ labIdentity.address }}</span>
                    <span>Contact: {{ labIdentity.phoneNumbers }}</span>
                  </div>
                </div>

                <!-- Patient Demographic Strip -->
                <div class="bg-slate-50 border border-slate-200 p-2 rounded text-[9.5px]">
                  <div class="grid grid-cols-4 gap-2">
                    <div><span class="text-slate-400 block text-[8px]">PATIENT</span><strong>{{ samplePatient.name }}</strong></div>
                    <div><span class="text-slate-400 block text-[8px]">AGE / SEX</span><strong>{{ samplePatient.ageGender }}</strong></div>
                    <div><span class="text-slate-400 block text-[8px]">PATIENT ID</span><strong class="font-mono">{{ samplePatient.pid }}</strong></div>
                    <div><span class="text-slate-400 block text-[8px]">REF DOCTOR</span><strong>{{ samplePatient.referredBy }}</strong></div>
                  </div>
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- SHARED TEST RESULTS INVESTIGATION TABLE              -->
              <!-- ==================================================== -->
              <div class="my-3 z-10 relative">
                <!-- HealthPlus Navy or Standard Header -->
                <table class="w-full text-[9.5px] border-collapse">
                  <thead>
                    <tr
                      :class="[
                        'border-b text-slate-700 font-bold',
                        currentThemeId === 'healthplus'
                          ? 'bg-[#0c3b5e] text-white'
                          : currentThemeId === 'medicore'
                            ? 'bg-emerald-50 text-emerald-900 border-emerald-300'
                            : currentThemeId === 'dragon'
                              ? 'bg-slate-100 text-slate-900 border-slate-300'
                              : 'bg-slate-100/80 border-slate-200'
                      ]"
                    >
                      <th class="py-1 px-2 text-left">INVESTIGATION PARAMETER</th>
                      <th class="py-1 px-2 text-right">OBSERVED VALUE</th>
                      <th class="py-1 px-2 text-center">UNIT</th>
                      <th class="py-1 px-2 text-right">REFERENCE RANGE</th>
                      <th class="py-1 px-2 text-center">FLAG</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    <tr
                      v-for="(row, idx) in sampleParameters"
                      :key="row.name"
                      :class="[
                        currentThemeId === 'healthplus' && idx % 2 === 1 ? 'bg-slate-50/70' : ''
                      ]"
                    >
                      <td class="py-1 px-2 font-medium text-slate-800">{{ row.name }}</td>
                      <td class="py-1 px-2 text-right font-mono font-bold" :class="row.isAbnormal ? 'text-red-700 font-black' : 'text-slate-900'">
                        {{ row.result }}
                      </td>
                      <td class="py-1 px-2 text-center font-mono text-slate-500 text-[8.5px]">{{ row.unit }}</td>
                      <td class="py-1 px-2 text-right font-mono text-slate-600 text-[8.5px]">{{ row.range }}</td>
                      <td class="py-1 px-2 text-center">
                        <span
                          v-if="row.isAbnormal"
                          class="inline-block px-1.5 py-0.2 rounded text-[8px] font-bold font-mono bg-red-100 text-red-800 border border-red-200"
                        >
                          {{ row.flag }}
                        </span>
                        <span v-else class="text-emerald-700 font-mono text-[8.5px] font-medium">
                          Normal
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>

                <!-- Inline Barcode under MediCore Table -->
                <div v-if="currentThemeId === 'medicore' && themeOptions.showQrAndBarcode" class="mt-2 pt-1 border-t border-slate-200 flex items-center justify-between text-[8px] text-slate-400">
                  <span>Method: Automated 5-Part Cell Counter (Impedance &amp; Flow Cytometry)</span>
                  <div class="flex items-center space-x-1">
                    <svg class="h-4 w-20" viewBox="0 0 80 18">
                      <rect x="0" y="0" width="2" height="18" fill="#1e293b"/><rect x="4" y="0" width="1" height="18" fill="#1e293b"/><rect x="7" y="0" width="3" height="18" fill="#1e293b"/><rect x="13" y="0" width="1" height="18" fill="#1e293b"/><rect x="16" y="0" width="4" height="18" fill="#1e293b"/><rect x="23" y="0" width="2" height="18" fill="#1e293b"/><rect x="27" y="0" width="1" height="18" fill="#1e293b"/><rect x="31" y="0" width="3" height="18" fill="#1e293b"/><rect x="37" y="0" width="2" height="18" fill="#1e293b"/><rect x="42" y="0" width="4" height="18" fill="#1e293b"/><rect x="49" y="0" width="1" height="18" fill="#1e293b"/><rect x="54" y="0" width="3" height="18" fill="#1e293b"/><rect x="61" y="0" width="2" height="18" fill="#1e293b"/><rect x="66" y="0" width="4" height="18" fill="#1e293b"/><rect x="73" y="0" width="2" height="18" fill="#1e293b"/>
                    </svg>
                    <span class="font-mono">{{ samplePatient.barcode }}</span>
                  </div>
                </div>

                <!-- Pathologist Remarks Note -->
                <div class="mt-2.5 p-2 rounded bg-slate-50 border border-slate-200 text-[9px] text-slate-600">
                  <strong class="text-slate-800">Clinical Interpretation:</strong>
                  Mild neutrophilic leukocytosis observed. Correlate with clinical symptoms and repeat if advised.
                </div>
              </div>

              <!-- ==================================================== -->
              <!-- PRE-PRINTED STATIONERY BOTTOM MARGIN PLACEHOLDER     -->
              <!-- ==================================================== -->
              <div
                v-if="themeOptions.letterheadMode === 'preprinted'"
                class="border-2 border-dashed border-amber-300 bg-amber-50/60 rounded p-2 mt-3 text-center text-amber-800 text-[10px] font-mono flex items-center justify-center"
                :style="{ height: `${themeOptions.preprintedBottomMarginMm * 2.8}px` }"
              >
                [ RESERVED BOTTOM {{ themeOptions.preprintedBottomMarginMm }}MM FOR PRE-PRINTED FOOTER ]
              </div>

              <!-- ==================================================== -->
              <!-- THEME-SPECIFIC FOOTERS & SIGNATORIES                 -->
              <!-- ==================================================== -->
              <div v-else class="mt-4 pt-2 border-t border-slate-200 z-10 relative">
                <!-- 3 Signatures Row -->
                <div class="grid grid-cols-3 gap-3 mb-2 text-center text-[9px]">
                  <div
                    v-for="(sig, idx) in signatories.filter(s => s.enabled)"
                    :key="sig.id"
                    :class="[
                      idx === 0 ? 'text-left' : idx === 1 ? 'text-center' : 'text-right'
                    ]"
                  >
                    <!-- Signature Image or Elegant Cursive Fallback -->
                    <div class="h-9 flex items-end justify-center mb-0.5" :class="idx === 0 ? 'justify-start' : idx === 1 ? 'justify-center' : 'justify-end'">
                      <img
                        v-if="sig.signatureImageUrl"
                        :src="sig.signatureImageUrl"
                        alt="Signature"
                        class="h-full max-w-[100px] object-contain"
                      />
                      <div v-else class="font-serif italic text-blue-950 text-xs border-b border-slate-300 px-3 pb-0.2">
                        {{ sig.name }}
                      </div>
                    </div>
                    <strong class="block text-slate-900 leading-tight">{{ sig.name }}</strong>
                    <span class="text-slate-500 block text-[8px] leading-tight">{{ sig.qualification }}</span>
                    <span class="text-slate-400 block text-[7.5px] leading-tight">{{ sig.designation }}</span>
                    <span v-if="sig.regNo" class="text-slate-400 block text-[7.5px] font-mono leading-tight">{{ sig.regNo }}</span>
                  </div>
                </div>

                <!-- Divider: **** End of Report **** -->
                <div class="text-center text-[8.5px] font-bold text-slate-400 tracking-widest my-1.5 uppercase">
                  &bull;&bull;&bull;&bull; End of Diagnostic Report &bull;&bull;&bull;&bull;
                </div>

                <!-- Theme 1 Footer: Drlogy Bottom Ribbon with Scooter & WhatsApp -->
                <div
                  v-if="currentThemeId === 'drlogy'"
                  class="bg-blue-600 text-white rounded p-1.5 flex items-center justify-between text-[8.5px] overflow-hidden"
                >
                  <div class="flex items-center space-x-1.5">
                    <!-- Delivery Scooter Icon -->
                    <svg class="w-4 h-4 text-white inline-block" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="6" cy="18" r="3" /><circle cx="18" cy="18" r="3" />
                      <path d="M6 18h12M9 18l1.5-6h4l1.5 6M8 8h5l2 4H9z" />
                    </svg>
                    <span class="font-bold tracking-wide">Sample Collection at Home:</span>
                  </div>

                  <!-- WhatsApp Number -->
                  <div class="flex items-center space-x-1 font-mono font-bold">
                    <svg class="w-3.5 h-3.5 text-emerald-300 fill-current" viewBox="0 0 24 24">
                      <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0012.04 2zm0 18.06c-1.48 0-2.93-.4-4.2-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.106 8.106 0 01-1.24-4.29c0-4.5 3.66-8.16 8.16-8.16 2.18 0 4.23.85 5.77 2.39a8.118 8.118 0 012.39 5.77c0 4.5-3.66 8.15-8.16 8.15z"/>
                    </svg>
                    <span>{{ labIdentity.homeCollectionPhone }}</span>
                  </div>

                  <!-- Diagonal Pattern on Far Right -->
                  <div class="flex items-center space-x-1 opacity-70">
                    <svg width="30" height="10">
                      <defs>
                        <pattern id="drlogy-stripes-footer" width="5" height="5" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                          <line x1="0" y1="0" x2="0" y2="5" stroke="#000" stroke-width="2" />
                        </pattern>
                      </defs>
                      <rect width="30" height="10" fill="url(#drlogy-stripes-footer)" />
                    </svg>
                  </div>
                </div>

                <!-- Theme 2 Footer: HealthPlus Clinical Navy Bottom Bar -->
                <div
                  v-else-if="currentThemeId === 'healthplus'"
                  class="bg-[#0c3b5e] text-white p-1 rounded-xs flex items-center justify-between text-[8px] font-sans"
                >
                  <span>Trusted Results for Better Health &bull; Correlate Clinically</span>
                  <span class="font-mono">Page 1 of 1</span>
                </div>

                <!-- Theme 3 Footer: MediCore Scooter & E-Report QR -->
                <div
                  v-else-if="currentThemeId === 'medicore'"
                  class="border-t border-emerald-500 pt-1.5 flex items-center justify-between text-[8.5px] text-emerald-900"
                >
                  <div class="flex items-center space-x-1.5">
                    <svg class="w-4 h-4 text-emerald-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="6" cy="18" r="3" /><circle cx="18" cy="18" r="3" />
                      <path d="M6 18h12M9 18l1.5-6h4l1.5 6M8 8h5l2 4H9z" />
                    </svg>
                    <span>Home Sample Collection Available: <strong>{{ labIdentity.homeCollectionPhone }}</strong></span>
                  </div>
                  <span class="text-[7.5px] font-mono text-slate-400">E-Report Verification Active</span>
                </div>

                <!-- Theme 4 Footer: Guru Dual-Tone Bar (Blue / Magenta) -->
                <div
                  v-else-if="currentThemeId === 'guru'"
                  class="flex items-stretch rounded-sm overflow-hidden text-white text-[8px] font-bold"
                >
                  <div class="bg-[#0f2942] px-3 py-1 flex-1 flex items-center justify-between">
                    <span>PATH LAB 2.0 ADVANCED DIAGNOSTICS</span>
                    <span>Home Collection Available</span>
                  </div>
                  <div class="bg-pink-600 px-3 py-1 flex items-center space-x-1">
                    <span>Contact:</span>
                    <span class="font-mono">{{ labIdentity.homeCollectionPhone }}</span>
                  </div>
                </div>

                <!-- Theme 5 Footer: Varad Red/Blue Border & Legal Notice -->
                <div
                  v-else-if="currentThemeId === 'varad'"
                  class="border-t-2 border-red-900 pt-1 text-center font-serif text-[8px] text-slate-500"
                >
                  Tests performed on calibrated analyzers. For clinical consultation only. Not for medico-legal purpose.
                </div>

                <!-- Theme 6 Footer: DragonHealth Gold Bottom Strip -->
                <div
                  v-else-if="currentThemeId === 'dragon'"
                  class="border-t-2 border-[#eab308] pt-1 flex items-center justify-between text-[8px] text-slate-500 font-serif"
                >
                  <span>DragonHealth Automated Laboratory Network</span>
                  <span class="font-mono">CLIA / CAP Accredited Equivalent</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- TAB 2: TEST CATALOG & MASTER TEMPLATES                   -->
    <!-- ======================================================== -->
    <div v-else-if="activePageTab === 'catalog'" class="space-y-4">
      <!-- Search & Filters -->
      <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div class="flex items-center space-x-2 flex-1 min-w-[260px] max-w-lg">
          <div class="relative flex-1">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              v-model="catalogSearch"
              type="search"
              placeholder="Search master templates by code, investigation name, department..."
              class="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <select
            v-model="catalogCategory"
            class="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs text-slate-700 cursor-pointer focus:outline-none font-semibold"
          >
            <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
      </div>

      <!-- Catalog Cards Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <div
          v-for="tpl in filteredCatalog"
          :key="tpl.id"
          class="bg-white rounded-lg border border-slate-200 hover:border-blue-400 hover:shadow-md transition p-4 flex flex-col justify-between"
        >
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[10px] font-mono font-bold text-blue-700 uppercase bg-blue-50 px-1.5 py-0.5 rounded">
                {{ tpl.code }}
              </span>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full border bg-emerald-50 text-emerald-700 border-emerald-200">
                {{ tpl.status }}
              </span>
            </div>
            <h3 class="text-sm font-bold text-slate-900">{{ tpl.title }}</h3>
            <p class="text-xs text-slate-500 mt-0.5">Discipline: {{ tpl.category }} &bull; Preset Layout: <strong class="text-slate-700 uppercase">{{ tpl.layout }}</strong></p>
          </div>

          <div class="pt-3 border-t border-slate-100 mt-4 flex items-center justify-between text-xs">
            <span class="text-[11px] text-slate-400">Ready to Print</span>
            <button
              type="button"
              class="px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded font-medium cursor-pointer shadow-2xs"
              @click="applyTemplateTheme(tpl.layout)"
            >
              Open in Theme Customizer
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media print {
  body * {
    visibility: hidden;
  }
  #a4-report-canvas,
  #a4-report-canvas * {
    visibility: visible;
  }
  #a4-report-canvas {
    position: absolute;
    left: 0;
    top: 0;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 10mm !important;
    box-shadow: none !important;
    border: none !important;
  }
}
</style>
