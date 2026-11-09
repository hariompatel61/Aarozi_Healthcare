<script setup lang="ts">
import { ref } from 'vue'
import Button from '~/components/ui/Button.vue'
import IconButton from '~/components/ui/IconButton.vue'
import Input from '~/components/ui/Input.vue'
import NumberInput from '~/components/ui/NumberInput.vue'
import Select from '~/components/ui/Select.vue'
import SegmentedControl from '~/components/ui/SegmentedControl.vue'
import Checkbox from '~/components/ui/Checkbox.vue'
import Switch from '~/components/ui/Switch.vue'
import FormField from '~/components/ui/FormField.vue'
import SearchField from '~/components/ui/SearchField.vue'
import Badge from '~/components/ui/Badge.vue'
import Chip from '~/components/ui/Chip.vue'
import Card from '~/components/ui/Card.vue'
import StatCard from '~/components/ui/StatCard.vue'
import DataTable, { type ColumnDef } from '~/components/ui/DataTable.vue'
import FilterBar from '~/components/ui/FilterBar.vue'
import Tabs from '~/components/ui/Tabs.vue'
import PageHeader from '~/components/ui/PageHeader.vue'
import Drawer from '~/components/ui/Drawer.vue'
import Modal from '~/components/ui/Modal.vue'
import ConfirmDialog from '~/components/ui/ConfirmDialog.vue'
import Skeleton from '~/components/ui/Skeleton.vue'
import EmptyState from '~/components/ui/EmptyState.vue'
import Kbd from '~/components/ui/Kbd.vue'
import Icon from '~/components/ui/Icon.vue'
import PaginationBar from '~/components/ui/PaginationBar.vue'
import { useToast } from '~/composables/useToast'

definePageMeta({
  layout: false, // Standalone preview kitchen sink
})

const { success, error, warning, info } = useToast()

// Theme State
const isDark = ref(false)
function toggleTheme() {
  isDark.value = !isDark.value
  if (typeof document !== 'undefined') {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      document.documentElement.removeAttribute('data-theme')
    }
  }
}

// Active Kitchen Sink Section
const activeSection = ref('buttons')
const sectionTabs = [
  { id: 'tokens', label: '1. Tokens & Typography' },
  { id: 'buttons', label: '2. Buttons & Actions' },
  { id: 'forms', label: '3. Form Inputs & Selects' },
  { id: 'badges', label: '4. Badges, Chips & KPIs' },
  { id: 'table', label: '5. Dense Clinical Table' },
  { id: 'overlays', label: '6. Modals, Drawers & Toasts' },
]

// Form Test States
const sampleText = ref('Aarav Sharma')
const sampleNumber = ref(12.5)
const sampleCurrency = ref(1450)
const sampleSelect = ref('CBC')
const selectOptions = [
  { label: 'Complete Blood Count (CBC)', value: 'CBC', badge: 'Routine', description: 'Hemoglobin, RBC, WBC, Platelets' },
  { label: 'Lipid Profile Screen', value: 'LIPID', badge: 'Special', description: 'Total Cholesterol, HDL, LDL, Triglycerides' },
  { label: 'Liver Function Test (LFT)', value: 'LFT', badge: 'Profile', description: 'Bilirubin, SGOT, SGPT, Alkaline Phosphatase' },
  { label: 'HbA1c Glycated Hemoglobin', value: 'HBA1C', badge: 'HPLC', description: 'Diabetes monitoring HPLC 3-month average' },
  { label: 'Serum Ferritin', value: 'FERRITIN', badge: 'CLIA', description: 'Chemiluminescence Immunoassay' },
]

const sampleSegment = ref('daily')
const segmentOptions = [
  { label: 'Today', value: 'daily', badge: 48 },
  { label: 'This Week', value: 'weekly', badge: 312 },
  { label: 'Monthly Summary', value: 'monthly' },
]

const paymentSegment = ref('cash')
const paymentOptions = [
  { label: 'Cash (POS)', value: 'cash' },
  { label: 'UPI / QR', value: 'upi' },
  { label: 'Credit/Debit Card', value: 'card' },
]

const sampleCheckbox = ref(true)
const sampleSwitch = ref(true)
const sampleSearch = ref('')
const activeFilterChip = ref('all')

// Table State
const isDense = ref(true)
const isZebra = ref(false)
const isTableLoading = ref(false)
const isTableEmpty = ref(false)
const selectedTableKeys = ref<string[]>(['SMP2601'])

const tableColumns: ColumnDef[] = [
  { key: 'sample_id', label: 'Sample ID', sortable: true, width: '120px' },
  { key: 'patient_name', label: 'Patient & UHID', sortable: true },
  { key: 'test_name', label: 'Investigation / Test', sortable: true },
  { key: 'result', label: 'Observed Result', align: 'right' },
  { key: 'status', label: 'Status Flag', align: 'center', width: '130px' },
  { key: 'tat', label: 'Turnaround Time', align: 'right', width: '120px' },
]

const mockTableData = [
  {
    sample_id: 'SMP2601',
    patient_name: 'Vikramaditya Roy (UHID-1082)',
    test_name: 'HbA1c (HPLC Method)',
    result: '11.8 %',
    status: 'Panic High',
    statusVariant: 'panic',
    tat: '32 mins ago',
  },
  {
    sample_id: 'SMP2602',
    patient_name: 'Meera Deshmukh (UHID-1083)',
    test_name: 'Complete Blood Count (CBC)',
    result: 'Hb 13.4 g/dL',
    status: 'Verified',
    statusVariant: 'success',
    tat: '45 mins ago',
  },
  {
    sample_id: 'SMP2603',
    patient_name: 'Arjun Singhania (UHID-1084)',
    test_name: 'Serum Bilirubin (Total)',
    result: '2.8 mg/dL',
    status: 'Abnormal',
    statusVariant: 'warning',
    tat: '1 hr ago',
  },
  {
    sample_id: 'SMP2604',
    patient_name: 'Pooja Bhatt (UHID-1085)',
    test_name: 'Thyroid Panel (TSH, T3, T4)',
    result: 'Pending Analyzer',
    status: 'In Process',
    statusVariant: 'info',
    tat: '1.2 hrs ago',
  },
  {
    sample_id: 'SMP2605',
    patient_name: 'Rajesh Nair (UHID-1086)',
    test_name: 'Serum Creatinine',
    result: '0.9 mg/dL',
    status: 'Normal',
    statusVariant: 'neutral',
    tat: '2 hrs ago',
  },
]

// Modal & Drawer State
const isModalOpen = ref(false)
const isDrawerOpen = ref(false)
const isConfirmOpen = ref(false)
</script>

<template>
  <div :class="['min-h-screen font-sans transition-colors', isDark ? 'dark bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900']">
    <!-- Top System Bar -->
    <header class="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-3 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <NuxtLink to="/dashboard" class="flex items-center space-x-2 text-slate-800 dark:text-slate-200 hover:text-teal-600 transition-colors">
          <div class="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold text-sm shadow-xs">
            AH
          </div>
          <div>
            <div class="font-bold text-sm tracking-tight leading-none">Aarozi Healthcare LIS</div>
            <div class="text-[11px] text-slate-400 mt-0.5">Design System & Component Kitchen Sink</div>
          </div>
        </NuxtLink>
        <span class="text-slate-300 dark:text-slate-700">|</span>
        <Badge variant="success" size="sm" dot>Phase 1 Verified</Badge>
        <Badge variant="neutral" size="sm">W3C 3-Tier Tokens</Badge>
      </div>

      <div class="flex items-center space-x-3">
        <!-- Theme Toggle -->
        <Button
          variant="secondary"
          size="sm"
          @click="toggleTheme"
        >
          <template #icon-left>
            <Icon :name="isDark ? 'sparkles' : 'activity'" size="xs" />
          </template>
          {{ isDark ? 'Light Theme' : 'Dark Theme' }}
        </Button>

        <NuxtLink to="/dashboard">
          <Button variant="primary" size="sm">
            <template #icon-left>
              <Icon name="arrow-left" size="xs" />
            </template>
            Back to App
          </Button>
        </NuxtLink>
      </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 text-left">
      <!-- Page Navigation Tabs -->
      <Tabs
        v-model="activeSection"
        :tabs="sectionTabs"
        variant="pill"
        size="md"
      />

      <!-- ================================================================== -->
      <!-- SECTION 1: TOKENS & TYPOGRAPHY -->
      <!-- ================================================================== -->
      <section v-if="activeSection === 'tokens'" class="space-y-6">
        <PageHeader
          title="Design Tokens & Typography Scale"
          subtitle="W3C Category-Property-Variant-State 3-tier token architecture with a strict 12px minimum baseline."
        />

        <!-- Brand Color Swatches -->
        <Card title="Brand & Semantic Color Palettes" subtitle="Global primitive values mapped into theme-safe semantic CSS variables.">
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <!-- Teal -->
            <div class="p-3 rounded-lg border border-teal-200 dark:border-teal-800 bg-teal-50 dark:bg-teal-950/40">
              <div class="h-10 rounded bg-teal-600 mb-2 shadow-2xs" />
              <div class="font-bold text-xs text-teal-900 dark:text-teal-200">Teal (Primary)</div>
              <div class="text-[11px] text-teal-600 font-mono mt-0.5">#0d9488</div>
              <div class="text-[10px] text-slate-400 mt-1">--action-primary</div>
            </div>

            <!-- Emerald -->
            <div class="p-3 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40">
              <div class="h-10 rounded bg-emerald-600 mb-2 shadow-2xs" />
              <div class="font-bold text-xs text-emerald-900 dark:text-emerald-200">Emerald (Success)</div>
              <div class="text-[11px] text-emerald-600 font-mono mt-0.5">#059669</div>
              <div class="text-[10px] text-slate-400 mt-1">--status-success</div>
            </div>

            <!-- Red -->
            <div class="p-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/40">
              <div class="h-10 rounded bg-red-600 mb-2 shadow-2xs" />
              <div class="font-bold text-xs text-red-900 dark:text-red-200">Red (Panic / Danger)</div>
              <div class="text-[11px] text-red-600 font-mono mt-0.5">#dc2626</div>
              <div class="text-[10px] text-slate-400 mt-1">--status-panic</div>
            </div>

            <!-- Amber -->
            <div class="p-3 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40">
              <div class="h-10 rounded bg-amber-500 mb-2 shadow-2xs" />
              <div class="font-bold text-xs text-amber-900 dark:text-amber-200">Amber (Warning)</div>
              <div class="text-[11px] text-amber-600 font-mono mt-0.5">#f59e0b</div>
              <div class="text-[10px] text-slate-400 mt-1">--status-warning</div>
            </div>

            <!-- Sky -->
            <div class="p-3 rounded-lg border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/40">
              <div class="h-10 rounded bg-sky-600 mb-2 shadow-2xs" />
              <div class="font-bold text-xs text-sky-900 dark:text-sky-200">Sky (Info)</div>
              <div class="text-[11px] text-sky-600 font-mono mt-0.5">#0284c7</div>
              <div class="text-[10px] text-slate-400 mt-1">--status-info</div>
            </div>

            <!-- Slate -->
            <div class="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
              <div class="h-10 rounded bg-slate-800 mb-2 shadow-2xs" />
              <div class="font-bold text-xs text-slate-900 dark:text-slate-200">Slate (Neutral)</div>
              <div class="text-[11px] text-slate-500 font-mono mt-0.5">#1e293b</div>
              <div class="text-[10px] text-slate-400 mt-1">--text-primary</div>
            </div>
          </div>
        </Card>

        <!-- Typography Scale -->
        <Card title="Typography Scale (Self-Hosted Inter WOFF2)" subtitle="Zero CDN dependencies. Optimized for Indian low-resolution 1366×768 monitors.">
          <div class="space-y-4 divide-y divide-slate-100 dark:divide-slate-800">
            <div class="pt-2 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <span class="text-xs font-mono text-slate-400">text-xs (12px / 0.75rem) — MINIMUM CLINICAL FLOOR</span>
              <span class="text-xs text-slate-800 dark:text-slate-200 font-medium">SMP250123 &bull; Serum Creatinine: 0.9 mg/dL (Normal Range: 0.7 - 1.2 mg/dL)</span>
            </div>
            <div class="pt-3 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <span class="text-xs font-mono text-slate-400">text-sm (14px / 0.875rem) — Standard Body & Form Labels</span>
              <span class="text-sm text-slate-800 dark:text-slate-200 font-medium">Patient Registration &bull; Cashier Collection Counter #1</span>
            </div>
            <div class="pt-3 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <span class="text-xs font-mono text-slate-400">text-base (16px / 1rem) — Card Titles & Subsections</span>
              <span class="text-base text-slate-900 dark:text-slate-100 font-bold">Automated Analyzer Interface &bull; Mindray BC-5000</span>
            </div>
            <div class="pt-3 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <span class="text-xs font-mono text-slate-400">text-lg (18px / 1.125rem) — Page Titles & Prominent Headers</span>
              <span class="text-lg text-slate-900 dark:text-slate-100 font-bold">Pathologist Verification Queue (14 Pending Review)</span>
            </div>
            <div class="pt-3 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <span class="text-xs font-mono text-slate-400">text-2xl (24px / 1.5rem) — KPI Metric Hero Numbers</span>
              <span class="text-2xl text-slate-900 dark:text-slate-100 font-extrabold tracking-tight">₹ 1,48,250 <span class="text-xs font-normal text-slate-500">Today's Net Billing</span></span>
            </div>
          </div>
        </Card>
      </section>

      <!-- ================================================================== -->
      <!-- SECTION 2: BUTTONS & ACTIONS -->
      <!-- ================================================================== -->
      <section v-if="activeSection === 'buttons'" class="space-y-6">
        <PageHeader
          title="Buttons & Interactive Controls"
          subtitle="Accessible, keyboard-navigable buttons with focus rings, hover/active micro-animations, loading spinners, and icon slots."
        />

        <Card title="Button Variants (Size: Medium / 36px)">
          <div class="flex flex-wrap items-center gap-3">
            <Button variant="primary">Primary Action</Button>
            <Button variant="secondary">Secondary Action</Button>
            <Button variant="tertiary">Tertiary Subtle</Button>
            <Button variant="success">
              <template #icon-left><Icon name="whatsapp" size="sm" /></template>
              Send WhatsApp
            </Button>
            <Button variant="danger">
              <template #icon-left><Icon name="trash" size="sm" /></template>
              Reject Sample
            </Button>
            <Button variant="ghost">Ghost Button</Button>
          </div>
        </Card>

        <Card title="Button Sizes (sm: 28px compact, md: 36px standard, lg: 44px touch)">
          <div class="flex flex-wrap items-center gap-3">
            <Button variant="primary" size="sm" icon-left="plus">Register [F2] (28px)</Button>
            <Button variant="primary" size="md" icon-left="plus">Standard Button (36px)</Button>
            <Button variant="primary" size="lg" icon-left="plus">Touch Friendly (44px)</Button>
          </div>
        </Card>

        <Card title="Button States (Loading & Disabled)">
          <div class="flex flex-wrap items-center gap-3">
            <Button variant="primary" loading>Saving Patient...</Button>
            <Button variant="secondary" loading>Exporting PDF...</Button>
            <Button variant="primary" disabled>Disabled State</Button>
            <Button variant="secondary" disabled>Disabled Outline</Button>
          </div>
        </Card>

        <Card title="Icon Buttons & Keyboard Shortcuts">
          <div class="flex flex-wrap items-center gap-3">
            <IconButton icon="printer" label="Print Invoice (Alt+P)" variant="secondary" />
            <IconButton icon="share" label="Share WhatsApp Report" variant="primary" />
            <IconButton icon="refresh" label="Refresh Analyzer Packets" variant="ghost" />
            <IconButton icon="trash" label="Delete Record" variant="danger" />
            <IconButton icon="check" label="Quick Approve" variant="secondary" shape="round" />

            <div class="ml-6 flex items-center gap-2">
              <span class="text-xs text-slate-400">Shortcut Badges:</span>
              <Kbd>F2</Kbd>
              <Kbd>F3</Kbd>
              <Kbd>Ctrl</Kbd> + <Kbd>K</Kbd>
              <Kbd>Alt+S</Kbd>
            </div>
          </div>
        </Card>
      </section>

      <!-- ================================================================== -->
      <!-- SECTION 3: FORM INPUTS & SELECTS -->
      <!-- ================================================================== -->
      <section v-if="activeSection === 'forms'" class="space-y-6">
        <PageHeader
          title="Form Controls & Inputs"
          subtitle="Precision inputs engineered for high-throughput receptionist and phlebotomist keyboard entry."
        />

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card title="Text & Search Inputs">
            <div class="space-y-4">
              <Input
                v-model="sampleText"
                label="Patient Full Name"
                placeholder="Enter patient name"
                required
                clearable
                prefix-icon="user"
                helper-text="Full legal name as per government ID"
              />

              <Input
                label="Error State Demonstration"
                model-value="invalid-mobile-999"
                error="Please enter a valid 10-digit Indian mobile number."
                prefix-icon="phone"
              />

              <SearchField
                v-model="sampleSearch"
                placeholder="Quick lookup by UHID, Mobile, or Barcode..."
                shortcut="Ctrl+K"
              />
            </div>
          </Card>

          <Card title="Numeric & Stepper Inputs">
            <div class="space-y-4">
              <NumberInput
                v-model="sampleCurrency"
                label="Collected Amount (₹ INR)"
                prefix="₹"
                :step="50"
                helper-text="Quick increments of ₹50"
              />

              <NumberInput
                v-model="sampleNumber"
                label="Hemoglobin Result Value"
                suffix="g/dL"
                :step="0.1"
                :precision="1"
                :min="1"
                :max="25"
                helper-text="Reference range: 12.0 - 16.0 g/dL"
              />

              <Select
                v-model="sampleSelect"
                label="Investigation / Test Package"
                :options="selectOptions"
                clearable
                helper-text="Searchable combobox with keyboard arrow support"
              />
            </div>
          </Card>
        </div>

        <Card title="Toggles, Checkboxes & Segmented Controls">
          <div class="space-y-5">
            <div>
              <div class="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Segmented Control (Filter / Timeline)</div>
              <SegmentedControl
                v-model="sampleSegment"
                :options="segmentOptions"
              />
            </div>

            <div>
              <div class="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Payment Method Switcher</div>
              <SegmentedControl
                v-model="paymentSegment"
                :options="paymentOptions"
                size="sm"
              />
            </div>

            <div class="pt-2 flex flex-wrap items-center gap-6">
              <Checkbox
                v-model="sampleCheckbox"
                label="Fast-Track Sample Priority"
                description="Immediately marks sample as urgent (STAT) in analyzer worklist."
              />

              <Switch
                v-model="sampleSwitch"
                label="Automatic WhatsApp PDF Dispatch"
                description="Dispatch verified PDF directly to patient upon sign-off."
              />
            </div>
          </div>
        </Card>
      </section>

      <!-- ================================================================== -->
      <!-- SECTION 4: BADGES, CHIPS & KPIS -->
      <!-- ================================================================== -->
      <section v-if="activeSection === 'badges'" class="space-y-6">
        <PageHeader
          title="Badges, Status Chips & KPI Cards"
          subtitle="Semantic status communication without decorative clutter."
        />

        <Card title="Clinical Status Badges">
          <div class="flex flex-wrap items-center gap-3">
            <Badge variant="success" dot>Verified & Signed</Badge>
            <Badge variant="warning" dot>Abnormal Findings</Badge>
            <Badge variant="danger" dot>Specimen Hemolyzed</Badge>
            <Badge variant="panic" dot>CRITICAL PANIC VALUE</Badge>
            <Badge variant="info">In Analyzer Queue</Badge>
            <Badge variant="neutral">Draft Registration</Badge>
          </div>
        </Card>

        <Card title="Interactive Filter Chips">
          <div class="flex flex-wrap items-center gap-2">
            <Chip
              label="All Samples (48)"
              :active="activeFilterChip === 'all'"
              @click="activeFilterChip = 'all'"
            />
            <Chip
              label="Pending Verification (12)"
              :active="activeFilterChip === 'pending'"
              @click="activeFilterChip = 'pending'"
            />
            <Chip
              label="Critical Panic Flags (3)"
              :active="activeFilterChip === 'panic'"
              @click="activeFilterChip = 'panic'"
            />
            <Chip
              label="Branch: Main City Lab"
              removable
              @remove="info('Filter Removed', 'Cleared branch filter')"
            />
          </div>
        </Card>

        <!-- KPI Stat Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Today's Samples"
            value="142"
            :trend="12.5"
            trend-direction="up"
            trend-label="vs yesterday (126)"
            icon="beaker"
            icon-color="teal"
          />

          <StatCard
            label="Gross Revenue"
            value="₹ 54,800"
            :trend="8.2"
            trend-direction="up"
            trend-label="100% collected at POS"
            icon="credit-card"
            icon-color="emerald"
          />

          <StatCard
            label="Pending Approval"
            value="14"
            trend="3 Panic"
            trend-direction="down"
            trend-label="Average turnaround: 38m"
            icon="shield-check"
            icon-color="amber"
          />

          <StatCard
            label="Loading State Demo"
            loading
          />
        </div>
      </section>

      <!-- ================================================================== -->
      <!-- SECTION 5: DENSE CLINICAL TABLE -->
      <!-- ================================================================== -->
      <section v-if="activeSection === 'table'" class="space-y-6">
        <PageHeader
          title="High-Density Clinical Data Table"
          subtitle="Sticky header, row selection, sortable columns, and dense 36px rows engineered for rapid lab review."
        />

        <!-- Controls Bar -->
        <FilterBar
          search-placeholder="Search samples by ID, patient name, or analyte..."
        >
          <div class="flex items-center space-x-2">
            <Button
              variant="secondary"
              size="sm"
              @click="isDense = !isDense"
            >
              {{ isDense ? 'Switch to Normal Density' : 'Switch to Dense (36px)' }}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              @click="isZebra = !isZebra"
            >
              {{ isZebra ? 'Disable Zebra' : 'Enable Zebra' }}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              @click="isTableLoading = !isTableLoading"
            >
              Toggle Loading
            </Button>
            <Button
              variant="secondary"
              size="sm"
              @click="isTableEmpty = !isTableEmpty"
            >
              Toggle Empty
            </Button>
          </div>
        </FilterBar>

        <!-- Data Table -->
        <DataTable
          :columns="tableColumns"
          :data="isTableEmpty ? [] : mockTableData"
          row-key="sample_id"
          :dense="isDense"
          :zebra="isZebra"
          :loading="isTableLoading"
          selectable
          v-model:selected-keys="selectedTableKeys"
          @row-click="(row) => success('Selected Sample', `Viewing details for ${row.sample_id}`)"
        >
          <template #cell-sample_id="{ value }">
            <span class="font-mono font-bold text-teal-700 dark:text-teal-400">{{ value }}</span>
          </template>

          <template #cell-result="{ value, row }">
            <span
              :class="[
                'font-mono font-semibold',
                row.statusVariant === 'panic' ? 'text-red-600 dark:text-red-400 font-bold' : '',
                row.statusVariant === 'warning' ? 'text-amber-600 dark:text-amber-400 font-bold' : ''
              ]"
            >
              {{ value }}
            </span>
          </template>

          <template #cell-status="{ row }">
            <Badge :variant="row.statusVariant" :dot="row.statusVariant === 'panic'">
              {{ row.status }}
            </Badge>
          </template>

          <template #footer>
            <PaginationBar
              :current-page="1"
              :page-size="10"
              :total-items="isTableEmpty ? 0 : 48"
            />
          </template>
        </DataTable>
      </section>

      <!-- ================================================================== -->
      <!-- SECTION 6: MODALS, DRAWERS & TOASTS -->
      <!-- ================================================================== -->
      <section v-if="activeSection === 'overlays'" class="space-y-6">
        <PageHeader
          title="Modals, Drawers & Toast Notifications"
          subtitle="Non-blocking, accessible dialogs and slide-overs with full Esc key and backdrop click support."
        />

        <Card title="Trigger Dialogs & Panels">
          <div class="flex flex-wrap items-center gap-3">
            <Button variant="primary" @click="isModalOpen = true">
              Open Standard Modal Dialog
            </Button>
            <Button variant="secondary" @click="isDrawerOpen = true">
              Open Right Slide-Over Drawer
            </Button>
            <Button variant="danger" @click="isConfirmOpen = true">
              Open Destructive Confirm Dialog
            </Button>
          </div>
        </Card>

        <Card title="Trigger Toast Notifications (With Auto-Dismiss Countdown)">
          <div class="flex flex-wrap items-center gap-3">
            <Button
              variant="success"
              @click="success('Report Released', 'WhatsApp delivery dispatched to +91 98765 43210.')"
            >
              Trigger Success Toast
            </Button>
            <Button
              variant="danger"
              @click="error('Panic Value Flagged', 'Critical Glucose 450 mg/dL requires immediate review!')"
            >
              Trigger Danger Toast
            </Button>
            <Button
              variant="secondary"
              @click="warning('Analyzer Warning', 'Mindray BC-5000 Lyse reagent below 10% volume.')"
            >
              Trigger Warning Toast
            </Button>
            <Button
              variant="tertiary"
              @click="info('LAN Sync Active', 'SQLite local backup synced to external drive.')"
            >
              Trigger Info Toast
            </Button>
          </div>
        </Card>

        <!-- Standard Modal Instance -->
        <Modal
          v-model="isModalOpen"
          title="Quick Investigation Order"
          description="Rapid test selection and billing counter"
          size="md"
        >
          <div class="space-y-4">
            <Input label="Patient UHID" model-value="UHID-1082" readonly prefix-icon="user" />
            <Select
              v-model="sampleSelect"
              label="Investigation Package"
              :options="selectOptions"
            />
            <NumberInput
              v-model="sampleCurrency"
              label="Billed Amount"
              prefix="₹"
            />
          </div>
          <template #footer>
            <Button variant="secondary" size="sm" @click="isModalOpen = false">Cancel</Button>
            <Button variant="primary" size="sm" @click="isModalOpen = false; success('Order Saved', 'Investigation added successfully.')">
              Save & Print Bill [Alt+S]
            </Button>
          </template>
        </Modal>

        <!-- Drawer Instance -->
        <Drawer
          v-model="isDrawerOpen"
          title="Sample Accession Details"
          subtitle="Barcode #SMP2601 &bull; Phlebotomy Bench"
          width="md"
        >
          <div class="space-y-4 text-xs">
            <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 space-y-1.5">
              <div class="font-bold text-slate-800 dark:text-slate-200">Patient: Vikramaditya Roy</div>
              <div class="text-slate-500">Age/Gender: 45 Y / Male &bull; Contact: +91 98765 12345</div>
              <div class="text-slate-500">Referring Consultant: Dr. S. K. Mehta (City Clinic)</div>
            </div>

            <div class="space-y-2">
              <label class="font-semibold text-slate-700 dark:text-slate-300">Specimen Condition</label>
              <div class="flex gap-2">
                <Badge variant="success">EDTA Whole Blood</Badge>
                <Badge variant="neutral">Adequate Volume</Badge>
              </div>
            </div>

            <Input
              label="Phlebotomist Notes"
              placeholder="e.g. Fasting sample taken at 08:30 AM"
            />
          </div>
          <template #footer>
            <Button variant="secondary" size="sm" @click="isDrawerOpen = false">Close</Button>
            <Button variant="primary" size="sm" @click="isDrawerOpen = false; success('Accession Complete', 'Barcode marked received.')">
              Accept Specimen
            </Button>
          </template>
        </Drawer>

        <!-- Destructive Confirm Dialog Instance -->
        <ConfirmDialog
          v-model="isConfirmOpen"
          title="Reject Diagnostic Specimen?"
          message="Rejecting Sample #SMP2601 will mark the tube as hemolyzed/unfit and notify the phlebotomy desk to request a repeat collection. This action is audited."
          confirm-text="Reject Specimen"
          severity="danger"
          @confirm="isConfirmOpen = false; error('Specimen Rejected', 'Sample #SMP2601 marked rejected in audit log.')"
        />
      </section>
    </main>
  </div>
</template>

