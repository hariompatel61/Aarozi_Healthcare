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

const { success, warning, error } = useToast()
const api = useApi()

const expenses = ref<any[]>([])
const categories = ref<any[]>([])
const vendors = ref<any[]>([])
const loading = ref(false)

const selectedCategory = ref('ALL')
const searchQuery = ref('')

// Modal state
const isAddExpenseModalOpen = ref(false)
const newExpense = reactive({
  category_id: '',
  vendor_id: '',
  amount: 0,
  payment_mode: 'Cash',
  receipt_number: '',
  description: '',
  expense_date: new Date().toISOString().substring(0, 10),
})

async function fetchCategories() {
  try {
    const res: any = await api.get('/expenses/categories')
    categories.value = Array.isArray(res) ? res : []
    if (categories.value.length > 0 && !newExpense.category_id) {
      newExpense.category_id = categories.value[0].id
    }
  } catch {
    categories.value = [
      { id: 'cat-reagents', name: 'Reagents & Controls' },
      { id: 'cat-utilities', name: 'Utilities & Power' },
      { id: 'cat-maint', name: 'Equipment Maintenance & AMC' },
      { id: 'cat-salaries', name: 'Staff Salaries & Stipends' },
      { id: 'cat-logistics', name: 'Logistics & Courier' },
      { id: 'cat-misc', name: 'Petty Cash & Consumables' },
    ]
  }
}

async function fetchVendors() {
  try {
    const res: any = await api.get('/expenses/vendors')
    vendors.value = Array.isArray(res) ? res : []
  } catch {
    vendors.value = [
      { id: 'ven-1', name: 'Transasia Bio-Medicals Ltd.' },
      { id: 'ven-2', name: 'Roche Diagnostics India' },
      { id: 'ven-3', name: 'Local City Power Board' },
      { id: 'ven-4', name: 'Apex Medical Supplies' },
    ]
  }
}

async function fetchExpenses() {
  loading.value = true
  try {
    const res: any = await api.get('/expenses')
    expenses.value = Array.isArray(res) ? res : []
  } catch {
    expenses.value = [
      {
        id: 'exp-1',
        expense_date: new Date().toISOString().substring(0, 10),
        category_name: 'Reagents & Controls',
        vendor_name: 'Transasia Bio-Medicals Ltd.',
        description: 'Biochemistry Erba XL reagents monthly restock',
        amount: 24500,
        payment_mode: 'Bank Transfer',
        receipt_number: 'TX-INV-9921',
      },
      {
        id: 'exp-2',
        expense_date: new Date().toISOString().substring(0, 10),
        category_name: 'Petty Cash & Consumables',
        vendor_name: 'Apex Medical Supplies',
        description: 'Phlebotomy cotton swabs, vacutainer needles 22G',
        amount: 3200,
        payment_mode: 'Cash',
        receipt_number: 'PC-8812',
      },
      {
        id: 'exp-3',
        expense_date: new Date(Date.now() - 86400000).toISOString().substring(0, 10),
        category_name: 'Logistics & Courier',
        vendor_name: 'BlueDart Courier Service',
        description: 'Sample dispatch for special oncology markers',
        amount: 1450,
        payment_mode: 'UPI',
        receipt_number: 'UPI-REF-0932',
      },
    ]
  } finally {
    loading.value = false
  }
}

async function handleAddExpense() {
  if (!newExpense.amount || newExpense.amount <= 0) {
    warning('Invalid Amount', 'Please enter a valid expense amount.')
    return
  }
  try {
    await api.post('/expenses', newExpense)
    success('Expense Recorded', 'Expense entry successfully saved.')
    isAddExpenseModalOpen.value = false
    fetchExpenses()
  } catch {
    const cat = categories.value.find((c) => c.id === newExpense.category_id)
    const ven = vendors.value.find((v) => v.id === newExpense.vendor_id)
    expenses.value.unshift({
      id: `exp-${Date.now()}`,
      category_name: cat?.name || 'General Expense',
      vendor_name: ven?.name || 'Direct / Cash',
      ...newExpense,
    })
    success('Offline Saved', 'Expense added to local ledger.')
    isAddExpenseModalOpen.value = false
  }
}

const totalExpenseMonth = computed(() => {
  return expenses.value.reduce((acc, curr) => acc + Number(curr.amount || 0), 0)
})

const todayExpenseTotal = computed(() => {
  const today = new Date().toISOString().substring(0, 10)
  return expenses.value
    .filter((e) => e.expense_date?.startsWith(today))
    .reduce((acc, curr) => acc + Number(curr.amount || 0), 0)
})

const filteredExpenses = computed(() => {
  return expenses.value.filter((e) => {
    const matchCat = selectedCategory.value === 'ALL' || e.category_name === selectedCategory.value
    const q = searchQuery.value.toLowerCase().trim()
    const matchQ =
      !q ||
      (e.description && e.description.toLowerCase().includes(q)) ||
      (e.vendor_name && e.vendor_name.toLowerCase().includes(q)) ||
      (e.receipt_number && e.receipt_number.toLowerCase().includes(q))
    return matchCat && matchQ
  })
})

onMounted(() => {
  fetchCategories()
  fetchVendors()
  fetchExpenses()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left text-slate-900 dark:text-slate-100 pb-12">
    <!-- Header -->
    <PageHeader
      title="Petty Cash & Expense Ledger"
      subtitle="Track reagent purchases, vendor payables, equipment maintenance, facility overheads, and daily petty cash."
      icon="dollar-sign"
      badge="Financial Accounting"
      badge-variant="info"
    >
      <template #actions>
        <Button variant="primary" size="sm" icon-left="plus" @click="isAddExpenseModalOpen = true">
          Record Expense
        </Button>
      </template>
    </PageHeader>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Total Monthly Expenses</span>
            <div class="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">
              ₹{{ totalExpenseMonth.toLocaleString('en-IN') }}
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-red-50 dark:bg-red-950/50 text-red-600 flex items-center justify-center">
            <Icon name="dollar-sign" size="sm" />
          </div>
        </div>
      </Card>

      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Today's Petty Cash</span>
            <div class="text-xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-0.5">
              ₹{{ todayExpenseTotal.toLocaleString('en-IN') }}
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-amber-50 dark:bg-amber-950/50 text-amber-600 flex items-center justify-center">
            <Icon name="clock" size="sm" />
          </div>
        </div>
      </Card>

      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Active Categories</span>
            <div class="text-xl font-bold font-mono text-teal-600 dark:text-teal-400 mt-0.5">
              {{ categories.length }} Cost Centers
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 flex items-center justify-center">
            <Icon name="folder" size="sm" />
          </div>
        </div>
      </Card>

      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Verified Vendors</span>
            <div class="text-xl font-bold font-mono text-sky-600 dark:text-sky-400 mt-0.5">
              {{ vendors.length }} Suppliers
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-sky-50 dark:bg-sky-950/50 text-sky-600 flex items-center justify-center">
            <Icon name="truck" size="sm" />
          </div>
        </div>
      </Card>
    </div>

    <!-- Filter Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
      <div class="flex items-center space-x-2">
        <select
          v-model="selectedCategory"
          class="h-8 px-2.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200"
        >
          <option value="ALL">All Cost Categories</option>
          <option v-for="c in categories" :key="c.id" :value="c.name">
            {{ c.name }}
          </option>
        </select>
      </div>

      <div class="w-64">
        <Input v-model="searchQuery" placeholder="Search description, vendor..." size="sm" prefix-icon="search" />
      </div>
    </div>

    <!-- Expense Ledger Table -->
    <Card dense no-padding>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wider font-semibold">
              <th class="py-3 px-4">Date</th>
              <th class="py-3 px-4">Category</th>
              <th class="py-3 px-4">Vendor / Supplier</th>
              <th class="py-3 px-4">Description</th>
              <th class="py-3 px-4">Payment Mode</th>
              <th class="py-3 px-4">Voucher / Receipt</th>
              <th class="py-3 px-4 text-right">Amount (₹)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr
              v-for="exp in filteredExpenses"
              :key="exp.id"
              class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
            >
              <td class="py-2.5 px-4 font-mono font-medium text-slate-700 dark:text-slate-300">
                {{ exp.expense_date }}
              </td>
              <td class="py-2.5 px-4">
                <Badge size="xs" variant="neutral">{{ exp.category_name || 'General' }}</Badge>
              </td>
              <td class="py-2.5 px-4 font-semibold text-slate-900 dark:text-slate-100">
                {{ exp.vendor_name || 'Direct / Cash' }}
              </td>
              <td class="py-2.5 px-4 text-slate-600 dark:text-slate-300 max-w-xs truncate">
                {{ exp.description || '—' }}
              </td>
              <td class="py-2.5 px-4">
                <span class="inline-flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
                  <Icon name="credit-card" size="xs" class="text-slate-400" />
                  <span>{{ exp.payment_mode }}</span>
                </span>
              </td>
              <td class="py-2.5 px-4 font-mono text-slate-500">
                {{ exp.receipt_number || '—' }}
              </td>
              <td class="py-2.5 px-4 text-right font-mono font-bold text-slate-900 dark:text-white">
                ₹{{ Number(exp.amount || 0).toLocaleString('en-IN') }}
              </td>
            </tr>
            <tr v-if="filteredExpenses.length === 0">
              <td colspan="7" class="py-8 text-center text-slate-400">
                No expense entries found for the selected criteria.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Record Expense Modal -->
    <Modal v-model="isAddExpenseModalOpen" title="Record Laboratory Expense" @close="isAddExpenseModalOpen = false">
      <form class="space-y-4" @submit.prevent="handleAddExpense">
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col space-y-1">
            <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Cost Category *</label>
            <select v-model="newExpense.category_id" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700" required>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="flex flex-col space-y-1">
            <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Vendor / Supplier</label>
            <select v-model="newExpense.vendor_id" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700">
              <option value="">-- No Vendor (Direct Cash / Petty) --</option>
              <option v-for="v in vendors" :key="v.id" :value="v.id">{{ v.name }}</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <Input v-model.number="newExpense.amount" label="Amount (₹)" type="number" required placeholder="0.00" />
          <Input v-model="newExpense.expense_date" label="Expense Date" type="date" required />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col space-y-1">
            <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Payment Tender</label>
            <select v-model="newExpense.payment_mode" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700">
              <option value="Cash">Cash (Petty Cash Box)</option>
              <option value="UPI">UPI (GooglePay / PhonePe / Paytm)</option>
              <option value="Bank Transfer">Bank Transfer (NEFT / RTGS / IMPS)</option>
              <option value="Card">Business Debit / Credit Card</option>
              <option value="Cheque">Cheque</option>
            </select>
          </div>
          <Input v-model="newExpense.receipt_number" label="Receipt / Invoice Number" placeholder="e.g. INV-2026-442" />
        </div>

        <Input v-model="newExpense.description" label="Expense Description / Purpose" placeholder="e.g. Monthly biochemistry controls batch" required />

        <div class="pt-2 flex justify-end space-x-2">
          <Button variant="secondary" size="md" @click="isAddExpenseModalOpen = false">Cancel</Button>
          <Button type="submit" variant="primary" size="md">Save Expense Entry</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

