<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlatformStore, type PlatformPlan, type TenantLab, type BlogPost, type PlatformTransaction } from '~/composables/usePlatformStore'
import { useAdminAuth } from '~/composables/useAdminAuth'
import { useToast } from '~/composables/useToast'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import Icon from '~/components/ui/Icon.vue'
import Card from '~/components/ui/Card.vue'
import Modal from '~/components/ui/Modal.vue'

definePageMeta({
  layout: 'admin',
})

const { currentAdmin, isAuthenticated, logout: adminLogout } = useAdminAuth()

const route = useRoute()
const router = useRouter()

const {
  plans,
  tenantLabs,
  blogPosts,
  windowsRelease,
  transactions,
  initStore,
  savePlans,
  saveTenantLabs,
  saveBlogPosts,
  saveWindowsRelease,
  saveTransactions,
  generateLicense,
} = usePlatformStore()

const { success, info, warning } = useToast()

const validTabs = ['plans', 'labs', 'license-gen', 'transactions', 'blog', 'release'] as const
type AdminTab = typeof validTabs[number]

const activeTab = ref<AdminTab>('plans')

function setTab(tab: AdminTab) {
  activeTab.value = tab
  router.replace({ query: { ...route.query, tab } })
}

watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab && validTabs.includes(newTab as AdminTab)) {
      activeTab.value = newTab as AdminTab
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (!isAuthenticated.value) {
    navigateTo('/admin/login')
    return
  }
  initStore()
  if (route.query.tab && validTabs.includes(route.query.tab as AdminTab)) {
    activeTab.value = route.query.tab as AdminTab
  }
})

// --------------------------------------------------------------------------
// 1. PLANS & PRICING MANAGEMENT
// --------------------------------------------------------------------------
const isEditPlanModalOpen = ref(false)
const editingPlan = ref<PlatformPlan | null>(null)

function openEditPlan(p: PlatformPlan) {
  editingPlan.value = JSON.parse(JSON.stringify(p))
  isEditPlanModalOpen.value = true
}

function saveEditedPlan() {
  if (!editingPlan.value) return
  const idx = plans.value.findIndex(p => p.id === editingPlan.value?.id)
  if (idx !== -1) {
    plans.value[idx] = { ...editingPlan.value }
    savePlans()
    success('Plan Updated', `Plan "${editingPlan.value.name}" updated and live on /pricing.`)
  }
  isEditPlanModalOpen.value = false
}

// --------------------------------------------------------------------------
// 2. TENANT LABORATORIES MANAGEMENT
// --------------------------------------------------------------------------
const isAddLabModalOpen = ref(false)
const newLab = ref({
  name: '',
  ownerName: '',
  email: '',
  phone: '',
  city: '',
  state: '',
  planCode: 'YEARLY_PRO',
  workstationsQuota: 6,
})

function handleCreateLab() {
  if (!newLab.value.name.trim() || !newLab.value.email.trim()) {
    warning('Missing Info', 'Lab Name and Email are required.')
    return
  }

  const generated = generateLicense({
    labName: newLab.value.name,
    planCode: newLab.value.planCode,
    workstationsQuota: newLab.value.workstationsQuota,
    validDays: 365,
    features: ['pathology', 'radiology', 'billing', 'barcode', 'qc'],
  })

  const createdLab: TenantLab = {
    id: `lab_${Date.now()}`,
    name: newLab.value.name.trim(),
    ownerName: newLab.value.ownerName.trim() || 'Laboratory Director',
    email: newLab.value.email.trim(),
    phone: newLab.value.phone.trim() || '+91 90000 00000',
    city: newLab.value.city.trim() || 'New Delhi',
    state: newLab.value.state.trim() || 'Delhi',
    planCode: newLab.value.planCode,
    workstationsQuota: newLab.value.workstationsQuota,
    joinedDate: new Date().toISOString().slice(0, 10),
    licenseId: generated.licenseId,
    licenseValidTo: generated.validTo,
    status: 'ACTIVE',
  }

  tenantLabs.value.unshift(createdLab)
  saveTenantLabs()
  success('Tenant Lab Created', `${createdLab.name} registered and issued license ${generated.licenseId}.`)
  isAddLabModalOpen.value = false

  newLab.value = {
    name: '',
    ownerName: '',
    email: '',
    phone: '',
    city: '',
    state: '',
    planCode: 'YEARLY_PRO',
    workstationsQuota: 6,
  }
}

function toggleLabStatus(lab: TenantLab) {
  lab.status = lab.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE'
  saveTenantLabs()
  info('Status Updated', `Lab ${lab.name} marked as ${lab.status}.`)
}

// --------------------------------------------------------------------------
// 3. CRYPTOGRAPHIC LICENSE GENERATOR
// --------------------------------------------------------------------------
const licenseForm = ref({
  labName: 'Shree Krishna Diagnostics & Imaging',
  planCode: 'YEARLY_PRO',
  workstationsQuota: 5,
  validDays: 365,
  hardwareId: '',
  features: ['pathology', 'radiology', 'billing', 'barcode', 'qc'],
})

const generatedLicenseOutput = ref<{
  licenseId: string
  validTo: string
  licenseJson: string
} | null>(null)

function handleGenerateLicense() {
  if (!licenseForm.value.labName.trim()) {
    warning('Missing Lab Name', 'Please specify the target laboratory name.')
    return
  }

  const res = generateLicense({
    labName: licenseForm.value.labName,
    planCode: licenseForm.value.planCode,
    workstationsQuota: licenseForm.value.workstationsQuota,
    validDays: licenseForm.value.validDays,
    hardwareId: licenseForm.value.hardwareId,
    features: licenseForm.value.features,
  })

  generatedLicenseOutput.value = res
  success('License Generated', `Cryptographically signed license ID: ${res.licenseId}`)
}

function downloadGeneratedLicenseFile() {
  if (!generatedLicenseOutput.value) return
  const blob = new Blob([generatedLicenseOutput.value.licenseJson], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `aarozi_${generatedLicenseOutput.value.licenseId.toLowerCase()}.license`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  success('Downloaded', 'License file saved to disk.')
}

// --------------------------------------------------------------------------
// 4. BLOG / CMS MANAGEMENT
// --------------------------------------------------------------------------
const isBlogModalOpen = ref(false)
const blogForm = ref<BlogPost>({
  id: '',
  slug: '',
  title: '',
  excerpt: '',
  content: '',
  category: 'Quality & NABL',
  author: 'Dr. Aarozi Editorial Team',
  readTime: '5 min read',
  date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
  published: true,
})

function openNewBlogPostModal() {
  blogForm.value = {
    id: `post_${Date.now()}`,
    slug: '',
    title: '',
    excerpt: '',
    content: '',
    category: 'Quality & NABL',
    author: 'Dr. Aarozi Editorial Team',
    readTime: '5 min read',
    date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
    published: true,
  }
  isBlogModalOpen.value = true
}

function handleSaveBlogPost() {
  if (!blogForm.value.title.trim() || !blogForm.value.content.trim()) {
    warning('Missing Details', 'Title and Content are required.')
    return
  }

  if (!blogForm.value.slug.trim()) {
    blogForm.value.slug = blogForm.value.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
  }

  const existingIdx = blogPosts.value.findIndex(p => p.id === blogForm.value.id)
  if (existingIdx !== -1) {
    blogPosts.value[existingIdx] = { ...blogForm.value }
    success('Article Updated', `"${blogForm.value.title}" updated on /blog.`)
  } else {
    blogPosts.value.unshift({ ...blogForm.value })
    success('Article Published', `"${blogForm.value.title}" is now live on /blog.`)
  }

  saveBlogPosts()
  isBlogModalOpen.value = false
}

function deleteBlogPost(id: string) {
  blogPosts.value = blogPosts.value.filter(p => p.id !== id)
  saveBlogPosts()
  info('Post Deleted', 'Article removed from public knowledge hub.')
}

// --------------------------------------------------------------------------
// 5. WINDOWS INSTALLER RELEASE MANAGEMENT
// --------------------------------------------------------------------------
function saveReleaseConfig() {
  saveWindowsRelease()
  success('Release Config Saved', `Windows installer info updated live on /download and /account/downloads.`)
}
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto pb-16 text-slate-900 dark:text-slate-100">
    <!-- Executive Summary Strip -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
      <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Tenant Labs</span>
        <div class="text-xl font-black text-slate-900 dark:text-white mt-1">{{ tenantLabs.length }} Laboratories</div>
        <span class="text-[10px] text-emerald-600 font-bold">100% Offline Activated</span>
      </div>

      <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Active Plans</span>
        <div class="text-xl font-black text-slate-900 dark:text-white mt-1">{{ plans.length }} Subscription Tiers</div>
        <span class="text-[10px] text-[#2576d2] font-bold">Live on /pricing</span>
      </div>

      <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Desktop Release</span>
        <div class="text-xl font-black text-slate-900 dark:text-white mt-1">{{ windowsRelease.version }}</div>
        <span class="text-[10px] text-emerald-600 font-bold">SHA-256 Verified</span>
      </div>

      <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">YTD Platform Revenue</span>
        <div class="text-xl font-black text-[#1c5fae] dark:text-[#90ccf9] mt-1">₹{{ transactions.reduce((acc, t) => acc + t.amountInr, 0).toLocaleString('en-IN', { maximumFractionDigits: 0 }) }}</div>
        <span class="text-[10px] text-slate-500 font-medium">Razorpay + GST</span>
      </div>
    </div>

    <!-- Navigation Control Tabs -->
    <div class="flex items-center space-x-2 overflow-x-auto border-b border-[#ede9f7] dark:border-[#23273e] pb-2">
      <button
        type="button"
        :class="[
          'px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 shrink-0 select-none',
          activeTab === 'plans'
            ? 'bg-[#2576d2] text-white shadow-xs'
            : 'text-slate-600 dark:text-slate-300 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d]'
        ]"
        @click="setTab('plans')"
      >
        <Icon name="tag" size="xs" />
        <span>Plans &amp; Pricing ({{ plans.length }})</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 shrink-0 select-none',
          activeTab === 'labs'
            ? 'bg-[#2576d2] text-white shadow-xs'
            : 'text-slate-600 dark:text-slate-300 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d]'
        ]"
        @click="setTab('labs')"
      >
        <Icon name="home" size="xs" />
        <span>Tenant Laboratories ({{ tenantLabs.length }})</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 shrink-0 select-none',
          activeTab === 'license-gen'
            ? 'bg-[#2576d2] text-white shadow-xs'
            : 'text-slate-600 dark:text-slate-300 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d]'
        ]"
        @click="setTab('license-gen')"
      >
        <Icon name="shield" size="xs" />
        <span>License Generator</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 shrink-0 select-none',
          activeTab === 'transactions'
            ? 'bg-[#2576d2] text-white shadow-xs'
            : 'text-slate-600 dark:text-slate-300 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d]'
        ]"
        @click="setTab('transactions')"
      >
        <Icon name="credit-card" size="xs" />
        <span>Payments &amp; GST Invoices ({{ transactions.length }})</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 shrink-0 select-none',
          activeTab === 'blog'
            ? 'bg-[#2576d2] text-white shadow-xs'
            : 'text-slate-600 dark:text-slate-300 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d]'
        ]"
        @click="setTab('blog')"
      >
        <Icon name="book-open" size="xs" />
        <span>Blog &amp; Knowledge CMS ({{ blogPosts.length }})</span>
      </button>

      <button
        type="button"
        :class="[
          'px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 shrink-0 select-none',
          activeTab === 'release'
            ? 'bg-[#2576d2] text-white shadow-xs'
            : 'text-slate-600 dark:text-slate-300 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d]'
        ]"
        @click="setTab('release')"
      >
        <Icon name="download" size="xs" />
        <span>Windows Desktop .exe Release</span>
      </button>
    </div>

    <!-- TAB 1: PLANS & PRICING -->
    <div v-if="activeTab === 'plans'" class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Active Subscription Plans</h2>
          <p class="text-xs text-slate-500">Changes here immediately reflect on public page /pricing and customer checkout.</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          v-for="p in plans"
          :key="p.id"
          class="rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-6 shadow-sm flex flex-col justify-between space-y-5"
        >
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono font-bold text-[#2576d2] dark:text-[#90ccf9]">{{ p.code }}</span>
              <Badge v-if="p.popular" variant="warning" size="sm">Most Popular</Badge>
            </div>

            <h3 class="text-xl font-black text-slate-900 dark:text-white">{{ p.name }}</h3>
            <p class="text-xs text-slate-500 leading-relaxed">{{ p.description }}</p>

            <div class="pt-2 border-t border-[#ede9f7] dark:border-[#23273e]">
              <div class="flex items-baseline space-x-1">
                <span class="text-2xl font-black text-slate-900 dark:text-white">₹{{ p.monthlyPrice.toLocaleString('en-IN') }}</span>
                <span class="text-xs text-slate-500">/ month</span>
              </div>
              <div class="text-[11px] font-semibold text-[#b73612] dark:text-[#fdb99b]">
                ₹{{ p.yearlyPrice.toLocaleString('en-IN') }} billed yearly
              </div>
            </div>

            <div class="space-y-1.5 pt-2">
              <div class="text-xs font-bold text-slate-700 dark:text-slate-300">
                LAN Workstations Quota: <span class="font-mono text-[#2576d2]">{{ p.workstationsLimit >= 900 ? 'Unlimited' : p.workstationsLimit }}</span>
              </div>
              <ul class="text-xs text-slate-600 dark:text-slate-400 space-y-1 pt-1">
                <li v-for="feat in p.features" :key="feat" class="flex items-start gap-1.5">
                  <span class="text-emerald-500 font-bold shrink-0">✓</span>
                  <span>{{ feat }}</span>
                </li>
              </ul>
            </div>
          </div>

          <div class="pt-4 border-t border-[#ede9f7] dark:border-[#23273e]">
            <Button variant="secondary" size="sm" full-width @click="openEditPlan(p)">
              <template #icon-left><Icon name="edit" size="xs" /></template>
              <span>Edit Plan &amp; Pricing</span>
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: TENANT LABORATORIES -->
    <div v-if="activeTab === 'labs'" class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Registered Customer Laboratories</h2>
          <p class="text-xs text-slate-500">Every laboratory licensed to run the offline LIS desktop application.</p>
        </div>
        <Button variant="primary" size="sm" @click="isAddLabModalOpen = true">
          <template #icon-left><Icon name="plus" size="xs" /></template>
          <span>Register &amp; License New Lab</span>
        </Button>
      </div>

      <div class="rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="bg-[#f0f7fe]/60 dark:bg-[#1d273d]/60 border-b border-[#ede9f7] dark:border-[#23273e] text-slate-600 dark:text-slate-400 font-bold">
                <th class="py-3 px-6">Laboratory Name &amp; City</th>
                <th class="py-3 px-6">Director / Owner</th>
                <th class="py-3 px-6">Plan &amp; Quota</th>
                <th class="py-3 px-6">License ID</th>
                <th class="py-3 px-6">Expiry</th>
                <th class="py-3 px-6">Status</th>
                <th class="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#ede9f7] dark:divide-[#23273e]">
              <tr v-for="lab in tenantLabs" :key="lab.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                <td class="py-3.5 px-6">
                  <div class="font-bold text-slate-900 dark:text-white">{{ lab.name }}</div>
                  <div class="text-[11px] text-slate-500">{{ lab.city }}, {{ lab.state }}</div>
                </td>
                <td class="py-3.5 px-6">
                  <div class="font-medium text-slate-800 dark:text-slate-200">{{ lab.ownerName }}</div>
                  <div class="text-[11px] text-slate-500 font-mono">{{ lab.email }} &bull; {{ lab.phone }}</div>
                </td>
                <td class="py-3.5 px-6">
                  <span class="px-2 py-0.5 rounded font-bold text-[10px] bg-[#f0f7fe] dark:bg-[#1d273d] text-[#1c5fae] dark:text-[#90ccf9]">
                    {{ lab.planCode }}
                  </span>
                  <div class="text-[11px] text-slate-500 mt-0.5">Quota: {{ lab.workstationsQuota }} LAN PCs</div>
                </td>
                <td class="py-3.5 px-6 font-mono font-bold text-slate-800 dark:text-slate-200">
                  {{ lab.licenseId }}
                </td>
                <td class="py-3.5 px-6 font-mono text-slate-600 dark:text-slate-400">
                  {{ lab.licenseValidTo }}
                </td>
                <td class="py-3.5 px-6">
                  <Badge :variant="lab.status === 'ACTIVE' ? 'success' : 'danger'" size="sm">
                    {{ lab.status }}
                  </Badge>
                </td>
                <td class="py-3.5 px-6 text-right">
                  <button
                    type="button"
                    class="text-xs font-bold text-[#2576d2] dark:text-[#90ccf9] hover:underline cursor-pointer"
                    @click="toggleLabStatus(lab)"
                  >
                    {{ lab.status === 'ACTIVE' ? 'Suspend' : 'Activate' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 3: CRYPTOGRAPHIC LICENSE GENERATOR -->
    <div v-if="activeTab === 'license-gen'" class="space-y-6">
      <div>
        <h2 class="text-lg font-bold text-slate-900 dark:text-white">Cryptographic Offline License Key Generator</h2>
        <p class="text-xs text-slate-500">
          Generate digitally signed Ed25519 software licences that activate offline LIS installations with zero cloud connection.
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div class="lg:col-span-7 rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-6 shadow-sm space-y-4">
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">License Parameters</h3>

          <div class="space-y-3 text-xs">
            <div>
              <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Target Laboratory Name *</label>
              <input
                v-model="licenseForm.labName"
                type="text"
                class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-[#3b93ee]"
                placeholder="e.g. Apex Diagnostics & Imaging Center"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Subscription Plan Code</label>
                <select
                  v-model="licenseForm.planCode"
                  class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-[#3b93ee]"
                >
                  <option v-for="p in plans" :key="p.code" :value="p.code">{{ p.name }} ({{ p.code }})</option>
                </select>
              </div>

              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Workstations LAN Quota</label>
                <input
                  v-model.number="licenseForm.workstationsQuota"
                  type="number"
                  min="1"
                  class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-[#3b93ee]"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Validity Duration (Days)</label>
                <select
                  v-model.number="licenseForm.validDays"
                  class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-[#3b93ee]"
                >
                  <option :value="14">14 Days (Free Trial)</option>
                  <option :value="30">30 Days (Monthly)</option>
                  <option :value="365">365 Days (1 Year)</option>
                  <option :value="730">730 Days (2 Years)</option>
                  <option :value="3650">3650 Days (10 Years / Perpetual)</option>
                </select>
              </div>

              <div>
                <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Hardware Fingerprint ID (Optional)</label>
                <input
                  v-model="licenseForm.hardwareId"
                  type="text"
                  placeholder="e.g. HW-89F4-A012 or leave empty for Any"
                  class="w-full px-3 py-2 border rounded-lg font-mono bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-[#3b93ee]"
                />
              </div>
            </div>

            <div class="pt-2">
              <Button variant="primary" size="md" full-width @click="handleGenerateLicense">
                <template #icon-left><Icon name="shield" size="xs" /></template>
                <span>Generate Signed .license</span>
              </Button>
            </div>
          </div>
        </div>

        <!-- Generated Output Box -->
        <div class="lg:col-span-5 rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-6 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-900 dark:text-white">Generated License Output</h3>
            <span v-if="generatedLicenseOutput" class="text-[11px] font-bold text-emerald-600">Signed ✓</span>
          </div>

          <div v-if="generatedLicenseOutput" class="space-y-3">
            <div class="p-3 rounded-xl bg-[#f0f7fe] dark:bg-[#1d273d] border border-[#bee1fb] dark:border-[#2576d2]/50 text-xs">
              <div class="text-[11px] text-slate-500">License ID:</div>
              <div class="font-mono font-bold text-base text-[#1c5fae] dark:text-[#90ccf9]">
                {{ generatedLicenseOutput.licenseId }}
              </div>
              <div class="text-[11px] text-slate-500 mt-1">Valid Until: {{ generatedLicenseOutput.validTo }}</div>
            </div>

            <div class="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-[10px] max-h-56 overflow-y-auto whitespace-pre-wrap">
              {{ generatedLicenseOutput.licenseJson }}
            </div>

            <Button variant="primary" size="sm" full-width @click="downloadGeneratedLicenseFile">
              <template #icon-left><Icon name="download" size="xs" /></template>
              <span>Download aarozi.license File</span>
            </Button>
          </div>

          <div v-else class="py-16 text-center text-xs text-slate-400">
            Click "Generate Signed .license" on the left to create and download the cryptographic key file.
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 4: BLOG & KNOWLEDGE CMS -->
    <div v-if="activeTab === 'blog'" class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Knowledge Hub &amp; Blog CMS</h2>
          <p class="text-xs text-slate-500">Articles published here appear live on the public marketing page (/blog).</p>
        </div>
        <Button variant="primary" size="sm" @click="openNewBlogPostModal">
          <template #icon-left><Icon name="plus" size="xs" /></template>
          <span>Write New Article</span>
        </Button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div
          v-for="post in blogPosts"
          :key="post.id"
          class="rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-6 shadow-sm flex flex-col justify-between space-y-4"
        >
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs">
              <span class="px-2.5 py-0.5 rounded-full font-bold bg-[#f0f7fe] dark:bg-[#1d273d] text-[#1c5fae] dark:text-[#90ccf9]">
                {{ post.category }}
              </span>
              <span class="text-slate-400">{{ post.date }}</span>
            </div>

            <h3 class="text-base font-bold text-slate-900 dark:text-white leading-snug">
              {{ post.title }}
            </h3>

            <p class="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
              {{ post.excerpt }}
            </p>
          </div>

          <div class="pt-4 border-t border-[#ede9f7] dark:border-[#23273e] flex items-center justify-between">
            <div class="text-[11px] text-slate-400 font-medium">By {{ post.author }}</div>
            <div class="flex items-center space-x-2">
              <NuxtLink :to="`/blog/${post.slug}`" class="text-xs font-bold text-[#2576d2] hover:underline">
                View Live &rarr;
              </NuxtLink>
              <button
                type="button"
                class="text-xs font-bold text-red-600 hover:underline cursor-pointer"
                @click="deleteBlogPost(post.id)"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 5: WINDOWS DESKTOP .EXE RELEASE -->
    <div v-if="activeTab === 'release'" class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div class="flex items-center space-x-2">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white">Windows Installer (.exe) Release Distribution</h2>
            <Badge variant="success" size="sm">Live Serving</Badge>
          </div>
          <p class="text-xs text-slate-500">
            Configure and test the official Windows desktop release served to customers upon software purchase on /download and /account/downloads.
          </p>
        </div>

        <!-- Quick Action Links -->
        <div class="flex items-center space-x-2">
          <NuxtLink to="/download" target="_blank">
            <Button variant="secondary" size="xs">
              <template #icon-left><Icon name="external-link" size="xs" /></template>
              <span>Public /download</span>
            </Button>
          </NuxtLink>

          <NuxtLink to="/account/downloads" target="_blank">
            <Button variant="secondary" size="xs">
              <template #icon-left><Icon name="external-link" size="xs" /></template>
              <span>Customer /account/downloads</span>
            </Button>
          </NuxtLink>

          <a :href="windowsRelease.downloadUrl" download>
            <Button variant="primary" size="xs">
              <template #icon-left><Icon name="download" size="xs" /></template>
              <span>Test Download .exe</span>
            </Button>
          </a>
        </div>
      </div>

      <!-- Release Configuration Card -->
      <div class="rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-6 sm:p-8 shadow-sm space-y-6">
        <div class="flex items-center justify-between border-b pb-4 border-[#ede9f7] dark:border-[#23273e]">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-2xl bg-[#f0f7fe] dark:bg-[#1d273d] text-[#2576d2] dark:text-[#90ccf9] flex items-center justify-center font-bold">
              <Icon name="download" size="sm" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-900 dark:text-white">Active Production Build Configuration</h3>
              <p class="text-[11px] text-slate-400">Settings below immediately update the customer download experience</p>
            </div>
          </div>

          <div class="text-right">
            <span class="text-[10px] text-slate-400 block font-mono">STATUS</span>
            <span class="inline-flex items-center space-x-1 text-xs font-bold text-emerald-600">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Available for Download</span>
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Release Version Tag</label>
            <input
              v-model="windowsRelease.version"
              type="text"
              class="w-full px-3 py-2 border rounded-xl bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-bold"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Release Date</label>
            <input
              v-model="windowsRelease.releaseDate"
              type="text"
              class="w-full px-3 py-2 border rounded-xl bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">File Size</label>
            <input
              v-model="windowsRelease.fileSize"
              type="text"
              class="w-full px-3 py-2 border rounded-xl bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div class="text-xs space-y-4">
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="font-bold text-slate-700 dark:text-slate-300">Download URL / Path (.exe)</label>
              <span class="text-[10px] text-slate-400">Serves directly from local /downloads or cloud CDN</span>
            </div>
            <input
              v-model="windowsRelease.downloadUrl"
              type="text"
              class="w-full px-3 py-2 border rounded-xl font-mono text-xs bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="font-bold text-slate-700 dark:text-slate-300">SHA-256 Checksum (Cryptographic Integrity)</label>
              <button
                type="button"
                class="text-[11px] font-bold text-[#2576d2] dark:text-[#90ccf9] hover:underline cursor-pointer"
                @click="windowsRelease.sha256 = '5a5a7291adae8c58ecc861841ad64af8a6c972a737d65c725d0e6f319ef85fb8'"
              >
                Set Production SHA-256
              </button>
            </div>
            <input
              v-model="windowsRelease.sha256"
              type="text"
              class="w-full px-3 py-2 border rounded-xl font-mono text-xs bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div class="pt-2 flex items-center justify-between">
          <div class="text-xs text-slate-400 flex items-center space-x-1.5">
            <Icon name="shield-check" size="xs" class="text-emerald-500" />
            <span>Target OS: {{ windowsRelease.targetOS || 'Windows 10 / 11 (64-bit)' }}</span>
          </div>

          <Button variant="primary" size="md" @click="saveReleaseConfig">
            <template #icon-left><Icon name="check" size="xs" /></template>
            <span>Save &amp; Publish Windows Release Info</span>
          </Button>
        </div>
      </div>

      <!-- Real Downloadable Assets Table -->
      <div class="rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-6 sm:p-8 shadow-sm space-y-4">
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">Active Windows Deployment Packages Served</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-[#ede9f7] dark:border-[#23273e] text-slate-400 font-semibold">
                <th class="py-2.5 px-3">PACKAGE NAME</th>
                <th class="py-2.5 px-3">FORMAT</th>
                <th class="py-2.5 px-3">FILE PATH</th>
                <th class="py-2.5 px-3">INTEGRITY</th>
                <th class="py-2.5 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#ede9f7] dark:divide-[#23273e]">
              <tr>
                <td class="py-3 px-3 font-bold text-slate-900 dark:text-white">
                  Aarozi Master LIS Installer (.exe)
                  <Badge variant="info" size="xs" class="ml-2">Recommended</Badge>
                </td>
                <td class="py-3 px-3 text-slate-500">Windows Setup Executable</td>
                <td class="py-3 px-3 font-mono text-[11px] text-slate-600 dark:text-slate-300">/downloads/Aarozi-LIS-Setup-v2.4.0.exe</td>
                <td class="py-3 px-3 font-mono text-[10px] text-emerald-600">5a5a7291...fb8</td>
                <td class="py-3 px-3 text-right">
                  <a href="/downloads/Aarozi-LIS-Setup-v2.4.0.exe" download>
                    <Button variant="primary" size="xs">
                      <template #icon-left><Icon name="download" size="xs" /></template>
                      <span>Download</span>
                    </Button>
                  </a>
                </td>
              </tr>
              <tr>
                <td class="py-3 px-3 font-bold text-slate-900 dark:text-white">
                  Aarozi Portable ZIP Package
                </td>
                <td class="py-3 px-3 text-slate-500">Portable .zip Archive</td>
                <td class="py-3 px-3 font-mono text-[11px] text-slate-600 dark:text-slate-300">/downloads/Aarozi-LIS-Portable-v2.4.0.zip</td>
                <td class="py-3 px-3 font-mono text-[10px] text-emerald-600">e205f8cd...8ad</td>
                <td class="py-3 px-3 text-right">
                  <a href="/downloads/Aarozi-LIS-Portable-v2.4.0.zip" download>
                    <Button variant="secondary" size="xs">
                      <template #icon-left><Icon name="download" size="xs" /></template>
                      <span>Download</span>
                    </Button>
                  </a>
                </td>
              </tr>
              <tr>
                <td class="py-3 px-3 font-bold text-slate-900 dark:text-white">
                  Master PC Background Service Script
                </td>
                <td class="py-3 px-3 text-slate-500">PowerShell / Batch Script</td>
                <td class="py-3 px-3 font-mono text-[11px] text-slate-600 dark:text-slate-300">/downloads/register-aarozi-service.bat</td>
                <td class="py-3 px-3 font-mono text-[10px] text-emerald-600">66aa6eb3...377</td>
                <td class="py-3 px-3 text-right">
                  <a href="/downloads/register-aarozi-service.bat" download>
                    <Button variant="secondary" size="xs">
                      <template #icon-left><Icon name="download" size="xs" /></template>
                      <span>Download</span>
                    </Button>
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Complete Customer Onboarding Journey Explanation -->
      <div class="rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-slate-50 dark:bg-slate-900/60 p-6 sm:p-8 space-y-4">
        <div class="flex items-center space-x-2">
          <Icon name="sparkles" size="xs" class="text-[#2576d2]" />
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">How Windows Desktop .exe Distribution Works</h3>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-1.5 shadow-2xs">
            <span class="w-6 h-6 rounded-full bg-[#2576d2] text-white font-bold flex items-center justify-center text-[10px]">1</span>
            <div class="font-bold text-slate-900 dark:text-white">Customer Buys Plan</div>
            <p class="text-slate-500 text-[11px] leading-relaxed">
              Customer selects Monthly Solo or Yearly Pro on <NuxtLink to="/pricing" class="text-[#2576d2] font-semibold hover:underline">/pricing</NuxtLink> and completes Razorpay payment.
            </p>
          </div>

          <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-1.5 shadow-2xs">
            <span class="w-6 h-6 rounded-full bg-[#2576d2] text-white font-bold flex items-center justify-center text-[10px]">2</span>
            <div class="font-bold text-slate-900 dark:text-white">Instant .exe Download</div>
            <p class="text-slate-500 text-[11px] leading-relaxed">
              Customer logs into <NuxtLink to="/account/downloads" class="text-[#2576d2] font-semibold hover:underline">/account/downloads</NuxtLink> or <NuxtLink to="/download" class="text-[#2576d2] font-semibold hover:underline">/download</NuxtLink> and downloads the Windows installer.
            </p>
          </div>

          <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-1.5 shadow-2xs">
            <span class="w-6 h-6 rounded-full bg-[#2576d2] text-white font-bold flex items-center justify-center text-[10px]">3</span>
            <div class="font-bold text-slate-900 dark:text-white">Runs on Master PC</div>
            <p class="text-slate-500 text-[11px] leading-relaxed">
              Installer sets up the local encrypted SQLite DB and launches the LIS locally on <code class="font-mono text-[#2576d2]">http://localhost:3000</code> with zero cloud requirement.
            </p>
          </div>

          <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-1.5 shadow-2xs">
            <span class="w-6 h-6 rounded-full bg-[#2576d2] text-white font-bold flex items-center justify-center text-[10px]">4</span>
            <div class="font-bold text-slate-900 dark:text-white">Offline .lic Activation</div>
            <p class="text-slate-500 text-[11px] leading-relaxed">
              Customer downloads their signed <code class="font-mono text-[#2576d2]">aarozi.license</code> from their portal and uploads it locally to unlock all features.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 6: TRANSACTIONS & GST INVOICES -->
    <div v-if="activeTab === 'transactions'" class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Commercial Billing &amp; GST Invoices</h2>
          <p class="text-xs text-slate-500">Live Razorpay webhook transactions, GST breakdowns, and tax invoices.</p>
        </div>
      </div>

      <!-- Financial Metrics Summary -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-1">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Gross Platform Revenue</span>
          <div class="text-2xl font-black text-[#1c5fae] dark:text-[#90ccf9]">
            ₹{{ transactions.reduce((acc, t) => acc + t.amountInr, 0).toLocaleString('en-IN', { maximumFractionDigits: 2 }) }}
          </div>
          <span class="text-[10px] text-emerald-600 font-semibold">100% Verified Razorpay Webhooks</span>
        </div>

        <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-1">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total GST Collected (18%)</span>
          <div class="text-2xl font-black text-slate-800 dark:text-white">
            ₹{{ transactions.reduce((acc, t) => acc + t.gstAmountInr, 0).toLocaleString('en-IN', { maximumFractionDigits: 2 }) }}
          </div>
          <span class="text-[10px] text-slate-500">9% CGST + 9% SGST / IGST</span>
        </div>

        <div class="p-4 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-1">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Active Subscriptions</span>
          <div class="text-2xl font-black text-slate-800 dark:text-white">
            {{ transactions.filter(t => t.paymentStatus === 'PAID').length }} Labs
          </div>
          <span class="text-[10px] text-[#2576d2] font-semibold">Automated Ed25519 Dispatched</span>
        </div>
      </div>

      <!-- Transactions Ledger Table -->
      <div class="bg-white dark:bg-[#15182a] rounded-2xl border border-[#ede9f7] dark:border-[#23273e] overflow-hidden shadow-xs">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse text-xs">
            <thead>
              <tr class="bg-slate-50/80 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 border-b border-[#ede9f7] dark:border-[#23273e]">
                <th class="py-3 px-4 font-bold">Invoice &amp; Order ID</th>
                <th class="py-3 px-4 font-bold">Laboratory Name</th>
                <th class="py-3 px-4 font-bold">Plan Tier</th>
                <th class="py-3 px-4 font-bold">Tender / Mode</th>
                <th class="py-3 px-4 font-bold">Gross Total</th>
                <th class="py-3 px-4 font-bold">Status</th>
                <th class="py-3 px-4 font-bold">Payment Date</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#ede9f7] dark:divide-[#23273e]">
              <tr
                v-for="tx in transactions"
                :key="tx.id"
                class="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
              >
                <td class="py-3 px-4 font-mono font-bold text-slate-900 dark:text-white">
                  <div>{{ tx.invoiceNumber }}</div>
                  <div class="text-[10px] text-slate-400 font-normal">{{ tx.orderId }}</div>
                </td>
                <td class="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">
                  {{ tx.labName }}
                </td>
                <td class="py-3 px-4">
                  <span class="px-2 py-0.5 rounded-md font-mono text-[10px] font-bold bg-[#f0f7fe] dark:bg-[#1d273d] text-[#1c5fae] dark:text-[#90ccf9]">
                    {{ tx.planCode }}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {{ tx.paymentMethod }}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <div class="font-bold text-slate-900 dark:text-white">
                    ₹{{ tx.amountInr.toLocaleString('en-IN', { maximumFractionDigits: 2 }) }}
                  </div>
                  <div class="text-[10px] text-slate-400">
                    Base: ₹{{ tx.taxableAmountInr }} + GST: ₹{{ tx.gstAmountInr }}
                  </div>
                </td>
                <td class="py-3 px-4">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                    {{ tx.paymentStatus }}
                  </span>
                </td>
                <td class="py-3 px-4 text-slate-500 font-mono text-[11px]">
                  {{ new Date(tx.paidAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- MODAL: EDIT PLAN -->
    <Modal
      v-model="isEditPlanModalOpen"
      title="Edit Subscription Plan"
      description="Modify plan pricing, workstation quotas and feature highlights."
      size="md"
    >
      <div v-if="editingPlan" class="space-y-4 text-xs">
        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Plan Display Name</label>
          <input
            v-model="editingPlan.name"
            type="text"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Monthly Price (₹)</label>
            <input
              v-model.number="editingPlan.monthlyPrice"
              type="number"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Yearly Price (₹)</label>
            <input
              v-model.number="editingPlan.yearlyPrice"
              type="number"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Workstations Quota Limit</label>
          <input
            v-model.number="editingPlan.workstationsLimit"
            type="number"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
          />
        </div>

        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Short Description</label>
          <input
            v-model="editingPlan.description"
            type="text"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
          />
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <Button variant="secondary" size="sm" @click="close">Cancel</Button>
          <Button variant="primary" size="sm" @click="saveEditedPlan">Save Changes</Button>
        </div>
      </template>
    </Modal>

    <!-- MODAL: REGISTER NEW LAB -->
    <Modal
      v-model="isAddLabModalOpen"
      title="Register &amp; License New Laboratory"
      description="Create a new laboratory record and automatically generate its offline activation key."
      size="md"
    >
      <div class="space-y-3.5 text-xs">
        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Laboratory / Diagnostic Center Name *</label>
          <input
            v-model="newLab.name"
            type="text"
            placeholder="e.g. LifeCare Diagnostic Hub"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Owner / Director Name</label>
            <input
              v-model="newLab.ownerName"
              type="text"
              placeholder="e.g. Dr. Anil Verma"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Email Address *</label>
            <input
              v-model="newLab.email"
              type="email"
              placeholder="lab@example.com"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Contact Phone</label>
            <input
              v-model="newLab.phone"
              type="tel"
              placeholder="+91 98765 00000"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">City</label>
            <input
              v-model="newLab.city"
              type="text"
              placeholder="e.g. Pune"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Subscription Plan</label>
            <select
              v-model="newLab.planCode"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            >
              <option v-for="p in plans" :key="p.code" :value="p.code">{{ p.name }}</option>
            </select>
          </div>
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Workstation Quota</label>
            <input
              v-model.number="newLab.workstationsQuota"
              type="number"
              min="1"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <Button variant="secondary" size="sm" @click="close">Cancel</Button>
          <Button variant="primary" size="sm" @click="handleCreateLab">Register &amp; Issue License</Button>
        </div>
      </template>
    </Modal>

    <!-- MODAL: WRITE / EDIT BLOG POST -->
    <Modal
      v-model="isBlogModalOpen"
      title="Write / Edit Knowledge Article"
      description="Create clinical or operational guides visible on the public /blog hub."
      size="lg"
    >
      <div class="space-y-3.5 text-xs">
        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Article Title *</label>
          <input
            v-model="blogForm.title"
            type="text"
            placeholder="e.g. How to Standardize IQC Levey-Jennings Plots in LIS"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Category</label>
            <select
              v-model="blogForm.category"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            >
              <option value="Quality & NABL">Quality &amp; NABL</option>
              <option value="Architecture & Tech">Architecture &amp; Tech</option>
              <option value="Lab Operations">Lab Operations</option>
              <option value="Radiology & Imaging">Radiology &amp; Imaging</option>
              <option value="Billing & Finance">Billing &amp; Finance</option>
            </select>
          </div>
          <div>
            <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Author Name</label>
            <input
              v-model="blogForm.author"
              type="text"
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Short Excerpt / Summary *</label>
          <textarea
            v-model="blogForm.excerpt"
            rows="2"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            placeholder="Brief 1-2 sentence preview for search results and social cards..."
          />
        </div>

        <div>
          <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Full Article Content (Markdown / Text) *</label>
          <textarea
            v-model="blogForm.content"
            rows="6"
            class="w-full px-3 py-2 border rounded-lg font-mono bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            placeholder="Write full guide, sections, checklists..."
          />
        </div>
      </div>

      <template #footer="{ close }">
        <div class="flex items-center justify-between w-full">
          <Button variant="secondary" size="sm" @click="close">Cancel</Button>
          <Button variant="primary" size="sm" @click="handleSaveBlogPost">Publish to /blog</Button>
        </div>
      </template>
    </Modal>
  </div>
</template>

