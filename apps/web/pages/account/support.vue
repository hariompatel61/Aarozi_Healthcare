<script setup lang="ts">
import { ref } from 'vue'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import { useToast } from '~/composables/useToast'

definePageMeta({
  layout: 'customer',
})

const { success } = useToast()

const showNewTicket = ref(false)
const newTicket = ref({
  subject: '',
  category: 'LAN Networking / Master PC',
  priority: 'HIGH',
  description: '',
})

const tickets = ref([
  {
    id: 'TICK-9081',
    subject: 'LAN Client Workstation Firewall Configuration',
    category: 'LAN Networking',
    priority: 'HIGH',
    status: 'RESOLVED',
    date: '09 Nov 2026',
    response: 'Engineer connected via AnyDesk and allowed port 8000 through Windows Defender firewall.',
  },
])

function submitTicket() {
  if (!newTicket.value.subject || !newTicket.value.description) return
  tickets.value.unshift({
    id: `TICK-${Math.floor(1000 + Math.random() * 9000)}`,
    subject: newTicket.value.subject,
    category: newTicket.value.category,
    priority: newTicket.value.priority,
    status: 'OPEN',
    date: 'Just now',
    response: 'Awaiting technician review (Guaranteed SLA: < 15 mins)',
  })
  success('Support Ticket Created', 'Our technical support engineer has been notified.')
  showNewTicket.value = false
  newTicket.value.subject = ''
  newTicket.value.description = ''
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 dark:text-white">Customer Support Desk</h1>
        <p class="text-xs text-slate-500">Raise priority support tickets or request live remote desktop assistance</p>
      </div>

      <Button variant="primary" size="sm" @click="showNewTicket = true">
        <template #icon-left><Icon name="plus" size="xs" /></template>
        Open New Support Ticket
      </Button>
    </div>

    <!-- Direct Emergency Channels -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
        <span class="text-[10px] font-bold text-teal-600 uppercase">Immediate Remote Desktop</span>
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">AnyDesk / TeamViewer Assistance</h3>
        <p class="text-xs text-slate-500">Share your 9-digit AnyDesk address on WhatsApp for instant remote session.</p>
        <a href="https://wa.me/919876543210" target="_blank" class="text-xs font-bold text-teal-600 hover:underline block pt-1">
          WhatsApp Support (+91 98765 43210) →
        </a>
      </div>

      <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
        <span class="text-[10px] font-bold text-sky-600 uppercase">Direct Engineer Call</span>
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">Priority Phone Hotline</h3>
        <p class="text-xs text-slate-500">Speak directly with a senior healthcare systems engineer.</p>
        <a href="tel:+919876543210" class="text-xs font-bold text-sky-600 hover:underline block pt-1">
          Call +91 98765 43210 →
        </a>
      </div>
    </div>

    <!-- Support Tickets List -->
    <div class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
      <div class="p-6 border-b border-slate-100 dark:border-slate-800">
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Your Support Tickets</h3>
      </div>

      <div class="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
        <div v-for="t in tickets" :key="t.id" class="p-6 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="font-mono font-bold text-slate-900 dark:text-white">{{ t.id }}</span>
              <span class="text-slate-400">&bull;</span>
              <span class="font-bold text-slate-800 dark:text-slate-200">{{ t.subject }}</span>
            </div>
            <span
              class="px-2 py-0.5 rounded-full text-[10px] font-bold"
              :class="t.status === 'RESOLVED' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-amber-100 text-amber-800'"
            >
              {{ t.status }}
            </span>
          </div>

          <div class="flex items-center space-x-4 text-[11px] text-slate-500">
            <span>Category: {{ t.category }}</span>
            <span>&bull;</span>
            <span>Priority: <strong class="text-red-500">{{ t.priority }}</strong></span>
            <span>&bull;</span>
            <span>{{ t.date }}</span>
          </div>

          <p class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400">
            <strong>Technician Note:</strong> {{ t.response }}
          </p>
        </div>
      </div>
    </div>

    <!-- New Ticket Modal -->
    <div
      v-if="showNewTicket"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm"
      @click.self="showNewTicket = false"
    >
      <div class="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8 space-y-4">
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Open Support Ticket</h3>

        <form @submit.prevent="submitTicket" class="space-y-3 text-xs">
          <div>
            <label class="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Subject *</label>
            <input
              v-model="newTicket.subject"
              type="text"
              required
              placeholder="e.g. Barcode label calibration issue on TSC printer"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Issue Category</label>
              <select
                v-model="newTicket.category"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs focus:ring-2 focus:ring-teal-500"
              >
                <option>LAN Networking / Master PC</option>
                <option>Barcode / Thermal Printer</option>
                <option>Licence File Activation</option>
                <option>Report Template Customization</option>
                <option>Database Backup & Restore</option>
              </select>
            </div>
            <div>
              <label class="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Priority</label>
              <select
                v-model="newTicket.priority"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs focus:ring-2 focus:ring-teal-500"
              >
                <option value="CRITICAL">Critical (Lab Stopped)</option>
                <option value="HIGH">High (Urgent)</option>
                <option value="NORMAL">Normal</option>
              </select>
            </div>
          </div>

          <div>
            <label class="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Detailed Description *</label>
            <textarea
              v-model="newTicket.description"
              rows="4"
              required
              placeholder="Describe what occurred, any error messages, and your AnyDesk address if remote assistance is needed..."
              class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs focus:ring-2 focus:ring-teal-500"
            ></textarea>
          </div>

          <div class="flex justify-end space-x-2 pt-2">
            <Button variant="secondary" size="xs" @click="showNewTicket = false">Cancel</Button>
            <Button type="submit" variant="primary" size="xs">Submit Ticket</Button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

