<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import { useToast } from '~/composables/useToast'

definePageMeta({
  layout: 'customer',
})

const { success } = useToast()

const orders = [
  {
    orderId: 'ORD-202611-9014',
    date: '09 Nov 2026',
    item: 'Aarozi LIS — Yearly Pro (Annual Licence)',
    baseAmount: '₹14,999.00',
    gstAmount: '₹2,699.82',
    totalAmount: '₹17,698.82',
    status: 'PAID',
    paymentMethod: 'UPI / NetBanking (Razorpay)',
    invoiceNo: 'INV-AAR-2026-0812',
  },
]

function downloadInvoice(invoiceNo: string) {
  success('Invoice Downloaded', `Tax invoice ${invoiceNo} generated in PDF format.`)
}
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-black text-slate-900 dark:text-white">Orders & Tax Invoices</h1>
      <p class="text-xs text-slate-500">Download GST tax invoices, review transaction receipts, and purchase history</p>
    </div>

    <!-- Orders Table -->
    <div class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-semibold">
              <th class="py-3.5 px-6">Order ID & Date</th>
              <th class="py-3.5 px-6">Product / Plan</th>
              <th class="py-3.5 px-6">Payment Mode</th>
              <th class="py-3.5 px-6">Total Amount (Incl. GST)</th>
              <th class="py-3.5 px-6">Status</th>
              <th class="py-3.5 px-6 text-right">Tax Invoice</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60">
            <tr v-for="order in orders" :key="order.orderId" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
              <td class="py-4 px-6">
                <span class="font-mono font-bold text-slate-900 dark:text-white block">{{ order.orderId }}</span>
                <span class="text-slate-400 text-[11px]">{{ order.date }}</span>
              </td>
              <td class="py-4 px-6 font-medium text-slate-800 dark:text-slate-200">
                {{ order.item }}
              </td>
              <td class="py-4 px-6 text-slate-500">
                {{ order.paymentMethod }}
              </td>
              <td class="py-4 px-6">
                <span class="font-bold text-slate-900 dark:text-white block">{{ order.totalAmount }}</span>
                <span class="text-[10px] text-slate-400">18% GST: {{ order.gstAmount }}</span>
              </td>
              <td class="py-4 px-6">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                  {{ order.status }}
                </span>
              </td>
              <td class="py-4 px-6 text-right">
                <button
                  @click="downloadInvoice(order.invoiceNo)"
                  class="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline flex items-center space-x-1 ml-auto"
                >
                  <Icon name="document" size="xs" />
                  <span>Download {{ order.invoiceNo }}</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

