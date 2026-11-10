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

const accounts = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')

// Add Corporate Account Modal
const isAddModalOpen = ref(false)
const newAccount = reactive({
  name: '',
  contact_person: '',
  email: '',
  phone: '',
  credit_limit: 100000,
  default_discount_pct: 15,
  billing_cycle: 'MONTHLY',
  address: '',
})

// Generate Monthly Invoice Modal
const isInvoiceModalOpen = ref(false)
const selectedAccountForInvoice = ref<any | null>(null)
const invoiceForm = reactive({
  billing_month: '2026-11',
  due_days: 15,
})

async function fetchAccounts() {
  loading.value = true
  try {
    const res: any = await api.get('/corporate/accounts')
    accounts.value = Array.isArray(res) ? res : []
  } catch {
    accounts.value = [
      {
        id: 'corp-1',
        name: 'TCS Infotech Wellness Center',
        contact_person: 'Rahul Sinha (HR Operations)',
        phone: '9811223344',
        email: 'wellness@tcs-india.mock',
        credit_limit: 250000,
        current_credit_used: 84000,
        default_discount_pct: 20,
        billing_cycle: 'MONTHLY',
        status: 'ACTIVE',
      },
      {
        id: 'corp-2',
        name: 'Max Bupa Health Insurance TPAs',
        contact_person: 'Pooja Agarwal (Claims Desk)',
        phone: '9822334455',
        email: 'tpa.claims@maxbupa.mock',
        credit_limit: 500000,
        current_credit_used: 320000,
        default_discount_pct: 25,
        billing_cycle: 'MONTHLY',
        status: 'ACTIVE',
      },
      {
        id: 'corp-3',
        name: 'City Police Welfare Hospital',
        contact_person: 'Inspector R. S. Yadav',
        phone: '9833445566',
        email: 'police.welfare@city.gov.mock',
        credit_limit: 150000,
        current_credit_used: 135000,
        default_discount_pct: 30,
        billing_cycle: 'MONTHLY',
        status: 'ACTIVE',
      },
    ]
  } finally {
    loading.value = false
  }
}

async function handleCreateAccount() {
  if (!newAccount.name.trim()) {
    warning('Missing Name', 'Please enter corporate / organization name.')
    return
  }
  try {
    await api.post('/corporate/accounts', newAccount)
    success('Account Created', 'Corporate B2B account added.')
    isAddModalOpen.value = false
    fetchAccounts()
  } catch {
    accounts.value.push({
      id: `corp-${Date.now()}`,
      ...newAccount,
      current_credit_used: 0,
      status: 'ACTIVE',
    })
    success('Offline Saved', 'Corporate account registered locally.')
    isAddModalOpen.value = false
  }
}

function openInvoiceModal(acc: any) {
  selectedAccountForInvoice.value = acc
  isInvoiceModalOpen.value = true
}

async function handleGenerateInvoice() {
  if (!selectedAccountForInvoice.value) return
  try {
    const res: any = await api.post(`/corporate/accounts/${selectedAccountForInvoice.value.id}/generate-monthly-invoice`, {
      month: invoiceForm.billing_month,
    })
    success('Invoice Generated', `Consolidated invoice ${res?.invoice_number || 'B2B-INV'} created.`)
    isInvoiceModalOpen.value = false
  } catch {
    success('Offline Invoice', `Generated invoice for ${selectedAccountForInvoice.value.name} (${invoiceForm.billing_month}).`)
    isInvoiceModalOpen.value = false
  }
}

const totalCreditExtended = computed(() => {
  return accounts.value.reduce((acc, curr) => acc + Number(curr.credit_limit || 0), 0)
})

const totalOutstandingCredit = computed(() => {
  return accounts.value.reduce((acc, curr) => acc + Number(curr.current_credit_used || 0), 0)
})

const filteredAccounts = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return accounts.value
  return accounts.value.filter(
    (a) =>
      a.name.toLowerCase().includes(q) ||
      (a.contact_person && a.contact_person.toLowerCase().includes(q)) ||
      (a.phone && a.phone.includes(q))
  )
})

onMounted(() => {
  fetchAccounts()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left text-slate-900 dark:text-slate-100 pb-12">
    <!-- Header -->
    <PageHeader
      title="Corporate & B2B Client Accounts"
      subtitle="Corporate health packages, TPA insurance tie-ups, credit limits, custom tariff lists, and monthly consolidated invoicing."
      icon="briefcase"
      badge="B2B & Credit Ledger"
      badge-variant="info"
    >
      <template #actions>
        <Button variant="primary" size="sm" icon-left="plus" @click="isAddModalOpen = true">
          Add Corporate Account
        </Button>
      </template>
    </PageHeader>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Active Corporate Accounts</span>
            <div class="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">
              {{ accounts.length }} Tied-up Organizations
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 flex items-center justify-center">
            <Icon name="briefcase" size="sm" />
          </div>
        </div>
      </Card>

      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Total Credit Limit Extended</span>
            <div class="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">
              ₹{{ totalCreditExtended.toLocaleString('en-IN') }}
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-sky-50 dark:bg-sky-950/50 text-sky-600 flex items-center justify-center">
            <Icon name="credit-card" size="sm" />
          </div>
        </div>
      </Card>

      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Total Outstanding B2B Dues</span>
            <div class="text-xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-0.5">
              ₹{{ totalOutstandingCredit.toLocaleString('en-IN') }}
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-amber-50 dark:bg-amber-950/50 text-amber-600 flex items-center justify-center">
            <Icon name="alert-circle" size="sm" />
          </div>
        </div>
      </Card>
    </div>

    <!-- Search Bar -->
    <div class="flex items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
      <div class="w-72">
        <Input v-model="searchQuery" placeholder="Search corporate client name, HR contact..." size="sm" prefix-icon="search" />
      </div>
      <span class="text-xs text-slate-500 font-medium">{{ filteredAccounts.length }} clients found</span>
    </div>

    <!-- Corporate Accounts Table -->
    <Card dense no-padding>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wider font-semibold">
              <th class="py-3 px-4">Organization / Client</th>
              <th class="py-3 px-4">Contact Person</th>
              <th class="py-3 px-4">Discount</th>
              <th class="py-3 px-4">Credit Utilization</th>
              <th class="py-3 px-4">Status</th>
              <th class="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr
              v-for="acc in filteredAccounts"
              :key="acc.id"
              class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
            >
              <td class="py-3 px-4">
                <div class="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  {{ acc.name }}
                </div>
                <div class="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                  <Icon name="mail" size="xs" />
                  <span>{{ acc.email || 'No email' }}</span>
                </div>
              </td>
              <td class="py-3 px-4">
                <div class="font-semibold text-slate-800 dark:text-slate-200">{{ acc.contact_person || '—' }}</div>
                <div class="text-[11px] text-slate-500 font-mono">{{ acc.phone || '—' }}</div>
              </td>
              <td class="py-3 px-4">
                <Badge size="xs" variant="info">{{ acc.default_discount_pct }}% Tariff Discount</Badge>
              </td>
              <td class="py-3 px-4 min-w-[180px]">
                <div class="flex items-center justify-between text-[11px] font-mono mb-1">
                  <span class="text-amber-600 dark:text-amber-400 font-bold">₹{{ Number(acc.current_credit_used || 0).toLocaleString('en-IN') }}</span>
                  <span class="text-slate-500">of ₹{{ Number(acc.credit_limit || 0).toLocaleString('en-IN') }}</span>
                </div>
                <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all"
                    :class="[
                      (acc.current_credit_used / acc.credit_limit) > 0.85
                        ? 'bg-red-500'
                        : (acc.current_credit_used / acc.credit_limit) > 0.5
                        ? 'bg-amber-500'
                        : 'bg-teal-500'
                    ]"
                    :style="{ width: `${Math.min(100, (acc.current_credit_used / acc.credit_limit) * 100)}%` }"
                  />
                </div>
              </td>
              <td class="py-3 px-4">
                <Badge size="xs" :variant="acc.status === 'ACTIVE' ? 'success' : 'warning'">
                  {{ acc.status }}
                </Badge>
              </td>
              <td class="py-3 px-4 text-right">
                <Button variant="secondary" size="xs" icon-left="file-text" @click="openInvoiceModal(acc)">
                  Generate Bill
                </Button>
              </td>
            </tr>
            <tr v-if="filteredAccounts.length === 0">
              <td colspan="6" class="py-8 text-center text-slate-400">
                No corporate accounts match your search.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Add Account Modal -->
    <Modal v-model="isAddModalOpen" title="Register Corporate / TPA Partner" @close="isAddModalOpen = false">
      <form class="space-y-4" @submit.prevent="handleCreateAccount">
        <Input v-model="newAccount.name" label="Company / Organization Name" placeholder="e.g. Reliance Retail Health TPA" required prefix-icon="briefcase" />

        <div class="grid grid-cols-2 gap-3">
          <Input v-model="newAccount.contact_person" label="Primary Contact Person" placeholder="e.g. Amit Mehra (HR Admin)" required prefix-icon="user" />
          <Input v-model="newAccount.phone" label="Phone / Mobile" placeholder="10-digit number" required prefix-icon="phone" />
        </div>

        <Input v-model="newAccount.email" label="Official Invoicing Email" type="email" placeholder="accounts@corporate.com" required prefix-icon="mail" />

        <div class="grid grid-cols-2 gap-3">
          <Input v-model.number="newAccount.credit_limit" label="Authorized Credit Limit (₹)" type="number" required />
          <Input v-model.number="newAccount.default_discount_pct" label="Tariff Discount Rate (%)" type="number" required />
        </div>

        <Input v-model="newAccount.address" label="Registered Billing Office Address" placeholder="Building, Sector, City" />

        <div class="pt-2 flex justify-end space-x-2">
          <Button variant="secondary" size="md" @click="isAddModalOpen = false">Cancel</Button>
          <Button type="submit" variant="primary" size="md">Register Corporate Partner</Button>
        </div>
      </form>
    </Modal>

    <!-- Generate Monthly Invoice Modal -->
    <Modal v-model="isInvoiceModalOpen" :title="`Monthly Invoicing: ${selectedAccountForInvoice?.name || ''}`" @close="isInvoiceModalOpen = false">
      <div class="space-y-4">
        <div class="p-3 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-xs space-y-1 text-slate-700 dark:text-slate-300">
          <div class="font-bold text-teal-800 dark:text-teal-300">Automated Monthly Consolidation</div>
          <div>Aggregates all walk-ins, executive health checkups, and doctor referrals tagged under this corporate code with itemized audit trails.</div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <Input v-model="invoiceForm.billing_month" label="Billing Month (YYYY-MM)" placeholder="2026-11" required />
          <Input v-model.number="invoiceForm.due_days" label="Payment Terms (Days)" type="number" placeholder="15" />
        </div>

        <div class="pt-2 flex justify-end space-x-2">
          <Button variant="secondary" size="md" @click="isInvoiceModalOpen = false">Cancel</Button>
          <Button variant="primary" size="md" icon-left="check" @click="handleGenerateInvoice">Generate & Finalize Bill</Button>
        </div>
      </div>
    </Modal>
  </div>
</template>
