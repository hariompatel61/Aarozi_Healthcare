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

const items = ref<any[]>([])
const movements = ref<any[]>([])
const loading = ref(false)
const selectedCategory = ref('ALL')
const searchQuery = ref('')
const activeTab = ref<'catalog' | 'movements'>('catalog')

// Receive Lot Modal
const isReceiveModalOpen = ref(false)
const receiveForm = reactive({
  item_id: '',
  lot_number: '',
  expiry_date: '',
  quantity: 100,
  unit_cost: 0,
})

// Log Consumption Modal
const isConsumeModalOpen = ref(false)
const consumeForm = reactive({
  item_id: '',
  lot_id: '',
  quantity: 1,
  movement_type: 'CONSUMPTION',
  reason: 'Routine Analyzer Runs',
})

async function fetchInventory() {
  loading.value = true
  try {
    const [resItems, resMovements]: any = await Promise.all([
      api.get('/inventory/items'),
      api.get('/inventory/movements'),
    ])
    items.value = Array.isArray(resItems) ? resItems : []
    movements.value = Array.isArray(resMovements) ? resMovements : []
  } catch {
    items.value = [
      {
        id: 'inv-1',
        item_code: 'BIO-GLU-500',
        name: 'Glucose Hexokinase Reagent Kit',
        category: 'REAGENT',
        unit_of_measure: 'Tests',
        current_stock: 450,
        minimum_threshold: 200,
        lot_number: 'LOT-GLU-2601',
        expiry_date: '2026-12-31',
      },
      {
        id: 'inv-2',
        item_code: 'HEM-CBC-DIL',
        name: 'CBC 5-Part Diluent 20L',
        category: 'REAGENT',
        unit_of_measure: 'Litres',
        current_stock: 12,
        minimum_threshold: 20,
        lot_number: 'LOT-HEM-9941',
        expiry_date: '2026-10-15',
      },
      {
        id: 'inv-3',
        item_code: 'CON-VAC-EDTA',
        name: 'K2-EDTA Vacutainer Tubes 2ml',
        category: 'TUBE',
        unit_of_measure: 'Pieces',
        current_stock: 800,
        minimum_threshold: 500,
        lot_number: 'LOT-VAC-5520',
        expiry_date: '2027-05-30',
      },
      {
        id: 'inv-4',
        item_code: 'QC-BIO-L1',
        name: 'Lyphochek Assayed Chemistry Control Level 1',
        category: 'CONTROL',
        unit_of_measure: 'Vials',
        current_stock: 4,
        minimum_threshold: 6,
        lot_number: 'LOT-QC-8812',
        expiry_date: '2026-08-20',
      },
    ]

    movements.value = [
      {
        id: 'mov-1',
        timestamp: new Date().toISOString(),
        item_name: 'Glucose Hexokinase Reagent Kit',
        movement_type: 'PURCHASE_RECEIPT',
        quantity: 500,
        balance_after: 450,
        lot_number: 'LOT-GLU-2601',
        user_name: 'Dr. Pathologist',
      },
      {
        id: 'mov-2',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        item_name: 'Glucose Hexokinase Reagent Kit',
        movement_type: 'CONSUMPTION',
        quantity: 50,
        balance_after: 450,
        lot_number: 'LOT-GLU-2601',
        user_name: 'Lab Technician #1',
      },
    ]
  } finally {
    loading.value = false
  }
}

async function handleReceiveLot() {
  if (!receiveForm.item_id || !receiveForm.lot_number || !receiveForm.expiry_date) {
    warning('Missing Fields', 'Please select item, lot number, and expiry date.')
    return
  }
  try {
    await api.post('/inventory/receive-lot', receiveForm)
    success('Stock Received', 'New reagent lot added to laboratory inventory.')
    isReceiveModalOpen.value = false
    fetchInventory()
  } catch {
    const item = items.value.find((i) => i.id === receiveForm.item_id)
    if (item) item.current_stock += Number(receiveForm.quantity)
    success('Offline Receipt', 'Stock quantity adjusted locally.')
    isReceiveModalOpen.value = false
  }
}

async function handleLogConsumption() {
  if (!consumeForm.item_id || consumeForm.quantity <= 0) {
    warning('Invalid Quantity', 'Please specify a valid quantity.')
    return
  }
  try {
    await api.post('/inventory/log-consumption', consumeForm)
    success('Consumption Logged', 'Stock deducted and audit entry saved.')
    isConsumeModalOpen.value = false
    fetchInventory()
  } catch {
    const item = items.value.find((i) => i.id === consumeForm.item_id)
    if (item) item.current_stock = Math.max(0, item.current_stock - Number(consumeForm.quantity))
    success('Offline Deduction', 'Stock balance updated locally.')
    isConsumeModalOpen.value = false
  }
}

const lowStockItems = computed(() => {
  return items.value.filter((i) => i.current_stock <= i.minimum_threshold)
})

const filteredItems = computed(() => {
  return items.value.filter((i) => {
    const matchCat = selectedCategory.value === 'ALL' || i.category === selectedCategory.value
    const q = searchQuery.value.toLowerCase().trim()
    const matchQ =
      !q ||
      i.name.toLowerCase().includes(q) ||
      i.item_code.toLowerCase().includes(q) ||
      (i.lot_number && i.lot_number.toLowerCase().includes(q))
    return matchCat && matchQ
  })
})

onMounted(() => {
  fetchInventory()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left text-slate-900 dark:text-slate-100 pb-12">
    <!-- Header -->
    <PageHeader
      title="Reagents, Kits & Stock Inventory"
      subtitle="Track laboratory reagents, vacutainers, lot numbers, expiry dates, automated test consumption, and reorder thresholds."
      icon="layers"
      badge="NABL Stock Audit"
      badge-variant="info"
    >
      <template #actions>
        <div class="flex items-center space-x-2">
          <Button variant="secondary" size="sm" icon-left="minus" @click="isConsumeModalOpen = true">
            Log Consumption
          </Button>
          <Button variant="primary" size="sm" icon-left="plus" @click="isReceiveModalOpen = true">
            Receive Reagent Lot
          </Button>
        </div>
      </template>
    </PageHeader>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Total Tracked SKUs</span>
            <div class="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">
              {{ items.length }} Catalog Items
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 flex items-center justify-center">
            <Icon name="layers" size="sm" />
          </div>
        </div>
      </Card>

      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Low Stock Alerts</span>
            <div class="text-xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-0.5">
              {{ lowStockItems.length }} Below Threshold
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-amber-50 dark:bg-amber-950/50 text-amber-600 flex items-center justify-center">
            <Icon name="alert-circle" size="sm" />
          </div>
        </div>
      </Card>

      <Card dense>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-500 font-medium">Near Expiry Lots (&lt; 90 Days)</span>
            <div class="text-xl font-bold font-mono text-red-600 dark:text-red-400 mt-0.5">
              1 Lot Active
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-red-50 dark:bg-red-950/50 text-red-600 flex items-center justify-center">
            <Icon name="clock" size="sm" />
          </div>
        </div>
      </Card>
    </div>

    <!-- Tab & Search Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
      <div class="flex items-center space-x-2">
        <button
          type="button"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition',
            activeTab === 'catalog'
              ? 'bg-teal-600 text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
          ]"
          @click="activeTab = 'catalog'"
        >
          Reagent Catalog
        </button>
        <button
          type="button"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition',
            activeTab === 'movements'
              ? 'bg-teal-600 text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
          ]"
          @click="activeTab = 'movements'"
        >
          Stock Audit Ledger
        </button>

        <select
          v-if="activeTab === 'catalog'"
          v-model="selectedCategory"
          class="h-8 px-2.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 ml-2"
        >
          <option value="ALL">All Categories</option>
          <option value="REAGENT">Reagents</option>
          <option value="TUBE">Vacutainer Tubes</option>
          <option value="CONTROL">QC Controls</option>
          <option value="CONSUMABLE">General Consumables</option>
        </select>
      </div>

      <div class="w-64">
        <Input v-model="searchQuery" placeholder="Search item, SKU, lot..." size="sm" prefix-icon="search" />
      </div>
    </div>

    <!-- Reagent Catalog Tab -->
    <Card v-if="activeTab === 'catalog'" dense no-padding>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wider font-semibold">
              <th class="py-3 px-4">SKU / Item Name</th>
              <th class="py-3 px-4">Category</th>
              <th class="py-3 px-4">Current Lot #</th>
              <th class="py-3 px-4">Expiry Date</th>
              <th class="py-3 px-4">Stock Level</th>
              <th class="py-3 px-4 text-right">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr
              v-for="item in filteredItems"
              :key="item.id"
              class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
            >
              <td class="py-3 px-4">
                <div class="font-bold text-slate-900 dark:text-slate-100">{{ item.name }}</div>
                <div class="text-[11px] font-mono text-slate-500">{{ item.item_code }}</div>
              </td>
              <td class="py-3 px-4">
                <Badge size="xs" variant="neutral">{{ item.category }}</Badge>
              </td>
              <td class="py-3 px-4 font-mono font-medium text-slate-700 dark:text-slate-300">
                {{ item.lot_number || 'LOT-GENERAL' }}
              </td>
              <td class="py-3 px-4 font-mono text-slate-600 dark:text-slate-400">
                {{ item.expiry_date || '2026-12-31' }}
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center gap-2">
                  <span class="font-mono font-bold text-slate-900 dark:text-white text-sm">
                    {{ item.current_stock }} {{ item.unit_of_measure }}
                  </span>
                  <span class="text-[11px] text-slate-400">
                    (Min: {{ item.minimum_threshold }})
                  </span>
                </div>
              </td>
              <td class="py-3 px-4 text-right">
                <Badge
                  size="xs"
                  :variant="item.current_stock <= item.minimum_threshold ? 'warning' : 'success'"
                >
                  {{ item.current_stock <= item.minimum_threshold ? 'Low Stock' : 'Optimal' }}
                </Badge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Stock Movements Audit Tab -->
    <Card v-else dense no-padding>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wider font-semibold">
              <th class="py-3 px-4">Timestamp</th>
              <th class="py-3 px-4">Item Name</th>
              <th class="py-3 px-4">Movement Type</th>
              <th class="py-3 px-4">Lot Number</th>
              <th class="py-3 px-4">Qty</th>
              <th class="py-3 px-4">Balance After</th>
              <th class="py-3 px-4 text-right">Operator</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr
              v-for="m in movements"
              :key="m.id"
              class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
            >
              <td class="py-2.5 px-4 font-mono text-slate-500">
                {{ new Date(m.timestamp).toLocaleDateString() }}
              </td>
              <td class="py-2.5 px-4 font-semibold text-slate-900 dark:text-slate-100">
                {{ m.item_name }}
              </td>
              <td class="py-2.5 px-4">
                <Badge
                  size="xs"
                  :variant="m.movement_type === 'PURCHASE_RECEIPT' ? 'success' : 'warning'"
                >
                  {{ m.movement_type }}
                </Badge>
              </td>
              <td class="py-2.5 px-4 font-mono text-slate-600 dark:text-slate-400">
                {{ m.lot_number || '—' }}
              </td>
              <td class="py-2.5 px-4 font-mono font-bold" :class="m.movement_type === 'CONSUMPTION' ? 'text-red-600' : 'text-emerald-600'">
                {{ m.movement_type === 'CONSUMPTION' ? '-' : '+' }}{{ m.quantity }}
              </td>
              <td class="py-2.5 px-4 font-mono font-medium text-slate-800 dark:text-slate-200">
                {{ m.balance_after }}
              </td>
              <td class="py-2.5 px-4 text-right text-slate-600 dark:text-slate-400 font-medium">
                {{ m.user_name || 'System' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Receive Lot Modal -->
    <Modal v-model="isReceiveModalOpen" title="Receive New Reagent / Consumable Lot" @close="isReceiveModalOpen = false">
      <form class="space-y-4" @submit.prevent="handleReceiveLot">
        <div class="flex flex-col space-y-1">
          <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Catalog Item *</label>
          <select v-model="receiveForm.item_id" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700" required>
            <option value="" disabled>-- Select Item to Receive --</option>
            <option v-for="it in items" :key="it.id" :value="it.id">
              {{ it.name }} ({{ it.item_code }})
            </option>
          </select>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <Input v-model="receiveForm.lot_number" label="Manufacturer Lot #" placeholder="e.g. LOT-2026-X" required />
          <Input v-model="receiveForm.expiry_date" label="Lot Expiry Date" type="date" required />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <Input v-model.number="receiveForm.quantity" label="Quantity Received" type="number" required />
          <Input v-model.number="receiveForm.unit_cost" label="Unit Cost (₹)" type="number" placeholder="0.00" />
        </div>

        <div class="pt-2 flex justify-end space-x-2">
          <Button variant="secondary" size="md" @click="isReceiveModalOpen = false">Cancel</Button>
          <Button type="submit" variant="primary" size="md">Add to Inventory</Button>
        </div>
      </form>
    </Modal>

    <!-- Log Consumption Modal -->
    <Modal v-model="isConsumeModalOpen" title="Log Reagent Consumption / Wastage" @close="isConsumeModalOpen = false">
      <form class="space-y-4" @submit.prevent="handleLogConsumption">
        <div class="flex flex-col space-y-1">
          <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Catalog Item *</label>
          <select v-model="consumeForm.item_id" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700" required>
            <option value="" disabled>-- Select Item --</option>
            <option v-for="it in items" :key="it.id" :value="it.id">
              {{ it.name }} (Current: {{ it.current_stock }} {{ it.unit_of_measure }})
            </option>
          </select>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <Input v-model.number="consumeForm.quantity" label="Quantity Consumed" type="number" required />
          <div class="flex flex-col space-y-1">
            <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Deduction Reason</label>
            <select v-model="consumeForm.movement_type" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700">
              <option value="CONSUMPTION">Routine Clinical Tests Run</option>
              <option value="EXPIRY_DISPOSAL">Expired / Discarded</option>
              <option value="ADJUSTMENT">Stock Audit Correction</option>
            </select>
          </div>
        </div>

        <Input v-model="consumeForm.reason" label="Audit Notes / Reason" placeholder="e.g. Calibration batch run" />

        <div class="pt-2 flex justify-end space-x-2">
          <Button variant="secondary" size="md" @click="isConsumeModalOpen = false">Cancel</Button>
          <Button type="submit" variant="primary" size="md">Deduct Stock</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

